# Project Context and AI Handoff

**Last updated:** November 14, 2026  
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

The existing Tkinter application remains the production implementation. The new PySide6 interface has a main-window implementation, automated tests, and its core workflow has been manually launched and verified by the user. The four feature-parity gaps identified on November 8 (theme, in-Qt settings, history panel, Enter shortcut) were each scoped as their own task and are now implemented and manually verified (section 5, Stage 4).

**Do not assume the migration is complete — three secondary verification items remain (idle-state close, long-inference responsiveness, a manually-triggered transcription failure), and `app.py` has not been switched.**

### Current implementation

| Component | File | Status |
|---|---|---|
| Production entry point | `app.py` | Launches Tkinter |
| Tkinter application | `src/ui.py` | Existing implementation |
| Qt editor proof of concept | `src/qt_ui.py` | Implemented |
| Qt main window | `src/qt_main_window.py` | Implemented; core workflow and all four feature-parity gaps manually verified |
| Qt settings dialog | `src/qt_settings_dialog.py` | Implemented and manually verified |
| Qt history panel | `src/qt_history_panel.py` | Implemented and manually verified |
| Audio recording | `src/recorder.py` | Shared component |
| Transcription | `src/transcriber.py` | Shared component |
| Transcript history | `src/history.py` | Existing component |
| Settings | `src/settings.py` | Existing component, now read by both UIs including theme |
| Themes | `src/theme.py` | Existing definitions; now integrated into the Qt window via a palette-driven stylesheet |

### Migration status

- PySide6 dependency has been added to `requirements.txt`.
- The Qt editor uses a 14 pt font with correct RTL/bidi rendering for mixed Persian/English/digit text.
- The Qt main window contains recording controls, an elapsed-time display, and an Enter-key shortcut to start/stop recording.
- Transcription runs through a background worker using Qt threading and signals.
- The Qt interface includes transcript editing, Copy, and Save As actions.
- The worker automatically saves non-empty transcription results when auto-save is enabled.
- Temporary audio cleanup is implemented in the Qt transcription workflow.
- An in-window Settings dialog (folder, auto-save, theme) and a transcript history panel (list, open folder, delete, click-to-load) are implemented.
- Dark/light theme switching is implemented, applied live and persisted.
- Automated Qt tests are passing in the latest reported test run (32).

### Verified (November 8–14, 2026)

- Manual launch of the Qt main window.
- Microphone recording through Qt, including the microphone-unavailable error path.
- End-to-end transcription using the local model (speech and silence cases).
- Automatic saving through the Qt workflow.
- Qt shutdown behavior during active recording and during active transcription.
- Bilingual/RTL text ordering, Copy action and shortcut (after fixes — see Stage 3).
- Settings dialog, transcript history panel, dark/light theme switching, and the Enter-to-record shortcut (see Stage 4).

### Not yet verified

- Shutdown behavior while completely idle.
- UI responsiveness during a long inference run.
- Transcription-failure error handling against the real model (covered only by automated tests with a mocked transcriber).

The existing `app.py` entry point must not be switched to Qt until the three items above have been verified.

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

### Stage 3 — Manual verification and bugfix patch (November 8, 2026)

The user launched `OrphivoMainWindow` via the documented command and manually tested, in order: recording and transcribing real speech (auto-saved correctly); recording silence (correctly produced no save and the expected status message); closing while a transcription was in progress (correctly blocked with a wait message); closing while actively recording (correctly showed a confirm dialog, aborted cleanly on confirmation); Save As with the `.txt` suffix removed from the typed filename (confirmed the code's suffix-forcing is intentional, not a bug); multiple record/stop cycles back to back (duration label and button state reset correctly each time).

Three bugs were found during this pass and fixed in `orphivo-qt-fixes.patch`, applied by the user:

1. Mixed Persian/English/digit text displayed in scrambled visual order — root cause was `QTextOption` only setting alignment, not bidi base direction; fixed with an explicit `setTextDirection(Qt.LayoutDirection.RightToLeft)` in both `qt_ui.py` and `qt_main_window.py`.
2. `copy_text()` crashed (`self.clipboard()` is not a `QMainWindow` method, also broke the `Ctrl+Shift+C` shortcut) — fixed with `QApplication.clipboard()`.
3. The microphone-error dialog leaked the raw PortAudio/MME backend error text — fixed to match the Tkinter app's generic message.

Regression tests were added for all three, bringing the suite from 23 to 25 tests. The user applied the patch, ran the full suite (`python -m pytest tests -v`, 25 passed, plus an unrelated pytest-teardown `PermissionError` from a custom Windows temp directory), and manually re-confirmed all three fixes.

A pre-existing, non-UI issue was also observed during this testing: Whisper occasionally hallucinates a plausible Persian sentence on silence/near-silence input. This happened on both the Tkinter and Qt UIs, confirming it is a model/`transcriber.py`-level behavior, not a migration regression. See `docs/KNOWN_ISSUES.md` section 4 for details. No action was taken on it as part of Issue #12.

Full details of all of the above, including the exact checklist status, are in `docs/KNOWN_ISSUES.md` sections 1, 3.4, 3.5, and 4.

### Stage 4 — Feature-parity gaps closed (November 9–14, 2026)

The four gaps identified at the end of Stage 3 (theme, in-Qt settings, history panel, Enter shortcut) were each implemented as their own task, in this order, each delivered and manually verified before moving to the next:

1. **Settings dialog** — new `src/qt_settings_dialog.py`, kept separate from `qt_main_window.py`. Folder (with Browse), auto-save checkbox, and a Dark/Light theme choice; Save stays disabled until something actually changes.
2. **Transcript history panel** — new `src/qt_history_panel.py`. List of saved transcripts, Open Folder, Delete with confirmation, click-to-load via a signal rather than direct coupling to the editor.
3. **Theme switching** — `src/theme.py`'s `PALETTES` wired into a palette-driven QSS builder in `qt_main_window.py`; toggle lives in the Settings dialog, applies live, persists.
4. **Enter-to-record shortcut** — a `keyPressEvent` override on the main window; simpler than Tkinter's equivalent since the Settings dialog is a separate top-level widget in Qt, so no global-binding leak to guard against.

A visual redesign was folded into the history-panel task at the user's request (RTL-appropriate control mirroring, a 3-color triadic accent palette) rather than deferred to its own task, since it was a small, well-specified set of edits. Two further Qt-specific bidi rendering bugs were found and fixed during that work (see `docs/KNOWN_ISSUES.md` section 3.7) — both traced to the same root cause as a `heading`/`status_label` alignment bug from Stage 3: Qt auto-swaps `AlignLeft`/`AlignRight` for RTL-direction widgets unless `Qt.AlignAbsolute` is also set.

The test suite grew from 25 to 32 across this stage; all passing, confirmed by the user after each task.

Full details are in `docs/KNOWN_ISSUES.md` sections 1, 3.6, and 3.7.

**Feature parity with Tkinter is now established for the four gaps tracked since Stage 3.** Three secondary items remain unverified before `app.py` can be considered for switching: idle-state close, long-inference UI responsiveness, and a manually-triggered transcription failure (see section 2 above and `docs/KNOWN_ISSUES.md` section 4).

## 6. Important Existing Issues

### Issue #12 — PySide6 migration

[GitHub Issue #12](https://github.com/TheRealMoeid/Orphivo/issues/12)

This is the current development focus.

Manual verification of the core workflow and all four feature-parity gaps is complete (see Stage 3 and Stage 4 above). Three secondary verification items (idle close, long-inference responsiveness, a manually-triggered transcription failure) remain before replacing the Tkinter production entry point.

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

The Qt core workflow and all four feature-parity gaps (Stage 3, Stage 4 above) are now manually verified. Do not start re-verifying the items already confirmed in section 2 and `docs/KNOWN_ISSUES.md` sections 1, 3.4, 3.6, and 3.7.

First establish the actual repository state, since the branch may have moved on since this document was last updated:

```powershell
cd D:\AI\Orphivo

git status
git branch --show-current
git log -1 --oneline
```

Then work through the three remaining secondary verification items in `docs/KNOWN_ISSUES.md` section 4: closing the app while completely idle, UI responsiveness during a long inference run, and manually triggering a transcription failure against the real model. Only after those are verified should a future `app.py` entry-point switch be planned, as its own separate task.

The next AI model should re-read `docs/KNOWN_ISSUES.md` in full before proposing any new work, since it now holds the authoritative list of what is verified versus still open.

---

**Handoff principle:** The Qt implementation's core record/transcribe/save/error/close workflow and all four feature-parity gaps have been manually verified. Three secondary items remain before `app.py` can reasonably be switched. Continue from the actual repository state and from `docs/KNOWN_ISSUES.md`, not from assumptions based on older summaries.
