"""Lazy-loading faster-whisper wrapper using the existing local model."""
from __future__ import annotations
from pathlib import Path
from faster_whisper import WhisperModel
from .settings import DEFAULT_MODEL_PATH


class PersianTranscriber:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self.model_path = Path(model_path)
        self._model: WhisperModel | None = None

    def load(self) -> None:
        if not self.model_path.is_dir():
            raise FileNotFoundError(f"Local Whisper model folder was not found: {self.model_path}")
        self._model = WhisperModel(str(self.model_path), device="cpu", compute_type="int8")

    def transcribe(self, audio_path: Path) -> str:
        if self._model is None:
            self.load()
        segments, _info = self._model.transcribe(str(audio_path), language="fa", beam_size=5, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()
