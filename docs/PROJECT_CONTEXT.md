# Orphivo — Project Context and Handoff

> Purpose: provide a source-grounded reference for future development sessions. This document describes the repository state inspected on 2026-10-13. Re-check GitHub and the working tree before relying on branch names, issue states, or test results, because they can change.

## 1. Project Overview

Orphivo is a local-first Windows desktop application for transcribing Persian (Farsi) speech into text. It uses a local Faster-Whisper/CTranslate2 model and currently configures inference for CPU INT8. The intended use is private, on-device speech transcription without sending audio to a hosted transcription service.

### Current user-facing functionality in the code

- Start and stop microphone recording from the main Tkinter window.
- Capture mono, 16 kHz, signed 16-bit PCM audio through `sounddevice`.
- Transcribe audio in Persian (`fa`) using the configured local model.
- Display the resulting text in the application.
- Automatically save non-empty results as timestamped UTF-8 `.txt` files when auto-save is enabled.
- Browse, open, copy, save, and delete transcript files.
- Select a transcript output folder and configure auto-save.
- Switch between dark and light themes.
- Persist theme, output directory, and auto-save preferences in a local JSON settings file.

These are implemented code paths, not a claim that every path has been exhaustively tested. The README records one successful initial GUI run in which a short Persian recording produced visible text and a saved transcript. Comprehensive end-to-end verification remains open.

## 2. Technology Stack and Runtime

- **Language:** Python; the development environment has been Python 3.12.
- **GUI:** Tkinter and ttk from Python's standard library.
- **Audio capture:** `sounddevice==0.5.6`.
- **Audio arrays:** NumPy (`numpy>=2.0` in `requirements.txt`).
- **Speech recognition:** `faster-whisper==1.2.1`, using CTranslate2 and a model already stored locally.
- **Persistence:** JSON for preferences and ordinary UTF-8 text files for transcript history; there is no database.
- **Tests:** pytest is documented as the runner, but it is not included in the current runtime `requirements.txt`; test setup is tracked in Issue #1.

### Model and compute constraints

- Default model path in code: `D:\whisper-large-fa-v1-ct2`.
- `src/transcriber.py` loads `WhisperModel` with `device="cpu"` and `compute_type="int8"`.
- Transcription uses `language="fa"`, `beam_size=5`, and `vad_filter=True`.
- Do not install CUDA, change to GPU inference, download a replacement model, or change the model architecture as part of the current issue plan.
- The model path is machine-specific and must exist locally or be adjusted in application settings/configuration code. The app does not download model files.
- Do not claim fully offline startup has been verified with networking disabled. Local inference is the intended design, but offline behavior has not been comprehensively tested.

## 3. Repository Structure

```text
.
├── .gitignore
├── README.md
├── PROJECT_CONTEXT.md          # This handoff document
├── app.py                      # Application entry point
├── requirements.txt            # Runtime dependencies
├── docs/
│   ├── ARCHITECTURE.md          # Module responsibilities and data flow
│   └── KNOWN_ISSUES.md          # Observed issues and verification notes
├── src/
│   ├── __init__.py
│   ├── ui.py                    # Tkinter windows and user interactions
│   ├── recorder.py              # Microphone capture and WAV output
│   ├── transcriber.py           # Local Faster-Whisper model wrapper
│   ├── history.py               # Transcript file read/write/list operations
│   ├── settings.py              # Preferences and default paths
│   └── theme.py                 # Dark/light color palettes
├── tests/
│   ├── test_history.py
│   └── test_settings.py
├── test_persian_stt.py          # Manual microphone/model smoke test
└── test_gpu.py                  # GPU diagnostic with CPU fallback
```

`.gitignore` excludes virtual environments, Python caches, local settings/secrets, model weight files, transcript/recording output, the sample WAV, patch files, and common IDE/OS artifacts. The repository currently has no license file; the README correctly says no license has been selected.

## 4. Architecture and Data Flow

1. `app.py` instantiates `PersianSTTApp` from `src/ui.py` and starts Tkinter's event loop.
2. The UI asks `AudioRecorder` to capture microphone audio.
3. `src/recorder.py` collects audio callbacks, concatenates frames, and writes mono 16 kHz 16-bit PCM WAV data to a temporary file when recording stops.
4. The UI starts a daemon worker thread for transcription. `PersianTranscriber` lazily loads the configured local model and transcribes the temporary WAV on CPU.
5. The worker posts success/error events to a queue. The Tkinter main thread polls that queue and updates the UI.
6. On a successful, non-empty result, auto-save (if enabled) writes a timestamped text file using `src/history.py`.
7. The history list is derived from `.txt` files in the selected output folder.
8. `src/settings.py` reads/writes preferences as JSON. `src/theme.py` provides dark and light palettes.

### Persistence details

- Transcript files are ordinary `.txt` files; history is discovered from the output folder rather than a database.
- Default transcript directory: `~/Documents/Persian Transcripts`.
- Settings path is `%APPDATA%\PersianSTT\settings.json` on Windows (or the fallback AppData path under the home directory).
- `APP_NAME = "PersianSTT"` is currently used for the settings directory. Do not rename it casually: existing users may have settings stored there. Any migration must preserve or explicitly migrate existing preferences.
- Changing the output directory does not move transcripts from the previous folder.

## 5. Current Project State

### Repository facts verified on 2026-10-13

- Public GitHub repository: https://github.com/TheRealMoeid/Orphivo
- Default branch: `main`.
- GitHub showed one commit: `Initial commit: Orphivo Persian speech-to-text app`.
- GitHub branch listing showed only `main` at the time of inspection. A local branch is not visible on GitHub until it is pushed.
- No pull requests were listed.
- Four GitHub Issues exist and were open at inspection time; see Section 6.

### Implemented but not fully verified

- Main Tkinter application and settings window.
- Microphone recording, temporary WAV creation, local CPU transcription, and result display.
- Automatic transcript saving and file-based history operations.
- Copy/save/delete/open-folder controls.
- Dark/light theme switching and JSON preferences.
- Unit tests for transcript file operations and settings validation/round-trip behavior.

The README reports that a short Persian recording was manually tested and produced a visible transcript and saved text file. This is a limited smoke-test observation, not a comprehensive acceptance test.

### Verification status

- **Automated tests:** six test functions are present in `tests/` (three history tests and three settings tests). A passing run has not been established. The virtual environment previously lacked pytest, and a global pytest invocation failed collection because `src` could not be imported.
- **End-to-end recording/transcription:** partial manual smoke-test evidence exists; failure cases, long recordings, accuracy, and responsiveness remain to be verified.
- **UI and RTL behavior:** the interface includes a right-aligned text tag for transcript content, but the full layout, mixed-direction text, focus, and resizing behavior have not been systematically reviewed.
- **GPU diagnostic:** `test_gpu.py` attempts CUDA and then CPU fallback. It is a diagnostic script, not evidence that GPU support is required or currently working.
- **License:** not selected; do not assume reuse or redistribution permission.

## 6. GitHub Issues and Work Order

All four issues below were verified as **open** on 2026-10-13. GitHub is the source of truth for their current status and full descriptions.

### Issue #1 — [Setup] Make the test suite runnable in a clean virtual environment

URL: https://github.com/TheRealMoeid/Orphivo/issues/1

Goal: establish reproducible test dependencies, investigate test import discovery, document a command that runs from the repository root, and record actual results.

Key acceptance criteria: clean virtual-environment setup; tests collect without import errors; suite runs or genuine failing tests are documented; no CUDA or inference changes.

**Recommended first issue.** A reliable test baseline is needed before changes to the application can be evaluated safely.

### Issue #2 — [Verification] Test microphone recording and transcription end to end

URL: https://github.com/TheRealMoeid/Orphivo/issues/2

Goal: verify recording start/stop, local model invocation, UI result display, microphone permission/device failures, empty/silent audio, missing model, error handling, and responsiveness. Add automated tests for reproducible defects where practical.

This is a verification task, not proof that the core workflow is broken. Keep CPU-only inference and avoid requiring a real microphone in automated tests.

### Issue #3 — [UI] Review layout, focus, and Persian RTL behavior

URL: https://github.com/TheRealMoeid/Orphivo/issues/3

Goal: review Persian and mixed-direction text, fonts, layout at different sizes, keyboard focus, settings-window behavior, and readability of long transcripts. Record reproduction steps and prioritize confirmed usability issues.

This is a review task; do not assume the settings window overlap or any other visual observation is a defect without checking intended behavior.

### Issue #4 — [Docs] Standardize project naming on Orphivo

URL: https://github.com/TheRealMoeid/Orphivo/issues/4

Goal: standardize README/documentation and appropriate user-facing names while preserving useful technical descriptions. Avoid unnecessary changes to persisted paths/configuration.

The documentation title mismatch is visible in the current repository. Application-title and settings-directory changes touch Python code and should be considered separately from documentation-only edits.

### Dependencies and recommended order

1. **Issue #1:** establish a dependable test command and baseline.
2. **Issue #2:** validate the core audio/transcription flow and create tests for confirmed defects.
3. **Issue #3:** review UI/RTL behavior and fix only reproducible issues.
4. **Issue #4:** finish remaining naming/documentation consistency after the code and user-facing behavior have been inspected.

Issue #4 can be partially addressed as a documentation-only change without waiting for the other issues, but application identifiers and settings migration should not be changed casually.

## 7. Known Bugs, Limitations, and Technical Debt

### Confirmed setup/documentation gaps

- `requirements.txt` currently lists only `faster-whisper==1.2.1`, `sounddevice==0.5.6`, and `numpy>=2.0`. It does not include pytest.
- Earlier evidence recorded in `README.md` and `docs/KNOWN_ISSUES.md`: pytest was absent from `.venv`; a global pytest command failed test collection with `ModuleNotFoundError: No module named 'src'`. Re-run with the intended virtual environment before choosing the fix.
- Naming is inconsistent between the GitHub repository name and existing README/application/settings identifiers.

### Unverified behavior / areas to investigate

- Microphone start/stop and error paths, empty audio, invalid model path, autosave failures, and longer recordings.
- UI responsiveness during CPU inference and shutdown while a worker is active.
- Persian RTL behavior, punctuation, mixed Persian/English content, layout at smaller sizes, keyboard focus, and settings-dialog usability.
- Whether the application launches and transcribes with network access disabled.
- Transcription accuracy and latency on representative Persian audio.

### Code-level observations to consider during relevant issues

- The UI reads settings into `self.settings` and the worker reads `self.settings` and `self.output_dir`; avoid unrelated concurrency refactors unless testing reveals a problem.
- The recording callback ignores non-empty PortAudio status values except for a comment. Verify whether user-visible diagnostics are needed.
- `src/recorder.py` creates a WAV only after frames have been collected; the UI displays an error for an empty capture. Verify cleanup and UI state in failure paths.
- `src/history.py` uses timestamp-based filenames and suffixes to avoid collisions; transcript history is folder-based.
- `src/settings.py` writes a temporary file and replaces the target, but broader persistence/error scenarios are not exhaustively tested.
- `test_gpu.py` is a standalone CUDA diagnostic with CPU fallback, despite the supported app configuration being CPU-only. Preserve it unless an explicit issue changes that requirement.

These observations are investigation notes, not automatically confirmed bugs.

## 8. Development Workflow and Git

### Branching

- Keep `main` as the stable integration branch.
- Work on one issue per branch, created from the latest `main`.
- Recommended branch names:
  - `issue/1-test-environment`
  - `issue/2-recording-transcription`
  - `issue/3-ui-rtl-review`
  - `issue/4-orphivo-naming-docs`
- Create the next branch from updated `main` after previous work is merged; do not create all branches from stale code.
- A local branch does not appear in the GitHub branch list until pushed.

### PowerShell commands for Issue #1

Run from the repository directory:

```powershell
cd D:\AI\Orphivo
git status
git switch main
git pull origin main
git switch -c issue/1-test-environment
git status
```

If the branch already exists locally, use `git switch issue/1-test-environment` instead of creating it again. Inspect any uncommitted changes before switching or pulling; do not discard work blindly.

### Testing

Use the same Python interpreter for dependency installation and tests. Once Issue #1 establishes the canonical command, document it here and in the README. The currently documented manual command is:

```powershell
python -m pip install pytest
python -m pytest tests -v
```

This command is a temporary documented workaround, not a verified clean-environment solution. The project should settle on a declared development-dependency approach as part of Issue #1. Do not report the tests as passing until the command has actually run successfully.

Manual microphone/model checks must be performed on the target Windows environment. Avoid depending on a real microphone or the large local model in ordinary unit tests.

### Preferred issue-resolution workflow

1. Inspect existing documentation and relevant code before proposing a change.
2. Identify the root cause and separate verified defects from hypotheses.
3. Compare viable approaches with pros/cons, affected files, risks, and compatibility implications.
4. Recommend an approach and wait for approval before implementation.
5. Prepare a `.patch` file, tests where applicable, and expected results.
6. The developer applies the patch locally, runs tests, and reports results.
7. Review the results, update docs, and close the GitHub issue only after verification.

Do not modify the user's working branch directly or skip the design/approval stage. Fix one issue at a time. Keep changes focused and avoid unrelated refactors.

## 9. Documentation and Handoff Notes

- `README.md` is the entry point for users: setup, requirements, features, test instructions, issue reporting, and license status.
- `docs/ARCHITECTURE.md` describes module boundaries, data flow, persistence, runtime/threading, and design constraints.
- `docs/KNOWN_ISSUES.md` is a concise register of observed issues and verification notes; link active work to GitHub Issues rather than treating this file as the issue tracker.
- This file is the detailed development handoff and should be updated when architecture, dependencies, issue order, or verified project status changes.
- Preserve `test_persian_stt.py`, `test_gpu.py`, and the ignored local `persian_test.wav` unless a dedicated decision changes their role.
- Do not add a database unless a demonstrated requirement makes file-based history insufficient.
- Do not download or replace the local model, install CUDA, or switch to GPU inference under the current constraints.
- Do not claim a feature, test, or issue is complete based only on code inspection. Record the exact verification evidence.
- No license has been selected; do not imply the code is licensed for reuse.

## 10. Next Step

Start with **GitHub Issue #1**. Inspect the actual local branch and working tree, verify the active Python interpreter and virtual environment, then reproduce the test setup problem using that interpreter. Decide whether to add a development requirements file, configure import discovery, or use another minimal approach only after observing the result. No application behavior changes should be part of Issue #1.

Repository: https://github.com/TheRealMoeid/Orphivo
