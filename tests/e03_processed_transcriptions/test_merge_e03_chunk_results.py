import unittest

from scripts.merge_e03_chunk_results import (
    ChunkRecord,
    canonical_entity_key,
    coverage_report,
    merge_didactic_text,
    public_payload,
)


class MergeE03ChunkResultsTests(unittest.TestCase):
    def test_merge_didactic_text_removes_artificial_headings_and_splits_long_paragraphs(self):
        long_text = (
            "Introdução\n\n"
            "A primeira frase apresenta o contexto da aula. "
            "A segunda frase preserva a sequência didática. "
            "A terceira frase mantém o conteúdo sem criar tópicos artificiais."
        )
        chunks = [
            ChunkRecord(
                chunk_id="chunk-01",
                order=0,
                first_segment_index=0,
                segment_indexes=[0],
                input_chars=len(long_text),
                didactic_chars=len(long_text),
                elapsed_seconds=1.0,
                response={"didactic_text": long_text},
            )
        ]

        merged = merge_didactic_text(chunks, max_paragraph_chars=80)

        self.assertNotIn("Introdução", merged)
        paragraphs = [part for part in merged.split("\n\n") if part.strip()]
        self.assertGreater(len(paragraphs), 1)
        self.assertTrue(all(not paragraph.startswith("#") for paragraph in paragraphs))

    def test_public_payload_removes_experimental_merge_fields(self):
        payload = {
            "processed_transcription_id": "ptr_merge_test",
            "themes": [{"title": "APIs", "source_chunks": ["chunk-01"]}],
            "technical_terms": [{"term": "API", "source_chunks": ["chunk-01"]}],
            "technology_mentions": [{"name": "FastAPI", "source_chunks": ["chunk-01"]}],
            "merge_metadata": {"chunk_count": 1},
        }

        public = public_payload(payload)

        self.assertNotIn("merge_metadata", public)
        self.assertNotIn("source_chunks", public["themes"][0])
        self.assertNotIn("source_chunks", public["technical_terms"][0])
        self.assertNotIn("source_chunks", public["technology_mentions"][0])

    def test_canonical_entity_key_collapses_common_variants(self):
        self.assertEqual(canonical_entity_key("APIs"), "api")
        self.assertEqual(
            canonical_entity_key("API (Application Programming Interface)"),
            "api",
        )
        self.assertEqual(
            canonical_entity_key("MVP (Minimum Viable Product)"),
            "mvp",
        )
        self.assertEqual(
            canonical_entity_key("Microserviços"),
            canonical_entity_key("Microsserviços"),
        )

    def test_coverage_report_marks_found_and_missing_terms(self):
        payload = {
            "didactic_text": "O projeto Positivo analisou editais e mencionou Data Lake.",
            "themes": [],
            "technical_terms": [],
            "technology_mentions": [],
            "processing_notes": [],
        }

        report = coverage_report(payload, ["Positivo", "Data Lake", "Eduardo"])

        self.assertEqual(report["checked"], 3)
        self.assertEqual(report["found"], 2)
        self.assertEqual(report["missing"], 1)
        self.assertEqual(
            [item["found"] for item in report["items"]],
            [True, True, False],
        )


if __name__ == "__main__":
    unittest.main()
