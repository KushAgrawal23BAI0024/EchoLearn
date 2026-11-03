import os
import tempfile
import ffmpeg

from backend.transcription.whisper_service import transcribe_audio
from backend.pipeline.study_pipeline import build_study_package


def process_video(file_obj, progress_callback=None):
    video_path = None
    audio_path = None

    try:
        if progress_callback:
            progress_callback(5, "Preparing video for processing...")

        # Save uploaded video temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp4"
        ) as temp:
            temp.write(file_obj.read())
            video_path = temp.name

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp:
            audio_path = temp.name

        if progress_callback:
            progress_callback(15, "Extracting audio from video...")

        # Extract audio using FFmpeg
        (
            ffmpeg.input(video_path)
            .output(audio_path, ac=1, ar=16000)
            .overwrite_output()
            .run(quiet=True)
        )

        if progress_callback:
            progress_callback(25, "Transcribing video audio...")

        # Transcribe extracted audio
        with open(audio_path, "rb") as audio_file:
            transcript_data = transcribe_audio(audio_file)

        transcript = " ".join(
            segment["text"]
            for segment in transcript_data["segments"]
        ).strip()

        if not transcript:
            return {
                "error": "No speech could be detected in this video."
            }

        if progress_callback:
            progress_callback(30, "Transcription completed. Generating study materials...")

        def update_study_progress(percent, message):
            if progress_callback:
                mapped_percent = 30 + int(percent * 0.7)
                progress_callback(mapped_percent, message)
        
        # Generate study package
        study_package = build_study_package(
            transcript,
            file_type="video",
            progress_callback=progress_callback
        )

        return {
            **study_package,
            "transcript_data": transcript_data
        }

    except Exception as e:
        return {
            "error": f"Video processing failed: {str(e)}"
        }

    finally:
        # Delete temporary files
        for path in (video_path, audio_path):
            if path and os.path.exists(path):
                os.remove(path)