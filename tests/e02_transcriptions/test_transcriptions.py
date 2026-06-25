import json
import os
import sys
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from main import app, create_app  # noqa: E402
from services.transcription_service import (  # noqa: E402
    TranscriptionServiceUnavailableError,
    _auto_transcription_backend,
    _language_for_mlx_whisper,
    _language_for_whisper,
    _prepare_mlx_whisper_model_layout,
    _response_language,
    transcribe_audio,
)
from services.transcription_artifacts import (  # noqa: E402
    _render_human_transcription_text,
)
from schemas.transcriptions import (  # noqa: E402
    TranscriptionEngine,
    TranscriptionMetadata,
    TranscriptionResponse,
    TranscriptionSegment,
)
from settings import DEFAULT_LOCAL_DEV_API_TOKEN, get_settings  # noqa: E402


VALID_TOKEN = "test-token"
TRANSCRIPTIONS_ENDPOINT = "/transcriptions/v1.0.0"


class TranscriptionsEndpointTest(unittest.TestCase):
    def setUp(self):
        self.previous_env = {
            "MINDVOX_API_TOKEN": os.environ.get("MINDVOX_API_TOKEN"),
            "MINDVOX_MAX_UPLOAD_MB": os.environ.get("MINDVOX_MAX_UPLOAD_MB"),
            "MINDVOX_PUBLIC_DEPLOYMENT": os.environ.get("MINDVOX_PUBLIC_DEPLOYMENT"),
            "MINDVOX_ENABLE_DOCS": os.environ.get("MINDVOX_ENABLE_DOCS"),
            "MINDVOX_TRUSTED_HOSTS": os.environ.get("MINDVOX_TRUSTED_HOSTS"),
            "MINDVOX_RUNTIME_PROFILE": os.environ.get("MINDVOX_RUNTIME_PROFILE"),
            "MINDVOX_TRANSCRIPTION_MODE": os.environ.get("MINDVOX_TRANSCRIPTION_MODE"),
            "MINDVOX_TRANSCRIPTION_BACKEND": os.environ.get(
                "MINDVOX_TRANSCRIPTION_BACKEND"
            ),
            "MINDVOX_TRANSCRIPTION_MODEL": os.environ.get(
                "MINDVOX_TRANSCRIPTION_MODEL"
            ),
            "MINDVOX_TRANSCRIPTION_FALLBACK_MODEL": os.environ.get(
                "MINDVOX_TRANSCRIPTION_FALLBACK_MODEL"
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
        os.environ["MINDVOX_API_TOKEN"] = VALID_TOKEN
        os.environ["MINDVOX_MAX_UPLOAD_MB"] = "500"
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "false"
        os.environ["MINDVOX_ENABLE_DOCS"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = ""
        os.environ["MINDVOX_RUNTIME_PROFILE"] = ""
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "contract"
        os.environ["MINDVOX_TRANSCRIPTION_BACKEND"] = "auto"
        os.environ["MINDVOX_TRANSCRIPTION_MODEL"] = (
            "mlx-community/whisper-large-v3-turbo-fp16"
        )
        os.environ["MINDVOX_TRANSCRIPTION_FALLBACK_MODEL"] = "turbo"
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

    def test_post_transcriptions_returns_structured_contract_response(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
            data={
                "course": "UFG Pos",
                "discipline": "API",
                "class_date": "2026-06-08",
                "class_title": "Aula de APIs",
                "session_label": "s1",
            },
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(payload),
            {
                "transcription_id",
                "text",
                "language",
                "duration_seconds",
                "segments",
                "metadata",
                "engine",
                "artifact_locations",
            },
        )
        self.assertRegex(payload["transcription_id"], r"^tr_\d{8}T\d{6}Z_[0-9a-f]{8}$")
        self.assertEqual(payload["language"], "pt-BR")
        self.assertEqual(payload["segments"], [])
        self.assertEqual(payload["metadata"]["discipline"], "API")
        self.assertEqual(payload["metadata"]["session_label"], "s1")
        self.assertEqual(payload["engine"]["name"], "contract-stub")
        self.assertIn(payload["engine"]["version"], {"contract-mode", "unknown"})

    def test_post_transcriptions_saves_raw_transcription_artifacts(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
            data={
                "discipline": "API",
                "class_date": "2026-06-08",
                "class_title": "Aula de APIs",
                "session_label": "s1",
            },
        )

        payload = response.json()
        json_path, text_path = self._artifact_paths(payload)
        artifact_payload = json.loads(json_path.read_text(encoding="utf-8"))
        human_filename = text_path.name
        technical_filename = json_path.name

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_path.exists())
        self.assertTrue(text_path.exists())
        self.assertEqual(text_path.read_text(encoding="utf-8"), payload["text"])
        self.assertIn("2026-06-08", human_filename)
        self.assertIn("aula-de-apis", human_filename)
        self.assertIn("s1", human_filename)
        self.assertTrue(human_filename.endswith(f"{payload['transcription_id']}.txt"))
        self.assertTrue(technical_filename.endswith(f"{payload['transcription_id']}.json"))
        self.assertEqual(payload["artifact_locations"]["human_text_path"].split("/")[-1], human_filename)
        self.assertEqual(payload["artifact_locations"]["technical_json_path"].split("/")[-1], technical_filename)
        self.assertEqual(artifact_payload["transcription_id"], payload["transcription_id"])
        self.assertEqual(artifact_payload["text"], payload["text"])
        self.assertEqual(artifact_payload["metadata"]["discipline"], "API")
        self.assertEqual(artifact_payload["metadata"]["class_date"], "2026-06-08")
        self.assertEqual(artifact_payload["metadata"]["class_title"], "Aula de APIs")
        self.assertEqual(
            artifact_payload["artifact_locations"],
            payload["artifact_locations"],
        )

    def test_human_transcription_text_is_paragraphed_when_segments_exist(self):
        response = TranscriptionResponse(
            transcription_id="tr_20260614T120000Z_1234abcd",
            text=(
                "Primeiro trecho da aula. Segundo trecho ainda no mesmo assunto. "
                "Depois de uma pausa, novo topico da aula."
            ),
            language="pt-BR",
            duration_seconds=20.0,
            segments=[
                TranscriptionSegment(
                    start_seconds=0.0,
                    end_seconds=3.0,
                    text=" Primeiro trecho da aula.",
                ),
                TranscriptionSegment(
                    start_seconds=3.4,
                    end_seconds=5.0,
                    text=" Segundo trecho ainda no mesmo assunto.",
                ),
                TranscriptionSegment(
                    start_seconds=12.0,
                    end_seconds=20.0,
                    text=" Depois de uma pausa, novo topico da aula.",
                ),
            ],
            metadata=TranscriptionMetadata(),
            engine=TranscriptionEngine(
                name="test",
                model="test-model",
                version="test",
            ),
        )

        rendered = _render_human_transcription_text(response)

        self.assertEqual(
            rendered,
            (
                "Primeiro trecho da aula. Segundo trecho ainda no mesmo assunto."
                "\n\n"
                "Depois de uma pausa, novo topico da aula."
            ),
        )

    def test_post_transcriptions_uses_default_language_when_absent(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["language"], "pt-BR")

    def test_post_transcriptions_treats_optional_date_string_placeholder_as_empty(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
            data={"class_date": "string"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["metadata"]["class_date"])

    def test_transcription_id_is_opaque(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "student_hidden_class_s1.wav",
                    self._minimal_wav_bytes(),
                    "audio/wav",
                )
            },
        )

        payload = response.json()
        transcription_id = payload["transcription_id"]

        self.assertEqual(response.status_code, 200)
        self.assertRegex(transcription_id, r"^tr_\d{8}T\d{6}Z_[0-9a-f]{8}$")
        self.assertNotIn("student", transcription_id.lower())
        self.assertNotIn("hidden", transcription_id.lower())
        self.assertNotIn("class_s1", transcription_id.lower())
        self.assertNotIn(VALID_TOKEN, transcription_id)
        self.assertNotIn("/", transcription_id)

    def test_transcription_response_does_not_expose_sensitive_terms(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
        )

        serialized_payload = json.dumps(response.json()).lower()
        forbidden_terms = [
            VALID_TOKEN,
            "authorization",
            "secret",
            "password",
            ".env",
            "/users/",
            "tmp",
        ]

        self.assertEqual(response.status_code, 200)
        for term in forbidden_terms:
            self.assertNotIn(term.lower(), serialized_payload)

    def test_transcription_error_responses_do_not_expose_sensitive_terms(self):
        responses = [
            self.client.post(
                TRANSCRIPTIONS_ENDPOINT,
                headers={"Authorization": "Bearer wrong-token"},
                files={
                    "audio_file": (
                        "secret.env.wav",
                        self._minimal_wav_bytes(),
                        "audio/wav",
                    )
                },
            ),
            self.client.post(
                TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                files={
                    "audio_file": (
                        "secret.env",
                        b"not audio",
                        "text/plain",
                    )
                },
            ),
            self.client.post(
                TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                files=self._wav_file(),
                data={"session_label": "s1/../../secret"},
            ),
        ]
        forbidden_terms = [
            VALID_TOKEN,
            "wrong-token",
            "secret",
            ".env",
            "/users/",
            "authorization",
        ]

        for response in responses:
            with self.subTest(status_code=response.status_code):
                serialized_payload = json.dumps(response.json()).lower()

                self.assertIn(response.status_code, {400, 401, 422})
                for term in forbidden_terms:
                    self.assertNotIn(term.lower(), serialized_payload)

    def test_transcription_logs_do_not_expose_sensitive_terms(self):
        with self.assertLogs("mindvox.transcriptions", level="INFO") as logs:
            response = self.client.post(
                TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                files={
                    "audio_file": (
                        "student_hidden_class_s1.wav",
                        self._minimal_wav_bytes(),
                        "audio/wav",
                    )
                },
            )

        serialized_logs = "\n".join(logs.output).lower()
        forbidden_terms = [
            VALID_TOKEN,
            "authorization",
            "contract-mode transcription",
            "student",
            "hidden",
            ".env",
            "/users/",
            "riff",
            "wave",
        ]

        self.assertEqual(response.status_code, 200)
        self.assertIn("transcription_auth_succeeded", serialized_logs)
        self.assertIn("transcription_request_started", serialized_logs)
        self.assertIn("size_bytes=", serialized_logs)
        self.assertIn("content_type=audio/wav", serialized_logs)
        self.assertIn("transcription_request_succeeded", serialized_logs)
        self.assertIn("duration_ms=", serialized_logs)
        for term in forbidden_terms:
            self.assertNotIn(term.lower(), serialized_logs)

    def test_transcription_response_redacts_sensitive_model_configuration(self):
        os.environ["MINDVOX_TRANSCRIPTION_MODEL"] = (
            "~/redacted-local-model"
        )

        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["engine"]["model"], "configured-model")
        self.assertNotIn("/Users/", json.dumps(payload))
        self.assertNotIn("redacted", json.dumps(payload).lower())

    def test_real_engine_language_uses_base_language_without_changing_contract_response(self):
        self.assertEqual(_language_for_mlx_whisper("pt-BR"), "pt")
        self.assertEqual(_language_for_whisper("pt-BR"), "pt")
        self.assertEqual(_language_for_mlx_whisper("en-US"), "en")
        self.assertEqual(
            _response_language(engine_language="pt", requested_language="pt-BR"),
            "pt-BR",
        )

    def test_auto_transcription_backend_prefers_mlx_on_apple_silicon(self):
        with patch("services.transcription_service.platform.system", return_value="Darwin"):
            with patch("services.transcription_service.platform.machine", return_value="arm64"):
                self.assertEqual(_auto_transcription_backend(), "mlx-whisper")

    def test_empty_transcription_backend_configuration_falls_back_to_auto(self):
        os.environ["MINDVOX_TRANSCRIPTION_BACKEND"] = " "
        os.environ["MINDVOX_TRANSCRIPTION_FALLBACK_MODEL"] = " "

        settings = get_settings()

        self.assertEqual(settings.transcription_backend, "auto")
        self.assertEqual(settings.transcription_fallback_model, "turbo")

    def test_auto_transcription_backend_uses_openai_whisper_on_windows_and_linux(self):
        platforms = [
            ("Linux", "x86_64"),
            ("Windows", "AMD64"),
        ]

        for system, machine in platforms:
            with self.subTest(system=system, machine=machine):
                with patch(
                    "services.transcription_service.platform.system",
                    return_value=system,
                ):
                    with patch(
                        "services.transcription_service.platform.machine",
                        return_value=machine,
                    ):
                        self.assertEqual(
                            _auto_transcription_backend(),
                            "openai-whisper",
                        )

    def test_auto_transcription_backend_rejects_unsupported_platforms(self):
        with patch("services.transcription_service.platform.system", return_value="Darwin"):
            with patch("services.transcription_service.platform.machine", return_value="x86_64"):
                with self.assertRaises(TranscriptionServiceUnavailableError):
                    _auto_transcription_backend()

    def test_openai_whisper_backend_returns_structured_response(self):
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "real"
        os.environ["MINDVOX_TRANSCRIPTION_BACKEND"] = "openai-whisper"
        os.environ["MINDVOX_TRANSCRIPTION_FALLBACK_MODEL"] = "tiny"
        calls: dict[str, str] = {}

        class FakeWhisperModel:
            def transcribe(self, path, *, language):
                audio_path = Path(path)
                calls["path"] = path
                calls["path_exists_during_transcribe"] = str(audio_path.exists())
                calls["file_header"] = audio_path.read_bytes()[:4].decode("ascii")
                calls["path_suffix"] = audio_path.suffix
                calls["language"] = language
                return {
                    "text": "Texto transcrito pelo backend cross-platform.",
                    "language": language,
                    "segments": [
                        {
                            "start": 0.0,
                            "end": 1.5,
                            "text": "Texto transcrito.",
                        }
                    ],
                }

        def load_model(model_name):
            calls["model_name"] = model_name
            return FakeWhisperModel()

        fake_whisper = SimpleNamespace(load_model=load_model)

        with patch.dict(sys.modules, {"whisper": fake_whisper}):
            response = transcribe_audio(
                audio_bytes=self._minimal_wav_bytes(),
                filename="class_s1.wav",
                language="pt-BR",
                metadata=TranscriptionMetadata(discipline="API"),
                settings=get_settings(),
            )

        self.assertEqual(response.text, "Texto transcrito pelo backend cross-platform.")
        self.assertEqual(response.language, "pt-BR")
        self.assertEqual(response.duration_seconds, 1.5)
        self.assertEqual(response.segments[0].speaker_label, None)
        self.assertEqual(response.metadata.discipline, "API")
        self.assertEqual(response.engine.name, "openai-whisper")
        self.assertEqual(response.engine.model, "tiny")
        self.assertEqual(response.engine.version, "unknown")
        self.assertEqual(calls["model_name"], "tiny")
        self.assertEqual(calls["language"], "pt")
        self.assertEqual(calls["path_suffix"], ".wav")
        self.assertEqual(calls["path_exists_during_transcribe"], "True")
        self.assertEqual(calls["file_header"], "RIFF")
        self.assertFalse(Path(calls["path"]).exists())

    def test_real_engine_model_layout_accepts_model_safetensors(self):
        with TemporaryDirectory() as directory:
            model_path = Path(directory)
            (model_path / "config.json").write_text("{}", encoding="utf-8")
            (model_path / "model.safetensors").write_bytes(b"fake model")

            with TemporaryDirectory() as cache_directory:
                with patch(
                    "services.transcription_service.MODEL_CACHE_DIR",
                    Path(cache_directory),
                ):
                    prepared_path = _prepare_mlx_whisper_model_layout(model_path)

                    self.assertNotEqual(prepared_path, model_path)
                    self.assertTrue((prepared_path / "weights.safetensors").exists())
                    self.assertTrue((prepared_path / "model.safetensors").exists())

    def test_post_transcriptions_without_token_returns_401(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_transcription_auth_failure_logs_status_error_and_duration(self):
        with self.assertLogs("mindvox.transcriptions", level="WARNING") as logs:
            response = self.client.post(
                TRANSCRIPTIONS_ENDPOINT,
                files=self._wav_file(),
            )

        serialized_logs = "\n".join(logs.output).lower()

        self.assertEqual(response.status_code, 401)
        self.assertIn("transcription_auth_failed", serialized_logs)
        self.assertIn("status_code=401", serialized_logs)
        self.assertIn("error_code=missing_credentials", serialized_logs)
        self.assertIn("phase=auth", serialized_logs)
        self.assertIn("duration_ms=", serialized_logs)
        for term in [VALID_TOKEN, "authorization", "bearer"]:
            self.assertNotIn(term.lower(), serialized_logs)

    def test_post_transcriptions_without_token_and_without_file_returns_401(self):
        response = self.client.post(TRANSCRIPTIONS_ENDPOINT)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_post_transcriptions_with_invalid_token_returns_401(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": "Bearer wrong-token"},
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_post_transcriptions_uses_dev_token_when_local_token_is_empty(self):
        os.environ["MINDVOX_API_TOKEN"] = ""

        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": f"Bearer {DEFAULT_LOCAL_DEV_API_TOKEN}"},
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 200)

    def test_post_transcriptions_rejects_placeholder_api_token_configuration(self):
        os.environ["MINDVOX_API_TOKEN"] = "replace-with-local-token"

        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": "Bearer replace-with-local-token"},
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Transcription service is unavailable."},
        )

    def test_post_transcriptions_rejects_dev_token_in_public_deployment(self):
        os.environ["MINDVOX_API_TOKEN"] = "dev-token"
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"

        secure_client = TestClient(app, base_url="https://api.example.com")

        response = secure_client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers={"Authorization": "Bearer dev-token"},
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Transcription service is unavailable."},
        )

    def test_post_transcriptions_requires_https_in_public_deployment(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"

        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "HTTPS is required for public deployment."})

    def test_post_transcriptions_accepts_https_in_public_deployment(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"
        secure_client = TestClient(app, base_url="https://api.example.com")

        response = secure_client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 200)

    def test_public_deployment_rejects_wildcard_trusted_hosts(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "*"

        with self.assertRaisesRegex(RuntimeError, "cannot contain '\\*'"):
            create_app()

    def test_post_transcriptions_with_malformed_authorization_header_returns_401(self):
        malformed_headers = [
            "Token test-token",
            "Bearer",
            "Bearer ",
        ]

        for authorization in malformed_headers:
            with self.subTest(authorization=authorization):
                response = self.client.post(
                    TRANSCRIPTIONS_ENDPOINT,
                    headers={"Authorization": authorization},
                    files=self._wav_file(),
                )

                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_post_transcriptions_without_file_returns_422(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            data={"discipline": "API"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertTrue(
            any(
                error.get("loc") == ["body", "audio_file"]
                for error in response.json()["detail"]
            )
        )

    def test_post_transcriptions_rejects_empty_filename(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "   ",
                    self._minimal_wav_bytes(),
                    "audio/wav",
                )
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "Audio file must have a filename."})

    def test_post_transcriptions_rejects_unsupported_file_type(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "notes.txt",
                    b"not audio",
                    "text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Unsupported audio file type. Supported formats: .wav, .m4a."},
        )

    def test_post_transcriptions_rejects_incompatible_content_type(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "class_s1.wav",
                    self._minimal_wav_bytes(),
                    "audio/mp4",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Unsupported audio content type."})

    def test_post_transcriptions_accepts_m4a_extension_and_content_type(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._m4a_file(),
        )

        self.assertEqual(response.status_code, 200)

    def test_post_transcriptions_rejects_corrupted_audio(self):
        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files={
                "audio_file": (
                    "corrupted.wav",
                    b"this is not a wav container",
                    "audio/wav",
                )
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "Audio file cannot be decoded."})

    def test_post_transcriptions_rejects_file_above_configured_limit(self):
        os.environ["MINDVOX_MAX_UPLOAD_MB"] = "0"

        response = self.client.post(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
            files=self._wav_file(),
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.json(),
            {"detail": "Audio file exceeds the maximum allowed size."},
        )

    def test_post_transcriptions_rejects_invalid_metadata(self):
        invalid_payloads = [
            (
                {"class_date": "08/06/2026"},
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
                response = self.client.post(
                    TRANSCRIPTIONS_ENDPOINT,
                    headers=self._auth_headers(),
                    files=self._wav_file(),
                    data=data,
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json(), {"detail": expected_detail})

    def test_post_transcriptions_rejects_oversized_metadata_text(self):
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
                response = self.client.post(
                    TRANSCRIPTIONS_ENDPOINT,
                    headers=self._auth_headers(),
                    files=self._wav_file(),
                    data=data,
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json(), {"detail": expected_detail})

    def test_get_transcriptions_is_not_allowed(self):
        response = self.client.get(
            TRANSCRIPTIONS_ENDPOINT,
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {"detail": "Method Not Allowed"})

    def test_transcription_engine_unavailable_returns_503(self):
        with patch(
            "routers.transcriptions.transcribe_audio",
            side_effect=TranscriptionServiceUnavailableError(),
        ):
            response = self.client.post(
                TRANSCRIPTIONS_ENDPOINT,
                headers=self._auth_headers(),
                files=self._wav_file(),
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Transcription service is unavailable."},
        )

    def test_transcription_unexpected_error_returns_500_without_sensitive_detail(self):
        sensitive_error = RuntimeError(
            f"token={VALID_TOKEN} redacted-local-audio-marker"
        )

        with self.assertLogs("mindvox.transcriptions", level="ERROR") as logs:
            with patch(
                "routers.transcriptions.transcribe_audio",
                side_effect=sensitive_error,
            ):
                response = self.client.post(
                    TRANSCRIPTIONS_ENDPOINT,
                    headers=self._auth_headers(),
                    files=self._wav_file(),
                )

        serialized_response = json.dumps(response.json()).lower()
        serialized_logs = "\n".join(logs.output).lower()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Internal transcription error."})
        self.assertIn("error_code=internal_error", serialized_logs)
        self.assertIn("status_code=500", serialized_logs)
        self.assertIn("duration_ms=", serialized_logs)
        for term in [VALID_TOKEN, "/users/", "redacted-local-audio-marker"]:
            self.assertNotIn(term.lower(), serialized_response)
            self.assertNotIn(term.lower(), serialized_logs)

    def test_openapi_documents_transcriptions_endpoint_contract(self):
        openapi_client = TestClient(create_app())
        response = openapi_client.get("/openapi.json")
        openapi = response.json()
        operation = openapi["paths"][TRANSCRIPTIONS_ENDPOINT]["post"]

        self.assertEqual(response.status_code, 200)
        self.assertIn("Active startup profile", openapi["info"]["description"])
        self.assertIn("`contract`", openapi["info"]["description"])
        self.assertEqual(operation["summary"], "Transcribe audio file")
        self.assertIn("recorded audio file", operation["description"])
        self.assertIn("streaming", operation["description"])
        self.assertIn("TTS", operation["description"])
        self.assertIn("speech-to-speech", operation["description"])
        self.assertIn("requestBody", operation)
        self.assertIn("multipart/form-data", operation["requestBody"]["content"])
        schema_ref = operation["requestBody"]["content"]["multipart/form-data"]["schema"][
            "$ref"
        ]
        schema_name = schema_ref.removeprefix("#/components/schemas/")
        request_schema = openapi["components"]["schemas"][schema_name]
        request_properties = request_schema["properties"]
        self.assertIn("audio_file", request_schema["required"])
        self.assertIn(".wav", request_properties["audio_file"]["description"])
        self.assertIn(".m4a", request_properties["audio_file"]["description"])
        self.assertIn(
            "class-2026-06-09.wav", request_properties["audio_file"]["description"]
        )
        self.assertIn(
            "organize the transcription",
            request_properties["course"]["description"],
        )
        self.assertIn(
            "Federal University of Goias", request_properties["course"]["description"]
        )
        self.assertIn("discipline", request_properties["discipline"]["description"])
        self.assertIn(
            "API Engineering for AI",
            request_properties["discipline"]["description"],
        )
        self.assertIn("YYYY-MM-DD", request_properties["class_date"]["description"])
        self.assertIn("Leave this empty", request_properties["class_date"]["description"])
        self.assertIn("2026-06-09", request_properties["class_date"]["description"])
        for optional_field in [
            "course",
            "discipline",
            "class_date",
            "class_title",
            "session_label",
        ]:
            self.assertEqual(request_properties[optional_field]["default"], "")
        self.assertIn("title", request_properties["class_title"]["description"])
        self.assertIn(
            "Introduction to API contracts",
            request_properties["class_title"]["description"],
        )
        self.assertIn(
            "short identifier",
            request_properties["session_label"]["description"],
        )
        self.assertIn("class-01", request_properties["session_label"]["description"])
        self.assertIn(
            "Brazilian Portuguese",
            request_properties["language"]["description"],
        )
        self.assertIn("Example: pt-BR", request_properties["language"]["description"])
        self.assertEqual(request_properties["language"]["default"], "pt-BR")
        self.assertIn("security", operation)
        self.assertEqual(operation["responses"]["200"]["description"], "Successful Response")
        for status_code in ["400", "401", "403", "413", "422", "500", "503"]:
            self.assertIn(status_code, operation["responses"])

        security_schemes = openapi["components"]["securitySchemes"]
        self.assertIn("HTTPBearer", security_schemes)
        self.assertEqual(security_schemes["HTTPBearer"]["scheme"], "bearer")

    def _auth_headers(self):
        return {"Authorization": f"Bearer {VALID_TOKEN}"}

    def _wav_file(self):
        return {
            "audio_file": (
                "class_s1.wav",
                self._minimal_wav_bytes(),
                "audio/wav",
            )
        }

    def _m4a_file(self):
        return {
            "audio_file": (
                "class_s1.m4a",
                self._minimal_m4a_bytes(),
                "audio/mp4",
            )
        }

    def _artifact_paths(self, payload: dict):
        output_dir = Path(self.output_directory.name)
        text_output_dir = Path(self.text_output_directory.name)
        json_name = payload["artifact_locations"]["technical_json_path"].split("/")[-1]
        text_name = payload["artifact_locations"]["human_text_path"].split("/")[-1]
        return (
            output_dir / json_name,
            text_output_dir / text_name,
        )

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

    def _minimal_m4a_bytes(self):
        return b"\x00\x00\x00\x18ftypM4A " + (0).to_bytes(8, "big")


if __name__ == "__main__":
    unittest.main()
