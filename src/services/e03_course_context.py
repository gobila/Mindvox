from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from settings import DEFAULT_E03_ACTIVE_COURSE_STORE, Settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class CourseContextError(Exception):
    """Raised when the E03 course context cannot be read or written."""


class CourseRecord(BaseModel):
    course_id: str
    course_name: str
    institution: str | None = None
    vault_path: str | None = None


class CourseContextState(BaseModel):
    active_course_id: str | None = None
    courses: list[CourseRecord] = Field(default_factory=list)


def load_course_context(*, settings: Settings) -> CourseContextState:
    path = _store_path(settings)
    if not path.exists():
        return CourseContextState()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return CourseContextState.model_validate(payload)
    except (OSError, ValueError, ValidationError) as exc:
        raise CourseContextError("E03 course context could not be loaded.") from exc


def save_course_context(
    state: CourseContextState,
    *,
    settings: Settings,
) -> Path:
    path = _store_path(settings)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_text_atomic(
            path,
            json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2),
        )
    except OSError as exc:
        raise CourseContextError("E03 course context could not be saved.") from exc

    return path


def upsert_course(
    *,
    course_name: str,
    settings: Settings,
    course_id: str | None = None,
    institution: str | None = None,
    vault_path: str | None = None,
    make_active: bool = True,
) -> CourseContextState:
    cleaned_name = _clean_required(course_name, "course_name")
    cleaned_id = _clean_course_id(course_id or cleaned_name)
    state = load_course_context(settings=settings)
    cleaned_institution = _clean_optional(institution)
    cleaned_vault_path = _clean_optional(vault_path)

    replaced = False
    courses: list[CourseRecord] = []
    for existing in state.courses:
        if existing.course_id == cleaned_id:
            courses.append(
                CourseRecord(
                    course_id=cleaned_id,
                    course_name=cleaned_name,
                    institution=cleaned_institution or existing.institution,
                    vault_path=cleaned_vault_path or existing.vault_path,
                )
            )
            replaced = True
        else:
            courses.append(existing)
    if not replaced:
        courses.append(
            CourseRecord(
                course_id=cleaned_id,
                course_name=cleaned_name,
                institution=cleaned_institution,
                vault_path=cleaned_vault_path,
            )
        )

    courses.sort(key=lambda course: course.course_name.casefold())
    state = CourseContextState(
        active_course_id=cleaned_id if make_active else state.active_course_id,
        courses=courses,
    )
    save_course_context(state, settings=settings)
    return state


def set_active_course(*, course_id: str, settings: Settings) -> CourseContextState:
    cleaned_id = _clean_course_id(course_id)
    state = load_course_context(settings=settings)
    if all(course.course_id != cleaned_id for course in state.courses):
        raise CourseContextError("Active course must reference a known course.")

    state.active_course_id = cleaned_id
    save_course_context(state, settings=settings)
    return state


def active_course(*, settings: Settings) -> CourseRecord | None:
    state = load_course_context(settings=settings)
    if state.active_course_id is None:
        return None

    for course in state.courses:
        if course.course_id == state.active_course_id:
            return course

    return None


def _store_path(settings: Settings) -> Path:
    configured = settings.e03_active_course_store.strip()
    if not configured:
        configured = DEFAULT_E03_ACTIVE_COURSE_STORE

    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _clean_required(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise CourseContextError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_course_id(value: str) -> str:
    cleaned = _clean_required(value, "course_id")
    normalized = unicodedata.normalize("NFKD", cleaned)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    if not slug:
        raise CourseContextError("course_id is invalid.")
    return slug[:80]


def _write_text_atomic(path: Path, content: str) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)
