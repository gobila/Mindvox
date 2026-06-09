from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex
from tempfile import NamedTemporaryFile
from typing import Any

from schemas.transcriptions import (
    TranscriptionEngine,
    TranscriptionMetadata,
    TranscriptionResponse,
    TranscriptionSegment,
)
from settings import Settings


PUBLIC_MODEL_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)?$"
)
SENSITIVE_MODEL_MARKERS = (
    ".env",
    "authorization",
    "bearer",
    "password",
    "private",
    "secret",
    "token",
)
REDACTED_MODEL_LABEL = "configured-model"
MODEL_CACHE_DIR = Path.home() / ".cache" / "mindvox" / "mlx-whisper"


class AudioDecodeError(Exception):
    """Raised when an accepted audio file cannot be decoded."""


class TranscriptionServiceUnavailableError(Exception):
    """Raised when the configured transcription engine cannot run."""


def transcribe_audio(
    *,
    audio_bytes: bytes,
    filename: str,
    language: str,
    metadata: TranscriptionMetadata,
    settings: Settings,
) -> TranscriptionResponse:
    if settings.transcription_mode == "contract":
        return _contract_transcription(language=language, metadata=metadata, settings=settings)

    return _real_transcription(
        audio_bytes=audio_bytes,
        filename=filename,
        language=language,
        metadata=metadata,
        settings=settings,
    )


def _contract_transcription(
    *,
    language: str,
    metadata: TranscriptionMetadata,
    settings: Settings,
) -> TranscriptionResponse:
    return TranscriptionResponse(
        transcription_id=_new_transcription_id(),
        text="Contract-mode transcription for automated tests and API demonstrations.",
        language=language,
        duration_seconds=None,
        segments=[],
        metadata=metadata,
        engine=TranscriptionEngine(
            name="contract-stub",
            model=_public_engine_model(settings.transcription_model),
            version="contract-mode",
        ),
    )


def _real_transcription(
    *,
    audio_bytes: bytes,
    filename: str,
    language: str,
    metadata: TranscriptionMetadata,
    settings: Settings,
) -> TranscriptionResponse:
    try:
        import mlx_whisper  # type: ignore[import-not-found]
    except ImportError as exc:
        raise TranscriptionServiceUnavailableError(
            "The real transcription engine is not installed."
        ) from exc

    try:
        model_reference = _model_reference_for_mlx_whisper(settings.transcription_model)
        engine_language = _language_for_mlx_whisper(language)
        suffix = "." + filename.rsplit(".", maxsplit=1)[-1].lower()
        with NamedTemporaryFile(suffix=suffix) as audio_file:
            audio_file.write(audio_bytes)
            audio_file.flush()
            result = mlx_whisper.transcribe(
                audio_file.name,
                path_or_hf_repo=model_reference,
                language=engine_language,
            )
    except Exception as exc:  # pragma: no cover - depends on the external STT engine.
        raise AudioDecodeError("Audio file cannot be decoded.") from exc

    return _response_from_engine_result(
        result=result,
        language=language,
        metadata=metadata,
        settings=settings,
    )


def _response_from_engine_result(
    *,
    result: dict[str, Any],
    language: str,
    metadata: TranscriptionMetadata,
    settings: Settings,
) -> TranscriptionResponse:
    raw_segments = result.get("segments") or []
    segments = [
        TranscriptionSegment(
            start_seconds=float(segment.get("start", 0.0)),
            end_seconds=float(segment.get("end", 0.0)),
            text=str(segment.get("text", "")),
            speaker_label=None,
        )
        for segment in raw_segments
    ]

    return TranscriptionResponse(
        transcription_id=_new_transcription_id(),
        text=str(result.get("text", "")),
        language=_response_language(
            engine_language=result.get("language"),
            requested_language=language,
        ),
        duration_seconds=_duration_from_segments(segments),
        segments=segments,
        metadata=metadata,
        engine=TranscriptionEngine(
            name="mlx-whisper",
            model=_public_engine_model(settings.transcription_model),
            version="unknown",
        ),
    )


def _duration_from_segments(segments: list[TranscriptionSegment]) -> float | None:
    if not segments:
        return None

    return max(segment.end_seconds for segment in segments)


def _model_reference_for_mlx_whisper(model: str) -> str:
    from huggingface_hub import snapshot_download

    model_path = Path(model).expanduser()
    if model_path.exists():
        return str(_prepare_mlx_whisper_model_layout(model_path))

    snapshot_path = Path(snapshot_download(repo_id=model))
    return str(_prepare_mlx_whisper_model_layout(snapshot_path))


def _prepare_mlx_whisper_model_layout(model_path: Path) -> Path:
    if (model_path / "weights.safetensors").exists() or (model_path / "weights.npz").exists():
        return model_path

    model_safetensors = model_path / "model.safetensors"
    if not model_safetensors.exists():
        return model_path

    prepared_path = MODEL_CACHE_DIR / _safe_model_cache_name(model_path)
    prepared_path.mkdir(parents=True, exist_ok=True)

    for child in model_path.iterdir():
        target = prepared_path / child.name
        if not target.exists():
            target.symlink_to(child.resolve())

    weights_target = prepared_path / "weights.safetensors"
    if not weights_target.exists():
        weights_target.symlink_to(model_safetensors.resolve())

    return prepared_path


def _safe_model_cache_name(model_path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(model_path.resolve())).strip("-")


def _language_for_mlx_whisper(language: str) -> str:
    return language.split("-", maxsplit=1)[0].lower()


def _response_language(*, engine_language: Any, requested_language: str) -> str:
    if not engine_language:
        return requested_language

    normalized_engine_language = str(engine_language)
    if requested_language.lower().startswith(f"{normalized_engine_language.lower()}-"):
        return requested_language

    return normalized_engine_language


def _new_transcription_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"tr_{timestamp}_{token_hex(4)}"


def _public_engine_model(model: str) -> str:
    normalized = model.strip()
    lower_model = normalized.lower()

    if not normalized:
        return REDACTED_MODEL_LABEL

    is_path_like = (
        normalized.startswith(("/", "~", "."))
        or "\\" in normalized
        or "://" in normalized
    )
    has_sensitive_marker = any(
        marker in lower_model for marker in SENSITIVE_MODEL_MARKERS
    )

    if (
        is_path_like
        or has_sensitive_marker
        or PUBLIC_MODEL_PATTERN.fullmatch(normalized) is None
    ):
        return REDACTED_MODEL_LABEL

    return normalized
