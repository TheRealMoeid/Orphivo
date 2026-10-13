import json
from pathlib import Path
from src.settings import defaults, load_settings, save_settings


def test_settings_round_trip(tmp_path: Path):
    target = tmp_path / "settings.json"
    value = defaults()
    value.update(theme="light", output_dir=str(tmp_path / "out"), auto_save=False)
    save_settings(value, target)
    assert load_settings(target) == value


def test_invalid_settings_fall_back_to_defaults(tmp_path: Path):
    target = tmp_path / "settings.json"
    target.write_text("{broken", encoding="utf-8")
    assert load_settings(target) == defaults()


def test_unknown_theme_is_normalized(tmp_path: Path):
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({"theme": "neon"}), encoding="utf-8")
    assert load_settings(target)["theme"] == "dark"
