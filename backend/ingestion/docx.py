from docx import Document
from backend.pipeline.study_pipeline import build_study_package


def process_docx(file_obj, progress_callback=None):
    try:
        document = Document(file_obj)
        text_parts = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                text_parts.append(text)

        for table in document.tables:
            for row in table.rows:
                row_text = [
                    cell.text.strip()
                    for cell in row.cells
                    if cell.text.strip()
                ]

                if row_text:
                    text_parts.append(" | ".join(row_text))

        full_text = "\n\n".join(text_parts).strip()

        if not full_text:
            return {"error": "No readable text found in this DOCX file."}

        return build_study_package(
            full_text,
            file_type="docx",
            progress_callback=progress_callback
        )

    except Exception as e:
        return {"error": f"DOCX processing failed: {str(e)}"}