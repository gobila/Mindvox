import re
from datetime import date

from fastapi import HTTPException, status

from schemas.transcriptions import TranscriptionMetadata


MAX_COURSE_LENGTH = 160
MAX_DISCIPLINE_LENGTH = 120
MAX_CLASS_TITLE_LENGTH = 200
MAX_SESSION_LABEL_LENGTH = 40
SESSION_LABEL_PATTERN = re.compile(r"^[\w][\w -]{0,39}$")
SWAGGER_STRING_PLACEHOLDER = "string"


def build_transcription_metadata(
    *,
    course: str | None,
    discipline: str | None,
    class_date: str | None,
    class_title: str | None,
    session_label: str | None,
) -> TranscriptionMetadata:
    cleaned_course = clean_limited_optional_text(
        field_name="course",
        value=course,
        max_length=MAX_COURSE_LENGTH,
    )
    cleaned_discipline = clean_limited_optional_text(
        field_name="discipline",
        value=discipline,
        max_length=MAX_DISCIPLINE_LENGTH,
    )
    cleaned_class_date = clean_optional_text(class_date)
    cleaned_class_title = clean_limited_optional_text(
        field_name="class_title",
        value=class_title,
        max_length=MAX_CLASS_TITLE_LENGTH,
    )
    cleaned_session_label = clean_optional_text(session_label)

    if cleaned_class_date:
        try:
            date.fromisoformat(cleaned_class_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="class_date must use YYYY-MM-DD.",
            ) from exc

    if cleaned_session_label and (
        len(cleaned_session_label) > MAX_SESSION_LABEL_LENGTH
        or SESSION_LABEL_PATTERN.fullmatch(cleaned_session_label) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="session_label must be short and use simple characters.",
        )

    return TranscriptionMetadata(
        course=cleaned_course,
        discipline=cleaned_discipline,
        class_date=cleaned_class_date,
        class_title=cleaned_class_title,
        session_label=cleaned_session_label,
    )


def clean_limited_optional_text(
    *,
    field_name: str,
    value: str | None,
    max_length: int,
) -> str | None:
    cleaned = clean_optional_text(value)
    if cleaned is None:
        return None

    if len(cleaned) > max_length:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{field_name} must be {max_length} characters or fewer.",
        )

    return cleaned


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if cleaned == SWAGGER_STRING_PLACEHOLDER:
        return None

    return cleaned or None
