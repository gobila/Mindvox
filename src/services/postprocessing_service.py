from __future__ import annotations

import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from secrets import token_hex
from typing import Any, Literal
from urllib.parse import urlparse
import unicodedata

from pydantic import BaseModel, ValidationError

from schemas.processed_transcriptions import (
    ProcessedTranscriptionResponse,
    ProcessingEngine,
    ProcessingNote,
    Source,
    TechnicalTerm,
    TechnologyMention,
    Theme,
)
from schemas.transcriptions import TranscriptionMetadata
from services.llm_client import (
    LLMClientTimeoutError,
    LLMClientUnavailableError,
    OpenAICompatibleClient,
)
from services.postprocessing_pipeline import (
    chunk_text_tfidf,
    merge_payload_dicts,
    pre_audit_context_header,
    pre_audit_raw_text,
    should_use_chunk_pipeline,
)
from settings import Settings


PUBLIC_MODEL_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)?$"
)
PUBLIC_PROVIDER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SENSITIVE_MARKERS = (
    ".env",
    "authorization",
    "bearer",
    "password",
    "private",
    "secret",
    "token",
)
PLACEHOLDER_API_KEYS = {
    "replace-with-provider-key",
    "<set-real-key-only-in-local-env>",
}
REDACTED_MODEL_LABEL = "configured-model"
REDACTED_PROVIDER_LABEL = "configured-provider"
LOCAL_LLM_HOSTNAMES = {"localhost", "host.docker.internal"}
E03_POSTPROCESSING_MANUAL_PATH = (
    Path(__file__).resolve().parent / "prompts" / "e03_postprocessing_manual.md"
)
CONFIDENCE_ALIASES = {
    "low": "low",
    "baixa": "low",
    "baixo": "low",
    "fraca": "low",
    "fraco": "low",
    "medium": "medium",
    "media": "medium",
    "medio": "medium",
    "moderada": "medium",
    "moderado": "medium",
    "high": "high",
    "alta": "high",
    "alto": "high",
    "forte": "high",
}
TECHNOLOGY_CATEGORY_ALIASES = {
    "api": "api",
    "apis": "api",
    "banco de dados": "database",
    "database": "database",
    "databases": "database",
    "ferramenta": "tool",
    "ferramentas": "tool",
    "framework": "framework",
    "frameworks": "framework",
    "infra": "infrastructure",
    "infraestrutura": "infrastructure",
    "infrastructure": "infrastructure",
    "language": "language",
    "languages": "language",
    "library": "library",
    "libraries": "library",
    "linguagem": "language",
    "linguagens": "language",
    "biblioteca": "library",
    "bibliotecas": "library",
    "plataforma": "platform",
    "plataformas": "platform",
    "platform": "platform",
    "platforms": "platform",
    "protocol": "protocol",
    "protocols": "protocol",
    "protocolo": "protocol",
    "protocolos": "protocol",
    "provedor": "provider",
    "provedores": "provider",
    "provider": "provider",
    "providers": "provider",
    "servico": "service",
    "servicos": "service",
    "service": "service",
    "services": "service",
    "tecnologia": "tool",
    "tecnologias": "tool",
    "tool": "tool",
    "tools": "tool",
}
LONG_TRANSCRIPT_SEMANTIC_COVERAGE_MIN_CHARS = 20_000
LONG_TRANSCRIPT_MIN_DIDACTIC_RATIO = 0.35
LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO = 0.18
LONG_TRANSCRIPT_MIN_THEMES = 8
LONG_TRANSCRIPT_MIN_SEMANTIC_ANCHOR_RATIO = 0.9
MAX_SEMANTIC_COVERAGE_ANCHORS = 32
PROTECTED_SEMANTIC_PHRASES = (
    ("Campus Party", ("campus party",)),
    (
        "Positivo",
        ("empresa positivo", "projeto positivo", "a positivo", "positivo informatica"),
    ),
    ("licitacoes publicas", ("licitacoes publicas", "licitacao publica")),
    ("editais", ("editais", "edital")),
    ("diarios oficiais", ("diarios oficiais", "diario oficial")),
    (
        "score de viabilidade",
        ("score de viabilidade", "score de negocio", "viabilidade de negocio"),
    ),
    ("NPS", ("nps",)),
    (
        "restaurante universitario",
        ("restaurante universitario", "ru", "restaurante da universidade"),
    ),
    ("Data Warehouse", ("data warehouse",)),
    ("Data Lake", ("data lake",)),
    ("banco de producao", ("banco de producao",)),
    ("ETL", ("etl",)),
    ("AutoML", ("automl", "auto ml")),
    ("testes temporais", ("testes temporais", "separacao temporal")),
    ("Invisible banking", ("invisible banking",)),
    (
        "microservicos",
        ("microservicos", "microservico", "microsservicos", "microsservico"),
    ),
    ("Java", ("java",)),
    ("Mainframe", ("mainframe",)),
    ("Cobol", ("cobol",)),
    ("TCC", ("tcc",)),
    ("MBA", ("mba",)),
    ("orgaos publicos", ("orgaos publicos", "orgao publico")),
    ("agencias de IA", ("agencias de ia", "agencia de ia")),
    ("nao engordar o codigo", ("nao engordar o codigo",)),
)
STUDENT_CONTRIBUTION_CUES = {
    "aluno",
    "aluna",
    "discutiu",
    "relatou",
    "comentou",
    "perguntou",
    "questionou",
    "explicou",
    "metafora",
}
CAPITALIZED_ANCHOR_STOPWORDS = {
    "A",
    "Acho",
    "Agora",
    "Ai",
    "Alguem",
    "Alguém",
    "As",
    "Assim",
    "Bom",
    "Com",
    "Da",
    "Das",
    "De",
    "Do",
    "Dos",
    "E",
    "Em",
    "Entao",
    "Então",
    "Isso",
    "Ja",
    "Já",
    "Na",
    "No",
    "O",
    "Os",
    "Para",
    "Por",
    "Que",
    "Temos",
    "Tá",
    "Vocês",
}


@dataclass(frozen=True)
class SemanticCoverageAnchor:
    label: str
    aliases: tuple[str, ...]


class PostprocessingServiceUnavailableError(Exception):
    """Raised when the configured post-processing engine cannot run."""


class PostprocessingTimeoutError(Exception):
    """Raised when the configured post-processing engine times out."""


class PostprocessingInvalidOutputError(Exception):
    """Raised when the engine returns an invalid structured response."""


class PostprocessingInsufficientCoverageError(PostprocessingInvalidOutputError):
    """Raised when the engine returns valid JSON with insufficient class coverage."""

    def __init__(
        self,
        message: str,
        *,
        retry_hint: str | None = None,
        rejected_payload: object | None = None,
    ):
        super().__init__(message)
        self.retry_hint = retry_hint or message
        self.rejected_payload = rejected_payload


class PostprocessingPayload(BaseModel):
    didactic_text: str
    themes: list[Theme]
    technical_terms: list[TechnicalTerm]
    technology_mentions: list[TechnologyMention]
    processing_notes: list[ProcessingNote]


def process_transcription(
    *,
    raw_text: str,
    input_type: str,
    language: str,
    metadata: TranscriptionMetadata,
    source: Source,
    settings: Settings,
) -> ProcessedTranscriptionResponse:
    mode = settings.postprocessing_mode.strip().lower()

    if should_use_chunk_pipeline(
        raw_text=raw_text,
        chunking_mode=settings.postprocessing_chunking_mode,
        min_chars=settings.postprocessing_chunking_min_chars,
    ):
        payload = _chunked_payload(
            raw_text=raw_text,
            language=language,
            metadata=metadata,
            settings=settings,
            mode=mode,
        )
    elif mode == "contract":
        payload = _contract_payload(raw_text=raw_text)
    elif mode in {"provider", "local"}:
        payload = _engine_payload(
            raw_text=raw_text,
            language=language,
            metadata=metadata,
            settings=settings,
            mode=mode,
        )
    else:
        raise PostprocessingServiceUnavailableError(
            "Unsupported post-processing mode."
        )

    return ProcessedTranscriptionResponse(
        processed_transcription_id=_new_processed_transcription_id(),
        input_type=input_type,
        language=language,
        raw_text=raw_text,
        didactic_text=payload.didactic_text,
        themes=payload.themes,
        technical_terms=payload.technical_terms,
        technology_mentions=payload.technology_mentions,
        processing_notes=payload.processing_notes,
        metadata=metadata,
        source=source,
        processing_engine=_processing_engine(settings=settings, mode=mode),
    )


def build_postprocessing_runtime_snapshot(
    *,
    raw_text: str,
    settings: Settings,
) -> dict[str, Any]:
    """Capture deterministic runtime settings used to diagnose E03 failures."""
    cleaned_raw_text = raw_text.strip()
    snapshot: dict[str, Any] = {
        "postprocessing_mode": settings.postprocessing_mode,
        "chunking_mode": settings.postprocessing_chunking_mode,
        "chunking_min_chars": settings.postprocessing_chunking_min_chars,
        "chunk_target_tokens": settings.postprocessing_chunk_target_tokens,
        "pre_audit_enabled": settings.postprocessing_pre_audit_enabled,
        "final_audit_enabled": settings.postprocessing_final_audit_enabled,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_max_output_tokens": settings.llm_max_output_tokens,
        "llm_timeout_seconds": settings.llm_timeout_seconds,
        "llama_server_ctx_size": settings.llama_server_ctx_size,
        "postprocessing_max_input_chars": settings.postprocessing_max_input_chars,
        "raw_text_chars": len(cleaned_raw_text),
        "estimated_raw_tokens": _estimated_tokens(cleaned_raw_text),
        "semantic_gate_minimum_didactic_chars_monolithic": (
            _minimum_didactic_text_chars(
                cleaned_raw_text,
                minimum_ratio=LONG_TRANSCRIPT_MIN_DIDACTIC_RATIO,
            )
        ),
        "semantic_gate_minimum_didactic_chars_chunked": (
            _minimum_didactic_text_chars(
                cleaned_raw_text,
                minimum_ratio=LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO,
            )
        ),
        "semantic_gate_minimum_themes": _minimum_theme_count(cleaned_raw_text),
        "protected_semantic_anchors_count": len(
            _semantic_coverage_anchors(cleaned_raw_text)
        ),
    }
    chunk_pipeline_enabled = should_use_chunk_pipeline(
        raw_text=cleaned_raw_text,
        chunking_mode=settings.postprocessing_chunking_mode,
        min_chars=settings.postprocessing_chunking_min_chars,
    )
    snapshot["chunk_pipeline_enabled"] = chunk_pipeline_enabled
    if not chunk_pipeline_enabled:
        snapshot["chunk_count"] = 0
        return snapshot

    pre_audit = pre_audit_raw_text(
        cleaned_raw_text,
        enabled=settings.postprocessing_pre_audit_enabled,
    )
    chunks = chunk_text_tfidf(
        pre_audit.text_for_llm,
        max_chunk_tokens=settings.postprocessing_chunk_target_tokens,
    )
    estimated_chunk_tokens = [_estimated_tokens(chunk.text) for chunk in chunks]
    chunk_chars = [len(chunk.text) for chunk in chunks]
    snapshot.update(
        {
            "pre_audit_issues_count": len(pre_audit.issues),
            "pre_audit_text_chars": len(pre_audit.text_for_llm.strip()),
            "chunk_count": len(chunks),
            "chunk_chars_min": min(chunk_chars) if chunk_chars else 0,
            "chunk_chars_max": max(chunk_chars) if chunk_chars else 0,
            "chunk_chars_avg": round(sum(chunk_chars) / len(chunk_chars), 2)
            if chunk_chars
            else 0,
            "chunk_estimated_tokens_min": min(estimated_chunk_tokens)
            if estimated_chunk_tokens
            else 0,
            "chunk_estimated_tokens_max": max(estimated_chunk_tokens)
            if estimated_chunk_tokens
            else 0,
            "chunk_estimated_tokens_avg": round(
                sum(estimated_chunk_tokens) / len(estimated_chunk_tokens),
                2,
            )
            if estimated_chunk_tokens
            else 0,
            "chunks_over_target_token_estimate": sum(
                1
                for estimated_tokens in estimated_chunk_tokens
                if estimated_tokens > settings.postprocessing_chunk_target_tokens
            ),
        }
    )
    return snapshot


def _chunked_payload(
    *,
    raw_text: str,
    language: str,
    metadata: TranscriptionMetadata,
    settings: Settings,
    mode: str,
) -> PostprocessingPayload:
    pre_audit = pre_audit_raw_text(
        raw_text,
        enabled=settings.postprocessing_pre_audit_enabled,
    )
    chunks = chunk_text_tfidf(
        pre_audit.text_for_llm,
        max_chunk_tokens=settings.postprocessing_chunk_target_tokens,
    )
    if not chunks:
        if mode == "contract":
            return _contract_payload(raw_text=raw_text)
        if mode in {"provider", "local"}:
            return _engine_payload(
                raw_text=raw_text,
                language=language,
                metadata=metadata,
                settings=settings,
                mode=mode,
            )
        raise PostprocessingServiceUnavailableError(
            "Unsupported post-processing mode."
        )

    chunk_payloads: list[dict[str, Any]] = []
    chunk_ids: list[str] = []
    header = pre_audit_context_header(pre_audit)
    for chunk in chunks:
        chunk_raw_text = f"{header}{chunk.text}".strip()
        if mode == "contract":
            chunk_payload = _contract_payload(raw_text=chunk_raw_text)
        elif mode in {"provider", "local"}:
            chunk_payload = _engine_payload(
                raw_text=chunk_raw_text,
                language=language,
                metadata=metadata,
                settings=settings,
                mode=mode,
                semantic_coverage_mode="chunk",
            )
        else:
            raise PostprocessingServiceUnavailableError(
                "Unsupported post-processing mode."
            )
        chunk_payloads.append(chunk_payload.model_dump())
        chunk_ids.append(chunk.chunk_id)

    merged = merge_payload_dicts(
        chunk_payloads=chunk_payloads,
        chunk_ids=chunk_ids,
        original_raw_text=raw_text,
        pre_audit=pre_audit,
        final_audit_enabled=settings.postprocessing_final_audit_enabled,
    )
    payload = PostprocessingPayload.model_validate(merged)
    if mode != "contract":
        try:
            _validate_semantic_coverage(
                payload=payload,
                raw_text=raw_text,
                minimum_didactic_ratio=LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO,
                enforce_semantic_anchors=False,
            )
        except PostprocessingInsufficientCoverageError as exc:
            raise PostprocessingInsufficientCoverageError(
                str(exc),
                retry_hint=exc.retry_hint,
                rejected_payload=payload,
            ) from exc
        _append_chunked_semantic_anchor_audit_note(payload=payload, raw_text=raw_text)
    return payload


def _estimated_tokens(text: str) -> int:
    if not text:
        return 0

    return max(1, len(text) // 4)


def _contract_payload(*, raw_text: str) -> PostprocessingPayload:
    excerpt = _short_excerpt(raw_text)
    technical_terms = _contract_technical_terms(raw_text=raw_text)
    technology_mentions = _contract_technology_mentions(raw_text=raw_text)
    return PostprocessingPayload(
        didactic_text=(
            "This contract-mode didactic text demonstrates the E03 response shape. "
            f"It preserves the raw transcription as audit evidence and organizes "
            f"the study material around the provided content: {excerpt}"
        ),
        themes=[
            Theme(
                order=1,
                title="Contract-mode study material",
                summary=(
                    "Controlled theme generated for automated tests and API "
                    "demonstrations."
                ),
                key_points=[
                    "The raw transcription remains available for audit.",
                    "The processed response contains the five public deliveries.",
                    "No memory storage, embedding generation, or search is performed.",
                ],
                semantic_role="fundamento",
                evidence=excerpt,
            )
        ],
        technical_terms=technical_terms,
        technology_mentions=technology_mentions,
        processing_notes=[
            ProcessingNote(
                type="processing",
                message=(
                    "Contract mode returns controlled content for automated tests; "
                    "it does not replace a real human proof."
                ),
            )
        ],
    )


def _contract_technical_terms(*, raw_text: str) -> list[TechnicalTerm]:
    lower_text = raw_text.lower()
    terms: list[TechnicalTerm] = []
    if "api" in lower_text:
        terms.append(
            TechnicalTerm(
                term="API",
                normalized_from=["api"],
                explanation=(
                    "Interface used by software systems to expose or consume "
                    "capabilities through a defined contract."
                ),
                confidence="high",
                evidence="api",
            )
        )
    if "bearer" in lower_text:
        terms.append(
            TechnicalTerm(
                term="Bearer authentication",
                normalized_from=["Bearer"],
                explanation=(
                    "Authentication scheme in which the client sends a token in "
                    "the Authorization header."
                ),
                confidence="high",
                evidence="Bearer",
            )
        )

    return terms


def _contract_technology_mentions(*, raw_text: str) -> list[TechnologyMention]:
    lower_text = raw_text.lower()
    mentions: list[TechnologyMention] = []
    if "fastapi" in lower_text or "fast api" in lower_text:
        mentions.append(
            TechnologyMention(
                name="FastAPI",
                category="framework",
                context="Framework explicitly mentioned in the raw transcription.",
                importance="high",
                normalized_from=["FastAPI"],
                confidence="high",
                evidence="FastAPI",
            )
        )
    if "openapi" in lower_text or "open api" in lower_text:
        mentions.append(
            TechnologyMention(
                name="OpenAPI",
                category="api",
                context="API description format explicitly mentioned in the raw transcription.",
                importance="high",
                normalized_from=["OpenAPI"],
                confidence="high",
                evidence="OpenAPI",
            )
        )

    return mentions


def _engine_payload(
    *,
    raw_text: str,
    language: str,
    metadata: TranscriptionMetadata,
    settings: Settings,
    mode: str,
    semantic_coverage_mode: Literal["full", "chunk"] = "full",
) -> PostprocessingPayload:
    if mode == "provider" and _missing_provider_api_key(settings.llm_api_key):
        raise PostprocessingServiceUnavailableError(
            "Provider API key is missing."
        )

    if not settings.llm_base_url.strip() or not settings.llm_model.strip():
        raise PostprocessingServiceUnavailableError(
            "LLM configuration is incomplete."
        )
    _validate_llm_endpoint(
        base_url=settings.llm_base_url,
        mode=mode,
        allowed_provider_hosts=settings.llm_allowed_provider_hosts,
        public_deployment=settings.public_deployment,
    )

    client = OpenAICompatibleClient(settings)
    try:
        if semantic_coverage_mode == "chunk":
            return _request_engine_payload(
                client=client,
                raw_text=raw_text,
                language=language,
                metadata=metadata,
                coverage_retry=False,
                coverage_retry_hint=None,
                semantic_coverage_mode=semantic_coverage_mode,
                validate_semantic_coverage=False,
            )
        try:
            return _request_engine_payload(
                client=client,
                raw_text=raw_text,
                language=language,
                metadata=metadata,
                coverage_retry=False,
                coverage_retry_hint=None,
                semantic_coverage_mode=semantic_coverage_mode,
                validate_semantic_coverage=True,
            )
        except PostprocessingInsufficientCoverageError as exc:
            first_error = exc
            try:
                payload = _request_engine_payload(
                    client=client,
                    raw_text=raw_text,
                    language=language,
                    metadata=metadata,
                    coverage_retry=True,
                    coverage_retry_hint=exc.retry_hint,
                    semantic_coverage_mode=semantic_coverage_mode,
                    validate_semantic_coverage=True,
                )
            except PostprocessingInsufficientCoverageError as retry_exc:
                raise PostprocessingInsufficientCoverageError(
                    "Post-processing engine returned insufficient semantic "
                    "coverage after quality retry.",
                    retry_hint=retry_exc.retry_hint,
                    rejected_payload=(
                        retry_exc.rejected_payload or first_error.rejected_payload
                    ),
                ) from retry_exc
            payload.processing_notes.append(
                ProcessingNote(
                    type="quality_control",
                    message=(
                        "The first LLM output was rejected for insufficient "
                        "semantic coverage, so E03 generated this result with "
                        "a stricter preservation instruction."
                    ),
                )
            )
            return payload
    except LLMClientTimeoutError as exc:
        raise PostprocessingTimeoutError("Post-processing timed out.") from exc
    except LLMClientUnavailableError as exc:
        raise PostprocessingServiceUnavailableError(
            "Post-processing engine is unavailable."
        ) from exc


def _request_engine_payload(
    *,
    client: OpenAICompatibleClient,
    raw_text: str,
    language: str,
    metadata: TranscriptionMetadata,
    coverage_retry: bool,
    coverage_retry_hint: str | None,
    semantic_coverage_mode: Literal["full", "chunk"],
    validate_semantic_coverage: bool,
) -> PostprocessingPayload:
    completion = client.complete_json(
        messages=_build_messages(
            raw_text=raw_text,
            language=language,
            metadata=metadata,
            coverage_retry=coverage_retry,
            coverage_retry_hint=coverage_retry_hint,
            semantic_coverage_mode=semantic_coverage_mode,
        )
    )
    payload = _payload_from_llm_content(completion.content)
    if not validate_semantic_coverage:
        return payload
    try:
        _validate_semantic_coverage(payload=payload, raw_text=raw_text)
    except PostprocessingInsufficientCoverageError as exc:
        raise PostprocessingInsufficientCoverageError(
            str(exc),
            retry_hint=exc.retry_hint,
            rejected_payload=payload,
        ) from exc
    return payload


def _payload_from_llm_content(content: str) -> PostprocessingPayload:
    try:
        decoded = _decode_llm_json_object(content)
        normalized = _normalize_llm_payload(decoded)
        return PostprocessingPayload.model_validate(normalized)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise PostprocessingInvalidOutputError(
            "Post-processing engine returned invalid output."
        ) from exc


def _build_messages(
    *,
    raw_text: str,
    language: str,
    metadata: TranscriptionMetadata,
    coverage_retry: bool = False,
    coverage_retry_hint: str | None = None,
    semantic_coverage_mode: Literal["full", "chunk"] = "full",
) -> list[dict[str, str]]:
    metadata_payload = metadata.model_dump()
    operational_manual = _load_e03_operational_manual()
    if semantic_coverage_mode == "chunk":
        minimum_didactic_chars = 0
        minimum_themes = 1
        semantic_anchors: tuple[SemanticCoverageAnchor, ...] = ()
    else:
        minimum_didactic_chars = _minimum_didactic_text_chars(raw_text)
        minimum_themes = _minimum_theme_count(raw_text)
        semantic_anchors = _semantic_coverage_anchors(raw_text)
    semantic_anchor_instruction = _semantic_anchor_instruction(semantic_anchors)
    retry_instruction = ""
    if coverage_retry:
        retry_hint = coverage_retry_hint or "The previous output lacked semantic coverage."
        retry_instruction = (
            "\n\nQUALITY RETRY: the previous valid JSON was rejected because it "
            "looked like a summary and did not preserve enough semantic content. "
            f"Concrete rejection reason: {retry_hint}. "
            "Regenerate the full JSON with broader coverage. Expand the "
            "didactic_text and themes. Include projects, case studies, student "
            "contributions, practical pains, examples, metaphors, technologies, "
            "methodological details, and operational consequences that are present "
            "in the raw transcript. Re-check every protected semantic coverage "
            "anchor listed in the user message before returning JSON."
        )

    return [
        {
            "role": "system",
            "content": (
                "You are the Mindvox E03 post-processing engine. Return only one "
                "valid JSON object, with no Markdown and no prose outside JSON. "
                "Use exactly these top-level keys: didactic_text, themes, "
                "technical_terms, technology_mentions, and processing_notes. "
                "Each theme must include order, title, summary, key_points, "
                "semantic_role, and evidence. technical_terms[].confidence, "
                "technology_mentions[].importance, and "
                "technology_mentions[].confidence must use only low, medium, or "
                "high. technology_mentions[].category must use only framework, "
                "library, platform, service, provider, protocol, language, "
                "database, infrastructure, tool, or api. processing_notes must be "
                "a list of objects with type and message. Do not include "
                "corrected_full_text. Do not invent technologies that are not "
                "present or strongly indicated in the raw transcript. The backend "
                "will reject outputs that are too short, have too few themes, or "
                "omit protected semantic coverage anchors.\n\n"
                "Mandatory operational manual:\n"
                f"{operational_manual}"
                f"{retry_instruction}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Language: {language}\n"
                f"Metadata: {json.dumps(metadata_payload, ensure_ascii=True)}\n"
                f"Raw transcript character count: {len(raw_text.strip())}\n"
                "Minimum didactic_text character count for long-transcript "
                f"semantic coverage: {minimum_didactic_chars}\n"
                "Minimum themes count for long-transcript semantic coverage: "
                f"{minimum_themes}\n"
                f"{semantic_anchor_instruction}"
                "Create comprehensive study material from this raw transcript. "
                "This is not an abstract, not an executive summary, and not an "
                "editorial selection of only the teacher's theoretical points. "
                "Preserve the class content as fully as possible and remove only "
                "semantic redundancy, speech noise, false starts, and duplicated "
                "content. The didactic_text must be continuous, logical, readable, "
                "and proportional to the semantic density of the class. If a "
                "minimum didactic_text character count greater than zero is shown "
                "above, satisfy it. Themes "
                "must be structured for future memory ingestion. Technical terms "
                "and technology mentions must be separate. Before returning JSON, "
                "check that named projects, case studies, student contributions, "
                "real-world implementation pains, examples, metaphors, technology "
                "mentions, and methodological details present in the transcript "
                "were not silently omitted. When protected semantic anchors are "
                "listed, keep each listed label visible verbatim at least once in "
                "didactic_text or in the structured fields.\n\n"
                f"Raw transcript:\n{raw_text}"
            ),
        },
    ]


def _validate_semantic_coverage(
    *,
    payload: PostprocessingPayload,
    raw_text: str,
    minimum_didactic_ratio: float = LONG_TRANSCRIPT_MIN_DIDACTIC_RATIO,
    enforce_semantic_anchors: bool = True,
) -> None:
    minimum_didactic_chars = _minimum_didactic_text_chars(
        raw_text,
        minimum_ratio=minimum_didactic_ratio,
    )
    if (
        minimum_didactic_chars
        and len(payload.didactic_text.strip()) < minimum_didactic_chars
    ):
        actual_didactic_chars = len(payload.didactic_text.strip())
        raise PostprocessingInsufficientCoverageError(
            "Post-processing engine returned insufficient semantic coverage.",
            retry_hint=(
                "didactic_text was too short for this long transcript "
                f"({actual_didactic_chars} characters; minimum "
                f"{minimum_didactic_chars})"
            ),
        )

    minimum_themes = _minimum_theme_count(raw_text)
    if len(payload.themes) < minimum_themes:
        raise PostprocessingInsufficientCoverageError(
            "Post-processing engine returned too few semantic themes.",
            retry_hint=(
                "themes list was too small for this long transcript "
                f"({len(payload.themes)} themes; minimum {minimum_themes})"
            ),
        )

    missing_anchors = _missing_semantic_coverage_anchors(
        payload=payload,
        raw_text=raw_text,
    )
    if enforce_semantic_anchors and missing_anchors:
        missing_labels = ", ".join(anchor.label for anchor in missing_anchors[:12])
        raise PostprocessingInsufficientCoverageError(
            "Post-processing engine omitted protected semantic anchors.",
            retry_hint=(
                "output omitted protected semantic coverage anchors: "
                f"{missing_labels}"
            ),
        )


def _append_chunked_semantic_anchor_audit_note(
    *,
    payload: PostprocessingPayload,
    raw_text: str,
) -> None:
    missing_anchors = _missing_semantic_coverage_anchors(
        payload=payload,
        raw_text=raw_text,
    )
    if not missing_anchors:
        return

    missing_labels = ", ".join(anchor.label for anchor in missing_anchors[:12])
    payload.processing_notes.append(
        ProcessingNote(
            type="semantic_anchor_audit",
            message=(
                "Auditoria final do fluxo chunked encontrou ancoras "
                "semanticas protegidas sem cobertura textual suficiente nos "
                f"artefatos principais: {missing_labels}."
            ),
        )
    )


def _minimum_didactic_text_chars(
    raw_text: str,
    *,
    minimum_ratio: float = LONG_TRANSCRIPT_MIN_DIDACTIC_RATIO,
) -> int:
    raw_text_chars = len(raw_text.strip())
    if raw_text_chars < LONG_TRANSCRIPT_SEMANTIC_COVERAGE_MIN_CHARS:
        return 0

    return int(raw_text_chars * minimum_ratio)


def _minimum_theme_count(raw_text: str) -> int:
    if len(raw_text.strip()) < LONG_TRANSCRIPT_SEMANTIC_COVERAGE_MIN_CHARS:
        return 1

    return LONG_TRANSCRIPT_MIN_THEMES


def _semantic_anchor_instruction(
    anchors: tuple[SemanticCoverageAnchor, ...],
) -> str:
    if not anchors:
        return "Protected semantic coverage anchors detected from raw transcript: none\n"

    anchor_lines = "\n".join(f"- {anchor.label}" for anchor in anchors)
    return (
        "Protected semantic coverage anchors detected from raw transcript. "
        "These are not optional summary hints. Preserve each anchor in "
        "didactic_text and, when relevant, in themes, technical_terms, or "
        "technology_mentions:\n"
        f"{anchor_lines}\n"
    )


def _missing_semantic_coverage_anchors(
    *,
    payload: PostprocessingPayload,
    raw_text: str,
) -> tuple[SemanticCoverageAnchor, ...]:
    anchors = _semantic_coverage_anchors(raw_text)
    if not anchors:
        return ()

    output_text = _processed_payload_search_text(payload)
    missing = [
        anchor
        for anchor in anchors
        if not any(_folded_phrase_in_text(alias=alias, text=output_text) for alias in anchor.aliases)
    ]
    allowed_missing = int(
        len(anchors) * (1 - LONG_TRANSCRIPT_MIN_SEMANTIC_ANCHOR_RATIO)
    )
    if len(missing) <= allowed_missing:
        return ()

    return tuple(missing)


def _semantic_coverage_anchors(
    raw_text: str,
) -> tuple[SemanticCoverageAnchor, ...]:
    if len(raw_text.strip()) < LONG_TRANSCRIPT_SEMANTIC_COVERAGE_MIN_CHARS:
        return ()

    folded_raw_text = _fold_search_text(raw_text)
    anchors: list[SemanticCoverageAnchor] = []
    seen_aliases: set[str] = set()

    for label, aliases in PROTECTED_SEMANTIC_PHRASES:
        folded_aliases = tuple(_fold_search_text(alias) for alias in aliases)
        if any(
            _folded_phrase_in_text(alias=alias, text=folded_raw_text)
            for alias in folded_aliases
        ):
            _append_semantic_anchor(
                anchors=anchors,
                seen_aliases=seen_aliases,
                anchor=SemanticCoverageAnchor(label=label, aliases=folded_aliases),
            )

    for label in _student_contribution_names(raw_text):
        folded_label = _fold_search_text(label)
        _append_semantic_anchor(
            anchors=anchors,
            seen_aliases=seen_aliases,
            anchor=SemanticCoverageAnchor(label=label, aliases=(folded_label,)),
        )

    return tuple(anchors[:MAX_SEMANTIC_COVERAGE_ANCHORS])


def _append_semantic_anchor(
    *,
    anchors: list[SemanticCoverageAnchor],
    seen_aliases: set[str],
    anchor: SemanticCoverageAnchor,
) -> None:
    primary_alias = anchor.aliases[0]
    if primary_alias in seen_aliases:
        return

    anchors.append(anchor)
    seen_aliases.update(anchor.aliases)


def _student_contribution_names(raw_text: str) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", raw_text):
        folded_sentence = _fold_search_text(sentence)
        if not any(cue in folded_sentence for cue in STUDENT_CONTRIBUTION_CUES):
            continue

        for match in re.finditer(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁ-ú]{2,}\b", sentence):
            name = match.group(0)
            if name in CAPITALIZED_ANCHOR_STOPWORDS:
                continue
            folded_name = _fold_search_text(name)
            if folded_name in seen:
                continue
            seen.add(folded_name)
            names.append(name)

    return tuple(names)


def _processed_payload_search_text(payload: PostprocessingPayload) -> str:
    parts: list[str] = [payload.didactic_text]
    for theme in payload.themes:
        parts.extend(
            [
                theme.title,
                theme.summary,
                theme.semantic_role,
                theme.evidence or "",
                *theme.key_points,
            ]
        )
    for term in payload.technical_terms:
        parts.extend(
            [
                term.term,
                term.explanation or "",
                term.evidence or "",
                *term.normalized_from,
            ]
        )
    for mention in payload.technology_mentions:
        parts.extend(
            [
                mention.name,
                mention.category,
                mention.context,
                mention.evidence or "",
                *mention.normalized_from,
            ]
        )
    return _fold_search_text(" ".join(parts))


@lru_cache(maxsize=1)
def _load_e03_operational_manual() -> str:
    return E03_POSTPROCESSING_MANUAL_PATH.read_text(encoding="utf-8").strip()


def _processing_engine(*, settings: Settings, mode: str) -> ProcessingEngine:
    if mode == "contract":
        return ProcessingEngine(
            mode="contract",
            name="contract-processor",
            model="contract-mode",
            version="contract-mode",
        )

    provider = _public_provider(settings.llm_provider, fallback=mode)
    return ProcessingEngine(
        mode=mode,
        name=f"{provider}-openai-compatible",
        model=_public_model(settings.llm_model),
        version="unknown",
    )


def _missing_provider_api_key(api_key: str | None) -> bool:
    if api_key is None:
        return True

    normalized = api_key.strip()
    if not normalized:
        return True

    return normalized.lower() in PLACEHOLDER_API_KEYS


def _validate_llm_endpoint(
    *,
    base_url: str,
    mode: str,
    allowed_provider_hosts: tuple[str, ...],
    public_deployment: bool,
) -> None:
    parsed = urlparse(base_url.strip())
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise PostprocessingServiceUnavailableError(
            "LLM endpoint configuration is invalid."
        )

    normalized_hostname = hostname.strip("[]").lower()
    is_local_endpoint = _is_local_or_private_host(hostname)
    if mode == "provider" and (parsed.scheme != "https" or is_local_endpoint):
        raise PostprocessingServiceUnavailableError(
            "Provider endpoint configuration is invalid."
        )
    if mode == "provider" and public_deployment and not allowed_provider_hosts:
        raise PostprocessingServiceUnavailableError(
            "Provider endpoint configuration is invalid."
        )
    if mode == "provider" and allowed_provider_hosts:
        if normalized_hostname not in allowed_provider_hosts:
            raise PostprocessingServiceUnavailableError(
                "Provider endpoint configuration is invalid."
            )
    if mode == "provider" and _provider_hostname_resolves_locally(hostname):
        raise PostprocessingServiceUnavailableError(
            "Provider endpoint configuration is invalid."
        )

    if mode == "local" and not is_local_endpoint:
        raise PostprocessingServiceUnavailableError(
            "Local LLM endpoint configuration is invalid."
        )


def _is_local_or_private_host(hostname: str) -> bool:
    normalized = hostname.strip("[]").lower()
    if normalized in LOCAL_LLM_HOSTNAMES:
        return True

    address = _ip_address_or_none(normalized)
    if address is None:
        return False

    return _is_local_or_private_address(address)


def _provider_hostname_resolves_locally(hostname: str) -> bool:
    normalized = hostname.strip("[]").lower()
    if _ip_address_or_none(normalized) is not None:
        return False

    return any(
        _is_local_or_private_address(address)
        for address in _resolve_host_addresses(normalized)
    )


def _resolve_host_addresses(
    hostname: str,
) -> tuple[ipaddress.IPv4Address | ipaddress.IPv6Address, ...]:
    try:
        address_infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise PostprocessingServiceUnavailableError(
            "LLM endpoint host cannot be resolved."
        ) from exc

    addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    for address_info in address_infos:
        socket_address = address_info[4]
        addresses.add(ipaddress.ip_address(socket_address[0]))

    return tuple(addresses)


def _ip_address_or_none(
    hostname: str,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        return None


def _is_local_or_private_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    return (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _public_provider(provider: str, *, fallback: str) -> str:
    normalized = provider.strip() or fallback
    lower_provider = normalized.lower()

    if any(marker in lower_provider for marker in SENSITIVE_MARKERS):
        return REDACTED_PROVIDER_LABEL

    if PUBLIC_PROVIDER_PATTERN.fullmatch(normalized) is None:
        return REDACTED_PROVIDER_LABEL

    return normalized


def _public_model(model: str) -> str:
    normalized = model.strip()
    lower_model = normalized.lower()

    if not normalized:
        return REDACTED_MODEL_LABEL

    is_path_like = (
        normalized.startswith(("/", "~", "."))
        or "\\" in normalized
        or "://" in normalized
    )
    has_sensitive_marker = any(marker in lower_model for marker in SENSITIVE_MARKERS)

    if (
        is_path_like
        or has_sensitive_marker
        or PUBLIC_MODEL_PATTERN.fullmatch(normalized) is None
    ):
        return REDACTED_MODEL_LABEL

    return normalized


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()

    return stripped


def _decode_llm_json_object(content: str) -> dict[str, Any]:
    stripped = _strip_json_fence(content)
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        decoded = json.loads(_extract_first_json_object(stripped))
    if isinstance(decoded, dict):
        return decoded

    raise TypeError("LLM output root must be a JSON object.")


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("No JSON object found.", text, 0)

    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise json.JSONDecodeError("Unclosed JSON object.", text, start)


def _normalize_llm_payload(decoded: dict[str, Any]) -> dict[str, Any]:
    didactic_text = _required_text(
        _value_from_aliases(
            decoded,
            (
                "didactic_text",
                "didacticText",
                "clean_text",
                "texto_didatico",
                "texto_didatico_continuo",
                "texto didatico",
            ),
        ),
        field_name="didactic_text",
    )
    themes = _normalize_themes(
        _value_from_aliases(decoded, ("themes", "temas", "topics", "topicos")),
        didactic_text=didactic_text,
    )
    technical_terms = _normalize_technical_terms(
        _value_from_aliases(
            decoded,
            (
                "technical_terms",
                "technicalTerms",
                "termos_tecnicos",
                "termos tecnicos",
            ),
        )
    )
    technology_mentions = _normalize_technology_mentions(
        _value_from_aliases(
            decoded,
            (
                "technology_mentions",
                "technologyMentions",
                "tecnologias_mencionadas",
                "tecnologias",
                "tools",
                "ferramentas",
            ),
        )
    )
    processing_notes = _normalize_processing_notes(
        _value_from_aliases(
            decoded,
            (
                "processing_notes",
                "processingNotes",
                "notas_processamento",
                "notas de processamento",
                "notes",
            ),
        )
    )

    return {
        "didactic_text": didactic_text,
        "themes": themes,
        "technical_terms": technical_terms,
        "technology_mentions": technology_mentions,
        "processing_notes": processing_notes,
    }


def _normalize_themes(value: Any, *, didactic_text: str) -> list[dict[str, Any]]:
    normalized_themes: list[dict[str, Any]] = []
    for index, item in enumerate(_as_list(value), start=1):
        if isinstance(item, str):
            summary = _required_text(item, field_name="themes[].summary")
            title = _excerpt(summary, limit=64)
            normalized_themes.append(
                {
                    "order": index,
                    "title": title,
                    "summary": summary,
                    "key_points": [summary],
                    "semantic_role": "tema",
                    "evidence": None,
                }
            )
            continue

        if not isinstance(item, dict):
            continue

        summary = _text_or_none(
            _value_from_aliases(item, ("summary", "resumo", "description", "descricao"))
        )
        key_points = _text_list(
            _value_from_aliases(
                item,
                (
                    "key_points",
                    "keyPoints",
                    "pontos_chave",
                    "pontos principais",
                    "points",
                ),
            )
        )
        title = _text_or_none(
            _value_from_aliases(item, ("title", "titulo", "theme", "tema", "name"))
        )

        if summary is None:
            summary = key_points[0] if key_points else title
        if title is None and summary is not None:
            title = _excerpt(summary, limit=64)
        if title is None or summary is None:
            continue
        if not key_points:
            key_points = [summary]

        normalized_themes.append(
            {
                "order": _positive_int(
                    _value_from_aliases(item, ("order", "ordem", "position")),
                    default=index,
                ),
                "title": title,
                "summary": summary,
                "key_points": key_points,
                "semantic_role": _text_or_none(
                    _value_from_aliases(
                        item,
                        ("semantic_role", "semanticRole", "papel_semantico", "role"),
                    )
                )
                or "tema",
                "evidence": _text_or_none(
                    _value_from_aliases(item, ("evidence", "evidencia", "trecho"))
                ),
            }
        )

    if not normalized_themes:
        summary = _excerpt(didactic_text, limit=240)
        normalized_themes.append(
            {
                "order": 1,
                "title": "Processed class content",
                "summary": summary,
                "key_points": [summary],
                "semantic_role": "tema",
                "evidence": None,
            }
        )

    return normalized_themes


def _normalize_technical_terms(value: Any) -> list[dict[str, Any]]:
    normalized_terms: list[dict[str, Any]] = []
    for item in _as_list(value):
        if isinstance(item, str):
            term = _text_or_none(item)
            if term:
                normalized_terms.append(
                    {
                        "term": term,
                        "normalized_from": [],
                        "explanation": None,
                        "confidence": "medium",
                        "evidence": None,
                    }
                )
            continue

        if not isinstance(item, dict):
            continue

        term = _text_or_none(
            _value_from_aliases(item, ("term", "termo", "name", "nome"))
        )
        if term is None:
            continue

        normalized_terms.append(
            {
                "term": term,
                "normalized_from": _text_list(
                    _value_from_aliases(
                        item,
                        ("normalized_from", "normalizedFrom", "formas_brutas"),
                    )
                ),
                "explanation": _text_or_none(
                    _value_from_aliases(
                        item,
                        (
                            "explanation",
                            "explicacao",
                            "note",
                            "nota",
                            "description",
                            "descricao",
                        ),
                    )
                ),
                "confidence": _confidence(
                    _value_from_aliases(item, ("confidence", "confianca")),
                    default="medium",
                ),
                "evidence": _text_or_none(
                    _value_from_aliases(item, ("evidence", "evidencia", "trecho"))
                ),
            }
        )

    return normalized_terms


def _normalize_technology_mentions(value: Any) -> list[dict[str, Any]]:
    normalized_mentions: list[dict[str, Any]] = []
    for item in _as_list(value):
        if isinstance(item, str):
            name = _text_or_none(item)
            if name:
                normalized_mentions.append(
                    {
                        "name": name,
                        "category": "tool",
                        "context": "Technology mention identified by the LLM.",
                        "importance": "medium",
                        "normalized_from": [],
                        "confidence": "medium",
                        "evidence": None,
                    }
                )
            continue

        if not isinstance(item, dict):
            continue

        name = _text_or_none(
            _value_from_aliases(item, ("name", "nome", "technology", "tecnologia"))
        )
        if name is None:
            continue

        normalized_mentions.append(
            {
                "name": name,
                "category": _technology_category(
                    _value_from_aliases(item, ("category", "categoria")),
                    default="tool",
                ),
                "context": _text_or_none(
                    _value_from_aliases(item, ("context", "contexto", "description"))
                )
                or "Technology mention identified by the LLM.",
                "importance": _confidence(
                    _value_from_aliases(item, ("importance", "importancia")),
                    default="medium",
                ),
                "normalized_from": _text_list(
                    _value_from_aliases(
                        item,
                        ("normalized_from", "normalizedFrom", "formas_brutas"),
                    )
                ),
                "confidence": _confidence(
                    _value_from_aliases(item, ("confidence", "confianca")),
                    default="medium",
                ),
                "evidence": _text_or_none(
                    _value_from_aliases(item, ("evidence", "evidencia", "trecho"))
                ),
            }
        )

    return normalized_mentions


def _normalize_processing_notes(value: Any) -> list[dict[str, str]]:
    normalized_notes: list[dict[str, str]] = []
    for item in _as_list(value):
        if isinstance(item, str):
            message = _text_or_none(item)
            if message:
                normalized_notes.append({"type": "processing", "message": message})
            continue

        if not isinstance(item, dict):
            continue

        message = _text_or_none(
            _value_from_aliases(item, ("message", "mensagem", "note", "nota"))
        )
        if message is None:
            continue
        normalized_notes.append(
            {
                "type": _text_or_none(_value_from_aliases(item, ("type", "tipo")))
                or "processing",
                "message": message,
            }
        )

    if not normalized_notes:
        normalized_notes.append(
            {
                "type": "processing",
                "message": "LLM output normalized to the E03 response schema.",
            }
        )

    return normalized_notes


def _value_from_aliases(data: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in data:
            return data[alias]

    folded_aliases = {_fold_token(alias) for alias in aliases}
    for key, value in data.items():
        if _fold_token(str(key)) in folded_aliases:
            return value

    return None


def _required_text(value: Any, *, field_name: str) -> str:
    text = _text_or_none(value)
    if text is None:
        raise TypeError(f"{field_name} must be a non-empty string.")
    return text


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else None
    if isinstance(value, (int, float, bool)):
        return str(value)
    return None


def _text_list(value: Any) -> list[str]:
    texts: list[str] = []
    for item in _as_list(value):
        text = _text_or_none(item)
        if text is not None:
            texts.append(text)
    return texts


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return [value]
    return [value]


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < 1:
        return default
    return parsed


def _confidence(value: Any, *, default: str) -> str:
    text = _text_or_none(value)
    if text is None:
        return default
    return CONFIDENCE_ALIASES.get(_fold_token(text), default)


def _technology_category(value: Any, *, default: str) -> str:
    text = _text_or_none(value)
    if text is None:
        return default
    return TECHNOLOGY_CATEGORY_ALIASES.get(_fold_token(text), default)


def _fold_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    ascii_value = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"[\s_-]+", " ", ascii_value).strip()


def _fold_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    ascii_value = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", " ", ascii_value).strip()


def _folded_phrase_in_text(*, alias: str, text: str) -> bool:
    if not alias:
        return False

    pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _excerpt(text: str, *, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."


def _short_excerpt(raw_text: str) -> str:
    cleaned = " ".join(raw_text.split())
    if len(cleaned) <= 120:
        return cleaned

    return f"{cleaned[:117]}..."


def _new_processed_transcription_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"ptr_{timestamp}_{token_hex(4)}"
