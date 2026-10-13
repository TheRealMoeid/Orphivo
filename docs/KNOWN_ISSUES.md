# Known Issues and Verification Notes

This document records issues and verification gaps observed during early local testing. GitHub Issues are the source of truth for active work, discussion, and resolution status. The following issues were open on 2026-10-13:

- [#1 — Make the test suite runnable in a clean virtual environment](https://github.com/TheRealMoeid/Orphivo/issues/1)
- [#2 — Test microphone recording and transcription end to end](https://github.com/TheRealMoeid/Orphivo/issues/2)
- [#3 — Review layout, focus, and Persian RTL behavior](https://github.com/TheRealMoeid/Orphivo/issues/3)
- [#4 — Standardize project naming on Orphivo](https://github.com/TheRealMoeid/Orphivo/issues/4)

Issues #1 and #4 address known setup/documentation gaps. Issues #2 and #3 are verification/review tasks; their existence does not establish that the reviewed behavior is defective.

Update this register when evidence changes. Do not mark an item resolved until the relevant behavior has been verified.

## Confirmed from the first test run

### 1. Test runner is not installed in the project virtual environment

**Evidence:** `.\.venv\Scripts\python.exe -m pytest tests -v` returned `No module named pytest`.

**Impact:** The project's own virtual environment cannot run the test suite until the test dependency is installed.

**Recommended action:** Add `pytest` to a development dependency file (for example, `requirements-dev.txt`) and install it using the venv's interpreter. Keep runtime and development dependencies clearly separated if practical.

**Verification:** `.\.venv\Scripts\python.exe -m pytest tests -v` should collect and execute tests using the virtual environment.

### 2. Test imports fail when using the global pytest executable

**Evidence:** The bare `pytest tests -v` command ran under `C:\Users\VAHABI\AppData\Local\Programs\Python\Python312\python.exe` and failed collection with `ModuleNotFoundError: No module named 'src'` in `tests/test_history.py` and `tests/test_settings.py`.

**Impact:** Tests do not reach assertion execution in this invocation.

**Likely area to investigate:** Test discovery/import configuration and whether the test command is using the intended interpreter. Do not assume this is solely a packaging defect until the tests are rerun with the venv interpreter.

**Recommended action:** First install pytest into `.venv` and run `python -m pytest`. If imports still fail, add a deliberate package/test configuration (for example, `pyproject.toml` with pytest settings and an installable project package) rather than relying on incidental working-directory behavior.

**Verification:** All tests collect and run from the documented command in a clean virtual environment.

## Manual observations from the screenshot

### 3. Settings window and main window are both visible at once

The screenshot shows the settings dialog overlapping the main application. This may be intentional while the settings window is open, but the interaction should be reviewed for focus, modality, and positioning.

**Question to resolve:** Should Settings be a modal dialog that blocks interaction with the main window, or a non-modal window that can remain open alongside it?

### 4. Main-window layout and controls need a UI review

The screenshot shows a wide transcript area, a history pane, recording control, elapsed time, save/copy controls, and a settings button. The current layout is usable enough for initial testing, but visual polish and resizing behavior still need review.

Items to verify:
- Layout behavior at smaller window sizes and when maximized.
- Clear distinction between recording, processing, success, and error states.
- Whether the recording control's label and visual state change consistently when recording starts/stops.
- Whether the theme toggle is visible and usable at the bottom of the main window as intended.
- Whether Persian text is readable and aligned right-to-left in both themes.

These are review items from the screenshot, not confirmed functional defects.

### 5. End-to-end audio behavior is not yet fully verified

The screenshot shows a short transcript and a status indicating that a transcript file was saved. It does not establish transcription accuracy, microphone error handling, performance across longer recordings, or behavior when the model cannot be loaded.

**Recommended manual checks:**
- Record a clear Persian sentence and compare the output with the spoken words.
- Test a longer recording.
- Test a missing/blocked microphone.
- Test a missing or invalid model directory.
- Confirm the app remains responsive while transcribing.
- Confirm autosave errors are visible and do not silently discard the transcript.

## Triage policy

- Keep one independently actionable bug per GitHub Issue.
- Include reproduction steps, expected behavior, actual behavior, environment, and logs.
- Separate confirmed defects from usability questions and future enhancements.
- Close issues only after the fix is tested and the verification result is recorded.
