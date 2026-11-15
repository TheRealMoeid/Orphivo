"""PySide6 transcript history panel: list, open, select, and delete.

Kept in its own module, separate from qt_main_window.py, matching the
qt_settings_dialog.py pattern so Qt feature work stays independently
reviewable and growable.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from .history import list_transcripts


class OrphivoHistoryPanel(QWidget):
    """Sidebar listing saved transcripts for a folder.

    Emits transcript_selected(Path) when the user picks an item, rather
    than reaching into the main window's editor directly, so this panel
    stays independent of how its content is displayed.
    """

    transcript_selected = Signal(Path)

    def __init__(self, output_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.output_dir = output_dir
        self._files: list[Path] = []

        self.setFixedWidth(250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # title_label/folder_label are constructed here (and kept in sync by
        # refresh() below) but deliberately not added to this widget's own
        # layout. The main window places them above this panel, in the same
        # header row as its own heading/status, so the panel's list box
        # starts flush with the transcript editor's top edge instead of
        # being pushed down by an in-panel header.
        self.title_label = QLabel("Transcript history", self)
        self.title_label.setObjectName("history_title")
        self.folder_label = QLabel(str(output_dir), self)
        self.folder_label.setWordWrap(True)

        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget, 1)

        actions = QHBoxLayout()
        self.open_folder_button = QPushButton("Open folder", self)
        self.open_folder_button.clicked.connect(self.open_output_folder)
        actions.addWidget(self.open_folder_button)
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.setObjectName("delete_button")
        self.delete_button.clicked.connect(self.delete_selected)
        actions.addWidget(self.delete_button)
        layout.addLayout(actions)

        self.refresh(output_dir)

    def refresh(self, output_dir: Path | None = None) -> None:
        if output_dir is not None:
            self.output_dir = output_dir
            self.folder_label.setText(str(output_dir))
        self._files = list_transcripts(self.output_dir)
        self.list_widget.clear()
        for path in self._files:
            self.list_widget.addItem(QListWidgetItem(path.stem))

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        index = self.list_widget.row(item)
        if 0 <= index < len(self._files):
            self.transcript_selected.emit(self._files[index])

    def open_output_folder(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(self.output_dir))
            else:
                subprocess.Popen(["xdg-open", str(self.output_dir)])
        except Exception as exc:
            QMessageBox.critical(self, "Could not open folder", str(exc))

    def delete_selected(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        index = self.list_widget.row(item)
        if not (0 <= index < len(self._files)):
            return
        path = self._files[index]
        answer = QMessageBox.question(
            self, "Delete transcript", f"Permanently delete {path.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            path.unlink()
            self.refresh()
        except OSError as exc:
            QMessageBox.critical(self, "Delete failed", str(exc))
