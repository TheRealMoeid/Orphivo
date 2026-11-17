# Project Context and AI Handoff

**Last updated:** November 17, 2026
**Repository:** https://github.com/TheRealMoeid/Orphivo
**Project:** Local-first Persian speech-to-text desktop application
**Current focus:** Tkinter-to-PySide6 migration complete — `app.py` now launches Qt; merge to `main` pending approval

---

## 1. Project Overview

Orphivo is a local-first Windows desktop application for transcribing Persian (Farsi) speech into text, using Faster-Whisper/CTranslate2 with a locally stored Persian model. No paid cloud transcription APIs.

## 2. Current Project State

**The PySide6 migration is complete.** `app.py` was switched to launch the Qt application on November 17, 2026, and `python app.py` was manually confirmed to open the Qt window. The Tkinter implementation (`src/ui.py`) is kept untouched as a fallback.

### Current implementation

| Component | File | Status |
|---|---|---|
| Production entry point | `app.py` | Launches the PySide6 window (switched November 17, 2026) |
| Tkinter application | `src/ui.py` | Fallback, untouched; no longer launched by `app.py` |
| Qt editor proof of concept | `src/qt_ui.py` | Implemented |
| Qt main window | `src/qt_main_window.py` | Implemented; fully manually verified, including status-message and busy-state fixes from this round |
| Qt settings dialog | `src/qt_settings_dialog.py` | Implemented and manually verified |
| Qt history panel | `src/qt_history_panel.py` | Implemented and manually verified |
| Audio recording | `src/recorder.py` | Shared component |
| Transcription | `src/transcriber.py` | Shared component |
| Transcript history | `src/history.py` | Existing component |
| Settings | `src/settings.py` | Existing component, shared by both UIs |
| Themes | `src/theme.py` | Existing definitions; integrated into the Qt window |

### Verified (cumulative, through November 16, 2026)

- Manual launch of the Qt main window.
- Microphone recording, including the microphone-unavailable error path.
- End-to-end transcription using the local model: speech, silence, **and two distinct real failure modes** (missing model directory; corrupted model file) — not just the mocked automated test.
- Automatic saving.
- Shutdown behavior during active recording, during active transcription, **and while completely idle.**
- Bilingual/RTL text ordering, Copy/Save As actions.
- Settings dialog, transcript history panel, dark/light theme switching, Enter-to-record shortcut.
- **UI responsiveness during a long inference run** (~7m14s recording, ~4min transcription, confirmed via CPU/memory logging and direct interaction with the app during inference).
- **Status-message correctness**: Copy/Save As/history-load/settings-saved confirmations now correctly coexist with an in-progress transcription instead of being silently overwritten (bug found and fixed this round).
- **Record-button busy-state feedback**: the button now visibly communicates "Transcribing…" instead of looking identical to its normal, clickable state.
- **Entry-point switch**: `python app.py` opens the Qt window (November 17, 2026). Full suite: 57 passed.

### Not yet done

- Commit and push the `app.py` switch and this documentation update, if not already done.
- Merge `feature/pyside6-ui-migration` to `main`, only with the user's explicit approval.
- Optional, later: retire `src/ui.py` and its three test modules.

## 3. Current Development Environment

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

Model directory: `D:\whisper-large-fa-v1-ct2`.

## 4. Repository and Branch State

**Local repository path:** `D:\AI\Orphivo`

**Branch:** `feature/pyside6-ui-migration` (created from `origin/main` at base commit `29c9c7e`)

**Not yet committed as of this update:** the `app.py` switch and this round's documentation updates (`README.md`, `docs/ARCHITECTURE.md`, `docs/KNOWN_ISSUES.md`, this file). The earlier status-revert and button UX fixes were already committed and pushed.

**Recommended next git action:**

```powershell
cd D:\AI\Orphivo
git status
git add -A
git commit -m "Switch app.py entry point to PySide6; keep Tkinter UI as fallback; update docs"
git push -u origin feature/pyside6-ui-migration
```

Do not merge to `main` yet — confirm with the user before any merge.

### First action when resuming

Confirm actual current repo state before any further work:

```powershell
git status
git branch --show-current
git log -1 --oneline
```

## 5. Recent Development History

### Stages 1–4 (through November 14, 2026)

Editor proof of concept → main-window shell → manual verification and bugfix round (RTL bidi, clipboard crash, raw mic-error text) → the four feature-parity gaps (settings dialog, history panel, theme switching, Enter-to-record shortcut), each implemented and verified as its own task, with an RTL-appropriate visual redesign folded into the history-panel task. Full detail in prior revisions of this document and in `docs/KNOWN_ISSUES.md` sections 3.4–3.7.

### Stage 5 — Secondary verification items and status-message fix (November 16, 2026)

With all four feature-parity gaps closed, the three secondary verification items identified at the end of Stage 4 were worked through in order:

1. **Idle-state close** — a 7-step manual checklist (close via X, close via Alt+F4, settings persistence, console warnings, stray temp files, repeat after opening/cancelling Settings). All clean, no issues.
2. **Long-inference UI responsiveness** — a real ~7m14s recording producing ~4 minutes of transcription, with CPU/memory usage logged throughout (`app_usage_log.csv`) and direct interaction with the app confirming it stayed responsive. See `docs/KNOWN_ISSUES.md` 3.9 for the full data.
3. **Real transcription-failure handling** — rather than relying only on the existing mocked automated test, two genuine failures were triggered through the real worker/thread/signal chain: a missing model directory and a corrupted model file. Both produced a readable error dialog, and the app returned to a normal state afterward in both cases. See `docs/KNOWN_ISSUES.md` section 4.

**A real bug was found during item 2**, not from the checklist itself but from the user actively using the app (Copy, Save As, loading history, saving Settings) while a long transcription ran in the background: those actions' confirmation messages were being silently overwritten by the transcription-completion status update if it landed shortly afterward. Fixed via a `_set_status`/`_show_temporary_status` split (permanent state vs. a 3-second auto-reverting temporary message). The user explicitly rejected disabling the affected buttons as an alternative — they wanted the buttons to stay usable at all times, just with correct status feedback.

**A related UX issue was raised and fixed in the same round**: while transcribing, the record button was disabled but looked identical to its normal clickable state, giving no visual indication it was busy rather than broken. Fixed by moving the "Transcribing…" message onto the button itself (with its own muted disabled style) and clearing the status line for that duration, rather than showing the same message in two places. Full detail in `docs/KNOWN_ISSUES.md` section 3.8.

The suite stands at 57 passing tests (earlier revisions of this document reported 60, which was a miscount). All changes delivered as complete files (not patches) per established preference, and confirmed passing/working by the user after each round.

**All migration-blocking verification is now complete.**

### Stage 6 — `app.py` entry-point switch (November 17, 2026)

Scoped as its own task. Options weighed: keep `src/ui.py` as a fallback (chosen) versus removing it together with its three test modules (deferred to a possible later cleanup). Only `app.py` and the three `tests/test_ui_*.py` modules referenced `src.ui`, so the switch was a single-file change: `app.py` now creates a `QApplication`, shows `OrphivoMainWindow`, and exits with the app's return code. No `--legacy` flag was added; nothing required it. The full suite ran at 57 passed, and `python app.py` was manually confirmed to open the Qt window.

**Tkinter rollback:** launch it manually with

```powershell
python -c "from src.ui import PersianSTTApp; PersianSTTApp().mainloop()"
```

or revert the commit that switched `app.py` to Qt.

## 6. Important Existing Issues

### Issue #12 — PySide6 migration

[GitHub Issue #12](https://github.com/TheRealMoeid/Orphivo/issues/12)

All manual verification is complete (Stages 1–5 above) and the `app.py` switch is done (Stage 6). Remaining: merge to `main` with the user's approval.

### Issue #3 — UI layout, focus, and Persian RTL behavior

Both originally-reported Tkinter problems (Enter-key focus leak, Persian caret reordering) are documented historically. The Qt replacement has its own, separately verified RTL/bidi handling (see `docs/KNOWN_ISSUES.md` 3.4 and the feature-parity work), which supersedes this issue's relevance going forward.

### Issue #2 — End-to-end recording and transcription

Now fully verified in the Qt interface, including real (non-mocked) failure modes — see `docs/KNOWN_ISSUES.md` section 4.

### Other historical issues

- [Issue #1 — Make the test suite runnable in a clean virtual environment](https://github.com/TheRealMoeid/Orphivo/issues/1)
- [Issue #4 — Standardize project naming on Orphivo](https://github.com/TheRealMoeid/Orphivo/issues/4)

Check current GitHub status rather than assuming.

## 7. Architecture and Technical Constraints

Unchanged from prior revisions — see `docs/ARCHITECTURE.md` for full detail. Key points: local-first, offline, CPU INT8, UTF-8 transcripts, JSON settings, no new database, no duplicated shared services between UIs.

One minor, non-blocking item identified this round: the corrupted-model-file failure path (section 4 above / `docs/KNOWN_ISSUES.md` section 4) surfaces a raw backend error string rather than a wrapped, friendlier message. Not a defect requiring immediate action — flagged as an optional future polish task.

## 8. Documentation Map

| Document | Purpose |
|---|---|
| `README.md` | Project overview, setup, features, and usage |
| `docs/ARCHITECTURE.md` | Components, responsibilities, data flow, and architectural constraints |
| `docs/KNOWN_ISSUES.md` | Known defects, migration gaps, and verification evidence |
| `PROJECT_CONTEXT.md` | Development history, current state, and AI handoff |

Read all four before making significant changes. Check whether the repository uses `docs/` or the root directory for each document before editing.

## 9. Required Workflow for the Next AI Model

Unchanged: review-first, approval-based. Inspect actual repo state and documentation before proposing anything; present root cause/approach/trade-offs/risks before writing code; wait for approval; deliver changes as complete files (patches were tried earlier in this project and abandoned after repeated apply mismatches); do not commit/merge/switch branches without explicit approval.

## 10. Immediate Recommended Next Step

**Do not re-verify anything listed as done in section 2 and `docs/KNOWN_ISSUES.md` sections 1, 3, and 4 — it is genuinely complete.**

1. Confirm actual current repo state (`git status`, `git branch --show-current`, `git log -1 --oneline`) since the branch may have moved since this document was last updated.
2. Commit and push this round's changes if not already done (see section 4 above for the exact commands).
3. Ask the user whether to merge `feature/pyside6-ui-migration` to `main`; do not merge without explicit approval. Optionally propose retiring `src/ui.py` and its three test modules as a separate, later task.

---

**Handoff principle:** The PySide6 migration is complete, including the `app.py` switch. Remaining work is administrative (commit, merge approval) plus optional cleanup.
