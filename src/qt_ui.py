"""Experimental PySide6 shell for the staged Orphivo UI migration.

This module is intentionally not wired into app.py yet. The existing Tkinter
application remains the production entry point until the Qt workflow has been
integrated and regression-tested.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget


class OrphivoQtWindow(QMainWindow):
    """Minimal Qt window used to validate plain-text Persian editing."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Orphivo — Persian speech to text")
        self.resize(1050, 680)
        self.setMinimumSize(820, 560)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        self.transcript_editor = QPlainTextEdit(central)
        editor_font = self.transcript_editor.font()
        editor_font.setPointSize(14)
        self.transcript_editor.setFont(editor_font)
        self.transcript_editor.setObjectName("transcript_editor")
        self.transcript_editor.setPlaceholderText("متن پیاده‌سازی‌شده اینجا نمایش داده می‌شود…")
        self.transcript_editor.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        # QPlainTextEdit has no setAlignment() method; set paragraph alignment
        # through the document's default text option instead. Alignment alone
        # only controls where the text sits in the widget - it does not set
        # the bidi *base direction* used to order mixed Persian/English/digit
        # runs. Without an explicit RightToLeft text direction, Qt's bidi
        # algorithm auto-detects the base direction from the first strong
        # character, which can treat the whole paragraph as LTR and scramble
        # the visual order of mixed-direction sentences even though they are
        # right-aligned.
        text_option = QTextOption(Qt.AlignmentFlag.AlignRight)
        text_option.setTextDirection(Qt.LayoutDirection.RightToLeft)
        self.transcript_editor.document().setDefaultTextOption(text_option)
        self.transcript_editor.setUndoRedoEnabled(True)
        layout.addWidget(self.transcript_editor)
        self.setCentralWidget(central)
