from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from src.history import save_transcript
from src.qt_history_panel import OrphivoHistoryPanel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_empty_folder_shows_empty_list_without_error(qapp, tmp_path):
    panel = OrphivoHistoryPanel(tmp_path / "does-not-exist-yet")
    assert panel.list_widget.count() == 0
    panel.close()


def test_lists_saved_transcripts_newest_first(qapp, tmp_path):
    save_transcript(tmp_path, "اول", datetime(2026, 1, 1, 9, 0, 0))
    save_transcript(tmp_path, "دوم", datetime(2026, 1, 2, 9, 0, 0))

    panel = OrphivoHistoryPanel(tmp_path)

    assert panel.list_widget.count() == 2
    assert panel.list_widget.item(0).text() == panel._files[0].stem
    assert panel._files[0].stat().st_mtime >= panel._files[1].stat().st_mtime
    panel.close()


def test_clicking_an_item_emits_its_path(qapp, tmp_path):
    saved = save_transcript(tmp_path, "سلام", datetime(2026, 1, 1, 9, 0, 0))
    panel = OrphivoHistoryPanel(tmp_path)
    emitted = []
    panel.transcript_selected.connect(emitted.append)

    item = panel.list_widget.item(0)
    panel._on_item_clicked(item)

    assert emitted == [saved]
    panel.close()


def test_delete_removes_file_and_refreshes_list(qapp, tmp_path, monkeypatch):
    saved = save_transcript(tmp_path, "حذف این", datetime(2026, 1, 1, 9, 0, 0))
    panel = OrphivoHistoryPanel(tmp_path)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes
    )

    panel.list_widget.setCurrentRow(0)
    panel.delete_selected()

    assert not saved.exists()
    assert panel.list_widget.count() == 0
    panel.close()


def test_refresh_with_new_folder_updates_label_and_contents(qapp, tmp_path):
    folder_a = tmp_path / "a"
    folder_b = tmp_path / "b"
    save_transcript(folder_b, "ب", datetime(2026, 1, 1, 9, 0, 0))

    panel = OrphivoHistoryPanel(folder_a)
    assert panel.list_widget.count() == 0

    panel.refresh(folder_b)

    assert panel.folder_label.text() == str(folder_b)
    assert panel.list_widget.count() == 1
    panel.close()
