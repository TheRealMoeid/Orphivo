"""Regression tests for the main-window Enter shortcut."""
from types import SimpleNamespace

from src.ui import PersianSTTApp


class _Widget:
    def __init__(self, toplevel):
        self._toplevel = toplevel

    def winfo_toplevel(self):
        return self._toplevel


class _AppHarness:
    """Small harness to test shortcut dispatch without creating a Tk window."""

    def __init__(self):
        self.transcript = object()
        self.busy = False
        self.toggle_calls = 0
        self.focused_widget = None

    def focus_get(self):
        return self.focused_widget

    def toggle_recording(self):
        self.toggle_calls += 1


def test_enter_from_settings_window_does_not_toggle_recording():
    app = _AppHarness()
    settings_window = object()
    event = SimpleNamespace(widget=_Widget(settings_window))

    result = PersianSTTApp._enter_shortcut(app, event)

    assert result is None
    assert app.toggle_calls == 0


def test_enter_from_main_window_keeps_recording_shortcut():
    app = _AppHarness()
    event = SimpleNamespace(widget=_Widget(app))

    result = PersianSTTApp._enter_shortcut(app, event)

    assert result == "break"
    assert app.toggle_calls == 1


def test_enter_in_transcript_editor_is_left_as_a_newline():
    app = _AppHarness()
    app.focused_widget = app.transcript
    event = SimpleNamespace(widget=_Widget(app))

    result = PersianSTTApp._enter_shortcut(app, event)

    assert result is None
    assert app.toggle_calls == 0


def test_enter_does_not_toggle_recording_while_busy():
    app = _AppHarness()
    app.busy = True
    event = SimpleNamespace(widget=_Widget(app))

    result = PersianSTTApp._enter_shortcut(app, event)

    assert result == "break"
    assert app.toggle_calls == 0