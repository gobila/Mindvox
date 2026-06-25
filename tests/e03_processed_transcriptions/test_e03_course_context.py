import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from services.e03_course_context import (  # noqa: E402
    CourseContextError,
    active_course,
    load_course_context,
    set_active_course,
    upsert_course,
)
from settings import Settings  # noqa: E402


class E03CourseContextTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upsert_course_persists_active_course(self):
        settings = self._settings()

        state = upsert_course(
            course_name="UFG Pos 2",
            institution="UFG",
            settings=settings,
        )
        loaded = load_course_context(settings=settings)

        self.assertEqual(state.active_course_id, "ufg_pos_2")
        self.assertEqual(loaded.active_course_id, "ufg_pos_2")
        self.assertEqual(len(loaded.courses), 1)
        self.assertEqual(loaded.courses[0].course_name, "UFG Pos 2")
        self.assertEqual(loaded.courses[0].institution, "UFG")
        self.assertEqual(active_course(settings=settings).course_id, "ufg_pos_2")

    def test_upsert_course_keeps_sorted_course_list_for_selector(self):
        settings = self._settings()

        upsert_course(course_name="PUC Mestrado Tx", settings=settings)
        upsert_course(course_name="UFG Pos 2", settings=settings)

        loaded = load_course_context(settings=settings)

        self.assertEqual(
            [course.course_id for course in loaded.courses],
            ["puc_mestrado_tx", "ufg_pos_2"],
        )
        self.assertEqual(loaded.active_course_id, "ufg_pos_2")

    def test_set_active_course_requires_known_course(self):
        settings = self._settings()
        upsert_course(course_name="UFG Pos 2", settings=settings)

        with self.assertRaises(CourseContextError):
            set_active_course(course_id="curso_inexistente", settings=settings)

    def test_set_active_course_changes_persistent_default(self):
        settings = self._settings()
        upsert_course(course_name="UFG Pos 2", settings=settings)
        upsert_course(course_name="PUC Mestrado Tx", settings=settings)

        state = set_active_course(course_id="ufg_pos_2", settings=settings)

        self.assertEqual(state.active_course_id, "ufg_pos_2")
        self.assertEqual(active_course(settings=settings).course_name, "UFG Pos 2")

    def _settings(self):
        return Settings(
            api_token="test-token",
            runtime_profile="dev",
            max_upload_mb=500,
            public_deployment=False,
            docs_enabled=True,
            trusted_hosts=(),
            postprocessing_mode="contract",
            postprocessing_max_input_chars=150000,
            postprocessing_chunking_mode="off",
            postprocessing_chunking_min_chars=20000,
            postprocessing_chunk_target_tokens=5000,
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
            transcription_mode="contract",
            transcription_backend="auto",
            transcription_model="test-transcription-model",
            transcription_fallback_model="turbo",
            transcription_output_dir=str(self.root / "transcriptions"),
            transcription_text_output_dir=str(self.root / "human" / "transcriptions"),
        )


if __name__ == "__main__":
    unittest.main()
