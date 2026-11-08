# Known Issues and Verification Notes

**Last updated:** November 8, 2026

GitHub Issues are the source of truth for active work, priorities, and resolution status. This document records known defects, unresolved questions, migration gaps, and available verification evidence.

Do not mark an issue fixed merely because related automated tests pass. Record manual verification separately.

## 1. Current Development Status

The project is undergoing a migration from Tkinter to PySide6.

| Area | Current status |
|---|---|
| Existing Tkinter application | Still available through `app.py` |
| PySide6 editor proof of concept | Implemented |
| PySide6 main-window shell | Implemented |
| Qt automated tests | Passing in the latest reported run |
| Manual Qt launch | Not performed |
| Qt microphone recording | Not manually verified |
| Qt end-to-end transcription | Not manually verified |
| Qt automatic saving | Not manually verified end to end |
| Qt shutdown behavior | Not manually verified |
| Complete feature parity | Not established |
| Production entry-point migration | Not done |

The current Qt implementation should be considered incomplete until its real application workflow has been tested.

## 2. Current Migration Issue

### Issue #12 — Migrate desktop interface from Tkinter to PySide6

[GitHub Issue #12](https://github.com/TheRealMoeid/Orphivo/issues/12)

**Status:** In progress.

**Branch last reported by the user:**

```text
feature/pyside6-ui-migration
```

**Implemented:**

- PySide6 dependency added to `requirements.txt`.
- Persian-friendly Qt editor proof of concept.
- Qt main-window shell.
- Recording controls and elapsed-time display.
- Background transcription worker using Qt threading and signals.
- Transcript editor.
- Copy and Save As actions.
- Automatic saving of non-empty transcription results when enabled.
- Temporary audio cleanup in the transcription workflow.
- Automated tests for the Qt UI and main window.

**Outstanding verification:**

- [ ] Manually launch the Qt main window.
- [ ] Verify the window renders and behaves correctly on Windows.
- [ ] Test microphone recording.
- [ ] Test stopping a recording and handing audio to the transcription worker.
- [ ] Verify transcription with the actual local Persian model.
- [ ] Verify the result is displayed correctly.
- [ ] Verify automatic saving.
- [ ] Verify manual Save As and Copy actions.
- [ ] Verify temporary audio cleanup.
- [ ] Test error handling, including microphone and transcription failures.
- [ ] Test closing the application while idle.
- [ ] Test closing the application during recording or transcription.
- [ ] Review feature parity with the existing Tkinter application.
- [ ] Review theme and settings integration.
- [ ] Decide when the Qt implementation is ready to replace the production entry point.

**Known architectural concern:**

`src/qt_main_window.py` accesses private recorder attributes (`_stream` and `_recording`) during close handling.

This creates coupling between the UI and the recorder's internal implementation. Review whether the recorder should expose a public lifecycle method or state interface. Do not change this without inspecting the current recorder implementation and its tests.

**Important:** Do not switch `app.py` to PySide6 until the migration requirements have been reviewed and the Qt application has passed manual verification.

## 3. Existing Tkinter UI Issues

These defects were documented during the earlier UI investigation. The Tkinter implementation remains in the repository, so they should not be considered resolved merely because a new UI framework is being introduced.

### 3.1 Enter triggers recording while Settings is open

**Original issue:** [#3 — Review layout, focus, and Persian RTL behavior](https://github.com/TheRealMoeid/Orphivo/issues/3)

**Status:** Previously confirmed by the user; no verified fix recorded here.

**Reproduction:**

1. Run `python app.py`.
2. Open Settings.
3. Press Enter.

**Actual behavior:** Recording starts in the main window unexpectedly.

**Expected behavior:** Pressing Enter while Settings or an unrelated control has focus must not start or stop recording.

**Code lead:** `src/ui.py` uses a global `<Return>` binding through `bind_all()`. The `_enter_shortcut()` handler excludes the transcript editor but does not adequately account for other focus contexts.

**Verification required:**

- [ ] Press Enter in Settings.
- [ ] Check Enter behavior in the history list.
- [ ] Check Enter behavior on buttons and other controls.
- [ ] Preserve appropriate transcript-editor behavior.
- [ ] Verify intentional recording shortcuts still work.

### 3.2 Persian text visually reorders when positioning the caret

**Original issue:** [#3 — Review layout, focus, and Persian RTL behavior](https://github.com/TheRealMoeid/Orphivo/issues/3)

**Status:** Previously confirmed by the user in the Tkinter application.

**Reproduction:**

1. Display a Persian transcript in the Tkinter editor.
2. Click inside the text to position the caret.

**Actual behavior:** Text appears to swap visual positions around the caret.

**Expected behavior:** Persian text must retain its correct visual order during caret placement, selection, and editing.

**Investigation findings:**

The earlier investigation identified a limitation in Tkinter's text-widget bidirectional editing behavior. Right alignment through `justify="right"` does not provide complete Unicode bidirectional text support.

The investigation evaluated several approaches:

- Custom caret hit-testing using `bbox()`: fragile and incomplete.
- Read-only transcript display: safe stopgap, but removes in-app editing.
- Visual-order text storage using reshaping and bidi libraries: rejected because of copy/paste, mixed-direction text, and data-integrity risks.
- A WebView2 editor embedded in the Tkinter application: recommended in that investigation as a possible way to provide proper bidi editing without replacing the rest of the application.

The project subsequently moved toward a full PySide6 UI migration. That migration may provide a better editing foundation, but the actual Qt behavior still needs manual verification.

**Do not assume this issue is fixed until Persian editing has been tested in the replacement UI.**

### 3.3 Long-transcript scrolling

**Status:** Previously tested and working in the Tkinter application.

The user confirmed that long transcripts could be scrolled through easily.

Do not modify scrolling behavior without new evidence. Re-verify it in the Qt interface because the editing surface is changing.

## 4. End-to-End Recording and Transcription

**Original issue:** [#2 — Test microphone recording and transcription end to end](https://github.com/TheRealMoeid/Orphivo/issues/2)

**Status:** End-to-end verification in the new Qt interface is outstanding.

Historical observations:

- Short Persian sentences were reported as less accurate than longer sentences. This is a transcription-quality observation, not an established code defect.
- Blocking microphone access caused stream initialization failure. Recording worked again after microphone access was restored.
- Silent recordings produced no saved transcript. Empty-output status handling was addressed in earlier work; verify it if the relevant code changes.

**Qt verification checklist:**

- [ ] Microphone access is available.
- [ ] Recording starts successfully.
- [ ] Recording stops successfully.
- [ ] Recorded audio is passed to the transcription worker.
- [ ] The configured local model loads successfully.
- [ ] Persian transcription completes.
- [ ] The result is displayed correctly.
- [ ] Non-empty results are automatically saved when auto-save is enabled.
- [ ] Empty results are handled appropriately.
- [ ] Microphone and model errors are communicated to the user.
- [ ] Temporary audio is cleaned up.
- [ ] The application remains responsive during inference.

## 5. Other Items Requiring Review

These are review items, not confirmed defects.

### Qt UI

- [ ] Layout at minimum, default, and maximized window sizes.
- [ ] Persian-only text editing.
- [ ] Mixed Persian and English text.
- [ ] Numbers, dates, punctuation, and parentheses in mixed-direction text.
- [ ] Caret placement and movement.
- [ ] Text selection, deletion, and copy/paste.
- [ ] Long-transcript scrolling.
- [ ] Keyboard tab order and focus visibility.
- [ ] Dark and light theme behavior.
- [ ] Settings persistence and integration.
- [ ] Recording, processing, success, and error states.
- [ ] Window close behavior during active operations.

### Shared services

- [ ] Recorder lifecycle and cleanup.
- [ ] Transcription worker error handling.
- [ ] Settings compatibility between the two UI implementations.
- [ ] Transcript history compatibility.
- [ ] No accidental changes to existing UTF-8 transcript files.

## 6. Automated Test Evidence

### Latest reported test run

**Date:** November 8, 2026

**Environment:** Windows, Python 3.12.10, pytest 9.1.1.

**Command:**

```powershell
python -m pytest tests -v
```

**Result:**

```text
23 passed in 0.77s
```

The reported run included tests for:

- Transcript history.
- Qt editor proof of concept.
- Qt main window and worker.
- Audio recorder.
- Settings.
- Existing UI shortcuts.
- Existing UI status behavior.
- Existing UI worker behavior.

This is the latest test result reported by the user. It has not been independently reproduced.

### What this result does not establish

Passing automated tests does not establish:

- Correct visual Persian RTL behavior in the actual Qt window.
- Successful access to the user's microphone.
- Successful inference using the installed local model.
- Correct end-to-end automatic saving.
- Correct behavior when closing the application during active operations.
- Complete feature parity with the Tkinter application.

Manual Windows verification is still required.

## 7. Historical Test Baseline

On October 21, 2026, the project had the following baseline:

```text
13 passed in 0.58s
```

Environment:

- Windows (`win32`)
- Python 3.12.10
- pytest 9.1.1

This is historical evidence and has been superseded by the November 8 test result. Keep it for reference rather than treating it as the current baseline.

## 8. Triage and Verification Policy

- Use GitHub Issues as the source of truth for active work.
- Separate confirmed defects from hypotheses, limitations, and enhancements.
- Include reproduction steps and expected versus actual behavior.
- Record the environment and exact test command.
- Distinguish automated test results from manual verification.
- Do not close issues until the relevant behavior has been verified.
- Keep changes focused on one issue or task per branch.
- Avoid unrelated changes to model configuration, inference behavior, persistence, and other shared components.
- Preserve local-first operation and compatibility with existing transcript files.

## 9. Next Recommended Work

The immediate next step is to resume Issue #12 from the existing branch and perform a focused review of the current implementation before making further changes.

Recommended order:

1. Inspect the current Git status and branch.
2. Review `src/qt_main_window.py`, `src/recorder.py`, and `src/transcriber.py`.
3. Review the Qt tests and identify what they actually verify.
4. Review the remaining feature-parity requirements.
5. Prepare a manual verification plan for the Qt application.
6. Only then decide which migration gaps require code changes.

Do not replace the Tkinter production entry point until the Qt implementation has been adequately verified.