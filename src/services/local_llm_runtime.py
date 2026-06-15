from __future__ import annotations

import logging
import shutil
import subprocess
import time
from pathlib import Path
from urllib import error, request
from urllib.parse import urlparse

from settings import Settings


DEFAULT_LLAMA_CPP_SERVER = (
    Path.home() / "Desenvolvedor" / "llama.cpp" / "build" / "bin" / "llama-server"
)
DEFAULT_QWEN_MODEL = Path.home() / "Models" / "Qwen3.6-35B-A3B-MTP-Q8.gguf"
READINESS_TIMEOUT_SECONDS = 1


class LocalLLMStartupError(RuntimeError):
    """Raised when local real post-processing cannot start."""


class LocalLLMRuntime:
    def __init__(
        self,
        settings: Settings,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._logger = logger or logging.getLogger("mindvox.local_llm")
        self._process: subprocess.Popen[str] | None = None
        self._started_by_app = False

    def start_if_required(self) -> None:
        if self._settings.postprocessing_mode != "local":
            self._logger.info(
                "local_llm_autostart_skipped mode=%s",
                self._settings.postprocessing_mode,
            )
            return

        if not self._settings.local_llm_autostart:
            self._logger.info("local_llm_autostart_disabled")
            return

        if _is_openai_compatible_server_ready(self._settings.llm_base_url):
            self._logger.info("local_llm_already_running")
            return

        server_path = _resolve_llama_server_path(self._settings)
        model_path = _resolve_local_model_path(self._settings)
        host, port = _host_and_port_from_base_url(self._settings.llm_base_url)
        command = [
            str(server_path),
            "--model",
            str(model_path),
            "--alias",
            self._settings.llm_model,
            "--host",
            host,
            "--port",
            str(port),
            "--ctx-size",
            str(self._settings.llama_server_ctx_size),
            "--n-gpu-layers",
            str(self._settings.llama_server_gpu_layers),
            "--parallel",
            str(self._settings.llama_server_parallel),
        ]

        self._logger.info(
            "local_llm_starting base_url=%s model_alias=%s",
            self._settings.llm_base_url,
            self._settings.llm_model,
        )
        self._process = subprocess.Popen(command, text=True)
        self._started_by_app = True

        try:
            self._wait_until_ready()
        except LocalLLMStartupError:
            self.stop()
            raise

        self._logger.info("local_llm_started")

    def stop(self) -> None:
        if not self._started_by_app or self._process is None:
            return

        if self._process.poll() is not None:
            return

        self._logger.info("local_llm_stopping")
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._logger.warning("local_llm_killing_after_stop_timeout")
            self._process.kill()
            self._process.wait(timeout=10)

    def _wait_until_ready(self) -> None:
        assert self._process is not None
        deadline = (
            time.monotonic()
            + self._settings.llama_server_startup_timeout_seconds
        )

        while time.monotonic() < deadline:
            return_code = self._process.poll()
            if return_code is not None:
                raise LocalLLMStartupError(
                    "Local LLM startup failed: llama-server exited before it "
                    f"became ready (exit code {return_code})."
                )

            if _is_openai_compatible_server_ready(self._settings.llm_base_url):
                return

            time.sleep(1)

        raise LocalLLMStartupError(
            "Local LLM startup failed: llama-server did not become ready within "
            f"{self._settings.llama_server_startup_timeout_seconds} seconds."
        )


def _resolve_llama_server_path(settings: Settings) -> Path:
    if settings.llama_server_path is not None:
        configured_path = Path(settings.llama_server_path).expanduser()
        if configured_path.is_file() and _is_executable(configured_path):
            return configured_path

        raise LocalLLMStartupError(
            "Local LLM startup failed: configured llama-server executable was "
            "not found or is not executable. Check MINDVOX_LLAMA_SERVER_PATH."
        )

    discovered_path = shutil.which("llama-server")
    if discovered_path:
        return Path(discovered_path)

    if DEFAULT_LLAMA_CPP_SERVER.is_file() and _is_executable(DEFAULT_LLAMA_CPP_SERVER):
        return DEFAULT_LLAMA_CPP_SERVER

    raise LocalLLMStartupError(
        "Local LLM startup failed: llama-server executable was not found. "
        "Install/build llama.cpp or set MINDVOX_LLAMA_SERVER_PATH."
    )


def _resolve_local_model_path(settings: Settings) -> Path:
    if settings.local_llm_model_path is not None:
        configured_path = Path(settings.local_llm_model_path).expanduser()
        if configured_path.is_file():
            return configured_path

        raise LocalLLMStartupError(
            "Local LLM startup failed: configured GGUF model file was not found. "
            "Check MINDVOX_LOCAL_LLM_MODEL_PATH."
        )

    model_as_path = Path(settings.llm_model).expanduser()
    if model_as_path.is_file():
        return model_as_path

    if DEFAULT_QWEN_MODEL.is_file():
        return DEFAULT_QWEN_MODEL

    raise LocalLLMStartupError(
        "Local LLM startup failed: GGUF model file was not found. "
        "Set MINDVOX_LOCAL_LLM_MODEL_PATH."
    )


def _host_and_port_from_base_url(base_url: str) -> tuple[str, int]:
    parsed = urlparse(base_url)
    if parsed.hostname is None:
        raise LocalLLMStartupError(
            "Local LLM startup failed: MINDVOX_LLM_BASE_URL must include a host."
        )

    if parsed.port is not None:
        return parsed.hostname, parsed.port

    if parsed.scheme == "https":
        return parsed.hostname, 443

    return parsed.hostname, 80


def _is_openai_compatible_server_ready(base_url: str) -> bool:
    req = request.Request(
        f"{base_url.rstrip('/')}/models",
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=READINESS_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 300
    except (TimeoutError, OSError, error.HTTPError, error.URLError, ValueError):
        return False


def _is_executable(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_mode & 0o111 != 0
