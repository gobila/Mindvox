from __future__ import annotations

import json
from pathlib import Path
from secrets import token_hex
from typing import Any

from schemas.processed_transcriptions import ProcessedTranscriptionResponse
from schemas.transcriptions import ArtifactLocations
from services.artifact_naming import (
    ArtifactNameError,
    build_artifact_stem,
    build_human_title,
    require_safe_artifact_id,
)
from settings import (
    DEFAULT_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR,
    DEFAULT_PROCESSED_TRANSCRIPTION_OUTPUT_DIR,
    DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR,
    DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR,
    Settings,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ProcessedTranscriptionArtifactWriteError(Exception):
    """Raised when processed transcription artifacts cannot be persisted."""


def save_processed_transcription_artifacts(
    response: ProcessedTranscriptionResponse,
    *,
    settings: Settings,
) -> tuple[Path, Path]:
    output_dir = _resolve_output_dir(
        settings.processed_transcription_output_dir,
        default=DEFAULT_PROCESSED_TRANSCRIPTION_OUTPUT_DIR,
    )
    markdown_output_dir = _resolve_output_dir(
        settings.processed_transcription_markdown_output_dir,
        default=DEFAULT_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR,
    )
    base_name = _artifact_stem(response)
    json_path = output_dir / f"{base_name}.json"
    markdown_path = markdown_output_dir / f"{base_name}.md"

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_output_dir.mkdir(parents=True, exist_ok=True)
        _write_text_atomic(
            json_path,
            json.dumps(
                response.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ),
        )
        _write_text_atomic(markdown_path, _render_markdown_artifact(response))
    except OSError as exc:
        raise ProcessedTranscriptionArtifactWriteError(
            "Processed transcription artifact could not be written."
        ) from exc

    return json_path, markdown_path


def build_processed_transcription_artifact_locations(
    response: ProcessedTranscriptionResponse,
    *,
    settings: Settings,
) -> ArtifactLocations:
    base_name = _artifact_stem(response)
    return ArtifactLocations(
        human_text_path=_public_artifact_path(
            settings.processed_transcription_markdown_output_dir,
            default=DEFAULT_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR,
            filename=f"{base_name}.md",
            env_name="MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR",
        ),
        technical_json_path=_public_artifact_path(
            settings.processed_transcription_output_dir,
            default=DEFAULT_PROCESSED_TRANSCRIPTION_OUTPUT_DIR,
            filename=f"{base_name}.json",
            env_name="MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR",
        ),
    )


def save_rejected_postprocessing_artifacts(
    *,
    raw_text: str,
    input_type: str,
    language: str,
    metadata,
    source,
    settings: Settings,
    error: Exception,
    rejected_payload: Any | None,
    attempt: int,
    max_attempts: int,
    runtime_snapshot: dict[str, Any] | None = None,
    job_id: str | None = None,
) -> dict[str, str]:
    output_dir = _resolve_output_dir(
        settings.processed_transcription_rejected_output_dir,
        default=DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR,
    )
    markdown_output_dir = _resolve_output_dir(
        settings.processed_transcription_rejected_markdown_output_dir,
        default=DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR,
    )
    artifact_id = _rejected_artifact_id(job_id=job_id, attempt=attempt)
    base_name = _safe_rejected_artifact_stem(
        artifact_id=artifact_id,
        metadata=metadata,
    )
    json_path = output_dir / f"{base_name}.json"
    markdown_path = markdown_output_dir / f"{base_name}.md"
    payload = _rejected_payload_dump(rejected_payload)
    report = _build_rejected_report(
        raw_text=raw_text,
        input_type=input_type,
        language=language,
        metadata=metadata,
        source=source,
        error=error,
        rejected_payload=payload,
        runtime_snapshot=runtime_snapshot,
        attempt=attempt,
        max_attempts=max_attempts,
        artifact_id=artifact_id,
    )

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_output_dir.mkdir(parents=True, exist_ok=True)
        _write_text_atomic(
            json_path,
            json.dumps(report, ensure_ascii=False, indent=2),
        )
        _write_text_atomic(
            markdown_path,
            _render_rejected_markdown_report(report),
        )
    except OSError as exc:
        raise ProcessedTranscriptionArtifactWriteError(
            "Rejected post-processing artifact could not be written."
        ) from exc

    return {
        "technical_json_path": _public_artifact_path(
            settings.processed_transcription_rejected_output_dir,
            default=DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR,
            filename=json_path.name,
            env_name="MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR",
        ),
        "human_report_path": _public_artifact_path(
            settings.processed_transcription_rejected_markdown_output_dir,
            default=DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR,
            filename=markdown_path.name,
            env_name="MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR",
        ),
    }


def _render_markdown_artifact(response: ProcessedTranscriptionResponse) -> str:
    lines = [
        "# "
        + build_human_title(
            default_title="Mindvox E03 Processed Transcription",
            metadata=response.metadata,
        ),
        "",
        f"- Processed transcription ID: `{response.processed_transcription_id}`",
        f"- Input type: `{response.input_type}`",
        f"- Language: `{response.language}`",
        f"- Processing mode: `{response.processing_engine.mode}`",
        f"- Model: `{response.processing_engine.model}`",
        "",
    ]
    metadata_lines = _metadata_lines(response)
    if metadata_lines:
        lines.extend(["## Class Metadata", "", *metadata_lines, ""])

    lines.extend(
        [
            "## Didactic Text",
            "",
            response.didactic_text.strip(),
            "",
            "## Themes",
            "",
        ]
    )

    for theme in response.themes:
        lines.extend(
            [
                f"### {theme.order}. {theme.title}",
                "",
                theme.summary,
                "",
            ]
        )
        if theme.key_points:
            lines.append("Key points:")
            for key_point in theme.key_points:
                lines.append(f"- {key_point}")
            lines.append("")
        lines.append(f"Semantic role: `{theme.semantic_role}`")
        if theme.evidence:
            lines.extend(["", f"Evidence: {theme.evidence}"])
        lines.append("")

    lines.extend(["## Technical Terms", ""])
    if response.technical_terms:
        for term in response.technical_terms:
            explanation = f": {term.explanation}" if term.explanation else ""
            lines.append(f"- **{term.term}** (`{term.confidence}`){explanation}")
    else:
        lines.append("- No technical terms were extracted.")
    lines.append("")

    lines.extend(["## Technology Mentions", ""])
    if response.technology_mentions:
        for mention in response.technology_mentions:
            lines.append(
                f"- **{mention.name}** (`{mention.category}`, "
                f"importance: `{mention.importance}`, "
                f"confidence: `{mention.confidence}`): {mention.context}"
            )
    else:
        lines.append("- No technology mentions were extracted.")
    lines.append("")

    lines.extend(["## Processing Notes", ""])
    for note in response.processing_notes:
        lines.append(f"- `{note.type}`: {note.message}")
    lines.append("")

    lines.extend(
        [
            "## Audit Note",
            "",
            "The raw transcription remains preserved in the JSON artifact and in the E02 raw transcription artifacts.",
            "",
        ]
    )

    return "\n".join(lines)


def _resolve_output_dir(configured_output_dir: str, *, default: str) -> Path:
    cleaned = configured_output_dir.strip()
    if not cleaned:
        cleaned = default

    output_dir = Path(cleaned).expanduser()
    if output_dir.is_absolute():
        return output_dir

    return PROJECT_ROOT / output_dir


def _public_artifact_path(
    configured_output_dir: str,
    *,
    default: str,
    filename: str,
    env_name: str,
) -> str:
    cleaned = configured_output_dir.strip() or default
    output_dir = Path(cleaned).expanduser()
    if output_dir.is_absolute():
        return f"${env_name}/{filename}"

    return f"{cleaned.rstrip('/')}/{filename}"


def _metadata_lines(response: ProcessedTranscriptionResponse) -> list[str]:
    metadata = response.metadata
    fields = [
        ("Course", metadata.course),
        ("Discipline", metadata.discipline),
        ("Class date", metadata.class_date),
        ("Class title", metadata.class_title),
        ("Session", metadata.session_label),
    ]
    return [f"- {label}: `{value}`" for label, value in fields if value]


def _artifact_stem(response: ProcessedTranscriptionResponse) -> str:
    try:
        return build_artifact_stem(
            artifact_id=response.processed_transcription_id,
            metadata=response.metadata,
        )
    except ArtifactNameError as exc:
        raise ProcessedTranscriptionArtifactWriteError(
            "Unsafe processed transcription artifact name."
        ) from exc


def _safe_rejected_artifact_stem(*, artifact_id: str, metadata) -> str:
    try:
        return build_artifact_stem(artifact_id=artifact_id, metadata=metadata)
    except ArtifactNameError as exc:
        raise ProcessedTranscriptionArtifactWriteError(
            "Unsafe rejected post-processing artifact name."
        ) from exc


def _rejected_artifact_id(*, job_id: str | None, attempt: int) -> str:
    safe_job_id = job_id or f"manual_{token_hex(4)}"
    try:
        require_safe_artifact_id(safe_job_id)
    except ArtifactNameError:
        safe_job_id = f"manual_{token_hex(4)}"
    return f"{safe_job_id}_rejected_attempt-{attempt}"


def _rejected_payload_dump(rejected_payload: Any | None) -> dict[str, Any] | None:
    if rejected_payload is None:
        return None
    if hasattr(rejected_payload, "model_dump"):
        return rejected_payload.model_dump(mode="json")
    if isinstance(rejected_payload, dict):
        return rejected_payload
    return {"repr": repr(rejected_payload)}


def _build_rejected_report(
    *,
    raw_text: str,
    input_type: str,
    language: str,
    metadata,
    source,
    error: Exception,
    rejected_payload: dict[str, Any] | None,
    runtime_snapshot: dict[str, Any] | None,
    attempt: int,
    max_attempts: int,
    artifact_id: str,
) -> dict[str, Any]:
    didactic_text = ""
    themes: list[Any] = []
    processing_notes: list[Any] = []
    if rejected_payload:
        didactic_text = str(rejected_payload.get("didactic_text") or "")
        themes = list(rejected_payload.get("themes") or [])
        processing_notes = list(rejected_payload.get("processing_notes") or [])

    raw_chars = len(raw_text.strip())
    didactic_chars = len(didactic_text.strip())
    compression_ratio = didactic_chars / raw_chars if raw_chars else 0
    return {
        "status": "rejected_by_semantic_coverage_gate",
        "artifact_id": artifact_id,
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "retry_hint": getattr(error, "retry_hint", None),
        "attempt": attempt,
        "max_attempts": max_attempts,
        "will_retry": attempt < max_attempts,
        "input_type": input_type,
        "language": language,
        "metadata": metadata.model_dump(mode="json"),
        "source": source.model_dump(mode="json") if source is not None else None,
        "metrics": {
            "raw_text_chars": raw_chars,
            "didactic_text_chars": didactic_chars,
            "didactic_to_raw_ratio": round(compression_ratio, 6),
            "themes_count": len(themes),
            "processing_notes_count": len(processing_notes),
        },
        "runtime_snapshot": runtime_snapshot or {},
        "raw_text_excerpt": raw_text[:4000],
        "rejected_payload": rejected_payload,
    }


def _render_rejected_markdown_report(report: dict[str, Any]) -> str:
    metadata = report["metadata"]
    metrics = report["metrics"]
    rejected_payload = report.get("rejected_payload") or {}
    lines = [
        "# Mindvox E03 Rejected Post-processing Output",
        "",
        f"- Status: `{report['status']}`",
        f"- Artifact ID: `{report['artifact_id']}`",
        f"- Error: `{report['error_type']}`",
        f"- Attempt: `{report['attempt']}` of `{report['max_attempts']}`",
        f"- Will retry: `{report['will_retry']}`",
        f"- Language: `{report['language']}`",
        "",
        "## Class Metadata",
        "",
    ]
    for key in ("course", "discipline", "class_date", "class_title", "session_label"):
        value = metadata.get(key)
        if value:
            lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Rejection Reason",
            "",
            str(report.get("retry_hint") or report.get("error_message") or ""),
            "",
            "## Runtime Snapshot",
            "",
        ]
    )
    for key, value in (report.get("runtime_snapshot") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- Raw text characters: `{metrics['raw_text_chars']}`",
            f"- Didactic text characters: `{metrics['didactic_text_chars']}`",
            f"- Didactic/raw ratio: `{metrics['didactic_to_raw_ratio']}`",
            f"- Themes count: `{metrics['themes_count']}`",
            f"- Processing notes count: `{metrics['processing_notes_count']}`",
            "",
            "## Rejected Didactic Text",
            "",
            str(rejected_payload.get("didactic_text") or "No rejected didactic text was available."),
            "",
            "## Rejected Themes",
            "",
        ]
    )
    themes = rejected_payload.get("themes") or []
    if themes:
        for index, theme in enumerate(themes, start=1):
            title = theme.get("title") if isinstance(theme, dict) else str(theme)
            summary = theme.get("summary", "") if isinstance(theme, dict) else ""
            lines.extend([f"### {index}. {title}", "", str(summary), ""])
    else:
        lines.append("- No rejected themes were available.")
        lines.append("")
    lines.extend(
        [
            "## Raw Text Excerpt",
            "",
            str(report.get("raw_text_excerpt") or ""),
            "",
        ]
    )
    return "\n".join(lines)


def _write_text_atomic(path: Path, content: str) -> None:
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)
