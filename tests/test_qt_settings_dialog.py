from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from src.qt_settings_dialog import OrphivoSettingsDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_dialog_prefills_current_output_dir_auto_save_and_theme(qapp, tmp_path):
    dialog = OrphivoSettingsDialog(tmp_path / "transcripts", False, "light")
    assert dialog.folder_edit.text() == str(tmp_path / "transcripts")
    assert dialog.auto_save_checkbox.isChecked() is False
    assert dialog.light_radio.isChecked() is True
    assert dialog.dark_radio.isChecked() is False
    dialog.close()


def test_dialog_defaults_to_dark_when_theme_is_dark(qapp, tmp_path):
    dialog = OrphivoSettingsDialog(tmp_path / "transcripts", True, "dark")
    assert dialog.dark_radio.isChecked() is True
    assert dialog.light_radio.isChecked() is False
    dialog.close()


def test_save_disabled_until_something_changes(qapp, tmp_path):
    dialog = OrphivoSettingsDialog(tmp_path / "folder", True, "dark")
    assert dialog.save_button.isEnabled() is False

    dialog.auto_save_checkbox.setChecked(False)
    assert dialog.save_button.isEnabled() is True

    dialog.auto_save_checkbox.setChecked(True)
    assert dialog.save_button.isEnabled() is False

    dialog.light_radio.setChecked(True)
    assert dialog.save_button.isEnabled() is True
    dialog.close()


def test_save_disabled_state_tracks_folder_text_changes(qapp, tmp_path):
    dialog = OrphivoSettingsDialog(tmp_path / "folder", True, "dark")
    assert dialog.save_button.isEnabled() is False

    dialog.folder_edit.setText(str(tmp_path / "different-folder"))
    assert dialog.save_button.isEnabled() is True

    dialog.folder_edit.setText(str(tmp_path / "folder"))
    assert dialog.save_button.isEnabled() is False
    dialog.close()


def test_save_with_valid_folder_creates_it_and_returns_values(qapp, tmp_path):
    target = tmp_path / "new-folder"
    dialog = OrphivoSettingsDialog(tmp_path / "old-folder", True, "dark")
    dialog.folder_edit.setText(str(target))
    dialog.auto_save_checkbox.setChecked(False)
    dialog.light_radio.setChecked(True)

    dialog._on_save()

    assert dialog.result() == OrphivoSettingsDialog.DialogCode.Accepted
    output_dir, auto_save, theme = dialog.result_values()
    assert output_dir == target
    assert auto_save is False
    assert theme == "light"
    assert target.is_dir()


def test_save_with_empty_folder_is_rejected_and_dialog_stays_open(qapp, tmp_path, monkeypatch):
    dialog = OrphivoSettingsDialog(tmp_path / "folder", True, "dark")
    dialog.folder_edit.setText("   ")
    shown = []
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: shown.append(a))

    dialog._on_save()

    assert dialog.result() != OrphivoSettingsDialog.DialogCode.Accepted
    assert len(shown) == 1
    dialog.close()


def test_cancel_rejects_without_touching_filesystem(qapp, tmp_path):
    dialog = OrphivoSettingsDialog(tmp_path / "folder", True, "dark")
    dialog.folder_edit.setText(str(tmp_path / "should-not-be-created"))

    dialog.reject()

    assert dialog.result() == OrphivoSettingsDialog.DialogCode.Rejected
    assert not (tmp_path / "should-not-be-created").exists()
