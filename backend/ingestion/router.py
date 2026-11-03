
from pathlib import Path

# Supported extensions

AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
PDF = {".pdf"}
IMAGE = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
PPT = {".ppt", ".pptx"}
DOCX = {".doc", ".docx"}
TEXT = {".txt", ".md"}

def detect_file_type(filename: str):

    ext = Path(filename).suffix.lower()

    if ext in AUDIO:
        return "audio"

    if ext in VIDEO:
        return "video"

    if ext in PDF:
        return "pdf"

    if ext in IMAGE:
        return "image"

    if ext in PPT:
        return "ppt"

    if ext in DOCX:
        return "docx"

    if ext in TEXT:
        return "text"

    return "unsupported"