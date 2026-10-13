"""Persistent user preferences stored outside the project directory."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

APP_NAME = "PersianSTT"
DEFAULT_MODEL_PATH = Path(r"D:\whisper-large-fa-v1-ct2")
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "Persian Transcripts"


def config_path() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return root / APP_NAME / "settings.json"


def defaults() -> dict[str, Any]:
    return {"theme": "dark", "output_dir": str(DEFAULT_OUTPUT_DIR), "auto_save": True}


def load_settings(path: Path | None = None) -> dict[str, Any]:
    result = defaults()
    target = path or config_path()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            result.update({k: data[k] for k in result.keys() if k in data})
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    if result.get("theme") not in {"dark", "light"}:
        result["theme"] = "dark"
    result["auto_save"] = bool(result.get("auto_save", True))
    return result


def save_settings(settings: dict[str, Any], path: Path | None = None) -> None:
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
