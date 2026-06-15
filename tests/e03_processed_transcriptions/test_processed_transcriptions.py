import asyncio
import ipaddress
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from main import app, create_app  # noqa: E402
from routers.upload_limits import (  # noqa: E402
    UPLOAD_READ_CHUNK_SIZE,
    read_upload_with_limit,
)
from services.postprocessing_service import (  # noqa: E402
    LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO,
    LONG_TRANSCRIPT_MIN_DIDACTIC_RATIO,
    PostprocessingServiceUnavailableError,
    PostprocessingTimeoutError,
    PostprocessingInsufficientCoverageError,
    _append_chunked_semantic_anchor_audit_note,
    _build_messages,
    _payload_from_llm_content,
    _semantic_coverage_anchors,
    _validate_semantic_coverage,
)
from services.llm_client import (  # noqa: E402
    LLMClientUnavailableError,
    LLMCompletion,
    OpenAICompatibleClient,
)
from services.processed_transcription_queue import process_pending_jobs  # noqa: E402
from scripts.benchmark_e03_models import Candidate, post_chat_completion  # noqa: E402
from schemas.transcriptions import TranscriptionMetadata  # noqa: E402
from settings import (  # noqa: E402
    DEFAULT_LLAMA_SERVER_PARALLEL,
    DEFAULT_LLM_MAX_OUTPUT_TOKENS,
    DEFAULT_LOCAL_LLM_BASE_URL,
    DEFAULT_LOCAL_LLM_MODEL,
    DEFAULT_LOCAL_LLM_PROVIDER,
    Settings,
    get_settings,
)


VALID_TOKEN = "test-token"
PROCESSED_TRANSCRIPTIONS_ENDPOINT = "/processed-transcriptions/v1.0.0"


class ProcessedTranscriptionsEndpointTest(unittest.TestCase):
    def setUp(self):
        self.previous_env = {
            "MINDVOX_API_TOKEN": os.environ.get("MINDVOX_API_TOKEN"),
            "MINDVOX_MAX_UPLOAD_MB": os.environ.get("MINDVOX_MAX_UPLOAD_MB"),
            "MINDVOX_PUBLIC_DEPLOYMENT": os.environ.get("MINDVOX_PUBLIC_DEPLOYMENT"),
            "MINDVOX_ENABLE_DOCS": os.environ.get("MINDVOX_ENABLE_DOCS"),
            "MINDVOX_TRUSTED_HOSTS": os.environ.get("MINDVOX_TRUSTED_HOSTS"),
            "MINDVOX_RUNTIME_PROFILE": os.environ.get("MINDVOX_RUNTIME_PROFILE"),
            "MINDVOX_TRANSCRIPTION_MODE": os.environ.get("MINDVOX_TRANSCRIPTION_MODE"),
            "MINDVOX_TRANSCRIPTION_MODEL": os.environ.get(
                "MINDVOX_TRANSCRIPTION_MODEL"
            ),
            "MINDVOX_POSTPROCESSING_MODE": os.environ.get(
                "MINDVOX_POSTPROCESSING_MODE"
            ),
            "MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS": os.environ.get(
                "MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS"
            ),
            "MINDVOX_POSTPROCESSING_CHUNKING_MODE": os.environ.get(
                "MINDVOX_POSTPROCESSING_CHUNKING_MODE"
            ),
            "MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS": os.environ.get(
                "MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS"
            ),
            "MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS": os.environ.get(
                "MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS"
            ),
            "MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED": os.environ.get(
                "MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED"
            ),
            "MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED": os.environ.get(
                "MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED"
            ),
            "MINDVOX_LLM_PROVIDER": os.environ.get("MINDVOX_LLM_PROVIDER"),
            "MINDVOX_LLM_BASE_URL": os.environ.get("MINDVOX_LLM_BASE_URL"),
            "MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS": os.environ.get(
                "MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS"
            ),
            "MINDVOX_LLM_MODEL": os.environ.get("MINDVOX_LLM_MODEL"),
            "MINDVOX_LLM_API_KEY": os.environ.get("MINDVOX_LLM_API_KEY"),
            "MINDVOX_LLM_MAX_OUTPUT_TOKENS": os.environ.get(
                "MINDVOX_LLM_MAX_OUTPUT_TOKENS"
            ),
            "MINDVOX_LLM_TIMEOUT_SECONDS": os.environ.get(
                "MINDVOX_LLM_TIMEOUT_SECONDS"
            ),
            "MINDVOX_LOCAL_LLM_AUTOSTART": os.environ.get(
                "MINDVOX_LOCAL_LLM_AUTOSTART"
            ),
            "MINDVOX_LLAMA_SERVER_PATH": os.environ.get("MINDVOX_LLAMA_SERVER_PATH"),
            "MINDVOX_LOCAL_LLM_MODEL_PATH": os.environ.get(
                "MINDVOX_LOCAL_LLM_MODEL_PATH"
            ),
            "MINDVOX_LLAMA_SERVER_CTX_SIZE": os.environ.get(
                "MINDVOX_LLAMA_SERVER_CTX_SIZE"
            ),
            "MINDVOX_LLAMA_SERVER_GPU_LAYERS": os.environ.get(
                "MINDVOX_LLAMA_SERVER_GPU_LAYERS"
            ),
            "MINDVOX_LLAMA_SERVER_PARALLEL": os.environ.get(
                "MINDVOX_LLAMA_SERVER_PARALLEL"
            ),
            "MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS": os.environ.get(
                "MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS"
            ),
            "MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR": os.environ.get(
                "MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR"
            ),
            "MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR": os.environ.get(
                "MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR"
            ),
            "MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR": os.environ.get(
                "MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR"
            ),
            "MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR": os.environ.get(
                "MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR"
            ),
            "MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR": os.environ.get(
                "MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR"
            ),
            "MINDVOX_E03_ACTIVE_COURSE_STORE": os.environ.get(
                "MINDVOX_E03_ACTIVE_COURSE_STORE"
            ),
            "MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED": os.environ.get(
                "MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED"
            ),
            "MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR": os.environ.get(
                "MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR"
            ),
            "MINDVOX_E03_OBSIDIAN_VAULT_CREATE_ONLY": os.environ.get(
                "MINDVOX_E03_OBSIDIAN_VAULT_CREATE_ONLY"
            ),
            "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED": os.environ.get(
                "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED"
            ),
            "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS": os.environ.get(
                "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS"
            ),
            "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS": os.environ.get(
                "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS"
            ),
            "MINDVOX_TRANSCRIPTION_OUTPUT_DIR": os.environ.get(
                "MINDVOX_TRANSCRIPTION_OUTPUT_DIR"
            ),
            "MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR": os.environ.get(
                "MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR"
            ),
        }
        self.output_directory = TemporaryDirectory()
        self.text_output_directory = TemporaryDirectory()
        self.processed_output_directory = TemporaryDirectory()
        self.processed_markdown_output_directory = TemporaryDirectory()
        self.study_package_output_directory = TemporaryDirectory()
        self.course_store_directory = TemporaryDirectory()
        os.environ["MINDVOX_API_TOKEN"] = VALID_TOKEN
        os.environ["MINDVOX_MAX_UPLOAD_MB"] = "500"
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "false"
        os.environ["MINDVOX_ENABLE_DOCS"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = ""
        os.environ["MINDVOX_RUNTIME_PROFILE"] = ""
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "contract"
        os.environ["MINDVOX_TRANSCRIPTION_MODEL"] = (
            "mlx-community/whisper-large-v3-turbo-fp16"
        )
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "contract"
        os.environ["MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS"] = "150000"
        os.environ["MINDVOX_POSTPROCESSING_CHUNKING_MODE"] = "off"
        os.environ["MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS"] = "20000"
        os.environ["MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS"] = "5000"
        os.environ["MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED"] = "true"
        os.environ["MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED"] = "true"
        os.environ["MINDVOX_LLM_PROVIDER"] = "groq"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://api.groq.com/openai/v1"
        os.environ["MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS"] = ""
        os.environ["MINDVOX_LLM_MODEL"] = "llama-3.3-70b-versatile"
        os.environ["MINDVOX_LLM_API_KEY"] = ""
        os.environ["MINDVOX_LLM_MAX_OUTPUT_TOKENS"] = "20000"
        os.environ["MINDVOX_LLM_TIMEOUT_SECONDS"] = "1200"
        os.environ["MINDVOX_LOCAL_LLM_AUTOSTART"] = "false"
        os.environ["MINDVOX_LLAMA_SERVER_PATH"] = ""
        os.environ["MINDVOX_LOCAL_LLM_MODEL_PATH"] = ""
        os.environ["MINDVOX_LLAMA_SERVER_CTX_SIZE"] = "65536"
        os.environ["MINDVOX_LLAMA_SERVER_GPU_LAYERS"] = "99"
        os.environ["MINDVOX_LLAMA_SERVER_PARALLEL"] = "1"
        os.environ["MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS"] = "240"
        os.environ["MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR"] = (
            self.processed_output_directory.name
        )
        os.environ["MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR"] = (
            self.processed_markdown_output_directory.name
        )
        os.environ["MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR"] = str(
            Path(self.processed_output_directory.name) / "rejected"
        )
        os.environ[
            "MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR"
        ] = str(Path(self.processed_markdown_output_directory.name) / "rejected")
        os.environ["MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR"] = (
            self.study_package_output_directory.name
        )
        os.environ["MINDVOX_E03_ACTIVE_COURSE_STORE"] = str(
            Path(self.course_store_directory.name) / "e03_courses.json"
        )
        os.environ["MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED"] = "false"
        os.environ["MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR"] = ""
        os.environ["MINDVOX_E03_OBSIDIAN_VAULT_CREATE_ONLY"] = "true"
        os.environ["MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED"] = "true"
        os.environ["MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS"] = "60"
        os.environ["MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS"] = "3"
        os.environ["MINDVOX_TRANSCRIPTION_OUTPUT_DIR"] = self.output_directory.name
        os.environ["MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR"] = (
            self.text_output_directory.name
        )
        self.client = TestClient(app)

    def tearDown(self):
        for name, value in self.previous_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.output_directory.cleanup()
        self.text_output_directory.cleanup()
        self.processed_output_directory.cleanup()
        self.processed_markdown_output_directory.cleanup()
        self.study_package_output_directory.cleanup()
        self.course_store_directory.cleanup()

    def test_post_processed_transcriptions_raw_text_contract_success(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            payload["processed_transcription_id"],
            r"^ptr_\d{8}T\d{6}Z_[0-9a-f]{8}$",
        )
        self.assertEqual(payload["input_type"], "raw_text")
        self.assertEqual(payload["language"], "pt-BR")
        self.assertEqual(payload["raw_text"], self._sample_raw_text())
        self.assertIn("contract-mode", payload["didactic_text"])
        self.assertEqual(payload["metadata"]["discipline"], "API")
        self.assertEqual(payload["processing_engine"]["mode"], "contract")

    def test_long_raw_text_can_use_internal_chunk_pipeline(self):
        os.environ["MINDVOX_POSTPROCESSING_CHUNKING_MODE"] = "tfidf"
        os.environ["MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS"] = "500"
        os.environ["MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS"] = "500"
        raw_text = "\n".join(
            [
                "A aula mencionou CIGA como forma ruidosa de SIGAA e discutiu API First, "
                "contratos OpenAPI, FastAPI e autenticacao Bearer.",
                "O professor retomou integracao de sistemas, dados academicos, "
                "governanca, processos de aula e organizacao de material didatico.",
            ]
            * 14
        )

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                **self._raw_text_payload(),
                "raw_text": raw_text,
            },
        )

        payload = response.json()
        note_types = {note["type"] for note in payload["processing_notes"]}
        notes_text = "\n".join(note["message"] for note in payload["processing_notes"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["raw_text"], raw_text)
        self.assertIn("chunk_merge", note_types)
        self.assertIn("pre_audit", note_types)
        self.assertIn("normalizacoes canonicas", notes_text)
        self.assertEqual(payload["processing_engine"]["mode"], "contract")

    def test_post_processed_transcriptions_raw_text_file_contract_success(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "raw_text",
                "language": "pt-BR",
                "processing_profile": "study_notes",
            },
            files={
                "raw_text_file": (
                    "e02-transcription.txt",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                )
            },
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["input_type"], "raw_text")
        self.assertEqual(payload["raw_text"], self._sample_raw_text())
        self.assertEqual(payload["source"]["input_origin"], "raw_text")
        self.assertEqual(payload["source"]["raw_text_origin"], "provided_by_client")

    def test_prepared_raw_text_file_name_fills_missing_metadata(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "raw_text_file",
                "language": "pt-BR",
                "processing_profile": "study_notes",
                "course": "UFG Pos 2",
            },
            files={
                "raw_text_file": (
                    "2026-05-09-api-rogerio-aula-1-sessao-4.txt",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                )
            },
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["metadata"]["course"], "UFG Pos 2")
        self.assertEqual(payload["metadata"]["discipline"], "API")
        self.assertEqual(payload["metadata"]["class_date"], "2026-05-09")
        self.assertEqual(
            payload["metadata"]["class_title"],
            "API - Aula 1 - Sessão 4 - Professor Rogerio",
        )
        self.assertEqual(payload["metadata"]["session_label"], "A1S4")

    def test_prepared_raw_text_file_keeps_custom_session_metadata(self):
        with self.assertLogs("mindvox.processed_transcriptions", level="WARNING") as logs:
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data={
                    "input_type": "raw_text_file",
                    "language": "pt-BR",
                    "processing_profile": "study_notes",
                    "class_date": "2026-05-09",
                    "class_title": "API - Aula 1 - Sessão 4 - Professor Rogério",
                    "session_label": "S2",
                },
                files={
                    "raw_text_file": (
                        "2026-05-09-api-rogerio-aula-1-sessao-4.txt",
                        self._sample_raw_text().encode("utf-8"),
                        "text/plain",
                    )
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["metadata"]["session_label"], "S2")
        self.assertIn(
            "processed_transcription_prepared_metadata_difference field=session_label",
            "\n".join(logs.output),
        )

    def test_prepared_raw_text_file_accepts_equivalent_session_metadata(self):
        for session_label in ["A1S01", "A1-S01", "S1", "S01", "API-Rogerio-A1-S01"]:
            with self.subTest(session_label=session_label):
                response = self.client.post(
                    PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                    headers=self._auth_headers(),
                    data={
                        "input_type": "raw_text_file",
                        "language": "pt-BR",
                        "processing_profile": "study_notes",
                        "class_date": "2026-05-09",
                        "class_title": "API - Aula 1 - Sessão 1 - Professor Rogério",
                        "session_label": session_label,
                    },
                    files={
                        "raw_text_file": (
                            "2026-05-09-api-rogerio-aula-1-sessao-1.txt",
                            self._sample_raw_text().encode("utf-8"),
                            "text/plain",
                        )
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json()["metadata"]["session_label"],
                    session_label,
                )

    def test_prepared_raw_text_file_keeps_custom_title_metadata(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "raw_text_file",
                "language": "pt-BR",
                "processing_profile": "study_notes",
                "class_date": "2026-05-09",
                "class_title": "API First and FastAPI",
                "session_label": "A1S4",
            },
            files={
                "raw_text_file": (
                    "2026-05-09-api-rogerio-aula-1-sessao-4.txt",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["metadata"]["class_title"],
            "API First and FastAPI",
        )

    def test_raw_text_file_ignores_legacy_swagger_string_placeholder(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "raw_text",
                "raw_text": "string",
                "language": "pt-BR",
                "processing_profile": "study_notes",
            },
            files={
                "raw_text_file": (
                    "e02-transcription.txt",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                )
            },
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["raw_text"], self._sample_raw_text())

    def test_raw_text_file_input_type_alias_is_normalized_to_raw_text(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "raw_text_file",
                "raw_text": "",
                "language": "pt-BR",
                "processing_profile": "study_notes",
            },
            files={
                "raw_text_file": (
                    "e02-transcription.txt",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                )
            },
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["input_type"], "raw_text")
        self.assertEqual(payload["raw_text"], self._sample_raw_text())

    def test_optional_date_string_placeholder_is_treated_as_empty(self):
        payload = self._raw_text_payload()
        payload["class_date"] = "string"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=payload,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["metadata"]["class_date"])

    def test_raw_text_flow_ignores_empty_audio_file_placeholder(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
            files={"audio_file": ("", b"", "application/octet-stream")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["raw_text"], self._sample_raw_text())

    def test_success_response_contains_five_deliveries_and_auxiliary_fields(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(payload),
            {
                "processed_transcription_id",
                "input_type",
                "language",
                "raw_text",
                "didactic_text",
                "themes",
                "technical_terms",
                "technology_mentions",
                "processing_notes",
                "metadata",
                "source",
                "processing_engine",
                "artifact_locations",
                "study_package",
            },
        )
        for field in [
            "raw_text",
            "didactic_text",
            "themes",
            "technical_terms",
            "technology_mentions",
        ]:
            self.assertIn(field, payload)
        self.assertIsInstance(payload["themes"], list)
        self.assertIsInstance(payload["technical_terms"], list)
        self.assertIsInstance(payload["technology_mentions"], list)
        self.assertIsInstance(payload["processing_notes"], list)
        self.assertEqual(
            payload["study_package"]["metadata"]["course_name"],
            "UFG Pos",
        )
        self.assertEqual(
            payload["study_package"]["memory_manifest"]["relational_target"],
            "sqlite",
        )
        self.assertIn(
            "didactic_text",
            payload["study_package"]["memory_manifest"]["vector_candidates"],
        )

    def test_contract_mode_does_not_invent_technology_mentions(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "raw_text",
                "raw_text": "A aula discutiu organizacao de estudos e revisao de conteudo.",
            },
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["technology_mentions"], [])

    def test_raw_text_source_has_no_transcription_object(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        source = response.json()["source"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(source["input_origin"], "raw_text")
        self.assertEqual(source["raw_text_origin"], "provided_by_client")
        self.assertIsNone(source["transcription"])

    def test_post_processed_transcriptions_audio_contract_success(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
            data={
                "input_type": "audio",
                "course": "UFG Pos",
                "discipline": "API",
                "class_date": "2026-06-09",
                "class_title": "API First and FastAPI",
                "session_label": "S02",
                "language": "pt-BR",
            },
        )

        payload = response.json()
        source = payload["source"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["input_type"], "audio")
        self.assertEqual(source["input_origin"], "audio")
        self.assertEqual(
            source["raw_text_origin"],
            "generated_by_transcription_service",
        )
        self.assertIsNotNone(source["transcription"])
        self.assertEqual(
            source["transcription"]["transcription_engine"]["name"],
            "contract-stub",
        )

    def test_audio_flow_saves_internal_raw_transcription_artifacts(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
            data={"input_type": "audio"},
        )

        payload = response.json()
        transcription_id = payload["source"]["transcription"]["transcription_id"]
        json_path, text_path = self._artifact_paths(transcription_id)
        artifact_payload = json.loads(json_path.read_text(encoding="utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_path.exists())
        self.assertTrue(text_path.exists())
        self.assertEqual(text_path.read_text(encoding="utf-8"), payload["raw_text"])
        self.assertEqual(artifact_payload["transcription_id"], transcription_id)
        self.assertEqual(artifact_payload["text"], payload["raw_text"])
        self.assertEqual(
            artifact_payload["artifact_locations"]["human_text_path"],
            f"$MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR/{transcription_id}.txt",
        )
        self.assertEqual(
            artifact_payload["artifact_locations"]["technical_json_path"],
            f"$MINDVOX_TRANSCRIPTION_OUTPUT_DIR/{transcription_id}.json",
        )

    def test_audio_flow_completes_generated_transcription_queue_job(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
            data={"input_type": "audio"},
        )

        payload = response.json()
        transcription_id = payload["source"]["transcription"]["transcription_id"]
        processed_id = payload["processed_transcription_id"]
        processed_path = self._processed_artifact_path(processed_id)
        markdown_path = self._processed_markdown_artifact_path(processed_id)
        study_package_path = self._study_package_artifact_path(processed_id)
        pending_path, completed_path = self._queue_paths(transcription_id)
        completed_payload = json.loads(completed_path.read_text(encoding="utf-8"))
        markdown_content = markdown_path.read_text(encoding="utf-8")
        study_package_payload = json.loads(
            study_package_path.read_text(encoding="utf-8")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(processed_path.exists())
        self.assertTrue(markdown_path.exists())
        self.assertTrue(study_package_path.exists())
        self.assertEqual(
            payload["artifact_locations"]["human_text_path"],
            f"$MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR/{processed_id}.md",
        )
        self.assertEqual(
            payload["artifact_locations"]["technical_json_path"],
            f"$MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR/{processed_id}.json",
        )
        self.assertIn("## Didactic Text", markdown_content)
        self.assertIn(payload["didactic_text"], markdown_content)
        self.assertIn("## Technology Mentions", markdown_content)
        self.assertEqual(
            study_package_payload["memory_manifest"]["relational_target"],
            "sqlite",
        )
        self.assertEqual(study_package_payload["source"]["input_origin"], "audio")
        self.assertIn(
            "didactic_text",
            study_package_payload["memory_manifest"]["vector_candidates"],
        )
        self.assertFalse(pending_path.exists())
        self.assertTrue(completed_path.exists())
        self.assertEqual(completed_payload["status"], "completed")
        self.assertEqual(completed_payload["processed_transcription_id"], processed_id)

    def test_processed_markdown_artifact_uses_class_metadata_title(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        payload = response.json()
        processed_id = payload["processed_transcription_id"]
        markdown_path = self._processed_markdown_artifact_path(processed_id)
        markdown_content = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("2026-06-09", markdown_path.name)
        self.assertIn("api-first-and-fastapi", markdown_path.name)
        self.assertIn("s02", markdown_path.name)
        self.assertTrue(markdown_path.name.endswith(f"{processed_id}.md"))
        self.assertEqual(
            payload["artifact_locations"]["human_text_path"].split("/")[-1],
            markdown_path.name,
        )
        self.assertIn("# 2026-06-09 - API First and FastAPI - S02", markdown_content)
        self.assertIn("## Class Metadata", markdown_content)
        self.assertIn("- Class date: `2026-06-09`", markdown_content)
        self.assertIn("- Class title: `API First and FastAPI`", markdown_content)

    def test_audio_flow_keeps_queue_job_pending_when_postprocessing_fails(self):
        with patch(
            "routers.processed_transcriptions.process_transcription",
            side_effect=PostprocessingServiceUnavailableError(),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                files=self._wav_file(),
                data={"input_type": "audio"},
            )

        transcription_artifacts = list(Path(self.output_directory.name).glob("*.json"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(len(transcription_artifacts), 1)

        transcription_id = json.loads(
            transcription_artifacts[0].read_text(encoding="utf-8")
        )["transcription_id"]
        pending_path, completed_path = self._queue_paths(transcription_id)
        pending_payload = json.loads(pending_path.read_text(encoding="utf-8"))

        self.assertTrue(pending_path.exists())
        self.assertFalse(completed_path.exists())
        self.assertEqual(pending_payload["status"], "pending")
        self.assertEqual(pending_payload["attempts"], 1)
        self.assertEqual(
            pending_payload["last_error"],
            "PostprocessingServiceUnavailableError",
        )

    def test_audio_flow_moves_quality_failure_to_failed_after_max_attempts(self):
        os.environ["MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS"] = "1"
        rejected_error = PostprocessingInsufficientCoverageError(
            "Rejected quality output.",
            retry_hint="didactic_text was too short",
            rejected_payload={
                "didactic_text": "Resumo curto.",
                "themes": [],
                "technical_terms": [],
                "technology_mentions": [],
                "processing_notes": [],
            },
        )

        with patch(
            "routers.processed_transcriptions.process_transcription",
            side_effect=rejected_error,
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                files=self._wav_file(),
                data={"input_type": "audio"},
            )

        transcription_id = json.loads(
            next(Path(self.output_directory.name).glob("*.json")).read_text(
                encoding="utf-8"
            )
        )["transcription_id"]
        pending_path, completed_path = self._queue_paths(transcription_id)
        failed_path = self._queue_failed_path(
            transcription_id,
            "PostprocessingInsufficientCoverageError",
        )
        rejected_json = list(
            (Path(self.processed_output_directory.name) / "rejected").glob("*.json")
        )

        self.assertEqual(response.status_code, 502)
        self.assertFalse(pending_path.exists())
        self.assertFalse(completed_path.exists())
        self.assertTrue(failed_path.exists())
        self.assertEqual(
            json.loads(failed_path.read_text(encoding="utf-8"))["status"],
            "failed",
        )
        self.assertEqual(len(rejected_json), 1)
        rejected_payload = json.loads(rejected_json[0].read_text(encoding="utf-8"))
        runtime_snapshot = rejected_payload["runtime_snapshot"]
        self.assertEqual(runtime_snapshot["llm_max_output_tokens"], 20000)
        self.assertEqual(runtime_snapshot["llm_model"], "llama-3.3-70b-versatile")
        self.assertIn("chunk_pipeline_enabled", runtime_snapshot)
        self.assertIn("semantic_gate_minimum_didactic_chars_chunked", runtime_snapshot)

    def test_pending_generated_transcription_job_can_be_retried_without_reupload(self):
        with patch(
            "routers.processed_transcriptions.process_transcription",
            side_effect=PostprocessingServiceUnavailableError(),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                files=self._wav_file(),
                data={"input_type": "audio"},
            )

        transcription_id = json.loads(
            next(Path(self.output_directory.name).glob("*.json")).read_text(
                encoding="utf-8"
            )
        )["transcription_id"]
        pending_path, completed_path = self._queue_paths(transcription_id)

        self.assertEqual(response.status_code, 503)
        self.assertTrue(pending_path.exists())

        summary = process_pending_jobs(settings=get_settings())

        self.assertEqual(summary.attempted, 1)
        self.assertEqual(summary.completed, 1)
        self.assertEqual(summary.failed, 0)
        self.assertFalse(pending_path.exists())
        self.assertTrue(completed_path.exists())

    def test_missing_token_returns_401(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_processed_transcription_auth_failure_logs_status_error_and_duration(self):
        with self.assertLogs("mindvox.processed_transcriptions", level="WARNING") as logs:
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                data=self._raw_text_payload(),
            )

        serialized_logs = "\n".join(logs.output).lower()

        self.assertEqual(response.status_code, 401)
        self.assertIn("processed_transcription_auth_failed", serialized_logs)
        self.assertIn("status_code=401", serialized_logs)
        self.assertIn("error_code=missing_credentials", serialized_logs)
        self.assertIn("phase=auth", serialized_logs)
        self.assertIn("duration_ms=", serialized_logs)
        for term in [VALID_TOKEN, "authorization", "bearer"]:
            self.assertNotIn(term.lower(), serialized_logs)

    def test_invalid_token_returns_401(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": "Bearer wrong-token"},
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_placeholder_api_token_configuration_returns_503(self):
        os.environ["MINDVOX_API_TOKEN"] = "replace-with-local-token"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": "Bearer replace-with-local-token"},
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_dev_token_configuration_returns_503_in_public_deployment(self):
        os.environ["MINDVOX_API_TOKEN"] = "dev-token"
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"

        secure_client = TestClient(app, base_url="https://api.example.com")

        response = secure_client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": "Bearer dev-token"},
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_public_deployment_requires_https_for_processed_transcriptions(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "HTTPS is required for public deployment."},
        )

    def test_public_deployment_accepts_https_for_processed_transcriptions(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"
        secure_client = TestClient(app, base_url="https://api.example.com")

        response = secure_client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 200)

    def test_malformed_authorization_header_returns_401(self):
        malformed_headers = [
            "Token test-token",
            "Bearer",
            "Bearer ",
        ]

        for authorization in malformed_headers:
            with self.subTest(authorization=authorization):
                response = self.client.post(
                    PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                    headers={"Authorization": authorization},
                    data=self._raw_text_payload(),
                )

                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_missing_main_input_returns_422(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={"input_type": "raw_text"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {"detail": "raw_text or raw_text_file is required when input_type is raw_text."},
        )

    def test_invalid_input_type_returns_422(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "video",
                "raw_text": self._sample_raw_text(),
            },
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertIn("input_type", str(detail))
        self.assertIn("audio", str(detail))
        self.assertIn("raw_text", str(detail))
        self.assertIn("raw_text_file", str(detail))

    def test_audio_input_without_audio_file_returns_422(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={"input_type": "audio"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {"detail": "audio_file is required when input_type is audio."},
        )

    def test_audio_and_raw_text_conflict_returns_422(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
            data={
                "input_type": "audio",
                "raw_text": self._sample_raw_text(),
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {"detail": "audio_file cannot be sent together with raw_text or raw_text_file."},
        )

    def test_raw_text_and_raw_text_file_conflict_returns_422(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
            files={
                "raw_text_file": (
                    "e02-transcription.txt",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {"detail": "raw_text and raw_text_file cannot be sent together."},
        )

    def test_audio_and_raw_text_file_conflict_returns_422(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                **self._wav_file(),
                "raw_text_file": (
                    "e02-transcription.txt",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                ),
            },
            data={"input_type": "audio"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {"detail": "audio_file cannot be sent together with raw_text or raw_text_file."},
        )

    def test_invalid_raw_text_file_extension_returns_400(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={
                "input_type": "raw_text",
                "language": "pt-BR",
                "processing_profile": "study_notes",
            },
            files={
                "raw_text_file": (
                    "e02-transcription.md",
                    self._sample_raw_text().encode("utf-8"),
                    "text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Unsupported raw text file type. Supported format: .txt."},
        )

    def test_invalid_processing_profile_returns_422(self):
        payload = self._raw_text_payload()
        payload["processing_profile"] = "executive_summary"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=payload,
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {"detail": "processing_profile must be study_notes."},
        )

    def test_invalid_audio_extension_returns_400(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "class.txt",
                    b"not audio",
                    "text/plain",
                )
            },
            data={"input_type": "audio"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Unsupported audio file type. Supported formats: .wav, .m4a."},
        )

    def test_incompatible_audio_content_type_returns_400(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "class.wav",
                    self._minimal_wav_bytes(),
                    "audio/mp4",
                )
            },
            data={"input_type": "audio"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Unsupported audio content type."})

    def test_invalid_metadata_returns_422(self):
        invalid_payloads = [
            (
                {"class_date": "09/06/2026"},
                "class_date must use YYYY-MM-DD.",
            ),
            (
                {"session_label": "s1/../../secret"},
                "session_label must be short and use simple characters.",
            ),
            (
                {"language": "portuguese"},
                "language must use a simple locale format such as pt-BR.",
            ),
        ]

        for data, expected_detail in invalid_payloads:
            with self.subTest(data=data):
                payload = self._raw_text_payload()
                payload.update(data)
                response = self.client.post(
                    PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                    headers=self._auth_headers(),
                    data=payload,
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json(), {"detail": expected_detail})

    def test_oversized_optional_metadata_returns_422(self):
        invalid_payloads = [
            (
                {"course": "x" * 161},
                "course must be 160 characters or fewer.",
            ),
            (
                {"discipline": "x" * 121},
                "discipline must be 120 characters or fewer.",
            ),
            (
                {"class_title": "x" * 201},
                "class_title must be 200 characters or fewer.",
            ),
        ]

        for data, expected_detail in invalid_payloads:
            with self.subTest(data=list(data)):
                payload = self._raw_text_payload()
                payload.update(data)
                response = self.client.post(
                    PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                    headers=self._auth_headers(),
                    data=payload,
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json(), {"detail": expected_detail})

    def test_raw_text_over_limit_returns_413(self):
        os.environ["MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS"] = "10"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.json(),
            {"detail": "Raw text exceeds the maximum allowed size."},
        )

    def test_audio_over_upload_limit_returns_413(self):
        os.environ["MINDVOX_MAX_UPLOAD_MB"] = "1"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "class_s1.wav",
                    b"x" * (1024 * 1024 + 1),
                    "audio/wav",
                )
            },
            data={"input_type": "audio"},
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.json(),
            {"detail": "Audio file exceeds the maximum allowed size."},
        )

    def test_limited_upload_reader_rejects_before_reading_full_oversized_upload(self):
        settings = self._settings(max_upload_mb=1)
        upload = _FakeUpload(
            [
                b"x" * UPLOAD_READ_CHUNK_SIZE,
                b"y",
                b"z",
            ]
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(
                read_upload_with_limit(
                    upload,
                    settings=settings,
                    detail="Audio file exceeds the maximum allowed size.",
                )
            )

        self.assertEqual(context.exception.status_code, 413)
        self.assertEqual(
            context.exception.detail,
            "Audio file exceeds the maximum allowed size.",
        )
        self.assertEqual(
            upload.read_sizes,
            [UPLOAD_READ_CHUNK_SIZE, UPLOAD_READ_CHUNK_SIZE],
        )
        self.assertEqual(upload.remaining_chunks, [b"z"])

    def test_unavailable_processing_engine_returns_503(self):
        with patch(
            "routers.processed_transcriptions.process_transcription",
            side_effect=PostprocessingServiceUnavailableError(),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data=self._raw_text_payload(),
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_placeholder_provider_key_returns_503(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_API_KEY"] = "replace-with-provider-key"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_empty_provider_key_returns_503(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_API_KEY"] = ""

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_provider_mode_rejects_localhost_endpoint(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "http://127.0.0.1:8080/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_provider_mode_rejects_hostname_resolving_to_private_address(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://internal.example/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"

        with patch(
            "services.postprocessing_service._resolve_host_addresses",
            return_value=(ipaddress.ip_address("10.0.0.10"),),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data=self._raw_text_payload(),
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_provider_mode_rejects_hostname_outside_allowed_list(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://example.com/v1"
        os.environ["MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS"] = "api.groq.com"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_provider_mode_accepts_hostname_inside_allowed_list(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://api.groq.com/openai/v1"
        os.environ["MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS"] = "api.groq.com"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"

        with patch(
            "services.postprocessing_service._resolve_host_addresses",
            return_value=(ipaddress.ip_address("8.8.8.8"),),
        ):
            with patch(
                "services.postprocessing_service.OpenAICompatibleClient.complete_json",
                return_value=LLMCompletion(content=json.dumps(self._valid_llm_payload())),
            ):
                response = self.client.post(
                    PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                    headers=self._auth_headers(),
                    data=self._raw_text_payload(),
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["processing_engine"]["name"],
            "groq-openai-compatible",
        )

    def test_local_mode_rejects_public_endpoint(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "local"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://api.groq.com/openai/v1"

        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data=self._raw_text_payload(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_local_unavailable_processing_engine_returns_503(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "local"
        os.environ["MINDVOX_LLM_BASE_URL"] = "http://127.0.0.1:8080/v1"

        with patch(
            "services.postprocessing_service.OpenAICompatibleClient.complete_json",
            side_effect=LLMClientUnavailableError(),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data=self._raw_text_payload(),
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing service is unavailable."},
        )

    def test_invalid_llm_output_returns_500(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://8.8.8.8/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"

        with patch(
            "services.postprocessing_service.OpenAICompatibleClient.complete_json",
            return_value=LLMCompletion(content='{"themes": []}'),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data=self._raw_text_payload(),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Internal post-processing error."})

    def test_long_llm_output_with_insufficient_semantic_coverage_returns_502_with_rejected_artifact(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://8.8.8.8/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"
        insufficient_payload = self._valid_llm_payload()

        with patch(
            "services.postprocessing_service.OpenAICompatibleClient.complete_json",
            return_value=LLMCompletion(content=json.dumps(insufficient_payload)),
        ) as complete_json:
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data={
                    **self._raw_text_payload(),
                    "raw_text": self._long_raw_text(),
                },
            )

        self.assertEqual(response.status_code, 502)
        detail = response.json()["detail"]
        self.assertEqual(detail["error_code"], "postprocessing_quality_rejected")
        self.assertEqual(detail["last_error"], "PostprocessingInsufficientCoverageError")
        self.assertEqual(detail["attempt"], 1)
        self.assertFalse(detail["will_retry"])
        self.assertIn("rejected_artifacts", detail)
        rejected_dir = Path(self.processed_output_directory.name) / "rejected"
        rejected_reports_dir = (
            Path(self.processed_markdown_output_directory.name) / "rejected"
        )
        rejected_json = list(rejected_dir.glob("*.json"))
        rejected_markdown = list(rejected_reports_dir.glob("*.md"))
        self.assertEqual(len(rejected_json), 1)
        self.assertEqual(len(rejected_markdown), 1)
        rejected_payload = json.loads(rejected_json[0].read_text(encoding="utf-8"))
        self.assertEqual(
            rejected_payload["status"],
            "rejected_by_semantic_coverage_gate",
        )
        self.assertEqual(rejected_payload["metrics"]["themes_count"], 1)
        runtime_snapshot = rejected_payload["runtime_snapshot"]
        self.assertEqual(runtime_snapshot["chunking_mode"], "off")
        self.assertFalse(runtime_snapshot["chunk_pipeline_enabled"])
        self.assertEqual(runtime_snapshot["chunk_count"], 0)
        self.assertEqual(runtime_snapshot["llm_max_output_tokens"], 20000)
        self.assertEqual(runtime_snapshot["llm_model"], "llama-3.3-70b-versatile")
        self.assertGreater(
            runtime_snapshot["semantic_gate_minimum_didactic_chars_monolithic"],
            0,
        )
        self.assertEqual(complete_json.call_count, 2)

    def test_long_llm_output_retry_can_recover_semantic_coverage(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://8.8.8.8/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"
        raw_text = self._long_raw_text()

        with patch(
            "services.postprocessing_service.OpenAICompatibleClient.complete_json",
            side_effect=[
                LLMCompletion(content=json.dumps(self._valid_llm_payload())),
                LLMCompletion(content=json.dumps(self._valid_long_llm_payload(raw_text))),
            ],
        ) as complete_json:
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data={
                    **self._raw_text_payload(),
                    "raw_text": raw_text,
                },
            )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(payload["didactic_text"]), int(len(raw_text) * 0.35))
        self.assertGreaterEqual(len(payload["themes"]), 8)
        self.assertEqual(complete_json.call_count, 2)
        self.assertIn(
            "insufficient semantic coverage",
            payload["processing_notes"][-1]["message"],
        )

    def test_chunked_semantic_coverage_allows_compact_anchor_preserving_merge(self):
        raw_text = self._long_raw_text()
        compact_payload = self._valid_long_llm_payload(raw_text)
        compact_payload["didactic_text"] = self._anchor_preserving_text_for_ratio(
            raw_text,
            ratio=LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO,
        )

        payload = _payload_from_llm_content(json.dumps(compact_payload))

        _validate_semantic_coverage(
            payload=payload,
            raw_text=raw_text,
            minimum_didactic_ratio=LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO,
        )
        with self.assertRaises(PostprocessingInsufficientCoverageError):
            _validate_semantic_coverage(payload=payload, raw_text=raw_text)

    def test_chunked_semantic_coverage_records_missing_anchors_without_rejecting(self):
        raw_text = self._long_raw_text()
        compact_payload = self._valid_long_llm_payload(raw_text)
        didactic_fragment = (
            "A aula tratou de API First, contratos, documentacao e integracao "
            "entre sistemas. "
        )
        compact_payload["didactic_text"] = didactic_fragment * max(
            1,
            int(
                len(raw_text)
                * LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO
                / len(didactic_fragment)
            )
            + 2,
        )
        compact_payload["themes"] = [
            {
                "order": index,
                "title": f"Tema generico {index}",
                "summary": "A aula abordou fundamentos gerais de APIs.",
                "key_points": ["Contratos ajudam sistemas a trocar dados."],
                "semantic_role": "fundamento",
                "evidence": "API",
            }
            for index in range(1, 9)
        ]
        compact_payload["processing_notes"] = [
            {
                "type": "audit",
                "message": (
                    "Nota operacional cita Positivo, NPS, Data Lake, AutoML e "
                    "Mainframe, mas isso nao conta como cobertura semantica."
                ),
            }
        ]

        payload = _payload_from_llm_content(json.dumps(compact_payload))

        _validate_semantic_coverage(
            payload=payload,
            raw_text=raw_text,
            minimum_didactic_ratio=LONG_TRANSCRIPT_CHUNKED_MIN_DIDACTIC_RATIO,
            enforce_semantic_anchors=False,
        )
        _append_chunked_semantic_anchor_audit_note(payload=payload, raw_text=raw_text)

        self.assertEqual(payload.processing_notes[-1].type, "semantic_anchor_audit")

    def test_semantic_anchors_do_not_treat_generic_positive_as_company(self):
        raw_text = (
            "A aula discutiu API First e os pontos positivos e negativos da "
            "arquitetura baseada em APIs. "
            * 260
        )

        labels = {anchor.label for anchor in _semantic_coverage_anchors(raw_text)}

        self.assertNotIn("Positivo", labels)

    def test_semantic_anchors_detect_possibly_named_positivo_company(self):
        raw_text = (
            "O professor descreveu um projeto com a empresa Positivo sobre "
            "licitacoes publicas e analise de editais. "
            * 240
        )

        labels = {anchor.label for anchor in _semantic_coverage_anchors(raw_text)}

        self.assertIn("Positivo", labels)

    def test_semantic_anchors_ignore_capitalized_discourse_words(self):
        block = (
            "Então, o aluno perguntou sobre os squads. "
            "Acho que a professora explicou o cronograma. "
            "Alguém comentou que temos entregas semanais. "
            "Temos uma discussão sobre órgãos públicos e gestão. "
        )
        raw_text = block * 180

        labels = {anchor.label for anchor in _semantic_coverage_anchors(raw_text)}

        self.assertNotIn("Então", labels)
        self.assertNotIn("Acho", labels)
        self.assertNotIn("Alguém", labels)
        self.assertNotIn("Temos", labels)
        self.assertIn("orgaos publicos", labels)

    def test_semantic_anchors_do_not_treat_generic_score_as_viability_case(self):
        raw_text = (
            "A aula mencionou um exemplo hipotetico de score financeiro da pessoa "
            "para explicar APIs e campos de retorno. "
            * 240
        )

        labels = {anchor.label for anchor in _semantic_coverage_anchors(raw_text)}

        self.assertNotIn("score de viabilidade", labels)

    def test_semantic_coverage_matches_microsservicos_accented_spelling(self):
        raw_text = (
            "A aula explicou microsserviços, arquitetura de APIs, integração "
            "entre sistemas e separação de responsabilidades. "
            * 220
        )
        didactic_fragment = (
            "A aula preservou a discussão sobre microsserviços, arquitetura de "
            "APIs, integração entre sistemas e separação de responsabilidades. "
        )
        payload_data = self._valid_llm_payload()
        payload_data["didactic_text"] = didactic_fragment * max(
            1,
            int(len(raw_text) * LONG_TRANSCRIPT_MIN_DIDACTIC_RATIO / len(didactic_fragment))
            + 2,
        )
        payload_data["themes"] = [
            {
                "order": index,
                "title": f"Tema {index}",
                "summary": "A aula preservou microsserviços e APIs.",
                "key_points": ["Microsserviços foram discutidos."],
                "semantic_role": "conteudo_preservado",
                "evidence": "microsserviços",
            }
            for index in range(1, 9)
        ]

        payload = _payload_from_llm_content(json.dumps(payload_data))

        _validate_semantic_coverage(payload=payload, raw_text=raw_text)

    def test_long_llm_output_missing_semantic_anchors_returns_502(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://8.8.8.8/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"
        raw_text = self._long_raw_text()
        editorial_payload = self._valid_long_llm_payload(raw_text)
        editorial_payload["didactic_text"] = (
            "A aula tratou de API First, documentacao, contratos e boas praticas "
            "de integracao entre sistemas. "
            * max(1, (int(len(raw_text) * 0.36) // 88) + 1)
        )
        editorial_payload["themes"] = [
            {
                "order": index,
                "title": f"Tema generico {index}",
                "summary": "A aula abordou fundamentos gerais de APIs.",
                "key_points": ["Contratos ajudam sistemas a trocar dados."],
                "semantic_role": "fundamento",
                "evidence": "API",
            }
            for index in range(1, 9)
        ]

        with patch(
            "services.postprocessing_service.OpenAICompatibleClient.complete_json",
            return_value=LLMCompletion(content=json.dumps(editorial_payload)),
        ) as complete_json:
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data={
                    **self._raw_text_payload(),
                    "raw_text": raw_text,
                },
            )

        self.assertEqual(response.status_code, 502)
        detail = response.json()["detail"]
        self.assertEqual(detail["error_code"], "postprocessing_quality_rejected")
        self.assertIn("output omitted protected semantic coverage anchors", detail["retry_hint"])
        self.assertEqual(complete_json.call_count, 2)

    def test_llm_output_with_common_aliases_is_normalized_to_e03_schema(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://8.8.8.8/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"
        llm_content = """
        The processed result follows.
        {
          "clean_text": "A aula explicou o uso de APIs e documentacao tecnica.",
          "temas": [
            {
              "titulo": "Documentacao da API",
              "resumo": "A aula tratou de Swagger e contratos OpenAPI.",
              "pontos_chave": "Swagger ajuda o usuario a entender parametros.",
              "papel_semantico": "pratica",
              "evidencia": "Swagger"
            }
          ],
          "termos_tecnicos": [
            {
              "termo": "API First",
              "nota": "Contrato definido antes da implementacao.",
              "confianca": "alta"
            }
          ],
          "tecnologias": [
            {
              "nome": "FastAPI",
              "categoria": "ferramenta",
              "contexto": "Usado para expor endpoints e Swagger.",
              "importancia": "alta",
              "confianca": "media",
              "evidencia": "FastAPI"
            }
          ],
          "notas_processamento": [
            "Valores do LLM foram normalizados para o contrato E03."
          ]
        }
        """

        with patch(
            "services.postprocessing_service.OpenAICompatibleClient.complete_json",
            return_value=LLMCompletion(content=llm_content),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data=self._raw_text_payload(),
            )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload["didactic_text"],
            "A aula explicou o uso de APIs e documentacao tecnica.",
        )
        self.assertEqual(payload["themes"][0]["order"], 1)
        self.assertEqual(payload["themes"][0]["key_points"], [
            "Swagger ajuda o usuario a entender parametros."
        ])
        self.assertEqual(payload["technical_terms"][0]["confidence"], "high")
        self.assertEqual(payload["technology_mentions"][0]["category"], "tool")
        self.assertEqual(payload["technology_mentions"][0]["importance"], "high")
        self.assertEqual(payload["technology_mentions"][0]["confidence"], "medium")
        self.assertEqual(payload["processing_notes"][0]["type"], "processing")

    def test_payload_normalizer_accepts_markdown_json_fence(self):
        payload = _payload_from_llm_content(
            """
            ```json
            {
              "didactic_text": "Texto didatico em JSON cercado por Markdown.",
              "themes": [],
              "technical_terms": [],
              "technology_mentions": [],
              "processing_notes": []
            }
            ```
            """
        )

        self.assertEqual(
            payload.didactic_text,
            "Texto didatico em JSON cercado por Markdown.",
        )
        self.assertEqual(payload.themes[0].title, "Processed class content")
        self.assertEqual(payload.processing_notes[0].type, "processing")

    def test_processing_engine_redacts_sensitive_provider_name(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "provider"
        os.environ["MINDVOX_LLM_PROVIDER"] = "secret-token-provider"
        os.environ["MINDVOX_LLM_BASE_URL"] = "https://8.8.8.8/v1"
        os.environ["MINDVOX_LLM_API_KEY"] = "test-provider-key"

        with patch(
            "services.postprocessing_service.OpenAICompatibleClient.complete_json",
            return_value=LLMCompletion(content=json.dumps(self._valid_llm_payload())),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data=self._raw_text_payload(),
            )

        serialized_payload = json.dumps(response.json()).lower()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["processing_engine"]["name"],
            "configured-provider-openai-compatible",
        )
        self.assertNotIn("secret-token-provider", serialized_payload)

    def test_processing_engine_timeout_returns_504(self):
        with patch(
            "routers.processed_transcriptions.process_transcription",
            side_effect=PostprocessingTimeoutError(),
        ):
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data=self._raw_text_payload(),
            )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(
            response.json(),
            {"detail": "Post-processing engine timed out."},
        )

    def test_get_processed_transcriptions_returns_405(self):
        response = self.client.get(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {"detail": "Method Not Allowed"})

    def test_public_deployment_requires_trusted_hosts(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ.pop("MINDVOX_TRUSTED_HOSTS", None)

        with self.assertRaisesRegex(RuntimeError, "MINDVOX_TRUSTED_HOSTS"):
            create_app()

    def test_public_deployment_rejects_wildcard_trusted_hosts(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "*"

        with self.assertRaisesRegex(RuntimeError, "cannot contain '\\*'"):
            create_app()

    def test_public_deployment_disables_docs_and_enforces_trusted_hosts(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ.pop("MINDVOX_ENABLE_DOCS", None)
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"

        public_app = create_app()
        client = TestClient(public_app)

        docs_response = client.get("/openapi.json", headers={"host": "api.example.com"})
        allowed_host_response = client.get("/health", headers={"host": "api.example.com"})
        rejected_host_response = client.get("/health", headers={"host": "bad.example"})

        self.assertEqual(public_app.docs_url, None)
        self.assertEqual(public_app.openapi_url, None)
        self.assertEqual(docs_response.status_code, 404)
        self.assertEqual(allowed_host_response.status_code, 200)
        self.assertEqual(rejected_host_response.status_code, 400)

    def test_openapi_documents_e03_contract(self):
        openapi_client = TestClient(create_app())
        response = openapi_client.get("/openapi.json")
        openapi = response.json()
        operation = openapi["paths"][PROCESSED_TRANSCRIPTIONS_ENDPOINT]["post"]

        self.assertEqual(response.status_code, 200)
        self.assertIn("Active startup profile", openapi["info"]["description"])
        self.assertIn("`contract`", openapi["info"]["description"])
        self.assertEqual(operation["summary"], "Post-process class transcription")
        self.assertIn("five deliveries", operation["description"])
        self.assertIn("raw_text", operation["description"])
        self.assertIn("didactic_text", operation["description"])
        self.assertIn("themes", operation["description"])
        self.assertIn("technical_terms", operation["description"])
        self.assertIn("technology_mentions", operation["description"])
        self.assertIn("does not store memory", operation["description"])
        self.assertIn("provider mode", operation["description"])
        self.assertIn("multipart/form-data", operation["requestBody"]["content"])
        schema_ref = operation["requestBody"]["content"]["multipart/form-data"]["schema"][
            "$ref"
        ]
        schema_name = schema_ref.removeprefix("#/components/schemas/")
        request_schema = openapi["components"]["schemas"][schema_name]
        request_properties = request_schema["properties"]
        input_type_schema = self._resolve_openapi_schema(
            openapi,
            request_properties["input_type"],
        )
        input_type_description = request_properties["input_type"]["description"]

        self.assertIn("input_type", request_schema["required"])
        self.assertIn("Example: audio", input_type_description)
        self.assertIn(
            "Type exactly one lowercase English value",
            input_type_description,
        )
        self.assertIn(
            "Do not translate",
            input_type_description,
        )
        self.assertIn(
            "raw_text_file is also accepted",
            input_type_description,
        )
        self.assertEqual(
            input_type_schema["enum"],
            ["audio", "raw_text", "raw_text_file"],
        )
        self.assertIn(".wav", request_properties["audio_file"]["description"])
        self.assertIn(".m4a", request_properties["audio_file"]["description"])
        self.assertIn(
            "Leave this empty when input_type is raw_text",
            request_properties["audio_file"]["description"],
        )
        self.assertIn(
            "previous STT run",
            request_properties["raw_text"]["description"],
        )
        self.assertIn(
            "Fill this only when input_type is exactly raw_text",
            request_properties["raw_text"]["description"],
        )
        for optional_field in [
            "raw_text",
            "course",
            "discipline",
            "class_date",
            "class_title",
            "session_label",
        ]:
            self.assertEqual(request_properties[optional_field]["default"], "")
        self.assertIn(
            "starts empty by default",
            request_properties["raw_text"]["description"],
        )
        self.assertIn(".txt", request_properties["raw_text_file"]["description"])
        self.assertIn(
            "Send either raw_text or raw_text_file, not both",
            request_properties["raw_text_file"]["description"],
        )
        self.assertIn(
            "Leave raw_text and audio_file empty",
            request_properties["raw_text_file"]["description"],
        )
        self.assertIn(
            "Federal University of Goias",
            request_properties["course"]["description"],
        )
        self.assertIn(
            "API Engineering for AI",
            request_properties["discipline"]["description"],
        )
        self.assertIn("YYYY-MM-DD", request_properties["class_date"]["description"])
        self.assertIn("Leave this empty", request_properties["class_date"]["description"])
        self.assertIn("API First and FastAPI", request_properties["class_title"]["description"])
        self.assertIn("Example: S02", request_properties["session_label"]["description"])
        self.assertIn("Example: pt-BR", request_properties["language"]["description"])
        self.assertIn(
            "Example: study_notes",
            request_properties["processing_profile"]["description"],
        )
        self.assertIn(
            "Type exactly study_notes",
            request_properties["processing_profile"]["description"],
        )
        self.assertIn("security", operation)
        self.assertEqual(operation["responses"]["200"]["description"], "Successful Response")
        for status_code in ["400", "401", "403", "405", "413", "422", "500", "502", "503", "504"]:
            self.assertIn(status_code, operation["responses"])

        security_schemes = openapi["components"]["securitySchemes"]
        self.assertIn("HTTPBearer", security_schemes)
        self.assertEqual(security_schemes["HTTPBearer"]["scheme"], "bearer")

    def test_response_and_errors_do_not_expose_sensitive_values(self):
        response = self.client.post(
            PROCESSED_TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": "Bearer wrong-token"},
            data={
                "input_type": "raw_text",
                "raw_text": "safe classroom text",
                "session_label": "secret/../../hidden",
            },
        )

        serialized_payload = json.dumps(response.json()).lower()

        self.assertEqual(response.status_code, 401)
        for term in [
            VALID_TOKEN,
            "wrong-token",
            "authorization",
            ".env",
            "/users/",
            "secret/../../hidden",
        ]:
            self.assertNotIn(term.lower(), serialized_payload)

    def test_e03_logs_are_sanitized(self):
        sensitive_raw_text = (
            "student hidden transcript with PRIVATE_RAW_MARKER and API discussion"
        )

        with self.assertLogs("mindvox.processed_transcriptions", level="INFO") as logs:
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data={
                    "input_type": "raw_text",
                    "raw_text": sensitive_raw_text,
                    "course": "Private Course",
                    "session_label": "S02",
                    "language": "pt-BR",
                },
            )

        serialized_logs = "\n".join(logs.output).lower()

        self.assertEqual(response.status_code, 200)
        self.assertIn("processed_transcription_auth_succeeded", serialized_logs)
        self.assertIn("processed_transcription_request_started", serialized_logs)
        self.assertIn("processed_transcription_request_succeeded", serialized_logs)
        self.assertIn("raw_text_chars=", serialized_logs)
        self.assertIn("themes_count=", serialized_logs)
        for term in [
            VALID_TOKEN,
            "authorization",
            "private_raw_marker",
            "student hidden transcript",
            "private course",
            ".env",
            "/users/",
            "bearer",
        ]:
            self.assertNotIn(term.lower(), serialized_logs)

    def test_controlled_validation_errors_are_logged_without_sensitive_values(self):
        sensitive_raw_text = "PRIVATE_RAW_MARKER should not appear in logs"

        with self.assertLogs("mindvox.processed_transcriptions", level="WARNING") as logs:
            response = self.client.post(
                PROCESSED_TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                data={
                    "input_type": "raw_text",
                    "raw_text": sensitive_raw_text,
                    "processing_profile": "executive_summary",
                },
            )

        serialized_logs = "\n".join(logs.output).lower()

        self.assertEqual(response.status_code, 422)
        self.assertIn("processed_transcription_request_failed", serialized_logs)
        self.assertIn("status_code=422", serialized_logs)
        self.assertIn("error_code=validation_failed", serialized_logs)
        self.assertIn("duration_ms=", serialized_logs)
        for term in [VALID_TOKEN, "private_raw_marker", "executive_summary", "authorization"]:
            self.assertNotIn(term.lower(), serialized_logs)

    def test_llm_client_sends_max_tokens_and_limits_response_size(self):
        body = json.dumps(
            {"choices": [{"message": {"content": '{"didactic_text": "ok"}'}}]}
        ).encode("utf-8")
        fake_response = _FakeHTTPResponse(body)
        settings = self._llm_client_settings(max_output_tokens=7)

        with patch("services.llm_client.request.urlopen", return_value=fake_response) as urlopen:
            completion = OpenAICompatibleClient(settings).complete_json(
                messages=[{"role": "user", "content": "hello"}]
            )

        sent_payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))

        self.assertEqual(completion.content, '{"didactic_text": "ok"}')
        self.assertEqual(sent_payload["max_tokens"], 7)
        self.assertEqual(fake_response.read_size, 65537)

    def test_llm_client_disables_thinking_for_local_llama_server(self):
        body = json.dumps(
            {"choices": [{"message": {"content": '{"didactic_text": "ok"}'}}]}
        ).encode("utf-8")
        fake_response = _FakeHTTPResponse(body)
        settings = self._llm_client_settings(
            max_output_tokens=7,
            postprocessing_mode="local",
        )

        with patch("services.llm_client.request.urlopen", return_value=fake_response) as urlopen:
            OpenAICompatibleClient(settings).complete_json(
                messages=[{"role": "user", "content": "hello"}]
            )

        sent_payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))

        self.assertEqual(
            sent_payload["chat_template_kwargs"],
            {"enable_thinking": False},
        )

    def test_llm_client_does_not_send_local_template_kwargs_to_provider(self):
        body = json.dumps(
            {"choices": [{"message": {"content": '{"didactic_text": "ok"}'}}]}
        ).encode("utf-8")
        fake_response = _FakeHTTPResponse(body)
        settings = self._llm_client_settings(
            max_output_tokens=7,
            postprocessing_mode="provider",
        )

        with patch("services.llm_client.request.urlopen", return_value=fake_response) as urlopen:
            OpenAICompatibleClient(settings).complete_json(
                messages=[{"role": "user", "content": "hello"}]
            )

        sent_payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))

        self.assertNotIn("chat_template_kwargs", sent_payload)

    def test_llm_client_rejects_excessive_response_body(self):
        fake_response = _FakeHTTPResponse(b"x" * 65537)
        settings = self._llm_client_settings(max_output_tokens=7)

        with patch("services.llm_client.request.urlopen", return_value=fake_response):
            with self.assertRaises(LLMClientUnavailableError):
                OpenAICompatibleClient(settings).complete_json(
                    messages=[{"role": "user", "content": "hello"}]
                )

    def test_benchmark_script_rejects_excessive_response_body(self):
        fake_response = _FakeHTTPResponse(b"x" * 65537)
        candidate = Candidate(
            name="test",
            base_url="https://example.com/v1",
            model="test-model",
            api_key="test-provider-key",
            api_key_source="test",
        )

        with patch(
            "scripts.benchmark_e03_models.urllib.request.urlopen",
            return_value=fake_response,
        ):
            with self.assertRaisesRegex(RuntimeError, "too much data"):
                post_chat_completion(
                    candidate,
                    messages=[{"role": "user", "content": "hello"}],
                    timeout=1,
                    temperature=0.2,
                    max_tokens=7,
                )

        self.assertEqual(fake_response.read_size, 65537)

    def test_benchmark_script_sends_json_response_format(self):
        body = json.dumps(
            {"choices": [{"message": {"content": '{"didactic_text": "ok"}'}}]}
        ).encode("utf-8")
        fake_response = _FakeHTTPResponse(body)
        candidate = Candidate(
            name="local-json-contract-model",
            base_url="http://127.0.0.1:8083/v1",
            model="local-json-contract-model.gguf",
            api_key="local",
            api_key_source="test",
        )

        with patch(
            "scripts.benchmark_e03_models.urllib.request.urlopen",
            return_value=fake_response,
        ) as urlopen:
            post_chat_completion(
                candidate,
                messages=[{"role": "user", "content": "hello"}],
                timeout=1,
                temperature=0.2,
                max_tokens=7,
            )

        sent_payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))

        self.assertEqual(sent_payload["response_format"], {"type": "json_object"})
        self.assertNotIn("chat_template_kwargs", sent_payload)

    def test_benchmark_script_disables_thinking_for_local_qwen(self):
        body = json.dumps(
            {"choices": [{"message": {"content": '{"didactic_text": "ok"}'}}]}
        ).encode("utf-8")
        fake_response = _FakeHTTPResponse(body)
        candidate = Candidate(
            name="qwen-local",
            base_url="http://localhost:8080/v1",
            model="Qwen3.6-35B-A3B-MTP-Q8.gguf",
            api_key="local",
            api_key_source="test",
        )

        with patch(
            "scripts.benchmark_e03_models.urllib.request.urlopen",
            return_value=fake_response,
        ) as urlopen:
            post_chat_completion(
                candidate,
                messages=[{"role": "user", "content": "hello"}],
                timeout=1,
                temperature=0.2,
                max_tokens=7,
            )

        sent_payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))

        self.assertEqual(
            sent_payload["chat_template_kwargs"],
            {"enable_thinking": False},
        )

    def test_zero_llm_max_output_tokens_falls_back_to_default(self):
        os.environ["MINDVOX_LLM_MAX_OUTPUT_TOKENS"] = "0"

        settings = get_settings()

        self.assertEqual(
            settings.llm_max_output_tokens,
            DEFAULT_LLM_MAX_OUTPUT_TOKENS,
        )

    def test_zero_llama_server_parallel_falls_back_to_default(self):
        os.environ["MINDVOX_LLAMA_SERVER_PARALLEL"] = "0"

        settings = get_settings()

        self.assertEqual(
            settings.llama_server_parallel,
            DEFAULT_LLAMA_SERVER_PARALLEL,
        )

    def test_llm_prompt_uses_e03_manual_without_concise_instruction(self):
        messages = _build_messages(
            raw_text="A aula explicou APIs e repetiu APIs com novo exemplo.",
            language="pt-BR",
            metadata=TranscriptionMetadata(course="UFG Pos"),
        )

        full_prompt = "\n".join(message["content"] for message in messages)

        self.assertIn("Mandatory operational manual", full_prompt)
        self.assertIn("semantic post-processing, not compression", full_prompt)
        self.assertIn("Preserve the class content as fully as possible", full_prompt)
        self.assertIn("not summarization", full_prompt)
        self.assertIn("Student contributions are class content", full_prompt)
        self.assertIn("Pre-audited transcript context", full_prompt)
        self.assertIn("Mindvox pre-audit context", full_prompt)
        self.assertIn("Minimum didactic_text character count", full_prompt)
        self.assertIn("named projects", full_prompt.lower())
        self.assertNotIn("concise", full_prompt.lower())

    def test_llm_prompt_lists_protected_semantic_anchors_for_long_transcript(self):
        messages = _build_messages(
            raw_text=self._long_raw_text(),
            language="pt-BR",
            metadata=TranscriptionMetadata(course="UFG Pos"),
        )

        full_prompt = "\n".join(message["content"] for message in messages)

        self.assertIn("Protected semantic coverage anchors", full_prompt)
        self.assertIn("- Positivo", full_prompt)
        self.assertIn("- NPS", full_prompt)
        self.assertIn("- Data Warehouse", full_prompt)
        self.assertIn("- Data Lake", full_prompt)
        self.assertIn("- Eduardo", full_prompt)

    def test_chunk_llm_prompt_does_not_apply_full_transcript_semantic_gate(self):
        raw_text = (
            "Então, o aluno perguntou sobre squads, papéis e entregas semanais. "
            * 420
        )

        messages = _build_messages(
            raw_text=raw_text,
            language="pt-BR",
            metadata=TranscriptionMetadata(course="UFG Pos"),
            semantic_coverage_mode="chunk",
        )

        full_prompt = "\n".join(message["content"] for message in messages)

        self.assertIn(
            "Minimum didactic_text character count for long-transcript semantic "
            "coverage: 0",
            full_prompt,
        )
        self.assertIn(
            "Minimum themes count for long-transcript semantic coverage: 1",
            full_prompt,
        )
        self.assertIn(
            "Protected semantic coverage anchors detected from raw transcript: none",
            full_prompt,
        )
        self.assertNotIn("- Então", full_prompt)

    def test_auto_postprocessing_mode_uses_contract_with_contract_transcription(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "auto"
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "contract"

        settings = get_settings()

        self.assertEqual(settings.transcription_mode, "contract")
        self.assertEqual(settings.postprocessing_mode, "contract")

    def test_auto_postprocessing_mode_uses_local_with_real_transcription(self):
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "auto"
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "real"
        os.environ.pop("MINDVOX_LLM_PROVIDER", None)
        os.environ.pop("MINDVOX_LLM_BASE_URL", None)
        os.environ.pop("MINDVOX_LLM_MODEL", None)

        settings = get_settings()

        self.assertEqual(settings.transcription_mode, "real")
        self.assertEqual(settings.postprocessing_mode, "local")
        self.assertEqual(settings.llm_provider, DEFAULT_LOCAL_LLM_PROVIDER)
        self.assertEqual(settings.llm_base_url, DEFAULT_LOCAL_LLM_BASE_URL)
        self.assertEqual(settings.llm_model, DEFAULT_LOCAL_LLM_MODEL)

    def _auth_headers(self):
        return {"Authorization": f"Bearer {VALID_TOKEN}"}

    def _resolve_openapi_schema(self, openapi: dict, schema: dict) -> dict:
        ref = schema.get("$ref")
        if ref is None and schema.get("allOf"):
            ref = schema["allOf"][0].get("$ref")
        if ref is None:
            return schema

        schema_name = ref.removeprefix("#/components/schemas/")
        return openapi["components"]["schemas"][schema_name]

    def _raw_text_payload(self):
        return {
            "input_type": "raw_text",
            "raw_text": self._sample_raw_text(),
            "course": "UFG Pos",
            "discipline": "API",
            "class_date": "2026-06-09",
            "class_title": "API First and FastAPI",
            "session_label": "S02",
            "language": "pt-BR",
            "processing_profile": "study_notes",
        }

    def _sample_raw_text(self):
        return (
            "A aula explicou API First, FastAPI, contratos OpenAPI e cuidados "
            "com autenticacao Bearer em endpoints."
        )

    def _long_raw_text(self):
        section = (
            "A aula discutiu API First, FastAPI e OpenAPI. O professor explicou "
            "o projeto Positivo sobre licitacoes publicas, com centenas de editais "
            "por dia, diarios oficiais, anexos nao estruturados e score de "
            "viabilidade. Eduardo discutiu vies de NPS no restaurante universitario "
            "e a diferenca entre estrela clicada sem atencao e comentario livre. "
            "Carlos relatou a dor de falta de APIs, Data Warehouse, Data Lake e "
            "consulta em banco de producao. Antonio comentou seu TCC de MBA sobre "
            "agencias de IA para orgaos publicos. Leo explicou invisible banking, "
            "microsservicos Java e legado mainframe Cobol. Mara usou a metafora de "
            "nao engordar o codigo. A aula tambem explicou AutoML, testes temporais "
            "e avaliacao de modelos."
        )
        return "\n".join(section for _ in range(35))

    def _valid_llm_payload(self):
        return {
            "didactic_text": "A aula organizou conceitos centrais sobre APIs.",
            "themes": [
                {
                    "order": 1,
                    "title": "API contracts",
                    "summary": "The class explained API contracts.",
                    "key_points": ["APIs need clear request and response contracts."],
                    "semantic_role": "fundamento",
                    "evidence": "API First",
                }
            ],
            "technical_terms": [
                {
                    "term": "API",
                    "normalized_from": ["api"],
                    "explanation": "Interface between software systems.",
                    "confidence": "high",
                    "evidence": "API",
                }
            ],
            "technology_mentions": [
                {
                    "name": "FastAPI",
                    "category": "framework",
                    "context": "Framework mentioned in class.",
                    "importance": "high",
                    "normalized_from": ["FastAPI"],
                    "confidence": "high",
                    "evidence": "FastAPI",
                }
            ],
            "processing_notes": [
                {
                    "type": "processing",
                    "message": "Synthetic provider payload for endpoint tests.",
                }
            ],
        }

    def _valid_long_llm_payload(self, raw_text: str):
        long_didactic_text = (
            "A aula preservou os conceitos de API First, FastAPI e OpenAPI, "
            "incluindo o projeto Positivo sobre licitacoes publicas, editais, "
            "diarios oficiais, anexos nao estruturados e score de viabilidade. "
            "Eduardo discutiu vies de NPS no restaurante universitario. Carlos "
            "relatou a dor de falta de APIs, Data Warehouse, Data Lake e consulta "
            "em banco de producao. Antonio comentou TCC de MBA sobre agencias de "
            "IA para orgaos publicos. Leo explicou invisible banking, "
            "microservicos Java e legado mainframe Cobol. Mara preservou a "
            "metafora de nao engordar o codigo. A aula tambem explicou AutoML, "
            "testes temporais e avaliacao de modelos. "
        )
        didactic_text = long_didactic_text * max(1, (int(len(raw_text) * 0.36) // len(long_didactic_text)) + 1)
        themes = [
            "Contratos de API",
            "Projeto Positivo e licitacoes",
            "Vies de NPS",
            "Data Warehouse e Data Lake",
            "AutoML e avaliacao temporal",
            "Invisible banking e legado Cobol",
            "Agencias de IA para orgaos publicos",
            "Metaforas de design de API",
            "Contribuicao de Eduardo",
            "Contribuicao de Carlos",
            "Contribuicao de Antonio",
            "Contribuicao de Leo",
            "Contribuicao de Mara",
        ]
        return {
            "didactic_text": didactic_text,
            "themes": [
                {
                    "order": index,
                    "title": title,
                    "summary": f"A aula preservou o tema: {title}.",
                    "key_points": [f"Ponto semantico sobre {title}."],
                    "semantic_role": "conteudo_preservado",
                    "evidence": title,
                }
                for index, title in enumerate(themes, start=1)
            ],
            "technical_terms": self._valid_llm_payload()["technical_terms"],
            "technology_mentions": self._valid_llm_payload()["technology_mentions"],
            "processing_notes": [
                {
                    "type": "processing",
                    "message": "Synthetic long provider payload for coverage tests.",
                }
            ],
        }

    def _anchor_preserving_text_for_ratio(self, raw_text: str, *, ratio: float) -> str:
        paragraph = (
            "A aula preservou API First, FastAPI, OpenAPI, Campus Party, projeto "
            "Positivo sobre licitacoes publicas, editais, diarios oficiais, score "
            "de viabilidade, NPS no restaurante universitario, Data Warehouse, "
            "Data Lake, banco de producao, ETL, AutoML, testes temporais, "
            "Invisible banking, microservicos Java, Mainframe, Cobol, TCC, MBA, "
            "orgaos publicos, agencias de IA e a metafora de nao engordar o codigo. "
        )
        minimum_chars = int(len(raw_text) * ratio)
        return paragraph * max(1, (minimum_chars // len(paragraph)) + 1)

    def _wav_file(self):
        return {
            "audio_file": (
                "class_s1.wav",
                self._minimal_wav_bytes(),
                "audio/wav",
            )
        }

    def _artifact_paths(self, transcription_id: str):
        output_dir = Path(self.output_directory.name)
        text_output_dir = Path(self.text_output_directory.name)
        json_matches = list(output_dir.glob(f"*{transcription_id}.json"))
        text_matches = list(text_output_dir.glob(f"*{transcription_id}.txt"))
        return (
            json_matches[0] if json_matches else output_dir / f"{transcription_id}.json",
            text_matches[0] if text_matches else text_output_dir / f"{transcription_id}.txt",
        )

    def _processed_artifact_path(self, processed_transcription_id: str):
        output_dir = Path(self.processed_output_directory.name)
        matches = list(output_dir.glob(f"*{processed_transcription_id}.json"))
        if matches:
            return matches[0]

        return (
            output_dir / f"{processed_transcription_id}.json"
        )

    def _processed_markdown_artifact_path(self, processed_transcription_id: str):
        output_dir = Path(self.processed_markdown_output_directory.name)
        matches = list(output_dir.glob(f"*{processed_transcription_id}.md"))
        if matches:
            return matches[0]

        return (
            output_dir / f"{processed_transcription_id}.md"
        )

    def _study_package_artifact_path(self, processed_transcription_id: str):
        output_dir = Path(self.study_package_output_directory.name)
        matches = list(output_dir.glob(f"*{processed_transcription_id}.json"))
        if matches:
            return matches[0]

        return output_dir / f"{processed_transcription_id}.json"

    def _queue_paths(self, transcription_id: str):
        queue_root = Path(self.processed_output_directory.name) / "queue"
        return (
            queue_root / "pending" / f"{transcription_id}.json",
            queue_root / "completed" / f"{transcription_id}.json",
        )

    def _queue_failed_path(self, transcription_id: str, error_type: str):
        queue_root = Path(self.processed_output_directory.name) / "queue"
        return queue_root / "failed" / f"{transcription_id}.{error_type}.json"

    def _minimal_wav_bytes(self):
        return (
            b"RIFF"
            + (36).to_bytes(4, "little")
            + b"WAVE"
            + b"fmt "
            + (16).to_bytes(4, "little")
            + (1).to_bytes(2, "little")
            + (1).to_bytes(2, "little")
            + (8000).to_bytes(4, "little")
            + (16000).to_bytes(4, "little")
            + (2).to_bytes(2, "little")
            + (16).to_bytes(2, "little")
            + b"data"
            + (0).to_bytes(4, "little")
        )

    def _llm_client_settings(
        self,
        *,
        max_output_tokens: int,
        postprocessing_mode: str = "provider",
    ):
        return self._settings(
            max_upload_mb=500,
            max_output_tokens=max_output_tokens,
            postprocessing_mode=postprocessing_mode,
        )

    def _settings(
        self,
        *,
        max_upload_mb: int = 500,
        max_output_tokens: int = 20000,
        postprocessing_mode: str = "provider",
    ):
        return Settings(
            api_token=VALID_TOKEN,
            runtime_profile="contract",
            max_upload_mb=max_upload_mb,
            public_deployment=False,
            docs_enabled=True,
            trusted_hosts=(),
            postprocessing_mode=postprocessing_mode,
            postprocessing_max_input_chars=150000,
            postprocessing_chunking_mode="off",
            postprocessing_chunking_min_chars=20000,
            postprocessing_chunk_target_tokens=5000,
            postprocessing_pre_audit_enabled=True,
            postprocessing_final_audit_enabled=True,
            llm_provider="test",
            llm_base_url="https://example.com/v1",
            llm_allowed_provider_hosts=(),
            llm_max_output_tokens=max_output_tokens,
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
            processed_transcription_output_dir=self.processed_output_directory.name,
            processed_transcription_markdown_output_dir=(
                self.processed_markdown_output_directory.name
            ),
            processed_transcription_rejected_output_dir=(
                str(Path(self.processed_output_directory.name) / "rejected")
            ),
            processed_transcription_rejected_markdown_output_dir=(
                str(Path(self.processed_markdown_output_directory.name) / "rejected")
            ),
            e03_study_package_output_dir=self.study_package_output_directory.name,
            e03_active_course_store=str(
                Path(self.course_store_directory.name) / "e03_courses.json"
            ),
            e03_obsidian_export_enabled=False,
            e03_obsidian_vaults_base_dir=None,
            e03_obsidian_vault_create_only=True,
            processed_transcription_queue_enabled=True,
            processed_transcription_queue_retry_seconds=60,
            processed_transcription_queue_max_attempts=3,
            transcription_mode="contract",
            transcription_model="test-transcription-model",
            transcription_output_dir=self.output_directory.name,
            transcription_text_output_dir=self.text_output_directory.name,
        )


class _FakeHTTPResponse:
    def __init__(self, body: bytes):
        self._body = body
        self.read_size: int | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, size: int = -1) -> bytes:
        self.read_size = size
        if size < 0:
            return self._body
        return self._body[:size]


class _FakeUpload:
    def __init__(self, chunks: list[bytes]):
        self.remaining_chunks = list(chunks)
        self.read_sizes: list[int] = []

    async def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        if not self.remaining_chunks:
            return b""
        return self.remaining_chunks.pop(0)


if __name__ == "__main__":
    unittest.main()
