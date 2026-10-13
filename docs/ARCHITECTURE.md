# Architecture

## Overview

Persian STT is a local Windows desktop application. The current implementation is organized into a Tkinter user interface and small modules for recording, transcription, preferences, theme configuration, and transcript-file management.

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `app.py` | Application entry point; creates and runs the main Tkinter app. |
| `src/ui.py` | Main window, settings window, user actions, status display, transcript editor, and history interaction. |
| `src/recorder.py` | Captures microphone audio and produces audio suitable for transcription. |
| `src/transcriber.py` | Loads the existing local Faster-Whisper model and runs Persian transcription. |
| `src/history.py` | Saves, lists, reads, and deletes timestamped transcript files. |
| `src/settings.py` | Loads and saves persistent preferences. |
| `src/theme.py` | Defines the visual tokens/styles for supported themes. |

## Data flow

1. The user starts a recording from the main window.
2. The recorder captures microphone audio.
3. The user stops the recording.
4. The transcriber processes the recorded audio using the local model and CPU INT8 inference.
5. The UI displays the resulting Persian text and a completion/error status.
6. When automatic saving is enabled, the transcript is written to the configured folder.
7. The history panel enumerates `.txt` files in that folder and loads a selected transcript on request.

## Persistence

- **Transcript content:** timestamped `.txt` files in the user-selected folder.
- **Preferences:** a local configuration file managed by `src/settings.py`.
- **History index:** derived from the contents of the selected folder; no database is required for the current design.

The output folder is user-configurable. Changing it should not move or delete transcripts in the previous folder.

## Runtime and threading

Audio capture and model inference can take time and should not block Tkinter's event loop. Long-running work should execute in a worker thread, with UI changes scheduled safely on the Tkinter main thread. Do not call Tkinter widget methods directly from a worker thread.

## Model and compute configuration

- Model: existing local Faster-Whisper/CTranslate2 model.
- Language: Persian (`fa`).
- Current compute target: CPU, INT8.
- CUDA is intentionally not required by the current setup.
- Model files should not be downloaded or replaced automatically.

## Design constraints

- Preserve existing diagnostic scripts and sample audio unless a dedicated issue explicitly changes that requirement.
- Keep user transcripts as ordinary text files to make them easy to inspect and back up.
- Do not add a database unless a documented requirement makes file-based history insufficient.
- Keep model configuration and persistent preferences out of source-controlled secrets or machine-specific transient files.
- Add tests around file operations and settings; manually verify real microphone and model behavior on Windows.
