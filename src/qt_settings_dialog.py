"""PySide6 settings dialog: output folder, auto-save, and theme.

Kept in its own module, separate from qt_main_window.py, so Qt feature
work can grow independently without this file becoming a dumping ground.
Reuses src/settings.py and src/theme.py directly rather than introducing
a second settings/theme system for the Qt UI.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QRadioButton, QVBoxLayout,
)


class OrphivoSettingsDialog(QDialog):
    """Modal dialog for the transcript folder, auto-save, and theme."""

    def __init__(
        self, output_dir: Path, auto_save: bool, theme: str, parent=None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(420)

        self._result_output_dir: Path | None = None
        self._result_auto_save: bool | None = None
        self._result_theme: str | None = None

        # Snapshot of the values this dialog was opened with, so Save can
        # stay disabled until something actually changes.
        self._initial_output_dir = str(output_dir)
        self._initial_auto_save = auto_save
        self._initial_theme = theme

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Transcript folder", self))
        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(str(output_dir), self)
        folder_row.addWidget(self.folder_edit, 1)
        browse_button = QPushButton("Browse…", self)
        browse_button.clicked.connect(self._pick_folder)
        folder_row.addWidget(browse_button)
        layout.addLayout(folder_row)

        self.auto_save_checkbox = QCheckBox(
            "Automatically save each completed transcript", self
        )
        self.auto_save_checkbox.setChecked(auto_save)
        layout.addWidget(self.auto_save_checkbox)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme:", self))
        self.dark_radio = QRadioButton("Dark", self)
        self.light_radio = QRadioButton("Light", self)
        self._theme_group = QButtonGroup(self)
        self._theme_group.addButton(self.dark_radio)
        self._theme_group.addButton(self.light_radio)
        (self.light_radio if theme == "light" else self.dark_radio).setChecked(True)
        theme_row.addWidget(self.dark_radio)
        theme_row.addWidget(self.light_radio)
        theme_row.addStretch(1)
        layout.addLayout(theme_row)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)
        button_row.addWidget(cancel_button)
        self.save_button = QPushButton("Save settings", self)
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._on_save)
        button_row.addWidget(self.save_button)
        layout.addLayout(button_row)

        # Save stays disabled until something actually differs from the
        # values this dialog was opened with.
        self.folder_edit.textChanged.connect(self._update_save_enabled)
        self.auto_save_checkbox.toggled.connect(self._update_save_enabled)
        self.dark_radio.toggled.connect(self._update_save_enabled)
        self.light_radio.toggled.connect(self._update_save_enabled)
        self._update_save_enabled()

    def _update_save_enabled(self) -> None:
        current_theme = "light" if self.light_radio.isChecked() else "dark"
        changed = (
            self.folder_edit.text() != self._initial_output_dir
            or self.auto_save_checkbox.isChecked() != self._initial_auto_save
            or current_theme != self._initial_theme
        )
        self.save_button.setEnabled(changed)

    def _pick_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose transcript folder", self.folder_edit.text()
        )
        if chosen:
            self.folder_edit.setText(chosen)

    def _on_save(self) -> None:
        text = self.folder_edit.text().strip()
        if not text:
            QMessageBox.critical(self, "Invalid folder", "Choose a transcript folder.")
            return
        chosen = Path(text).expanduser()
        try:
            chosen.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "Folder error", str(exc))
            return
        self._result_output_dir = chosen
        self._result_auto_save = self.auto_save_checkbox.isChecked()
        self._result_theme = "light" if self.light_radio.isChecked() else "dark"
        self.accept()

    def result_values(self) -> tuple[Path, bool, str]:
        """Return the chosen (output_dir, auto_save, theme) after accept()."""
        assert self._result_output_dir is not None
        assert self._result_auto_save is not None
        assert self._result_theme is not None
        return self._result_output_dir, self._result_auto_save, self._result_theme
