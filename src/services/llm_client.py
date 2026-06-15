from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from urllib import error, request

from settings import Settings

LLM_RESPONSE_BYTES_PER_OUTPUT_TOKEN = 16
MIN_LLM_RESPONSE_BYTES = 65536


class LLMClientUnavailableError(Exception):
    """Raised when the configured LLM endpoint cannot be reached."""


class LLMClientTimeoutError(Exception):
    """Raised when the configured LLM endpoint times out."""


@dataclass(frozen=True)
class LLMCompletion:
    content: str


class OpenAICompatibleClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    def complete_json(self, *, messages: list[dict[str, str]]) -> LLMCompletion:
        payload = {
            "model": self._settings.llm_model,
            "max_tokens": self._settings.llm_max_output_tokens,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        if self._settings.postprocessing_mode == "local":
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        payload_bytes = json.dumps(payload).encode("utf-8")
        req = request.Request(
            _chat_completions_url(self._settings.llm_base_url),
            data=payload_bytes,
            headers=self._headers(),
            method="POST",
        )

        try:
            with request.urlopen(
                req,
                timeout=self._settings.llm_timeout_seconds,
            ) as response:
                max_response_bytes = _max_response_bytes(
                    self._settings.llm_max_output_tokens
                )
                response_body = response.read(max_response_bytes + 1)
                if len(response_body) > max_response_bytes:
                    raise LLMClientUnavailableError(
                        "LLM endpoint returned too much data."
                    )
                response_payload = json.loads(response_body.decode("utf-8"))
        except TimeoutError as exc:
            raise LLMClientTimeoutError("LLM request timed out.") from exc
        except socket.timeout as exc:
            raise LLMClientTimeoutError("LLM request timed out.") from exc
        except error.HTTPError as exc:
            if exc.code == 504:
                raise LLMClientTimeoutError("LLM request timed out.") from exc
            raise LLMClientUnavailableError("LLM endpoint returned an error.") from exc
        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError | socket.timeout):
                raise LLMClientTimeoutError("LLM request timed out.") from exc
            raise LLMClientUnavailableError("LLM endpoint is unavailable.") from exc
        except json.JSONDecodeError as exc:
            raise LLMClientUnavailableError("LLM endpoint returned invalid JSON.") from exc

        try:
            content = response_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientUnavailableError("LLM endpoint returned an invalid payload.") from exc

        return LLMCompletion(content=str(content))

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self._settings.llm_api_key}"
        return headers


def _chat_completions_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/chat/completions"


def _max_response_bytes(max_output_tokens: int) -> int:
    return max(
        MIN_LLM_RESPONSE_BYTES,
        max_output_tokens * LLM_RESPONSE_BYTES_PER_OUTPUT_TOKEN,
    )
