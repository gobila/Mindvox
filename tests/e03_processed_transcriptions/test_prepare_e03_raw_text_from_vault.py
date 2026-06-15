import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.prepare_e03_raw_text_from_vault import (  # noqa: E402
    extract_session_section,
    extract_transcription_block,
    main,
    prepare_transcript,
)


class PrepareE03RawTextFromVaultTest(unittest.TestCase):
    def test_extracts_transcription_from_requested_capture_section(self):
        markdown = """---
disciplina: "[[UFG_Pos_2/01_Aulas/API/_INDEX|API]]"
professor: Rogério
aula: "1"
data: 2026-05-09
sessao-ativa: 3
---

## 🔵 Sessão 1 · Manhã

Texto da primeira.

## 🔴 Sessão 4 · Tarde

![](image)

0:22/1:34:49

Transcrição

0:02

Boa tarde novamente.

0:08

Vamos continuar a aula de API.
"""

        section = extract_session_section(markdown, section=4)
        transcript = extract_transcription_block(section)

        self.assertIn("0:02", transcript)
        self.assertIn("Boa tarde novamente.", transcript)
        self.assertNotIn("Transcrição", transcript)
        self.assertNotIn("![](image)", transcript)

    def test_prepare_writes_txt_with_metadata_based_name(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            note = root / "_captura-rapida.md"
            note.write_text(
                """---
disciplina: "[[UFG_Pos_2/01_Aulas/API/_INDEX|API]]"
professor: Rogério
aula: "1"
data: 2026-05-09
sessao-ativa: 3
---

## 🔴 Sessão 4

Transcrição

0:02

Conteúdo bruto da aula.
""",
                encoding="utf-8",
            )

            prepared = prepare_transcript(
                note_path=note,
                section=4,
                output_dir=root / "out",
            )

            self.assertTrue(prepared.output_path.exists())
            self.assertTrue(prepared.metadata_path.exists())
            self.assertIn("api", prepared.output_path.name)
            self.assertIn("rogerio", prepared.output_path.name)
            self.assertIn("sessao-3", prepared.output_path.name)
            self.assertNotIn("secao-4", prepared.output_path.name)
            self.assertEqual(prepared.e03_form_metadata["discipline"], "API")
            self.assertEqual(prepared.e03_form_metadata["class_date"], "2026-05-09")
            self.assertEqual(prepared.e03_form_metadata["session_label"], "A1S3")
            self.assertIn("Rogério", prepared.e03_form_metadata["class_title"])
            metadata_payload = json.loads(
                prepared.metadata_path.read_text(encoding="utf-8")
            )
            self.assertEqual(metadata_payload["e03_form"]["input_type"], "raw_text")
            self.assertEqual(metadata_payload["capture_section"], 4)
            self.assertEqual(
                metadata_payload["raw_text_file"],
                str(prepared.output_path.resolve()),
            )
            self.assertEqual(
                prepared.output_path.read_text(encoding="utf-8").strip(),
                "0:02\n\nConteúdo bruto da aula.",
            )

    def test_main_submit_imports_submit_client_from_project_root(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            note = root / "_captura-rapida.md"
            note.write_text(
                """---
disciplina: API
professor: Rogério
aula: "1"
data: 2026-05-09
sessao-ativa: 1
---

## Sessão 1

Transcrição

0:02

Conteúdo bruto da aula.
""",
                encoding="utf-8",
            )

            with patch("scripts.submit_e03_raw_text.httpx.post") as post:
                post.return_value.raise_for_status.return_value = None
                post.return_value.json.return_value = {
                    "processed_transcription_id": "ptr_test",
                    "artifact_locations": {},
                }

                with redirect_stdout(StringIO()):
                    exit_code = main(
                        [
                            "--vault",
                            str(root),
                            "--note",
                            "_captura-rapida.md",
                            "--section",
                            "1",
                            "--output-dir",
                            str(root / "out"),
                            "--submit",
                            "--endpoint",
                            "http://testserver/processed-transcriptions/v1.0.0",
                            "--token",
                            "test-token",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
