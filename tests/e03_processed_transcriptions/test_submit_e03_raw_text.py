import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.submit_e03_raw_text import submit_prepared_raw_text  # noqa: E402


class SubmitE03RawTextTest(unittest.TestCase):
    def test_submit_uses_metadata_json_as_form_source(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_text = root / "2026-05-09-api-rogerio-aula-1-sessao-4.txt"
            raw_text.write_text("0:02\n\nTexto bruto.", encoding="utf-8")
            metadata = root / "2026-05-09-api-rogerio-aula-1-sessao-4.metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "raw_text_file": str(raw_text),
                        "capture_section": 4,
                        "e03_form": {
                            "input_type": "raw_text",
                            "language": "pt-BR",
                            "processing_profile": "study_notes",
                            "course": "UFG Pos 2",
                            "discipline": "API",
                            "class_date": "2026-05-09",
                            "class_title": "API - Aula 1 - Sessão 4 - Professor Rogério",
                            "session_label": "A1S4",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch("scripts.submit_e03_raw_text.httpx.post") as post:
                post.return_value.raise_for_status.return_value = None
                post.return_value.json.return_value = {
                    "processed_transcription_id": "ptr_test",
                    "artifact_locations": {},
                }

                response = submit_prepared_raw_text(
                    metadata_path=metadata,
                    endpoint="http://testserver/processed-transcriptions/v1.0.0",
                    token="test-token",
                    timeout_seconds=10,
                )

        self.assertEqual(response["processed_transcription_id"], "ptr_test")
        post.assert_called_once()
        _, kwargs = post.call_args
        self.assertEqual(
            kwargs["headers"],
            {"Authorization": "Bearer test-token"},
        )
        self.assertEqual(kwargs["data"]["input_type"], "raw_text_file")
        self.assertEqual(kwargs["data"]["class_title"], "API - Aula 1 - Sessão 4 - Professor Rogério")
        self.assertEqual(kwargs["data"]["session_label"], "A1S4")
        self.assertEqual(kwargs["files"]["raw_text_file"][0], raw_text.name)
        self.assertEqual(kwargs["files"]["raw_text_file"][2], "text/plain")


if __name__ == "__main__":
    unittest.main()
