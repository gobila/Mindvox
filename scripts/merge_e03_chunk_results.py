#!/usr/bin/env python3
"""Merge independently post-processed E03 chunks into one benchmark artifact.

This script is intentionally experimental. It does not change the public E03
endpoint and does not write to the Student Vault. It consumes the output of
scripts/process_e03_semantic_chunks.py and produces a deterministic merged
result for human inspection.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".benchmarks" / "e03_chunk_merge"
DEFAULT_COVERAGE_TERMS = [
    "Positivo",
    "licitações",
    "editais",
    "diários oficiais",
    "score",
    "NPS",
    "Data Lake",
    "banco de produção",
    "AutoML",
    "auto machine learning",
    "temporal",
    "invisible banking",
    "mainframe",
    "COBOL",
    "Mara",
    "Carlos",
    "Antônio",
    "Léo",
    "Eduardo",
    "restaurante universitário",
    "RU",
]

ARTIFICIAL_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?"
    r"(?:introdu[cç][aã]o|conclus[aã]o|resumo|s[ií]ntese|"
    r"t[oó]pico\s+\d+|parte\s+\d+|se[cç][aã]o\s+\d+)"
    r"\s*:?\s*$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    order: int
    first_segment_index: int
    segment_indexes: list[int]
    input_chars: int
    didactic_chars: int
    elapsed_seconds: float
    response: dict[str, Any]


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def canonical_entity_key(value: str) -> str:
    key = normalize_key(value)
    key = re.sub(r"\bapplication programming interface\b", "api", key)
    key = re.sub(r"\bminimum viable product\b", "mvp", key)
    key = re.sub(r"\bcreate read update delete\b", "crud", key)
    key = re.sub(r"\bmodel view controller\b", "mvc", key)
    key = re.sub(r"\bmodel template view\b", "mtv", key)
    key = re.sub(r"\bobject relational mapping\b", "orm", key)
    key = re.sub(r"\bnet promoter score\b", "nps", key)
    key = re.sub(r"\bauto machine learning\b", "automl", key)
    key = re.sub(r"\bbusiness intelligence\b", "bi", key)
    key = key.replace("microservicos", "microsservicos")
    key = key.replace("metabase", "metabase")
    key = re.sub(r"\bapis\b", "api", key)
    key = re.sub(r"\s+", " ", key).strip()
    key = re.sub(r"\b([a-z0-9]+) \1\b", r"\1", key)
    return key


def normalize_paragraph_key(value: str) -> str:
    value = normalize_key(value)
    return re.sub(r"\b(o|a|os|as|um|uma|uns|umas)\b", " ", value).strip()


def compact_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def split_paragraphs(text: str) -> list[str]:
    text = compact_text(text)
    if not text:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    normalized: list[str] = []
    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if len(lines) == 1 and ARTIFICIAL_HEADING_RE.match(lines[0]):
            continue
        cleaned_lines = []
        for line in lines:
            if line.startswith("#"):
                line = re.sub(r"^#{1,6}\s*", "", line).strip()
            cleaned_lines.append(line)
        cleaned = " ".join(cleaned_lines).strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def split_long_paragraph(paragraph: str, *, max_chars: int) -> list[str]:
    if max_chars <= 0 or len(paragraph) <= max_chars:
        return [paragraph]

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ0-9])", paragraph)
    if len(sentences) <= 1:
        return [paragraph]

    parts: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        projected_len = current_len + len(sentence) + (1 if current else 0)
        if current and projected_len > max_chars:
            parts.append(" ".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
            continue
        current.append(sentence)
        current_len = projected_len

    if current:
        parts.append(" ".join(current).strip())
    return parts or [paragraph]


def merge_didactic_text(chunks: list[ChunkRecord], *, max_paragraph_chars: int) -> str:
    merged: list[str] = []
    last_key = ""

    for chunk in chunks:
        paragraphs = split_paragraphs(str(chunk.response.get("didactic_text") or ""))
        for paragraph in paragraphs:
            for part in split_long_paragraph(paragraph, max_chars=max_paragraph_chars):
                key = normalize_paragraph_key(part)
                if key and key == last_key:
                    continue
                merged.append(part)
                last_key = key

    return "\n\n".join(merged).strip()


def first_segment_index(result: dict[str, Any], fallback: int) -> int:
    indexes = result.get("segment_indexes")
    if isinstance(indexes, list) and indexes:
        numeric_indexes = [int(index) for index in indexes if isinstance(index, int)]
        if numeric_indexes:
            return min(numeric_indexes)
    display = str(result.get("segment_indexes_display") or "")
    match = re.search(r"\d+", display)
    if match:
        return int(match.group(0))
    return fallback


def load_chunk_records(path: Path, *, allow_errors: bool) -> tuple[dict[str, Any], list[ChunkRecord]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise SystemExit("chunk_results.json does not contain non-empty results list.")

    errored = [result for result in results if result.get("status") != "pass"]
    if errored and not allow_errors:
        errored_ids = ", ".join(str(result.get("chunk_id")) for result in errored)
        raise SystemExit(
            "Chunk results contain errors. Re-run with --allow-errors to merge only "
            f"successful chunks. Errored chunks: {errored_ids}"
        )

    records: list[ChunkRecord] = []
    for order, result in enumerate(results):
        if result.get("status") != "pass":
            continue
        response = result.get("response")
        if not isinstance(response, dict):
            raise SystemExit(f"Chunk {result.get('chunk_id')} has no response object.")
        segment_indexes = [
            int(index)
            for index in result.get("segment_indexes", [])
            if isinstance(index, int)
        ]
        records.append(
            ChunkRecord(
                chunk_id=str(result.get("chunk_id") or f"chunk-{order + 1:02d}"),
                order=order,
                first_segment_index=first_segment_index(result, order),
                segment_indexes=segment_indexes,
                input_chars=int(result.get("input_chars") or 0),
                didactic_chars=int(result.get("didactic_chars") or 0),
                elapsed_seconds=float(result.get("elapsed_seconds") or 0.0),
                response=response,
            )
        )

    if not records:
        raise SystemExit("No successful chunks available to merge.")
    records.sort(key=lambda item: (item.first_segment_index, item.order))
    return payload, records


def value_aliases(*values: Any) -> set[str]:
    aliases: set[str] = set()
    for value in values:
        if isinstance(value, str) and value.strip():
            aliases.add(value.strip())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    aliases.add(item.strip())
    return aliases


def append_unique_text(target: list[str], values: list[str], *, limit: int | None = None) -> None:
    seen = {normalize_key(item) for item in target}
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        key = normalize_key(value)
        if not key or key in seen:
            continue
        target.append(value.strip())
        seen.add(key)
        if limit is not None and len(target) >= limit:
            break


def merge_themes(chunks: list[ChunkRecord]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    order_keys: list[str] = []

    for chunk in chunks:
        for theme in chunk.response.get("themes") or []:
            if not isinstance(theme, dict):
                continue
            title = str(theme.get("title") or "").strip()
            summary = str(theme.get("summary") or "").strip()
            key = canonical_entity_key(title or summary)
            if not key:
                continue

            if key not in by_key:
                by_key[key] = {
                    "order": 0,
                    "title": title or "Tema sem titulo",
                    "summary": summary,
                    "key_points": [],
                    "semantic_role": str(theme.get("semantic_role") or "didactic").strip(),
                    "evidence": str(theme.get("evidence") or "").strip() or None,
                    "source_chunks": [chunk.chunk_id],
                }
                order_keys.append(key)
            else:
                item = by_key[key]
                if not item.get("summary") and summary:
                    item["summary"] = summary
                if not item.get("evidence") and theme.get("evidence"):
                    item["evidence"] = str(theme.get("evidence")).strip()
                if chunk.chunk_id not in item["source_chunks"]:
                    item["source_chunks"].append(chunk.chunk_id)

            append_unique_text(
                by_key[key]["key_points"],
                theme.get("key_points") if isinstance(theme.get("key_points"), list) else [],
                limit=8,
            )

    merged = [by_key[key] for key in order_keys]
    for index, item in enumerate(merged, start=1):
        item["order"] = index
    return merged


def confidence_rank(value: str | None) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(str(value or "").lower(), 0)


def best_confidence(left: str | None, right: str | None) -> str:
    left_value = str(left or "medium").lower()
    right_value = str(right or "medium").lower()
    return left_value if confidence_rank(left_value) >= confidence_rank(right_value) else right_value


def merge_technical_terms(chunks: list[ChunkRecord]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    order_keys: list[str] = []

    for chunk in chunks:
        for term in chunk.response.get("technical_terms") or []:
            if not isinstance(term, dict):
                continue
            canonical = str(term.get("term") or "").strip()
            aliases = value_aliases(canonical, term.get("normalized_from"))
            key = canonical_entity_key(canonical)
            if not key:
                continue

            if key not in by_key:
                by_key[key] = {
                    "term": canonical,
                    "normalized_from": [],
                    "explanation": term.get("explanation"),
                    "confidence": str(term.get("confidence") or "medium").lower(),
                    "evidence": term.get("evidence"),
                    "source_chunks": [chunk.chunk_id],
                }
                order_keys.append(key)
            else:
                item = by_key[key]
                if not item.get("explanation") and term.get("explanation"):
                    item["explanation"] = term.get("explanation")
                if not item.get("evidence") and term.get("evidence"):
                    item["evidence"] = term.get("evidence")
                item["confidence"] = best_confidence(item.get("confidence"), term.get("confidence"))
                if chunk.chunk_id not in item["source_chunks"]:
                    item["source_chunks"].append(chunk.chunk_id)

            existing_aliases = set(by_key[key]["normalized_from"])
            for alias in sorted(aliases):
                if canonical_entity_key(alias) != key and alias not in existing_aliases:
                    by_key[key]["normalized_from"].append(alias)
                    existing_aliases.add(alias)

    return [by_key[key] for key in order_keys]


def merge_technology_mentions(chunks: list[ChunkRecord]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    order_keys: list[str] = []

    for chunk in chunks:
        for mention in chunk.response.get("technology_mentions") or []:
            if not isinstance(mention, dict):
                continue
            name = str(mention.get("name") or "").strip()
            category = str(mention.get("category") or "tool").strip()
            key = canonical_entity_key(name)
            if not key:
                continue

            if key not in by_key:
                by_key[key] = {
                    "name": name,
                    "category": category,
                    "context": str(mention.get("context") or "").strip(),
                    "importance": str(mention.get("importance") or "medium").lower(),
                    "normalized_from": [],
                    "confidence": str(mention.get("confidence") or "medium").lower(),
                    "evidence": mention.get("evidence"),
                    "source_chunks": [chunk.chunk_id],
                }
                order_keys.append(key)
            else:
                item = by_key[key]
                if not item.get("context") and mention.get("context"):
                    item["context"] = str(mention.get("context")).strip()
                if not item.get("evidence") and mention.get("evidence"):
                    item["evidence"] = mention.get("evidence")
                item["importance"] = best_confidence(item.get("importance"), mention.get("importance"))
                item["confidence"] = best_confidence(item.get("confidence"), mention.get("confidence"))
                if chunk.chunk_id not in item["source_chunks"]:
                    item["source_chunks"].append(chunk.chunk_id)

            aliases = value_aliases(name, mention.get("normalized_from"))
            existing_aliases = set(by_key[key]["normalized_from"])
            for alias in sorted(aliases):
                if canonical_entity_key(alias) != canonical_entity_key(name) and alias not in existing_aliases:
                    by_key[key]["normalized_from"].append(alias)
                    existing_aliases.add(alias)

    return [by_key[key] for key in order_keys]


def merge_processing_notes(chunks: list[ChunkRecord]) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = [
        {
            "type": "chunk_merge",
            "message": (
                f"O texto foi processado em {len(chunks)} chunks semanticos e "
                "fundido em ordem original por script deterministico de bancada."
            ),
        },
        {
            "type": "chunk_merge",
            "message": (
                "O merge priorizou fidelidade semantica, paragrafos legiveis, "
                "deduplicacao leve e preservacao de rastreabilidade por chunk."
            ),
        },
    ]
    seen = {normalize_key(note["type"] + " " + note["message"]) for note in notes}

    for chunk in chunks:
        for note in chunk.response.get("processing_notes") or []:
            if not isinstance(note, dict):
                continue
            note_type = str(note.get("type") or "processing").strip()
            message = str(note.get("message") or "").strip()
            if not message:
                continue
            key = normalize_key(note_type + " " + message)
            if key in seen:
                continue
            notes.append(
                {
                    "type": note_type,
                    "message": f"[{chunk.chunk_id}] {message}",
                }
            )
            seen.add(key)
    return notes


def merged_search_text(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(payload.get("didactic_text") or ""),
            json.dumps(payload.get("themes") or [], ensure_ascii=False),
            json.dumps(payload.get("technical_terms") or [], ensure_ascii=False),
            json.dumps(payload.get("technology_mentions") or [], ensure_ascii=False),
            json.dumps(payload.get("processing_notes") or [], ensure_ascii=False),
        ]
    )


def coverage_report(payload: dict[str, Any], terms: list[str]) -> dict[str, Any]:
    haystack = canonical_entity_key(merged_search_text(payload))
    items: list[dict[str, Any]] = []
    for term in terms:
        normalized = canonical_entity_key(term)
        found = bool(normalized and normalized in haystack)
        items.append(
            {
                "term": term,
                "normalized": normalized,
                "found": found,
            }
        )
    found_count = sum(1 for item in items if item["found"])
    return {
        "checked": len(items),
        "found": found_count,
        "missing": len(items) - found_count,
        "items": items,
    }


def text_shape_report(didactic_text: str) -> dict[str, Any]:
    paragraphs = [part for part in didactic_text.split("\n\n") if part.strip()]
    paragraph_lengths = [len(part) for part in paragraphs]
    return {
        "chars": len(didactic_text),
        "paragraphs": len(paragraphs),
        "max_paragraph_chars": max(paragraph_lengths) if paragraph_lengths else 0,
        "min_paragraph_chars": min(paragraph_lengths) if paragraph_lengths else 0,
        "avg_paragraph_chars": round(sum(paragraph_lengths) / len(paragraph_lengths), 2)
        if paragraph_lengths
        else 0,
        "markdown_headings": len(re.findall(r"(?m)^#{1,6}\s+.*$", didactic_text)),
        "bullet_lines": len(re.findall(r"(?m)^\s*[-*]\s+", didactic_text)),
        "numbered_list_lines": len(re.findall(r"(?m)^\s*\d+\.\s+", didactic_text)),
    }


def merged_raw_text(chunks: list[ChunkRecord], raw_text_file: Path | None) -> str:
    if raw_text_file is not None:
        return raw_text_file.read_text(encoding="utf-8").strip()
    return "\n\n".join(
        str(chunk.response.get("raw_text") or "").strip()
        for chunk in chunks
        if str(chunk.response.get("raw_text") or "").strip()
    ).strip()


def build_merged_payload(
    *,
    source_payload: dict[str, Any],
    chunks: list[ChunkRecord],
    raw_text: str,
    didactic_text: str,
    coverage_terms: list[str],
) -> dict[str, Any]:
    first_response = chunks[0].response
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    payload = {
        "processed_transcription_id": f"ptr_merge_{timestamp}",
        "input_type": first_response.get("input_type", "raw_text"),
        "language": first_response.get("language", "pt-BR"),
        "raw_text": raw_text,
        "didactic_text": didactic_text,
        "themes": merge_themes(chunks),
        "technical_terms": merge_technical_terms(chunks),
        "technology_mentions": merge_technology_mentions(chunks),
        "processing_notes": merge_processing_notes(chunks),
        "metadata": first_response.get("metadata") or {},
        "source": first_response.get("source") or {},
        "processing_engine": {
            **(first_response.get("processing_engine") or {}),
            "name": "deterministic-chunk-merge",
            "version": "experimental",
        },
        "artifact_locations": None,
        "merge_metadata": {
            "source_chunks_file": source_payload.get("chunks_file"),
            "source_method": source_payload.get("method"),
            "source_settings": source_payload.get("settings"),
            "chunk_count": len(chunks),
            "source_chunk_ids": [chunk.chunk_id for chunk in chunks],
            "total_input_chars": sum(chunk.input_chars for chunk in chunks),
            "total_chunk_didactic_chars": sum(chunk.didactic_chars for chunk in chunks),
            "total_elapsed_seconds": round(sum(chunk.elapsed_seconds for chunk in chunks), 3),
            "merge_strategy": "ordered_deterministic_light_dedup",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    payload["merge_metadata"]["text_shape"] = text_shape_report(didactic_text)
    payload["merge_metadata"]["coverage_report"] = coverage_report(
        payload,
        coverage_terms,
    )
    return payload


def markdown_for_didactic_text(payload: dict[str, Any]) -> str:
    metadata = payload.get("metadata") or {}
    title_parts = ["Texto Didatico E03"]
    if metadata.get("discipline"):
        title_parts.append(str(metadata["discipline"]))
    if metadata.get("class_date"):
        title_parts.append(str(metadata["class_date"]))

    lines = [
        f"# {' - '.join(title_parts)}",
        "",
        "> Artefato experimental gerado por merge deterministico de chunks ja processados pela LLM.",
        "",
        payload.get("didactic_text", "").strip(),
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    clean = {
        key: value
        for key, value in payload.items()
        if key != "merge_metadata"
    }
    clean["themes"] = [
        {key: value for key, value in theme.items() if key != "source_chunks"}
        for theme in payload.get("themes", [])
    ]
    clean["technical_terms"] = [
        {key: value for key, value in term.items() if key != "source_chunks"}
        for term in payload.get("technical_terms", [])
    ]
    clean["technology_mentions"] = [
        {key: value for key, value in mention.items() if key != "source_chunks"}
        for mention in payload.get("technology_mentions", [])
    ]
    return clean


def markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def write_outputs(
    *,
    run_dir: Path,
    chunk_results_file: Path,
    payload: dict[str, Any],
    chunks: list[ChunkRecord],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "merged_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    public = public_payload(payload)
    (run_dir / "merged_public_result.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "merge_audit.json").write_text(
        json.dumps(
            {
                "text_shape": payload["merge_metadata"]["text_shape"],
                "coverage_report": payload["merge_metadata"]["coverage_report"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "merged_didactic_text.md").write_text(
        markdown_for_didactic_text(public),
        encoding="utf-8",
    )

    summary = payload["merge_metadata"]
    coverage = summary["coverage_report"]
    text_shape = summary["text_shape"]
    lines = [
        "# E03 Chunk Merge Benchmark",
        "",
        f"- `chunk_results_file`: `{chunk_results_file}`",
        f"- `chunk_count`: `{summary['chunk_count']}`",
        f"- `merge_strategy`: `{summary['merge_strategy']}`",
        f"- `raw_text_chars`: `{len(payload['raw_text'])}`",
        f"- `didactic_text_chars`: `{len(payload['didactic_text'])}`",
        f"- `themes`: `{len(payload['themes'])}`",
        f"- `technical_terms`: `{len(payload['technical_terms'])}`",
        f"- `technology_mentions`: `{len(payload['technology_mentions'])}`",
        f"- `processing_notes`: `{len(payload['processing_notes'])}`",
        f"- `paragraphs`: `{text_shape['paragraphs']}`",
        f"- `max_paragraph_chars`: `{text_shape['max_paragraph_chars']}`",
        f"- `markdown_headings`: `{text_shape['markdown_headings']}`",
        f"- `bullet_lines`: `{text_shape['bullet_lines']}`",
        f"- `coverage_found`: `{coverage['found']}/{coverage['checked']}`",
        "",
        "## Chunks",
        "",
        "| Chunk | First segment | Input chars | Didactic chars | Time |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for chunk in chunks:
        lines.append(
            "| "
            f"`{markdown_cell(chunk.chunk_id)}` | "
            f"`{chunk.first_segment_index}` | "
            f"`{chunk.input_chars}` | "
            f"`{chunk.didactic_chars}` | "
            f"`{chunk.elapsed_seconds}` |"
        )

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            "| Term | Found |",
            "| --- | --- |",
        ]
    )
    for item in coverage["items"]:
        lines.append(
            f"| `{markdown_cell(item['term'])}` | `{'yes' if item['found'] else 'no'}` |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is an experimental merge artifact and is not the public E03 endpoint output.",
            "- `merged_public_result.json` removes experimental merge metadata and source chunk annotations.",
            "- `merged_result.json` keeps experimental merge metadata for audit.",
            "- `merge_audit.json` records deterministic text-shape and lexical coverage checks.",
            "- The merge preserves source order and does not rerun embeddings.",
            "- The didactic text is kept as continuous prose with paragraphs, without artificial Markdown headings.",
            "- Structured lists include `source_chunks` for inspection; this extra field is experimental.",
        ]
    )
    (run_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge independently processed E03 chunk results into one benchmark artifact."
    )
    parser.add_argument(
        "--chunk-results-file",
        required=True,
        type=Path,
        help="Path to chunk_results.json produced by process_e03_semantic_chunks.py.",
    )
    parser.add_argument(
        "--raw-text-file",
        type=Path,
        help="Optional original raw transcript file to use as final raw_text.",
    )
    parser.add_argument(
        "--case-name",
        default="",
        help="Optional run directory suffix. Defaults to chunk results parent name.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        type=Path,
        help="Directory where merge benchmark artifacts will be written.",
    )
    parser.add_argument(
        "--allow-errors",
        action="store_true",
        help="Merge successful chunks even if some chunk results errored.",
    )
    parser.add_argument(
        "--max-paragraph-chars",
        default=1800,
        type=int,
        help="Soft maximum paragraph length for merged didactic text. Use 0 to disable.",
    )
    parser.add_argument(
        "--coverage-term",
        action="append",
        default=[],
        help="Critical term to check in merged outputs. Can be repeated.",
    )
    parser.add_argument(
        "--coverage-terms-file",
        type=Path,
        help="Optional UTF-8 text file with one critical coverage term per line.",
    )
    parser.add_argument(
        "--no-default-coverage-terms",
        action="store_true",
        help=(
            "Disable built-in benchmark coverage terms. Use this for unrelated "
            "aulas so that anchors from another transcript do not create false positives."
        ),
    )
    return parser.parse_args()


def load_coverage_terms(args: argparse.Namespace) -> list[str]:
    terms = [] if args.no_default_coverage_terms else list(DEFAULT_COVERAGE_TERMS)
    if args.coverage_terms_file:
        if not args.coverage_terms_file.exists():
            raise SystemExit(f"Coverage terms file not found: {args.coverage_terms_file}")
        for line in args.coverage_terms_file.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                terms.append(value)
    terms.extend(args.coverage_term or [])

    unique_terms: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = canonical_entity_key(term)
        if not key or key in seen:
            continue
        unique_terms.append(term)
        seen.add(key)
    return unique_terms


def main() -> int:
    args = parse_args()
    chunk_results_file = args.chunk_results_file.resolve()
    if not chunk_results_file.exists():
        raise SystemExit(f"Chunk results file not found: {chunk_results_file}")
    if args.raw_text_file and not args.raw_text_file.exists():
        raise SystemExit(f"Raw text file not found: {args.raw_text_file}")

    source_payload, chunks = load_chunk_records(
        chunk_results_file,
        allow_errors=bool(args.allow_errors),
    )
    raw_text = merged_raw_text(chunks, args.raw_text_file)
    didactic_text = merge_didactic_text(
        chunks,
        max_paragraph_chars=int(args.max_paragraph_chars),
    )
    coverage_terms = load_coverage_terms(args)
    payload = build_merged_payload(
        source_payload=source_payload,
        chunks=chunks,
        raw_text=raw_text,
        didactic_text=didactic_text,
        coverage_terms=coverage_terms,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    case_name = args.case_name.strip() or chunk_results_file.parent.name
    run_dir = args.output_dir / f"{timestamp}_{case_name}"
    write_outputs(
        run_dir=run_dir,
        chunk_results_file=chunk_results_file,
        payload=payload,
        chunks=chunks,
    )
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
