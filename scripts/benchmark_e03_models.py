#!/usr/bin/env python3
"""Internal benchmark for E03 post-processing model candidates.

This script is intentionally outside the canonical endpoint specs. It compares
OpenAI-compatible LLM targets using the same raw transcript sample and records
basic operational and contract metrics for model selection.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from schemas.transcriptions import TranscriptionMetadata  # noqa: E402
from services.postprocessing_service import (  # noqa: E402
    PostprocessingInvalidOutputError,
    _build_messages,
    _payload_from_llm_content,
    _validate_semantic_coverage,
)


DEFAULT_OUTPUT_DIR = Path(".benchmarks/e03_models")
BENCHMARK_RESPONSE_BYTES_PER_OUTPUT_TOKEN = 16
MIN_BENCHMARK_RESPONSE_BYTES = 65536


@dataclass(frozen=True)
class Candidate:
    name: str
    base_url: str
    model: str
    api_key: str
    api_key_source: str


@dataclass
class BenchmarkResult:
    candidate: str
    base_url: str
    model: str
    status: str
    elapsed_seconds: float
    input_chars: int
    output_chars: int
    json_valid: bool
    required_fields_present: bool
    themes_count: int
    technical_terms_count: int
    technology_mentions_count: int
    semantic_coverage_valid: bool
    error: str | None
    output_text: str
    parsed_output: dict[str, Any] | None


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE lines without overriding existing environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def default_candidates() -> list[Candidate]:
    groq_key = os.getenv("MINDVOX_LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    groq_key_source = "MINDVOX_LLM_API_KEY" if os.getenv("MINDVOX_LLM_API_KEY") else "GROQ_API_KEY"
    return [
        Candidate(
            name="local-light",
            base_url=os.getenv("MINDVOX_LOCAL_LIGHT_BASE_URL", "http://127.0.0.1:8080/v1"),
            model=os.getenv("MINDVOX_LOCAL_LIGHT_MODEL", "Qwen3.6-35B-A3B-MTP-Q8.gguf"),
            api_key=os.getenv("MINDVOX_LOCAL_LIGHT_API_KEY", "local"),
            api_key_source="MINDVOX_LOCAL_LIGHT_API_KEY or local",
        ),
        Candidate(
            name="local-heavy",
            base_url=os.getenv("MINDVOX_LOCAL_HEAVY_BASE_URL", "http://127.0.0.1:8082/v1"),
            model=os.getenv("MINDVOX_LOCAL_HEAVY_MODEL", "Qwen3.6-27B-MTP-Q8_0.gguf"),
            api_key=os.getenv("MINDVOX_LOCAL_HEAVY_API_KEY", "local"),
            api_key_source="MINDVOX_LOCAL_HEAVY_API_KEY or local",
        ),
        Candidate(
            name="groq",
            base_url=os.getenv("MINDVOX_LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            model=os.getenv("MINDVOX_LLM_MODEL", "llama-3.3-70b-versatile"),
            api_key=groq_key or "",
            api_key_source=groq_key_source,
        ),
    ]


def custom_candidate(values: list[str]) -> Candidate:
    name, base_url, model, api_key_env = values
    api_key = os.getenv(api_key_env, "")
    return Candidate(
        name=name,
        base_url=base_url.rstrip("/"),
        model=model,
        api_key=api_key,
        api_key_source=api_key_env,
    )


def read_input(args: argparse.Namespace) -> str:
    if args.input_text:
        text = args.input_text
    else:
        text = Path(args.input_file).read_text(encoding="utf-8")

    text = text.strip()
    if not text:
        raise SystemExit("Input text is empty.")
    if len(text) > args.max_input_chars:
        return text[: args.max_input_chars]
    return text


def build_prompt(raw_text: str, case_name: str, language: str) -> list[dict[str, str]]:
    _ = case_name
    return _build_messages(
        raw_text=raw_text,
        language=language,
        metadata=TranscriptionMetadata(),
    )


def post_chat_completion(
    candidate: Candidate,
    messages: list[dict[str, str]],
    timeout: float,
    temperature: float,
    max_tokens: int,
) -> str:
    url = f"{candidate.base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": candidate.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    if _is_local_base_url(candidate.base_url) and _is_qwen_model(candidate.model):
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {candidate.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        max_response_bytes = max(
            MIN_BENCHMARK_RESPONSE_BYTES,
            max_tokens * BENCHMARK_RESPONSE_BYTES_PER_OUTPUT_TOKEN,
        )
        response_body_bytes = response.read(max_response_bytes + 1)
        if len(response_body_bytes) > max_response_bytes:
            raise RuntimeError("Provider returned too much data.")
        response_body = response_body_bytes.decode("utf-8")

    data = json.loads(response_body)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Provider returned no choices.")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Provider returned empty message content.")
    return content.strip()


def _is_local_base_url(base_url: str) -> bool:
    return "127.0.0.1" in base_url or "localhost" in base_url


def _is_qwen_model(model: str) -> bool:
    return "qwen" in model.casefold()


def extract_json_object(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def evaluate_output(candidate: Candidate, raw_text: str, output_text: str, elapsed: float) -> BenchmarkResult:
    parsed = extract_json_object(output_text)
    required_fields_present = False
    semantic_coverage_valid = False
    themes_count = 0
    technical_terms_count = 0
    technology_mentions_count = 0
    error = None

    if parsed is not None:
        themes = parsed.get("themes")
        technical_terms = parsed.get("technical_terms")
        technology_mentions = parsed.get("technology_mentions")
        required_fields_present = (
            isinstance(parsed.get("didactic_text"), str)
            and isinstance(themes, list)
            and isinstance(technical_terms, list)
            and isinstance(technology_mentions, list)
            and isinstance(parsed.get("processing_notes"), list)
        )
        themes_count = len(themes) if isinstance(themes, list) else 0
        technical_terms_count = len(technical_terms) if isinstance(technical_terms, list) else 0
        technology_mentions_count = len(technology_mentions) if isinstance(technology_mentions, list) else 0
        try:
            payload = _payload_from_llm_content(output_text)
            _validate_semantic_coverage(payload=payload, raw_text=raw_text)
            semantic_coverage_valid = True
        except PostprocessingInvalidOutputError as exc:
            error = f"{type(exc).__name__}: {exc}"

    status = "pass" if parsed is not None and required_fields_present and semantic_coverage_valid else "warn"
    return BenchmarkResult(
        candidate=candidate.name,
        base_url=candidate.base_url,
        model=candidate.model,
        status=status,
        elapsed_seconds=elapsed,
        input_chars=len(raw_text),
        output_chars=len(output_text),
        json_valid=parsed is not None,
        required_fields_present=required_fields_present,
        themes_count=themes_count,
        technical_terms_count=technical_terms_count,
        technology_mentions_count=technology_mentions_count,
        semantic_coverage_valid=semantic_coverage_valid,
        error=error,
        output_text=output_text,
        parsed_output=parsed,
    )


def failure_result(candidate: Candidate, raw_text: str, elapsed: float, error: Exception) -> BenchmarkResult:
    return BenchmarkResult(
        candidate=candidate.name,
        base_url=candidate.base_url,
        model=candidate.model,
        status="fail",
        elapsed_seconds=elapsed,
        input_chars=len(raw_text),
        output_chars=0,
        json_valid=False,
        required_fields_present=False,
        themes_count=0,
        technical_terms_count=0,
        technology_mentions_count=0,
        semantic_coverage_valid=False,
        error=f"{type(error).__name__}: {error}",
        output_text="",
        parsed_output=None,
    )


def run_candidate(
    candidate: Candidate,
    raw_text: str,
    args: argparse.Namespace,
) -> BenchmarkResult:
    if not candidate.api_key:
        return failure_result(candidate, raw_text, 0.0, RuntimeError(f"Missing API key: {candidate.api_key_source}"))

    messages = build_prompt(raw_text, args.case_name, args.language)
    started = time.perf_counter()
    try:
        output_text = post_chat_completion(
            candidate=candidate,
            messages=messages,
            timeout=args.timeout,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        elapsed = time.perf_counter() - started
        return evaluate_output(candidate, raw_text, output_text, elapsed)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        elapsed = time.perf_counter() - started
        return failure_result(candidate, raw_text, elapsed, exc)


def write_report(
    run_dir: Path,
    results: list[BenchmarkResult],
    raw_text: str,
    args: argparse.Namespace,
) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_name": args.case_name,
        "language": args.language,
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        },
        "input_chars": len(raw_text),
        "results": [asdict(result) for result in results],
    }
    (run_dir / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E03 Model Benchmark",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Case: `{args.case_name}`",
        f"- Input chars: {len(raw_text)}",
        "",
        "| Candidate | Status | Time | JSON | Fields | Coverage | Themes | Terms | Tech mentions | Model |",
        "| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            f"{result.candidate} | "
            f"{result.status} | "
            f"{result.elapsed_seconds:.2f}s | "
            f"{'yes' if result.json_valid else 'no'} | "
            f"{'yes' if result.required_fields_present else 'no'} | "
            f"{'yes' if result.semantic_coverage_valid else 'no'} | "
            f"{result.themes_count} | "
            f"{result.technical_terms_count} | "
            f"{result.technology_mentions_count} | "
            f"`{result.model}` |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `pass` means the provider returned valid JSON with the minimum E03 fields and passed the same semantic coverage gate used by the endpoint.",
            "- This benchmark does not replace human quality review.",
            "- Real transcript contents and model outputs are stored in `results.json`; keep this folder out of Git.",
        ]
    )
    (run_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark E03 LLM post-processing candidates.")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input-file", help="Raw transcript text file.")
    input_group.add_argument("--input-text", help="Raw transcript text passed directly.")
    parser.add_argument("--case-name", default="manual-e03-benchmark", help="Human-readable test case name.")
    parser.add_argument("--language", default="pt-BR", help="Source language label.")
    parser.add_argument("--target", action="append", choices=["local-light", "local-heavy", "groq"], help="Default target to run. Can be repeated. Defaults to all.")
    parser.add_argument(
        "--candidate",
        action="append",
        nargs=4,
        metavar=("NAME", "BASE_URL", "MODEL", "API_KEY_OR_ENV"),
        help="Custom OpenAI-compatible candidate. API_KEY_OR_ENV must be an environment variable name, not a literal key.",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds.")
    parser.add_argument("--temperature", type=float, default=0.1, help="Generation temperature.")
    parser.add_argument("--max-tokens", type=int, default=3000, help="Maximum output tokens.")
    parser.add_argument("--max-input-chars", type=int, default=100000, help="Maximum input chars sent to each model.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for benchmark outputs.")
    return parser


def main() -> int:
    load_dotenv(Path(".env"))
    args = build_parser().parse_args()
    raw_text = read_input(args)

    candidates = [] if args.candidate and not args.target else default_candidates()
    if args.target:
        selected = set(args.target)
        candidates = [candidate for candidate in default_candidates() if candidate.name in selected]
    if args.candidate:
        candidates.extend(custom_candidate(values) for values in args.candidate)
    if not candidates:
        raise SystemExit("No candidates selected.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.output_dir) / f"{timestamp}_{args.case_name}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"E03 benchmark case: {args.case_name}")
    print(f"Input chars sent: {len(raw_text)}")
    print(f"Output directory: {run_dir}")

    results: list[BenchmarkResult] = []
    for candidate in candidates:
        print(f"\nRunning {candidate.name}: {candidate.model} @ {candidate.base_url}")
        result = run_candidate(candidate, raw_text, args)
        results.append(result)
        print(
            f"  status={result.status} time={result.elapsed_seconds:.2f}s "
            f"json={result.json_valid} fields={result.required_fields_present} "
            f"themes={result.themes_count} terms={result.technical_terms_count} "
            f"tech_mentions={result.technology_mentions_count}"
        )
        if result.error:
            print(f"  error={result.error}")

    write_report(run_dir, results, raw_text, args)
    print(f"\nSaved: {run_dir / 'results.json'}")
    print(f"Saved: {run_dir / 'README.md'}")
    return 0 if any(result.status == "pass" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
