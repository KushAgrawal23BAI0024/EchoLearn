import os
import gc
import tempfile

import pymupdf as fitz
from PIL import Image
import easyocr

from backend.pipeline.study_pipeline import build_study_package


# Load OCR once
reader = easyocr.Reader(["en"], gpu=False)


def process_pdf(file_obj, progress_callback=None):
    pdf_path = None
    doc = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp:
            temp.write(file_obj.read())
            pdf_path = temp.name

        doc = fitz.open(pdf_path)
        text_parts = []

        total_pages = len(doc)

        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text().strip()

            # OCR scanned pages
            if not page_text:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes(
                    "RGB",
                    (pix.width, pix.height),
                    pix.samples
                )

                page_text = "\n".join(
                    reader.readtext(
                        img,
                        detail=0,
                        paragraph=True
                    )
                )

            text_parts.append(page_text)

            if progress_callback:
                extraction_progress = 5 + int(
                    (page_number / total_pages) * 25
                )

                progress_callback(
                    extraction_progress,
                    f"Extracting text from PDF page {page_number} of {total_pages}..."
                )

        full_text = "\n\n".join(text_parts).strip()

        if not full_text:
            return {"error": "No readable text found in this PDF."}

        def update_study_progress(percent, message):
            if progress_callback:
                mapped_percent = 30 + int(percent * 0.7)
                progress_callback(mapped_percent, message)

        return build_study_package(
            full_text,
            file_type="pdf",
            progress_callback=progress_callback
        )

    except Exception as e:
        return {"error": f"PDF processing failed: {str(e)}"}

    finally:
        if doc is not None:
            doc.close()

        gc.collect()

        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)