# Known Issues and Verification Notes

**Last updated:** November 14, 2026

GitHub Issues are the source of truth for active work, priorities, and resolution status. This document records known defects, unresolved questions, migration gaps, and available verification evidence.

Do not mark an issue fixed merely because related automated tests pass. Record manual verification separately.

## 1. Current Development Status

The project is undergoing a migration from Tkinter to PySide6.

| Area | Current status |
|---|---|
| Existing Tkinter application | Still available through `app.py` |
| PySide6 editor proof of concept | Implemented |
| PySide6 main-window shell | Implemented |
| Qt automated tests | Passing in the latest reported run (32) |
| Manual Qt launch | Done — `OrphivoMainWindow` launched via the documented command |
| Qt microphone recording | Manually verified, including the microphone-unavailable error path |
| Qt end-to-end transcription | Manually verified (speech → transcript, and silence → no transcript) |
| Qt automatic saving | Manually verified |
| Qt shutdown behavior | Manually verified for close-during-recording and close-during-transcription; idle-state close not yet verified |
| Qt bilingual/RTL text ordering | Manually verified after fix (see 3.4 below) |
| Qt copy/save actions | Manually verified after fix (see 3.4 below) |
| Qt settings dialog (folder, auto-save, theme) | Implemented and manually verified (see 3.6 below) |
| Qt transcript history panel | Implemented and manually verified (see 3.6 below) |
| Qt dark/light theme switching | Implemented and manually verified (see 3.6 below) |
| Qt Enter-to-record shortcut | Implemented and manually verified (see 3.6 below) |
| Complete feature parity | The four previously tracked gaps (theme, settings, history, Enter shortcut) are closed. Idle-state close, long-inference responsiveness, and a manually-triggered transcription failure remain unverified (section 4) |
| Production entry-point migration | Not done — pending the three items just above |

The current Qt implementation's core recording/transcription/save workflow, settings, history, theme, and Enter shortcut have now all been manually verified. Three secondary items remain open before feature parity can be called fully established (section 4).

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
- Settings dialog (transcript folder, auto-save, theme), transcript history panel, dark/light theme switching, and the Enter-to-record shortcut — see section 3.6.

**Outstanding verification:**

- [x] Manually launch the Qt main window.
- [x] Verify the window renders and behaves correctly on Windows.
- [x] Test microphone recording.
- [x] Test stopping a recording and handing audio to the transcription worker.
- [x] Verify transcription with the actual local Persian model.
- [x] Verify the result is displayed correctly.
- [x] Verify automatic saving.
- [x] Verify manual Save As and Copy actions.
- [ ] Verify temporary audio cleanup (covered automatically by `tests/test_qt_main_window.py`; not separately confirmed by manual file-system inspection).
- [x] Test microphone error handling.
- [ ] Test transcription-failure error handling manually (covered automatically by `tests/test_qt_main_window.py`; not manually triggered against the real model).
- [ ] Test closing the application while idle.
- [x] Test closing the application during recording.
- [x] Test closing the application during transcription.
- [x] Review feature parity with the existing Tkinter application — the four gaps tracked here (theme, in-Qt settings, history panel, Enter-to-record shortcut) are implemented and manually verified; see section 3.6.
- [x] Review theme and settings integration — implemented via an in-window Settings dialog and `src/theme.py` palette switching; see section 3.6.
- [ ] Decide when the Qt implementation is ready to replace the production entry point — pending the idle-close, long-inference, and manual transcription-failure items in section 4.

**Known architectural concern:**

`src/qt_main_window.py` accesses private recorder attributes (`_stream` and `_recording`) during close handling.

This creates coupling between the UI and the recorder's internal implementation. Review whether the recorder should expose a public lifecycle method or state interface. Do not change this without inspecting the current recorder implementation and its tests.

**Important:** Do not switch `app.py` to PySide6 until the migration requirements have been reviewed and the Qt application has passed manual verification.

## 3. Existing Tkinter UI Issues

These defects were documented during the earlier UI investigation. The Tkinter implementation remains in the repository, so they should not be considered resolved merely because a new UI framework is being introduced.

### 3.1 Enter triggers recording while Settings is open

**Original issue:** [#3 — Review layout, focus, and Persian RTL behavior](https://github.com/TheRealMoeid/Orphivo/issues/3)

**Status:** Previously confirmed by the user; no manual re-verification recorded here. Note: `src/ui.py`'s `_enter_shortcut()` already contains a `winfo_toplevel() is not self` guard that matches this issue's expected behavior, and `tests/test_ui_shortcuts.py` (4 tests, all passing) covers exactly this scenario, including `test_enter_from_settings_window_does_not_toggle_recording`. Per this document's own policy, passing tests alone do not close this issue — it should be manually re-confirmed in the running Tkinter app before this status line is updated.

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

### 3.4 Qt bugs found and fixed during manual verification (November 8, 2026)

Three defects were found while manually testing `src/qt_main_window.py` and `src/qt_ui.py` for the first time, and were fixed in `orphivo-qt-fixes.patch`:

1. **Mixed Persian/English/digit text displayed in the wrong visual order.** `QTextOption(Qt.AlignmentFlag.AlignRight)` only sets paragraph alignment, not the Unicode bidi base direction; without an explicit direction, Qt can auto-detect an LTR base direction for a right-aligned paragraph, scrambling the order of mixed-direction runs. This reproduced the same user-facing symptom as issue 3.2 above, though the underlying mechanism is Qt-specific rather than the Tkinter limitation described there. **Fix:** `QTextOption.setTextDirection(Qt.LayoutDirection.RightToLeft)` is now set explicitly in both `src/qt_ui.py` and `src/qt_main_window.py`. **Verified fixed:** the user confirmed a bilingual test sentence now displays in correct right-to-left order.
2. **`copy_text()` crashed with `AttributeError: 'OrphivoMainWindow' object has no attribute 'clipboard'`**, also breaking the `Ctrl+Shift+C` shortcut, which calls the same method. `QMainWindow` has no `clipboard()` method; clipboard access belongs on the application object. **Fix:** uses `QApplication.clipboard().setText(text)`. **Verified fixed:** both the Copy button and the shortcut now work and update the status label.
3. **The microphone-error dialog showed the raw backend exception** (e.g. `Unanticipated host error [PaErrorCode -9999]: 'Undefined external error.' [MME error 1]`) instead of a user-facing message, inconsistent with the Tkinter app's existing generic message. **Fix:** the dialog and status label now both show the same generic message the Tkinter app uses ("Could not start recording. Check Windows microphone permissions and the selected input device, then try again."). **Verified fixed:** confirmed with the microphone disabled in Windows settings.

Regression tests were added to `tests/test_qt_ui.py` and `tests/test_qt_main_window.py` for all three (bidi text-direction assertions, a clipboard-copy test, and a microphone-error-message test), bringing the suite from 23 to 25 tests, all passing.

None of these three were caught by the original automated test suite, which only checked widget construction/alignment and the transcription worker in isolation — `copy_text()`, `save_as()`, and the microphone-error path had no prior coverage.

### 3.5 Qt feature-parity gaps versus Tkinter — now resolved

The four gaps found by direct inspection of `src/qt_main_window.py` on November 8, 2026 (no theme integration, no in-Qt settings dialog, no transcript history panel, no Enter-to-record shortcut) were each scoped as a separate task and are now implemented and manually verified. See section 3.6 for details of each.

### 3.6 Qt feature-parity work completed (November 9–14, 2026)

Each of the four gaps from 3.5 was implemented as its own task/branch, in this order:

1. **Settings dialog** (`src/qt_settings_dialog.py`, new module, kept separate from `qt_main_window.py`). A modal `OrphivoSettingsDialog` with the transcript folder (with Browse), an auto-save checkbox, and a Dark/Light theme choice. Reuses `src/settings.py` directly — no second settings system. The Save button stays disabled until something actually differs from the values the dialog was opened with (folder text, auto-save, or theme), with a matching `:disabled` style so the state is visually obvious, not just functional. **Verified:** folder changes take effect and persist, empty-path is rejected with a dialog, Cancel leaves everything untouched, and automated tests cover all of this.
2. **Transcript history panel** (`src/qt_history_panel.py`, new module). An `OrphivoHistoryPanel` widget: title/folder display, a list of saved transcripts (newest first), Open Folder, and Delete (with confirmation). Emits a `transcript_selected(Path)` signal rather than reaching into the editor directly, keeping it decoupled from the main window. Its title/folder labels are placed in the main window's own header row (not inside the panel's layout) so the panel's list box starts flush with the transcript editor's top edge. **Verified:** lists real saved transcripts, clicking one loads it into the editor, delete removes the file and confirms first, and the panel refreshes after every save and after a settings-dialog folder change.
3. **Theme switching.** `src/theme.py`'s `PALETTES` (dark/light) are now read directly into a palette-driven QSS builder in `qt_main_window.py`, replacing what had been a hardcoded dark-only stylesheet. The window's accent color already comes from the palette (so it shifts with theme); two extra accent colors introduced during the UI redesign (active-recording pink, timer green — see section 3.7) got separate, more saturated light-mode variants, since a plain hue swap of the dark pair was unreadable against a white background. The toggle lives in the Settings dialog (not a standalone button, to avoid adding yet another main-window control) and applies immediately plus persists. **Verified:** both themes render correctly end to end, including inside the Settings dialog itself (which inherits the main window's stylesheet).
4. **Enter-to-record shortcut.** Implemented as a `keyPressEvent` override on `OrphivoMainWindow`: toggles recording on Return/Enter unless the transcript editor has focus (left as a newline) or the app is busy (event is still consumed, but nothing toggles). Simpler than the Tkinter implementation: Tkinter needed explicit toplevel-filtering because its `bind_all` binding is global across every window, whereas in Qt the Settings dialog is a separate top-level widget with its own event handling (and its own default button for Enter), so there is no equivalent leak to guard against. **Verified:** Enter starts/stops recording with nothing special focused, inserts a newline in the editor instead, and triggers Save in the Settings dialog (Qt's native default-button behavior) rather than toggling recording in the background.

### 3.7 Qt visual redesign (folded into the history-panel task)

Originally scoped as a separate, later "theme" task, but implemented early at the user's request because it was a small, well-specified set of edits:

- **RTL-appropriate mirroring:** heading, status text, and the record button/timer moved to the top-right of the window; Settings, Copy text, and Save As moved to the left/middle, with Copy text and Save As specifically vertically aligned with the record button's row.
- **A deliberately limited color palette** (max 3 accents, triadic): blue-violet for branding/primary actions (matches the Tkinter dark theme's existing accent), pink-red for the active-recording state and destructive actions, green for the timer.
- Several follow-up layout fixes once the above was in place: a 3-column grid (history/settings | Copy+Save | heading/editor) so Copy text and Save As could sit in the gap between the other two columns without leaving a visual hole in the history/editor row; the Settings button no longer stretches to fill its column; visible radio-button/checkbox indicators (a Qt/QSS quirk — once any stylesheet is set in the ancestor chain, native indicators can become invisible without explicit `::indicator` rules).
- Two Qt-specific bidi rendering issues were found and fixed during this work, both via the same root cause: Qt auto-swaps `AlignLeft`/`AlignRight` for any widget with RTL-direction content unless `Qt.AlignAbsolute` is also set. This affected the heading/status labels and, separately, the transcript editor's placeholder text — `QPlainTextEdit.placeholderText` does not respect the document's text-direction/alignment settings at all (confirmed real typed/transcribed text renders correctly; only the empty-state hint was broken), so it was replaced with a custom overlay `QLabel`.

## 4. End-to-End Recording and Transcription

**Original issue:** [#2 — Test microphone recording and transcription end to end](https://github.com/TheRealMoeid/Orphivo/issues/2)

**Status:** Core end-to-end verification in the new Qt interface is complete; a few secondary items remain open (see checklist).

Historical observations:

- Short Persian sentences were reported as less accurate than longer sentences. This is a transcription-quality observation, not an established code defect.
- Blocking microphone access caused stream initialization failure. Recording worked again after microphone access was restored.
- Silent recordings produced no saved transcript. Empty-output status handling was addressed in earlier work; verify it if the relevant code changes.
- **Occasional Whisper hallucination on silence/near-silence (observed November 8, 2026).** A few times during manual testing, the model produced a plausible-looking Persian sentence when no speech had actually been said. This occurred on both the Tkinter and the Qt UI, confirming it is a model/`src/transcriber.py`-level behavior rather than something either UI introduces. This is a known class of Whisper failure mode (VAD passes a short/noisy segment through and beam search fabricates fluent-sounding text instead of returning empty). Treated as a transcription-quality observation, not a code defect, and out of scope for Issue #12.

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
- [x] Microphone errors are communicated to the user (fixed to use a generic message, see 3.4).
- [ ] Model/transcription errors are communicated to the user (covered automatically; not manually triggered against the real model).
- [ ] Temporary audio is cleaned up (covered automatically; not separately confirmed by manual file-system inspection).
- [ ] The application remains responsive during inference (not explicitly stress-tested).
- [x] Duration label and record button reset correctly across repeated record/stop cycles.

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

### Latest reported test run (after `orphivo-qt-fixes.patch`)

**Date:** November 8, 2026

**Environment:** Windows, Python 3.12.10, pytest 9.1.1.

**Command:**

```powershell
python -m pytest tests -v
```

**Result:**

```text
32 passed
```

(a `PermissionError` was observed during pytest's own teardown of a custom `D:\PytestTemp` directory in earlier runs at this same step — occurred after all tests already reported `PASSED`; a local Windows temp-directory/permissions issue unrelated to the test results or to any file this project's patches touched.)

This run includes regression tests for the RTL-direction and clipboard fixes (3.4), the settings dialog including the change-tracked Save button (3.6.1), the history panel (3.6.2), theme switching (3.6.3), and the Enter-to-record shortcut (3.6.4), plus the original Qt and Tkinter test coverage.

This is the latest test result reported by the user. It has not been independently reproduced by an AI model, but it is now corroborated by manual verification (see sections 1, 3.4, 3.6, and 4).

### What this result establishes, combined with manual verification

With the manual testing recorded in sections 1, 3.4, 3.6, and 4, the following are now established, not just assumed from passing tests:

- Correct visual Persian/bilingual RTL behavior in the actual Qt window (after the 3.4 and 3.7 fixes).
- Successful access to the user's microphone, including the error path when it is unavailable.
- Successful inference using the installed local model, for both speech and silence input.
- Correct end-to-end automatic saving.
- Correct behavior when closing the application during active recording or transcription.
- Correct Copy and Save As behavior (after the 3.4 fix).
- The settings dialog, transcript history panel, dark/light theme switching, and Enter-to-record shortcut all work as implemented (3.6).

Still not established by either tests or manual verification:

- Behavior when closing the application while completely idle.
- UI responsiveness during a long inference run.
- Manually-triggered transcription-failure handling (covered only by automated tests with a mocked transcriber, never a real failure against the local model).
- Manually-triggered transcription-failure error handling (covered only by automated tests).

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

The Qt core workflow (recording, transcription, auto-save, error handling, close behavior) and all four feature-parity gaps (settings dialog, history panel, theme, Enter shortcut — 3.6) are now manually verified, along with the visual redesign (3.7).

The immediate next step is the three remaining secondary verification items before the `app.py` entry-point switch can reasonably be considered:

1. Test closing the application while completely idle.
2. Check UI responsiveness during a long inference run.
3. Manually trigger a transcription failure against the real model (not just the mocked automated test) and confirm the error is communicated clearly.

Recommended order after that:

4. Re-evaluate the recorder private-attribute coupling noted in Issue #12's "Known architectural concern" if/when recorder lifecycle changes are considered — unchanged by any of this work, and present identically in the Tkinter app's own close handling.
5. Only once the three items above are verified, plan the `app.py` entry-point switch as its own task.

Do not replace the Tkinter production entry point until the three items above have been verified.
