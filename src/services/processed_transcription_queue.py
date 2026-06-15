from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from schemas.processed_transcriptions import Source
from schemas.transcriptions import TranscriptionMetadata
from services.postprocessing_service import (
    build_postprocessing_runtime_snapshot,
    process_transcription,
)
from services.processed_transcription_artifacts import (
    ProcessedTranscriptionArtifactWriteError,
    build_processed_transcription_artifact_locations,
    save_processed_transcription_artifacts,
    save_rejected_postprocessing_artifacts,
)
from services.e03_study_package import (
    attach_study_package,
    save_study_package_artifact,
)
from settings import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ProcessedTranscriptionQueueWriteError(Exception):
    """Raised when the local processed-transcription queue cannot be written."""


class ProcessedTranscriptionQueueJob(BaseModel):
    job_id: str
    status: Literal["pending", "completed", "failed"]
    created_at: str
    updated_at: str
    attempts: int = 0
    last_error: str | None = None
    processed_transcription_id: str | None = None
    raw_text: str
    language: str
    metadata: TranscriptionMetadata
    source: Source


@dataclass(frozen=True)
class QueueProcessingSummary:
    attempted: int
    completed: int
    failed: int


@dataclass(frozen=True)
class QueueFailureResult:
    job: ProcessedTranscriptionQueueJob
    failed_permanently: bool


def enqueue_generated_transcription_job(
    *,
    raw_text: str,
    language: str,
    metadata: TranscriptionMetadata,
    source: Source,
    settings: Settings,
) -> str | None:
    if not settings.processed_transcription_queue_enabled:
        return None

    if source.transcription is None:
        return None

    job_id = source.transcription.transcription_id
    now = _utc_now()
    queue_dirs = _queue_dirs(settings)
    pending_path = queue_dirs.pending / f"{job_id}.json"
    completed_path = queue_dirs.completed / f"{job_id}.json"

    if completed_path.exists():
        return job_id

    if pending_path.exists():
        return job_id

    job = ProcessedTranscriptionQueueJob(
        job_id=job_id,
        status="pending",
        created_at=now,
        updated_at=now,
        raw_text=raw_text,
        language=language,
        metadata=metadata,
        source=source,
    )
    _write_job(pending_path, job)
    return job_id


def complete_generated_transcription_job(
    *,
    job_id: str | None,
    response,
    settings: Settings,
) -> None:
    response.artifact_locations = build_processed_transcription_artifact_locations(
        response,
        settings=settings,
    )
    attach_study_package(response)
    if job_id is None or not settings.processed_transcription_queue_enabled:
        save_processed_transcription_artifacts(response, settings=settings)
        save_study_package_artifact(response, settings=settings)
        return

    json_path, _markdown_path = save_processed_transcription_artifacts(
        response,
        settings=settings,
    )
    save_study_package_artifact(response, settings=settings)
    queue_dirs = _queue_dirs(settings)
    pending_path = queue_dirs.pending / f"{job_id}.json"
    completed_path = queue_dirs.completed / f"{job_id}.json"
    now = _utc_now()

    if not pending_path.exists():
        return

    job = _read_job(pending_path)
    job.status = "completed"
    job.updated_at = now
    job.last_error = None
    job.processed_transcription_id = response.processed_transcription_id
    _write_job(completed_path, job)
    _remove_if_exists(pending_path)
    logging.getLogger("mindvox.processed_transcription_queue").info(
        "processed_transcription_job_completed job_id=%s artifact=%s",
        job_id,
        json_path.name,
    )


def mark_generated_transcription_job_failed(
    *,
    job_id: str | None,
    error: Exception,
    settings: Settings,
) -> QueueFailureResult | None:
    if job_id is None or not settings.processed_transcription_queue_enabled:
        return None

    queue_dirs = _queue_dirs(settings)
    pending_path = queue_dirs.pending / f"{job_id}.json"
    if not pending_path.exists():
        return None

    job = _read_job(pending_path)
    job.updated_at = _utc_now()
    job.attempts += 1
    job.last_error = error.__class__.__name__
    failed_permanently = job.attempts >= settings.processed_transcription_queue_max_attempts
    if failed_permanently:
        job.status = "failed"
        failed_path = queue_dirs.failed / f"{job_id}.{job.last_error}.json"
        _write_job(failed_path, job)
        _remove_if_exists(pending_path)
    else:
        job.status = "pending"
        _write_job(pending_path, job)

    return QueueFailureResult(job=job, failed_permanently=failed_permanently)


def process_pending_jobs(
    *,
    settings: Settings,
    limit: int | None = None,
    logger: logging.Logger | None = None,
) -> QueueProcessingSummary:
    if not settings.processed_transcription_queue_enabled:
        return QueueProcessingSummary(attempted=0, completed=0, failed=0)

    logger = logger or logging.getLogger("mindvox.processed_transcription_queue")
    queue_dirs = _queue_dirs(settings)
    pending_paths = sorted(queue_dirs.pending.glob("*.json"))
    if limit is not None:
        pending_paths = pending_paths[:limit]

    attempted = 0
    completed = 0
    failed = 0

    for pending_path in pending_paths:
        try:
            job = _read_job(pending_path)
        except ProcessedTranscriptionQueueWriteError:
            failed += 1
            logger.warning("processed_transcription_job_invalid file=%s", pending_path.name)
            continue

        attempted += 1
        try:
            response = process_transcription(
                raw_text=job.raw_text,
                input_type="audio",
                language=job.language,
                metadata=job.metadata,
                source=job.source,
                settings=settings,
            )
            complete_generated_transcription_job(
                job_id=job.job_id,
                response=response,
                settings=settings,
            )
            completed += 1
        except Exception as exc:
            failure = mark_generated_transcription_job_failed(
                job_id=job.job_id,
                error=exc,
                settings=settings,
            )
            _save_rejected_artifacts_if_available(
                job=job,
                failure=failure,
                error=exc,
                settings=settings,
            )
            failed += 1
            logger.warning(
                "processed_transcription_job_retry_failed job_id=%s error_type=%s attempts=%s max_attempts=%s failed_permanently=%s",
                job.job_id,
                exc.__class__.__name__,
                failure.job.attempts if failure else None,
                settings.processed_transcription_queue_max_attempts,
                failure.failed_permanently if failure else None,
            )

    return QueueProcessingSummary(
        attempted=attempted,
        completed=completed,
        failed=failed,
    )


@dataclass(frozen=True)
class _QueueDirs:
    pending: Path
    completed: Path
    failed: Path


def _queue_dirs(settings: Settings) -> _QueueDirs:
    root = _resolve_output_dir(settings.processed_transcription_output_dir)
    queue_root = root / "queue"
    pending = queue_root / "pending"
    completed = queue_root / "completed"
    failed = queue_root / "failed"
    try:
        pending.mkdir(parents=True, exist_ok=True)
        completed.mkdir(parents=True, exist_ok=True)
        failed.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ProcessedTranscriptionQueueWriteError(
            "Processed transcription queue directory could not be created."
        ) from exc

    return _QueueDirs(pending=pending, completed=completed, failed=failed)


def _resolve_output_dir(configured_output_dir: str) -> Path:
    cleaned = configured_output_dir.strip()
    if not cleaned:
        cleaned = "outputs/processed_transcriptions"

    output_dir = Path(cleaned).expanduser()
    if output_dir.is_absolute():
        return output_dir

    return PROJECT_ROOT / output_dir


def _read_job(path: Path) -> ProcessedTranscriptionQueueJob:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ProcessedTranscriptionQueueJob.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ProcessedTranscriptionQueueWriteError(
            "Processed transcription queue job could not be read."
        ) from exc


def _write_job(path: Path, job: ProcessedTranscriptionQueueJob) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f"{path.name}.tmp")
        temp_path.write_text(
            json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(path)
    except OSError as exc:
        raise ProcessedTranscriptionQueueWriteError(
            "Processed transcription queue job could not be written."
        ) from exc


def _save_rejected_artifacts_if_available(
    *,
    job: ProcessedTranscriptionQueueJob,
    failure: QueueFailureResult | None,
    error: Exception,
    settings: Settings,
) -> None:
    rejected_payload = getattr(error, "rejected_payload", None)
    if rejected_payload is None:
        return

    attempt = failure.job.attempts if failure else job.attempts + 1
    save_rejected_postprocessing_artifacts(
        raw_text=job.raw_text,
        input_type="audio",
        language=job.language,
        metadata=job.metadata,
        source=job.source,
        settings=settings,
        error=error,
        rejected_payload=rejected_payload,
        attempt=attempt,
        max_attempts=settings.processed_transcription_queue_max_attempts,
        runtime_snapshot=build_postprocessing_runtime_snapshot(
            raw_text=job.raw_text,
            settings=settings,
        ),
        job_id=job.job_id,
    )


def _remove_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise ProcessedTranscriptionArtifactWriteError(
            "Processed transcription queue job could not be moved to completed."
        ) from exc


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
