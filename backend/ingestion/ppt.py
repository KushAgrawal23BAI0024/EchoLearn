import os
import tempfile

from pptx import Presentation
from backend.pipeline.study_pipeline import build_study_package


def process_ppt(file_obj, progress_callback=None):
    ppt_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pptx"
        ) as temp:
            temp.write(file_obj.read())
            ppt_path = temp.name

        presentation = Presentation(ppt_path)
        text_parts = []

        for slide_number, slide in enumerate(
            presentation.slides,
            start=1
        ):
            slide_text = []

            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())

            if slide_text:
                text_parts.append(
                    f"Slide {slide_number}\n" + "\n".join(slide_text)
                )

        full_text = "\n\n".join(text_parts).strip()

        if not full_text:
            return {
                "error": "No readable text found in this PowerPoint."
            }

        return build_study_package(
            full_text,
            file_type="ppt",
            progress_callback=progress_callback
        )

    except Exception as e:
        return {
            "error": f"PowerPoint processing failed: {str(e)}"
        }

    finally:
        if ppt_path and os.path.exists(ppt_path):
            os.remove(ppt_path)