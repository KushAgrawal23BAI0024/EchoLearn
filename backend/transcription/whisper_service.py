import os
import time
import tempfile

from faster_whisper import WhisperModel

# ---------- Load model only once ----------

MODEL_SIZE = "base"

print(f"Loading Faster-Whisper model ({MODEL_SIZE})...")

model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8"
)

print("Whisper model loaded successfully!")

# ---------- Main ----------

def transcribe_audio(file_obj):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
        temp.write(file_obj.read())
        temp_path = temp.name

    try:
        print("Starting Whisper transcription...")
        start_time = time.time()

        segments, info = model.transcribe(
            temp_path,
            beam_size=2,                  # Faster than 5 with almost identical quality
            best_of=2,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=400
            )
        )

        segment_list = []
        duration = 0

        for seg in segments:
            duration = seg.end

            segment_list.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip()
            })

        elapsed = time.time() - start_time
        print(f"Whisper finished in {elapsed:.1f} seconds.")
        print(f"Generated {len(segment_list)} transcript segments.")

        return {
            "segments": segment_list,
            "language": info.language,
            "duration": round(duration, 2)
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)