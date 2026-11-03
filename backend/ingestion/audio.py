from backend.transcription.whisper_service import transcribe_audio
from backend.pipeline.study_pipeline import build_study_package


def process_audio(file_obj, progress_callback=None):
    try:
        if progress_callback:
            progress_callback(5, "Preparing audio for transcription...")

        # Transcribe uploaded audio
        transcript_data = transcribe_audio(file_obj)

        if progress_callback:
            progress_callback(30, "Audio transcription completed. Preparing study materials...")

        transcript = " ".join(
            segment["text"]
            for segment in transcript_data["segments"]
        ).strip()

        if not transcript:
            return {
                "error": "No speech could be detected in this audio."
            }

        def update_study_progress(percent, message):
            if progress_callback:
                mapped_percent = 30 + int(percent * 0.7)
                progress_callback(mapped_percent, message)

        study_package = build_study_package(
            transcript,
            file_type="audio",
            progress_callback=progress_callback
        )

        return {
            **study_package,
            "transcript_data": transcript_data
        }

    except Exception as e:
        return {
            "error": f"Audio processing failed: {str(e)}"
        }