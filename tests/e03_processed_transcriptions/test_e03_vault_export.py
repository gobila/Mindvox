import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from schemas.processed_transcriptions import (  # noqa: E402
    ConceptCandidate,
    MemoryManifest,
    OperationalAnchors,
    ProcessingEngine,
    ProcessingNote,
    ProcessedTranscriptionResponse,
    Source,
    StudyPackage,
    StudyPackageAuditReport,
    StudyPackageExportTargets,
    StudyPackageMetadata,
    StudyPackageRawTranscription,
    TechnicalTerm,
    TechnologyMention,
    Theme,
)
from schemas.transcriptions import TranscriptionMetadata  # noqa: E402
from services.e03_course_context import upsert_course  # noqa: E402
from services.e03_study_package import (  # noqa: E402
    attach_study_package,
    save_study_package_artifact,
)
from services.e03_vault_exporter import export_study_package_to_vault  # noqa: E402
from services.e03_vault_scaffold import (  # noqa: E402
    StudentVaultScaffoldError,
    create_student_vault,
)
from settings import Settings  # noqa: E402


class E03VaultExportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_student_vault_builds_canonical_minimum_structure(self):
        settings = self._settings()

        scaffold = create_student_vault(
            course_name="UFG Pos 2",
            institution="UFG",
            settings=settings,
        )

        self.assertEqual(scaffold.course_id, "ufg_pos_2")
        self.assertTrue((scaffold.vault_path / "00-Inbox" / "_captura-rapida.md").exists())
        self.assertTrue((scaffold.vault_path / "03-Operacional" / "links-de-aula.md").exists())
        self.assertTrue((scaffold.vault_path / "01-Cursos" / "ufg_pos_2" / "_index.md").exists())

    def test_create_student_vault_refuses_existing_non_empty_directory(self):
        settings = self._settings()
        existing = self.root / "vaults" / "ufg_pos_2"
        existing.mkdir(parents=True)
        (existing / "manual.md").write_text("conteudo anterior\n", encoding="utf-8")

        with self.assertRaises(StudentVaultScaffoldError):
            create_student_vault(course_name="UFG Pos 2", settings=settings)

    def test_export_study_package_writes_canonical_notes(self):
        settings = self._settings()
        scaffold = create_student_vault(course_name="UFG Pos 2", settings=settings)
        study_package = self._study_package()

        export = export_study_package_to_vault(
            study_package=study_package,
            vault_path=scaffold.vault_path,
        )

        aulas_path = (
            scaffold.vault_path
            / "01-Cursos"
            / "ufg_pos_2"
            / "api"
            / "aulas"
            / "Aula_01_2026-05-09_s4.md"
        )
        bruto_path = aulas_path.parent.parent / "brutos" / "Aula_01_2026-05-09_s4_bruto.md"
        concept_path = scaffold.vault_path / "02-Conceitos" / "api_first.md"
        links_path = scaffold.vault_path / "03-Operacional" / "links-de-aula.md"

        self.assertIn(aulas_path, export.written_paths)
        self.assertTrue(aulas_path.exists())
        self.assertTrue(bruto_path.exists())
        self.assertTrue(concept_path.exists())
        self.assertIn("Texto didatico final.", aulas_path.read_text(encoding="utf-8"))
        self.assertIn("Transcrito bruto auditavel.", bruto_path.read_text(encoding="utf-8"))
        self.assertIn("https://example.com/aula", links_path.read_text(encoding="utf-8"))

    def test_export_requires_existing_vault_directory(self):
        with self.assertRaisesRegex(Exception, "existing directory"):
            export_study_package_to_vault(
                study_package=self._study_package(),
                vault_path=self.root / "missing",
            )

    def test_save_study_package_exports_to_active_vault_when_enabled(self):
        settings = self._settings(obsidian_export_enabled=True)
        scaffold = create_student_vault(course_name="UFG Pos 2", settings=settings)
        upsert_course(
            course_name="UFG Pos 2",
            vault_path=str(scaffold.vault_path),
            settings=settings,
        )
        response = attach_study_package(self._processed_response())

        save_study_package_artifact(response, settings=settings)

        self.assertEqual(
            response.study_package.export_targets.obsidian_vault_path,
            str(scaffold.vault_path),
        )
        self.assertTrue(
            (
                scaffold.vault_path
                / "01-Cursos"
                / "ufg_pos_2"
                / "api"
                / "aulas"
                / "Aula_01_2026-05-09_s4.md"
            ).exists()
        )

    def _study_package(self) -> StudyPackage:
        theme = Theme(
            order=1,
            title="Contratos de API",
            summary="Discussao sobre API First.",
            key_points=["OpenAPI", "FastAPI"],
            semantic_role="topico",
        )
        term = TechnicalTerm(
            term="API First",
            explanation="Design do contrato antes da implementacao.",
            confidence="high",
        )
        technology = TechnologyMention(
            name="FastAPI",
            category="framework",
            context="Framework citado na aula.",
            importance="high",
            confidence="high",
        )
        return StudyPackage(
            metadata=StudyPackageMetadata(
                course_id="ufg_pos_2",
                course_name="UFG Pos 2",
                institution="UFG",
                discipline="API",
                professor="Rogerio",
                class_number="1",
                class_date="2026-05-09",
                class_title="API - Aula 1 - Sessao 4",
                session_number="4",
                session_label="A1S4",
            ),
            source=Source(
                input_origin="raw_text",
                raw_text_origin="provided_by_client",
                transcription=None,
            ),
            raw_transcription=StudyPackageRawTranscription(
                text="Transcrito bruto auditavel.",
            ),
            didactic_text="Texto didatico final.",
            themes=[theme],
            technical_terms=[term],
            technology_mentions=[technology],
            operational_anchors=OperationalAnchors(
                links=["https://example.com/aula"],
            ),
            concept_candidates=[
                ConceptCandidate(
                    title="API First",
                    source="technical_term",
                    summary="Design do contrato antes da implementacao.",
                    confidence="high",
                )
            ],
            audit_report=StudyPackageAuditReport(
                status="passed",
                processing_notes_count=1,
                themes_count=1,
                technical_terms_count=1,
                technology_mentions_count=1,
                notes=[ProcessingNote(type="audit", message="ok")],
            ),
            memory_manifest=MemoryManifest(
                relational_entities=["course", "class"],
                vector_candidates=["didactic_text"],
            ),
            export_targets=StudyPackageExportTargets(),
        )

    def _processed_response(self) -> ProcessedTranscriptionResponse:
        study_package = self._study_package()
        return ProcessedTranscriptionResponse(
            processed_transcription_id="ptr_20260614T000000Z_12345678",
            input_type="raw_text",
            language="pt-BR",
            raw_text=study_package.raw_transcription.text,
            didactic_text=study_package.didactic_text,
            themes=study_package.themes,
            technical_terms=study_package.technical_terms,
            technology_mentions=study_package.technology_mentions,
            processing_notes=study_package.audit_report.notes,
            metadata=TranscriptionMetadata(
                course="UFG Pos 2",
                discipline="API",
                class_date="2026-05-09",
                class_title="API - Aula 1 - Sessao 4",
                session_label="A1S4",
            ),
            source=study_package.source,
            processing_engine=ProcessingEngine(
                mode="contract",
                name="contract",
                model="contract",
                version="1",
            ),
            artifact_locations=None,
        )

    def _settings(self, *, obsidian_export_enabled: bool = False):
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
            e03_obsidian_export_enabled=obsidian_export_enabled,
            e03_obsidian_vaults_base_dir=str(self.root / "vaults"),
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
