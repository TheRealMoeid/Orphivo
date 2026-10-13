"""Microphone recording to mono, 16 kHz PCM WAV."""
from __future__ import annotations
import threading
import wave
from pathlib import Path
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000


class AudioRecorder:
    def __init__(self, sample_rate: int = SAMPLE_RATE, device: int | None = None):
        self.sample_rate = sample_rate
        self.device = device
        self._stream = None
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._recording = False

    @property
    def recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        if self._recording:
            raise RuntimeError("Recording is already in progress")
        self._frames = []
        self._recording = True

        def callback(indata, frames, time_info, status):
            if status:
                # Device overflow is non-fatal; keep all audio delivered by PortAudio.
                pass
            with self._lock:
                self._frames.append(indata[:, 0].copy())

        try:
            self._stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="int16", callback=callback, device=self.device)
            self._stream.start()
        except Exception:
            self._recording = False
            self._stream = None
            raise

    def stop(self, output_path: Path) -> Path:
        if not self._recording or self._stream is None:
            raise RuntimeError("Recording is not in progress")
        stream, self._stream = self._stream, None
        self._recording = False
        stream.stop()
        stream.close()
        with self._lock:
            frames = list(self._frames)
        if not frames:
            raise RuntimeError("No audio was captured. Check your microphone input.")
        audio = np.concatenate(frames).astype(np.int16, copy=False)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(audio.tobytes())
        return output_path
