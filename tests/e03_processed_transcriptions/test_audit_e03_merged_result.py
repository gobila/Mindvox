import tempfile
import unittest
from pathlib import Path

from scripts.audit_e03_merged_result import (
    AuditCandidate,
    audit_conclusion,
    build_issues,
    clip_window,
    clip_windows_for_matches,
    find_segment_matches,
    retranscription_confirms_term,
    segment_records,
)


class AuditE03MergedResultTests(unittest.TestCase):
    def test_explicit_suspicious_term_is_mapped_to_timestamped_segment(self):
        merged = {
            "didactic_text": "A aula mencionou um evento em Goiania chamado NASA.",
            "themes": [],
            "technical_terms": [],
            "technology_mentions": [],
            "processing_notes": [],
        }
        transcription = {
            "text": "O professor citou NASA durante a aula.",
            "duration_seconds": 120.0,
            "segments": [
                {
                    "start_seconds": 20.0,
                    "end_seconds": 24.0,
                    "text": "O professor citou NASA durante a aula.",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            issues = build_issues(
                merged_payload=merged,
                transcription=transcription,
                merge_audit=None,
                suspicious_terms=["NASA"],
                include_unconfirmed_entities=False,
                include_low_confidence=True,
                include_rare_acronyms=False,
                rare_acronym_max_raw_matches=6,
                max_auto_suspicions=12,
                margin_seconds=5.0,
                run_dir=Path(tmp),
                audio_file=None,
                make_clips=False,
                transcribe_clips=False,
            )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["suspect_text"], "NASA")
        self.assertEqual(issues[0]["status"], "needs_audio_verification")
        self.assertEqual(issues[0]["raw_segment_matches"][0]["segment_index"], 0)
        self.assertEqual(issues[0]["clip_plan"]["start_seconds"], 15.0)
        self.assertEqual(issues[0]["clip_plan"]["end_seconds"], 29.0)

    def test_clip_window_clamps_to_duration_bounds(self):
        matches = [
            {"start_seconds": 3.0, "end_seconds": 8.0},
            {"start_seconds": 90.0, "end_seconds": 98.0},
        ]

        window = clip_window(matches, margin_seconds=10.0, duration_seconds=100.0)

        self.assertEqual(window["start_seconds"], 0.0)
        self.assertEqual(window["end_seconds"], 100.0)
        self.assertEqual(window["source_match_start_seconds"], 3.0)
        self.assertEqual(window["source_match_end_seconds"], 98.0)

    def test_missing_coverage_anchor_becomes_audit_issue_with_segment_match(self):
        merged = {
            "didactic_text": "A aula tratou de NPS, mas nao nomeou o aluno.",
            "themes": [],
            "technical_terms": [],
            "technology_mentions": [],
            "processing_notes": [],
        }
        transcription = {
            "text": "Eduardo iniciou a pergunta sobre NPS.",
            "duration_seconds": 60.0,
            "segments": [
                {
                    "start_seconds": 10.0,
                    "end_seconds": 12.0,
                    "text": "Eduardo iniciou a pergunta sobre NPS.",
                }
            ],
        }
        merge_audit = {
            "coverage_report": {
                "items": [
                    {"term": "Eduardo", "normalized": "eduardo", "found": False}
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            issues = build_issues(
                merged_payload=merged,
                transcription=transcription,
                merge_audit=merge_audit,
                suspicious_terms=["NASA"],
                include_unconfirmed_entities=False,
                include_low_confidence=True,
                include_rare_acronyms=False,
                rare_acronym_max_raw_matches=6,
                max_auto_suspicions=12,
                margin_seconds=2.0,
                run_dir=Path(tmp),
                audio_file=None,
                make_clips=False,
                transcribe_clips=False,
            )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "missing_coverage_anchor")
        self.assertEqual(issues[0]["suspect_text"], "Eduardo")
        self.assertEqual(issues[0]["raw_segment_matches"][0]["start_seconds"], 10.0)
        self.assertEqual(issues[0]["clip_plan"]["start_seconds"], 8.0)
        self.assertEqual(issues[0]["clip_plan"]["end_seconds"], 14.0)
        self.assertEqual(len(issues[0]["clip_plans"]), 1)
        self.assertIsNone(issues[0]["clip_plan"]["retranscription"])

    def test_segment_matching_uses_canonical_forms(self):
        transcription = {
            "segments": [
                {
                    "start_seconds": 0.0,
                    "end_seconds": 1.0,
                    "text": "Foram discutidas varias APIs internas.",
                }
            ]
        }

        segments = segment_records(transcription)
        matches = find_segment_matches(segments, "API")

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["segment_index"], 0)

    def test_overlapping_clip_windows_are_merged_per_issue(self):
        matches = [
            {"start_seconds": 100.0, "end_seconds": 102.0},
            {"start_seconds": 103.0, "end_seconds": 105.0},
            {"start_seconds": 150.0, "end_seconds": 152.0},
        ]

        windows = clip_windows_for_matches(
            matches,
            margin_seconds=5.0,
            duration_seconds=200.0,
        )

        self.assertEqual(len(windows), 2)
        self.assertEqual(windows[0]["start_seconds"], 95.0)
        self.assertEqual(windows[0]["end_seconds"], 110.0)
        self.assertEqual(windows[1]["start_seconds"], 145.0)

    def test_retranscription_confirmation_uses_canonical_text(self):
        clips = [
            {
                "retranscription": {
                    "status": "pass",
                    "text": "O professor falou sobre varias APIs internas.",
                }
            }
        ]

        self.assertTrue(retranscription_confirms_term(clips, "API"))
        self.assertFalse(retranscription_confirms_term(clips, "Eduardo"))

    def test_rare_acronym_policy_adds_audio_check_without_manual_term(self):
        merged = {
            "didactic_text": "A aula mencionou o Hackathon da NASA em Goiania.",
            "themes": [],
            "technical_terms": [],
            "technology_mentions": [],
            "processing_notes": [],
        }
        transcription = {
            "text": "Houve comentario sobre Hackathon da NASA em Goiania.",
            "duration_seconds": 30.0,
            "segments": [
                {
                    "start_seconds": 5.0,
                    "end_seconds": 8.0,
                    "text": "Houve comentario sobre Hackathon da NASA em Goiania.",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            issues = build_issues(
                merged_payload=merged,
                transcription=transcription,
                merge_audit=None,
                suspicious_terms=[],
                include_unconfirmed_entities=False,
                include_low_confidence=False,
                include_rare_acronyms=True,
                rare_acronym_max_raw_matches=6,
                max_auto_suspicions=12,
                margin_seconds=2.0,
                run_dir=Path(tmp),
                audio_file=None,
                make_clips=False,
                transcribe_clips=False,
            )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "rare_acronym_audio_check")
        self.assertEqual(issues[0]["suspect_text"], "NASA")

    def test_rare_acronym_policy_ignores_plain_numbers(self):
        merged = {
            "didactic_text": "A aula citou 30 dias e 100% de liberdade para perguntas.",
            "themes": [],
            "technical_terms": [],
            "technology_mentions": [],
            "processing_notes": [],
        }
        transcription = {
            "text": "A aula citou 30 dias e 100% de liberdade para perguntas.",
            "duration_seconds": 30.0,
            "segments": [
                {
                    "start_seconds": 5.0,
                    "end_seconds": 8.0,
                    "text": "A aula citou 30 dias e 100% de liberdade para perguntas.",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            issues = build_issues(
                merged_payload=merged,
                transcription=transcription,
                merge_audit=None,
                suspicious_terms=[],
                include_unconfirmed_entities=False,
                include_low_confidence=False,
                include_rare_acronyms=True,
                rare_acronym_max_raw_matches=6,
                max_auto_suspicions=12,
                margin_seconds=2.0,
                run_dir=Path(tmp),
                audio_file=None,
                make_clips=False,
                transcribe_clips=False,
            )

        self.assertEqual(issues, [])

    def test_rare_acronym_policy_ignores_processing_notes_only_terms(self):
        merged = {
            "didactic_text": "A aula mencionou a OpenAI e o Groq como servicos de IA.",
            "themes": [],
            "technical_terms": [],
            "technology_mentions": [],
            "processing_notes": [
                {"message": "Termos como GMI e PNI foram tratados como ruido de transcricao."}
            ],
        }
        transcription = {
            "text": "Uma coisa eu vou mandar para a OpenAI e outra para o Groq.",
            "duration_seconds": 30.0,
            "segments": [
                {
                    "start_seconds": 5.0,
                    "end_seconds": 8.0,
                    "text": "Uma coisa eu vou mandar para a OpenAI e outra para o Groq.",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            issues = build_issues(
                merged_payload=merged,
                transcription=transcription,
                merge_audit=None,
                suspicious_terms=[],
                include_unconfirmed_entities=False,
                include_low_confidence=False,
                include_rare_acronyms=True,
                rare_acronym_max_raw_matches=6,
                max_auto_suspicions=12,
                margin_seconds=2.0,
                run_dir=Path(tmp),
                audio_file=None,
                make_clips=False,
                transcribe_clips=False,
            )

        self.assertEqual(issues, [])

    def test_known_spelling_candidate_changes_recommended_action(self):
        conclusion = audit_conclusion(
            candidate=AuditCandidate(
                issue_type="rare_acronym_audio_check",
                suspect_text="GROC",
                reason="test",
                source="test",
            ),
            confirmed_by_clip_stt=True,
            raw_matches=[{"segment_index": 0}],
            transcribe_clips=True,
        )

        self.assertEqual(
            conclusion["recommended_action"],
            "review_canonical_spelling",
        )
        self.assertEqual(conclusion["canonical_spelling_candidate"], "Groq")


if __name__ == "__main__":
    unittest.main()
