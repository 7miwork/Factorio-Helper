from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
AI_PROVIDERS_FILE = CONFIG_DIR / "ai_providers.json"
BLUEPRINTS_DIR = ROOT / "blueprints"
LOGS_DIR = ROOT / "logs"
DATA_DIR = ROOT / "data"
DATA_FACTORIO_DIR = DATA_DIR / "factorio"


def load_settings() -> dict:
    if not SETTINGS_PATH.is_file():
        return {}
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")