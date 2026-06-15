import logging
import re
import secrets
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.processed_transcriptions import (
    ProcessedTranscriptionResponse,
    Source,
    SourceTranscription,
)
from schemas.transcriptions import TranscriptionMetadata
from routers.endpoint_security import require_secure_transport_for_public_request
from routers.metadata_validation import (
    MAX_CLASS_TITLE_LENGTH,
    MAX_COURSE_LENGTH,
    MAX_DISCIPLINE_LENGTH,
    build_transcription_metadata,
    clean_optional_text,
)
from routers.upload_limits import read_upload_with_limit
from services.postprocessing_service import (
    PostprocessingInsufficientCoverageError,
    PostprocessingInvalidOutputError,
    PostprocessingServiceUnavailableError,
    PostprocessingTimeoutError,
    build_postprocessing_runtime_snapshot,
    process_transcription,
)
from services.processed_transcription_artifacts import (
    ProcessedTranscriptionArtifactWriteError,
    save_rejected_postprocessing_artifacts,
)
from services.processed_transcription_queue import (
    ProcessedTranscriptionQueueWriteError,
    complete_generated_transcription_job,
    enqueue_generated_transcription_job,
    mark_generated_transcription_job_failed,
)
from services.e03_study_package import StudyPackageArtifactWriteError
from services.transcription_service import (
    AudioDecodeError,
    TranscriptionServiceUnavailableError,
    transcribe_audio,
)
from services.transcription_artifacts import (
    TranscriptionArtifactWriteError,
    build_transcription_artifact_locations,
    save_transcription_artifacts,
)
from settings import Settings, get_settings


router = APIRouter(tags=["processed-transcriptions"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger("mindvox.processed_transcriptions")
logger.addHandler(logging.NullHandler())

SUPPORTED_EXTENSIONS = {".wav", ".m4a"}
SUPPORTED_CONTENT_TYPES = {
    ".wav": {"audio/wav", "audio/x-wav", "audio/vnd.wave"},
    ".m4a": {"audio/mp4", "audio/m4a", "audio/x-m4a"},
}
SUPPORTED_RAW_TEXT_FILE_EXTENSIONS = {".txt"}
SUPPORTED_RAW_TEXT_FILE_CONTENT_TYPES = {"application/octet-stream", "text/plain"}
PROCESSING_PROFILES = {"study_notes"}
LANGUAGE_PATTERN = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")
PREPARED_RAW_TEXT_FILENAME_PATTERN = re.compile(
    r"^(?P<class_date>\d{4}-\d{2}-\d{2})-"
    r"(?P<body>.+)-aula-(?P<class_number>\d+)-sessao-(?P<session>\d+)\.txt$",
    flags=re.IGNORECASE,
)


class InputType(str, Enum):
    AUDIO = "audio"
    RAW_TEXT = "raw_text"
    RAW_TEXT_FILE = "raw_text_file"


INPUT_TYPE_ALIASES = {InputType.RAW_TEXT_FILE: InputType.RAW_TEXT}


def get_authenticated_settings(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Settings:
    started_at = perf_counter()
    try:
        require_secure_transport_for_public_request(request=request, settings=settings)
    except HTTPException as exc:
        _log_auth_failure(
            started_at=started_at,
            status_code=exc.status_code,
            error_code="insecure_transport",
        )
        raise

    if settings.api_token is None:
        _log_auth_failure(
            started_at=started_at,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="missing_api_token",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Post-processing service is unavailable.",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        _log_auth_failure(
            started_at=started_at,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="missing_credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    if not secrets.compare_digest(credentials.credentials, settings.api_token):
        _log_auth_failure(
            started_at=started_at,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="invalid_credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    logger.info("processed_transcription_auth_succeeded")
    return settings


@router.post(
    "/processed-transcriptions/v1.0.0",
    summary="Post-process class transcription",
    description=(
    "`Receive:` an existing recorded audio file or raw transcript. "
"`Delivery:` five deliveries in total: four didactic outputs for study "
"plus one auditable raw_text reference. "

"`1) didactic_text:` text, clean, didactic, logical, continuous format, "
"with reduced semantic redundancies. "

"`2) themes:` the main semantic topics "
"prepared for future memorization. "

"`3) technical_terms:` relevant technical concepts and corrections. "

"`4) technology_mentions:` technologies, frameworks, platforms, "
"tools, services, libraries, APIs, or reference providers used in class. "

"`Audit/reference output:` raw_text, the auditable raw transcript. "
"This endpoint does not store memory, create embeddings, or perform search. "
"When provider mode is configured, raw transcription content is sent to the "
"configured external LLM provider; use local mode when content must remain "
"on this machine. "
"`NOTE:` the processed didactic result is saved as .md in: "
"`mindvox/outputs/human/processed_transcriptions`. "
"The auditable raw_text transcript will be saved in: "
"`mindvox/outputs/human/transcriptions`."
    ),
    response_model=ProcessedTranscriptionResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Unsupported audio file type or content type.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication required.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "HTTPS is required in public deployment.",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "description": "Method not allowed.",
        },
        status.HTTP_413_CONTENT_TOO_LARGE: {
            "description": "Audio or raw text exceeds the maximum allowed size.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Missing, conflicting, or invalid request data.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal post-processing error.",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "description": "LLM output was rejected by semantic quality control.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Post-processing service is unavailable.",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "description": "Post-processing engine timed out.",
        },
    },
)
async def post_process_class_transcription(
    input_type: Annotated[
        InputType,
        Form(
            description=(
                "Required strict technical selector. Type exactly one lowercase "
                "English value: audio or raw_text. In Swagger, raw_text_file "
                "is also accepted as a user-friendly alias when uploading a "
                ".txt transcript; the backend normalizes it to raw_text. Do "
                "not translate these values and do not use accents. Use audio "
                "when uploading audio_file. Use raw_text when pasting an "
                "existing transcription. Use raw_text_file when uploading the "
                ".txt field named raw_text_file. Example: audio for audio "
                "upload. Example for pasted text: raw_text. Example for .txt "
                "upload in Swagger: raw_text_file."
            ),
        ),
    ],
    audio_file: Annotated[
        UploadFile | None,
        File(
            description=(
                "Recorded audio file to transcribe before post-processing. "
                "Fill this only when input_type is exactly audio. Leave this "
                "empty when input_type is raw_text or when uploading "
                "raw_text_file. Supported formats are .wav and .m4a. "
                "Example: class-2026-06-09.wav."
            ),
        ),
    ] = None,
    raw_text: Annotated[
        str,
        Form(
            description=(
                "Raw transcription text to be post-processed. Fill this only "
                "when input_type is exactly raw_text and you want to paste the "
                "text directly. For long transcriptions, use raw_text_file "
                "instead. This field starts empty by default; leave it empty "
                "when uploading raw_text_file. Leave audio_file empty. Example: "
                "a rough transcript copied from a previous STT run."
            ),
        ),
    ] = "",
    raw_text_file: Annotated[
        UploadFile | None,
        File(
            description=(
                "Optional .txt file containing a raw transcription to be "
                "post-processed. Use this only when input_type is exactly "
                "raw_text, or when the Swagger input_type alias is "
                "raw_text_file, and the transcript is too long to paste "
                "comfortably in raw_text. Send either raw_text or "
                "raw_text_file, not both. Leave raw_text and audio_file empty. "
                "Example: e02-transcription.txt."
            ),
        ),
    ] = None,
    course: Annotated[
        str,
        Form(
            description=(
                "Optional name of the course or broader learning context. "
                "Example: Postgraduate course at Federal University of Goias. "
                f"Maximum: {MAX_COURSE_LENGTH} characters."
            ),
        ),
    ] = "",
    discipline: Annotated[
        str,
        Form(
            description=(
                "Optional name of the discipline, subject, or class area. "
                "Example: API Engineering for AI. Maximum: "
                f"{MAX_DISCIPLINE_LENGTH} characters."
            ),
        ),
    ] = "",
    class_date: Annotated[
        str,
        Form(
            description=(
                "Optional date of the class. Leave this empty if there is no "
                "date. If filled, use the YYYY-MM-DD format. Example: "
                "2026-06-09."
            ),
        ),
    ] = "",
    class_title: Annotated[
        str,
        Form(
            description=(
                "Optional title or topic of the class. Example: API First and "
                f"FastAPI. Maximum: {MAX_CLASS_TITLE_LENGTH} characters."
            ),
        ),
    ] = "",
    session_label: Annotated[
        str,
        Form(
            description=(
                "Optional short identifier for the recording or class session. "
                "Example: S02."
            ),
        ),
    ] = "",
    language: Annotated[
        str,
        Form(
            description=(
                "Expected language of the source content. For Brazilian "
                "Portuguese, use pt-BR. Example: pt-BR."
            ),
        ),
    ] = "pt-BR",
    processing_profile: Annotated[
        str,
        Form(
            description=(
                "Post-processing profile to apply. Type exactly study_notes or "
                "leave the default value unchanged. Example: study_notes."
            ),
        ),
    ] = "study_notes",
    settings: Settings = Depends(get_authenticated_settings),
) -> ProcessedTranscriptionResponse:
    started_at = perf_counter()
    queued_job_id: str | None = None
    try:
        normalized_input_type = _normalize_input_type(input_type)
        normalized_profile = _validate_processing_profile(processing_profile)
        metadata = build_transcription_metadata(
            course=course,
            discipline=discipline,
            class_date=class_date,
            class_title=class_title,
            session_label=session_label,
        )
        metadata = _metadata_with_prepared_raw_text_file_guard(
            raw_text_file=raw_text_file,
            metadata=metadata,
        )
        language = _validate_language(language)

        logger.info(
            "processed_transcription_request_started input_type=%s profile=%s mode=%s raw_text_file=%s course_present=%s discipline=%s class_date=%s class_title=%s session_label=%s",
            normalized_input_type,
            normalized_profile,
            settings.postprocessing_mode,
            _safe_filename(raw_text_file),
            metadata.course is not None,
            metadata.discipline,
            metadata.class_date,
            metadata.class_title,
            metadata.session_label,
        )

        if normalized_input_type == "raw_text":
            raw_text_value = await _validate_raw_text_flow(
                raw_text=raw_text,
                audio_file=audio_file,
                raw_text_file=raw_text_file,
                settings=settings,
            )
            source = Source(
                input_origin="raw_text",
                raw_text_origin="provided_by_client",
                transcription=None,
            )
        else:
            raw_text_value, source = await _transcribe_audio_input(
                audio_file=audio_file,
                raw_text=raw_text,
                raw_text_file=raw_text_file,
                language=language,
                metadata=metadata,
                settings=settings,
            )
            _validate_raw_text_size(raw_text_value, settings=settings)
            queued_job_id = enqueue_generated_transcription_job(
                raw_text=raw_text_value,
                language=language,
                metadata=metadata,
                source=source,
                settings=settings,
            )

        response = process_transcription(
            raw_text=raw_text_value,
            input_type=normalized_input_type,
            language=language,
            metadata=metadata,
            source=source,
            settings=settings,
        )
        complete_generated_transcription_job(
            job_id=queued_job_id,
            response=response,
            settings=settings,
        )
    except HTTPException as exc:
        _log_failure(
            started_at=started_at,
            status_code=exc.status_code,
            error_code=_error_code_for_status(exc.status_code),
        )
        raise
    except AudioDecodeError as exc:
        _log_failure(started_at=started_at, status_code=422, error_code="audio_decode_failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Audio file cannot be decoded.",
        ) from exc
    except TranscriptionServiceUnavailableError as exc:
        _log_failure(started_at=started_at, status_code=503, error_code="stt_unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Post-processing service is unavailable.",
        ) from exc
    except TranscriptionArtifactWriteError as exc:
        _log_failure(started_at=started_at, status_code=500, error_code="artifact_write_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal post-processing error.",
        ) from exc
    except (
        ProcessedTranscriptionArtifactWriteError,
        ProcessedTranscriptionQueueWriteError,
        StudyPackageArtifactWriteError,
    ) as exc:
        _log_failure(started_at=started_at, status_code=500, error_code="processed_artifact_write_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal post-processing error.",
        ) from exc
    except PostprocessingServiceUnavailableError as exc:
        _mark_queued_job_failed(
            queued_job_id=queued_job_id,
            error=exc,
            settings=settings,
        )
        _log_failure(started_at=started_at, status_code=503, error_code="engine_unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Post-processing service is unavailable.",
        ) from exc
    except PostprocessingTimeoutError as exc:
        _mark_queued_job_failed(
            queued_job_id=queued_job_id,
            error=exc,
            settings=settings,
        )
        _log_failure(started_at=started_at, status_code=504, error_code="engine_timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Post-processing engine timed out.",
        ) from exc
    except PostprocessingInsufficientCoverageError as exc:
        failure = _mark_queued_job_failed(
            queued_job_id=queued_job_id,
            error=exc,
            settings=settings,
        )
        rejected_artifacts = save_rejected_postprocessing_artifacts(
            raw_text=raw_text_value,
            input_type=normalized_input_type,
            language=language,
            metadata=metadata,
            source=source,
            settings=settings,
            error=exc,
            rejected_payload=getattr(exc, "rejected_payload", None),
            attempt=failure.job.attempts if failure else 1,
            max_attempts=settings.processed_transcription_queue_max_attempts,
            runtime_snapshot=build_postprocessing_runtime_snapshot(
                raw_text=raw_text_value,
                settings=settings,
            ),
            job_id=queued_job_id,
        )
        _log_failure(
            started_at=started_at,
            status_code=502,
            error_code="insufficient_semantic_coverage",
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error_code": "postprocessing_quality_rejected",
                "message": (
                    "The LLM output was rejected by the semantic coverage gate "
                    "because it did not preserve enough class content."
                ),
                "attempt": failure.job.attempts if failure else 1,
                "max_attempts": settings.processed_transcription_queue_max_attempts,
                "will_retry": failure.job.attempts < settings.processed_transcription_queue_max_attempts
                if failure
                else False,
                "last_error": exc.__class__.__name__,
                "retry_hint": exc.retry_hint,
                "rejected_artifacts": rejected_artifacts,
            },
        ) from exc
    except PostprocessingInvalidOutputError as exc:
        _mark_queued_job_failed(
            queued_job_id=queued_job_id,
            error=exc,
            settings=settings,
        )
        _log_failure(started_at=started_at, status_code=500, error_code="invalid_engine_output")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal post-processing error.",
        ) from exc
    except Exception:
        _mark_queued_job_failed(
            queued_job_id=queued_job_id,
            error=RuntimeError("unexpected_processing_error"),
            settings=settings,
        )
        _log_failure(started_at=started_at, status_code=500, error_code="internal_error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal post-processing error.",
        ) from None

    duration_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "processed_transcription_request_succeeded status_code=200 input_type=%s raw_text_chars=%s themes_count=%s technology_mentions_count=%s duration_ms=%.3f",
        normalized_input_type,
        len(raw_text_value),
        len(response.themes),
        len(response.technology_mentions),
        duration_ms,
    )
    return response


def _mark_queued_job_failed(
    *,
    queued_job_id: str | None,
    error: Exception,
    settings: Settings,
) -> object | None:
    try:
        return mark_generated_transcription_job_failed(
            job_id=queued_job_id,
            error=error,
            settings=settings,
        )
    except ProcessedTranscriptionQueueWriteError:
        logger.warning(
            "processed_transcription_queue_mark_failed_error job_present=%s",
            queued_job_id is not None,
        )
        return None


def _metadata_with_prepared_raw_text_file_guard(
    *,
    raw_text_file: UploadFile | None,
    metadata: TranscriptionMetadata,
) -> TranscriptionMetadata:
    if not _has_uploaded_file(raw_text_file):
        return metadata

    prepared = _prepared_metadata_from_raw_text_filename(raw_text_file.filename or "")
    if prepared is None:
        return metadata

    _log_prepared_metadata_difference(
        field_name="class_date",
        received=metadata.class_date,
        filename_default=prepared.class_date,
    )
    _log_prepared_metadata_difference(
        field_name="discipline",
        received=metadata.discipline,
        filename_default=prepared.discipline,
        compare_slug=True,
    )
    _log_prepared_metadata_difference(
        field_name="session_label",
        received=metadata.session_label,
        filename_default=prepared.session_label,
        compare_session_label=True,
    )
    _log_prepared_metadata_difference(
        field_name="class_title",
        received=metadata.class_title,
        filename_default=prepared.class_title,
        compare_slug=True,
    )

    return TranscriptionMetadata(
        course=metadata.course,
        discipline=metadata.discipline or prepared.discipline,
        class_date=metadata.class_date or prepared.class_date,
        class_title=metadata.class_title or prepared.class_title,
        session_label=metadata.session_label or prepared.session_label,
    )


def _log_prepared_metadata_difference(
    *,
    field_name: str,
    received: str | None,
    filename_default: str | None,
    compare_slug: bool = False,
    compare_session_label: bool = False,
) -> None:
    if not received or not filename_default:
        return

    if compare_session_label:
        values_match = _session_labels_match(
            received=received,
            expected=filename_default,
        )
    else:
        received_value = (
            _metadata_compare_slug(received)
            if compare_slug
            else received.strip().lower()
        )
        filename_value = (
            _metadata_compare_slug(filename_default)
            if compare_slug
            else filename_default.strip().lower()
        )
        values_match = received_value == filename_value

    if values_match:
        return

    logger.warning(
        "processed_transcription_prepared_metadata_difference field=%s received=%s filename_default=%s action=using_received",
        field_name,
        received,
        filename_default,
    )


def _prepared_metadata_from_raw_text_filename(
    filename: str,
) -> TranscriptionMetadata | None:
    match = PREPARED_RAW_TEXT_FILENAME_PATTERN.fullmatch(Path(filename).name)
    if match is None:
        return None

    body = match.group("body")
    class_number = match.group("class_number")
    session = match.group("session")
    body_parts = [part for part in body.split("-") if part]
    if not body_parts:
        return None

    discipline = _display_slug(body_parts[0], prefer_upper=True)
    professor = _display_slug("-".join(body_parts[1:])) if len(body_parts) > 1 else ""
    session_label = f"A{class_number}S{session}"
    title_parts = [
        discipline,
        f"Aula {class_number}",
        f"Sessão {session}",
    ]
    if professor:
        title_parts.append(f"Professor {professor}")

    return TranscriptionMetadata(
        course=None,
        discipline=discipline,
        class_date=match.group("class_date"),
        class_title=" - ".join(title_parts),
        session_label=session_label,
    )


def _display_slug(value: str, *, prefer_upper: bool = False) -> str:
    words = [part for part in re.split(r"[-_\s]+", value.strip()) if part]
    if not words:
        return ""
    if prefer_upper and len(words) == 1 and len(words[0]) <= 5:
        return words[0].upper()
    return " ".join(word.capitalize() for word in words)


def _metadata_compare_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", _strip_accents(value).lower())
    return re.sub(r"-+", "-", normalized).strip("-")


def _session_labels_match(*, received: str, expected: str) -> bool:
    received_parts = _parse_session_label(received)
    expected_parts = _parse_session_label(expected)
    if received_parts is None or expected_parts is None:
        return received.strip().lower() == expected.strip().lower()

    received_class, received_session = received_parts
    expected_class, expected_session = expected_parts
    if received_session != expected_session:
        return False
    return received_class is None or expected_class is None or received_class == expected_class


def _parse_session_label(value: str) -> tuple[int | None, int] | None:
    normalized = _strip_accents(value).strip().upper()
    normalized = re.sub(r"[^A-Z0-9]+", "", normalized)

    match = re.search(r"A(?P<class_number>\d+)S(?P<session>\d+)", normalized)
    if match:
        return int(match.group("class_number")), int(match.group("session"))

    match = re.search(r"S(?P<session>\d+)$", normalized)
    if match:
        return None, int(match.group("session"))

    return None


def _strip_accents(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _safe_filename(file: UploadFile | None) -> str | None:
    if not _has_uploaded_file(file):
        return None
    return Path(file.filename or "").name or None


async def _transcribe_audio_input(
    *,
    audio_file: UploadFile | None,
    raw_text: str | None,
    raw_text_file: UploadFile | None,
    language: str,
    metadata: TranscriptionMetadata,
    settings: Settings,
) -> tuple[str, Source]:
    if not _has_uploaded_file(audio_file):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="audio_file is required when input_type is audio.",
        )

    if clean_optional_text(raw_text) is not None or _has_uploaded_file(raw_text_file):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="audio_file cannot be sent together with raw_text or raw_text_file.",
        )

    extension = _validate_filename(audio_file.filename)
    content_type = _validate_content_type(
        extension=extension,
        content_type=audio_file.content_type,
    )
    audio_bytes = await read_upload_with_limit(
        audio_file,
        settings=settings,
        detail="Audio file exceeds the maximum allowed size.",
    )
    _validate_audio_container(extension=extension, audio_bytes=audio_bytes)

    logger.info(
        "processed_transcription_audio_validated size_bytes=%s content_type=%s",
        len(audio_bytes),
        content_type,
    )

    transcription = transcribe_audio(
        audio_bytes=audio_bytes,
        filename=audio_file.filename or f"audio{extension}",
        language=language,
        metadata=metadata,
        settings=settings,
    )
    transcription.artifact_locations = build_transcription_artifact_locations(
        transcription,
        settings=settings,
    )
    save_transcription_artifacts(transcription, settings=settings)
    logger.info("processed_transcription_raw_artifact_saved input_type=audio")
    source = Source(
        input_origin="audio",
        raw_text_origin="generated_by_transcription_service",
        transcription=SourceTranscription(
            transcription_id=transcription.transcription_id,
            duration_seconds=transcription.duration_seconds,
            segments_count=len(transcription.segments),
            transcription_engine=transcription.engine,
        ),
    )
    return transcription.text, source


async def _validate_raw_text_flow(
    *,
    raw_text: str | None,
    audio_file: UploadFile | None,
    raw_text_file: UploadFile | None,
    settings: Settings,
) -> str:
    if _has_uploaded_file(audio_file):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="audio_file cannot be sent together with raw_text or raw_text_file.",
        )

    cleaned = clean_optional_text(raw_text)
    has_raw_text_file = _has_uploaded_file(raw_text_file)
    if cleaned is not None and has_raw_text_file:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="raw_text and raw_text_file cannot be sent together.",
        )

    if has_raw_text_file:
        return await _read_raw_text_file(raw_text_file, settings=settings)

    if cleaned is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="raw_text or raw_text_file is required when input_type is raw_text.",
        )

    _validate_raw_text_size(cleaned, settings=settings)
    return cleaned


async def _read_raw_text_file(
    raw_text_file: UploadFile,
    *,
    settings: Settings,
) -> str:
    _validate_raw_text_file(raw_text_file)
    raw_text_bytes = await read_upload_with_limit(
        raw_text_file,
        settings=settings,
        detail="Raw text file exceeds the maximum allowed upload size.",
    )
    try:
        decoded = raw_text_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="raw_text_file must be UTF-8 text.",
        ) from exc

    cleaned = clean_optional_text(decoded)
    if cleaned is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="raw_text_file must not be empty.",
        )

    _validate_raw_text_size(cleaned, settings=settings)
    return cleaned


def _normalize_input_type(input_type: InputType) -> str:
    normalized = INPUT_TYPE_ALIASES.get(input_type, input_type)
    return normalized.value


def _validate_processing_profile(processing_profile: str) -> str:
    normalized = processing_profile.strip()
    if normalized not in PROCESSING_PROFILES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="processing_profile must be study_notes.",
        )

    return normalized


def _validate_language(language: str) -> str:
    language = language.strip()
    if not LANGUAGE_PATTERN.fullmatch(language):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="language must use a simple locale format such as pt-BR.",
        )

    return language


def _has_uploaded_file(upload_file: UploadFile | None) -> bool:
    return upload_file is not None and bool((upload_file.filename or "").strip())


def _validate_raw_text_file(raw_text_file: UploadFile) -> None:
    filename = raw_text_file.filename or ""
    lower_filename = filename.strip().lower()
    if not any(lower_filename.endswith(extension) for extension in SUPPORTED_RAW_TEXT_FILE_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported raw text file type. Supported format: .txt.",
        )

    normalized_content_type = (
        raw_text_file.content_type.lower().split(";")[0].strip()
        if raw_text_file.content_type
        else ""
    )
    if normalized_content_type and normalized_content_type not in SUPPORTED_RAW_TEXT_FILE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported raw text file content type.",
        )


def _validate_filename(filename: str | None) -> str:
    cleaned_filename = filename.strip() if filename else ""
    if not cleaned_filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Audio file must have a filename.",
        )

    lower_filename = cleaned_filename.lower()
    for extension in SUPPORTED_EXTENSIONS:
        if lower_filename.endswith(extension):
            return extension

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported audio file type. Supported formats: .wav, .m4a.",
    )


def _validate_content_type(*, extension: str, content_type: str | None) -> str:
    normalized_content_type = content_type.lower().split(";")[0].strip() if content_type else ""
    if normalized_content_type not in SUPPORTED_CONTENT_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio content type.",
        )

    return normalized_content_type


def _validate_raw_text_size(raw_text: str, *, settings: Settings) -> None:
    if len(raw_text) > settings.postprocessing_max_input_chars:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Raw text exceeds the maximum allowed size.",
        )


def _validate_audio_container(*, extension: str, audio_bytes: bytes) -> None:
    if extension == ".wav" and _looks_like_wav(audio_bytes):
        return

    if extension == ".m4a" and _looks_like_m4a(audio_bytes):
        return

    raise AudioDecodeError("Audio file cannot be decoded.")


def _looks_like_wav(audio_bytes: bytes) -> bool:
    return (
        len(audio_bytes) >= 12
        and audio_bytes[:4] == b"RIFF"
        and audio_bytes[8:12] == b"WAVE"
    )


def _looks_like_m4a(audio_bytes: bytes) -> bool:
    return len(audio_bytes) >= 12 and audio_bytes[4:8] == b"ftyp"


def _log_failure(*, started_at: float, status_code: int, error_code: str) -> None:
    duration_ms = (perf_counter() - started_at) * 1000
    logger.warning(
        "processed_transcription_request_failed status_code=%s error_code=%s duration_ms=%.3f",
        status_code,
        error_code,
        duration_ms,
    )


def _log_auth_failure(*, started_at: float, status_code: int, error_code: str) -> None:
    duration_ms = (perf_counter() - started_at) * 1000
    logger.warning(
        "processed_transcription_auth_failed status_code=%s error_code=%s phase=auth duration_ms=%.3f",
        status_code,
        error_code,
        duration_ms,
    )


def _error_code_for_status(status_code: int) -> str:
    return {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "authentication_failed",
        status.HTTP_413_CONTENT_TOO_LARGE: "payload_too_large",
        status.HTTP_422_UNPROCESSABLE_CONTENT: "validation_failed",
        status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
        status.HTTP_504_GATEWAY_TIMEOUT: "gateway_timeout",
    }.get(status_code, "controlled_http_error")
