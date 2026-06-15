#!/usr/bin/env python3
"""Experimental semantic chunking for E03 raw transcripts.

This script is intentionally a bench tool, not part of the public API. It reads
a raw transcript, splits it into ordered segments, clusters related segments in
memory, and writes a local report for human inspection.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".benchmarks" / "e03_semantic_chunks"

PORTUGUESE_STOPWORDS = {
    "a",
    "agora",
    "ainda",
    "alguma",
    "algumas",
    "algum",
    "alguns",
    "ali",
    "ao",
    "aos",
    "aquela",
    "aquelas",
    "aquele",
    "aqueles",
    "aquilo",
    "as",
    "ate",
    "aí",
    "bem",
    "cada",
    "com",
    "como",
    "da",
    "das",
    "de",
    "dela",
    "dele",
    "deles",
    "depois",
    "do",
    "dos",
    "e",
    "ela",
    "elas",
    "ele",
    "eles",
    "em",
    "entao",
    "era",
    "essa",
    "essas",
    "esse",
    "esses",
    "esta",
    "estao",
    "estar",
    "estas",
    "este",
    "estes",
    "eu",
    "foi",
    "gente",
    "isso",
    "isto",
    "ja",
    "lá",
    "mais",
    "mas",
    "me",
    "mesmo",
    "meu",
    "minha",
    "muito",
    "na",
    "nao",
    "nas",
    "no",
    "nos",
    "nossa",
    "nosso",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "porque",
    "pra",
    "quando",
    "que",
    "quem",
    "se",
    "sem",
    "ser",
    "seu",
    "sua",
    "tambem",
    "tem",
    "ter",
    "teu",
    "toda",
    "todas",
    "todo",
    "todos",
    "tu",
    "um",
    "uma",
    "umas",
    "uns",
    "vai",
    "voce",
    "voces",
}

TECH_TERMS = {
    "api",
    "apis",
    "automl",
    "banco",
    "captcha",
    "cobol",
    "data lake",
    "data warehouse",
    "diario oficial",
    "editais",
    "etl",
    "graphql",
    "grpc",
    "http",
    "ia",
    "java",
    "json",
    "lgpd",
    "mainframe",
    "microservicos",
    "nps",
    "openai",
    "playwright",
    "positivo",
    "rest",
    "selenium",
    "soap",
    "xml",
}


@dataclass(frozen=True)
class Segment:
    index: int
    start_char: int
    end_char: int
    text: str


@dataclass
class Chunk:
    chunk_id: str
    method: str
    segment_indexes: list[int]
    segment_indexes_display: str
    first_segment_index: int
    last_segment_index: int
    chars: int
    estimated_tokens: int
    top_terms: list[str]
    anchors: list[str]
    preview: str
    text: str


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def segment_transcript(text: str, *, target_chars: int, min_chars: int) -> list[Segment]:
    text = normalize_text(text)
    if not text:
        return []

    sentence_matches = list(
        re.finditer(r".+?(?:[.!?…]+(?=\s|$)|\n{2,}|$)", text, flags=re.DOTALL)
    )
    raw_units: list[tuple[int, int, str]] = []
    for match in sentence_matches:
        unit = re.sub(r"\s+", " ", match.group(0)).strip()
        if unit:
            raw_units.append((match.start(), match.end(), unit))

    segments: list[Segment] = []
    current: list[str] = []
    start_char = raw_units[0][0] if raw_units else 0
    end_char = start_char

    for unit_start, unit_end, unit in raw_units:
        current_len = sum(len(part) for part in current) + max(0, len(current) - 1)
        should_flush = current and current_len >= min_chars and current_len + len(unit) > target_chars
        if should_flush:
            text_segment = " ".join(current).strip()
            segments.append(
                Segment(
                    index=len(segments),
                    start_char=start_char,
                    end_char=end_char,
                    text=text_segment,
                )
            )
            current = []
            start_char = unit_start
        current.append(unit)
        end_char = unit_end

    if current:
        segments.append(
            Segment(
                index=len(segments),
                start_char=start_char,
                end_char=end_char,
                text=" ".join(current).strip(),
            )
        )

    return segments


def tokenize(text: str) -> list[str]:
    tokens = [
        _strip_accents(token.casefold())
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9_-]{2,}", text)
    ]
    return [token for token in tokens if token not in PORTUGUESE_STOPWORDS and not token.isdigit()]


def _strip_accents(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "ä": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c",
        }
    )
    return text.translate(replacements)


def tfidf_embeddings(segments: list[Segment]) -> np.ndarray:
    docs = [tokenize(segment.text) for segment in segments]
    vocab = sorted({token for doc in docs for token in doc})
    if not vocab:
        return np.zeros((len(segments), 1), dtype=np.float32)

    vocab_index = {term: idx for idx, term in enumerate(vocab)}
    df = Counter(term for doc in docs for term in set(doc))
    matrix = np.zeros((len(segments), len(vocab)), dtype=np.float32)

    for row, doc in enumerate(docs):
        counts = Counter(doc)
        if not counts:
            continue
        doc_len = sum(counts.values())
        for term, count in counts.items():
            tf = count / doc_len
            idf = math.log((1 + len(docs)) / (1 + df[term])) + 1
            matrix[row, vocab_index[term]] = tf * idf

    return normalize_vectors(matrix)


def bertimbau_embeddings(
    segments: list[Segment],
    *,
    model_name: str,
    batch_size: int,
) -> np.ndarray:
    try:
        import torch
        from transformers import AutoModel, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(
            "Bertimbau backend requires transformers and torch. "
            "Install locally with: uv pip install transformers"
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    vectors: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(segments), batch_size):
            batch = segments[start : start + batch_size]
            encoded = tokenizer(
                [segment.text for segment in batch],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            output = model(**encoded)
            token_embeddings = output.last_hidden_state
            attention_mask = encoded["attention_mask"].unsqueeze(-1)
            masked = token_embeddings * attention_mask
            summed = masked.sum(dim=1)
            counts = attention_mask.sum(dim=1).clamp(min=1)
            pooled = summed / counts
            vectors.append(pooled.cpu().numpy())

    return normalize_vectors(np.vstack(vectors).astype(np.float32))


def normalize_vectors(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return matrix / norms


def center_and_normalize_vectors(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - np.mean(matrix, axis=0, keepdims=True)
    return normalize_vectors(centered)


def cluster_segments(
    segments: list[Segment],
    vectors: np.ndarray,
    *,
    similarity_threshold: float,
    max_chunk_tokens: int,
) -> list[list[int]]:
    centroids: list[np.ndarray] = []
    clusters: list[list[int]] = []

    for segment in segments:
        vector = vectors[segment.index]
        token_estimate = estimate_tokens(segment.text)
        best_cluster = -1
        best_similarity = -1.0

        for cluster_index, centroid in enumerate(centroids):
            cluster_tokens = sum(estimate_tokens(segments[idx].text) for idx in clusters[cluster_index])
            if cluster_tokens + token_estimate > max_chunk_tokens:
                continue
            similarity = float(np.dot(vector, centroid))
            if similarity > best_similarity:
                best_similarity = similarity
                best_cluster = cluster_index

        if best_cluster >= 0 and best_similarity >= similarity_threshold:
            clusters[best_cluster].append(segment.index)
            centroids[best_cluster] = normalize_vectors(
                np.mean(vectors[clusters[best_cluster]], axis=0, keepdims=True)
            )[0]
        else:
            clusters.append([segment.index])
            centroids.append(vector)

    return merge_small_adjacent_clusters(segments, clusters, max_chunk_tokens=max_chunk_tokens)


def merge_small_adjacent_clusters(
    segments: list[Segment],
    clusters: list[list[int]],
    *,
    max_chunk_tokens: int,
) -> list[list[int]]:
    if not clusters:
        return []

    ordered = sorted(clusters, key=lambda indexes: min(indexes))
    merged: list[list[int]] = []

    for cluster in ordered:
        cluster = sorted(cluster)
        if not merged:
            merged.append(cluster)
            continue
        previous = merged[-1]
        previous_tokens = sum(estimate_tokens(segments[idx].text) for idx in previous)
        cluster_tokens = sum(estimate_tokens(segments[idx].text) for idx in cluster)
        previous_is_tiny = previous_tokens < max_chunk_tokens * 0.35
        cluster_is_tiny = cluster_tokens < max_chunk_tokens * 0.25
        if previous_is_tiny and cluster_is_tiny and previous_tokens + cluster_tokens <= max_chunk_tokens:
            previous.extend(cluster)
            previous.sort()
        else:
            merged.append(cluster)

    return merged


def build_chunks(
    segments: list[Segment],
    clusters: list[list[int]],
    *,
    method: str,
    preview_chars: int,
    top_terms_count: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for cluster_number, indexes in enumerate(sorted(clusters, key=lambda values: min(values)), start=1):
        ordered_indexes = sorted(indexes)
        text = "\n\n".join(segments[index].text for index in ordered_indexes)
        chunks.append(
            Chunk(
                chunk_id=f"{method}-{cluster_number:02d}",
                method=method,
                segment_indexes=ordered_indexes,
                segment_indexes_display=compact_indexes(ordered_indexes),
                first_segment_index=ordered_indexes[0],
                last_segment_index=ordered_indexes[-1],
                chars=len(text),
                estimated_tokens=estimate_tokens(text),
                top_terms=top_terms(text, top_terms_count),
                anchors=extract_anchors(text),
                preview=make_preview(text, preview_chars),
                text=text,
            )
        )
    return chunks


def compact_indexes(indexes: list[int]) -> str:
    if not indexes:
        return ""
    ranges: list[str] = []
    start = indexes[0]
    previous = indexes[0]
    for index in indexes[1:]:
        if index == previous + 1:
            previous = index
            continue
        ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = index
        previous = index
    ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def top_terms(text: str, count: int) -> list[str]:
    frequencies = Counter(tokenize(text))
    return [term for term, _ in frequencies.most_common(count)]


def extract_anchors(text: str) -> list[str]:
    anchors: set[str] = set()
    folded = _strip_accents(text.casefold())

    for term in TECH_TERMS:
        if term in folded:
            anchors.add(term)

    for match in re.finditer(r"\b\d+(?:[.,]\d+)?\s*(?:%|mil|milhao|milhoes|gb|mb|tokens?|editais?)?\b", folded):
        value = match.group(0).strip()
        if value:
            anchors.add(value)

    proper_phrases = re.findall(
        r"\b[A-ZÁÀÃÂÉÊÍÓÔÕÚÇ][A-Za-zÁÀÃÂÉÊÍÓÔÕÚÇáàãâéêíóôõúç]+"
        r"(?:\s+[A-ZÁÀÃÂÉÊÍÓÔÕÚÇ][A-Za-zÁÀÃÂÉÊÍÓÔÕÚÇáàãâéêíóôõúç]+){0,3}",
        text,
    )
    for phrase in proper_phrases:
        if len(phrase) >= 4 and phrase.casefold() not in PORTUGUESE_STOPWORDS:
            anchors.add(phrase.strip())

    return sorted(anchors, key=lambda item: (item.casefold(), item))[:30]


def make_preview(text: str, preview_chars: int) -> str:
    preview = re.sub(r"\s+", " ", text).strip()
    if len(preview) <= preview_chars:
        return preview
    return preview[:preview_chars].rstrip() + "..."


def evaluate_chunks(chunks: list[Chunk]) -> dict[str, Any]:
    if not chunks:
        return {
            "chunk_count": 0,
            "min_tokens": 0,
            "max_tokens": 0,
            "avg_tokens": 0,
            "total_tokens": 0,
        }
    token_counts = [chunk.estimated_tokens for chunk in chunks]
    return {
        "chunk_count": len(chunks),
        "min_tokens": min(token_counts),
        "max_tokens": max(token_counts),
        "avg_tokens": round(sum(token_counts) / len(token_counts), 2),
        "total_tokens": sum(token_counts),
    }


def write_outputs(
    *,
    run_dir: Path,
    input_file: str,
    raw_text: str,
    segments: list[Segment],
    results: dict[str, list[Chunk]],
    elapsed_seconds: float,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "input_file": input_file,
        "input_chars": len(raw_text),
        "segment_count": len(segments),
        "elapsed_seconds": elapsed_seconds,
        "methods": {
            method: {
                "metrics": evaluate_chunks(chunks),
                "chunks": [asdict(chunk) for chunk in chunks],
            }
            for method, chunks in results.items()
        },
    }
    (run_dir / "chunks.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# E03 Semantic Chunking Benchmark",
        "",
        f"- `input_file`: `{input_file}`",
        f"- `input_chars`: `{len(raw_text)}`",
        f"- `segments`: `{len(segments)}`",
        f"- `elapsed_seconds`: `{elapsed_seconds:.2f}`",
        "",
        "## Methods",
        "",
    ]
    for method, chunks in results.items():
        metrics = evaluate_chunks(chunks)
        lines.extend(
            [
                f"### {method}",
                "",
                f"- `chunk_count`: `{metrics['chunk_count']}`",
                f"- `min_tokens`: `{metrics['min_tokens']}`",
                f"- `max_tokens`: `{metrics['max_tokens']}`",
                f"- `avg_tokens`: `{metrics['avg_tokens']}`",
                "",
                "| Chunk | Segments | Tokens | Top terms | Anchors | Preview |",
                "| --- | ---: | ---: | --- | --- | --- |",
            ]
        )
        for chunk in chunks:
            lines.append(
                "| "
                f"`{chunk.chunk_id}` | "
                f"`{chunk.segment_indexes_display}` | "
                f"`{chunk.estimated_tokens}` | "
                f"{', '.join(chunk.top_terms[:8])} | "
                f"{', '.join(chunk.anchors[:8])} | "
                f"{chunk.preview.replace('|', '/')} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Notes",
            "",
            "- This is an experimental local report; outputs may contain real transcript excerpts.",
            "- Keep `.benchmarks/` out of Git.",
            "- The script does not call the E03 post-processing LLM.",
        ]
    )
    (run_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def run_method(args: argparse.Namespace, method: str, segments: list[Segment]) -> list[Chunk]:
    if method == "tfidf":
        vectors = tfidf_embeddings(segments)
    elif method == "bertimbau":
        vectors = bertimbau_embeddings(
            segments,
            model_name=args.bertimbau_model,
            batch_size=args.batch_size,
        )
    else:
        raise ValueError(f"Unsupported method: {method}")

    if args.center_vectors:
        vectors = center_and_normalize_vectors(vectors)

    clusters = cluster_segments(
        segments,
        vectors,
        similarity_threshold=args.similarity_threshold,
        max_chunk_tokens=args.max_chunk_tokens,
    )
    return build_chunks(
        segments,
        clusters,
        method=method,
        preview_chars=args.preview_chars,
        top_terms_count=args.top_terms,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Experiment with thematic chunking for E03 transcripts.")
    parser.add_argument("--input-file", required=True, help="Raw transcript text file.")
    parser.add_argument(
        "--method",
        choices=["tfidf", "bertimbau", "all"],
        default="tfidf",
        help="Chunking backend. `all` runs every available backend.",
    )
    parser.add_argument("--case-name", default="semantic-chunking", help="Human-readable benchmark case name.")
    parser.add_argument("--target-segment-chars", type=int, default=900, help="Target size for initial ordered segments.")
    parser.add_argument("--min-segment-chars", type=int, default=180, help="Minimum segment size before flushing.")
    parser.add_argument("--max-chunk-tokens", type=int, default=5000, help="Approximate maximum tokens per output chunk.")
    parser.add_argument("--similarity-threshold", type=float, default=0.18, help="Cosine threshold for assigning a segment to an existing thematic cluster.")
    parser.add_argument("--preview-chars", type=int, default=220, help="Preview chars written to README rows.")
    parser.add_argument("--top-terms", type=int, default=12, help="Top lexical terms per chunk.")
    parser.add_argument("--batch-size", type=int, default=4, help="Embedding batch size for transformer backends.")
    parser.add_argument("--bertimbau-model", default="neuralmind/bert-base-portuguese-cased", help="Hugging Face model for the Bertimbau backend.")
    parser.add_argument("--center-vectors", action="store_true", help="Center embeddings before clustering; useful for raw BERT mean-pooled vectors.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for local benchmark outputs.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    start = time.monotonic()

    input_path = Path(args.input_file)
    raw_text = input_path.read_text(encoding="utf-8").strip()
    if not raw_text:
        raise SystemExit("Input transcript is empty.")

    segments = segment_transcript(
        raw_text,
        target_chars=args.target_segment_chars,
        min_chars=args.min_segment_chars,
    )
    if not segments:
        raise SystemExit("No segments were produced.")

    methods = ["tfidf", "bertimbau"] if args.method == "all" else [args.method]
    results: dict[str, list[Chunk]] = {}
    failures: dict[str, str] = {}
    for method in methods:
        try:
            results[method] = run_method(args, method, segments)
        except SystemExit as exc:
            if args.method != "all":
                raise
            failures[method] = str(exc)

    if not results:
        raise SystemExit(f"No method completed. Failures: {failures}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_case = re.sub(r"[^A-Za-z0-9_.-]+", "-", args.case_name).strip("-")
    run_dir = Path(args.output_dir) / f"{timestamp}_{safe_case}"
    elapsed = time.monotonic() - start
    write_outputs(
        run_dir=run_dir,
        input_file=str(input_path),
        raw_text=raw_text,
        segments=segments,
        results=results,
        elapsed_seconds=elapsed,
    )

    print(f"E03 semantic chunking case: {args.case_name}")
    print(f"Input chars: {len(raw_text)}")
    print(f"Segments: {len(segments)}")
    for method, chunks in results.items():
        metrics = evaluate_chunks(chunks)
        print(
            f"{method}: chunks={metrics['chunk_count']} "
            f"min_tokens={metrics['min_tokens']} "
            f"max_tokens={metrics['max_tokens']} "
            f"avg_tokens={metrics['avg_tokens']}"
        )
    for method, failure in failures.items():
        print(f"{method}: skipped ({failure})", file=sys.stderr)
    print(f"Saved: {run_dir / 'chunks.json'}")
    print(f"Saved: {run_dir / 'README.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
