import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from services.local_llm_runtime import (  # noqa: E402
    LocalLLMRuntime,
    LocalLLMStartupError,
)
from settings import Settings  # noqa: E402


class LocalLLMRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.server_path = self.root / "llama-server"
        self.server_path.write_text("#!/bin/sh\n", encoding="utf-8")
        self.server_path.chmod(0o755)
        self.model_path = self.root / "qwen.gguf"
        self.model_path.write_bytes(b"gguf")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_contract_mode_does_not_start_llama_server(self):
        settings = self._settings(postprocessing_mode="contract")

        with patch("services.local_llm_runtime.subprocess.Popen") as popen:
            LocalLLMRuntime(settings).start_if_required()

        popen.assert_not_called()

    def test_local_autostart_disabled_does_not_start_llama_server(self):
        settings = self._settings(
            postprocessing_mode="local",
            local_llm_autostart=False,
        )

        with patch("services.local_llm_runtime.subprocess.Popen") as popen:
            LocalLLMRuntime(settings).start_if_required()

        popen.assert_not_called()

    def test_existing_openai_compatible_server_is_reused(self):
        settings = self._settings(postprocessing_mode="local")

        with patch(
            "services.local_llm_runtime._is_openai_compatible_server_ready",
            return_value=True,
        ):
            with patch("services.local_llm_runtime.subprocess.Popen") as popen:
                LocalLLMRuntime(settings).start_if_required()

        popen.assert_not_called()

    def test_local_autostart_starts_llama_server_until_ready(self):
        settings = self._settings(postprocessing_mode="local")
        fake_process = _FakeProcess()

        with patch(
            "services.local_llm_runtime._is_openai_compatible_server_ready",
            side_effect=[False, True],
        ):
            with patch(
                "services.local_llm_runtime.subprocess.Popen",
                return_value=fake_process,
            ) as popen:
                LocalLLMRuntime(settings).start_if_required()

        command = popen.call_args.args[0]

        self.assertEqual(command[0], str(self.server_path))
        self.assertIn("--model", command)
        self.assertIn(str(self.model_path), command)
        self.assertIn("--alias", command)
        self.assertIn("qwen35a3b-q8", command)
        self.assertIn("--host", command)
        self.assertIn("127.0.0.1", command)
        self.assertIn("--port", command)
        self.assertIn("8080", command)
        self.assertIn("--ctx-size", command)
        self.assertIn("65536", command)
        self.assertIn("--n-gpu-layers", command)
        self.assertIn("99", command)
        self.assertIn("--parallel", command)
        self.assertIn("1", command)

    def test_missing_llama_server_path_fails_with_clear_message(self):
        settings = self._settings(
            postprocessing_mode="local",
            llama_server_path=str(self.root / "missing-server"),
        )

        with patch(
            "services.local_llm_runtime._is_openai_compatible_server_ready",
            return_value=False,
        ):
            with self.assertRaisesRegex(
                LocalLLMStartupError,
                "MINDVOX_LLAMA_SERVER_PATH",
            ):
                LocalLLMRuntime(settings).start_if_required()

    def test_missing_model_path_fails_with_clear_message(self):
        settings = self._settings(
            postprocessing_mode="local",
            local_llm_model_path=str(self.root / "missing-model.gguf"),
        )

        with patch(
            "services.local_llm_runtime._is_openai_compatible_server_ready",
            return_value=False,
        ):
            with self.assertRaisesRegex(
                LocalLLMStartupError,
                "MINDVOX_LOCAL_LLM_MODEL_PATH",
            ):
                LocalLLMRuntime(settings).start_if_required()

    def test_startup_timeout_terminates_started_process(self):
        settings = self._settings(
            postprocessing_mode="local",
            llama_server_startup_timeout_seconds=1,
        )
        fake_process = _FakeProcess()

        with patch(
            "services.local_llm_runtime._is_openai_compatible_server_ready",
            return_value=False,
        ):
            with patch(
                "services.local_llm_runtime.subprocess.Popen",
                return_value=fake_process,
            ):
                with patch(
                    "services.local_llm_runtime.time.monotonic",
                    side_effect=[0, 0, 2],
                ):
                    with patch("services.local_llm_runtime.time.sleep"):
                        with self.assertRaisesRegex(
                            LocalLLMStartupError,
                            "did not become ready",
                        ):
                            LocalLLMRuntime(settings).start_if_required()

        self.assertTrue(fake_process.terminated)

    def _settings(
        self,
        *,
        postprocessing_mode: str,
        local_llm_autostart: bool = True,
        llama_server_path: str | None = None,
        local_llm_model_path: str | None = None,
        llama_server_startup_timeout_seconds: int = 240,
    ) -> Settings:
        return Settings(
            api_token="test-token",
            runtime_profile="dev",
            max_upload_mb=500,
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
            llm_provider="local",
            llm_base_url="http://127.0.0.1:8080/v1",
            llm_allowed_provider_hosts=(),
            llm_max_output_tokens=20000,
            llm_model="qwen35a3b-q8",
            llm_api_key=None,
            llm_timeout_seconds=1200,
            local_llm_autostart=local_llm_autostart,
            llama_server_path=llama_server_path or str(self.server_path),
            local_llm_model_path=local_llm_model_path or str(self.model_path),
            llama_server_ctx_size=65536,
            llama_server_gpu_layers=99,
            llama_server_parallel=1,
            llama_server_startup_timeout_seconds=(
                llama_server_startup_timeout_seconds
            ),
            processed_transcription_output_dir=str(self.root / "processed"),
            processed_transcription_markdown_output_dir=str(
                self.root / "human" / "processed"
            ),
            processed_transcription_rejected_output_dir=str(
                self.root / "processed" / "rejected"
            ),
            processed_transcription_rejected_markdown_output_dir=str(
                self.root / "human" / "processed" / "rejected"
            ),
            e03_study_package_output_dir=str(self.root / "study_packages"),
            e03_active_course_store=str(self.root / "config" / "e03_courses.json"),
            e03_obsidian_export_enabled=False,
            e03_obsidian_vaults_base_dir=None,
            e03_obsidian_vault_create_only=True,
            processed_transcription_queue_enabled=True,
            processed_transcription_queue_retry_seconds=60,
            processed_transcription_queue_max_attempts=3,
            transcription_mode="real",
            transcription_model="test-transcription-model",
            transcription_output_dir=str(self.root / "transcriptions"),
            transcription_text_output_dir=str(self.root / "human" / "transcriptions"),
        )


class _FakeProcess:
    def __init__(self):
        self.terminated = False
        self.killed = False

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


if __name__ == "__main__":
    unittest.main()
