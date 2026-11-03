
import numpy as np
from PIL import Image

from backend.ingestion.pdf import reader
from backend.pipeline.study_pipeline import build_study_package


def process_image(file_obj, progress_callback=None):
    try:
        image = Image.open(file_obj).convert("RGB")

        if progress_callback:
            progress_callback(5, "Extracting text from image using OCR...")

        # Convert PIL Image into a NumPy array for EasyOCR
        image_array = np.array(image)

        extracted_text = reader.readtext(
            image_array,
            detail=0,
            paragraph=True
        )

        full_text = "\n\n".join(extracted_text).strip()

        if not full_text:
            return {"error": "No readable text found in this image."}

        if progress_callback:
            progress_callback(
                30,
                "Image text extraction completed. Generating study materials..."
            )

        def update_study_progress(percent, message):
            if progress_callback:
                mapped_percent = 30 + int(percent * 0.7)
                progress_callback(mapped_percent, message)

        return build_study_package(
            full_text,
            file_type="image",
            progress_callback=update_study_progress
        )

    except Exception as e:
        return {"error": f"Image processing failed: {str(e)}"}
