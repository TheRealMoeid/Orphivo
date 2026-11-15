from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QMessageBox, QPlainTextEdit, QPushButton

from src.qt_main_window import OrphivoMainWindow, _TranscriptionWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_has_editable_rtl_editor_and_controls(qapp):
    window = OrphivoMainWindow()
    assert isinstance(window.transcript_editor, QPlainTextEdit)
    assert window.transcript_editor.isReadOnly() is False
    assert window.transcript_editor.layoutDirection() == Qt.LayoutDirection.RightToLeft
    assert window.transcript_editor.document().defaultTextOption().alignment() & Qt.AlignmentFlag.AlignRight
    assert window.transcript_editor.document().defaultTextOption().textDirection() == Qt.LayoutDirection.RightToLeft
    assert window.transcript_editor.font().pointSize() == 14
    assert isinstance(window.record_button, QPushButton)
    assert window.record_button.text() == "● Start recording"
    assert window.status_label.text() == "Ready — press Start recording"
    assert isinstance(window.settings_button, QPushButton)
    window.close()


def test_record_button_recording_property_toggles_with_state(qapp):
    window = OrphivoMainWindow()
    assert window.record_button.property("recording") is False

    window._set_recording_button_active(True)
    assert window.record_button.property("recording") is True

    window._set_recording_button_active(False)
    assert window.record_button.property("recording") is False
    window.close()


def test_starting_a_recording_marks_the_button_active(qapp, monkeypatch):
    window = OrphivoMainWindow()
    monkeypatch.setattr(window.recorder, "start", lambda: None)

    window.toggle_recording()

    assert window.record_button.property("recording") is True
    window.close()


def test_heading_and_status_use_absolute_right_alignment(qapp):
    # AlignAbsolute matters for the Persian heading specifically: Qt
    # auto-detects RTL script content and silently swaps AlignRight to
    # visual-left for RTL-direction widgets unless AlignAbsolute is also
    # set. Without it, this regresses to flush-left heading/status text.
    window = OrphivoMainWindow()
    heading_align = window.heading_label.alignment()
    status_align = window.status_label.alignment()
    assert heading_align & Qt.AlignmentFlag.AlignRight
    assert heading_align & Qt.AlignmentFlag.AlignAbsolute
    assert status_align & Qt.AlignmentFlag.AlignRight
    assert status_align & Qt.AlignmentFlag.AlignAbsolute
    window.close()


def test_history_panel_header_sits_outside_the_panel_itself(qapp):
    # The panel's title/folder labels are placed in the main window's
    # header row (not inside the panel's own layout) so the panel's list
    # box starts flush with the transcript editor's top edge.
    window = OrphivoMainWindow()
    panel = window.history_panel
    assert panel.layout().indexOf(panel.title_label) == -1
    assert panel.layout().indexOf(panel.folder_label) == -1
    window.close()


def test_transcript_placeholder_is_right_aligned_and_toggles_with_content(qapp):
    window = OrphivoMainWindow()
    align = window._placeholder_label.alignment()
    assert align & Qt.AlignmentFlag.AlignRight
    assert align & Qt.AlignmentFlag.AlignAbsolute
    # isHidden() reflects the widget's own explicit visibility state,
    # independent of whether the top-level window has been shown.
    assert window._placeholder_label.isHidden() is False

    window.transcript_editor.setPlainText("سلام")
    assert window._placeholder_label.isHidden() is True

    window.transcript_editor.setPlainText("")
    assert window._placeholder_label.isHidden() is False
    window.close()


def _enter_key_event():
    from PySide6.QtCore import QEvent
    return QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)


def test_enter_toggles_recording_when_editor_does_not_have_focus(qapp, monkeypatch):
    window = OrphivoMainWindow()
    monkeypatch.setattr(window.recorder, "start", lambda: None)

    window.keyPressEvent(_enter_key_event())

    assert window.record_button.property("recording") is True
    window.close()


def test_enter_in_transcript_editor_does_not_toggle_recording(qapp):
    window = OrphivoMainWindow()
    window.show()
    window.transcript_editor.setFocus()
    assert window.focusWidget() is window.transcript_editor

    window.keyPressEvent(_enter_key_event())

    assert window.record_button.property("recording") is False
    window.close()


def test_enter_does_not_toggle_recording_while_busy(qapp):
    window = OrphivoMainWindow()
    window.busy = True
    calls = []
    window.toggle_recording = lambda: calls.append(True)

    event = _enter_key_event()
    window.keyPressEvent(event)

    assert calls == []
    assert event.isAccepted() is True
    window.close()


def test_history_panel_present_and_loads_selected_transcript(qapp, tmp_path):
    from src.history import save_transcript

    window = OrphivoMainWindow()
    window.output_dir = tmp_path
    window.history_panel.refresh(tmp_path)
    saved = save_transcript(tmp_path, "متن تست", __import__("datetime").datetime(2026, 1, 1))
    window.history_panel.refresh()

    window._load_transcript(saved)

    assert window.transcript_editor.toPlainText().strip() == "متن تست"
    assert window.status_label.text() == f"Loaded {saved.name}"
    window.close()


def test_save_as_and_autosave_refresh_the_history_panel(qapp, tmp_path, monkeypatch):
    window = OrphivoMainWindow()
    window.output_dir = tmp_path
    window.history_panel.refresh(tmp_path)
    refreshed = []
    monkeypatch.setattr(window.history_panel, "refresh", lambda *a, **k: refreshed.append(True))

    window._on_transcription_completed("سلام", tmp_path / "transcript_x.txt")

    assert refreshed == [True]
    window.close()


def test_open_settings_applies_accepted_values_and_persists(qapp, monkeypatch, tmp_path):
    from pathlib import Path
    import src.qt_main_window as qt_main_window_module

    window = OrphivoMainWindow()
    new_dir = tmp_path / "chosen-folder"
    new_dir.mkdir()

    class _FakeDialog:
        DialogCode = qt_main_window_module.OrphivoSettingsDialog.DialogCode

        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return self.DialogCode.Accepted

        def result_values(self):
            return new_dir, False, "light"

    monkeypatch.setattr(qt_main_window_module, "OrphivoSettingsDialog", _FakeDialog)
    saved = {}
    monkeypatch.setattr(
        qt_main_window_module, "save_settings", lambda settings: saved.update(settings)
    )

    window.open_settings()

    assert window.output_dir == new_dir
    assert window.settings["auto_save"] is False
    assert window.settings["theme"] == "light"
    assert saved.get("output_dir") == str(new_dir)
    assert saved.get("auto_save") is False
    assert saved.get("theme") == "light"
    assert window.status_label.text() == "Settings saved"
    window.close()


def test_apply_theme_switches_palette_and_placeholder_color(qapp):
    from src.theme import PALETTES

    window = OrphivoMainWindow()
    window.settings["theme"] = "light"
    window.apply_theme()
    assert PALETTES["light"]["muted"] in window._placeholder_label.styleSheet()

    window.settings["theme"] = "dark"
    window.apply_theme()
    assert PALETTES["dark"]["muted"] in window._placeholder_label.styleSheet()
    window.close()


def test_copy_text_copies_transcript_to_system_clipboard(qapp):
    window = OrphivoMainWindow()
    window.transcript_editor.setPlainText("سلام Orphivo")
    window.copy_text()
    assert QApplication.clipboard().text() == "سلام Orphivo"
    assert window.status_label.text() == "Transcript copied to clipboard"
    window.close()


def test_microphone_error_shows_generic_message_not_raw_backend_text(qapp, monkeypatch):
    window = OrphivoMainWindow()
    window.recorder = Mock()
    window.recorder.recording = False
    window.recorder.start.side_effect = RuntimeError(
        "Unanticipated host error [PaErrorCode -9999]: 'Undefined external error.' [MME error 1]"
    )
    shown = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: shown.append(args))

    window.toggle_recording()

    assert "PaErrorCode" not in window.status_label.text()
    assert "Could not start recording" in window.status_label.text()
    assert len(shown) == 1
    assert "PaErrorCode" not in shown[0][-1]
    window.close()


def test_worker_autosaves_nonempty_result_and_removes_audio(tmp_path):
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"mock audio")
    transcriber = Mock()
    transcriber.transcribe.return_value = "  سلام Orphivo  "
    worker = _TranscriptionWorker(transcriber, audio_path, tmp_path / "history", True)
    completed, failed = [], []
    worker.completed.connect(lambda text, saved: completed.append((text, saved)))
    worker.failed.connect(failed.append)
    worker.run()
    assert failed == []
    assert len(completed) == 1
    text, saved = completed[0]
    assert text == "سلام Orphivo"
    assert isinstance(saved, Path)
    assert saved.read_text(encoding="utf-8") == "سلام Orphivo\n"
    assert not audio_path.exists()


def test_worker_does_not_save_empty_result(tmp_path):
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"mock audio")
    transcriber = Mock()
    transcriber.transcribe.return_value = "  \n "
    worker = _TranscriptionWorker(transcriber, audio_path, tmp_path / "history", True)
    completed = []
    worker.completed.connect(lambda text, saved: completed.append((text, saved)))
    worker.run()
    assert completed == [("", None)]
    assert not (tmp_path / "history").exists()
    assert not audio_path.exists()


def test_worker_reports_errors_and_removes_audio(tmp_path):
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"mock audio")
    transcriber = Mock()
    transcriber.transcribe.side_effect = RuntimeError("simulated failure")
    worker = _TranscriptionWorker(transcriber, audio_path, tmp_path / "history", True)
    failed = []
    worker.failed.connect(failed.append)
    worker.run()
    assert failed == ["simulated failure"]
    assert not audio_path.exists()
