from __future__ import annotations

import json
import re
from pathlib import Path

from schemas.transcriptions import (
    ArtifactLocations,
    TranscriptionResponse,
    TranscriptionSegment,
)
from services.artifact_naming import (
    ArtifactNameError,
    build_artifact_stem,
)
from settings import (
    DEFAULT_TRANSCRIPTION_OUTPUT_DIR,
    DEFAULT_TRANSCRIPTION_TEXT_OUTPUT_DIR,
    Settings,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TranscriptionArtifactWriteError(Exception):
    """Raised when a generated transcription cannot be persisted to disk."""


def save_transcription_artifacts(
    transcription: TranscriptionResponse,
    *,
    settings: Settings,
) -> tuple[Path, Path]:
    output_dir = _resolve_output_dir(
        settings.transcription_output_dir,
        default=DEFAULT_TRANSCRIPTION_OUTPUT_DIR,
    )
    text_output_dir = _resolve_output_dir(
        settings.transcription_text_output_dir,
        default=DEFAULT_TRANSCRIPTION_TEXT_OUTPUT_DIR,
    )
    base_name = _artifact_stem(transcription)
    json_path = output_dir / f"{base_name}.json"
    text_path = text_output_dir / f"{base_name}.txt"

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        text_output_dir.mkdir(parents=True, exist_ok=True)
        _write_text_atomic(
            text_path,
            _render_human_transcription_text(transcription),
        )
        _write_text_atomic(
            json_path,
            json.dumps(
                transcription.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ),
        )
    except OSError as exc:
        raise TranscriptionArtifactWriteError(
            "Generated transcription artifacts could not be written."
        ) from exc

    return json_path, text_path


def build_transcription_artifact_locations(
    transcription: TranscriptionResponse,
    *,
    settings: Settings,
) -> ArtifactLocations:
    base_name = _artifact_stem(transcription)
    return ArtifactLocations(
        human_text_path=_public_artifact_path(
            settings.transcription_text_output_dir,
            default=DEFAULT_TRANSCRIPTION_TEXT_OUTPUT_DIR,
            filename=f"{base_name}.txt",
            env_name="MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR",
        ),
        technical_json_path=_public_artifact_path(
            settings.transcription_output_dir,
            default=DEFAULT_TRANSCRIPTION_OUTPUT_DIR,
            filename=f"{base_name}.json",
            env_name="MINDVOX_TRANSCRIPTION_OUTPUT_DIR",
        ),
    )


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


def _artifact_stem(transcription: TranscriptionResponse) -> str:
    try:
        return build_artifact_stem(
            artifact_id=transcription.transcription_id,
            metadata=transcription.metadata,
        )
    except ArtifactNameError as exc:
        raise TranscriptionArtifactWriteError(
            "Unsafe transcription artifact name."
        ) from exc


def _render_human_transcription_text(transcription: TranscriptionResponse) -> str:
    if transcription.segments:
        return _paragraphs_from_segments(transcription.segments)

    return _paragraphs_from_plain_text(transcription.text)


def _paragraphs_from_segments(segments: list[TranscriptionSegment]) -> str:
    paragraphs: list[str] = []
    current = ""
    previous_end: float | None = None

    for segment in segments:
        segment_text = _normalize_inline_whitespace(segment.text)
        if not segment_text:
            continue

        if _should_start_new_paragraph(
            current=current,
            previous_end=previous_end,
            segment=segment,
        ):
            paragraphs.append(current)
            current = segment_text
        else:
            current = _join_segment_text(current, segment_text)

        previous_end = segment.end_seconds

    if current:
        paragraphs.append(current)

    return "\n\n".join(paragraphs)


def _paragraphs_from_plain_text(text: str) -> str:
    normalized = _normalize_inline_whitespace(text)
    if len(normalized) <= 1400:
        return normalized

    paragraphs: list[str] = []
    current = ""
    for sentence in _split_sentence_like_units(normalized):
        candidate = _join_segment_text(current, sentence)
        if current and len(candidate) > 1200:
            paragraphs.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        paragraphs.append(current)

    return "\n\n".join(paragraphs)


def _should_start_new_paragraph(
    *,
    current: str,
    previous_end: float | None,
    segment: TranscriptionSegment,
) -> bool:
    if not current:
        return False

    pause_seconds = segment.start_seconds - previous_end if previous_end is not None else 0
    if pause_seconds >= 6:
        return True

    if len(current) >= 900:
        return True

    return len(current) >= 520 and current.rstrip().endswith((".", "?", "!", ":"))


def _join_segment_text(current: str, addition: str) -> str:
    if not current:
        return addition

    return f"{current.rstrip()} {addition.lstrip()}"


def _split_sentence_like_units(text: str) -> list[str]:
    return [
        chunk.strip()
        for chunk in re.split(r"(?<=[.!?:])\s+", text)
        if chunk.strip()
    ]


def _normalize_inline_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _write_text_atomic(path: Path, content: str) -> None:
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)
