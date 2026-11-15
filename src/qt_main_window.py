"""Stage 2 PySide6 main window; the legacy app entry point is not changed."""
from __future__ import annotations

import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QKeyEvent, QTextOption
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from .history import read_transcript, save_transcript
from .qt_history_panel import OrphivoHistoryPanel
from .recorder import AudioRecorder
from .settings import load_settings, save_settings
from .qt_settings_dialog import OrphivoSettingsDialog
from .theme import PALETTES
from .transcriber import PersianTranscriber

# Two deliberately limited extra accents (triadic, rotated from each
# theme's own "accent" color in src/theme.py) used only for the
# active-recording state and the duration timer/success state. The light
# variants are darker/more saturated than the dark variants for contrast
# against a light background - a plain hue rotation of the dark pair would
# be unreadably pale on white. Everything else comes from PALETTES
# directly, so switching themes also shifts the window's neutrals and its
# primary accent (which is already theme-aware in src/theme.py).
_SEMANTIC_ACCENTS = {
    "dark": {"recording": "#ff6d8c", "recording_hover": "#e6597a", "timer": "#8cff6d"},
    "light": {"recording": "#d6336c", "recording_hover": "#b8255c", "timer": "#2f9e44"},
}


def _build_stylesheet(palette: dict) -> str:
    accent = palette["accent"]
    semantic = _SEMANTIC_ACCENTS["light" if palette is PALETTES["light"] else "dark"]
    recording = semantic["recording"]
    recording_hover = semantic["recording_hover"]
    timer = semantic["timer"]
    return f"""
QWidget {{
    background-color: {palette["bg"]};
    color: {palette["text"]};
}}
QLabel#app_heading {{
    color: {accent};
}}
QLabel#status_label {{
    color: {palette["muted"]};
}}
QLabel#duration_label {{
    color: {timer};
}}
QLabel#history_title {{
    color: {accent};
    font-weight: bold;
}}
QPushButton#delete_button:hover {{
    border-color: {recording};
    color: {recording};
}}
QPushButton {{
    background-color: {palette["panel"]};
    color: {palette["text"]};
    border: 1px solid {palette["border"]};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    border-color: {accent};
}}
QPushButton:disabled {{
    color: {palette["muted"]};
    border-color: {palette["border"]};
}}
QPushButton#record_button {{
    background-color: {accent};
    color: #ffffff;
    border: none;
    font-weight: bold;
}}
QPushButton#record_button:hover {{
    background-color: {accent};
}}
QPushButton#record_button[recording="true"] {{
    background-color: {recording};
}}
QPushButton#record_button[recording="true"]:hover {{
    background-color: {recording_hover};
}}
QPlainTextEdit, QLineEdit, QListWidget {{
    background-color: {palette["input"]};
    color: {palette["text"]};
    border: 1px solid {palette["border"]};
    border-radius: 6px;
}}
QListWidget::item {{
    padding: 4px 6px;
}}
QListWidget::item:selected {{
    background-color: {recording};
    color: #ffffff;
}}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 2px solid {palette["border"]};
    background-color: {palette["input"]};
}}
QRadioButton::indicator {{
    border-radius: 8px;
}}
QCheckBox::indicator {{
    border-radius: 3px;
}}
QRadioButton::indicator:checked {{
    border-color: {accent};
    background-color: {accent};
}}
QCheckBox::indicator:checked {{
    border-color: {accent};
    background-color: {accent};
}}
"""


class _TranscriptionWorker(QObject):
    """Run inference off the GUI thread and communicate through Qt signals."""

    completed = Signal(str, object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, transcriber: PersianTranscriber, audio_path: Path,
                 output_dir: Path, auto_save: bool) -> None:
        super().__init__()
        self.transcriber = transcriber
        self.audio_path = audio_path
        self.output_dir = output_dir
        self.auto_save = auto_save

    @Slot()
    def run(self) -> None:
        try:
            result = (self.transcriber.transcribe(self.audio_path) or "").strip()
            saved = save_transcript(self.output_dir, result) if result and self.auto_save else None
            self.completed.emit(result, saved)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            try:
                self.audio_path.unlink(missing_ok=True)
            except OSError:
                pass
            self.finished.emit()


class OrphivoMainWindow(QMainWindow):
    """Main Qt shell for recording, local transcription, and transcript editing."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Orphivo — Persian speech to text")
        self.resize(1050, 680)
        self.setMinimumSize(820, 560)
        self.settings = load_settings()
        self.output_dir = Path(self.settings["output_dir"]).expanduser()
        self.recorder = AudioRecorder()
        self.transcriber = PersianTranscriber()
        self.record_started = 0.0
        self.busy = False
        self._thread: QThread | None = None
        self._worker: _TranscriptionWorker | None = None

        self.apply_theme()

        central = QWidget(self)
        grid = QGridLayout(central)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        # Top-left (column 0): Settings, then the history panel's own
        # title/folder labels - kept in this header row (rather than inside
        # the panel itself) so the panel's list box below starts flush with
        # the transcript editor's top edge in row 1.
        left_column = QVBoxLayout()
        left_column.setSpacing(6)
        self.settings_button = QPushButton("⚙ Settings", central)
        self.settings_button.clicked.connect(self.open_settings)
        left_column.addWidget(self.settings_button)
        left_column.setAlignment(self.settings_button, Qt.AlignmentFlag.AlignLeft)

        self.history_panel = OrphivoHistoryPanel(self.output_dir, central)
        self.history_panel.transcript_selected.connect(self._load_transcript)
        self.history_panel.setMinimumWidth(220)
        left_column.addWidget(self.history_panel.title_label)
        left_column.addWidget(self.history_panel.folder_label)
        grid.addLayout(left_column, 0, 0)

        # Bottom-left: the history panel's list/buttons, same row as the
        # editor so they share the same height via the grid's row stretch,
        # and the same top edge since neither has an in-cell header now.
        grid.addWidget(self.history_panel, 1, 0)

        # Top-middle (column 1): Copy text / Save as, between the history
        # column and the heading column. Row 1 of this column is left empty.
        copy_save_row = QHBoxLayout()
        copy_save_row.setSpacing(10)
        self.copy_button = QPushButton("Copy text", central)
        self.copy_button.clicked.connect(self.copy_text)
        copy_save_row.addWidget(self.copy_button)
        self.save_button = QPushButton("Save as…", central)
        self.save_button.clicked.connect(self.save_as)
        copy_save_row.addWidget(self.save_button)
        # Bottom-aligned so this sits at the same vertical level as the
        # record button, which is the bottom-most item of the heading
        # column's own header stack (right_top, added below).
        grid.addLayout(copy_save_row, 0, 1, Qt.AlignmentFlag.AlignBottom)

        # Top-right: heading, status, and the record button + timer.
        right_top = QVBoxLayout()
        right_top.setSpacing(6)
        heading = self.heading_label = QLabel("گفتار به متن فارسی", central)
        heading.setObjectName("app_heading")
        font = heading.font(); font.setPointSize(20); font.setBold(True)
        heading.setFont(font)
        # AlignAbsolute matters here: Qt auto-detects this label's RTL script
        # content and, per Qt's own documented rule, silently swaps
        # AlignLeft/AlignRight to the opposite visual side for RTL-direction
        # widgets unless AlignAbsolute is also set - without it this label
        # renders flush-left despite requesting AlignRight.
        heading.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignAbsolute
        )
        right_top.addWidget(heading)

        self.status_label = QLabel("Ready — press Start recording", central)
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignAbsolute
        )
        right_top.addWidget(self.status_label)

        record_row = QHBoxLayout()
        # Stretch first, then the button/timer, so the pair hugs the right
        # edge of the window rather than sitting flush against the history
        # panel on the left.
        record_row.addStretch(1)
        self.duration_label = QLabel("00:00", central)
        self.duration_label.setObjectName("duration_label")
        font = self.duration_label.font(); font.setPointSize(12); font.setBold(True)
        self.duration_label.setFont(font)
        record_row.addWidget(self.duration_label)
        self.record_button = QPushButton("● Start recording", central)
        self.record_button.setObjectName("record_button")
        self.record_button.setProperty("recording", False)
        self.record_button.setMinimumHeight(40)
        self.record_button.clicked.connect(self.toggle_recording)
        record_row.addWidget(self.record_button)
        right_top.addLayout(record_row)
        grid.addLayout(right_top, 0, 2)

        # Bottom-right: the transcript editor, same row/height as the
        # history panel.
        self.transcript_editor = QPlainTextEdit(central)
        self.transcript_editor.setObjectName("transcript_editor")
        self.transcript_editor.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        font = self.transcript_editor.font(); font.setPointSize(14)
        self.transcript_editor.setFont(font)
        # See qt_ui.py: alignment alone does not set the bidi base direction,
        # so mixed Persian/English/digit text can render in scrambled order
        # even though it is right-aligned. Set an explicit RTL text direction.
        # AlignAbsolute additionally matters because this widget's own
        # layoutDirection is RightToLeft: per Qt's documented behavior,
        # AlignLeft/AlignRight are otherwise auto-swapped for RTL-direction
        # widgets, which would undo the alignment we just asked for.
        text_option = QTextOption(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        text_option.setTextDirection(Qt.LayoutDirection.RightToLeft)
        self.transcript_editor.document().setDefaultTextOption(text_option)
        self.transcript_editor.setUndoRedoEnabled(True)
        # Spans columns 1-2 in this row so the editor's left edge meets the
        # history panel directly, with no gap left over from the middle
        # column that only has content in row 0.
        grid.addWidget(self.transcript_editor, 1, 1, 1, 2)

        # QPlainTextEdit's built-in placeholderText does not respect the
        # document's text-direction/alignment settings above (a Qt
        # limitation confirmed by direct testing: real typed/transcribed
        # text renders correctly right-aligned, but the placeholder hint
        # renders flush-left regardless). A custom overlay label, with its
        # own explicit RTL direction and AlignAbsolute, is used instead so
        # the empty-state hint matches the RTL layout of real content.
        self._placeholder_label = QLabel(
            "متن پیاده‌سازی‌شده اینجا نمایش داده می‌شود…",
            self.transcript_editor.viewport(),
        )
        self._placeholder_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._placeholder_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignAbsolute
        )
        self._placeholder_label.setWordWrap(True)
        self._placeholder_label.setFont(font)
        _current_palette = PALETTES.get(self.settings.get("theme"), PALETTES["dark"])
        self._placeholder_label.setStyleSheet(
            f"color: {_current_palette['muted']}; background: transparent;"
        )
        placeholder_layout = QVBoxLayout(self.transcript_editor.viewport())
        placeholder_layout.setContentsMargins(4, 4, 4, 4)
        placeholder_layout.addWidget(self._placeholder_label)
        self.transcript_editor.textChanged.connect(self._update_placeholder_visibility)
        self._update_placeholder_visibility()

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        self.setCentralWidget(central)

        self._duration_timer = QTimer(self)
        self._duration_timer.setInterval(250)
        self._duration_timer.timeout.connect(self._update_duration)
        copy_action = QAction("Copy transcript", self)
        copy_action.setShortcut("Ctrl+Shift+C")
        copy_action.triggered.connect(self.copy_text)
        self.addAction(copy_action)
        save_action = QAction("Save transcript as", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_as)
        self.addAction(save_action)

    def _set_recording_button_active(self, active: bool) -> None:
        # Drives the QSS [recording="true"] selector; a dynamic property
        # change needs an explicit re-polish to take visual effect.
        self.record_button.setProperty("recording", active)
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Mirrors the Tkinter app's Enter-to-record shortcut. Unlike
        # Tkinter's single global bind_all (which needed manual toplevel
        # filtering to keep Enter from leaking into the Settings dialog),
        # Qt's keyPressEvent here only ever fires for this window - the
        # Settings dialog is its own top-level widget with its own event
        # handling (and its own default button), so no extra filtering is
        # needed to keep the two from interfering with each other.
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.focusWidget() is self.transcript_editor:
                # Leave Enter as a newline while the transcript editor has
                # focus, instead of toggling recording.
                super().keyPressEvent(event)
                return
            if not self.busy:
                self.toggle_recording()
            event.accept()
            return
        super().keyPressEvent(event)

    def toggle_recording(self) -> None:
        if self.busy:
            return
        if not self.recorder.recording:
            try:
                self.recorder.start()
            except Exception:
                # Avoid exposing backend-specific PortAudio/MME details in the
                # dialog; mirrors the existing Tkinter app's behavior.
                message = (
                    "Could not start recording. Check Windows microphone "
                    "permissions and the selected input device, then try again."
                )
                self.status_label.setText(message)
                QMessageBox.warning(self, "Microphone error", message)
                return
            self.record_started = time.monotonic()
            self.duration_label.setText("00:00")
            self.record_button.setText("■ Stop recording")
            self._set_recording_button_active(True)
            self.status_label.setText("Recording… press Stop to finish")
            self._duration_timer.start()
            return
        self._stop_recording()

    def _update_duration(self) -> None:
        if not self.recorder.recording:
            self._duration_timer.stop(); return
        seconds = max(0, int(time.monotonic() - self.record_started))
        self.duration_label.setText(f"{seconds // 60:02d}:{seconds % 60:02d}")

    def _stop_recording(self) -> None:
        audio_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(prefix="orphivo_", suffix=".wav", delete=False) as handle:
                audio_path = Path(handle.name)
            audio_path.unlink(missing_ok=True)
            self.recorder.stop(audio_path)
        except Exception as exc:
            if audio_path is not None:
                audio_path.unlink(missing_ok=True)
            self._duration_timer.stop()
            self.record_button.setText("● Start recording")
            self._set_recording_button_active(False)
            self.duration_label.setText("00:00")
            self.status_label.setText("Recording failed")
            QMessageBox.warning(self, "Recording error", str(exc))
            return
        self._duration_timer.stop()
        self.record_button.setText("● Start recording")
        self._set_recording_button_active(False)
        self.record_button.setEnabled(False)
        self.busy = True
        self.status_label.setText("Transcribing locally on CPU…")
        thread = QThread(self)
        worker = _TranscriptionWorker(self.transcriber, audio_path, self.output_dir,
                                      bool(self.settings.get("auto_save", True)))
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(self._on_transcription_completed)
        worker.failed.connect(self._on_transcription_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_transcription_thread_finished)
        thread.finished.connect(thread.deleteLater)
        self._thread, self._worker = thread, worker
        thread.start()

    @Slot(str, object)
    def _on_transcription_completed(self, result: str, saved: object) -> None:
        self.transcript_editor.setPlainText(result)
        if not result:
            self.status_label.setText("No speech detected · nothing to save")
        elif isinstance(saved, Path):
            self.status_label.setText(f"Transcription complete · saved to {saved.name}")
            self.history_panel.refresh()
        else:
            self.status_label.setText("Transcription complete · not auto-saved")

    def _update_placeholder_visibility(self) -> None:
        self._placeholder_label.setVisible(not self.transcript_editor.toPlainText())

    def _load_transcript(self, path: Path) -> None:
        try:
            self.transcript_editor.setPlainText(read_transcript(path))
            self.status_label.setText(f"Loaded {path.name}")
        except OSError as exc:
            QMessageBox.critical(self, "Could not open transcript", str(exc))

    @Slot(str)
    def _on_transcription_failed(self, error: str) -> None:
        self.status_label.setText("Transcription failed")
        QMessageBox.critical(self, "Transcription error", error)

    @Slot()
    def _on_transcription_thread_finished(self) -> None:
        self.busy = False
        self.record_button.setEnabled(True)
        self._worker = None
        self._thread = None

    def copy_text(self) -> None:
        text = self.transcript_editor.toPlainText()
        if not text:
            self.status_label.setText("Transcript is empty"); return
        # Clipboard access lives on the application object, not the window -
        # QMainWindow has no clipboard() method.
        QApplication.clipboard().setText(text)
        self.status_label.setText("Transcript copied to clipboard")

    def save_as(self) -> None:
        text = self.transcript_editor.toPlainText().strip()
        if not text:
            self.status_label.setText("Nothing to save"); return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename, _ = QFileDialog.getSaveFileName(self, "Save transcript as",
                                                   str(self.output_dir / "transcript.txt"),
                                                   "Text files (*.txt)")
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        try:
            path.write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc)); return
        self.status_label.setText(f"Saved {path.name}")
        self.history_panel.refresh()

    def _persist_settings(self) -> None:
        self.settings["output_dir"] = str(self.output_dir)
        save_settings(self.settings)

    def apply_theme(self) -> None:
        palette = PALETTES.get(self.settings.get("theme"), PALETTES["dark"])
        self.setStyleSheet(_build_stylesheet(palette))
        # The placeholder label's color is set directly (not through the
        # cascade, since it must stay unaffected by the editor's own text
        # color) so it needs updating here too - but it doesn't exist yet
        # the first time this runs, during __init__.
        placeholder = getattr(self, "_placeholder_label", None)
        if placeholder is not None:
            placeholder.setStyleSheet(f"color: {palette['muted']}; background: transparent;")

    def open_settings(self) -> None:
        dialog = OrphivoSettingsDialog(
            self.output_dir, bool(self.settings.get("auto_save", True)),
            self.settings.get("theme", "dark"), self,
        )
        if dialog.exec() == OrphivoSettingsDialog.DialogCode.Accepted:
            self.output_dir, auto_save, theme = dialog.result_values()
            self.settings["auto_save"] = auto_save
            self.settings["theme"] = theme
            self._persist_settings()
            self.apply_theme()
            self.history_panel.refresh(self.output_dir)
            self.status_label.setText("Settings saved")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._thread is not None and self._thread.isRunning():
            self.status_label.setText("Please wait for transcription to finish before closing.")
            event.ignore(); return
        if self.recorder.recording:
            answer = QMessageBox.question(self, "Recording in progress",
                "Stop recording and close? The current recording will not be transcribed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore(); return
            stream = getattr(self.recorder, "_stream", None)
            try:
                if stream is not None:
                    stream.abort(); stream.close()
            except Exception:
                pass
            self.recorder._stream = None
            self.recorder._recording = False
            self._duration_timer.stop()
        event.accept()
