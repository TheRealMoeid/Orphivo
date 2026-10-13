import time
from faster_whisper import WhisperModel

MODEL_PATH = r"D:\whisper-large-fa-v1-ct2"
AUDIO_PATH = "persian_test.wav"

def transcribe(device, compute_type):
    print(f"\nLoading model: device={device}, compute_type={compute_type}")
    start = time.perf_counter()

    model = WhisperModel(
        MODEL_PATH,
        device=device,
        compute_type=compute_type,
    )

    print(f"Model loaded in {time.perf_counter() - start:.2f}s")
    start = time.perf_counter()

    segments, info = model.transcribe(
        AUDIO_PATH,
        language="fa",
        beam_size=5,
        vad_filter=True,
    )

    text = "".join(segment.text for segment in segments).strip()

    print(f"Language: {info.language}")
    print(f"Transcription: {text}")
    print(f"Transcription time: {time.perf_counter() - start:.2f}s")

try:
    transcribe("cuda", "int8_float16")
    print("\nGPU transcription succeeded.")
except Exception as exc:
    print(f"\nGPU test failed: {type(exc).__name__}: {exc}")
    print("Trying CPU fallback...")
    transcribe("cpu", "int8")
    print("\nCPU fallback succeeded.")
