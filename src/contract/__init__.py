import os

os.environ["MINDVOX_PUBLIC_DEPLOYMENT"] = "false"
os.environ["MINDVOX_ENABLE_DOCS"] = "true"
os.environ["MINDVOX_RUNTIME_PROFILE"] = "contract"
os.environ["MINDVOX_TRANSCRIPTION_MODE"] = "contract"
os.environ["MINDVOX_POSTPROCESSING_MODE"] = "auto"
os.environ["MINDVOX_LOCAL_LLM_AUTOSTART"] = "false"

from main import create_app  # noqa: E402


app = create_app()
