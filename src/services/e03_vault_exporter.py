from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from schemas.processed_transcriptions import StudyPackage


class StudentVaultExportError(Exception):
    """Raised when a Study Package cannot be exported to a Student Vault."""


@dataclass(frozen=True)
class StudentVaultExport:
    vault_path: Path
    written_paths: tuple[Path, ...]


def export_study_package_to_vault(
    *,
    study_package: StudyPackage,
    vault_path: str | Path,
) -> StudentVaultExport:
    root = Path(vault_path).expanduser()
    if not root.exists() or not root.is_dir():
        raise StudentVaultExportError("Student Vault path must be an existing directory.")

    course_id = _required_slug(
        study_package.metadata.course_id or study_package.metadata.course_name,
        "course_id",
    )
    discipline_name = study_package.metadata.discipline or "Disciplina"
    discipline_id = _slug(discipline_name)
    class_number = _class_number(study_package.metadata.class_number)
    class_date = study_package.metadata.class_date or "sem-data"
    session_number = _session_number(study_package)

    discipline_dir = root / "01-Cursos" / course_id / discipline_id
    aulas_dir = discipline_dir / "aulas"
    brutos_dir = discipline_dir / "brutos"
    resumos_dir = discipline_dir / "resumos"
    entregas_dir = discipline_dir / "entregas"
    concepts_dir = root / "02-Conceitos"
    operational_dir = root / "03-Operacional"

    for directory in (
        aulas_dir,
        brutos_dir,
        resumos_dir,
        entregas_dir,
        concepts_dir,
        operational_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    stem = _artifact_stem(
        class_number=class_number,
        class_date=class_date,
        session_number=session_number,
    )
    written_paths: list[Path] = []

    written_paths.append(
        _write_text_atomic(
            aulas_dir / f"{stem}.md",
            _didactic_note_markdown(study_package=study_package),
        )
    )
    written_paths.append(
        _write_text_atomic(
            brutos_dir / f"{stem}_bruto.md",
            _raw_note_markdown(study_package=study_package),
        )
    )
    written_paths.append(
        _write_text_atomic(
            resumos_dir
            / f"Resumo_{discipline_id}_{class_date}{_session_suffix(session_number)}.md",
            _summary_note_markdown(study_package=study_package),
        )
    )

    for concept in study_package.concept_candidates:
        concept_title = concept.title.strip()
        if not concept_title:
            continue
        written_paths.append(
            _write_text_atomic(
                concepts_dir / f"{_slug(concept_title)}.md",
                _concept_markdown(
                    title=concept_title,
                    source=concept.source,
                    summary=concept.summary,
                    confidence=concept.confidence,
                    study_package=study_package,
                ),
            )
        )

    written_paths.extend(_write_operational_anchors(study_package, operational_dir))

    return StudentVaultExport(
        vault_path=root,
        written_paths=tuple(written_paths),
    )


def _didactic_note_markdown(*, study_package: StudyPackage) -> str:
    metadata = study_package.metadata
    return (
        _frontmatter(
            {
                "tipo": "nota-aula",
                "disciplina": metadata.discipline,
                "data": metadata.class_date,
                "professor": metadata.professor,
                "tema": metadata.class_title,
                "sessao": metadata.session_number,
                "status": "processado",
            }
        )
        + f"# {_title(metadata.class_title, metadata.discipline)}\n\n"
        + study_package.didactic_text.strip()
        + "\n"
    )


def _raw_note_markdown(*, study_package: StudyPackage) -> str:
    metadata = study_package.metadata
    return (
        _frontmatter(
            {
                "tipo": "bruto",
                "disciplina": metadata.discipline,
                "aula-origem": metadata.class_title,
                "data": metadata.class_date,
                "sessao": metadata.session_number,
                "status": "auditavel",
            }
        )
        + f"# Bruto - {_title(metadata.class_title, metadata.discipline)}\n\n"
        + study_package.raw_transcription.text.strip()
        + "\n"
    )


def _summary_note_markdown(*, study_package: StudyPackage) -> str:
    metadata = study_package.metadata
    lines = [
        _frontmatter(
            {
                "tipo": "resumo",
                "disciplina": metadata.discipline,
                "aula-origem": metadata.class_title,
                "data": metadata.class_date,
                "sessao": metadata.session_number,
                "status": "processado",
            }
        ),
        f"# Resumo - {_title(metadata.class_title, metadata.discipline)}",
        "",
    ]
    for theme in study_package.themes:
        lines.extend([f"## {theme.title}", "", theme.summary or "", ""])
    return "\n".join(lines).rstrip() + "\n"


def _concept_markdown(
    *,
    title: str,
    source: str,
    summary: str | None,
    confidence: str,
    study_package: StudyPackage,
) -> str:
    metadata = study_package.metadata
    return (
        _frontmatter(
            {
                "tipo": "conceito",
                "disciplina": metadata.discipline,
                "aula-origem": metadata.class_title,
                "data": metadata.class_date,
                "fonte": source,
                "confianca": confidence,
                "status": "candidato",
            }
        )
        + f"# {title}\n\n"
        + (summary.strip() if summary else "")
        + "\n"
    )


def _write_operational_anchors(
    study_package: StudyPackage,
    operational_dir: Path,
) -> list[Path]:
    anchors = study_package.operational_anchors
    groups = (
        ("links-de-aula.md", "Links de aula", anchors.links),
        ("prazos-e-eventos.md", "Prazos e eventos", anchors.deadlines + anchors.events),
        ("contatos.md", "Contatos", anchors.contacts),
        ("canais-e-comunidades.md", "Canais e comunidades", anchors.channels),
        ("documentos-institucionais.md", "Documentos institucionais", anchors.documents),
        ("_captura-operacional.md", "Entregas e tarefas", anchors.assignments),
    )
    written: list[Path] = []
    context = _operational_context(study_package)
    for filename, heading, values in groups:
        if not values:
            continue
        path = operational_dir / filename
        existing = path.read_text(encoding="utf-8") if path.exists() else f"# {heading}\n"
        block = ["", f"## {context}", ""]
        block.extend(f"- {value}" for value in values)
        block.append("")
        written.append(_write_text_atomic(path, existing.rstrip() + "\n" + "\n".join(block)))
    return written


def _operational_context(study_package: StudyPackage) -> str:
    metadata = study_package.metadata
    parts = [
        metadata.discipline,
        metadata.class_date,
        metadata.session_label or (
            f"S{metadata.session_number}" if metadata.session_number else None
        ),
    ]
    return " - ".join(part for part in parts if part) or "Aula sem metadados"


def _frontmatter(values: dict[str, str | None]) -> str:
    lines = ["---"]
    for key, value in values.items():
        if value:
            lines.append(f"{key}: {value}")
    lines.extend(["---", ""])
    return "\n".join(lines) + "\n"


def _title(class_title: str | None, discipline: str | None) -> str:
    return class_title or discipline or "Aula"


def _artifact_stem(
    *,
    class_number: str,
    class_date: str,
    session_number: str | None,
) -> str:
    stem = f"Aula_{class_number}_{class_date}"
    if session_number:
        stem += f"_s{session_number}"
    return stem


def _class_number(value: str | None) -> str:
    if not value:
        return "00"
    digits = re.sub(r"\D+", "", value)
    if not digits:
        return "00"
    return digits.zfill(2)


def _session_number(study_package: StudyPackage) -> str | None:
    if study_package.metadata.session_number:
        digits = re.sub(r"\D+", "", study_package.metadata.session_number)
        return digits or None
    if not study_package.metadata.session_label:
        return None

    match = re.search(r"S(?:essao)?\s*[-_]?(\d+)$", study_package.metadata.session_label, re.I)
    if match:
        return match.group(1)
    match = re.search(r"S(\d+)", study_package.metadata.session_label, re.I)
    if match:
        return match.group(1)
    return None


def _session_suffix(session_number: str | None) -> str:
    return f"_s{session_number}" if session_number else ""


def _required_slug(value: str | None, field_name: str) -> str:
    if value is None:
        raise StudentVaultExportError(f"{field_name} is required.")
    return _slug(value)


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    if not slug:
        raise StudentVaultExportError("Cannot build a valid slug.")
    return slug[:100]


def _write_text_atomic(path: Path, content: str) -> Path:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)
    return path
