#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_VAULT_PATH = Path(
    "/Users/adalbertobatista/Library/Mobile Documents/iCloud~md~obsidian/Documents/UFG_Pos_2"
)
DEFAULT_NOTE = Path("00_Inbox/_captura-rapida.md")
DEFAULT_OUTPUT_DIR = Path("inputs/e03_raw_texts")


@dataclass(frozen=True)
class PreparedTranscript:
    output_path: Path
    metadata_path: Path
    text: str
    metadata: dict[str, str]
    e03_form_metadata: dict[str, str]

    @property
    def char_count(self) -> int:
        return len(self.text)


def prepare_transcript(
    *,
    note_path: Path,
    section: int,
    output_dir: Path,
    output_name: str | None = None,
) -> PreparedTranscript:
    content = note_path.read_text(encoding="utf-8")
    metadata = _parse_frontmatter(content)
    section_text = extract_session_section(content, section=section)
    transcript = extract_transcription_block(section_text)
    if not transcript:
        raise ValueError(
            f"No transcription text found in section {section} of {note_path}."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (output_name or _default_output_name(metadata, section))
    output_path.write_text(transcript + "\n", encoding="utf-8")
    e03_form_metadata = _e03_form_metadata(metadata=metadata, vault_path=note_path)
    metadata_path = output_path.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(
            {
                "raw_text_file": str(output_path.resolve()),
                "capture_section": section,
                "vault_frontmatter": metadata,
                "e03_form": e03_form_metadata,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return PreparedTranscript(
        output_path=output_path,
        metadata_path=metadata_path,
        text=transcript,
        metadata=metadata,
        e03_form_metadata=e03_form_metadata,
    )


def extract_session_section(markdown: str, *, section: int) -> str:
    heading_re = re.compile(r"^##\s+.*Sess[aã]o\s+(\d+)\b.*$", flags=re.IGNORECASE)
    lines = markdown.splitlines()
    start: int | None = None
    end = len(lines)
    for index, line in enumerate(lines):
        match = heading_re.match(line.strip())
        if not match:
            continue
        found = int(match.group(1))
        if found == section:
            start = index + 1
            continue
        if start is not None:
            end = index
            break

    if start is None:
        raise ValueError(f"Section {section} not found.")

    return "\n".join(lines[start:end]).strip()


def extract_transcription_block(section_text: str) -> str:
    lines = section_text.splitlines()
    start = 0
    for index, line in enumerate(lines):
        if _normalize(line) == "transcricao":
            start = index + 1
            break

    selected = lines[start:]
    selected = _drop_leading_non_transcript_lines(selected)
    return _clean_transcript("\n".join(selected))


def _drop_leading_non_transcript_lines(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if re.match(r"^\s*\d{1,2}:\d{2}(?::\d{2})?\s*$", line):
            return lines[index:]
    return lines


def _clean_transcript(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_frontmatter(markdown: str) -> dict[str, str]:
    if not markdown.startswith("---\n"):
        return {}
    end = markdown.find("\n---", 4)
    if end < 0:
        return {}

    metadata: dict[str, str] = {}
    for line in markdown[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = _clean_metadata_value(value.strip())
    return metadata


def _clean_metadata_value(value: str) -> str:
    value = value.strip().strip('"').strip("'")
    wiki_match = re.search(r"\[\[[^|\]]+\|([^\]]+)\]\]", value)
    if wiki_match:
        return wiki_match.group(1).strip()
    return value


def _default_output_name(metadata: dict[str, str], section: int) -> str:
    date = metadata.get("data") or "sem-data"
    discipline = _slug(metadata.get("disciplina") or "disciplina")
    professor = _slug(metadata.get("professor") or "professor")
    class_number = _slug(metadata.get("aula") or "aula")
    active_session = _slug(metadata.get("sessao-ativa") or str(section))
    return (
        f"{date}-{discipline}-{professor}-aula-{class_number}"
        f"-sessao-{active_session}.txt"
    )


def _e03_form_metadata(*, metadata: dict[str, str], vault_path: Path) -> dict[str, str]:
    discipline = metadata.get("disciplina") or ""
    professor = metadata.get("professor") or ""
    class_number = metadata.get("aula") or ""
    class_date = metadata.get("data") or ""
    session = metadata.get("sessao-ativa") or ""
    session_label = _session_label(class_number=class_number, session=session)
    course_name = _course_from_vault_path(vault_path)

    title_parts = [
        part
        for part in [
            discipline,
            f"Aula {class_number}" if class_number else "",
            f"Sessão {session}" if session else "",
            f"Professor {professor}" if professor else "",
        ]
        if part
    ]
    return {
        "input_type": "raw_text",
        "language": "pt-BR",
        "processing_profile": "study_notes",
        "course": course_name,
        "discipline": discipline,
        "class_date": class_date,
        "class_title": " - ".join(title_parts),
        "session_label": session_label,
    }


def _session_label(*, class_number: str, session: str) -> str:
    class_digits = re.sub(r"\D+", "", class_number)
    session_digits = re.sub(r"\D+", "", session)
    if class_digits and session_digits:
        return f"A{class_digits}S{session_digits}"
    if session_digits:
        return f"S{session_digits}"
    return ""


def _course_from_vault_path(vault_path: Path) -> str:
    parts = list(vault_path.parts)
    for index, part in enumerate(parts):
        if part == "Documents" and index + 1 < len(parts):
            return parts[index + 1].replace("_", " ")
    return "UFG Pos 2"


def _slug(value: str) -> str:
    value = _strip_accents(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "sem-valor"


def _normalize(value: str) -> str:
    return _strip_accents(value).strip().lower()


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a raw transcript from UFG_Pos_2/00_Inbox/_captura-rapida.md "
            "and save a .txt ready for E03 raw_text_file upload."
        )
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=DEFAULT_VAULT_PATH,
        help="Path to the Obsidian vault.",
    )
    parser.add_argument(
        "--note",
        type=Path,
        default=DEFAULT_NOTE,
        help="Note path relative to the vault, or an absolute note path.",
    )
    parser.add_argument(
        "--section",
        type=int,
        required=True,
        help="Capture section number inside _captura-rapida.md, for example 4.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the prepared .txt will be written.",
    )
    parser.add_argument(
        "--output-name",
        help="Optional output filename. Defaults to metadata-based filename.",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="After preparing the files, submit the generated .metadata.json to E03.",
    )
    parser.add_argument(
        "--copy-swagger-fields",
        action="store_true",
        help=(
            "Copy the prepared E03 form fields to the macOS clipboard for "
            "manual Swagger use."
        ),
    )
    parser.add_argument(
        "--open-swagger",
        action="store_true",
        help=(
            "Print the local Swagger URL after preparing. It does not open the "
            "browser automatically, to avoid resetting a page already authorized "
            "or already in Try it out mode."
        ),
    )
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:8000/processed-transcriptions/v1.0.0",
        help="E03 endpoint URL used with --submit.",
    )
    parser.add_argument(
        "--token",
        help="Bearer token used with --submit. Defaults to MINDVOX_API_TOKEN or dev-token.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1800,
        help="E03 request timeout in seconds used with --submit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    note_path = args.note if args.note.is_absolute() else args.vault / args.note

    try:
        prepared = prepare_transcript(
            note_path=note_path,
            section=args.section,
            output_dir=args.output_dir,
            output_name=args.output_name,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Arquivo preparado: {prepared.output_path}")
    print(f"Caminho absoluto: {prepared.output_path.resolve()}")
    print(f"Metadados E03: {prepared.metadata_path}")
    print(f"Caracteres: {prepared.char_count}")
    if prepared.metadata:
        print("Metadados detectados:")
        for key in ["disciplina", "professor", "aula", "data", "sessao-ativa"]:
            if key in prepared.metadata:
                print(f"- {key}: {prepared.metadata[key]}")
    print("")
    print("Campos preparados para o formulario E03:")
    for key, value in prepared.e03_form_metadata.items():
        print(f"- {key}: {value}")
    print("- raw_text_file:", prepared.output_path)
    print("- raw_text vazio")
    print("- audio_file vazio")
    if args.copy_swagger_fields:
        try:
            _copy_to_clipboard(_swagger_fields_text(prepared))
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print("")
        print("Campos do Swagger copiados para a area de transferencia.")
    if args.open_swagger:
        print("")
        print(
            "Swagger URL: http://127.0.0.1:8000/docs"
        )
        print(
            "Nao abri o navegador automaticamente para nao perder Authorize, "
            "Try it out ou campos ja preenchidos."
        )
    if not args.submit:
        print("")
        print("Para enviar automaticamente ao endpoint E03 sem usar a tela do Swagger, rode:")
        print(f"uv run python scripts/submit_e03_raw_text.py {prepared.metadata_path}")
        print("")
        print("Ou refaca preparo e envio em um unico comando:")
        print(
            "uv run python scripts/prepare_e03_raw_text_from_vault.py "
            f"--section {args.section} --submit"
        )
    if args.submit:
        import httpx

        from scripts.submit_e03_raw_text import submit_prepared_raw_text

        print("")
        print("Submetendo transcrito preparado diretamente ao endpoint E03...")
        try:
            response = submit_prepared_raw_text(
                metadata_path=prepared.metadata_path,
                endpoint=args.endpoint,
                token=args.token,
                timeout_seconds=args.timeout,
            )
        except (httpx.HTTPError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(
            "Processed transcription ID:",
            response.get("processed_transcription_id"),
        )
        artifact_locations = response.get("artifact_locations") or {}
        if artifact_locations:
            print("Artifacts:")
            for key, value in artifact_locations.items():
                print(f"- {key}: {value}")
    return 0


def _swagger_fields_text(prepared: PreparedTranscript) -> str:
    lines = ["Swagger E03 - campos preparados"]
    for key, value in prepared.e03_form_metadata.items():
        lines.append(f"{key}: {value}")
    lines.extend(
        [
            f"raw_text_file: {prepared.output_path.resolve()}",
            "raw_text: vazio",
            "audio_file: vazio",
        ]
    )
    return "\n".join(lines) + "\n"


def _copy_to_clipboard(text: str) -> None:
    try:
        subprocess.run(
            ["pbcopy"],
            input=text,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Unable to copy Swagger fields to clipboard.") from exc


if __name__ == "__main__":
    raise SystemExit(main())
