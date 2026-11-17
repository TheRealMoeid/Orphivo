from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from src.qt_ui import OrphivoQtWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_qt_window_uses_editable_plain_text_editor(qapp):
    window = OrphivoQtWindow()
    editor = window.transcript_editor

    assert isinstance(editor, QPlainTextEdit)
    assert editor.isReadOnly() is False
    assert editor.font().pointSize() == 14
    assert editor.layoutDirection() == Qt.LayoutDirection.RightToLeft
    assert (
        editor.document().defaultTextOption().alignment()
        == Qt.AlignmentFlag.AlignRight
    )
    assert (
        editor.document().defaultTextOption().textDirection()
        == Qt.LayoutDirection.RightToLeft
    )
    window.close()


def test_qt_editor_preserves_persian_and_mixed_text_content(qapp):
    window = OrphivoQtWindow()
    expected = "سلام Orphivo 2.5 — transcription با Faster-Whisper"

    window.transcript_editor.setPlainText(expected)

    assert window.transcript_editor.toPlainText() == expected
    window.close()
