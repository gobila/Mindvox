import os

os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "true"
os.environ["MINDVOX_ENABLE_DOCS"] = os.getenv("MINDVOX_ENABLE_DOCS", "false")
os.environ["MINDVOX_RUNTIME_PROFILE"] = "prod"
os.environ["MINDVOX_POSTPROCESSING_MODE"] = os.getenv(
    "MINDVOX_POSTPROCESSING_MODE",
    "provider",
)
os.environ["MINDVOX_LOCAL_LLM_AUTOSTART"] = "false"

from main import create_app  # noqa: E402


app = create_app()
