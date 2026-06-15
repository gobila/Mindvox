#!/usr/bin/env python3
"""Run E03 post-processing over semantic chunks one by one.

This is a local experiment runner. It does not change the public E03 endpoint
and does not merge chunk outputs into a canonical response.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from schemas.processed_transcriptions import Source  # noqa: E402
from schemas.transcriptions import TranscriptionMetadata  # noqa: E402
from services.postprocessing_service import (  # noqa: E402
    PostprocessingInvalidOutputError,
    PostprocessingServiceUnavailableError,
    PostprocessingTimeoutError,
    process_transcription,
)
from settings import Settings, get_settings  # noqa: E402


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".benchmarks" / "e03_chunk_postprocessing"


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE lines without overriding existing environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_chunks(path: Path, method: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    try:
        chunks = payload["methods"][method]["chunks"]
    except KeyError as exc:
        available = ", ".join(sorted(payload.get("methods", {}).keys()))
        raise SystemExit(
            f"Method {method!r} not found in chunks file. Available: {available}"
        ) from exc
    if not isinstance(chunks, list) or not chunks:
        raise SystemExit("Chunks file contains no chunks for selected method.")
    return chunks


def load_pre_audit_context(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload, dict) else None
    issues = payload.get("issues") if isinstance(payload, dict) else None
    corrections = payload.get("canonical_replacements") if isinstance(payload, dict) else None
    if not isinstance(summary, dict) or not isinstance(issues, list):
        raise SystemExit(f"Invalid pre-audit JSON file: {path}")
    return {
        "file": str(path),
        "summary": summary,
        "issues": issues,
        "canonical_replacements": corrections if isinstance(corrections, list) else [],
    }


def pre_audit_header(context: dict[str, Any] | None) -> str:
    if not context:
        return ""

    summary = context["summary"]
    issues = context["issues"]
    replacements = context["canonical_replacements"]
    unresolved = [
        issue
        for issue in issues
        if str(issue.get("status")) in {
            "not_confirmed_by_clip_retranscription",
            "needs_audio_verification",
            "canonical_replacement_candidate",
        }
    ]
    unresolved_terms = [
        str(issue.get("suspect_text") or "").strip()
        for issue in unresolved
        if str(issue.get("suspect_text") or "").strip()
    ]
    replacement_lines = [
        f"- {item.get('suspect_text')} -> {item.get('replacement')} ({item.get('status')})"
        for item in replacements
        if item.get("suspect_text") and item.get("replacement")
    ]
    if not replacement_lines:
        replacement_lines = ["- none"]

    if unresolved_terms:
        unresolved_line = ", ".join(unresolved_terms)
        confidence_line = (
            "Remaining suspicious transcription terms were detected but are not "
            "verified class content. Do not promote them to didactic_text, themes, "
            "technical_terms, or technology_mentions unless the transcript body gives "
            "independent, clear semantic evidence. Mention unresolved terms only in "
            f"processing_notes when useful: {unresolved_line}."
        )
    else:
        confidence_line = (
            "No remaining suspicious transcription terms were detected after "
            "the pre-audit. Do not add new uncertainty notes about audited "
            "names, acronyms, or technical terms by plausibility alone."
        )

    status_counts = json.dumps(summary.get("status_counts") or {}, ensure_ascii=False)
    return "\n".join(
        [
            "<<< Mindvox pre-audit context >>>",
            "This block is operational metadata, not classroom content.",
            "The transcript body below was generated after E02 raw pre-audit.",
            f"Pre-audit issues: {summary.get('issues', 0)}.",
            f"Pre-audit status counts: {status_counts}.",
            f"Canonical replacements applied before this prompt: {summary.get('canonical_replacements', 0)}.",
            "Canonical replacements:",
            *replacement_lines,
            confidence_line,
            "Do not copy this pre-audit block into the final JSON deliveries.",
            "<<< End Mindvox pre-audit context >>>",
            "",
        ]
    )


def chunk_source() -> Source:
    return Source(
        input_origin="raw_text",
        raw_text_origin="provided_by_client",
        transcription=None,
    )


def process_chunk(
    *,
    chunk: dict[str, Any],
    language: str,
    settings: Settings,
    pre_audit_context: dict[str, Any] | None,
) -> dict[str, Any]:
    chunk_id = str(chunk["chunk_id"])
    chunk_text = str(chunk["text"]).strip()
    raw_text = f"{pre_audit_header(pre_audit_context)}{chunk_text}".strip()
    started = time.monotonic()
    result: dict[str, Any] = {
        "chunk_id": chunk_id,
        "segment_indexes": chunk.get("segment_indexes", []),
        "segment_indexes_display": chunk.get("segment_indexes_display"),
        "input_chars": len(chunk_text),
        "prompt_input_chars": len(raw_text),
        "input_estimated_tokens": chunk.get("estimated_tokens"),
        "input_top_terms": chunk.get("top_terms", []),
        "input_anchors": chunk.get("anchors", []),
        "pre_audit_context_applied": pre_audit_context is not None,
        "status": "error",
        "elapsed_seconds": 0.0,
        "didactic_chars": 0,
        "themes_count": 0,
        "technical_terms_count": 0,
        "technology_mentions_count": 0,
        "processing_notes_count": 0,
        "error_type": None,
        "error": None,
        "response": None,
    }

    try:
        response = process_transcription(
            raw_text=raw_text,
            input_type="raw_text",
            language=language,
            metadata=TranscriptionMetadata(),
            source=chunk_source(),
            settings=settings,
        )
        result.update(
            {
                "status": "pass",
                "didactic_chars": len(response.didactic_text),
                "themes_count": len(response.themes),
                "technical_terms_count": len(response.technical_terms),
                "technology_mentions_count": len(response.technology_mentions),
                "processing_notes_count": len(response.processing_notes),
                "response": response.model_dump(),
            }
        )
    except (
        PostprocessingInvalidOutputError,
        PostprocessingServiceUnavailableError,
        PostprocessingTimeoutError,
    ) as exc:
        result.update(
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
    finally:
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)

    return result


def write_outputs(
    *,
    run_dir: Path,
    chunks_file: Path,
    method: str,
    settings: Settings,
    results: list[dict[str, Any]],
    pre_audit_context: dict[str, Any] | None,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks_file": str(chunks_file),
        "method": method,
        "settings": {
            "postprocessing_mode": settings.postprocessing_mode,
            "llm_provider": settings.llm_provider,
            "llm_base_url": settings.llm_base_url,
            "llm_model": settings.llm_model,
            "llm_max_output_tokens": settings.llm_max_output_tokens,
            "llm_timeout_seconds": settings.llm_timeout_seconds,
        },
        "pre_audit": pre_audit_run_metadata(pre_audit_context),
        "summary": summarize(results),
        "results": results,
    }
    (run_dir / "chunk_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# E03 Chunk Post-Processing Benchmark",
        "",
        f"- `chunks_file`: `{chunks_file}`",
        f"- `method`: `{method}`",
        f"- `postprocessing_mode`: `{settings.postprocessing_mode}`",
        f"- `llm_model`: `{settings.llm_model}`",
        f"- `pre_audit`: `{json.dumps(payload['pre_audit'], ensure_ascii=False)}`",
        f"- `summary`: `{json.dumps(payload['summary'], ensure_ascii=False)}`",
        "",
        "| Chunk | Status | Input chars | Didactic chars | Themes | Terms | Tech | Time | Error |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            f"`{result['chunk_id']}` | "
            f"`{result['status']}` | "
            f"`{result['input_chars']}` | "
            f"`{result['didactic_chars']}` | "
            f"`{result['themes_count']}` | "
            f"`{result['technical_terms_count']}` | "
            f"`{result['technology_mentions_count']}` | "
            f"`{result['elapsed_seconds']}` | "
            f"{_markdown_cell(result.get('error') or '')} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is an experimental local benchmark and may contain real transcript text in `chunk_results.json`.",
            "- Keep `.benchmarks/` out of Git.",
            "- This runner processes chunks independently and does not perform final merge/deduplication.",
        ]
    )
    (run_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_partial_outputs(
    *,
    run_dir: Path,
    chunks_file: Path,
    method: str,
    settings: Settings,
    results: list[dict[str, Any]],
    pre_audit_context: dict[str, Any] | None,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks_file": str(chunks_file),
        "method": method,
        "settings": {
            "postprocessing_mode": settings.postprocessing_mode,
            "llm_provider": settings.llm_provider,
            "llm_base_url": settings.llm_base_url,
            "llm_model": settings.llm_model,
            "llm_max_output_tokens": settings.llm_max_output_tokens,
            "llm_timeout_seconds": settings.llm_timeout_seconds,
        },
        "pre_audit": pre_audit_run_metadata(pre_audit_context),
        "summary": summarize(results),
        "results": results,
    }
    (run_dir / "chunk_results.partial.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [result for result in results if result["status"] == "pass"]
    errored = [result for result in results if result["status"] != "pass"]
    return {
        "chunk_count": len(results),
        "passed": len(passed),
        "errored": len(errored),
        "total_elapsed_seconds": round(sum(result["elapsed_seconds"] for result in results), 3),
        "total_didactic_chars": sum(result["didactic_chars"] for result in passed),
        "total_themes": sum(result["themes_count"] for result in passed),
        "total_technical_terms": sum(result["technical_terms_count"] for result in passed),
        "total_technology_mentions": sum(result["technology_mentions_count"] for result in passed),
    }


def pre_audit_run_metadata(context: dict[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {"applied": False}
    summary = context["summary"]
    unresolved = [
        issue
        for issue in context["issues"]
        if str(issue.get("status")) in {
            "not_confirmed_by_clip_retranscription",
            "needs_audio_verification",
            "canonical_replacement_candidate",
        }
    ]
    return {
        "applied": True,
        "file": context["file"],
        "issues": summary.get("issues", 0),
        "status_counts": summary.get("status_counts") or {},
        "canonical_replacements": summary.get("canonical_replacements", 0),
        "unresolved_suspicions": len(unresolved),
    }


def _markdown_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value).replace("|", "/")[:120]


def safe_case_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "chunk-run"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run E03 over semantic chunks one by one.")
    parser.add_argument("--chunks-file", required=True, help="Path to semantic_chunk_transcript.py chunks.json.")
    parser.add_argument("--method", default="tfidf", help="Method key inside chunks.json.")
    parser.add_argument("--case-name", default="e03-chunk-postprocessing", help="Human-readable run name.")
    parser.add_argument("--language", default="pt-BR", help="Language label sent to E03.")
    parser.add_argument("--limit", type=int, default=0, help="Process only the first N chunks; 0 means all.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for local benchmark outputs.")
    parser.add_argument(
        "--pre-audit-file",
        default=None,
        help="Optional raw_transcription_audit.json used to add pre-audit context to each chunk prompt.",
    )
    return parser


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    args = build_parser().parse_args()
    chunks_file = Path(args.chunks_file)
    chunks = load_chunks(chunks_file, args.method)
    pre_audit_context = load_pre_audit_context(
        Path(args.pre_audit_file) if args.pre_audit_file else None
    )
    if args.limit > 0:
        chunks = chunks[: args.limit]

    settings = get_settings()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.output_dir) / f"{timestamp}_{safe_case_name(args.case_name)}"

    print(f"E03 chunk post-processing case: {args.case_name}", flush=True)
    print(f"Chunks file: {chunks_file}", flush=True)
    print(f"Method: {args.method}", flush=True)
    print(f"Chunks selected: {len(chunks)}", flush=True)
    print(f"Mode: {settings.postprocessing_mode}", flush=True)
    print(f"Model: {settings.llm_model}", flush=True)
    print(
        f"Pre-audit context: {json.dumps(pre_audit_run_metadata(pre_audit_context), ensure_ascii=False)}",
        flush=True,
    )

    results = []
    for index, chunk in enumerate(chunks, start=1):
        print(f"Running {index}/{len(chunks)}: {chunk['chunk_id']}", flush=True)
        result = process_chunk(
            chunk=chunk,
            language=args.language,
            settings=settings,
            pre_audit_context=pre_audit_context,
        )
        results.append(result)
        print(
            f"  status={result['status']} time={result['elapsed_seconds']}s "
            f"didactic_chars={result['didactic_chars']} themes={result['themes_count']} "
            f"terms={result['technical_terms_count']} tech={result['technology_mentions_count']}",
            flush=True,
        )
        write_partial_outputs(
            run_dir=run_dir,
            chunks_file=chunks_file,
            method=args.method,
            settings=settings,
            results=results,
            pre_audit_context=pre_audit_context,
        )

    write_outputs(
        run_dir=run_dir,
        chunks_file=chunks_file,
        method=args.method,
        settings=settings,
        results=results,
        pre_audit_context=pre_audit_context,
    )
    print(f"Summary: {json.dumps(summarize(results), ensure_ascii=False)}", flush=True)
    print(f"Saved: {run_dir / 'chunk_results.json'}", flush=True)
    print(f"Saved: {run_dir / 'README.md'}", flush=True)
    return 0 if all(result["status"] == "pass" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
