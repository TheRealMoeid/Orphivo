# Orphivo — Persian Speech-to-Text

Orphivo is a local-first Windows desktop application for transcribing Persian (Farsi) speech into text using a locally stored Faster-Whisper model.

The project aims to provide offline transcription, editable transcripts, automatic saving, and transcript history without relying on paid cloud transcription APIs.

> **Development status — November 8, 2026**
>
> The project is currently undergoing a migration from Tkinter to PySide6. The new Qt main window has been implemented and its automated tests pass, but it has not yet been manually launched or tested end to end.
>
> The existing `app.py` entry point still launches the Tkinter application. The PySide6 implementation is separate and is not yet the production application.

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

### In-progress PySide6 implementation

The current Qt implementation includes:

- A Persian-friendly text editor.
- Right-aligned text with a 14 pt font.
- Recording controls and elapsed recording duration.
- Background transcription using Qt threading.
- Automatic saving of non-empty transcription results.
- Copy and Save As actions.

The Qt implementation is still incomplete. Feature parity with the existing Tkinter application has not been established.

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

### Experimental PySide6 application

The new Qt main window can be launched separately using:

```powershell
python -c "from PySide6.QtWidgets import QApplication; from src.qt_main_window import OrphivoMainWindow; app = QApplication([]); window = OrphivoMainWindow(); window.show(); app.exec()"
```

**Important:** This command has not yet been manually tested by the user. Real microphone recording, transcription, saving, and shutdown behavior through the Qt window remain unverified.

Do not replace the existing `app.py` entry point until the Qt implementation has been manually tested and the remaining migration requirements have been reviewed.

## Running Tests

Run the test suite from the repository root:

```powershell
python -m pytest tests -v
```

### Latest test result

\<text>**Date:** November 8, 2026\</text>

\<text>**Environment:** Windows, Python 3.12.10, pytest 9.1.1\</text>

\<text>**Result:** 23 passed in 0.77 seconds.\</text>

The reported test run includes the Qt main-window tests and the existing application tests.

Passing automated tests do not establish that the Qt interface works correctly with a real microphone, the local model, or the complete application workflow. Manual verification is still required.

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
| Qt automated tests                  | Passing                 |
| Manual Qt launch and smoke test     | Not performed           |
| Complete Qt feature parity          | Not established         |
| `app.py` switched to Qt             | Not done                |

## Development Guidelines

- Keep transcription local; do not introduce hosted transcription APIs without an explicit change in project requirements.
- Preserve the existing local model and CPU INT8 configuration unless a dedicated task requires otherwise.
- Keep transcript files in ordinary UTF-8 text format.
- Avoid introducing a database without a documented requirement.
- Preserve existing functionality during the UI migration.
- Verify behavior on Windows, especially microphone recording and Persian text editing.
- Keep changes focused on one issue or task per branch.
