from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from settings import Settings


class StudentVaultScaffoldError(Exception):
    """Raised when a deterministic Student Vault cannot be created."""


@dataclass(frozen=True)
class StudentVaultScaffold:
    vault_path: Path
    course_id: str
    course_name: str
    institution: str | None
    created_paths: tuple[Path, ...]


def create_student_vault(
    *,
    course_name: str,
    settings: Settings,
    course_id: str | None = None,
    institution: str | None = None,
    base_dir: str | Path | None = None,
) -> StudentVaultScaffold:
    if not settings.e03_obsidian_vault_create_only:
        raise StudentVaultScaffoldError("Student Vault v1 only supports create-only mode.")

    cleaned_course_name = _required(course_name, "course_name")
    cleaned_course_id = _slug(course_id or cleaned_course_name)
    cleaned_institution = _optional(institution)
    vault_base = _vault_base_dir(base_dir=base_dir, settings=settings)
    vault_path = vault_base / cleaned_course_id

    if vault_path.exists() and any(vault_path.iterdir()):
        raise StudentVaultScaffoldError(
            "Refusing to create Student Vault over an existing non-empty directory."
        )

    created_paths: list[Path] = []
    for directory in _canonical_directories(cleaned_course_id):
        path = vault_path / directory
        path.mkdir(parents=True, exist_ok=True)
        created_paths.append(path)

    files = _canonical_files(
        course_id=cleaned_course_id,
        course_name=cleaned_course_name,
        institution=cleaned_institution,
    )
    for relative_path, content in files.items():
        path = vault_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created_paths.append(path)

    return StudentVaultScaffold(
        vault_path=vault_path,
        course_id=cleaned_course_id,
        course_name=cleaned_course_name,
        institution=cleaned_institution,
        created_paths=tuple(created_paths),
    )


def _vault_base_dir(*, base_dir: str | Path | None, settings: Settings) -> Path:
    configured = base_dir or settings.e03_obsidian_vaults_base_dir
    if configured is None:
        raise StudentVaultScaffoldError(
            "MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR is required to create a Student Vault."
        )

    path = Path(configured).expanduser()
    if not path.is_absolute():
        raise StudentVaultScaffoldError("Student Vault base directory must be absolute.")
    return path


def _canonical_directories(course_id: str) -> tuple[Path, ...]:
    return (
        Path("00-Inbox"),
        Path("01-Cursos") / course_id,
        Path("01-Cursos") / course_id / "disciplinas",
        Path("02-Conceitos"),
        Path("03-Operacional"),
        Path("03-Imagens"),
        Path("03-Audios"),
        Path("_templates"),
    )


def _canonical_files(
    *,
    course_id: str,
    course_name: str,
    institution: str | None,
) -> dict[Path, str]:
    frontmatter = [
        "---",
        "tipo: captura-rapida",
        f"curso: {course_name}",
        "disciplina: ",
        "professor: ",
        "aula: ",
        "data: ",
        "sessao-ativa: 1",
        "status: captura",
        "---",
        "",
    ]
    return {
        Path("README.md"): _readme_content(
            course_id=course_id,
            course_name=course_name,
            institution=institution,
        ),
        Path("00-Inbox") / "_captura-rapida.md": "\n".join(frontmatter)
        + _capture_sections(),
        Path("03-Operacional") / "_captura-operacional.md": (
            "---\n"
            "tipo: captura-operacional\n"
            "data: \n"
            "status: captura\n"
            "---\n\n"
            "# Captura operacional\n\n"
            "-\n"
        ),
        Path("03-Operacional") / "links-de-aula.md": "# Links de aula\n\n",
        Path("03-Operacional") / "contatos.md": "# Contatos\n\n",
        Path("03-Operacional") / "canais-e-comunidades.md": "# Canais e comunidades\n\n",
        Path("03-Operacional") / "prazos-e-eventos.md": "# Prazos e eventos\n\n",
        Path("03-Operacional") / "documentos-institucionais.md": (
            "# Documentos institucionais\n\n"
        ),
        Path("01-Cursos") / course_id / "_index.md": _course_index_content(
            course_id=course_id,
            course_name=course_name,
            institution=institution,
        ),
        Path("_templates") / "nota-aula.md": _template_note_content(),
    }


def _readme_content(
    *,
    course_id: str,
    course_name: str,
    institution: str | None,
) -> str:
    lines = [
        f"# {course_name}",
        "",
        "Vault criado deterministicamente pelo Mindvox E03.",
        "",
        f"- course_id: `{course_id}`",
    ]
    if institution:
        lines.append(f"- institution: `{institution}`")
    lines.extend(
        [
            "",
            "Este Vault e opcional. O registro relacional principal do Mindvox deve ser SQLite.",
        ]
    )
    return "\n".join(lines) + "\n"


def _course_index_content(
    *,
    course_id: str,
    course_name: str,
    institution: str | None,
) -> str:
    institution_line = f"institution: {institution}" if institution else "institution: "
    return (
        "---\n"
        "tipo: curso\n"
        f"course_id: {course_id}\n"
        f"course_name: {course_name}\n"
        f"{institution_line}\n"
        "status: ativo\n"
        "---\n\n"
        f"# {course_name}\n\n"
        "## Disciplinas\n\n"
        "-\n"
    )


def _capture_sections() -> str:
    sections = [
        ("🔵", "1", "Manha - Inicio"),
        ("🟢", "2", "Manha - Continuacao"),
        ("🟡", "3", "Tarde - Inicio"),
        ("🔴", "4", "Tarde - Continuacao"),
    ]
    body: list[str] = ["# Captura rapida", ""]
    for icon, number, label in sections:
        body.extend(
            [
                "---",
                "",
                f"## {icon} Sessão {number} · {label}",
                "",
                "<!-- Fragmentos desta sessão. -->",
                "",
                "-",
                "",
            ]
        )
    return "\n".join(body)


def _template_note_content() -> str:
    return (
        "---\n"
        "tipo: nota-aula\n"
        "disciplina: \n"
        "data: \n"
        "professor: \n"
        "tema: \n"
        "status: processado\n"
        "---\n\n"
        "# Nota de aula\n\n"
    )


def _required(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise StudentVaultScaffoldError(f"{field_name} is required.")
    return cleaned


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", _required(value, "course_id"))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    if not slug:
        raise StudentVaultScaffoldError("course_id is invalid.")
    return slug[:80]
