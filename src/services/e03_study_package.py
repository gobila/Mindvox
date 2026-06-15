from __future__ import annotations

import json
from pathlib import Path

from schemas.processed_transcriptions import (
    ConceptCandidate,
    MemoryManifest,
    OperationalAnchors,
    ProcessedTranscriptionResponse,
    StudyPackage,
    StudyPackageAuditReport,
    StudyPackageExportTargets,
    StudyPackageMetadata,
    StudyPackageRawTranscription,
)
from services.artifact_naming import build_artifact_stem
from services.e03_course_context import active_course
from services.e03_vault_exporter import StudentVaultExportError, export_study_package_to_vault
from settings import DEFAULT_E03_STUDY_PACKAGE_OUTPUT_DIR, Settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class StudyPackageArtifactWriteError(Exception):
    """Raised when the E03 Study Package cannot be persisted."""


def build_study_package(response: ProcessedTranscriptionResponse) -> StudyPackage:
    return StudyPackage(
        metadata=_study_package_metadata(response),
        source=response.source,
        raw_transcription=StudyPackageRawTranscription(
            text=response.raw_text,
            artifact_path=(
                response.artifact_locations.technical_json_path
                if response.artifact_locations
                else None
            ),
        ),
        didactic_text=response.didactic_text,
        themes=response.themes,
        technical_terms=response.technical_terms,
        technology_mentions=response.technology_mentions,
        operational_anchors=_operational_anchors(response),
        concept_candidates=_concept_candidates(response),
        audit_report=StudyPackageAuditReport(
            status="passed",
            processing_notes_count=len(response.processing_notes),
            themes_count=len(response.themes),
            technical_terms_count=len(response.technical_terms),
            technology_mentions_count=len(response.technology_mentions),
            notes=response.processing_notes,
        ),
        memory_manifest=_memory_manifest(response),
        export_targets=StudyPackageExportTargets(
            local_json_path=(
                response.artifact_locations.technical_json_path
                if response.artifact_locations
                else None
            ),
            local_markdown_path=(
                response.artifact_locations.human_text_path
                if response.artifact_locations
                else None
            ),
        ),
    )


def attach_study_package(
    response: ProcessedTranscriptionResponse,
) -> ProcessedTranscriptionResponse:
    response.study_package = build_study_package(response)
    return response


def save_study_package_artifact(
    response: ProcessedTranscriptionResponse,
    *,
    settings: Settings,
) -> Path | None:
    if response.study_package is None:
        return None

    output_dir = _resolve_output_dir(settings.e03_study_package_output_dir)
    artifact_stem = build_artifact_stem(
        artifact_id=response.processed_transcription_id,
        metadata=response.metadata,
    )
    filename = f"{artifact_stem}.json"
    path = output_dir / filename

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        _export_to_obsidian_if_configured(response, settings=settings)
        _write_text_atomic(
            path,
            json.dumps(
                response.study_package.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ),
        )
    except OSError as exc:
        raise StudyPackageArtifactWriteError(
            "E03 Study Package artifact could not be written."
        ) from exc

    return path


def _export_to_obsidian_if_configured(
    response: ProcessedTranscriptionResponse,
    *,
    settings: Settings,
) -> None:
    if not settings.e03_obsidian_export_enabled or response.study_package is None:
        return

    course = active_course(settings=settings)
    if course is None or course.vault_path is None:
        return

    try:
        export = export_study_package_to_vault(
            study_package=response.study_package,
            vault_path=course.vault_path,
        )
    except StudentVaultExportError as exc:
        raise StudyPackageArtifactWriteError(
            "E03 Study Package could not be exported to the optional Student Vault."
        ) from exc

    response.study_package.export_targets.obsidian_vault_path = str(export.vault_path)


def _study_package_metadata(
    response: ProcessedTranscriptionResponse,
) -> StudyPackageMetadata:
    course_name = response.metadata.course
    class_number, session_number = _class_and_session_from_label(
        response.metadata.session_label
    )
    return StudyPackageMetadata(
        course_id=_slug_or_none(course_name),
        course_name=course_name,
        discipline=response.metadata.discipline,
        class_date=response.metadata.class_date,
        class_title=response.metadata.class_title,
        session_label=response.metadata.session_label,
        class_number=class_number,
        session_number=session_number,
    )


def _operational_anchors(
    response: ProcessedTranscriptionResponse,
) -> OperationalAnchors:
    links = sorted(set(_extract_urls(response.raw_text) + _extract_urls(response.didactic_text)))
    return OperationalAnchors(links=links)


def _concept_candidates(
    response: ProcessedTranscriptionResponse,
) -> list[ConceptCandidate]:
    candidates: list[ConceptCandidate] = []
    seen: set[str] = set()

    for theme in response.themes:
        key = theme.title.strip().casefold()
        if key and key not in seen:
            seen.add(key)
            candidates.append(
                ConceptCandidate(
                    title=theme.title,
                    source="theme",
                    summary=theme.summary,
                    confidence="medium",
                )
            )

    for term in response.technical_terms:
        key = term.term.strip().casefold()
        if key and key not in seen:
            seen.add(key)
            candidates.append(
                ConceptCandidate(
                    title=term.term,
                    source="technical_term",
                    summary=term.explanation,
                    confidence=term.confidence,
                )
            )

    return candidates


def _memory_manifest(response: ProcessedTranscriptionResponse) -> MemoryManifest:
    relational_entities = [
        "course",
        "discipline",
        "class",
        "session",
        "theme",
        "technical_term",
        "technology_mention",
        "operational_anchor",
    ]
    vector_candidates = ["didactic_text"]
    if response.themes:
        vector_candidates.append("themes")
    if response.technical_terms:
        vector_candidates.append("technical_terms")

    return MemoryManifest(
        relational_entities=relational_entities,
        vector_candidates=vector_candidates,
    )


def _extract_urls(text: str) -> list[str]:
    import re

    return re.findall(r"https?://[^\s)\]>\"']+", text)


def _class_and_session_from_label(
    session_label: str | None,
) -> tuple[str | None, str | None]:
    if not session_label:
        return None, None

    import re

    class_session = re.search(
        r"a(?:ula-?)?(\d+).*?s(?:essao-?)?(\d+)$",
        session_label.strip(),
        re.IGNORECASE,
    )
    if class_session:
        return class_session.group(1), class_session.group(2)

    match = re.search(r"s(?:essao-?)?(\d+)$", session_label.strip(), re.IGNORECASE)
    if match:
        return None, match.group(1)

    return None, None


def _slug_or_none(value: str | None) -> str | None:
    if not value:
        return None

    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    return slug or None


def _resolve_output_dir(configured_output_dir: str) -> Path:
    cleaned = configured_output_dir.strip() or DEFAULT_E03_STUDY_PACKAGE_OUTPUT_DIR
    output_dir = Path(cleaned).expanduser()
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    return output_dir


def _write_text_atomic(path: Path, content: str) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)
