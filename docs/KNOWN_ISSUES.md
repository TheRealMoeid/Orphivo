# Known Issues and Verification Notes

Updated: 2026-10-21

GitHub Issues are the source of truth for active work and current
status. This file records observations and verification evidence; do not
mark a defect fixed until verified.

## Active GitHub issues

-   [#1 --- Make the test suite runnable in a clean virtual
    environment](https://github.com/TheRealMoeid/Orphivo/issues/1)
-   [#2 --- Test microphone recording and transcription end to
    end](https://github.com/TheRealMoeid/Orphivo/issues/2)
-   [#3 --- Review layout, focus, and Persian RTL
    behavior](https://github.com/TheRealMoeid/Orphivo/issues/3)
-   [#4 --- Standardize project naming on
    Orphivo](https://github.com/TheRealMoeid/Orphivo/issues/4)

## Latest test evidence

**Date:** 2026-10-21\
**Environment:** Windows (`win32`), Python 3.12.10, pytest 9.1.1,
project virtual environment.

Command:

``` powershell
python -m pytest tests -v
```

Result: **13 passed in 0.58s**. This is the pre-change baseline on
branch `issue/3-ui-rtl-review`. Re-run after implementation. Automated
tests do not establish visual RTL/caret correctness.

## Issue #3 --- Confirmed UI defects

Issue: https://github.com/TheRealMoeid/Orphivo/issues/3

### 1. Enter triggers recording while Settings is open

**Status:** Confirmed by user; not fixed.

**Reproduction:** 1. Run `python app.py`. 2. Open Settings. 3. Press
Enter.

**Actual:** Recording starts in the main window unexpectedly.

**Expected:** Enter while Settings or an unrelated control has focus
must not start or stop recording.

**Code lead:** `src/ui.py` binds `<Return>` globally with `bind_all()`
and `_enter_shortcut()` triggers recording unless the transcript editor
has focus. Inspect event routing/focus before choosing a fix.

**Verify:** Enter in Settings, history list, buttons and other controls;
preserve appropriate text-editor behavior and intentional recording
shortcuts.

### 2. Persian text visually reorders when placing the caret

**Status:** Confirmed by user; root cause and fix not yet established.

**Reproduction:** 1. Display a Persian transcript in the main text
editor. 2. Click inside the text to position the caret.

**Actual:** Text appears to swap visual positions around the caret: text
before the click appears in front, and text in front appears behind. The
user supplied before/after screenshots.

**Expected:** Persian text remains correctly ordered during caret
placement, selection and editing.

**Code lead:** `src/ui.py` uses `tk.Text` and applies an `rtl` tag
configured with `justify="right"`. Right alignment is not equivalent to
full bidirectional text editing.

**Plan:** First try a focused solution compatible with Tkinter (Approach
A). Test Persian-only and mixed Persian/English text, numbers and
punctuation. Consider a broader RTL approach only if a focused solution
proves inadequate. Do not replace the UI framework without separate
discussion and approval.

### 3. Long-transcript scrolling

**Status:** Tested and working; no change needed based on current
evidence.

The user confirmed long transcripts can be scrolled through easily.

## Other UI review items not yet verified

These remain review items, not confirmed defects: - Layout at
minimum/default/maximized window sizes. - Persian punctuation and
mixed-direction text in dark and light themes. - Keyboard tab order and
focus visibility. - Settings dialog positioning, initial focus,
cancel/save/close behavior. - Consistency of recording, processing,
success and error labels.

## Historical Issue #2 observations

-   Short Persian sentences were reported as less accurate than longer
    sentences; this is a quality observation, not yet attributed to a
    code defect.
-   Blocking microphone access caused stream initialization failure;
    recording worked again after access was restored.
-   Silent recordings produced no saved transcript. Status handling for
    empty output was addressed in earlier work; verify related behavior
    if that path changes.

## Triage policy

-   Separate confirmed defects from hypotheses and enhancements.
-   Record reproduction steps, expected/actual behavior, environment and
    verification results.
-   Add automated regression tests where practical. RTL caret/rendering
    behavior also needs manual Windows testing.
-   Close issues only after fixes are verified.
-   Keep Issue #3 focused on UI behavior; avoid unrelated changes to
    model configuration, GPU support, persistence architecture or other
    modules.
