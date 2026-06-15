import logging
import re
import secrets
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

from schemas.transcriptions import TranscriptionResponse
from routers.endpoint_security import require_secure_transport_for_public_request
from routers.metadata_validation import (
    MAX_CLASS_TITLE_LENGTH,
    MAX_COURSE_LENGTH,
    MAX_DISCIPLINE_LENGTH,
    build_transcription_metadata,
)
from routers.upload_limits import read_upload_with_limit
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


router = APIRouter(tags=["transcriptions"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger("mindvox.transcriptions")
logger.addHandler(logging.NullHandler())

SUPPORTED_EXTENSIONS = {".wav", ".m4a"}
SUPPORTED_CONTENT_TYPES = {
    ".wav": {"audio/wav", "audio/x-wav", "audio/vnd.wave"},
    ".m4a": {"audio/mp4", "audio/m4a", "audio/x-m4a"},
}
LANGUAGE_PATTERN = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")


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
            detail="Transcription service is unavailable.",
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

    logger.info("transcription_auth_succeeded")
    return settings


@router.post(
    "/transcriptions/v1.0.0",
    summary="Transcribe audio file",
    description=(
        "Receives a recorded audio file and returns a text transcription with "
        "optional class metadata. This endpoint does not provide streaming, TTS, "
        "or speech-to-speech processing. In local development, the human-readable "
        "raw transcript is also saved as a .txt file under "
        "outputs/human/transcriptions; see artifact_locations.human_text_path in "
        "the response. The technical JSON artifact is separate and is indicated "
        "by artifact_locations.technical_json_path."
    ),
    response_model=TranscriptionResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Unsupported audio file type.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication required.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "HTTPS is required in public deployment.",
        },
        status.HTTP_413_CONTENT_TOO_LARGE: {
            "description": "Audio file exceeds the maximum allowed size.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Missing file, invalid metadata, or undecodable audio.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal transcription error.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Transcription service is unavailable.",
        },
    },
)
async def transcribe_recorded_audio(
    audio_file: Annotated[
        UploadFile,
        File(
            description=(
                "Required recorded audio file to be transcribed. Supported formats "
                "are .wav and .m4a. Example: class-2026-06-09.wav."
            ),
        ),
    ],
    course: Annotated[
        str,
        Form(
            description=(
                "Optional name of the course or broader learning context. Use it "
                "to organize the transcription after it is generated. Example: "
                "Postgraduate course at Federal University of Goias. Maximum: "
                f"{MAX_COURSE_LENGTH} characters."
            ),
        ),
    ] = "",
    discipline: Annotated[
        str,
        Form(
            description=(
                "Optional name of the discipline, subject, or class area related "
                "to the audio. Example: API Engineering for AI. Maximum: "
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
                "Optional title, topic, or human-readable identification of the "
                "class. It helps identify the transcription later. Example: "
                "Introduction to API contracts. Maximum: "
                f"{MAX_CLASS_TITLE_LENGTH} characters."
            ),
        ),
    ] = "",
    session_label: Annotated[
        str,
        Form(
            description=(
                "Optional short identifier for the recording session. Use a simple "
                "value. Example: class-01."
            ),
        ),
    ] = "",
    language: Annotated[
        str,
        Form(
            description=(
                "Expected language of the audio. For Brazilian Portuguese, use "
                "pt-BR. Example: pt-BR."
            ),
        ),
    ] = "pt-BR",
    settings: Settings = Depends(get_authenticated_settings),
) -> TranscriptionResponse:
    metadata = build_transcription_metadata(
        course=course,
        discipline=discipline,
        class_date=class_date,
        class_title=class_title,
        session_label=session_label,
    )
    language = _validate_language(language)
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

    started_at = perf_counter()
    logger.info(
        "transcription_request_started size_bytes=%s content_type=%s mode=%s",
        len(audio_bytes),
        content_type,
        settings.transcription_mode,
    )

    try:
        response = transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio_file.filename or f"audio{extension}",
            language=language,
            metadata=metadata,
            settings=settings,
        )
        response.artifact_locations = build_transcription_artifact_locations(
            response,
            settings=settings,
        )
        save_transcription_artifacts(response, settings=settings)
    except AudioDecodeError as exc:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.warning(
            "transcription_request_failed status_code=422 error_code=audio_decode_failed duration_ms=%.3f",
            duration_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Audio file cannot be decoded.",
        ) from exc
    except TranscriptionServiceUnavailableError as exc:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.warning(
            "transcription_request_failed status_code=503 error_code=service_unavailable duration_ms=%.3f",
            duration_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service is unavailable.",
        ) from exc
    except TranscriptionArtifactWriteError as exc:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.error(
            "transcription_request_failed status_code=500 error_code=artifact_write_failed duration_ms=%.3f",
            duration_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal transcription error.",
        ) from exc
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.error(
            "transcription_request_failed status_code=500 error_code=internal_error duration_ms=%.3f",
            duration_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal transcription error.",
        ) from None

    duration_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "transcription_request_succeeded status_code=200 artifact_saved=true duration_ms=%.3f",
        duration_ms,
    )
    return response


def _validate_language(language: str) -> str:
    language = language.strip()
    if not LANGUAGE_PATTERN.fullmatch(language):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="language must use a simple locale format such as pt-BR.",
        )

    return language


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


def _validate_audio_container(*, extension: str, audio_bytes: bytes) -> None:
    if extension == ".wav" and _looks_like_wav(audio_bytes):
        return

    if extension == ".m4a" and _looks_like_m4a(audio_bytes):
        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Audio file cannot be decoded.",
    )


def _looks_like_wav(audio_bytes: bytes) -> bool:
    return (
        len(audio_bytes) >= 12
        and audio_bytes[:4] == b"RIFF"
        and audio_bytes[8:12] == b"WAVE"
    )


def _looks_like_m4a(audio_bytes: bytes) -> bool:
    return len(audio_bytes) >= 12 and audio_bytes[4:8] == b"ftyp"


def _log_auth_failure(*, started_at: float, status_code: int, error_code: str) -> None:
    duration_ms = (perf_counter() - started_at) * 1000
    logger.warning(
        "transcription_auth_failed status_code=%s error_code=%s phase=auth duration_ms=%.3f",
        status_code,
        error_code,
        duration_ms,
    )
