from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from schemas.transcriptions import TranscriptionMetadata  # noqa: E402
from services.artifact_naming import (  # noqa: E402
    build_artifact_stem,
    build_human_title,
)


class ArtifactNamingTest(unittest.TestCase):
    def test_artifact_stem_uses_safe_class_metadata_prefix(self) -> None:
        metadata = TranscriptionMetadata(
            class_date="2026-06-09",
            class_title="Aula de APIs",
            session_label="S02",
        )

        stem = build_artifact_stem(
            artifact_id="tr_20260609T000000Z_ab12cd34",
            metadata=metadata,
        )

        self.assertEqual(
            stem,
            "2026-06-09-aula-de-apis-s02_tr_20260609T000000Z_ab12cd34",
        )

    def test_artifact_stem_uses_safe_fallback_metadata(self) -> None:
        metadata = TranscriptionMetadata(session_label="S01")

        stem = build_artifact_stem(
            artifact_id="ptr_20260609T000000Z_ab12cd34",
            metadata=metadata,
        )

        self.assertEqual(stem, "s01_ptr_20260609T000000Z_ab12cd34")

    def test_human_title_uses_class_title_and_session(self) -> None:
        metadata = TranscriptionMetadata(
            class_date="2026-06-09",
            class_title="API First and FastAPI",
            session_label="S02",
        )

        title = build_human_title(default_title="Fallback", metadata=metadata)

        self.assertEqual(title, "2026-06-09 - API First and FastAPI - S02")


if __name__ == "__main__":
    unittest.main()
