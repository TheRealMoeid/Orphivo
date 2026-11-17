# Architecture

**Last updated:** November 17, 2026
**Migration status:** Tkinter → PySide6 complete; `app.py` launches the Qt application, Tkinter kept as a fallback

## 1. Architectural Overview

Orphivo is a local-first Windows desktop application for Persian speech-to-text transcription.

Its core workflow is:

1. Capture audio from the user's microphone.
2. Pass the recorded audio to a locally installed Faster-Whisper model.
3. Transcribe the audio into Persian text.
4. Display the transcription in an editable text area.
5. Save the transcript locally.
6. Allow the user to access previously saved transcripts.

The application is designed to work without cloud-based transcription services or paid APIs.

The project currently has two UI implementations:

- **PySide6:** The production UI, launched through `app.py`. Fully implemented and manually verified.
- **Tkinter:** The previous UI, kept untouched in `src/ui.py` as a fallback. No longer launched by `app.py`.

## 2. High-Level Component Structure

Production (launched by `app.py`):

```text
                         app.py
                           |
                           v
                  PySide6 main window
                 src/qt_main_window.py
                           |
        +---------+--------+--------+-----------------+
        |         |        |        |                 |
        v         v        v        v                 v
 qt_settings_  qt_history_  Recorder  Transcriber    History
 dialog.py     panel.py   recorder.py transcriber.py history.py
                              |        |               |
                              v        v               v
                         Microphone  Faster-Whisper  Transcript
                          Capture    / CTranslate2     Files
                                         |
                                         v
                                   Local Model
```

Legacy Tkinter fallback (not launched by `app.py`, uses the same shared services):

```text
                    Tkinter Application
                        src/ui.py
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Recorder     Transcriber     History
```

## 3. Core Components

### 3.1 Application Entry Point — `app.py`

Launches the PySide6 application: creates the `QApplication`, shows `OrphivoMainWindow` from `src/qt_main_window.py`, and exits with the application's return code. Switched from Tkinter on November 17, 2026; `python app.py` was manually confirmed to open the Qt window.

### 3.2 Tkinter UI — `src/ui.py`

The previous desktop interface, kept untouched as a fallback and behavioral reference. It is no longer launched by `app.py`, and its three test modules still run.

**Rollback:** to launch the Tkinter application manually:

```powershell
python -c "from src.ui import PersianSTTApp; PersianSTTApp().mainloop()"
```

To make it the default again, revert the commit that switched `app.py` to Qt.

### 3.3 PySide6 UI Proof of Concept — `src/qt_ui.py`

The initial PySide6 editor experiment investigating Persian RTL/bidi text rendering. Uses a 14 pt font with an explicit `setTextDirection(Qt.LayoutDirection.RightToLeft)` (added as a fix — see `docs/KNOWN_ISSUES.md` 3.4).

### 3.4 PySide6 Main Window — `src/qt_main_window.py`

The main-window implementation. Current responsibilities:

- Main application window and recording controls, including an Enter-key shortcut to start/stop recording (scoped so it doesn't fire while the transcript editor has focus or while busy).
- Recording elapsed-time display.
- Transcript editing, with correct RTL/bidi rendering for mixed Persian/English/digit text.
- Copy and Save As actions, usable at any time including during an active transcription.
- Background transcription via a worker thread/signal pair, keeping inference off the UI thread.
- Automatic saving of non-empty transcription results when auto-save is enabled.
- Temporary audio cleanup after transcription.
- Hosting the settings dialog (`src/qt_settings_dialog.py`) and the transcript history panel (`src/qt_history_panel.py`), both kept in their own modules.
- A palette-driven stylesheet read from `src/theme.py`, switched live via the settings dialog.
- A status-message model split between permanent state text and temporary confirmation messages (see 3.4.3 below).
- A record button whose text and style reflect busy state directly (see 3.4.3 below).

**Status:** Fully manually verified. Core record/transcribe/save workflow, silence handling, microphone-error handling, close behavior during active recording/transcription, settings dialog, history panel, theme switching, Enter-to-record shortcut, idle-state close, long-inference UI responsiveness, and real transcription-failure handling (against the actual model, not just a mocked test) have all been manually tested and confirmed working. See `docs/KNOWN_ISSUES.md` sections 3.4, 3.6, 3.7, 3.8, and 4 for the full history of bugs found and fixed along the way.

### 3.4.1 PySide6 Settings Dialog — `src/qt_settings_dialog.py`

A modal `OrphivoSettingsDialog` covering the transcript folder, auto-save, and theme (dark/light). Reuses `src/settings.py` and `src/theme.py` directly. The Save button is disabled until something in the dialog actually differs from the values it was opened with. Explicit QSS rules give radio/checkbox indicators visible checked states (a Qt/QSS quirk otherwise hides them once any stylesheet is applied in the ancestor chain).

**Status:** Implemented and manually verified.

### 3.4.2 PySide6 History Panel — `src/qt_history_panel.py`

An `OrphivoHistoryPanel` widget listing saved transcripts (newest first), with Open Folder and Delete (confirmed) actions. Emits a `transcript_selected(Path)` signal rather than reaching into the main window's editor directly.

**Status:** Implemented and manually verified.

### 3.4.3 Status messaging and busy-state feedback

Added this round, after manual long-inference testing surfaced a real bug: clicking Copy, Save As, loading a transcript from history, or saving Settings while a transcription was still running would show the correct confirmation message briefly, then have it silently overwritten the moment the background worker's completion signal arrived — there was no guard against a later state-change signal clobbering an earlier, still-relevant confirmation.

**Fix:** `qt_main_window.py` now distinguishes two kinds of status-label update:

- `_set_status(text)` — a genuine state change (recording started/stopped, transcription started/completed/failed, microphone error, the close-while-busy warning). Sets both the visible text and the "base" text to revert to, and cancels any pending temporary-message timer so a stale revert can't later overwrite a newer real state.
- `_show_temporary_status(text)` — a transient confirmation (Copy, Save As, loading a transcript, saving Settings). Shows the message immediately, then a single-shot 3-second `QTimer` reverts the label back to whatever the current base state is.

Disabling the Copy/Save buttons during busy state was considered and explicitly rejected — the buttons stay usable throughout; only the status *message* needed the fix.

A related UX gap was fixed at the same time: while transcribing, the record button was disabled but visually identical to its normal enabled state (the button's own QSS override for its blue "active" look took priority over the generic disabled style), so it looked broken rather than busy. The status line also duplicated "Transcribing locally on CPU…" right next to it. Fixed by moving that one message onto the button itself — it now reads "Transcribing…" with a dedicated muted `:disabled` QSS rule — and clearing the status line to empty for the duration, freeing it for the temporary confirmations described above without a redundant second "Transcribing…" competing with them.

**Status:** Implemented and manually verified; covered by `tests/test_qt_status_revert.py`.

### 3.5 Audio Recorder — `src/recorder.py`

Handles microphone audio capture via `sounddevice`. Both UI implementations share this component.

The Qt main window accesses private recorder attributes (`_stream` and `_recording`) during close handling — an architectural concern carried over unchanged from the same pattern already present in the Tkinter app's own close handling. Not a new issue introduced by the migration; still worth evaluating before any recorder lifecycle changes.

### 3.6 Transcription Engine — `src/transcriber.py`

Uses Faster-Whisper/CTranslate2 with a locally stored Persian model, `fa` language selection, CPU INT8 inference. Development model directory: `D:\whisper-large-fa-v1-ct2`.

This round's real transcription-failure testing exercised two genuine failure paths through the actual worker/thread/signal chain:

- A missing/misnamed model directory, which surfaces `transcriber.py`'s own `FileNotFoundError` message cleanly through to the error dialog.
- A corrupted model file inside an otherwise-valid model directory, which surfaces a raw CTranslate2/faster-whisper backend error string — readable, but not wrapped in a friendlier message the way the microphone-error path was (see `docs/KNOWN_ISSUES.md` 3.4 item 3). Worth a future small polish task if a friendlier message is wanted, but not blocking: the dialog is clear enough, and the app recovers to a normal state afterward in both cases.

### 3.7 Transcript History — `src/history.py`

UTF-8 `.txt` storage. Shared and compatible across both UIs.

### 3.8 Settings — `src/settings.py`

JSON-backed settings, shared by both UIs, including theme.

### 3.9 Theme — `src/theme.py`

`PALETTES` (dark/light), now fully integrated into the Qt window via a palette-driven QSS builder in `qt_main_window.py`. Two extra accent colors (active-recording, timer) have their own light/dark variants outside `PALETTES`, since a plain hue rotation of the dark pair was unreadable against a light background.

## 4. PySide6 Threading and Transcription Flow

```text
User stops recording
        |
        v
Recorded audio is handed to transcription worker
        |
        v
Worker runs local Faster-Whisper inference
        |
        v
Worker emits completion/result signal
        |
        v
Main window receives the result
        |
        +--------------------------+
        |                          |
        v                          v
Update transcript editor     Auto-save enabled?
                                   |
                              +----+----+
                              |         |
                             Yes        No
                              |         |
                              v         v
                         Save result   Keep result
                              |
                              v
                     Remove temporary audio
```

**Fully manually verified**, including long-running inference: a real ~7m14s recording produced ~4 minutes of CPU INT8 transcription, during which CPU/memory logging showed a steady single-core-equivalent ~25% CPU load (consistent with the worker thread doing the work, not the UI thread) and the window remained interactive — draggable, resizable, and responsive to clicks — throughout. The diagram's error path (worker signals a failure instead of a result) has also now been exercised with two real failures, not just the mocked automated test; see 3.6 above.

## 5. Data and Storage

| Data | Storage / handling |
|---|---|
| Recorded audio | Temporary audio used by the recording/transcription workflow |
| Transcripts | UTF-8 `.txt` files |
| Application settings | JSON |
| Speech recognition model | Local model directory |
| UI state | Managed by the respective UI implementation |

## 6. Testing Structure

| Test module | Area |
|---|---|
| `tests/test_history.py` | Transcript history and persistence |
| `tests/test_qt_ui.py` | PySide6 editor proof of concept |
| `tests/test_qt_main_window.py` | Qt main window, worker, settings/history wiring, theme, Enter shortcut |
| `tests/test_qt_settings_dialog.py` | Qt settings dialog (folder, auto-save, theme, change-tracked Save button) |
| `tests/test_qt_history_panel.py` | Qt transcript history panel |
| `tests/test_qt_status_revert.py` | Status-message permanent-vs-temporary revert behavior, record-button busy state |
| `tests/test_recorder.py` | Audio recorder |
| `tests/test_settings.py` | Application settings |
| `tests/test_ui_shortcuts.py` | Tkinter fallback UI shortcuts |
| `tests/test_ui_status.py` | Tkinter fallback UI status behavior |
| `tests/test_ui_worker.py` | Tkinter fallback UI worker behavior |

```powershell
python -m pytest tests -v
```

**Latest reported result (November 17, 2026):** `57 passed`. Earlier revisions reported 60, which was a miscount.

Automated tests, combined with the manual verification recorded throughout this document and in `docs/KNOWN_ISSUES.md`, now cover the complete desktop workflow: microphone, local model (including real failure modes), record/transcribe/save, error handling, close behavior during active operations and while idle, settings, history, theme, the Enter shortcut, and UI responsiveness during long inference runs.

## 7. Current Architectural Boundaries

1. `app.py` launches the PySide6 application. `src/ui.py` (Tkinter) is kept as an untouched fallback; removing it is a separate, future decision.
2. Shared services (recording, transcription, settings, history) are not duplicated between UIs.
3. UI code should not depend on private implementation details of shared services (see the recorder note in 3.5 — an existing, not new, concern).
4. Local transcription remains independent of hosted APIs.
5. Existing transcript files and settings remain compatible across both UIs.

## 8. Known Architectural Gaps

All migration-blocking verification is now complete. What remains:

- The Qt main window's access to private recorder attributes (`_stream`, `_recording`) during close handling — present identically in the Tkinter app, not a new issue, but still worth evaluating if recorder lifecycle work is ever planned.
- `src/ui.py` and its three test modules remain in the repository as a fallback. Retiring them is an optional future cleanup, not required for anything.
- The corrupted-model-file failure path surfaces a raw backend error string rather than a wrapped, friendlier message (see 3.6) — a minor, non-blocking polish item if ever prioritized.
- A pre-existing, out-of-scope model behavior: Whisper occasionally hallucinates plausible Persian text on silence/near-silence input, observed on both UIs. Not a migration regression.

## 9. Guidance for Future Development

Before implementing additional work:

1. Inspect the current Git branch and working tree.
2. Read `README.md`, `PROJECT_CONTEXT.md`, and `KNOWN_ISSUES.md`.
3. Review GitHub Issue #12's current state and whether `feature/pyside6-ui-migration` has been merged to `main`.
4. If retiring the Tkinter fallback, present it as its own scoped task first (it removes `src/ui.py` and `tests/test_ui_shortcuts.py`, `tests/test_ui_status.py`, `tests/test_ui_worker.py`).
