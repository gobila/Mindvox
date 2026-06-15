from typing import Literal

from pydantic import BaseModel, Field

from schemas.transcriptions import (
    ArtifactLocations,
    TranscriptionEngine,
    TranscriptionMetadata,
)

Confidence = Literal["low", "medium", "high"]
TechnologyCategory = Literal[
    "framework",
    "library",
    "platform",
    "service",
    "provider",
    "protocol",
    "language",
    "database",
    "infrastructure",
    "tool",
    "api",
]


class Theme(BaseModel):
    order: int = Field(ge=1)
    title: str
    summary: str
    key_points: list[str]
    semantic_role: str
    evidence: str | None = None


class TechnicalTerm(BaseModel):
    term: str
    normalized_from: list[str] = Field(default_factory=list)
    explanation: str | None = None
    confidence: Confidence
    evidence: str | None = None


class TechnologyMention(BaseModel):
    name: str
    category: TechnologyCategory
    context: str
    importance: Confidence
    normalized_from: list[str] = Field(default_factory=list)
    confidence: Confidence
    evidence: str | None = None


class ProcessingNote(BaseModel):
    type: str
    message: str


class SourceTranscription(BaseModel):
    transcription_id: str
    duration_seconds: float | None = None
    segments_count: int = Field(ge=0)
    transcription_engine: TranscriptionEngine


class Source(BaseModel):
    input_origin: Literal["audio", "raw_text"]
    raw_text_origin: Literal["generated_by_transcription_service", "provided_by_client"]
    transcription: SourceTranscription | None = None


class ProcessingEngine(BaseModel):
    mode: Literal["contract", "local", "provider"]
    name: str
    model: str
    version: str


class StudyPackageMetadata(BaseModel):
    course_id: str | None = None
    course_name: str | None = None
    institution: str | None = None
    discipline: str | None = None
    professor: str | None = None
    class_number: str | None = None
    class_date: str | None = None
    class_title: str | None = None
    session_number: str | None = None
    session_label: str | None = None


class StudyPackageRawTranscription(BaseModel):
    text: str
    artifact_path: str | None = None


class OperationalAnchors(BaseModel):
    links: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    assignments: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    contacts: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)


class ConceptCandidate(BaseModel):
    title: str
    source: str
    summary: str | None = None
    confidence: Confidence = "medium"


class StudyPackageAuditReport(BaseModel):
    status: str
    processing_notes_count: int = Field(ge=0)
    themes_count: int = Field(ge=0)
    technical_terms_count: int = Field(ge=0)
    technology_mentions_count: int = Field(ge=0)
    notes: list[ProcessingNote] = Field(default_factory=list)


class MemoryManifest(BaseModel):
    relational_target: Literal["sqlite"] = "sqlite"
    relational_entities: list[str] = Field(default_factory=list)
    vector_candidates: list[str] = Field(default_factory=list)


class StudyPackageExportTargets(BaseModel):
    local_json_path: str | None = None
    local_markdown_path: str | None = None
    obsidian_vault_path: str | None = None


class StudyPackage(BaseModel):
    metadata: StudyPackageMetadata
    source: Source
    raw_transcription: StudyPackageRawTranscription
    didactic_text: str
    themes: list[Theme]
    technical_terms: list[TechnicalTerm]
    technology_mentions: list[TechnologyMention]
    operational_anchors: OperationalAnchors = Field(default_factory=OperationalAnchors)
    concept_candidates: list[ConceptCandidate] = Field(default_factory=list)
    audit_report: StudyPackageAuditReport
    memory_manifest: MemoryManifest
    export_targets: StudyPackageExportTargets = Field(
        default_factory=StudyPackageExportTargets
    )


class ProcessedTranscriptionResponse(BaseModel):
    processed_transcription_id: str
    input_type: Literal["audio", "raw_text"]
    language: str
    raw_text: str
    didactic_text: str
    themes: list[Theme]
    technical_terms: list[TechnicalTerm]
    technology_mentions: list[TechnologyMention]
    processing_notes: list[ProcessingNote]
    metadata: TranscriptionMetadata
    source: Source
    processing_engine: ProcessingEngine
    artifact_locations: ArtifactLocations | None = None
    study_package: StudyPackage | None = None
