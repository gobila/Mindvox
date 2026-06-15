import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from routers.health import router as health_router
from routers.processed_transcriptions import router as processed_transcriptions_router
from routers.transcriptions import router as transcriptions_router
from services.local_llm_runtime import LocalLLMRuntime
from services.processed_transcription_queue import process_pending_jobs
from settings import apply_main_profile_defaults, get_settings
from starlette.middleware.trustedhost import TrustedHostMiddleware


apply_main_profile_defaults()

logger = logging.getLogger("mindvox.startup")
logger.addHandler(logging.NullHandler())


PROFILE_DESCRIPTIONS = {
    "dev": (
        "Local development profile: real STT, automatic local post-processing, "
        "and didactic dev-token when no private token is configured."
    ),
    "contract": (
        "Contract profile: controlled STT and post-processing responses for "
        "technical tests; Llama is not started."
    ),
    "prod": (
        "Public production profile: public hardening enabled, docs disabled by "
        "default, dev-token blocked, and external secure configuration required."
    ),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    local_llm_runtime = LocalLLMRuntime(settings)
    queue_task: asyncio.Task[None] | None = None
    stop_queue = asyncio.Event()

    local_llm_runtime.start_if_required()
    app.state.local_llm_runtime = local_llm_runtime

    if settings.postprocessing_mode in {"local", "provider"}:
        queue_task = asyncio.create_task(
            _run_processed_transcription_queue(
                settings=settings,
                stop_event=stop_queue,
            )
        )

    try:
        yield
    finally:
        stop_queue.set()
        if queue_task is not None:
            queue_task.cancel()
            with suppress(asyncio.CancelledError):
                await queue_task
        local_llm_runtime.stop()


async def _run_processed_transcription_queue(
    *,
    settings,
    stop_event: asyncio.Event,
) -> None:
    queue_logger = logging.getLogger("mindvox.processed_transcription_queue")
    while not stop_event.is_set():
        summary = await asyncio.to_thread(
            process_pending_jobs,
            settings=settings,
            logger=queue_logger,
        )
        if summary.attempted:
            queue_logger.info(
                "processed_transcription_queue_pass attempted=%s completed=%s failed=%s",
                summary.attempted,
                summary.completed,
                summary.failed,
            )

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=settings.processed_transcription_queue_retry_seconds,
            )
        except TimeoutError:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.public_deployment and not settings.trusted_hosts:
        raise RuntimeError(
            "MINDVOX_TRUSTED_HOSTS is required when MINDVOX_PUBLIC_DEPLOYMENT=true."
        )
    if settings.public_deployment and "*" in settings.trusted_hosts:
        raise RuntimeError(
            "MINDVOX_TRUSTED_HOSTS cannot contain '*' when MINDVOX_PUBLIC_DEPLOYMENT=true."
        )

    app = FastAPI(
        title="Mindvox",
        description=_build_openapi_description(settings.runtime_profile),
        version="1.0.0",
        contact={
            "name": "Adalberto Tenório Batista",
            "url": "https://github.com/b-e-t-o/Mindvox.git",
            "email": "improprio.leghorn0m@icloud.com",
        },
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    if settings.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=list(settings.trusted_hosts),
        )

    app.include_router(health_router)
    app.include_router(transcriptions_router)
    app.include_router(processed_transcriptions_router)
    return app


def _build_openapi_description(runtime_profile: str) -> str:
    profile_description = PROFILE_DESCRIPTIONS.get(
        runtime_profile,
        "Unknown startup profile.",
    )
    return (
        "An AI-powered framework for personalized learning and development.\n\n"
        f"**Active startup profile:** `{runtime_profile}`. {profile_description}"
    )


app = create_app()
