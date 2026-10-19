from unittest.mock import Mock, patch

from src.recorder import AudioRecorder


def test_failed_stream_start_resets_recorder_state_and_allows_retry():
    failed_stream = Mock()
    failed_stream.start.side_effect = RuntimeError("simulated unavailable microphone")
    working_stream = Mock()

    with patch("src.recorder.sd.InputStream", side_effect=[failed_stream, working_stream]):
        recorder = AudioRecorder()

        try:
            recorder.start()
        except RuntimeError as exc:
            assert "simulated unavailable microphone" in str(exc)
        else:
            raise AssertionError("start() should propagate a stream-start failure")

        assert recorder.recording is False
        assert recorder._stream is None

        recorder.start()

    assert recorder.recording is True
    assert recorder._stream is working_stream

    # Keep this test independent of audio hardware and leave no active stream.
    recorder._recording = False
    recorder._stream = None
