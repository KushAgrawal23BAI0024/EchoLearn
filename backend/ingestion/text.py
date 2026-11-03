
from backend.pipeline.study_pipeline import build_study_package


def process_text(file_obj, progress_callback=None):

    try:
        text = file_obj.read().decode("utf-8-sig").strip()

        if not text:
            return {
                "error": "No readable text found in this file."
            }

        return build_study_package(
            text,
            file_type="text",
            progress_callback=progress_callback
        )

    except UnicodeDecodeError:
        return {
            "error": "Unable to read this file. Please upload a UTF-8 encoded text file."
        }

    except Exception as e:
        return {
            "error": f"Text processing failed: {str(e)}"
        }
