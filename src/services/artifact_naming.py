from __future__ import annotations

import re
import unicodedata

from schemas.transcriptions import TranscriptionMetadata


SAFE_ARTIFACT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
SAFE_ARTIFACT_STEM_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
MAX_ARTIFACT_LABEL_CHARS = 96


class ArtifactNameError(Exception):
    """Raised when an artifact name cannot be made safe."""


def build_artifact_stem(*, artifact_id: str, metadata: TranscriptionMetadata) -> str:
    safe_id = require_safe_artifact_id(artifact_id)
    label = _metadata_slug(metadata)
    if label is None:
        return safe_id

    stem = f"{label}_{safe_id}"
    if not SAFE_ARTIFACT_STEM_PATTERN.fullmatch(stem):
        raise ArtifactNameError("Unsafe artifact stem.")

    return stem


def build_human_title(
    *,
    default_title: str,
    metadata: TranscriptionMetadata,
) -> str:
    parts: list[str] = []
    if metadata.class_date:
        parts.append(metadata.class_date)
    if metadata.class_title:
        parts.append(metadata.class_title)
    elif metadata.session_label:
        parts.append(metadata.session_label)
    elif metadata.discipline:
        parts.append(metadata.discipline)
    elif metadata.course:
        parts.append(metadata.course)

    if metadata.class_title and metadata.session_label:
        parts.append(metadata.session_label)

    return " - ".join(parts) if parts else default_title


def require_safe_artifact_id(artifact_id: str) -> str:
    if not SAFE_ARTIFACT_ID_PATTERN.fullmatch(artifact_id):
        raise ArtifactNameError("Unsafe artifact id.")

    return artifact_id


def _metadata_slug(metadata: TranscriptionMetadata) -> str | None:
    parts = [metadata.class_date]
    if metadata.class_title:
        parts.extend([metadata.class_title, metadata.session_label])
    elif metadata.session_label:
        parts.append(metadata.session_label)
    elif metadata.discipline:
        parts.append(metadata.discipline)
    elif metadata.course:
        parts.append(metadata.course)

    slugs = [_slugify(part) for part in parts if part]
    slugs = [slug for slug in slugs if slug]
    if not slugs:
        return None

    label = "-".join(slugs)
    return label[:MAX_ARTIFACT_LABEL_CHARS].rstrip("-_.") or None


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-{2,}", "-", slug)
