#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx


DEFAULT_ENDPOINT = "http://127.0.0.1:8000/processed-transcriptions/v1.0.0"
DEFAULT_TOKEN = "dev-token"


def submit_prepared_raw_text(
    *,
    metadata_path: Path,
    endpoint: str = DEFAULT_ENDPOINT,
    token: str | None = None,
    timeout_seconds: float = 1800,
) -> dict[str, Any]:
    payload = _load_metadata_payload(metadata_path)
    e03_form = payload["e03_form"]
    raw_text_file = Path(payload["raw_text_file"]).expanduser()
    if not raw_text_file.exists():
        raise FileNotFoundError(f"raw_text_file not found: {raw_text_file}")

    data = {
        "input_type": "raw_text_file",
        "language": e03_form.get("language", "pt-BR"),
        "processing_profile": e03_form.get("processing_profile", "study_notes"),
        "course": e03_form.get("course", ""),
        "discipline": e03_form.get("discipline", ""),
        "class_date": e03_form.get("class_date", ""),
        "class_title": e03_form.get("class_title", ""),
        "session_label": e03_form.get("session_label", ""),
    }
    headers = {"Authorization": f"Bearer {token or _token_from_environment()}"}

    with raw_text_file.open("rb") as file_handle:
        response = httpx.post(
            endpoint,
            headers=headers,
            data=data,
            files={
                "raw_text_file": (
                    raw_text_file.name,
                    file_handle,
                    "text/plain",
                )
            },
            timeout=timeout_seconds,
        )

    response.raise_for_status()
    return response.json()


def _load_metadata_payload(metadata_path: Path) -> dict[str, Any]:
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("metadata JSON must contain an object.")
    if not isinstance(data.get("e03_form"), dict):
        raise ValueError("metadata JSON must contain e03_form object.")
    if not data.get("raw_text_file"):
        raise ValueError("metadata JSON must contain raw_text_file.")
    return data


def _token_from_environment() -> str:
    token = os.environ.get("MINDVOX_API_TOKEN", "").strip()
    return token or DEFAULT_TOKEN


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Submit a prepared E03 raw transcript using its .metadata.json as "
            "the source of truth for Swagger/form fields."
        )
    )
    parser.add_argument(
        "metadata_json",
        type=Path,
        help="Path to inputs/e03_raw_texts/*.metadata.json.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"E03 endpoint URL. Default: {DEFAULT_ENDPOINT}",
    )
    parser.add_argument(
        "--token",
        help=(
            "Bearer token. Defaults to MINDVOX_API_TOKEN or dev-token in local "
            "development."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1800,
        help="Request timeout in seconds. Default: 1800.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        response = submit_prepared_raw_text(
            metadata_path=args.metadata_json,
            endpoint=args.endpoint,
            token=args.token,
            timeout_seconds=args.timeout,
        )
    except (httpx.HTTPError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Processed transcription ID: {response.get('processed_transcription_id')}")
    artifact_locations = response.get("artifact_locations") or {}
    if artifact_locations:
        print("Artifacts:")
        for key, value in artifact_locations.items():
            print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
