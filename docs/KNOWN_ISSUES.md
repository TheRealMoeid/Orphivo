# Known Issues and Verification Notes

**Last updated:** November 16, 2026

GitHub Issues are the source of truth for active work, priorities, and resolution status. This document records known defects, unresolved questions, migration gaps, and available verification evidence.

Do not mark an issue fixed merely because related automated tests pass. Record manual verification separately.

## 1. Current Development Status

| Area | Current status |
|---|---|
| Existing Tkinter application | Still available through `app.py` |
| PySide6 editor proof of concept | Implemented |
| PySide6 main-window shell | Implemented |
| Qt automated tests | Passing (60) |
| Manual Qt launch | Done |
| Qt microphone recording | Manually verified, including the microphone-unavailable error path |
| Qt end-to-end transcription | Manually verified (speech, silence, and two real failure modes — see section 4) |
| Qt automatic saving | Manually verified |
| Qt shutdown behavior | Manually verified for close-during-recording, close-during-transcription, **and idle-state close** |
| Qt bilingual/RTL text ordering | Manually verified after fix (3.4) |
| Qt copy/save/load/settings status messages | Manually verified after fix (3.8) |
| Qt settings dialog (folder, auto-save, theme) | Implemented and manually verified (3.6) |
| Qt transcript history panel | Implemented and manually verified (3.6) |
| Qt dark/light theme switching | Implemented and manually verified (3.6) |
| Qt Enter-to-record shortcut | Implemented and manually verified (3.6) |
| Qt long-inference UI responsiveness | Manually verified (3.9) |
| Qt real transcription-failure handling | Manually verified against the actual model, not just a mock (4) |
| Qt record-button busy-state feedback | Implemented and manually verified (3.8) |
| Complete feature parity | Established — all four original gaps plus all three secondary verification items are closed |
| Production entry-point migration | Not done — next planned task |

The Qt implementation is now functionally complete and fully manually verified. The only remaining item before production is the `app.py` entry-point switch itself, which has not yet been scoped.

## 2. Current Migration Issue

### Issue #12 — Migrate desktop interface from Tkinter to PySide6

[GitHub Issue #12](https://github.com/TheRealMoeid/Orphivo/issues/12)

**Status:** Verification complete; entry-point switch pending.

**Branch:**

```text
feature/pyside6-ui-migration
```

**Outstanding verification:**

- [x] Manually launch the Qt main window.
- [x] Verify the window renders and behaves correctly on Windows.
- [x] Test microphone recording.
- [x] Test stopping a recording and handing audio to the transcription worker.
- [x] Verify transcription with the actual local Persian model.
- [x] Verify the result is displayed correctly.
- [x] Verify automatic saving.
- [x] Verify manual Save As and Copy actions.
- [x] Test microphone error handling.
- [x] Test transcription-failure error handling manually against the real model (see section 4 — two distinct real failures reproduced).
- [x] Test closing the application while idle.
- [x] Test closing the application during recording.
- [x] Test closing the application during transcription.
- [x] Review feature parity with the existing Tkinter application.
- [x] Review theme and settings integration.
- [x] Verify UI responsiveness during a long inference run (3.9).
- [ ] Decide when the Qt implementation is ready to replace the production entry point — all verification is now done; this is the one remaining open decision/task.

**Known architectural concern (unchanged, not new):**

`src/qt_main_window.py` accesses private recorder attributes (`_stream` and `_recording`) during close handling, the same pattern already present in the Tkinter app's own close handling. Worth evaluating if recorder lifecycle changes are ever planned; not blocking.

## 3. Qt Implementation Notes and Fix History

### 3.1–3.3 Tkinter-era issues

Historical Tkinter issues (Enter-key focus scoping, Persian caret reordering, long-transcript scrolling) remain documented for the Tkinter app but are superseded in relevance now that the Qt app is the verified implementation moving toward production. See prior revisions of this document for full detail if the Tkinter app is ever revisited.

### 3.4 Qt bugs found and fixed during initial manual verification (November 8, 2026)

Three defects were found and fixed in `orphivo-qt-fixes.patch`:

1. Mixed Persian/English/digit text displayed in the wrong visual order — fixed with explicit `setTextDirection(Qt.LayoutDirection.RightToLeft)`.
2. `copy_text()` crashed (`QMainWindow` has no `clipboard()` method) — fixed with `QApplication.clipboard()`.
3. The microphone-error dialog leaked a raw backend error string — fixed to show a generic, user-facing message.

### 3.5–3.7 Feature-parity gaps, resolved

The four feature-parity gaps (settings dialog, history panel, theme switching, Enter-to-record shortcut) and the RTL visual redesign folded into the history-panel task are implemented and manually verified. See prior revisions of this document for full implementation and bug-fix detail (two further bidi-rendering bugs traced to Qt's `AlignLeft`/`AlignRight` auto-swap for RTL-direction widgets, and a placeholder-text rendering gap in `QPlainTextEdit`, both fixed).

### 3.8 Status-message revert bug and record-button busy-state feedback (found and fixed November 16, 2026)

Found during manual long-inference testing (section 3.9): clicking **Copy text**, **Save As**, loading a transcript from the history panel, or saving **Settings** while a transcription was still running correctly showed its confirmation message (e.g. "Transcript copied to clipboard") — but if the transcription finished shortly afterward, `_on_transcription_completed`'s own status update silently overwrote it with no warning. The user perceived this as the confirmation "disappearing" or the transcribing message reappearing.

**Root cause:** `status_label.setText()` was called directly and unconditionally from several places, with no distinction between a message that represents a real, ongoing state (recording, transcribing) and a message that's just a brief confirmation of an action that doesn't change that state.

**Fix:** Two helper methods on `OrphivoMainWindow`:

- `_set_status(text)` — for genuine state changes. Also cancels any pending temporary-message timer.
- `_show_temporary_status(text)` — for Copy/Save As/load-transcript/settings-saved confirmations. Displays the message, then a single-shot 3-second `QTimer` reverts the label to the current base state.

The user explicitly considered and rejected disabling the Copy/Save buttons during busy state as an alternative fix — the buttons remain clickable at all times; only the status-label behavior changed.

**Related UX fix, same round:** while transcribing, the record button was disabled but visually indistinguishable from its normal enabled (blue) state, since its own `[recording="true"]` QSS rule took priority over the generic `:disabled` style — it looked broken, not busy. At the same time, the status line duplicated "Transcribing locally on CPU…" right next to it. Fixed by:

- Giving `record_button` its own explicit `:disabled` QSS rule (muted panel/border colors).
- Changing the button's text to "Transcribing…" while busy, reverting to "● Start recording" when the worker thread finishes.
- Clearing the status label to empty for the duration of transcription, instead of repeating the same message — freeing it for the temporary confirmations above without a redundant second "Transcribing…" competing with them.

**Verified fixed:** user confirmed via manual testing (clicking Copy/Save/load/settings-save mid-transcription, watching the message show then correctly revert to the real state — recording, transcribing-with-empty-status-line, or idle — after a few seconds) across all four trigger points, plus the button text/style change. Covered by 8 new regression tests in `tests/test_qt_status_revert.py`, bringing the suite from 55 to 60 (an earlier intermediate run was 57, between the status-revert fix and the button UX fix).

### 3.9 Long-inference UI responsiveness (verified November 16, 2026)

**Original issue:** [#2 — Test microphone recording and transcription end to end](https://github.com/TheRealMoeid/Orphivo/issues/2), secondary item.

A real recording of 7 minutes 14 seconds was transcribed, producing roughly 4 minutes of CPU INT8 inference. CPU/memory usage was logged throughout (`app_usage_log.csv`, user-provided): idle/recording phase held at roughly 0% CPU and ~954 MB memory; the transcription phase held a steady ~25% CPU (consistent with a single core fully occupied by the background worker thread, not the UI thread) with memory climbing to roughly 1.2–1.3 GB, dropping back to ~0% once complete.

During the transcription phase, the user confirmed the window remained interactive: draggable, resizable, and responsive to button clicks (which is also how the 3.8 bug above was surfaced — the user was actively using Copy/Save/Settings/history while transcription ran, which would not have been possible if the UI had frozen).

**Verified:** UI responsiveness during long inference is confirmed. No freezing, no "Not Responding" state observed.

## 4. End-to-End Recording and Transcription

**Original issue:** [#2 — Test microphone recording and transcription end to end](https://github.com/TheRealMoeid/Orphivo/issues/2)

**Status:** Complete, including real (non-mocked) failure-mode testing.

Historical observations (unchanged, informational only):

- Short Persian sentences were previously reported as less accurate than longer sentences — a transcription-quality observation, not a code defect.
- Occasional Whisper hallucination on silence/near-silence input, observed on both UIs — model-level behavior, out of scope for Issue #12.

**Real transcription-failure testing (verified November 16, 2026):**

Two distinct real failures were triggered through the actual worker/thread/signal chain, not the mocked automated test:

1. **Missing/misnamed model directory** (e.g. a typo'd path) — surfaces `transcriber.py`'s own `FileNotFoundError` message ("Local Whisper model folder was not found: ...") cleanly through to the error dialog. Clear and user-actionable.
2. **Corrupted model file inside an otherwise-valid model directory** (e.g. `model.bin` renamed/unreadable) — surfaces a raw CTranslate2/faster-whisper backend error string ("Unable to open file 'model.bin' in model '...'"). Readable and informative, but not wrapped in a friendlier message the way the microphone-error path was (3.4 item 3). Flagged as a minor, non-blocking future polish item, not a defect requiring action now.

In both cases: the error dialog appeared with the message above, and — critically — the application returned to a normal, fully usable state after the user dismissed the dialog (record button re-enabled, able to start a new recording immediately). No hang, no crash, no stuck state.

**Qt verification checklist:**

- [x] Microphone access is available.
- [x] Recording starts successfully.
- [x] Recording stops successfully.
- [x] Recorded audio is passed to the transcription worker.
- [x] The configured local model loads successfully.
- [x] Persian transcription completes.
- [x] The result is displayed correctly.
- [x] Non-empty results are automatically saved when auto-save is enabled.
- [x] Empty results are handled appropriately.
- [x] Microphone errors are communicated to the user.
- [x] Model/transcription errors are communicated to the user (two real failure modes confirmed above).
- [x] The application recovers to a usable state after a transcription failure.
- [x] The application remains responsive during inference (3.9).
- [x] Duration label and record button reset correctly across repeated record/stop cycles.

Temporary-audio-cleanup is still only covered by automated tests, not a separate manual file-system inspection — low-priority given everything else above is now confirmed.

## 5. Automated Test Evidence

**Date:** November 16, 2026

**Environment:** Windows, Python 3.12.10, pytest 9.1.1.

```powershell
python -m pytest tests -v
```

```text
60 passed
```

This run includes `tests/test_qt_status_revert.py` (new this round, 8 tests) alongside all prior Qt and Tkinter coverage.

## 6. What Is Now Established

Combining automated tests with the manual verification above:

- Correct visual Persian/bilingual RTL behavior.
- Successful microphone access, including the unavailable-device error path.
- Successful local-model inference for speech, silence, and two distinct real failure modes.
- Correct automatic saving.
- Correct close behavior during active recording, active transcription, **and while completely idle**.
- Correct Copy, Save As, history-load, and Settings-save behavior, including status-message correctness when used concurrently with an in-progress transcription.
- The settings dialog, history panel, theme switching, and Enter-to-record shortcut all work as implemented.
- **UI responsiveness during long inference runs.**
- **Real (non-mocked) transcription-failure handling and recovery.**

Nothing material remains unverified for the migration itself. The one open item is the `app.py` entry-point switch, not yet scoped.

## 7. Triage and Verification Policy

(unchanged)

- Use GitHub Issues as the source of truth for active work.
- Separate confirmed defects from hypotheses, limitations, and enhancements.
- Include reproduction steps and expected versus actual behavior.
- Record the environment and exact test command.
- Distinguish automated test results from manual verification.
- Do not close issues until the relevant behavior has been verified.
- Keep changes focused on one issue or task per branch.

## 8. Next Recommended Work

1. Commit this round's changes (`qt_main_window.py` status-revert and button-UX fixes, `tests/test_qt_status_revert.py`, and this documentation update) to `feature/pyside6-ui-migration` and push.
2. Scope the `app.py` entry-point switch as its own explicitly-approved task — not yet discussed in detail. Likely considerations: whether to keep `src/ui.py` available as a fallback/reference, how to communicate the switch to any existing users, and a final smoke test immediately after the switch.
3. Optionally, as a low-priority follow-up: wrap the corrupted-model-file error (section 4, item 2) in a friendlier message, matching the treatment the microphone-error path already received.
