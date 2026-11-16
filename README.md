# Orphivo — Persian Speech-to-Text

Orphivo is a local-first Windows desktop application for transcribing Persian (Farsi) speech into text using a locally stored Faster-Whisper model.

The project aims to provide offline transcription, editable transcripts, automatic saving, and transcript history without relying on paid cloud transcription APIs.

> **Development status — November 16, 2026**
>
> The project is undergoing a migration from Tkinter to PySide6. The Qt main window has been manually launched and its core workflow — recording, local transcription, automatic saving, silence handling, copy/save actions, microphone-error handling, and close behavior during active recording or transcription — has been manually verified on Windows.
>
> All four previously identified feature-parity gaps are implemented and manually verified: an in-window Settings dialog (output folder, auto-save, and theme), a transcript history panel (list, open folder, delete, click-to-load), dark/light theme switching, and the Enter-key recording shortcut.
>
> **All three secondary verification items are now closed as well:** closing the app while completely idle (clean, no issues), UI responsiveness during a long inference run (confirmed via a real ~7m14s recording / ~4min transcription, with CPU/memory logging showing the window stayed interactive throughout), and manually triggering a transcription failure against the real model (two distinct real failures reproduced — a missing model directory and a corrupted model file — both surfaced a readable error dialog and the app returned to a normal, usable state afterward).
>
> During the long-inference test, a real bug was found and fixed: clicking Copy, Save As, loading a transcript from history, or saving Settings while a transcription was still running would briefly show the right confirmation message, then have it silently overwritten when the transcription finished. This is fixed — those actions now show their confirmation for a few seconds before correctly reverting to whatever the real state actually is, and the buttons were deliberately kept enabled throughout rather than disabled during busy state. A related UX improvement was made at the same time: the record button now reads "Transcribing…" with its own muted styling while busy, instead of just going an unreadable, unexplained gray.
>
> The existing `app.py` entry point still launches the Tkinter application. The PySide6 implementation is separate and is not yet the production application. With migration and all verification now complete, the `app.py` entry-point switch is the next planned task, to be scoped and approved separately.

## Features

### Existing Tkinter application

The established application includes:

- Microphone recording.
- Local Persian speech-to-text transcription.
- Editable transcript display.
- Automatic transcript saving.
- Transcript history.
- Persistent application settings.
- Dark and light themes.
- Keyboard shortcuts.

### PySide6 implementation

The current Qt implementation includes:

- A Persian-friendly text editor with correct RTL/bidi rendering for mixed Persian/English/digit text.
- Right-aligned text with a 14 pt font.
- Recording controls and elapsed recording duration, with an Enter-key shortcut to start/stop (scoped so it doesn't fire while the transcript editor has focus, or while busy).
- Background transcription using Qt threading, with the record button showing "Transcribing…" and a muted disabled style while busy, so the busy state is visually clear rather than looking like an unresponsive button.
- Automatic saving of non-empty transcription results.
- Copy and Save As actions, usable at any time (including during an active transcription) — their confirmation messages display briefly, then correctly revert to whatever the real state is (idle, recording, or transcribing).
- An in-window Settings dialog: transcript folder, auto-save toggle, and dark/light theme, with the Save button disabled until something actually changes.
- A transcript history panel: lists saved transcripts, opens the folder, deletes with confirmation, and loads a transcript on click.
- Dark/light theme switching, applied live and persisted.

The four feature-parity gaps previously tracked here (theme, settings dialog, history panel, Enter shortcut) are closed and manually verified. The three secondary verification items (idle-state close, long-inference responsiveness, real transcription-failure handling) are also closed and manually verified — see `docs/KNOWN_ISSUES.md` for the full record.

## Technology Stack

- **Language:** Python
- **Desktop UI:** Tkinter (existing application), PySide6 (migration)
- **Speech recognition:** Faster-Whisper
- **Inference backend:** CTranslate2
- **Audio recording:** sounddevice
- **Transcription language:** Persian (`fa`)
- **Compute configuration:** CPU INT8
- **Transcript format:** UTF-8 `.txt`
- **Settings storage:** JSON

## Local Model

Orphivo uses a locally stored Faster-Whisper/CTranslate2 model.

The development environment has used this model directory:

```text
D:\whisper-large-fa-v1-ct2
```

The model is expected to be available locally. The application is not intended to download a replacement model automatically.

The current verified development configuration uses CPU INT8 inference. CUDA/GPU inference is not part of the established configuration.

## Repository Structure

```text
Orphivo/
│
├── app.py
├── requirements.txt
│
├── src/
│   ├── ui.py
│   ├── qt_ui.py
│   ├── qt_main_window.py
│   ├── qt_settings_dialog.py
│   ├── qt_history_panel.py
│   ├── recorder.py
│   ├── transcriber.py
│   ├── history.py
│   ├── settings.py
│   └── theme.py
│
├── tests/
│   ├── test_history.py
│   ├── test_qt_ui.py
│   ├── test_qt_main_window.py
│   ├── test_qt_settings_dialog.py
│   ├── test_qt_history_panel.py
│   ├── test_qt_status_revert.py
│   ├── test_recorder.py
│   ├── test_settings.py
│   ├── test_ui_shortcuts.py
│   ├── test_ui_status.py
│   └── test_ui_worker.py
│
└── docs/
    ├── ARCHITECTURE.md
    └── KNOWN_ISSUES.md
```

This is an overview of the relevant project files, not a guarantee that it lists every file in the repository.

## Installation

The development environment used for the latest reported test run:

- Windows
- Python 3.12.10
- pytest 9.1.1
- Project virtual environment

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Make sure the local Faster-Whisper model is available and that the configured model directory is correct.

## Running the Application

### Existing Tkinter application

The current application entry point remains:

```powershell
python app.py
```

This launches the existing Tkinter implementation.

### PySide6 application

The Qt main window can be launched separately using:

```powershell
python -c "from PySide6.QtWidgets import QApplication; from src.qt_main_window import OrphivoMainWindow; app = QApplication([]); window = OrphivoMainWindow(); window.show(); app.exec()"
```

**Status:** This command has been manually run by the user repeatedly across several verification rounds. Real microphone recording, local-model transcription, automatic saving, copy/save actions, microphone-error handling, shutdown behavior during active recording/transcription, idle-state shutdown, long-inference responsiveness, and real transcription-failure handling have all been manually verified. Feature parity with the Tkinter application (theme, settings, history, Enter shortcut) is established.

The `app.py` entry-point switch has not yet been made; it is the next planned task.

## Running Tests

Run the test suite from the repository root:

```powershell
python -m pytest tests -v
```

### Latest test result

\<text>**Date:** November 16, 2026\</text>

\<text>**Environment:** Windows, Python 3.12.10, pytest 9.1.1\</text>

\<text>**Result:** 60 passed.\</text>

The reported test run includes regression tests for the status-message revert behavior (added this round) alongside the Qt main-window, settings-dialog, history-panel, and existing Tkinter application tests.

Passing automated tests, together with the manual verification recorded in `docs/KNOWN_ISSUES.md`, establish that the Qt interface's core workflow, settings, history, theme switching, Enter shortcut, idle-close, long-inference responsiveness, and real transcription-failure handling all work correctly.

## Development Status

The current UI migration is tracked in:

[Issue #12 — Migrate desktop interface from Tkinter to PySide6](https://github.com/TheRealMoeid/Orphivo/issues/12)

The latest reported development branch is:

```text
feature/pyside6-ui-migration
```

The migration currently has these boundaries:

| Component                           | Status                  |
| ----------------------------------- | ----------------------- |
| Existing Tkinter application        | Existing implementation |
| PySide6 RTL/editor proof of concept | Implemented             |
| PySide6 main-window shell           | Implemented             |
| Qt automated tests                  | Passing (60)            |
| Manual Qt launch and smoke test     | Done                    |
| Qt core workflow (record/transcribe/save/errors/close) | Manually verified |
| Settings dialog, history panel, theme, Enter shortcut | Implemented and manually verified |
| Idle close / long-inference responsiveness / real transcription-failure handling | Manually verified |
| `app.py` switched to Qt             | Not done — next planned task |

## Development Guidelines

- Keep transcription local; do not introduce hosted transcription APIs without an explicit change in project requirements.
- Preserve the existing local model and CPU INT8 configuration unless a dedicated task requires otherwise.
- Keep transcript files in ordinary UTF-8 text format.
- Avoid introducing a database without a documented requirement.
- Preserve existing functionality during the UI migration.
- Verify behavior on Windows, especially microphone recording and Persian text editing.
- Keep changes focused on one issue or task per branch.
