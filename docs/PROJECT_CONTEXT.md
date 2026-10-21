# Orphivo --- Project Context and Handoff

> Updated 2026-10-21. Handoff for continuing Issue #3 in a new chat. No
> code or repository files were modified during this investigation.

## Project overview

Orphivo is a local-first Windows desktop application for Persian
speech-to-text. It uses Faster-Whisper/CTranslate2 with a locally stored
model and CPU INT8 inference. The UI uses Tkinter. Transcripts are UTF-8
`.txt` files; history is derived from those files, and preferences are
stored as JSON.

Repository: https://github.com/TheRealMoeid/Orphivo

## Architecture and constraints

-   `app.py`: application entry point.
-   `src/ui.py`: main window, transcript editor, history, settings,
    keyboard shortcuts, UI event handling.
-   `src/recorder.py`: microphone capture and WAV output.
-   `src/transcriber.py`: local Faster-Whisper wrapper.
-   `src/history.py`: transcript read/write/list operations.
-   `src/settings.py`: persistent preferences.
-   `src/theme.py`: dark/light palettes.
-   `tests/`: automated regression tests.

Default model path: `D:\whisper-large-fa-v1-ct2`. Do not change
inference/GPU configuration, download a replacement model, introduce a
new UI framework, or make unrelated refactors for Issue #3.

Preserve recording, transcription, transcript display, auto-save,
history, copy/save/delete/open-folder, settings persistence and theme
switching.

## Repository and branch state

Verified by the user on 2026-10-21: - Local directory:
`D:\AI\Orphivo`. - `main` was synchronized with `origin/main` at commit
`f4c2701` before branch creation. - Current branch:
`issue/3-ui-rtl-review`. - Working tree was clean when the branch was
created. - `git pull --ff-only origin main` reported
`Already up to date`. - No code or repository files have been changed
during this Issue #3 investigation.

## Test baseline

Command: `python -m pytest tests -v`

Result on 2026-10-21: **13 passed in 0.58s** on Windows (`win32`),
Python 3.12.10, pytest 9.1.1, project virtual environment. Re-run after
implementation.

## Issue #3 --- UI layout, focus and Persian RTL

Issue: https://github.com/TheRealMoeid/Orphivo/issues/3

The user approved **Approach A**: keep Tkinter and make focused fixes
for confirmed issues. Consider a broader RTL solution only if testing
shows a focused Tkinter fix is insufficient. Do not write code or
generate a patch until the minimal fix plan and tests are agreed.

### Confirmed bug 1: Enter triggers recording while Settings is open

**Reproduction:** Launch app, open Settings, press Enter.

**Actual:** Recording starts in the main window unexpectedly.

**Code lead:** `src/ui.py` binds
`self.bind_all("<Return>", self._enter_shortcut, add="+")`.
`_enter_shortcut()` excludes the transcript widget only; other focus
contexts can trigger recording.

**Expected:** Enter in Settings and unrelated controls must not
start/stop recording. Preserve normal text editing behavior and any
intentional shortcut in appropriate contexts.

### Confirmed bug 2: Persian text visually reorders when clicking to edit

**Reproduction:** Display Persian transcript and click inside the text
to place the caret.

**Actual:** Text visually swaps around the caret: text before the click
appears in front, while text in front appears behind. User supplied
screenshots showing before/after states.

**Code lead:** `src/ui.py` uses a `tk.Text` widget and an `rtl` tag
configured with `justify="right"`. Right justification controls
alignment; it does not guarantee correct bidirectional editing/caret
behavior.

**Expected:** Persian text remains correctly ordered during caret
placement, selection and editing. The exact technical root cause and
best fix are not yet established.

### Checked and working

The user confirmed long transcripts can be scrolled through easily. Do
not add or change scrolling behavior without new evidence.

### Recommended next steps

1.  Inspect current `src/ui.py` and relevant tests.
2.  Propose the smallest reliable focus/shortcut fix.
3.  Investigate a minimal Tkinter-compatible RTL editing solution.
4.  Add automated regression tests where practical. Tkinter's visual
    RTL/caret behavior also requires manual Windows verification.
5.  Do not change unrelated layout or transcription code.

### Manual verification checklist

-   [ ] Enter in Settings does not start/stop recording.
-   [ ] Check Enter behavior in transcript editor, history list, buttons
    and other controls.
-   [ ] Click at several positions in Persian text; visual order does
    not jump around the caret.
-   [ ] Test typing, caret movement, selection, deletion, and mixed
    Persian/English with numbers and punctuation.
-   [ ] Test dark and light themes.
-   [ ] Verify record → stop → transcribe → auto-save → history.
-   [ ] Run `python -m pytest tests -v`.
-   [ ] Update `docs/KNOWN_ISSUES.md` with actual test results.

## Preferred workflow

Inspect code/docs, identify root cause, compare options and risks,
recommend an approach, then wait for approval. After approval, prepare a
`.patch` file, tests, exact apply commands and expected results. The
user applies the patch locally. Work on one issue branch at a time; do
not modify `main` or skip the approval step.

Resume on `issue/3-ui-rtl-review`. First run:

``` powershell
cd D:\AI\Orphivo
git status --short --branch
git diff
git diff --cached
```

No code has been written or patched yet.
