import wave
import time
import sounddevice as sd
from faster_whisper import WhisperModel

MODEL_PATH = r"D:\whisper-large-fa-v1-ct2"
AUDIO_PATH = "persian_test.wav"
SAMPLE_RATE = 16000
DURATION = 8

print("Loading Persian Whisper model on CPU...")
start = time.perf_counter()

model = WhisperModel(
    MODEL_PATH,
    device="cpu",
    compute_type="int8",
)

print(f"Model loaded in {time.perf_counter() - start:.1f} seconds.")
print(f"\nSpeak Persian for {DURATION} seconds after recording starts.")
input("Press Enter when ready...")

print("Recording...")
audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16",
)
sd.wait()

with wave.open(AUDIO_PATH, "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(audio.tobytes())

print(f"Audio saved to {AUDIO_PATH}")
print("Transcribing...")
start = time.perf_counter()

segments, info = model.transcribe(
    AUDIO_PATH,
    language="fa",
    beam_size=5,
    vad_filter=True,
)

text = "".join(segment.text for segment in segments).strip()

print("\n--- RESULTS ---")
print(f"Detected language: {info.language}")
print(f"Transcription: {text}")
print(f"Transcription time: {time.perf_counter() - start:.2f} seconds")
