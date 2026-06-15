from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Any


CANONICAL_REPLACEMENTS = {
    "CIGA": "SIGAA",
    "UFNDE": "FNDE",
    "IAC": "IaC",
    "ICTI": "TI",
    "EPT": "ChatGPT",
    "GROC": "Groq",
}

REPETITIVE_NOISE_TOKENS = {"os", "ste"}
REPETITIVE_NOISE_MIN_RUN = 10

ACRONYM_ALLOWLIST = {
    "API",
    "APIS",
    "AWS",
    "BFF",
    "BI",
    "CNPJ",
    "COBOL",
    "CPF",
    "CRUD",
    "CSS",
    "Django".upper(),
    "DRF",
    "E02",
    "E03",
    "ETL",
    "FNDE",
    "GPT",
    "HTML",
    "HTTP",
    "HTTPS",
    "IA",
    "IAC",
    "JSON",
    "LGPD",
    "LLM",
    "MCP",
    "MGI",
    "MVP",
    "NPS",
    "OCR",
    "OPENAI",
    "ORM",
    "POC",
    "PRD",
    "REST",
    "RH",
    "RU",
    "SEI",
    "SIGAA",
    "SOAP",
    "SQL",
    "STT",
    "TCU",
    "TI",
    "UFG",
    "URL",
    "URLS",
    "VPS",
    "XML",
}

PORTUGUESE_STOPWORDS = {
    "a",
    "agora",
    "ainda",
    "ali",
    "ao",
    "aos",
    "as",
    "ate",
    "bem",
    "com",
    "como",
    "da",
    "das",
    "de",
    "dele",
    "depois",
    "do",
    "dos",
    "e",
    "ela",
    "ele",
    "eles",
    "em",
    "entao",
    "essa",
    "esse",
    "eu",
    "foi",
    "gente",
    "isso",
    "ja",
    "mais",
    "mas",
    "me",
    "mesmo",
    "muito",
    "na",
    "nao",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelo",
    "porque",
    "pra",
    "quando",
    "que",
    "se",
    "sem",
    "ser",
    "tambem",
    "tem",
    "ter",
    "todo",
    "um",
    "uma",
    "vai",
    "voce",
    "voces",
}

ARTIFICIAL_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?"
    r"(?:introdu[cç][aã]o|conclus[aã]o|resumo|s[ií]ntese|"
    r"t[oó]pico\s+\d+|parte\s+\d+|se[cç][aã]o\s+\d+)"
    r"\s*:?\s*$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class PreAuditIssue:
    suspect_text: str
    status: str
    replacement: str | None
    count: int


@dataclass(frozen=True)
class PreAuditResult:
    original_text: str
    text_for_llm: str
    issues: tuple[PreAuditIssue, ...]

    @property
    def canonical_replacements_count(self) -> int:
        return sum(1 for issue in self.issues if issue.replacement)

    @property
    def unresolved_terms(self) -> tuple[str, ...]:
        return tuple(
            issue.suspect_text
            for issue in self.issues
            if issue.status in {"unresolved_rare_acronym", "needs_review"}
        )


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    segment_indexes: tuple[int, ...]
    segment_indexes_display: str
    first_segment_index: int
    estimated_tokens: int
    text: str


def should_use_chunk_pipeline(
    *,
    raw_text: str,
    chunking_mode: str,
    min_chars: int,
) -> bool:
    return chunking_mode == "tfidf" and len(raw_text.strip()) >= min_chars


def pre_audit_raw_text(raw_text: str, *, enabled: bool) -> PreAuditResult:
    if not enabled:
        return PreAuditResult(original_text=raw_text, text_for_llm=raw_text, issues=())

    text = raw_text
    issues: list[PreAuditIssue] = []
    text = _remove_repetitive_noise(text, issues=issues)
    for suspect, replacement in CANONICAL_REPLACEMENTS.items():
        pattern = re.compile(rf"\b{re.escape(suspect)}\b")
        text, count = pattern.subn(replacement, text)
        if count:
            issues.append(
                PreAuditIssue(
                    suspect_text=suspect,
                    status="canonical_replacement_ready",
                    replacement=replacement,
                    count=count,
                )
            )

    for acronym in _rare_acronyms(text):
        if any(issue.suspect_text == acronym for issue in issues):
            continue
        issues.append(
            PreAuditIssue(
                suspect_text=acronym,
                status="unresolved_rare_acronym",
                replacement=None,
                count=len(re.findall(rf"\b{re.escape(acronym)}\b", text)),
            )
        )

    return PreAuditResult(
        original_text=raw_text,
        text_for_llm=text,
        issues=tuple(issues),
    )


def _remove_repetitive_noise(text: str, *, issues: list[PreAuditIssue]) -> str:
    for token in sorted(REPETITIVE_NOISE_TOKENS):
        pattern = re.compile(
            rf"(?<!\w)(?:{re.escape(token)}\s+){{{REPETITIVE_NOISE_MIN_RUN},}}",
            flags=re.IGNORECASE,
        )

        def replace(match: re.Match[str]) -> str:
            repeated = re.findall(rf"\b{re.escape(token)}\b", match.group(0), re.I)
            issues.append(
                PreAuditIssue(
                    suspect_text=token,
                    status="repetitive_noise_removed",
                    replacement="",
                    count=len(repeated),
                )
            )
            return " "

        text = pattern.sub(replace, text)

    return text


def pre_audit_context_header(pre_audit: PreAuditResult) -> str:
    if not pre_audit.issues:
        replacement_lines = ["- none"]
    else:
        replacement_lines = [
            f"- {issue.suspect_text} -> {issue.replacement} ({issue.status})"
            for issue in pre_audit.issues
            if issue.replacement
        ] or ["- none"]

    unresolved_terms = pre_audit.unresolved_terms
    if unresolved_terms:
        confidence_line = (
            "Remaining suspicious transcription terms were detected but are not "
            "verified class content. Do not promote them to didactic_text, themes, "
            "technical_terms, or technology_mentions unless the transcript body gives "
            "independent, clear semantic evidence. Mention unresolved terms only in "
            f"processing_notes when useful: {', '.join(unresolved_terms)}."
        )
    else:
        confidence_line = (
            "No remaining known suspicious transcription terms were detected after "
            "the pre-audit. Do not add new uncertainty notes about audited names, "
            "acronyms, or technical terms by plausibility alone."
        )

    status_counts = Counter(issue.status for issue in pre_audit.issues)
    return "\n".join(
        [
            "<<< Mindvox pre-audit context >>>",
            "This block is operational metadata, not classroom content.",
            "The transcript body below was generated after E02/E03 raw pre-audit.",
            f"Pre-audit issues: {len(pre_audit.issues)}.",
            f"Pre-audit status counts: {dict(status_counts)}.",
            f"Canonical replacements applied before this prompt: {pre_audit.canonical_replacements_count}.",
            "Canonical replacements:",
            *replacement_lines,
            confidence_line,
            "Do not copy this pre-audit block into the final JSON deliveries.",
            "<<< End Mindvox pre-audit context >>>",
            "",
        ]
    )


def chunk_text_tfidf(raw_text: str, *, max_chunk_tokens: int) -> list[TextChunk]:
    segments = _segment_transcript(raw_text, target_chars=900, min_chars=180)
    if not segments:
        return []
    vectors = _tfidf_vectors([segment[1] for segment in segments])
    clusters = _cluster_segments(
        segments=segments,
        vectors=vectors,
        max_chunk_tokens=max_chunk_tokens,
        similarity_threshold=0.18,
    )
    return _build_chunks(segments, clusters)


def merge_payload_dicts(
    *,
    chunk_payloads: list[dict[str, Any]],
    chunk_ids: list[str],
    original_raw_text: str,
    pre_audit: PreAuditResult,
    final_audit_enabled: bool,
) -> dict[str, Any]:
    didactic_text = _merge_didactic_text(chunk_payloads)
    payload = {
        "didactic_text": didactic_text,
        "themes": _merge_themes(chunk_payloads),
        "technical_terms": _merge_technical_terms(chunk_payloads),
        "technology_mentions": _merge_technology_mentions(chunk_payloads),
        "processing_notes": _merge_processing_notes(
            chunk_payloads=chunk_payloads,
            chunk_ids=chunk_ids,
            pre_audit=pre_audit,
        ),
    }
    if final_audit_enabled:
        _apply_final_audit(payload=payload, original_raw_text=original_raw_text, pre_audit=pre_audit)
    return payload


def _apply_final_audit(
    *,
    payload: dict[str, Any],
    original_raw_text: str,
    pre_audit: PreAuditResult,
) -> None:
    unresolved = set(pre_audit.unresolved_terms)
    if unresolved:
        payload["themes"] = [
            item for item in payload["themes"] if not _contains_any(item, unresolved)
        ]
        payload["technical_terms"] = [
            item for item in payload["technical_terms"] if not _contains_any(item, unresolved)
        ]
        payload["technology_mentions"] = [
            item for item in payload["technology_mentions"] if not _contains_any(item, unresolved)
        ]

    semantic_text = "\n".join(
        [
            payload.get("didactic_text", ""),
            str(payload.get("themes", "")),
            str(payload.get("technical_terms", "")),
            str(payload.get("technology_mentions", "")),
        ]
    )
    residual = [
        acronym
        for acronym in _rare_acronyms(semantic_text)
        if len(re.findall(rf"\b{re.escape(acronym)}\b", original_raw_text)) <= 6
    ]
    if residual:
        payload["processing_notes"].append(
            {
                "type": "final_audit",
                "message": (
                    "Auditoria final detectou siglas raras nos artefatos "
                    f"semanticos: {', '.join(sorted(set(residual)))}."
                ),
            }
        )


def _rare_acronyms(text: str) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"\b[A-Z][A-Z0-9]{1,9}\b", text):
        acronym = match.group(0)
        if acronym in seen or acronym.upper() in ACRONYM_ALLOWLIST:
            continue
        count = len(re.findall(rf"\b{re.escape(acronym)}\b", text))
        if 0 < count <= 6:
            output.append(acronym)
            seen.add(acronym)
    return output


def _segment_transcript(
    text: str,
    *,
    target_chars: int,
    min_chars: int,
) -> list[tuple[int, str]]:
    text = _compact_text(text)
    units = [
        re.sub(r"\s+", " ", match.group(0)).strip()
        for match in re.finditer(r".+?(?:[.!?…]+(?=\s|$)|\n{2,}|$)", text, flags=re.DOTALL)
        if match.group(0).strip()
    ]
    segments: list[tuple[int, str]] = []
    current: list[str] = []
    for unit in units:
        current_len = sum(len(part) for part in current) + max(0, len(current) - 1)
        if current and current_len >= min_chars and current_len + len(unit) > target_chars:
            segments.append((len(segments), " ".join(current).strip()))
            current = []
        current.append(unit)
    if current:
        segments.append((len(segments), " ".join(current).strip()))
    return segments


def _tfidf_vectors(segments: list[str]) -> list[dict[str, float]]:
    docs = [_tokenize(segment) for segment in segments]
    df = Counter(token for doc in docs for token in set(doc))
    vectors: list[dict[str, float]] = []
    for doc in docs:
        counts = Counter(doc)
        doc_len = sum(counts.values()) or 1
        vector: dict[str, float] = {}
        for token, count in counts.items():
            tf = count / doc_len
            idf = math.log((1 + len(docs)) / (1 + df[token])) + 1
            vector[token] = tf * idf
        vectors.append(_normalize_sparse(vector))
    return vectors


def _cluster_segments(
    *,
    segments: list[tuple[int, str]],
    vectors: list[dict[str, float]],
    max_chunk_tokens: int,
    similarity_threshold: float,
) -> list[list[int]]:
    centroids: list[dict[str, float]] = []
    clusters: list[list[int]] = []
    for index, segment_text in segments:
        vector = vectors[index]
        token_estimate = _estimate_tokens(segment_text)
        best_cluster = -1
        best_similarity = -1.0
        for cluster_index, centroid in enumerate(centroids):
            cluster_tokens = sum(_estimate_tokens(segments[idx][1]) for idx in clusters[cluster_index])
            if cluster_tokens + token_estimate > max_chunk_tokens:
                continue
            similarity = _sparse_dot(vector, centroid)
            if similarity > best_similarity:
                best_similarity = similarity
                best_cluster = cluster_index
        if best_cluster >= 0 and best_similarity >= similarity_threshold:
            clusters[best_cluster].append(index)
            centroids[best_cluster] = _centroid([vectors[idx] for idx in clusters[best_cluster]])
        else:
            clusters.append([index])
            centroids.append(vector)
    return _merge_small_adjacent_clusters(segments, clusters, max_chunk_tokens=max_chunk_tokens)


def _merge_small_adjacent_clusters(
    segments: list[tuple[int, str]],
    clusters: list[list[int]],
    *,
    max_chunk_tokens: int,
) -> list[list[int]]:
    ordered = sorted(clusters, key=min)
    merged: list[list[int]] = []
    for cluster in ordered:
        cluster = sorted(cluster)
        if not merged:
            merged.append(cluster)
            continue
        previous = merged[-1]
        previous_tokens = sum(_estimate_tokens(segments[idx][1]) for idx in previous)
        cluster_tokens = sum(_estimate_tokens(segments[idx][1]) for idx in cluster)
        if (
            previous_tokens < max_chunk_tokens * 0.35
            and cluster_tokens < max_chunk_tokens * 0.25
            and previous_tokens + cluster_tokens <= max_chunk_tokens
        ):
            previous.extend(cluster)
            previous.sort()
        else:
            merged.append(cluster)
    return merged


def _build_chunks(
    segments: list[tuple[int, str]],
    clusters: list[list[int]],
) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for number, indexes in enumerate(sorted(clusters, key=min), start=1):
        ordered = tuple(sorted(indexes))
        text = "\n\n".join(segments[index][1] for index in ordered)
        chunks.append(
            TextChunk(
                chunk_id=f"tfidf-{number:02d}",
                segment_indexes=ordered,
                segment_indexes_display=_compact_indexes(list(ordered)),
                first_segment_index=ordered[0],
                estimated_tokens=_estimate_tokens(text),
                text=text,
            )
        )
    return chunks


def _merge_didactic_text(chunk_payloads: list[dict[str, Any]]) -> str:
    paragraphs: list[str] = []
    last_key = ""
    for payload in chunk_payloads:
        for paragraph in _split_paragraphs(str(payload.get("didactic_text") or "")):
            key = _normalize_key(paragraph)
            if key and key != last_key:
                paragraphs.extend(_split_long_paragraph(paragraph, max_chars=1800))
                last_key = key
    return "\n\n".join(paragraphs).strip()


def _merge_themes(chunk_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = _merge_dict_items(
        chunk_payloads,
        collection="themes",
        key_field="title",
        defaults={
            "order": 0,
            "title": "Tema sem titulo",
            "summary": "",
            "key_points": [],
            "semantic_role": "tema",
            "evidence": None,
        },
    )
    for index, item in enumerate(merged, start=1):
        item["order"] = index
    return merged


def _merge_technical_terms(chunk_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _merge_dict_items(
        chunk_payloads,
        collection="technical_terms",
        key_field="term",
        defaults={
            "term": "",
            "normalized_from": [],
            "explanation": None,
            "confidence": "medium",
            "evidence": None,
        },
    )


def _merge_technology_mentions(chunk_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _merge_dict_items(
        chunk_payloads,
        collection="technology_mentions",
        key_field="name",
        defaults={
            "name": "",
            "category": "tool",
            "context": "Technology mention identified by E03.",
            "importance": "medium",
            "normalized_from": [],
            "confidence": "medium",
            "evidence": None,
        },
    )


def _merge_dict_items(
    chunk_payloads: list[dict[str, Any]],
    *,
    collection: str,
    key_field: str,
    defaults: dict[str, Any],
) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for payload in chunk_payloads:
        for item in payload.get(collection) or []:
            if not isinstance(item, dict):
                continue
            key_value = str(
                item.get(key_field)
                or item.get("summary")
                or item.get("title")
                or item.get("term")
                or item.get("name")
                or ""
            ).strip()
            key = _canonical_entity_key(key_value)
            if not key:
                continue
            if key not in by_key:
                merged = {**defaults, **{k: v for k, v in item.items() if k in defaults}}
                by_key[key] = merged
                order.append(key)
            else:
                _merge_item_values(by_key[key], item)
    return [by_key[key] for key in order]


def _merge_item_values(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if key not in target:
            continue
        if isinstance(target[key], list):
            existing = {_normalize_key(str(item)) for item in target[key]}
            for item in value if isinstance(value, list) else []:
                item_key = _normalize_key(str(item))
                if item_key and item_key not in existing:
                    target[key].append(item)
                    existing.add(item_key)
        elif not target[key] and value:
            target[key] = value
        elif key in {"confidence", "importance"}:
            target[key] = _best_confidence(str(target[key]), str(value))


def _merge_processing_notes(
    *,
    chunk_payloads: list[dict[str, Any]],
    chunk_ids: list[str],
    pre_audit: PreAuditResult,
) -> list[dict[str, str]]:
    notes = [
        {
            "type": "chunk_merge",
            "message": (
                f"Texto longo processado em {len(chunk_payloads)} chunks TF-IDF "
                "e fundido por merge canonico deterministico."
            ),
        }
    ]
    if pre_audit.issues:
        notes.append(
            {
                "type": "pre_audit",
                "message": (
                    f"Pre-auditoria aplicou {pre_audit.canonical_replacements_count} "
                    "normalizacoes canonicas antes do LLM."
                ),
            }
        )
    seen = {_normalize_key(note["type"] + " " + note["message"]) for note in notes}
    for chunk_id, payload in zip(chunk_ids, chunk_payloads):
        for note in payload.get("processing_notes") or []:
            if not isinstance(note, dict):
                continue
            note_type = str(note.get("type") or "processing").strip()
            message = str(note.get("message") or "").strip()
            key = _normalize_key(note_type + " " + message)
            if not message or key in seen:
                continue
            notes.append({"type": note_type, "message": f"[{chunk_id}] {message}"})
            seen.add(key)
    return notes


def _split_paragraphs(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", _compact_text(text)) if part.strip()]
    output: list[str] = []
    for part in parts:
        lines = [line.strip() for line in part.splitlines() if line.strip()]
        if len(lines) == 1 and ARTIFICIAL_HEADING_RE.match(lines[0]):
            continue
        cleaned = " ".join(re.sub(r"^#{1,6}\s*", "", line).strip() for line in lines)
        if cleaned:
            output.append(cleaned)
    return output


def _split_long_paragraph(paragraph: str, *, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ0-9])", paragraph)
    output: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        projected = len(" ".join([*current, sentence]))
        if current and projected > max_chars:
            output.append(" ".join(current).strip())
            current = [sentence]
        else:
            current.append(sentence)
    if current:
        output.append(" ".join(current).strip())
    return output or [paragraph]


def _contains_any(item: Any, terms: set[str]) -> bool:
    text = str(item)
    return any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms)


def _tokenize(text: str) -> list[str]:
    tokens = [
        _strip_accents(token.casefold())
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9_-]{2,}", text)
    ]
    return [token for token in tokens if token not in PORTUGUESE_STOPWORDS and not token.isdigit()]


def _normalize_sparse(vector: dict[str, float]) -> dict[str, float]:
    norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
    return {key: value / norm for key, value in vector.items()}


def _sparse_dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def _centroid(vectors: list[dict[str, float]]) -> dict[str, float]:
    values: dict[str, float] = {}
    for vector in vectors:
        for key, value in vector.items():
            values[key] = values.get(key, 0.0) + value
    count = len(vectors) or 1
    return _normalize_sparse({key: value / count for key, value in values.items()})


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def _compact_indexes(indexes: list[int]) -> str:
    if not indexes:
        return ""
    ranges: list[str] = []
    start = previous = indexes[0]
    for index in indexes[1:]:
        if index == previous + 1:
            previous = index
            continue
        ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = previous = index
    ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def _best_confidence(left: str, right: str) -> str:
    rank = {"low": 1, "medium": 2, "high": 3}
    left_value = left if left in rank else "medium"
    right_value = right if right in rank else "medium"
    return left_value if rank[left_value] >= rank[right_value] else right_value


def _compact_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    return "".join(char for char in value if not unicodedata.combining(char))


def _normalize_key(value: str) -> str:
    value = _strip_accents(value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _canonical_entity_key(value: str) -> str:
    key = _normalize_key(value)
    key = re.sub(r"\bapplication programming interface\b", "api", key)
    key = re.sub(r"\bminimum viable product\b", "mvp", key)
    key = re.sub(r"\bcreate read update delete\b", "crud", key)
    key = re.sub(r"\bobject relational mapping\b", "orm", key)
    key = re.sub(r"\bnet promoter score\b", "nps", key)
    key = re.sub(r"\bauto machine learning\b", "automl", key)
    key = re.sub(r"\bapis\b", "api", key)
    return re.sub(r"\s+", " ", key).strip()
