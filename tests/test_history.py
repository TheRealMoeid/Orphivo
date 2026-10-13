from datetime import datetime
from pathlib import Path
from src.history import list_transcripts, read_transcript, save_transcript


def test_save_and_read_transcript(tmp_path: Path):
    path = save_transcript(tmp_path, "سلام دنیا", datetime(2026, 10, 13, 12, 30, 45))
    assert path.name == "transcript_2026-10-13_12-30-45.txt"
    assert read_transcript(path) == "سلام دنیا\n"


def test_timestamp_collision_gets_unique_name(tmp_path: Path):
    stamp = datetime(2026, 10, 13, 12, 30, 45)
    first = save_transcript(tmp_path, "اول", stamp)
    second = save_transcript(tmp_path, "دوم", stamp)
    assert first != second
    assert second.exists()


def test_history_lists_only_txt_newest_first(tmp_path: Path):
    old = tmp_path / "old.txt"
    old.write_text("old", encoding="utf-8")
    new = tmp_path / "new.txt"
    new.write_text("new", encoding="utf-8")
    (tmp_path / "ignore.wav").write_text("x", encoding="utf-8")
    assert {p.name for p in list_transcripts(tmp_path)} == {"old.txt", "new.txt"}
