import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from schemas.processed_transcriptions import Source  # noqa: E402
from schemas.transcriptions import TranscriptionMetadata  # noqa: E402
from services.postprocessing_pipeline import (  # noqa: E402
    chunk_text_tfidf,
    merge_payload_dicts,
    pre_audit_context_header,
    pre_audit_raw_text,
)
from services.postprocessing_service import process_transcription  # noqa: E402
from settings import Settings  # noqa: E402


class PostprocessingPipelineTests(unittest.TestCase):
    def test_pre_audit_replaces_known_suspects_and_tracks_unresolved_terms(self):
        result = pre_audit_raw_text(
            "O aluno falou de CIGA, GROC e PNI durante a aula.",
            enabled=True,
        )

        self.assertIn("SIGAA", result.text_for_llm)
        self.assertIn("Groq", result.text_for_llm)
        self.assertNotIn("CIGA", result.text_for_llm)
        self.assertIn("PNI", result.unresolved_terms)

        header = pre_audit_context_header(result)
        self.assertIn("CIGA -> SIGAA", header)
        self.assertIn("not verified class content", header)

    def test_pre_audit_removes_repetitive_transcription_noise_only_from_llm_text(self):
        raw_text = (
            "A aula discutiu entregas semanais. "
            + ("ste " * 12)
            + "Depois falou sobre squads. "
            + ("os " * 12)
            + "Por fim, comentou o cronograma."
        )

        result = pre_audit_raw_text(raw_text, enabled=True)

        self.assertEqual(result.original_text, raw_text)
        self.assertNotIn("ste ste ste", result.text_for_llm)
        self.assertNotIn("os os os", result.text_for_llm)
        self.assertIn("A aula discutiu entregas semanais.", result.text_for_llm)
        self.assertIn("Por fim, comentou o cronograma.", result.text_for_llm)
        self.assertTrue(
            any(issue.status == "repetitive_noise_removed" for issue in result.issues)
        )

    def test_chunk_text_tfidf_creates_ordered_chunks(self):
        raw_text = " ".join(
            f"Aula parte {index}. APIs, FastAPI, Docker e OpenAI foram discutidos."
            for index in range(140)
        )

        chunks = chunk_text_tfidf(raw_text, max_chunk_tokens=250)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_id, "tfidf-01")
        self.assertLess(chunks[0].first_segment_index, chunks[-1].first_segment_index)

    def test_merge_filters_unresolved_terms_from_structured_deliveries(self):
        pre_audit = pre_audit_raw_text("PNI apareceu no bruto.", enabled=True)
        payload = merge_payload_dicts(
            chunk_payloads=[
                {
                    "didactic_text": "A aula citou OpenAI como provider.",
                    "themes": [
                        {
                            "order": 1,
                            "title": "PNI",
                            "summary": "Termo suspeito.",
                            "key_points": ["PNI"],
                            "semantic_role": "tema",
                            "evidence": "PNI",
                        }
                    ],
                    "technical_terms": [
                        {
                            "term": "PNI",
                            "normalized_from": [],
                            "explanation": "Suspeito",
                            "confidence": "low",
                            "evidence": "PNI",
                        }
                    ],
                    "technology_mentions": [
                        {
                            "name": "PNI",
                            "category": "provider",
                            "context": "Suspeito",
                            "importance": "low",
                            "normalized_from": [],
                            "confidence": "low",
                            "evidence": "PNI",
                        }
                    ],
                    "processing_notes": [],
                }
            ],
            chunk_ids=["tfidf-01"],
            original_raw_text="PNI apareceu no bruto.",
            pre_audit=pre_audit,
            final_audit_enabled=True,
        )

        self.assertEqual(payload["themes"], [])
        self.assertEqual(payload["technical_terms"], [])
        self.assertEqual(payload["technology_mentions"], [])

    def test_process_transcription_uses_chunk_pipeline_without_changing_public_raw_text(self):
        raw_text = " ".join(
            "A aula mencionou CIGA, GROC, APIs, FastAPI e Docker. "
            "O professor explicou que APIs organizam integrações."
            for _ in range(80)
        )
        response = process_transcription(
            raw_text=raw_text,
            input_type="raw_text",
            language="pt-BR",
            metadata=TranscriptionMetadata(discipline="API"),
            source=Source(
                input_origin="raw_text",
                raw_text_origin="provided_by_client",
                transcription=None,
            ),
            settings=self._settings(),
        )

        self.assertEqual(response.raw_text, raw_text)
        self.assertGreaterEqual(len(response.processing_notes), 2)
        self.assertTrue(
            any(note.type == "chunk_merge" for note in response.processing_notes)
        )
        self.assertTrue(
            any(note.type == "pre_audit" for note in response.processing_notes)
        )

    def _settings(self) -> Settings:
        return Settings(
            api_token="test-token",
            runtime_profile="contract",
            max_upload_mb=500,
            public_deployment=False,
            docs_enabled=True,
            trusted_hosts=(),
            postprocessing_mode="contract",
            postprocessing_max_input_chars=150000,
            postprocessing_chunking_mode="tfidf",
            postprocessing_chunking_min_chars=500,
            postprocessing_chunk_target_tokens=350,
            postprocessing_pre_audit_enabled=True,
            postprocessing_final_audit_enabled=True,
            llm_provider="test",
            llm_base_url="https://example.com/v1",
            llm_allowed_provider_hosts=(),
            llm_max_output_tokens=20000,
            llm_model="test-model",
            llm_api_key="test-provider-key",
            llm_timeout_seconds=1200,
            local_llm_autostart=False,
            llama_server_path=None,
            local_llm_model_path=None,
            llama_server_ctx_size=65536,
            llama_server_gpu_layers=99,
            llama_server_parallel=1,
            llama_server_startup_timeout_seconds=240,
            processed_transcription_output_dir="outputs/processed_transcriptions",
            processed_transcription_markdown_output_dir="outputs/human/processed_transcriptions",
            processed_transcription_rejected_output_dir="outputs/processed_transcriptions/rejected",
            processed_transcription_rejected_markdown_output_dir="outputs/human/processed_transcriptions/rejected",
            e03_study_package_output_dir="outputs/study_packages",
            e03_active_course_store="outputs/config/e03_courses.json",
            e03_obsidian_export_enabled=False,
            e03_obsidian_vaults_base_dir=None,
            e03_obsidian_vault_create_only=True,
            processed_transcription_queue_enabled=True,
            processed_transcription_queue_retry_seconds=60,
            processed_transcription_queue_max_attempts=3,
            transcription_mode="contract",
            transcription_backend="auto",
            transcription_model="test-transcription-model",
            transcription_fallback_model="turbo",
            transcription_output_dir="outputs/transcriptions",
            transcription_text_output_dir="outputs/human/transcriptions",
        )


if __name__ == "__main__":
    unittest.main()
