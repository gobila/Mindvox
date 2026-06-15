import unittest

from scripts.audit_e02_raw_transcription import (
    RawAuditIssue,
    build_qwen_input_text,
    collect_raw_candidates,
)


class AuditE02RawTranscriptionTests(unittest.TestCase):
    def test_collect_raw_candidates_detects_known_suspicious_acronym(self):
        candidates = collect_raw_candidates(
            raw_text="A API da GROC foi citada durante a aula.",
            explicit_terms=[],
            include_rare_acronyms=True,
            rare_acronym_max_raw_matches=6,
            max_auto_suspicions=12,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].suspect_text, "GROC")

    def test_collect_raw_candidates_ignores_allowlisted_acronyms_and_numbers(self):
        candidates = collect_raw_candidates(
            raw_text="A API REST recebeu 100 requisicoes em 30 segundos.",
            explicit_terms=[],
            include_rare_acronyms=True,
            rare_acronym_max_raw_matches=6,
            max_auto_suspicions=12,
        )

        self.assertEqual(candidates, [])

    def test_build_qwen_input_applies_ready_canonical_replacement(self):
        issues = [
            RawAuditIssue(
                issue_id="raw-audit-001",
                type="rare_raw_acronym_audio_check",
                suspect_text="GROC",
                status="canonical_replacement_ready",
                reason="test",
                source="test",
                raw_segment_matches=[],
                clip_plans=[],
                recommended_action="apply_canonical_replacement_to_qwen_input",
                canonical_candidate="Groq",
                replacement="Groq",
            )
        ]

        text, corrections = build_qwen_input_text(
            "A aula usou a API da GROC e comparou com outras APIs.",
            issues,
        )

        self.assertIn("API da Groq", text)
        self.assertNotIn("GROC", text)
        self.assertEqual(corrections[0]["count"], "1")

    def test_build_qwen_input_preserves_not_confirmed_suspect(self):
        issues = [
            RawAuditIssue(
                issue_id="raw-audit-001",
                type="rare_raw_acronym_audio_check",
                suspect_text="ICTI",
                status="not_confirmed_by_clip_retranscription",
                reason="test",
                source="test",
                raw_segment_matches=[],
                clip_plans=[],
                recommended_action="mark_or_review_before_qwen",
                canonical_candidate=None,
                replacement="TI",
            )
        ]

        text, corrections = build_qwen_input_text("Sou analista de ICTI.", issues)

        self.assertEqual(text, "Sou analista de ICTI.")
        self.assertEqual(corrections, [])

    def test_build_qwen_input_applies_replacement_ready_from_nonconfirmation(self):
        issues = [
            RawAuditIssue(
                issue_id="raw-audit-001",
                type="rare_raw_acronym_audio_check",
                suspect_text="ICTI",
                status="canonical_replacement_ready_from_nonconfirmation",
                reason="test",
                source="test",
                raw_segment_matches=[],
                clip_plans=[],
                recommended_action="apply_canonical_replacement_to_qwen_input",
                canonical_candidate="TI",
                replacement="TI",
            )
        ]

        text, corrections = build_qwen_input_text("Sou analista de ICTI.", issues)

        self.assertEqual(text, "Sou analista de TI.")
        self.assertEqual(corrections[0]["status"], "canonical_replacement_ready_from_nonconfirmation")


if __name__ == "__main__":
    unittest.main()
