from pydantic import BaseModel, Field


class TranscriptionSegment(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    text: str
    speaker_label: str | None = None


class TranscriptionMetadata(BaseModel):
    course: str | None = None
    discipline: str | None = None
    class_date: str | None = None
    class_title: str | None = None
    session_label: str | None = None


class TranscriptionEngine(BaseModel):
    name: str
    model: str
    version: str


class ArtifactLocations(BaseModel):
    human_text_path: str | None = Field(
        default=None,
        description=(
            "Human-readable artifact path. In local defaults, E02 writes raw "
            "transcription text here and E03 writes processed Markdown here."
        ),
    )
    technical_json_path: str | None = Field(
        default=None,
        description=(
            "Technical JSON artifact path for integrations, audit, queue, or "
            "future processing. Absolute local paths are not exposed."
        ),
    )


class TranscriptionResponse(BaseModel):
    transcription_id: str
    text: str
    language: str
    duration_seconds: float | None = None
    segments: list[TranscriptionSegment]
    metadata: TranscriptionMetadata
    engine: TranscriptionEngine
    artifact_locations: ArtifactLocations | None = None
