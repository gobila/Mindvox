#!/usr/bin/env python3
"""Audit a merged E03 result against timestamped raw transcription segments.

This script is intentionally offline and experimental. It does not modify the
public E03 endpoint and does not rewrite the final didactic text. Its purpose is
to prepare an evidence dossier for suspicious terms, possible transcription
errors, low-confidence generated entities, and missing coverage anchors.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".benchmarks" / "e03_final_audit"
DEFAULT_SUSPICIOUS_TERMS: list[str] = []
DEFAULT_ACRONYM_ALLOWLIST = {
    "API",
    "APIS",
    "BFF",
    "BI",
    "CNPJ",
    "CPF",
    "CRUD",
    "CSS",
    "E02",
    "E03",
    "HTML",
    "HTTP",
    "HTTPS",
    "IA",
    "IFG",
    "JSON",
    "LGPD",
    "LLM",
    "MVP",
    "NPS",
    "OCR",
    "ORM",
    "COBOL",
    "MGI",
    "POC",
    "PRD",
    "REST",
    "RH",
    "RU",
    "SEI",
    "SOAP",
    "SQL",
    "STT",
    "TCU",
    "UFG",
    "URL",
    "URLS",
    "VPS",
    "XML",
}
KNOWN_CANONICAL_SPELLING_CANDIDATES = {
    "CIGA": "SIGAA",
    "EPT": "GPT ou ChatGPT",
    "GROC": "Groq",
    "IAC": "IaC",
    "ICTI": "TI",
    "UFNDE": "FNDE",
}


@dataclass(frozen=True)
class SegmentRecord:
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class AuditCandidate:
    issue_type: str
    suspect_text: str
    reason: str
    source: str
    confidence: str = "medium"


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


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
    key = re.sub(r"\bapis\b", "api", key)
    key = re.sub(r"\s+", " ", key).strip()
    return re.sub(r"\b([a-z0-9]+) \1\b", r"\1", key)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON file: {path}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"JSON root must be an object: {path}")
    return payload


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


def semantic_delivery_search_text(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(payload.get("didactic_text") or ""),
            json.dumps(payload.get("themes") or [], ensure_ascii=False),
            json.dumps(payload.get("technical_terms") or [], ensure_ascii=False),
            json.dumps(payload.get("technology_mentions") or [], ensure_ascii=False),
        ]
    )


def segment_records(transcription: dict[str, Any]) -> list[SegmentRecord]:
    raw_segments = transcription.get("segments")
    if not isinstance(raw_segments, list) or not raw_segments:
        raise SystemExit("Transcription JSON must contain a non-empty segments list.")

    records: list[SegmentRecord] = []
    cursor = 0
    for index, segment in enumerate(raw_segments):
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text") or "").strip()
        start = float(segment.get("start_seconds") or 0.0)
        end = float(segment.get("end_seconds") or start)
        char_start = cursor
        char_end = char_start + len(text)
        records.append(
            SegmentRecord(
                index=index,
                start_seconds=start,
                end_seconds=end,
                text=text,
                char_start=char_start,
                char_end=char_end,
            )
        )
        cursor = char_end + 1

    if not records:
        raise SystemExit("Transcription JSON contains no usable segments.")
    return records


def collect_default_candidates(
    *,
    merged_payload: dict[str, Any],
    transcription: dict[str, Any],
    suspicious_terms: list[str],
    include_unconfirmed_entities: bool,
    include_low_confidence: bool,
    include_rare_acronyms: bool,
    rare_acronym_max_raw_matches: int,
    max_auto_suspicions: int,
) -> list[AuditCandidate]:
    candidates: list[AuditCandidate] = []
    merged_text = merged_search_text(merged_payload)
    semantic_text = semantic_delivery_search_text(merged_payload)
    raw_text = str(transcription.get("text") or "")
    merged_key = canonical_entity_key(merged_text)
    raw_key = canonical_entity_key(raw_text)

    for term in suspicious_terms:
        normalized = canonical_entity_key(term)
        if normalized and normalized in merged_key:
            candidates.append(
                AuditCandidate(
                    issue_type="possible_transcription_error",
                    suspect_text=term,
                    reason="Termo explicitamente marcado para auditoria humana/sonora.",
                    source="explicit_suspicious_terms",
                    confidence="medium",
                )
            )

    if include_rare_acronyms:
        candidates.extend(
            collect_rare_acronym_candidates(
                merged_text=semantic_text,
                raw_text=raw_text,
                max_raw_matches=rare_acronym_max_raw_matches,
                max_candidates=max_auto_suspicions,
            )
        )

    if include_low_confidence:
        for collection_name, text_key in (
            ("technical_terms", "term"),
            ("technology_mentions", "name"),
        ):
            for item in merged_payload.get(collection_name) or []:
                if not isinstance(item, dict):
                    continue
                confidence = str(item.get("confidence") or "").lower()
                value = str(item.get(text_key) or "").strip()
                if value and confidence == "low":
                    candidates.append(
                        AuditCandidate(
                            issue_type="low_confidence_entity",
                            suspect_text=value,
                            reason=f"Entidade gerada com confidence=low em {collection_name}.",
                            source=collection_name,
                            confidence="low",
                        )
                    )

    if include_unconfirmed_entities:
        for collection_name, text_key in (
            ("technical_terms", "term"),
            ("technology_mentions", "name"),
        ):
            for item in merged_payload.get(collection_name) or []:
                if not isinstance(item, dict):
                    continue
                value = str(item.get(text_key) or "").strip()
                normalized = canonical_entity_key(value)
                if not normalized or normalized in raw_key:
                    continue
                candidates.append(
                    AuditCandidate(
                        issue_type="generated_entity_not_found_in_raw_text",
                        suspect_text=value,
                        reason=(
                            "Entidade aparece no resultado processado, mas nao foi "
                            "encontrada lexicalmente na transcricao bruta."
                        ),
                        source=collection_name,
                        confidence=str(item.get("confidence") or "medium").lower(),
                    )
                )

    return deduplicate_candidates(candidates)


def collect_rare_acronym_candidates(
    *,
    merged_text: str,
    raw_text: str,
    max_raw_matches: int,
    max_candidates: int,
) -> list[AuditCandidate]:
    seen: set[str] = set()
    candidates: list[AuditCandidate] = []
    for match in re.finditer(r"\b[A-Z][A-Z0-9]{1,9}\b", merged_text):
        acronym = match.group(0)
        if not any(char.isalpha() for char in acronym):
            continue
        if acronym in seen or acronym.upper() in DEFAULT_ACRONYM_ALLOWLIST:
            continue
        seen.add(acronym)

        raw_count = len(
            re.findall(rf"\b{re.escape(acronym)}\b", raw_text, flags=re.IGNORECASE)
        )
        if raw_count <= 0 or raw_count > max_raw_matches:
            continue

        candidates.append(
            AuditCandidate(
                issue_type="rare_acronym_audio_check",
                suspect_text=acronym,
                reason=(
                    "Sigla rara detectada no resultado processado e encontrada poucas "
                    "vezes na transcricao bruta; deve ser confirmada por audio."
                ),
                source="rare_acronym_policy",
                confidence="medium",
            )
        )
        if len(candidates) >= max_candidates:
            break
    return candidates


def collect_missing_coverage_candidates(merge_audit: dict[str, Any] | None) -> list[AuditCandidate]:
    if not merge_audit:
        return []

    report = merge_audit.get("coverage_report") or {}
    items = report.get("items")
    if not isinstance(items, list):
        return []

    candidates: list[AuditCandidate] = []
    for item in items:
        if not isinstance(item, dict) or item.get("found") is not False:
            continue
        term = str(item.get("term") or "").strip()
        if not term:
            continue
        candidates.append(
            AuditCandidate(
                issue_type="missing_coverage_anchor",
                suspect_text=term,
                reason=(
                    "Ancora de cobertura esperada nao foi encontrada no resultado "
                    "mesclado; deve ser conferida contra a transcricao segmentada."
                ),
                source="merge_audit.coverage_report",
                confidence="medium",
            )
        )
    return candidates


def deduplicate_candidates(candidates: list[AuditCandidate]) -> list[AuditCandidate]:
    seen: set[tuple[str, str]] = set()
    output: list[AuditCandidate] = []
    for candidate in candidates:
        key = (candidate.issue_type, canonical_entity_key(candidate.suspect_text))
        if not key[1] or key in seen:
            continue
        output.append(candidate)
        seen.add(key)
    return output


def find_occurrences(text: str, term: str, *, context_chars: int = 120) -> list[dict[str, Any]]:
    if not text or not term:
        return []

    pattern = re.compile(re.escape(term), flags=re.IGNORECASE)
    occurrences: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)
        occurrences.append(
            {
                "char_start": match.start(),
                "char_end": match.end(),
                "context": text[start:end].strip(),
            }
        )
        if len(occurrences) >= 20:
            break
    return occurrences


def find_segment_matches(
    segments: list[SegmentRecord],
    term: str,
    *,
    max_matches: int = 12,
) -> list[dict[str, Any]]:
    normalized_term = canonical_entity_key(term)
    if not normalized_term:
        return []

    matches: list[dict[str, Any]] = []
    for segment in segments:
        if normalized_term not in canonical_entity_key(segment.text):
            continue
        matches.append(segment_match_payload(segment))
        if len(matches) >= max_matches:
            break
    return matches


def segment_match_payload(segment: SegmentRecord) -> dict[str, Any]:
    return {
        "segment_index": segment.index,
        "start_seconds": round(segment.start_seconds, 3),
        "end_seconds": round(segment.end_seconds, 3),
        "text": segment.text,
    }


def clip_window(
    matches: list[dict[str, Any]],
    *,
    margin_seconds: float,
    duration_seconds: float | None,
) -> dict[str, Any] | None:
    if not matches:
        return None

    start = min(float(match["start_seconds"]) for match in matches)
    end = max(float(match["end_seconds"]) for match in matches)
    clip_start = max(0.0, start - margin_seconds)
    clip_end = end + margin_seconds
    if duration_seconds is not None:
        clip_end = min(duration_seconds, clip_end)
    if clip_end <= clip_start:
        clip_end = end

    return {
        "start_seconds": round(clip_start, 3),
        "end_seconds": round(clip_end, 3),
        "margin_seconds": margin_seconds,
        "source_match_start_seconds": round(start, 3),
        "source_match_end_seconds": round(end, 3),
    }


def clip_windows_for_matches(
    matches: list[dict[str, Any]],
    *,
    margin_seconds: float,
    duration_seconds: float | None,
    merge_gap_seconds: float = 1.0,
) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    seen: set[tuple[float, float]] = set()
    for match in matches:
        window = clip_window(
            [match],
            margin_seconds=margin_seconds,
            duration_seconds=duration_seconds,
        )
        if window is None:
            continue
        key = (float(window["start_seconds"]), float(window["end_seconds"]))
        if key in seen:
            continue
        windows.append(window)
        seen.add(key)
    return merge_overlapping_windows(windows, merge_gap_seconds=merge_gap_seconds)


def merge_overlapping_windows(
    windows: list[dict[str, Any]],
    *,
    merge_gap_seconds: float,
) -> list[dict[str, Any]]:
    if len(windows) <= 1:
        return windows

    sorted_windows = sorted(windows, key=lambda item: float(item["start_seconds"]))
    merged: list[dict[str, Any]] = []
    for window in sorted_windows:
        if not merged:
            merged.append(dict(window))
            continue

        previous = merged[-1]
        if float(window["start_seconds"]) > float(previous["end_seconds"]) + merge_gap_seconds:
            merged.append(dict(window))
            continue

        previous["end_seconds"] = round(
            max(float(previous["end_seconds"]), float(window["end_seconds"])),
            3,
        )
        previous["source_match_start_seconds"] = round(
            min(
                float(previous["source_match_start_seconds"]),
                float(window["source_match_start_seconds"]),
            ),
            3,
        )
        previous["source_match_end_seconds"] = round(
            max(
                float(previous["source_match_end_seconds"]),
                float(window["source_match_end_seconds"]),
            ),
            3,
        )
    return merged


def cut_audio_clip(*, audio_file: Path, output_file: Path, window: dict[str, Any]) -> bool:
    if shutil.which("ffmpeg") is None:
        return False

    output_file.parent.mkdir(parents=True, exist_ok=True)
    start = float(window["start_seconds"])
    end = float(window["end_seconds"])
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start:.3f}",
        "-to",
        f"{end:.3f}",
        "-i",
        str(audio_file),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_file),
    ]
    completed = subprocess.run(command, check=False)
    return completed.returncode == 0 and output_file.exists()


def transcribe_clip_with_e02_engine(
    *,
    clip_path: Path,
    filename: str,
    language: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    src_path = PROJECT_ROOT / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from schemas.transcriptions import TranscriptionMetadata
        from services.transcription_service import transcribe_audio
        from settings import get_settings

        transcription_metadata = TranscriptionMetadata(
            course=metadata.get("course"),
            discipline=metadata.get("discipline"),
            class_date=metadata.get("class_date"),
            class_title=metadata.get("class_title"),
            session_label=metadata.get("session_label"),
        )
        response = transcribe_audio(
            audio_bytes=clip_path.read_bytes(),
            filename=filename,
            language=language,
            metadata=transcription_metadata,
            settings=get_settings(),
        )
        payload = (
            response.model_dump()
            if hasattr(response, "model_dump")
            else response.dict()
        )
        return {
            "status": "pass",
            "text": payload.get("text"),
            "language": payload.get("language"),
            "duration_seconds": payload.get("duration_seconds"),
            "segments": payload.get("segments"),
            "engine": payload.get("engine"),
        }
    except Exception as exc:  # pragma: no cover - depends on local STT runtime.
        return {
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }


def write_clip_retranscription_artifacts(
    *,
    run_dir: Path,
    clip_path: Path,
    retranscription: dict[str, Any],
) -> dict[str, str] | None:
    if retranscription.get("status") != "pass":
        return None

    output_dir = run_dir / "clip_transcriptions"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = clip_path.stem
    json_path = output_dir / f"{stem}.json"
    text_path = output_dir / f"{stem}.txt"
    json_path.write_text(
        json.dumps(retranscription, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    text_path.write_text(str(retranscription.get("text") or "").strip() + "\n", encoding="utf-8")
    return {
        "json_path": str(json_path),
        "text_path": str(text_path),
    }


def retranscription_confirms_term(clips: list[dict[str, Any]], term: str) -> bool:
    normalized_term = canonical_entity_key(term)
    if not normalized_term:
        return False

    for clip in clips:
        retranscription = clip.get("retranscription") or {}
        if retranscription.get("status") != "pass":
            continue
        text = str(retranscription.get("text") or "")
        if normalized_term in canonical_entity_key(text):
            return True
    return False


def audit_conclusion(
    *,
    candidate: AuditCandidate,
    confirmed_by_clip_stt: bool,
    raw_matches: list[dict[str, Any]],
    transcribe_clips: bool,
) -> dict[str, Any]:
    if confirmed_by_clip_stt:
        canonical_candidate = KNOWN_CANONICAL_SPELLING_CANDIDATES.get(
            candidate.suspect_text.upper()
        )
        if canonical_candidate:
            return {
                "confirmed_by_clip_stt": True,
                "recommended_action": "review_canonical_spelling",
                "message": (
                    "O STT pontual confirmou uma forma lexical suspeita, mas ha "
                    f"candidato conhecido de grafia canonica: {canonical_candidate}. "
                    "Nao corrigir automaticamente sem regra de normalizacao ou revisao."
                ),
                "canonical_spelling_candidate": canonical_candidate,
            }
        if candidate.issue_type == "possible_transcription_error":
            action = "preserve_or_review_in_context"
            message = (
                "O STT pontual confirmou a presenca do termo no audio; nao corrigir "
                "por mera plausibilidade."
            )
        elif candidate.issue_type == "missing_coverage_anchor":
            action = "review_reinsertion_of_authorship"
            message = (
                "O STT pontual confirmou a ancora ausente; revisar se a autoria deve "
                "ser reinserida no artefato final."
            )
        else:
            action = "review_with_confirmed_audio_evidence"
            message = "O STT pontual confirmou a presenca do termo no audio."
        return {
            "confirmed_by_clip_stt": True,
            "recommended_action": action,
            "message": message,
        }

    if raw_matches and transcribe_clips:
        return {
            "confirmed_by_clip_stt": False,
            "recommended_action": "treat_as_probable_transcription_error_or_manual_review",
            "message": (
                "A transcricao segmentada encontrou o termo, mas o STT pontual nao "
                "confirmou lexicalmente; tratar como provavel erro de transcricao ou "
                "revisar o clipe manualmente."
            ),
        }

    if raw_matches:
        return {
            "confirmed_by_clip_stt": False,
            "recommended_action": "run_clip_retranscription",
            "message": (
                "A transcricao segmentada encontrou o termo; falta executar "
                "re-transcricao pontual do clipe."
            ),
        }

    return {
        "confirmed_by_clip_stt": False,
        "recommended_action": "inspect_raw_transcription_or_prompt_source",
        "message": "Nenhum segmento timestampado correspondente foi localizado.",
    }


def build_issues(
    *,
    merged_payload: dict[str, Any],
    transcription: dict[str, Any],
    merge_audit: dict[str, Any] | None,
    suspicious_terms: list[str],
    include_unconfirmed_entities: bool,
    include_low_confidence: bool,
    include_rare_acronyms: bool,
    rare_acronym_max_raw_matches: int,
    max_auto_suspicions: int,
    margin_seconds: float,
    run_dir: Path,
    audio_file: Path | None,
    make_clips: bool,
    transcribe_clips: bool,
) -> list[dict[str, Any]]:
    segments = segment_records(transcription)
    merged_text = merged_search_text(merged_payload)
    raw_text = str(transcription.get("text") or "")
    duration_seconds = transcription.get("duration_seconds")
    duration = float(duration_seconds) if duration_seconds is not None else None

    candidates = collect_default_candidates(
        merged_payload=merged_payload,
        transcription=transcription,
        suspicious_terms=suspicious_terms,
        include_unconfirmed_entities=include_unconfirmed_entities,
        include_low_confidence=include_low_confidence,
        include_rare_acronyms=include_rare_acronyms,
        rare_acronym_max_raw_matches=rare_acronym_max_raw_matches,
        max_auto_suspicions=max_auto_suspicions,
    )
    candidates.extend(collect_missing_coverage_candidates(merge_audit))
    candidates = deduplicate_candidates(candidates)

    issues: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        issue_id = f"audit-{index:03d}"
        raw_matches = find_segment_matches(segments, candidate.suspect_text)
        windows = clip_windows_for_matches(
            raw_matches,
            margin_seconds=margin_seconds,
            duration_seconds=duration,
        )
        primary_window = windows[0] if windows else None

        clip_plans: list[dict[str, Any]] = []
        for clip_index, window in enumerate(windows, start=1):
            clip_path = None
            clip_created = False
            retranscription = None
            retranscription_artifacts = None
            should_create_clip = make_clips or transcribe_clips
            if audio_file is not None and should_create_clip:
                output_file = (
                    run_dir
                    / "audio_clips"
                    / f"{issue_id}_{clip_index:02d}_{safe_filename(candidate.suspect_text)}.wav"
                )
                clip_created = cut_audio_clip(
                    audio_file=audio_file,
                    output_file=output_file,
                    window=window,
                )
                if clip_created:
                    clip_path = str(output_file)
                    if transcribe_clips:
                        retranscription = transcribe_clip_with_e02_engine(
                            clip_path=output_file,
                            filename=output_file.name,
                            language=str(transcription.get("language") or "pt-BR"),
                            metadata=merged_payload.get("metadata") or {},
                        )
                        retranscription_artifacts = write_clip_retranscription_artifacts(
                            run_dir=run_dir,
                            clip_path=output_file,
                            retranscription=retranscription,
                        )
            clip_plans.append(
                {
                    **window,
                    "audio_file": str(audio_file) if audio_file else None,
                    "clip_path": clip_path,
                    "clip_created": clip_created,
                    "retranscription": retranscription,
                    "retranscription_artifacts": retranscription_artifacts,
                }
            )

        confirmed_by_clip_stt = retranscription_confirms_term(
            clip_plans,
            candidate.suspect_text,
        )
        if confirmed_by_clip_stt:
            status = "verified_by_clip_retranscription"
        elif raw_matches and transcribe_clips:
            status = "not_confirmed_by_clip_retranscription"
        elif raw_matches:
            status = "needs_audio_verification"
        else:
            status = "not_found_in_segments"
        conclusion = audit_conclusion(
            candidate=candidate,
            confirmed_by_clip_stt=confirmed_by_clip_stt,
            raw_matches=raw_matches,
            transcribe_clips=transcribe_clips,
        )

        if primary_window is not None:
            primary_clip_plan = {
                **primary_window,
                "audio_file": str(audio_file) if audio_file else None,
                "clip_path": clip_plans[0]["clip_path"] if clip_plans else None,
                "clip_created": clip_plans[0]["clip_created"] if clip_plans else False,
                "retranscription": clip_plans[0]["retranscription"] if clip_plans else None,
                "retranscription_artifacts": (
                    clip_plans[0]["retranscription_artifacts"] if clip_plans else None
                ),
            }
        else:
            primary_clip_plan = None

        issues.append(
            {
                "issue_id": issue_id,
                "type": candidate.issue_type,
                "suspect_text": candidate.suspect_text,
                "reason": candidate.reason,
                "source": candidate.source,
                "confidence": candidate.confidence,
                "status": status,
                "audit_conclusion": conclusion,
                "merged_occurrences": find_occurrences(merged_text, candidate.suspect_text),
                "raw_text_occurrences": find_occurrences(raw_text, candidate.suspect_text),
                "raw_segment_matches": raw_matches,
                "clip_plan": primary_clip_plan,
                "clip_plans": clip_plans,
            }
        )

    return issues


def safe_filename(value: str) -> str:
    value = normalize_key(value).replace(" ", "-")
    return value[:60] or "suspect"


def severity_counts(issues: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        status = str(issue.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def write_outputs(
    *,
    run_dir: Path,
    merged_result_file: Path,
    transcription_json_file: Path,
    merge_audit_file: Path | None,
    audio_file: Path | None,
    issues: list[dict[str, Any]],
    settings: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "merged_result_file": str(merged_result_file),
            "transcription_json_file": str(transcription_json_file),
            "merge_audit_file": str(merge_audit_file) if merge_audit_file else None,
            "audio_file": str(audio_file) if audio_file else None,
            "strategy": "offline_deterministic_timestamp_audit",
            "settings": settings,
        },
        "summary": {
            "issues": len(issues),
            "status_counts": severity_counts(issues),
            "audio_clips_created": sum(
                1
                for issue in issues
                for clip in issue.get("clip_plans") or []
                if clip.get("clip_created")
            ),
            "clip_retranscriptions_passed": sum(
                1
                for issue in issues
                for clip in issue.get("clip_plans") or []
                if (clip.get("retranscription") or {}).get("status") == "pass"
            ),
            "clip_retranscriptions_failed": sum(
                1
                for issue in issues
                for clip in issue.get("clip_plans") or []
                if (clip.get("retranscription") or {}).get("status") == "error"
            ),
        },
        "issues": issues,
    }
    (run_dir / "audit_issues.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "README.md").write_text(
        readme_text(payload),
        encoding="utf-8",
    )
    (run_dir / "audit_resolution.md").write_text(
        resolution_markdown(payload),
        encoding="utf-8",
    )


def readme_text(payload: dict[str, Any]) -> str:
    metadata = payload["audit_metadata"]
    summary = payload["summary"]
    lines = [
        "# Auditoria Final E03 - Dossie de Suspeitas",
        "",
        "Artefato experimental offline. Este processo nao reescreve o texto final; ele apenas localiza suspeitas e prepara evidencias para verificacao pontual.",
        "",
        "## Entradas",
        "",
        f"- `merged_result_file`: `{metadata['merged_result_file']}`",
        f"- `transcription_json_file`: `{metadata['transcription_json_file']}`",
        f"- `merge_audit_file`: `{metadata['merge_audit_file']}`",
        f"- `audio_file`: `{metadata['audio_file']}`",
        "",
        "## Resultado",
        "",
        f"- `issues`: {summary['issues']}",
        f"- `status_counts`: `{json.dumps(summary['status_counts'], ensure_ascii=False)}`",
        f"- `audio_clips_created`: {summary['audio_clips_created']}",
        f"- `clip_retranscriptions_passed`: {summary['clip_retranscriptions_passed']}",
        f"- `clip_retranscriptions_failed`: {summary['clip_retranscriptions_failed']}",
        "",
        "## Arquivos",
        "",
        "- `audit_issues.json`: dossie estruturado das suspeitas, segmentos e planos de clipe.",
        "- `audit_resolution.md`: sintese humana das conclusoes e acoes recomendadas.",
        "- `audio_clips/`: clipes WAV quando `--audio-file` e `--make-clips` forem usados.",
        "- `clip_transcriptions/`: transcricoes pontuais dos clipes quando `--transcribe-clips` for usado.",
        "",
    ]
    return "\n".join(lines)


def resolution_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Resolucao da Auditoria Final E03",
        "",
        "Este arquivo resume as conclusoes auditaveis. Ele nao altera o texto final automaticamente.",
        "",
        "## Sumario",
        "",
        f"- `issues`: {payload['summary']['issues']}",
        f"- `status_counts`: `{json.dumps(payload['summary']['status_counts'], ensure_ascii=False)}`",
        f"- `audio_clips_created`: {payload['summary']['audio_clips_created']}",
        f"- `clip_retranscriptions_passed`: {payload['summary']['clip_retranscriptions_passed']}",
        f"- `clip_retranscriptions_failed`: {payload['summary']['clip_retranscriptions_failed']}",
        "",
        "## Suspeitas",
        "",
    ]
    for issue in payload.get("issues") or []:
        conclusion = issue.get("audit_conclusion") or {}
        lines.extend(
            [
                f"### {issue.get('issue_id')} - {issue.get('suspect_text')}",
                "",
                f"- `type`: `{issue.get('type')}`",
                f"- `status`: `{issue.get('status')}`",
                f"- `recommended_action`: `{conclusion.get('recommended_action')}`",
                f"- `message`: {conclusion.get('message')}",
                f"- `raw_segment_matches`: {len(issue.get('raw_segment_matches') or [])}",
                f"- `clip_plans`: {len(issue.get('clip_plans') or [])}",
                "",
            ]
        )
        for clip in issue.get("clip_plans") or []:
            artifacts = clip.get("retranscription_artifacts") or {}
            retranscription = clip.get("retranscription") or {}
            text = str(retranscription.get("text") or "").strip()
            if len(text) > 700:
                text = text[:700].rstrip() + "..."
            lines.extend(
                [
                    f"- Janela: `{clip.get('start_seconds')}` -> `{clip.get('end_seconds')}`",
                    f"  - Clip: `{clip.get('clip_path')}`",
                    f"  - Transcricao: `{artifacts.get('text_path')}`",
                    f"  - Texto STT: {text}",
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a merged E03 result against timestamped transcription segments.",
    )
    parser.add_argument("--merged-result-file", required=True, type=Path)
    parser.add_argument("--transcription-json-file", required=True, type=Path)
    parser.add_argument("--merge-audit-file", type=Path)
    parser.add_argument("--audio-file", type=Path)
    parser.add_argument("--case-name", default="e03-final-audit")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--issue-term", action="append", default=[])
    parser.add_argument("--issue-terms-file", type=Path)
    parser.add_argument("--clip-margin-seconds", type=float, default=10.0)
    parser.add_argument("--include-unconfirmed-entities", action="store_true")
    parser.add_argument("--include-low-confidence", action="store_true", default=True)
    parser.add_argument("--no-low-confidence", dest="include_low_confidence", action="store_false")
    parser.add_argument("--include-rare-acronyms", action="store_true", default=True)
    parser.add_argument("--no-rare-acronyms", dest="include_rare_acronyms", action="store_false")
    parser.add_argument("--rare-acronym-max-raw-matches", type=int, default=6)
    parser.add_argument("--max-auto-suspicions", type=int, default=12)
    parser.add_argument("--make-clips", action="store_true")
    parser.add_argument(
        "--transcribe-clips",
        action="store_true",
        help="Create clips and re-transcribe each one with the same STT engine used by E02.",
    )
    return parser.parse_args(argv)


def issue_terms_from_args(args: argparse.Namespace) -> list[str]:
    terms = list(DEFAULT_SUSPICIOUS_TERMS)
    terms.extend(args.issue_term or [])
    if args.issue_terms_file is not None:
        terms.extend(
            line.strip()
            for line in args.issue_terms_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    output: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = canonical_entity_key(term)
        if not key or key in seen:
            continue
        output.append(term)
        seen.add(key)
    return output


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    merged_result_file = args.merged_result_file.resolve()
    transcription_json_file = args.transcription_json_file.resolve()
    merge_audit_file = args.merge_audit_file.resolve() if args.merge_audit_file else None
    audio_file = args.audio_file.resolve() if args.audio_file else None

    if not merged_result_file.exists():
        raise SystemExit(f"Merged result file not found: {merged_result_file}")
    if not transcription_json_file.exists():
        raise SystemExit(f"Transcription JSON file not found: {transcription_json_file}")
    if merge_audit_file is not None and not merge_audit_file.exists():
        raise SystemExit(f"Merge audit file not found: {merge_audit_file}")
    if audio_file is not None and not audio_file.exists():
        raise SystemExit(f"Audio file not found: {audio_file}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.output_dir.resolve() / f"{timestamp}_{safe_filename(args.case_name)}"

    suspicious_terms = issue_terms_from_args(args)
    merged_payload = load_json(merged_result_file)
    transcription = load_json(transcription_json_file)
    merge_audit = load_json(merge_audit_file) if merge_audit_file else None

    settings = {
        "suspicious_terms": suspicious_terms,
        "include_unconfirmed_entities": args.include_unconfirmed_entities,
        "include_low_confidence": args.include_low_confidence,
        "include_rare_acronyms": args.include_rare_acronyms,
        "rare_acronym_max_raw_matches": args.rare_acronym_max_raw_matches,
        "max_auto_suspicions": args.max_auto_suspicions,
        "clip_margin_seconds": args.clip_margin_seconds,
        "make_clips": args.make_clips,
        "transcribe_clips": args.transcribe_clips,
    }
    issues = build_issues(
        merged_payload=merged_payload,
        transcription=transcription,
        merge_audit=merge_audit,
        suspicious_terms=suspicious_terms,
        include_unconfirmed_entities=args.include_unconfirmed_entities,
        include_low_confidence=args.include_low_confidence,
        include_rare_acronyms=args.include_rare_acronyms,
        rare_acronym_max_raw_matches=args.rare_acronym_max_raw_matches,
        max_auto_suspicions=args.max_auto_suspicions,
        margin_seconds=args.clip_margin_seconds,
        run_dir=run_dir,
        audio_file=audio_file,
        make_clips=args.make_clips,
        transcribe_clips=args.transcribe_clips,
    )
    write_outputs(
        run_dir=run_dir,
        merged_result_file=merged_result_file,
        transcription_json_file=transcription_json_file,
        merge_audit_file=merge_audit_file,
        audio_file=audio_file,
        issues=issues,
        settings=settings,
    )

    print(f"Audit run: {run_dir}")
    print(f"Issues: {len(issues)}")
    print(f"Status counts: {severity_counts(issues)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
