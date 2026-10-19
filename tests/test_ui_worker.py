import queue
from unittest.mock import Mock

from src.transcriber import PersianTranscriber
from src.ui import PersianSTTApp


def test_missing_model_directory_raises_clear_file_not_found_error(tmp_path):
    transcriber = PersianTranscriber(tmp_path / "missing-model")

    try:
        transcriber.load()
    except FileNotFoundError as exc:
        assert "Local Whisper model folder was not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError for a missing model directory")


def test_transcription_exception_is_queued_for_ui_and_audio_is_removed(tmp_path):
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"mock audio")

    app = PersianSTTApp.__new__(PersianSTTApp)
    app.transcriber = Mock()
    app.transcriber.transcribe.side_effect = RuntimeError("simulated inference failure")
    app.settings = {"auto_save": True}
    app.output_dir = tmp_path
    app.events = queue.Queue()

    app._transcribe_worker(audio_path)

    assert app.events.get_nowait() == ("error", "simulated inference failure")
    assert not audio_path.exists()
