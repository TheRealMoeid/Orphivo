# Architecture

**Last updated:** November 8, 2026  
**Migration status:** Tkinter → PySide6 (in progress)

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

- **Tkinter:** The established application, still launched through `app.py`.
- **PySide6:** The replacement UI under development. Its main-window implementation is separate from the production entry point.

These implementations should not be treated as interchangeable or as having complete feature parity.

## 2. High-Level Component Structure

```text
                         app.py
                           |
                           v
                    Tkinter Application
                        src/ui.py
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Recorder     Transcriber     History
       src/recorder.py src/transcriber.py src/history.py
             |             |             |
             v             v             v
        Microphone    Faster-Whisper   Transcript
         Capture       / CTranslate2    Files
                           |
                           v
                     Local Model
```

The PySide6 implementation is currently a separate UI path:

```text
             Experimental PySide6 UI
                         |
              +----------+----------+
              |                     |
              v                     v
           qt_ui.py          qt_main_window.py
                                    |
                    +---------------+---------------+
                    |               |               |
                    v               v               v
                 Recorder       Transcriber       History
```

The diagrams describe the intended component relationships and current implementation organization. They do not establish that every workflow has been manually verified.

## 3. Core Components

### 3.1 Application Entry Point — `app.py`

`app.py` is the current application entry point.

It launches the existing Tkinter application through `PersianSTTApp` from `src.ui`.

**Current status:**

- Tkinter remains the production UI.
- The entry point has not been migrated to PySide6.
- The Qt main window must be tested before considering an entry-point change.

### 3.2 Tkinter UI — `src/ui.py`

This module contains the established desktop interface.

It is responsible for the existing application's UI and interaction flow, including its recording and transcription controls.

It should be treated as the current behavioral reference during the migration. Existing functionality should not be removed merely because the new Qt interface has a corresponding control.

### 3.3 PySide6 UI Proof of Concept — `src/qt_ui.py`

This module contains the initial PySide6 UI experiment.

It was introduced to investigate Persian text editing and right-to-left alignment in Qt.

The editor uses a 14 pt font. Text alignment is configured through Qt's document and text-option APIs rather than a nonexistent `QPlainTextEdit.setAlignment()` method.

The module is covered by `tests/test_qt_ui.py`.

### 3.4 PySide6 Main Window — `src/qt_main_window.py`

This module contains the newer PySide6 main-window implementation.

Its current responsibilities include:

- Main application window and recording controls, including an Enter-key shortcut to start/stop recording (scoped so it doesn't fire while the transcript editor has focus or while busy).
- Recording elapsed-time display.
- Transcript editing, with correct RTL/bidi rendering for mixed Persian/English/digit text.
- Copy and Save As actions.
- Background transcription.
- Automatic saving of non-empty transcription results when auto-save is enabled.
- Temporary audio cleanup after transcription.
- Hosting the settings dialog (`src/qt_settings_dialog.py`) and the transcript history panel (`src/qt_history_panel.py`), both kept in their own modules.
- A palette-driven stylesheet read from `src/theme.py`, switched live via the settings dialog.

The transcription worker uses Qt threading and signals to keep the transcription task outside the main UI thread.

**Status (updated November 14, 2026):** The main window has passed its automated tests and has been manually launched and tested by the user. Its core record/transcribe/save workflow, silence handling, microphone-error handling, close behavior during active recording or transcription, settings dialog, transcript history panel, theme switching, and Enter-to-record shortcut are all manually verified. Several bugs found across this testing (bidi text ordering in two separate places, a clipboard crash, a raw backend error shown to the user, invisible radio/checkbox indicators) were fixed and re-verified; see `docs/KNOWN_ISSUES.md` sections 3.4, 3.6, and 3.7. Three secondary items remain unverified: idle-state close, long-inference UI responsiveness, and a manually-triggered transcription failure (section 8 below).

### 3.4.1 PySide6 Settings Dialog — `src/qt_settings_dialog.py`

Kept in its own module, separate from `qt_main_window.py`, so Qt feature work can grow independently. A modal `OrphivoSettingsDialog` covering the transcript folder, auto-save, and theme (dark/light). Reuses `src/settings.py` and `src/theme.py` directly rather than introducing second settings/theme systems for the Qt UI. The Save button is disabled until something in the dialog actually differs from the values it was opened with.

**Status:** Implemented and manually verified (`docs/KNOWN_ISSUES.md` section 3.6.1).

### 3.4.2 PySide6 History Panel — `src/qt_history_panel.py`

Also kept in its own module. An `OrphivoHistoryPanel` widget listing saved transcripts (newest first), with Open Folder and Delete (confirmed) actions. Emits a `transcript_selected(Path)` signal rather than reaching into the main window's editor directly, so the panel has no dependency on how its content is displayed.

**Status:** Implemented and manually verified (`docs/KNOWN_ISSUES.md` section 3.6.2).

### 3.5 Audio Recorder — `src/recorder.py`

This module handles microphone audio capture.

The project uses `sounddevice` for recording.

Both UI implementations rely on the recorder component rather than implementing microphone capture independently.

The recorder's internal implementation and lifecycle should be inspected before making changes to its threading, stream management, or shutdown behavior.

In particular, the Qt main window currently accesses private recorder attributes (`_stream` and `_recording`) during its close handling. This is an architectural concern because the UI depends on implementation details that should ideally be encapsulated by the recorder.

Do not change the recorder lifecycle without first understanding the existing implementation and its tests.

### 3.6 Transcription Engine — `src/transcriber.py`

This module provides the transcription functionality.

The application uses:

- Faster-Whisper
- CTranslate2
- A locally stored Persian model
- Persian language selection (`fa`)
- CPU INT8 inference in the established development configuration

The development model directory has been:

```text
D:\whisper-large-fa-v1-ct2
```

The model is expected to be available locally. The application should not silently introduce a cloud transcription dependency or automatic model downloads.

The exact model-loading and inference behavior should be confirmed from the source code before changing it.

### 3.7 Transcript History — `src/history.py`

This module handles transcript persistence and history.

The established storage format is ordinary UTF-8 text (`.txt`).

The application should retain compatibility with existing transcript files during the UI migration.

Do not introduce a database or a new transcript format without a specific requirement and migration plan.

### 3.8 Settings — `src/settings.py`

This module handles persistent application settings using JSON.

UI-specific changes should preserve the existing settings behavior where applicable.

Before adding new settings, inspect the existing schema, defaults, and tests. Avoid creating duplicate settings systems for Tkinter and Qt.

### 3.9 Theme — `src/theme.py`

This module contains the existing theme definitions (`PALETTES`, dark/light).

**Status (updated November 14, 2026):** now integrated into the Qt window. `qt_main_window.py` reads `PALETTES` directly into a palette-driven QSS stylesheet builder, replacing what had been a hardcoded dark-only style. The window's primary accent color comes from the palette (so it already shifts with theme). Two extra accent colors introduced during the Qt visual redesign (active-recording state, timer) are not part of `PALETTES` and have their own separate light/dark variants defined in `qt_main_window.py`, since a plain hue rotation of the dark pair was unreadable against a light background. The toggle lives in the settings dialog (`src/qt_settings_dialog.py`) rather than a standalone button. See `docs/KNOWN_ISSUES.md` section 3.6.3.

## 4. PySide6 Threading and Transcription Flow

The Qt main-window implementation uses a background worker for transcription.

The intended workflow is:

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

The purpose of the background worker is to prevent model inference from blocking the Qt event loop.

The worker and its tests are covered by `tests/test_qt_main_window.py`.

The diagram represents the implemented design. As of November 8, 2026, actual microphone capture, model inference, signal delivery, saving, and shutdown (during recording and during transcription) have all been manually tested and verified. Idle-state shutdown and responsiveness during a long inference run remain untested.

## 5. Data and Storage

| Data | Storage / handling |
|---|---|
| Recorded audio | Temporary audio used by the recording/transcription workflow |
| Transcripts | UTF-8 `.txt` files |
| Application settings | JSON |
| Speech recognition model | Local model directory |
| UI state | Managed by the respective UI implementation |

The application should remain local-first.

Avoid introducing external services, unnecessary persistence layers, or format changes without a clear architectural reason.

## 6. Testing Structure

The repository includes tests for the existing application and the Qt migration.

Relevant test modules include:

| Test module | Area |
|---|---|
| `tests/test_history.py` | Transcript history and persistence |
| `tests/test_qt_ui.py` | PySide6 editor proof of concept |
| `tests/test_qt_main_window.py` | Qt main window, worker, settings/history wiring, theme, Enter shortcut |
| `tests/test_qt_settings_dialog.py` | Qt settings dialog (folder, auto-save, theme, change-tracked Save button) |
| `tests/test_qt_history_panel.py` | Qt transcript history panel |
| `tests/test_recorder.py` | Audio recorder |
| `tests/test_settings.py` | Application settings |
| `tests/test_ui_shortcuts.py` | Existing UI shortcuts |
| `tests/test_ui_status.py` | Existing UI status behavior |
| `tests/test_ui_worker.py` | Existing UI worker behavior |

Run the suite from the repository root:

```powershell
python -m pytest tests -v
```

**Latest reported result (November 14, 2026):**

```text
32 passed
```

Regression tests were added across the RTL-text-direction and clipboard fixes, the settings dialog, the history panel, theme switching, and the Enter-to-record shortcut; see `docs/KNOWN_ISSUES.md` sections 3.4 and 3.6. This result is based on the user's reported test run and is now corroborated by the user's manual verification of the same workflow (same sections).

Automated tests alone still do not replace manual testing, but the core desktop workflow — microphone, local model, record/transcribe/save, error handling, close behavior during active operations, settings, history, theme, and the Enter shortcut — has now had both. Three secondary items (idle close, long-inference responsiveness, a manually-triggered transcription failure) still have only automated coverage, if any.

## 7. Current Architectural Boundaries

The following boundaries should be respected while the migration is in progress:

1. `app.py` remains connected to the Tkinter application.
2. The Qt implementation remains separate until its required behavior is verified.
3. Shared services such as recording, transcription, settings, and history should not be duplicated unnecessarily.
4. UI code should not depend on private implementation details of shared services.
5. Local transcription must remain independent of hosted APIs.
6. Existing transcript files and settings should remain compatible.
7. UI migration should preserve existing functionality unless a deliberate product decision changes it.

## 8. Known Architectural Gaps

Resolved as of November 8, 2026 (see `docs/KNOWN_ISSUES.md` sections 1, 3.4, 4 for detail):

- ~~The Qt main window has not been manually launched.~~ Manually launched and tested.
- ~~Qt microphone recording and shutdown behavior have not been manually verified.~~ Verified, including the microphone-error path and shutdown during active recording/transcription.
- ~~End-to-end local transcription through the Qt interface has not been verified.~~ Verified for both speech and silence input.
- ~~Automatic saving through the complete Qt workflow has not been manually verified.~~ Verified.

Resolved as of November 14, 2026 (see `docs/KNOWN_ISSUES.md` sections 1, 3.6, 3.7 for detail):

- ~~Complete feature parity with the Tkinter application has not been established.~~ The four gaps (theme integration, in-window settings dialog, transcript history panel, Enter-to-record shortcut) are each implemented and manually verified.

Still open:

- The Qt main window's access to private recorder attributes (`_stream`, `_recording`) during close handling remains, carried over unchanged from the same pattern already present in the Tkinter app's `_on_close`. Still worth evaluating, but not a new issue introduced by the migration.
- The production entry point has not been migrated; do not switch it until the three items below are verified.
- Idle-state shutdown, UI responsiveness during a long inference run, and a manually-triggered transcription failure against the real model have not been explicitly tested — the last of these has only mocked automated coverage.

These are migration gaps, not evidence that the corresponding functionality is necessarily broken.

## 9. Guidance for Future Development

Before implementing additional migration work:

1. Inspect the current Git branch and working tree.
2. Read `README.md`, `PROJECT_CONTEXT.md`, and `KNOWN_ISSUES.md`.
3. Inspect the relevant implementation and tests.
4. Review GitHub Issue #12 and any related open issues.
5. Identify the actual root cause or missing behavior before proposing changes.
6. Present implementation options, trade-offs, risks, and a recommendation before writing code.
7. Keep each task isolated to its own branch.
8. Provide repository modifications as a `.patch` file for the user to apply and test.

Do not assume the project is ready for a production switch to PySide6 simply because the current automated test suite passes.
