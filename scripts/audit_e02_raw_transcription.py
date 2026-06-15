#!/usr/bin/env python3
"""Pre-audit an E02 raw transcription before sending it to Qwen/E03.

This is an offline bench tool. It preserves the original E02 transcription,
detects suspicious lexical artifacts in the timestamped raw text, optionally
checks them against audio clips with the same STT engine used by E02, and writes
a Qwen-ready raw text with conservative canonical spelling replacements.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_e03_merged_result import (
    AuditCandidate,
    DEFAULT_ACRONYM_ALLOWLIST,
    canonical_entity_key,
    clip_windows_for_matches,
    cut_audio_clip,
    find_segment_matches,
    safe_filename,
    segment_records,
    transcribe_clip_with_e02_engine,
    write_clip_retranscription_artifacts,
)


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".benchmarks" / "e02_raw_pre_audit"

CANONICAL_REPLACEMENTS = {
    "CIGA": {
        "canonical": "SIGAA",
        "replacement": "SIGAA",
        "reason": "Sistema academico provavelmente referido como SIGAA.",
    },
    "UFNDE": {
        "canonical": "FNDE",
        "replacement": "FNDE",
        "reason": "Orgao federal citado no contexto costuma ser FNDE.",
    },
    "IAC": {
        "canonical": "IaC",
        "replacement": "IaC",
        "reason": "Contexto de infraestrutura como codigo usa grafia IaC.",
    },
    "EPT": {
        "canonical": "ChatGPT",
        "replacement": "ChatGPT",
        "reason": "Contexto de chat/LLM sugere ChatGPT.",
    },
    "GROC": {
        "canonical": "Groq",
        "replacement": "Groq",
        "reason": "Fornecedor de inferencia LLM citado no contexto e Groq.",
    },
    "ICTI": {
        "canonical": "TI",
        "replacement": "TI",
        "reason": "Re-STT pontual indicou 'analista de TI' no trecho auditado.",
    },
}


@dataclass(frozen=True)
class RawAuditIssue:
    issue_id: str
    type: str
    suspect_text: str
    status: str
    reason: str
    source: str
    raw_segment_matches: list[dict[str, Any]]
    clip_plans: list[dict[str, Any]]
    recommended_action: str
    canonical_candidate: str | None = None
    replacement: str | None = None


def collect_raw_candidates(
    *,
    raw_text: str,
    explicit_terms: list[str],
    include_rare_acronyms: bool,
    rare_acronym_max_raw_matches: int,
    max_auto_suspicions: int,
) -> list[AuditCandidate]:
    candidates: list[AuditCandidate] = []

    for term in explicit_terms:
        if term and re.search(rf"\b{re.escape(term)}\b", raw_text, flags=re.IGNORECASE):
            candidates.append(
                AuditCandidate(
                    issue_type="explicit_raw_audio_check",
                    suspect_text=term,
                    reason="Termo explicitamente marcado para pre-auditoria.",
                    source="explicit_terms",
                )
            )

    if include_rare_acronyms:
        seen: set[str] = set()
        for match in re.finditer(r"\b[A-Z][A-Z0-9]{1,9}\b", raw_text):
            acronym = match.group(0)
            if acronym in seen or acronym.upper() in DEFAULT_ACRONYM_ALLOWLIST:
                continue
            seen.add(acronym)
            raw_count = len(
                re.findall(rf"\b{re.escape(acronym)}\b", raw_text, flags=re.IGNORECASE)
            )
            if raw_count <= 0 or raw_count > rare_acronym_max_raw_matches:
                continue
            candidates.append(
                AuditCandidate(
                    issue_type="rare_raw_acronym_audio_check",
                    suspect_text=acronym,
                    reason=(
                        "Sigla rara detectada na transcricao bruta antes do Qwen; "
                        "deve ser confirmada ou normalizada antes do pos-processamento."
                    ),
                    source="raw_rare_acronym_policy",
                )
            )
            if len(candidates) >= max_auto_suspicions:
                break

    return deduplicate_candidates(candidates)


def deduplicate_candidates(candidates: list[AuditCandidate]) -> list[AuditCandidate]:
    seen: set[str] = set()
    output: list[AuditCandidate] = []
    for candidate in candidates:
        key = canonical_entity_key(candidate.suspect_text)
        if not key or key in seen:
            continue
        output.append(candidate)
        seen.add(key)
    return output


def build_raw_issues(
    *,
    transcription: dict[str, Any],
    audio_file: Path | None,
    explicit_terms: list[str],
    include_rare_acronyms: bool,
    rare_acronym_max_raw_matches: int,
    max_auto_suspicions: int,
    clip_margin_seconds: float,
    make_clips: bool,
    transcribe_clips: bool,
    apply_known_canonical: bool,
    run_dir: Path,
) -> list[RawAuditIssue]:
    raw_text = str(transcription.get("text") or "")
    segments = segment_records(transcription)
    duration_value = transcription.get("duration_seconds")
    duration = float(duration_value) if duration_value is not None else None
    candidates = collect_raw_candidates(
        raw_text=raw_text,
        explicit_terms=explicit_terms,
        include_rare_acronyms=include_rare_acronyms,
        rare_acronym_max_raw_matches=rare_acronym_max_raw_matches,
        max_auto_suspicions=max_auto_suspicions,
    )

    issues: list[RawAuditIssue] = []
    for index, candidate in enumerate(candidates, start=1):
        issue_id = f"raw-audit-{index:03d}"
        raw_matches = find_segment_matches(segments, candidate.suspect_text)
        windows = clip_windows_for_matches(
            raw_matches,
            margin_seconds=clip_margin_seconds,
            duration_seconds=duration,
        )
        clip_plans: list[dict[str, Any]] = []
        for clip_index, window in enumerate(windows, start=1):
            clip_path = None
            clip_created = False
            retranscription = None
            retranscription_artifacts = None
            if audio_file is not None and (make_clips or transcribe_clips):
                output_file = (
                    run_dir
                    / "audio_clips"
                    / f"{issue_id}_{clip_index:02d}_{safe_filename(candidate.suspect_text)}.wav"
                )
                clip_created = cut_audio_clip(
                    audio_file=audio_file,
                    output_file=output_file,
                    window=window,
                )
                if clip_created:
                    clip_path = str(output_file)
                    if transcribe_clips:
                        retranscription = transcribe_clip_with_e02_engine(
                            clip_path=output_file,
                            filename=output_file.name,
                            language=str(transcription.get("language") or "pt-BR"),
                            metadata=transcription.get("metadata") or {},
                        )
                        retranscription_artifacts = write_clip_retranscription_artifacts(
                            run_dir=run_dir,
                            clip_path=output_file,
                            retranscription=retranscription,
                        )
            clip_plans.append(
                {
                    **window,
                    "audio_file": str(audio_file) if audio_file else None,
                    "clip_path": clip_path,
                    "clip_created": clip_created,
                    "retranscription": retranscription,
                    "retranscription_artifacts": retranscription_artifacts,
                }
            )

        confirmed = retranscription_confirms_candidate(clip_plans, candidate.suspect_text)
        replacement_info = CANONICAL_REPLACEMENTS.get(candidate.suspect_text.upper())
        if replacement_info and confirmed and apply_known_canonical:
            status = "canonical_replacement_ready"
            recommended_action = "apply_canonical_replacement_to_qwen_input"
            canonical_candidate = str(replacement_info["canonical"])
            replacement = str(replacement_info["replacement"])
        elif replacement_info and confirmed:
            status = "canonical_replacement_candidate"
            recommended_action = "review_canonical_replacement"
            canonical_candidate = str(replacement_info["canonical"])
            replacement = None
        elif replacement_info and raw_matches and transcribe_clips and apply_known_canonical:
            status = "canonical_replacement_ready_from_nonconfirmation"
            recommended_action = "apply_canonical_replacement_to_qwen_input"
            canonical_candidate = str(replacement_info["canonical"])
            replacement = str(replacement_info["replacement"])
        elif confirmed:
            status = "verified_in_audio"
            recommended_action = "preserve_in_qwen_input"
            canonical_candidate = None
            replacement = None
        elif raw_matches and transcribe_clips:
            status = "not_confirmed_by_clip_retranscription"
            recommended_action = "mark_or_review_before_qwen"
            canonical_candidate = replacement_info["canonical"] if replacement_info else None
            replacement = None
        elif raw_matches:
            status = "needs_audio_verification"
            recommended_action = "run_clip_retranscription"
            canonical_candidate = replacement_info["canonical"] if replacement_info else None
            replacement = None
        else:
            status = "not_found_in_segments"
            recommended_action = "inspect_transcription_source"
            canonical_candidate = replacement_info["canonical"] if replacement_info else None
            replacement = None

        issues.append(
            RawAuditIssue(
                issue_id=issue_id,
                type=candidate.issue_type,
                suspect_text=candidate.suspect_text,
                status=status,
                reason=candidate.reason,
                source=candidate.source,
                raw_segment_matches=raw_matches,
                clip_plans=clip_plans,
                recommended_action=recommended_action,
                canonical_candidate=str(canonical_candidate) if canonical_candidate else None,
                replacement=replacement,
            )
        )

    return issues


def retranscription_confirms_candidate(clip_plans: list[dict[str, Any]], suspect: str) -> bool:
    suspect_key = canonical_entity_key(suspect)
    if not suspect_key:
        return False
    for clip in clip_plans:
        retranscription = clip.get("retranscription") or {}
        if retranscription.get("status") != "pass":
            continue
        if suspect_key in canonical_entity_key(str(retranscription.get("text") or "")):
            return True
    return False


def build_qwen_input_text(raw_text: str, issues: list[RawAuditIssue]) -> tuple[str, list[dict[str, str]]]:
    text = raw_text
    corrections: list[dict[str, str]] = []
    replacement_ready_statuses = {
        "canonical_replacement_ready",
        "canonical_replacement_ready_from_nonconfirmation",
    }
    for issue in issues:
        if issue.status not in replacement_ready_statuses or not issue.replacement:
            continue
        pattern = re.compile(rf"\b{re.escape(issue.suspect_text)}\b")
        text, count = pattern.subn(issue.replacement, text)
        if count:
            corrections.append(
                {
                    "suspect_text": issue.suspect_text,
                    "replacement": issue.replacement,
                    "canonical_candidate": issue.canonical_candidate or issue.replacement,
                    "count": str(count),
                    "issue_id": issue.issue_id,
                    "status": issue.status,
                }
            )
    return text, corrections


def status_counts(issues: list[RawAuditIssue]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue.status] = counts.get(issue.status, 0) + 1
    return counts


def write_outputs(
    *,
    run_dir: Path,
    transcription_json_file: Path,
    audio_file: Path | None,
    transcription: dict[str, Any],
    issues: list[RawAuditIssue],
    qwen_text: str,
    corrections: list[dict[str, str]],
    settings: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "transcription_json_file": str(transcription_json_file),
            "audio_file": str(audio_file) if audio_file else None,
            "strategy": "offline_e02_raw_pre_audit",
            "settings": settings,
        },
        "summary": {
            "issues": len(issues),
            "status_counts": status_counts(issues),
            "audio_clips_created": sum(
                1
                for issue in issues
                for clip in issue.clip_plans
                if clip.get("clip_created")
            ),
            "clip_retranscriptions_passed": sum(
                1
                for issue in issues
                for clip in issue.clip_plans
                if (clip.get("retranscription") or {}).get("status") == "pass"
            ),
            "clip_retranscriptions_failed": sum(
                1
                for issue in issues
                for clip in issue.clip_plans
                if (clip.get("retranscription") or {}).get("status") == "error"
            ),
            "canonical_replacements": len(corrections),
        },
        "canonical_replacements": corrections,
        "issues": [asdict(issue) for issue in issues],
    }
    (run_dir / "raw_transcription_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "raw_text_original.txt").write_text(
        str(transcription.get("text") or "").strip() + "\n",
        encoding="utf-8",
    )
    (run_dir / "raw_text_for_qwen.txt").write_text(qwen_text.strip() + "\n", encoding="utf-8")
    (run_dir / "pre_audit_resolution.md").write_text(
        resolution_markdown(payload),
        encoding="utf-8",
    )
    (run_dir / "README.md").write_text(readme_markdown(payload), encoding="utf-8")


def readme_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metadata = payload["audit_metadata"]
    return "\n".join(
        [
            "# E02 Raw Pre-Audit Benchmark",
            "",
            "Artefato experimental offline. A transcricao original e preservada; `raw_text_for_qwen.txt` contem apenas substituicoes canonicas controladas.",
            "",
            f"- `transcription_json_file`: `{metadata['transcription_json_file']}`",
            f"- `audio_file`: `{metadata['audio_file']}`",
            f"- `issues`: {summary['issues']}",
            f"- `status_counts`: `{json.dumps(summary['status_counts'], ensure_ascii=False)}`",
            f"- `audio_clips_created`: {summary['audio_clips_created']}",
            f"- `clip_retranscriptions_passed`: {summary['clip_retranscriptions_passed']}",
            f"- `clip_retranscriptions_failed`: {summary['clip_retranscriptions_failed']}",
            f"- `canonical_replacements`: {summary['canonical_replacements']}",
            "",
            "## Arquivos",
            "",
            "- `raw_transcription_audit.json`: dossie tecnico.",
            "- `raw_text_original.txt`: bruto original preservado.",
            "- `raw_text_for_qwen.txt`: bruto preparado para chunking/E03.",
            "- `pre_audit_resolution.md`: sintese humana.",
            "- `audio_clips/`: clipes WAV de evidencias.",
            "- `clip_transcriptions/`: re-transcricoes pontuais.",
            "",
        ]
    )


def resolution_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Resolucao da Pre-Auditoria E02",
        "",
        "Esta etapa roda antes do Qwen/E03 e prepara uma entrada mais limpa para o pos-processamento.",
        "",
        "## Sumario",
        "",
        f"- `issues`: {payload['summary']['issues']}",
        f"- `status_counts`: `{json.dumps(payload['summary']['status_counts'], ensure_ascii=False)}`",
        f"- `canonical_replacements`: {payload['summary']['canonical_replacements']}",
        "",
        "## Correcoes Canonicas",
        "",
    ]
    if payload["canonical_replacements"]:
        for correction in payload["canonical_replacements"]:
            lines.append(
                f"- `{correction['suspect_text']}` -> `{correction['replacement']}` "
                f"({correction['count']} ocorrencias; {correction['issue_id']})"
            )
    else:
        lines.append("- Nenhuma correcao canonica aplicada.")

    lines.extend(["", "## Suspeitas", ""])
    for issue in payload.get("issues") or []:
        lines.extend(
            [
                f"### {issue['issue_id']} - {issue['suspect_text']}",
                "",
                f"- `type`: `{issue['type']}`",
                f"- `status`: `{issue['status']}`",
                f"- `recommended_action`: `{issue['recommended_action']}`",
                f"- `canonical_candidate`: `{issue.get('canonical_candidate')}`",
                f"- `replacement`: `{issue.get('replacement')}`",
                f"- `raw_segment_matches`: {len(issue.get('raw_segment_matches') or [])}",
                f"- `clip_plans`: {len(issue.get('clip_plans') or [])}",
                "",
            ]
        )
        for clip in (issue.get("clip_plans") or [])[:2]:
            retranscription = clip.get("retranscription") or {}
            text = str(retranscription.get("text") or "").strip()
            if len(text) > 500:
                text = text[:500].rstrip() + "..."
            lines.extend(
                [
                    f"- Janela: `{clip.get('start_seconds')}` -> `{clip.get('end_seconds')}`",
                    f"  - Clip: `{clip.get('clip_path')}`",
                    f"  - Texto STT: {text}",
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-audit timestamped E02 raw transcription before Qwen/E03.",
    )
    parser.add_argument("--transcription-json-file", required=True, type=Path)
    parser.add_argument("--audio-file", type=Path)
    parser.add_argument("--case-name", default="e02-raw-pre-audit")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--issue-term", action="append", default=[])
    parser.add_argument("--issue-terms-file", type=Path)
    parser.add_argument("--clip-margin-seconds", type=float, default=10.0)
    parser.add_argument("--include-rare-acronyms", action="store_true", default=True)
    parser.add_argument("--no-rare-acronyms", dest="include_rare_acronyms", action="store_false")
    parser.add_argument("--rare-acronym-max-raw-matches", type=int, default=6)
    parser.add_argument("--max-auto-suspicions", type=int, default=12)
    parser.add_argument("--make-clips", action="store_true")
    parser.add_argument("--transcribe-clips", action="store_true")
    parser.add_argument("--apply-known-canonical", action="store_true", default=True)
    parser.add_argument("--no-apply-known-canonical", dest="apply_known_canonical", action="store_false")
    return parser.parse_args(argv)


def issue_terms_from_args(args: argparse.Namespace) -> list[str]:
    terms = list(args.issue_term or [])
    if args.issue_terms_file is not None:
        terms.extend(
            line.strip()
            for line in args.issue_terms_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    output: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = canonical_entity_key(term)
        if not key or key in seen:
            continue
        output.append(term)
        seen.add(key)
    return output


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    transcription_json_file = args.transcription_json_file.resolve()
    audio_file = args.audio_file.resolve() if args.audio_file else None

    if not transcription_json_file.exists():
        raise SystemExit(f"Transcription JSON file not found: {transcription_json_file}")
    if audio_file is not None and not audio_file.exists():
        raise SystemExit(f"Audio file not found: {audio_file}")

    transcription = json.loads(transcription_json_file.read_text(encoding="utf-8"))
    explicit_terms = issue_terms_from_args(args)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.output_dir.resolve() / f"{timestamp}_{safe_filename(args.case_name)}"

    issues = build_raw_issues(
        transcription=transcription,
        audio_file=audio_file,
        explicit_terms=explicit_terms,
        include_rare_acronyms=args.include_rare_acronyms,
        rare_acronym_max_raw_matches=args.rare_acronym_max_raw_matches,
        max_auto_suspicions=args.max_auto_suspicions,
        clip_margin_seconds=args.clip_margin_seconds,
        make_clips=args.make_clips,
        transcribe_clips=args.transcribe_clips,
        apply_known_canonical=args.apply_known_canonical,
        run_dir=run_dir,
    )
    qwen_text, corrections = build_qwen_input_text(
        str(transcription.get("text") or ""),
        issues,
    )
    write_outputs(
        run_dir=run_dir,
        transcription_json_file=transcription_json_file,
        audio_file=audio_file,
        transcription=transcription,
        issues=issues,
        qwen_text=qwen_text,
        corrections=corrections,
        settings={
            "explicit_terms": explicit_terms,
            "include_rare_acronyms": args.include_rare_acronyms,
            "rare_acronym_max_raw_matches": args.rare_acronym_max_raw_matches,
            "max_auto_suspicions": args.max_auto_suspicions,
            "clip_margin_seconds": args.clip_margin_seconds,
            "make_clips": args.make_clips,
            "transcribe_clips": args.transcribe_clips,
            "apply_known_canonical": args.apply_known_canonical,
        },
    )

    print(f"Pre-audit run: {run_dir}")
    print(f"Issues: {len(issues)}")
    print(f"Status counts: {status_counts(issues)}")
    print(f"Canonical replacements: {len(corrections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
