# Project Context and AI Handoff

**Last updated:** November 8, 2026  
**Repository:** https://github.com/TheRealMoeid/Orphivo  
**Project:** Local-first Persian speech-to-text desktop application  
**Current focus:** Tkinter-to-PySide6 migration

---

## 1. Project Overview

Orphivo is a local-first Windows desktop application for transcribing Persian (Farsi) speech into text.

The application uses Faster-Whisper with CTranslate2 and a locally stored Persian speech recognition model.

Its intended capabilities include:

- Offline speech-to-text transcription.
- Microphone recording.
- Editable Persian transcripts.
- Automatic transcript saving.
- Transcript history.
- Persistent application settings.

The project does not depend on paid cloud transcription APIs.

## 2. Current Project State

The project is currently undergoing a migration from Tkinter to PySide6.

The existing Tkinter application remains the production implementation. The new PySide6 interface has a main-window implementation and automated tests, but has not yet been manually launched by the user.

**Do not assume the migration is complete.**

### Current implementation

| Component | File | Status |
|---|---|---|
| Production entry point | `app.py` | Launches Tkinter |
| Tkinter application | `src/ui.py` | Existing implementation |
| Qt editor proof of concept | `src/qt_ui.py` | Implemented |
| Qt main window | `src/qt_main_window.py` | Implemented; not manually verified |
| Audio recording | `src/recorder.py` | Shared component |
| Transcription | `src/transcriber.py` | Shared component |
| Transcript history | `src/history.py` | Existing component |
| Settings | `src/settings.py` | Existing component |
| Themes | `src/theme.py` | Existing definitions; Qt integration not established |

### Migration status

- PySide6 dependency has been added to `requirements.txt`.
- The Qt editor uses a 14 pt font.
- The Qt main window contains recording controls and an elapsed-time display.
- Transcription runs through a background worker using Qt threading and signals.
- The Qt interface includes transcript editing, Copy, and Save As actions.
- The worker automatically saves non-empty transcription results when auto-save is enabled.
- Temporary audio cleanup is implemented in the Qt transcription workflow.
- Automated Qt tests are passing in the latest reported test run.

### Not yet verified

- Manual launch of the Qt main window.
- Actual microphone recording through Qt.
- End-to-end transcription using the local model.
- Actual automatic saving through the Qt workflow.
- Qt shutdown behavior during active operations.
- Complete feature parity with the Tkinter application.

The existing `app.py` entry point must not be switched to Qt until the migration has been reviewed and manually verified.

## 3. Current Development Environment

The following environment information was reported during development.

| Item | Value |
|---|---|
| Operating system | Windows |
| Python | 3.12.10 |
| pytest | 9.1.1 |
| Faster-Whisper | 1.2.1 |
| CTranslate2 | 4.8.3 |
| PyAV | 18.1.0 |
| UI migration | PySide6 |
| Existing UI | Tkinter |
| Audio recording | sounddevice |
| Transcription language | Persian (`fa`) |
| Inference configuration | CPU INT8 |

The development model directory has been:

```text
D:\whisper-large-fa-v1-ct2
```

The model is expected to be available locally. The project should not introduce automatic model downloads or hosted transcription services without an explicit change in requirements.

## 4. Repository and Branch State

**Local repository path last reported:**

```text
D:\AI\Orphivo
```

**Latest reported branch:**

```text
feature/pyside6-ui-migration
```

**Base commit when the branch was created:**

```text
29c9c7e
```

**Related GitHub Issue:**

[Issue #12 — Migrate desktop interface from Tkinter to PySide6](https://github.com/TheRealMoeid/Orphivo/issues/12)

The user reported that the branch was created from `origin/main` and was clean before the migration patches were applied.

The current working-tree status has not been confirmed after the latest changes. Do not assume the branch is clean or that all changes have been committed.

### First action when resuming

Ask the user to run:

```powershell
git status
git branch --show-current
git log -1 --oneline
```

Use the output to establish the actual repository state before recommending any implementation work.

Do not switch branches, discard changes, reset files, or modify the user's working tree without explicit approval.

## 5. Recent Development History

### Stage 1 — PySide6 editor proof of concept

The initial Qt work introduced:

- `requirements.txt` dependency changes.
- `src/qt_ui.py`.
- `tests/test_qt_ui.py`.

An initial test exposed an incorrect use of `QPlainTextEdit.setAlignment()`, which does not exist.

A corrective change configured text alignment through `QTextOption`.

The user subsequently approved a 14 pt editor font.

### Stage 2 — Qt main-window shell

A later patch added:

- `src/qt_main_window.py`
- `tests/test_qt_main_window.py`

The corrected patch was additions-only. An earlier attempted patch that modified `src/qt_ui.py` and `tests/test_qt_ui.py` was not the patch applied for this stage.

The new main-window implementation includes recording controls, transcript editing, background transcription, and saving behavior.

### Latest automated test run

On November 8, 2026, the user ran:

```powershell
python -m pytest tests -v
```

Reported result:

```text
23 passed in 0.77s
```

This is the latest user-reported automated test result.

The user has explicitly stated that they have not run the Qt launch command or manually tested the new interface.

The following command was provided for a future manual launch:

```powershell
python -c "from PySide6.QtWidgets import QApplication; from src.qt_main_window import OrphivoMainWindow; app = QApplication([]); window = OrphivoMainWindow(); window.show(); app.exec()"
```

Do not claim that the Qt application has been manually tested.

## 6. Important Existing Issues

### Issue #12 — PySide6 migration

[GitHub Issue #12](https://github.com/TheRealMoeid/Orphivo/issues/12)

This is the current development focus.

The migration needs manual verification and a feature-parity review before replacing the Tkinter production entry point.

### Issue #3 — UI layout, focus, and Persian RTL behavior

[GitHub Issue #3](https://github.com/TheRealMoeid/Orphivo/issues/3)

Two previously confirmed Tkinter problems were documented:

1. Pressing Enter while Settings is open unexpectedly starts recording.
2. Persian text visually reorders around the caret when clicking inside the transcript editor.

The earlier investigation identified limitations in Tkinter's bidirectional text editing behavior. Right alignment alone does not provide correct RTL caret handling.

The project subsequently moved toward PySide6. The Qt editor must be tested with Persian text, mixed Persian/English text, numbers, punctuation, selection, and caret movement before considering this problem resolved.

Long-transcript scrolling was previously confirmed to work in the Tkinter application.

### Issue #2 — End-to-end recording and transcription

[GitHub Issue #2](https://github.com/TheRealMoeid/Orphivo/issues/2)

The complete recording-to-transcription workflow still requires verification in the new Qt interface.

Historical observations include microphone permission problems and differences in transcription quality between short and longer Persian sentences.

These observations should not automatically be treated as current defects.

### Other historical issues

The existing documentation also references:

- [Issue #1 — Make the test suite runnable in a clean virtual environment](https://github.com/TheRealMoeid/Orphivo/issues/1)
- [Issue #4 — Standardize project naming on Orphivo](https://github.com/TheRealMoeid/Orphivo/issues/4)

Check the current GitHub status of these issues rather than assuming they remain open or resolved.

## 7. Architecture and Technical Constraints

The project should retain these characteristics:

- Local-first operation.
- Offline transcription.
- Faster-Whisper/CTranslate2 inference.
- Locally stored model.
- CPU INT8 as the established inference configuration.
- UTF-8 transcript files.
- JSON settings.
- Existing transcript compatibility.

Avoid:

- Introducing paid cloud transcription APIs.
- Downloading a replacement model automatically.
- Changing inference configuration without a dedicated reason.
- Introducing a database without a documented requirement.
- Duplicating shared recorder, transcriber, history, or settings logic unnecessarily.
- Making unrelated refactors during a focused migration task.

The Qt implementation should reuse the existing shared services where appropriate.

One architectural concern already identified is that `src/qt_main_window.py` accesses private recorder attributes (`_stream` and `_recording`) during close handling. Review this dependency before changing recorder lifecycle behavior.

For additional architecture details, consult `docs/ARCHITECTURE.md`.

## 8. Documentation Map

The main project documents are:

| Document | Purpose |
|---|---|
| `README.md` | Project overview, setup, features, and usage |
| `docs/ARCHITECTURE.md` | Components, responsibilities, data flow, and architectural constraints |
| `docs/KNOWN_ISSUES.md` | Known defects, migration gaps, and verification evidence |
| `PROJECT_CONTEXT.md` | Development history, current state, and AI handoff |

Read all four documents before making significant changes.

Check whether the repository uses `docs/` or the root directory for each document before editing. Do not assume a file's location based only on its name.

## 9. Required Workflow for the Next AI Model

The user expects a review-first, approval-based development process.

### Phase 1 — Inspect

Before proposing implementation:

1. Inspect the current Git branch and working tree.
2. Read the project documentation.
3. Inspect the relevant source files and tests.
4. Review the relevant GitHub Issues.
5. Determine the actual development stage.
6. Identify what has been implemented, tested, and manually verified.

Do not assume previous conversation summaries are more accurate than the current repository.

### Phase 2 — Analyze

Before writing code, present:

- The actual root cause or missing requirement.
- Relevant files and components.
- Possible implementation approaches.
- Advantages and disadvantages.
- Architectural and compatibility risks.
- Required automated tests.
- Required manual verification.
- A clear recommendation.

Wait for the user's decision before implementation.

### Phase 3 — Implement

After approval:

- Work on one issue or task per branch.
- Do not edit the user's active branch without agreement.
- Provide repository changes as a `.patch` file.
- Do not directly edit the repository or send separate replacement files unless explicitly requested.
- Include the intended branch name and exact Git commands.
- Explain how to apply the patch with `git apply`.
- Include automated and manual test commands.

The user applies the patch, runs tests, and reports the results.

Do not commit or merge changes on the user's behalf.

### Phase 4 — Verify and document

After the user reports results:

- Review the actual test output.
- Distinguish passing automated tests from manual verification.
- Identify any remaining failures or gaps.
- Update the relevant documentation.
- Do not mark an issue resolved without sufficient evidence.

## 10. Immediate Recommended Next Step

Resume the PySide6 migration, but do not start implementing another feature yet.

First establish the actual repository state:

```powershell
cd D:\AI\Orphivo

git status
git branch --show-current
git log -1 --oneline
```

Then inspect:

```text
src/qt_main_window.py
src/qt_ui.py
src/recorder.py
src/transcriber.py
src/history.py
src/settings.py
tests/test_qt_main_window.py
tests/test_qt_ui.py
```

Compare the implementation against the requirements in GitHub Issue #12.

The next AI model should produce a concise assessment of the migration's current state and recommend the next task before generating any patch.

---

**Handoff principle:** The Qt implementation has passed its reported automated tests, but its real-world workflow remains unverified. Continue from the actual repository state, not assumptions based on this document.