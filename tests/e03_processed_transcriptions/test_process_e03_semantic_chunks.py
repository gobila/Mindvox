import unittest

from scripts.process_e03_semantic_chunks import pre_audit_header, pre_audit_run_metadata


class ProcessE03SemanticChunksTests(unittest.TestCase):
    def test_pre_audit_header_declares_no_remaining_suspicions(self):
        context = {
            "file": "raw_transcription_audit.json",
            "summary": {
                "issues": 2,
                "status_counts": {"canonical_replacement_ready": 2},
                "canonical_replacements": 2,
            },
            "issues": [
                {"suspect_text": "CIGA", "status": "canonical_replacement_ready"},
                {"suspect_text": "GROC", "status": "canonical_replacement_ready"},
            ],
            "canonical_replacements": [
                {
                    "suspect_text": "CIGA",
                    "replacement": "SIGAA",
                    "status": "canonical_replacement_ready",
                }
            ],
        }

        header = pre_audit_header(context)

        self.assertIn("Mindvox pre-audit context", header)
        self.assertIn("No remaining suspicious transcription terms", header)
        self.assertIn("CIGA -> SIGAA", header)
        self.assertIn("not classroom content", header)

    def test_pre_audit_metadata_counts_unresolved_suspicions(self):
        context = {
            "file": "raw_transcription_audit.json",
            "summary": {
                "issues": 2,
                "status_counts": {"not_confirmed_by_clip_retranscription": 1},
                "canonical_replacements": 0,
            },
            "issues": [
                {
                    "suspect_text": "PNI",
                    "status": "not_confirmed_by_clip_retranscription",
                },
                {"suspect_text": "API", "status": "verified_in_audio"},
            ],
            "canonical_replacements": [],
        }

        metadata = pre_audit_run_metadata(context)

        self.assertTrue(metadata["applied"])
        self.assertEqual(metadata["unresolved_suspicions"], 1)

    def test_pre_audit_header_keeps_unresolved_terms_out_of_deliveries(self):
        context = {
            "file": "raw_transcription_audit.json",
            "summary": {
                "issues": 1,
                "status_counts": {"not_confirmed_by_clip_retranscription": 1},
                "canonical_replacements": 0,
            },
            "issues": [
                {
                    "suspect_text": "PNI",
                    "status": "not_confirmed_by_clip_retranscription",
                }
            ],
            "canonical_replacements": [],
        }

        header = pre_audit_header(context)

        self.assertIn("not verified class content", header)
        self.assertIn("Do not promote them to didactic_text", header)
        self.assertIn("Mention unresolved terms only in processing_notes", header)


if __name__ == "__main__":
    unittest.main()
