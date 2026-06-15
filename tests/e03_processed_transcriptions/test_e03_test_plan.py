from pathlib import Path
import unittest


class E03TestPlanDocumentationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.readme = (self.repo_root / "tests/e03_processed_transcriptions/README.md").read_text(
            encoding="utf-8"
        )
        self.spec = (
            self.repo_root / "docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md"
        ).read_text(encoding="utf-8")
        self.plan = (
            self.repo_root
            / "docs/sdd/plans/P03_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md"
        ).read_text(encoding="utf-8")
        self.tasks = (
            self.repo_root
            / "docs/sdd/tasks/T03_TAREFAS_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md"
        ).read_text(encoding="utf-8")

    def test_e03_test_plan_documents_required_contract(self) -> None:
        required_terms = [
            "POST /processed-transcriptions/v1.0.0",
            "raw_text",
            "didactic_text",
            "themes",
            "technical_terms",
            "technology_mentions",
            "processing_notes",
            "source.transcription",
            "Enum",
            "MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS=150000",
            "MINDVOX_MAX_UPLOAD_MB",
            "413 Payload Too Large",
            "503 Service Unavailable",
            "504 Gateway Timeout",
            "405 Method Not Allowed",
            "test_malformed_authorization_header_returns_401",
            "test_audio_over_upload_limit_returns_413",
            "test_limited_upload_reader_rejects_before_reading_full_oversized_upload",
            "test_placeholder_provider_key_returns_503",
            "test_provider_mode_rejects_hostname_resolving_to_private_address",
            "test_e03_logs_are_sanitized",
            "test_processed_transcription_auth_failure_logs_status_error_and_duration",
            "test_processing_engine_redacts_sensitive_provider_name",
            "test_benchmark_script_rejects_excessive_response_body",
            "test_long_llm_output_with_insufficient_semantic_coverage_returns_502_with_rejected_artifact",
            "test_long_llm_output_retry_can_recover_semantic_coverage",
            "test_audio_flow_moves_quality_failure_to_failed_after_max_attempts",
            "cobertura semantica",
            "postprocessing_quality_rejected",
            "runtime_snapshot",
            "MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS",
            "MINDVOX_LOCAL_LLM_AUTOSTART",
            "MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR",
            "test_contract_mode_does_not_start_llama_server",
            "test_audio_flow_keeps_queue_job_pending_when_postprocessing_fails",
            "test_processed_markdown_artifact_uses_class_metadata_title",
            "test_artifact_stem_uses_safe_class_metadata_prefix",
            "test_raw_text_file_ignores_legacy_swagger_string_placeholder",
            "textuais opcionais",
            "cliente antigo",
            "test_local_development_without_api_token_uses_dev_token",
            "test_public_deployment_without_api_token_has_no_default_token",
            "test_contract_profile_forces_contract_modes_and_disables_llama_autostart",
            "test_prod_profile_enables_public_hardening_without_dev_token_default",
            "MINDVOX_RUNTIME_PROFILE",
            "Active startup profile",
            "fastapi dev contract",
            "fastapi run prod",
            "replace-with-provider-key",
            "provider externo configurado",
            "uv run python -m unittest discover -s tests/e03_processed_transcriptions -v",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.readme)
                self.assertIn(term, self.spec)
                self.assertIn(term, self.plan)
                self.assertIn(term, self.tasks)


if __name__ == "__main__":
    unittest.main()
