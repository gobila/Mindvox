import os
import runpy
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from settings import (  # noqa: E402
    DEFAULT_LOCAL_DEV_API_TOKEN,
    apply_main_profile_defaults,
    get_settings,
)


PROFILE_ENV_NAMES = [
    "MINDVOX_API_TOKEN",
    "MINDVOX_RUNTIME_PROFILE",
    "MINDVOX_PUBLIC_DEPLOYMENT",
    "MINDVOX_ENABLE_DOCS",
    "MINDVOX_TRUSTED_HOSTS",
    "MINDVOX_TRANSCRIPTION_MODE",
    "MINDVOX_POSTPROCESSING_MODE",
    "MINDVOX_POSTPROCESSING_CHUNKING_MODE",
    "MINDVOX_LOCAL_LLM_AUTOSTART",
]


class StartupProfilesTest(unittest.TestCase):
    def setUp(self):
        self.previous_env = {
            name: os.environ.get(name)
            for name in PROFILE_ENV_NAMES
        }
        for name in PROFILE_ENV_NAMES:
            os.environ.pop(name, None)

    def tearDown(self):
        for name, value in self.previous_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_local_development_without_api_token_uses_dev_token(self):
        settings = get_settings()

        self.assertEqual(settings.api_token, DEFAULT_LOCAL_DEV_API_TOKEN)
        self.assertEqual(settings.runtime_profile, "dev")
        self.assertFalse(settings.public_deployment)
        self.assertEqual(settings.transcription_mode, "real")
        self.assertEqual(settings.postprocessing_mode, "local")

    def test_plain_main_profile_resets_stale_contract_modes(self):
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "contract"
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "contract"

        apply_main_profile_defaults()
        settings = get_settings()

        self.assertEqual(settings.runtime_profile, "dev")
        self.assertEqual(settings.transcription_mode, "real")
        self.assertEqual(settings.postprocessing_mode, "local")
        self.assertEqual(settings.postprocessing_chunking_mode, "tfidf")

    def test_plain_main_profile_preserves_explicit_chunking_override(self):
        os.environ["MINDVOX_POSTPROCESSING_CHUNKING_MODE"] = "off"

        apply_main_profile_defaults()
        settings = get_settings()

        self.assertEqual(settings.runtime_profile, "dev")
        self.assertEqual(settings.postprocessing_chunking_mode, "off")

    def test_public_deployment_without_api_token_has_no_default_token(self):
        os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"

        settings = get_settings()

        self.assertIsNone(settings.api_token)
        self.assertEqual(settings.runtime_profile, "prod")

    def test_contract_profile_forces_contract_modes_and_disables_llama_autostart(self):
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "real"
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "local"
        os.environ["MINDVOX_LOCAL_LLM_AUTOSTART"] = "true"

        namespace = runpy.run_path(str(SRC_DIR / "contract" / "__init__.py"))
        settings = get_settings()

        self.assertIn("app", namespace)
        self.assertEqual(settings.api_token, DEFAULT_LOCAL_DEV_API_TOKEN)
        self.assertEqual(settings.runtime_profile, "contract")
        self.assertFalse(settings.public_deployment)
        self.assertTrue(settings.docs_enabled)
        self.assertEqual(settings.transcription_mode, "contract")
        self.assertEqual(settings.postprocessing_mode, "contract")
        self.assertFalse(settings.local_llm_autostart)

    def test_explicit_contract_profile_is_preserved_by_main_defaults(self):
        os.environ["MINDVOX_RUNTIME_PROFILE"] = "contract"
        os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "contract"
        os.environ["MINDVOX_POSTPROCESSING_MODE"] = "auto"

        apply_main_profile_defaults()
        settings = get_settings()

        self.assertEqual(settings.runtime_profile, "contract")
        self.assertEqual(settings.transcription_mode, "contract")
        self.assertEqual(settings.postprocessing_mode, "contract")

    def test_prod_profile_enables_public_hardening_without_dev_token_default(self):
        os.environ["MINDVOX_API_TOKEN"] = "prod-token"
        os.environ["MINDVOX_TRUSTED_HOSTS"] = "api.example.com"

        namespace = runpy.run_path(str(SRC_DIR / "prod" / "__init__.py"))
        settings = get_settings()

        self.assertIn("app", namespace)
        self.assertEqual(settings.api_token, "prod-token")
        self.assertEqual(settings.runtime_profile, "prod")
        self.assertTrue(settings.public_deployment)
        self.assertFalse(settings.docs_enabled)
        self.assertEqual(settings.trusted_hosts, ("api.example.com",))
        self.assertEqual(settings.postprocessing_mode, "provider")
        self.assertFalse(settings.local_llm_autostart)


if __name__ == "__main__":
    unittest.main()
