import os
from dataclasses import dataclass


DEFAULT_MAX_UPLOAD_MB = 500
DEFAULT_POSTPROCESSING_MAX_INPUT_CHARS = 150000
DEFAULT_LLM_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_LLM_MAX_OUTPUT_TOKENS = 20000
DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
DEFAULT_LLM_PROVIDER = "groq"
DEFAULT_LLM_TIMEOUT_SECONDS = 1200
DEFAULT_LOCAL_LLM_BASE_URL = "http://127.0.0.1:8080/v1"
DEFAULT_LOCAL_LLM_MODEL = "qwen35a3b-q8"
DEFAULT_LOCAL_LLM_PROVIDER = "local"
DEFAULT_LOCAL_LLM_AUTOSTART = True
DEFAULT_LLAMA_SERVER_CTX_SIZE = 65536
DEFAULT_LLAMA_SERVER_GPU_LAYERS = 99
DEFAULT_LLAMA_SERVER_PARALLEL = 1
DEFAULT_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS = 240
DEFAULT_LOCAL_DEV_API_TOKEN = "dev-token"
DEFAULT_POSTPROCESSING_MODE = "auto"
DEFAULT_POSTPROCESSING_CHUNKING_MODE = "off"
DEFAULT_POSTPROCESSING_CHUNKING_MIN_CHARS = 20000
DEFAULT_POSTPROCESSING_CHUNK_TARGET_TOKENS = 5000
DEFAULT_POSTPROCESSING_PRE_AUDIT_ENABLED = True
DEFAULT_POSTPROCESSING_FINAL_AUDIT_ENABLED = True
DEFAULT_PROCESSED_TRANSCRIPTION_OUTPUT_DIR = "outputs/processed_transcriptions"
DEFAULT_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR = (
    "outputs/human/processed_transcriptions"
)
DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR = (
    "outputs/processed_transcriptions/rejected"
)
DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR = (
    "outputs/human/processed_transcriptions/rejected"
)
DEFAULT_E03_STUDY_PACKAGE_OUTPUT_DIR = "outputs/study_packages"
DEFAULT_E03_ACTIVE_COURSE_STORE = "outputs/config/e03_courses.json"
DEFAULT_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS = 60
DEFAULT_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS = 3
DEFAULT_TRANSCRIPTION_OUTPUT_DIR = "outputs/transcriptions"
DEFAULT_TRANSCRIPTION_TEXT_OUTPUT_DIR = "outputs/human/transcriptions"
DEFAULT_TRANSCRIPTION_BACKEND = "auto"
DEFAULT_TRANSCRIPTION_MODEL = "mlx-community/whisper-large-v3-turbo-fp16"
DEFAULT_TRANSCRIPTION_FALLBACK_MODEL = "turbo"
PLACEHOLDER_API_TOKENS = {
    "<set-real-token-only-in-local-env>",
    "replace-with-local-token",
}
PUBLIC_DEPLOYMENT_BLOCKED_API_TOKENS = {
    "dev-token",
}
RUNTIME_PROFILES = {"dev", "contract", "prod"}


@dataclass(frozen=True)
class Settings:
    api_token: str | None
    runtime_profile: str
    max_upload_mb: int
    public_deployment: bool
    docs_enabled: bool
    trusted_hosts: tuple[str, ...]
    postprocessing_mode: str
    postprocessing_max_input_chars: int
    postprocessing_chunking_mode: str
    postprocessing_chunking_min_chars: int
    postprocessing_chunk_target_tokens: int
    postprocessing_pre_audit_enabled: bool
    postprocessing_final_audit_enabled: bool
    llm_provider: str
    llm_base_url: str
    llm_allowed_provider_hosts: tuple[str, ...]
    llm_max_output_tokens: int
    llm_model: str
    llm_api_key: str | None
    llm_timeout_seconds: int
    local_llm_autostart: bool
    llama_server_path: str | None
    local_llm_model_path: str | None
    llama_server_ctx_size: int
    llama_server_gpu_layers: int
    llama_server_parallel: int
    llama_server_startup_timeout_seconds: int
    processed_transcription_output_dir: str
    processed_transcription_markdown_output_dir: str
    processed_transcription_rejected_output_dir: str
    processed_transcription_rejected_markdown_output_dir: str
    e03_study_package_output_dir: str
    e03_active_course_store: str
    e03_obsidian_export_enabled: bool
    e03_obsidian_vaults_base_dir: str | None
    e03_obsidian_vault_create_only: bool
    processed_transcription_queue_enabled: bool
    processed_transcription_queue_retry_seconds: int
    processed_transcription_queue_max_attempts: int
    transcription_mode: str
    transcription_backend: str
    transcription_model: str
    transcription_fallback_model: str
    transcription_output_dir: str
    transcription_text_output_dir: str


def apply_main_profile_defaults() -> None:
    """Normalize defaults for the plain `fastapi dev` application entrypoint."""
    raw_profile = os.getenv("MINDVOX_RUNTIME_PROFILE")
    normalized_profile = raw_profile.strip().lower() if raw_profile else ""
    if normalized_profile in RUNTIME_PROFILES:
        return

    if _read_bool("MINDVOX_PUBLIC_DEPLOYMENT", default=False):
        return

    os.environ["MINDVOX_RUNTIME_PROFILE"] = "dev"
    _replace_absent_or_contract_env("MINDVOX_TRANSCRIPTION_MODE", "real")
    _replace_absent_or_contract_env("MINDVOX_POSTPROCESSING_MODE", "auto")
    os.environ.setdefault("MINDVOX_POSTPROCESSING_CHUNKING_MODE", "tfidf")


def get_settings() -> Settings:
    public_deployment = _read_bool("MINDVOX_PUBLIC_DEPLOYMENT", default=False)
    docs_enabled = _read_bool("MINDVOX_ENABLE_DOCS", default=not public_deployment)
    transcription_mode = os.getenv("MINDVOX_TRANSCRIPTION_MODE", "real").strip().lower()
    if not transcription_mode:
        transcription_mode = "real"
    postprocessing_mode = _read_postprocessing_mode(transcription_mode)
    max_upload_mb = _read_positive_int(
        "MINDVOX_MAX_UPLOAD_MB",
        default=DEFAULT_MAX_UPLOAD_MB,
    )
    postprocessing_max_input_chars = _read_positive_int(
        "MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS",
        default=DEFAULT_POSTPROCESSING_MAX_INPUT_CHARS,
    )
    postprocessing_chunking_min_chars = _read_positive_int(
        "MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS",
        default=DEFAULT_POSTPROCESSING_CHUNKING_MIN_CHARS,
        minimum=1,
    )
    postprocessing_chunk_target_tokens = _read_positive_int(
        "MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS",
        default=DEFAULT_POSTPROCESSING_CHUNK_TARGET_TOKENS,
        minimum=500,
    )
    llm_timeout_seconds = _read_positive_int(
        "MINDVOX_LLM_TIMEOUT_SECONDS",
        default=DEFAULT_LLM_TIMEOUT_SECONDS,
    )
    llm_max_output_tokens = _read_positive_int(
        "MINDVOX_LLM_MAX_OUTPUT_TOKENS",
        default=DEFAULT_LLM_MAX_OUTPUT_TOKENS,
        minimum=1,
    )
    llama_server_ctx_size = _read_positive_int(
        "MINDVOX_LLAMA_SERVER_CTX_SIZE",
        default=DEFAULT_LLAMA_SERVER_CTX_SIZE,
        minimum=1,
    )
    llama_server_gpu_layers = _read_positive_int(
        "MINDVOX_LLAMA_SERVER_GPU_LAYERS",
        default=DEFAULT_LLAMA_SERVER_GPU_LAYERS,
        minimum=0,
    )
    llama_server_parallel = _read_positive_int(
        "MINDVOX_LLAMA_SERVER_PARALLEL",
        default=DEFAULT_LLAMA_SERVER_PARALLEL,
        minimum=1,
    )
    llama_server_startup_timeout_seconds = _read_positive_int(
        "MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS",
        default=DEFAULT_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS,
        minimum=1,
    )
    processed_transcription_queue_retry_seconds = _read_positive_int(
        "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS",
        default=DEFAULT_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS,
        minimum=1,
    )
    processed_transcription_queue_max_attempts = _read_positive_int(
        "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS",
        default=DEFAULT_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS,
        minimum=1,
    )

    return Settings(
        api_token=_read_api_token(public_deployment=public_deployment),
        runtime_profile=_read_runtime_profile(
            public_deployment=public_deployment,
            transcription_mode=transcription_mode,
        ),
        max_upload_mb=max_upload_mb,
        public_deployment=public_deployment,
        docs_enabled=docs_enabled,
        trusted_hosts=_read_csv("MINDVOX_TRUSTED_HOSTS"),
        postprocessing_mode=postprocessing_mode,
        postprocessing_max_input_chars=postprocessing_max_input_chars,
        postprocessing_chunking_mode=os.getenv(
            "MINDVOX_POSTPROCESSING_CHUNKING_MODE",
            DEFAULT_POSTPROCESSING_CHUNKING_MODE,
        ).strip().lower(),
        postprocessing_chunking_min_chars=postprocessing_chunking_min_chars,
        postprocessing_chunk_target_tokens=postprocessing_chunk_target_tokens,
        postprocessing_pre_audit_enabled=_read_bool(
            "MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED",
            default=DEFAULT_POSTPROCESSING_PRE_AUDIT_ENABLED,
        ),
        postprocessing_final_audit_enabled=_read_bool(
            "MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED",
            default=DEFAULT_POSTPROCESSING_FINAL_AUDIT_ENABLED,
        ),
        llm_provider=os.getenv(
            "MINDVOX_LLM_PROVIDER",
            _default_llm_provider(postprocessing_mode),
        ),
        llm_base_url=os.getenv(
            "MINDVOX_LLM_BASE_URL",
            _default_llm_base_url(postprocessing_mode),
        ),
        llm_allowed_provider_hosts=_read_csv("MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS"),
        llm_max_output_tokens=llm_max_output_tokens,
        llm_model=os.getenv(
            "MINDVOX_LLM_MODEL",
            _default_llm_model(postprocessing_mode),
        ),
        llm_api_key=os.getenv("MINDVOX_LLM_API_KEY"),
        llm_timeout_seconds=llm_timeout_seconds,
        local_llm_autostart=_read_bool(
            "MINDVOX_LOCAL_LLM_AUTOSTART",
            default=DEFAULT_LOCAL_LLM_AUTOSTART,
        ),
        llama_server_path=_read_optional_path("MINDVOX_LLAMA_SERVER_PATH"),
        local_llm_model_path=_read_optional_path("MINDVOX_LOCAL_LLM_MODEL_PATH"),
        llama_server_ctx_size=llama_server_ctx_size,
        llama_server_gpu_layers=llama_server_gpu_layers,
        llama_server_parallel=llama_server_parallel,
        llama_server_startup_timeout_seconds=llama_server_startup_timeout_seconds,
        processed_transcription_output_dir=os.getenv(
            "MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR",
            DEFAULT_PROCESSED_TRANSCRIPTION_OUTPUT_DIR,
        ),
        processed_transcription_markdown_output_dir=os.getenv(
            "MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR",
            DEFAULT_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR,
        ),
        processed_transcription_rejected_output_dir=os.getenv(
            "MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR",
            DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR,
        ),
        processed_transcription_rejected_markdown_output_dir=os.getenv(
            "MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR",
            DEFAULT_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR,
        ),
        e03_study_package_output_dir=os.getenv(
            "MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR",
            DEFAULT_E03_STUDY_PACKAGE_OUTPUT_DIR,
        ),
        e03_active_course_store=os.getenv(
            "MINDVOX_E03_ACTIVE_COURSE_STORE",
            DEFAULT_E03_ACTIVE_COURSE_STORE,
        ),
        e03_obsidian_export_enabled=_read_bool(
            "MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED",
            default=False,
        ),
        e03_obsidian_vaults_base_dir=_read_optional_path(
            "MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR"
        ),
        e03_obsidian_vault_create_only=_read_bool(
            "MINDVOX_E03_OBSIDIAN_VAULT_CREATE_ONLY",
            default=True,
        ),
        processed_transcription_queue_enabled=_read_bool(
            "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED",
            default=True,
        ),
        processed_transcription_queue_retry_seconds=(
            processed_transcription_queue_retry_seconds
        ),
        processed_transcription_queue_max_attempts=(
            processed_transcription_queue_max_attempts
        ),
        transcription_mode=transcription_mode,
        transcription_backend=_read_transcription_backend(),
        transcription_model=os.getenv(
            "MINDVOX_TRANSCRIPTION_MODEL",
            DEFAULT_TRANSCRIPTION_MODEL,
        ),
        transcription_fallback_model=_read_non_empty_string(
            "MINDVOX_TRANSCRIPTION_FALLBACK_MODEL",
            DEFAULT_TRANSCRIPTION_FALLBACK_MODEL,
        ),
        transcription_output_dir=os.getenv(
            "MINDVOX_TRANSCRIPTION_OUTPUT_DIR",
            DEFAULT_TRANSCRIPTION_OUTPUT_DIR,
        ),
        transcription_text_output_dir=os.getenv(
            "MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR",
            DEFAULT_TRANSCRIPTION_TEXT_OUTPUT_DIR,
        ),
    )


def _read_api_token(*, public_deployment: bool) -> str | None:
    raw_value = os.getenv("MINDVOX_API_TOKEN")
    if raw_value is None:
        return _default_api_token(public_deployment=public_deployment)

    token = raw_value.strip()
    if not token:
        return _default_api_token(public_deployment=public_deployment)

    if token.lower() in PLACEHOLDER_API_TOKENS:
        return None

    if public_deployment and token.lower() in PUBLIC_DEPLOYMENT_BLOCKED_API_TOKENS:
        return None

    return token


def _default_api_token(*, public_deployment: bool) -> str | None:
    if public_deployment:
        return None

    return DEFAULT_LOCAL_DEV_API_TOKEN


def _read_runtime_profile(*, public_deployment: bool, transcription_mode: str) -> str:
    raw_value = os.getenv("MINDVOX_RUNTIME_PROFILE")
    normalized = raw_value.strip().lower() if raw_value else ""
    if normalized in RUNTIME_PROFILES:
        return normalized

    if public_deployment:
        return "prod"
    if transcription_mode == "contract":
        return "contract"

    return "dev"


def _replace_absent_or_contract_env(name: str, replacement: str) -> None:
    raw_value = os.getenv(name)
    normalized = raw_value.strip().lower() if raw_value else ""
    if normalized in {"", "contract"}:
        os.environ[name] = replacement


def _read_postprocessing_mode(transcription_mode: str) -> str:
    raw_value = os.getenv("MINDVOX_POSTPROCESSING_MODE", DEFAULT_POSTPROCESSING_MODE)
    normalized = raw_value.strip().lower() if raw_value else DEFAULT_POSTPROCESSING_MODE
    if normalized == "auto":
        return _postprocessing_mode_for_transcription_mode(transcription_mode)

    return normalized


def _read_transcription_backend() -> str:
    raw_value = os.getenv("MINDVOX_TRANSCRIPTION_BACKEND", DEFAULT_TRANSCRIPTION_BACKEND)
    normalized = raw_value.strip().lower() if raw_value else DEFAULT_TRANSCRIPTION_BACKEND
    return normalized or DEFAULT_TRANSCRIPTION_BACKEND


def _read_non_empty_string(name: str, default: str) -> str:
    raw_value = os.getenv(name, default)
    normalized = raw_value.strip() if raw_value else default
    return normalized or default


def _postprocessing_mode_for_transcription_mode(transcription_mode: str) -> str:
    if transcription_mode == "contract":
        return "contract"

    return "local"


def _default_llm_provider(postprocessing_mode: str) -> str:
    if postprocessing_mode == "local":
        return DEFAULT_LOCAL_LLM_PROVIDER

    return DEFAULT_LLM_PROVIDER


def _default_llm_base_url(postprocessing_mode: str) -> str:
    if postprocessing_mode == "local":
        return DEFAULT_LOCAL_LLM_BASE_URL

    return DEFAULT_LLM_BASE_URL


def _default_llm_model(postprocessing_mode: str) -> str:
    if postprocessing_mode == "local":
        return DEFAULT_LOCAL_LLM_MODEL

    return DEFAULT_LLM_MODEL


def _read_bool(name: str, *, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    return default


def _read_csv(name: str) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return ()

    values = tuple(
        value.strip().lower()
        for value in raw_value.split(",")
        if value.strip()
    )
    return values


def _read_optional_path(name: str) -> str | None:
    raw_value = os.getenv(name)
    if raw_value is None:
        return None

    value = raw_value.strip()
    if not value:
        return None

    return value


def _read_positive_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    if value < minimum:
        return default

    return value
