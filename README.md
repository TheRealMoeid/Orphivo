# Persian STT

A local-first Windows desktop application for transcribing Persian (Farsi) speech into text. The application uses Python, Tkinter, and a locally stored Faster-Whisper model, with CPU INT8 inference as the current supported configuration.

> **Project status:** Early development. The GUI has been launched and a short Persian recording produced a visible transcript and an automatically saved text file. Automated test execution still needs environment/import-path cleanup, and several UI/behavior issues remain to be triaged.

## Features

- Record microphone audio and stop recording from the main window.
- Transcribe Persian speech locally using Faster-Whisper.
- Display the transcript in a Persian-friendly text area.
- Automatically save completed transcripts as timestamped `.txt` files.
- Browse transcript history from the selected output folder.
- Copy transcript text, save a copy elsewhere, open the output folder, and delete saved transcripts.
- Configure the transcript folder and automatic saving.
- Switch between dark and light themes.
- Store preferences locally between launches.

## Privacy and network behavior

Audio transcription is intended to run locally with a model already present on the computer. The app does not need to upload recordings to a hosted transcription service. The model directory is configured in the application and must exist locally.

The app may still depend on locally installed Python packages. Do not describe the application as fully offline until startup and transcription have been verified with network access disabled.

## Requirements

- Windows 10/11
- Python 3.12 (the current development environment uses Python 3.12)
- A working microphone and Windows microphone permission
- The existing Faster-Whisper CTranslate2 model at `D:\whisper-large-fa-v1-ct2`, or a corresponding local path configured in the application
- Project dependencies installed into the same Python environment used to launch the app

The current implementation uses CPU INT8 inference. CUDA/GPU inference is not part of the current setup.

## Setup

Open PowerShell in the project directory:

```powershell
# Activate the project's virtual environment
.\.venv\Scripts\Activate.ps1

# Install runtime dependencies into that environment
python -m pip install -r requirements.txt

# Launch the application
python app.py
```

If the virtual environment has not been created yet:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set the model path to the directory containing the converted Faster-Whisper/CTranslate2 model files. No model download is performed by the app.

## Tests

Install the test runner in the same environment that will run the tests:

```powershell
python -m pip install pytest
python -m pytest tests -v
```

Use `python -m pytest`, rather than a bare `pytest` command, to make it clearer which Python interpreter is running the test suite.

The initial development run exposed two setup issues:
- `.\.venv\Scripts\python.exe -m pytest` reported that `pytest` was not installed in the virtual environment.
- The global `pytest` executable collected tests using the global Python interpreter and could not import `src`.

These are test-environment/import-discovery issues, not evidence that the test assertions themselves failed. Fix and verify them before treating the suite as passing.

## Project layout

```text
.
├── app.py                 # Application entry point
├── src/
│   ├── __init__.py
│   ├── history.py         # Read, save, list, and manage transcript files
│   ├── recorder.py        # Microphone recording
│   ├── settings.py        # Persistent application preferences
│   ├── theme.py           # Dark/light theme definitions
│   ├── transcriber.py     # Faster-Whisper model loading and transcription
│   └── ui.py              # Tkinter application and windows
├── tests/
│   ├── test_history.py
│   └── test_settings.py
├── test_persian_stt.py    # Existing manual/model test; preserve
├── test_gpu.py            # Existing GPU diagnostic; preserve
└── persian_test.wav       # Existing sample recording; preserve
```

Some files in the tree may be added or changed during development. Update this section when the repository structure changes.

## Known limitations

See [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) for the current issue register. Use GitHub Issues as the source of truth for active work, priorities, reproduction steps, and resolution status.

## Issue tracking

Please report bugs and propose improvements through the repository's **GitHub Issues** tab. Include:
- Windows version and Python version
- Steps to reproduce
- Expected behavior and actual behavior
- Relevant terminal output or traceback
- Whether the issue occurs with the CPU configuration

Do not attach private recordings or sensitive transcripts unless you have checked their contents and intentionally chosen to share them.

## Development workflow

1. Read the existing documentation and open GitHub Issues before starting work.
2. Reproduce the issue and record the expected/actual behavior.
3. Discuss the proposed fix and its risks before implementation when the change affects architecture or user-visible behavior.
4. Make one focused change per issue and add/update tests.
5. Run the tests using the project virtual environment.
6. Update documentation and close the issue only after verification.

## License

No license has been selected yet. Until one is added, do not assume that the repository grants permission to reuse, modify, or redistribute its code.
