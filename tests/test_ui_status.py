from pathlib import Path

from src.ui import _completion_status


def test_empty_transcription_reports_no_speech_and_no_save():
    assert _completion_status("", None) == "No speech detected · nothing to save"


def test_whitespace_transcription_reports_no_speech_and_no_save():
    assert _completion_status(" \n\t ", None) == "No speech detected · nothing to save"


def test_saved_transcription_reports_saved_filename():
    assert _completion_status("سلام", Path("transcript-123.txt")) == (
        "Transcription complete · saved to transcript-123.txt"
    )


def test_nonempty_transcription_without_saved_file_reports_not_auto_saved():
    assert _completion_status("سلام", None) == "Transcription complete · not auto-saved"
