"""Regression tests for temporary status messages (Copy/Save) correctly
reverting to the real base state instead of permanently overwriting it.

Covers the bug found during manual long-inference testing: clicking Copy
or Save As while transcription was still running showed the right message
for a moment, but when the worker later finished, _on_transcription_completed
overwrote it - the user only ever saw the completion status, never the
earlier "copied"/"saved" confirmation lingering, and depending on timing
could perceive the opposite (the transcribing message reappearing).
"""
from unittest.mock import Mock

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.qt_main_window import OrphivoMainWindow

# A QTimer needs a live QApplication/event-loop context to track isActive()
# correctly, even when it's never actually left running past a test.
_app = QApplication.instance() or QApplication([])


def _make_window_harness():
    """A minimally constructed window: real status/timer wiring, mocked
    widgets for anything we don't need a real QWidget for."""
    window = OrphivoMainWindow.__new__(OrphivoMainWindow)
    window.status_label = Mock()
    window.history_panel = Mock()
    window.transcript_editor = Mock()
    window.busy = False
    window._base_status_text = "Ready — press Start recording"
    window._status_revert_timer = QTimer()
    window._status_revert_timer.setSingleShot(True)
    window._status_revert_timer.setInterval(3000)
    window._status_revert_timer.timeout.connect(window._revert_status)
    return window


def test_show_temporary_status_does_not_change_base_text():
    window = _make_window_harness()
    window._set_status("Transcribing locally on CPU…")

    window._show_temporary_status("Transcript copied to clipboard")

    assert window._base_status_text == "Transcribing locally on CPU…"
    window.status_label.setText.assert_called_with("Transcript copied to clipboard")


def test_revert_status_restores_the_base_text():
    window = _make_window_harness()
    window._set_status("Transcribing locally on CPU…")
    window._show_temporary_status("Transcript copied to clipboard")

    window._revert_status()

    window.status_label.setText.assert_called_with("Transcribing locally on CPU…")


def test_set_status_cancels_a_pending_revert_so_it_cannot_fire_later():
    window = _make_window_harness()
    window._set_status("Transcribing locally on CPU…")
    window._show_temporary_status("Transcript copied to clipboard")
    assert window._status_revert_timer.isActive()

    # A real state change (e.g. transcription completing) must win outright,
    # not get clobbered by an earlier temporary message's timer firing later.
    window._set_status("Transcription complete · saved to transcript.txt")

    assert not window._status_revert_timer.isActive()
    assert window._base_status_text == "Transcription complete · saved to transcript.txt"
    window.status_label.setText.assert_called_with(
        "Transcription complete · saved to transcript.txt"
    )


def test_copy_while_busy_shows_temporary_message_without_touching_busy_state():
    window = _make_window_harness()
    window.busy = True
    window._set_status("Transcribing locally on CPU…")
    window.transcript_editor.toPlainText.return_value = "متن نمونه"

    with __import__("unittest.mock", fromlist=["patch"]).patch(
        "src.qt_main_window.QApplication"
    ) as mock_app:
        window.copy_text()

    # Buttons are never disabled by this fix - busy state is untouched.
    assert window.busy is True
    mock_app.clipboard.return_value.setText.assert_called_once_with("متن نمونه")
    window.status_label.setText.assert_called_with("Transcript copied to clipboard")
    assert window._base_status_text == "Transcribing locally on CPU…"


def test_loading_a_transcript_while_busy_does_not_clobber_the_base_status():
    # Found in manual testing: _load_transcript originally used _set_status,
    # so clicking a history-panel item while a transcription was running
    # permanently stomped "Transcribing locally…" with "Loaded <file>",
    # the same class of bug as the original copy_text/save_as issue.
    window = _make_window_harness()
    window.busy = True
    window._set_status("Transcribing locally on CPU…")
    window.transcript_editor.setPlainText = Mock()

    with __import__("unittest.mock", fromlist=["patch"]).patch(
        "src.qt_main_window.read_transcript", return_value="سلام"
    ):
        window._load_transcript(__import__("pathlib").Path("/tmp/transcript_x.txt"))

    window.status_label.setText.assert_called_with("Loaded transcript_x.txt")
    assert window._base_status_text == "Transcribing locally on CPU…"

    window._revert_status()
    window.status_label.setText.assert_called_with("Transcribing locally on CPU…")


def test_settings_saved_message_while_recording_does_not_clobber_the_base_status():
    # Same class of bug: opening Settings and saving while recording is in
    # progress must not permanently overwrite "Recording… press Stop to
    # finish" with "Settings saved".
    window = _make_window_harness()
    window._set_status("Recording… press Stop to finish")

    window._show_temporary_status("Settings saved")

    assert window._base_status_text == "Recording… press Stop to finish"
    window.status_label.setText.assert_called_with("Settings saved")

    window._revert_status()
    window.status_label.setText.assert_called_with("Recording… press Stop to finish")


def _make_full_window_for_stop_recording():
    """A window harness exercising the real _stop_recording() path, with the
    recorder/transcriber/QThread machinery mocked so no real audio or model
    inference runs."""
    window = _make_window_harness()
    window.record_button = Mock()
    window._set_recording_button_active = Mock()
    window._duration_timer = Mock()
    window.recorder = Mock()
    window.recorder.stop = Mock()
    window.transcriber = Mock()
    window.output_dir = __import__("pathlib").Path("/tmp")
    window.settings = {"auto_save": True}
    return window


def test_transcribing_moves_the_state_onto_the_button_and_clears_the_status_line():
    # User-requested change: the status line used to say "Transcribing
    # locally on CPU…" at the same time the button went gray - duplicating
    # the same information in two places while the button gave no visual
    # indication of what was actually happening. Now the button itself
    # carries the state ("Transcribing…", with its own muted :disabled
    # style) and the status line is cleared, freeing it up for copy/save/
    # load/settings confirmations without a second "Transcribing…" to
    # immediately clash with or get confused for.
    window = _make_full_window_for_stop_recording()

    with __import__("unittest.mock", fromlist=["patch"]).patch(
        "src.qt_main_window.QThread"
    ), __import__("unittest.mock", fromlist=["patch"]).patch(
        "src.qt_main_window._TranscriptionWorker"
    ), __import__("unittest.mock", fromlist=["patch"]).patch(
        "src.qt_main_window.tempfile.NamedTemporaryFile"
    ) as mock_tmp:
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/fake.wav"
        window._stop_recording()

    window.record_button.setText.assert_called_with("Transcribing…")
    window.record_button.setEnabled.assert_called_with(False)
    assert window.busy is True
    assert window._base_status_text == ""
    window.status_label.setText.assert_called_with("")


def test_transcription_finishing_restores_the_record_button_text():
    window = _make_window_harness()
    window.record_button = Mock()
    window._worker = Mock()
    window._thread = Mock()

    window._on_transcription_thread_finished()

    window.record_button.setText.assert_called_with("● Start recording")
    window.record_button.setEnabled.assert_called_with(True)
    assert window.busy is False
