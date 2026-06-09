import os
from dataclasses import dataclass


DEFAULT_MAX_UPLOAD_MB = 500
DEFAULT_TRANSCRIPTION_MODEL = "mlx-community/whisper-large-v3-turbo-fp16"


@dataclass(frozen=True)
class Settings:
    api_token: str | None
    max_upload_mb: int
    transcription_mode: str
    transcription_model: str


def get_settings() -> Settings:
    max_upload_mb = _read_positive_int(
        "MINDVOX_MAX_UPLOAD_MB",
        default=DEFAULT_MAX_UPLOAD_MB,
    )

    return Settings(
        api_token=os.getenv("MINDVOX_API_TOKEN"),
        max_upload_mb=max_upload_mb,
        transcription_mode=os.getenv("MINDVOX_TRANSCRIPTION_MODE", "real"),
        transcription_model=os.getenv(
            "MINDVOX_TRANSCRIPTION_MODEL",
            DEFAULT_TRANSCRIPTION_MODEL,
        ),
    )


def _read_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    if value < 0:
        return default

    return value
