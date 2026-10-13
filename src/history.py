"""File-backed transcript history; no database is required."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path


def list_transcripts(folder: Path) -> list[Path]:
    try:
        return sorted((p for p in folder.glob("*.txt") if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return []


def save_transcript(folder: Path, text: str, now: datetime | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")
    target = folder / f"transcript_{stamp}.txt"
    suffix = 1
    while target.exists():
        target = folder / f"transcript_{stamp}_{suffix}.txt"
        suffix += 1
    target.write_text(text.rstrip() + "\n", encoding="utf-8")
    return target


def read_transcript(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")
