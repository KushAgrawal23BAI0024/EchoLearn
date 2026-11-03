import io
import uuid
import threading

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.transcription.whisper_service import transcribe_audio
from backend.summarization.summary_service import generate_summary
from backend.quiz.quiz_service import generate_quiz
from backend.chat.chat_service import chat_with_lecture

from backend.ingestion.router import detect_file_type
from backend.ingestion.audio import process_audio
from backend.ingestion.video import process_video
from backend.ingestion.pdf import process_pdf
from backend.ingestion.image import process_image
from backend.ingestion.ppt import process_ppt
from backend.ingestion.docx import process_docx
from backend.ingestion.text import process_text


app = FastAPI(title="EchoLearn API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "EchoLearn API is running"
    }


# ---------- Job Storage ----------

jobs = {}
jobs_lock = threading.Lock()


# ---------- Request Models ----------

class QuizRequest(BaseModel):
    text: str
    num_questions: int = 5


QuizRequest.model_rebuild()


class ChatRequest(BaseModel):
    question: str
    transcript: str


ChatRequest.model_rebuild()


# ---------- Background Upload Processing ----------

def process_upload_job(job_id, file_bytes, file_type):

    processors = {
        "audio": process_audio,
        "video": process_video,
        "pdf": process_pdf,
        "image": process_image,
        "ppt": process_ppt,
        "docx": process_docx,
        "text": process_text,
    }

    def update_progress(percent, message):
        with jobs_lock:
            jobs[job_id]["progress"] = percent
            jobs[job_id]["message"] = message

    try:
        processor = processors.get(file_type)

        if processor is None:
            raise ValueError("Unsupported file type.")

        update_progress(5, "Preparing your uploaded material...")

        file_obj = io.BytesIO(file_bytes)

        result = processor(
            file_obj,
            progress_callback=update_progress
        )

        if not isinstance(result, dict):
            raise ValueError("The processor returned an invalid result.")

        if "error" in result:
            with jobs_lock:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = result["error"]
                jobs[job_id]["message"] = "Processing failed."
            return

        with jobs_lock:
            jobs[job_id]["result"] = result
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Study package ready!"
            jobs[job_id]["status"] = "completed"

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)
            jobs[job_id]["message"] = "An error occurred during processing."


# ---------- Upload ----------

@app.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):

    file_type = detect_file_type(file.filename)

    processors = {
        "audio": process_audio,
        "video": process_video,
        "pdf": process_pdf,
        "image": process_image,
        "ppt": process_ppt,
        "docx": process_docx,
        "text": process_text,
    }

    if file_type not in processors:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type."
        )

    file_bytes = await file.read()

    job_id = str(uuid.uuid4())

    with jobs_lock:
        jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Upload received. Preparing to process...",
            "result": None,
            "error": None,
        }

    background_tasks.add_task(
        process_upload_job,
        job_id,
        file_bytes,
        file_type
    )

    return {
        "job_id": job_id,
        "status": "processing"
    }


# ---------- Processing Progress ----------

@app.get("/progress/{job_id}")
def get_progress(job_id: str):

    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Processing job not found."
            )

        return {
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"],
            "error": job["error"],
        }


# ---------- Completed Study Package ----------

@app.get("/result/{job_id}")
def get_result(job_id: str):

    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Processing job not found."
            )

        if job["status"] != "completed":
            raise HTTPException(
                status_code=409,
                detail="Study package is not ready yet."
            )

        return job["result"]


# ---------- Transcription ----------

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    return transcribe_audio(file.file)


# ---------- Summarization ----------

@app.post("/summarize")
async def summarize(data: dict):

    text = data.get("text", "")
    summary = generate_summary(text)

    return {"summary": summary}


# ---------- Quiz ----------

@app.post("/quiz")
def quiz(request: QuizRequest):

    questions = generate_quiz(
        request.text,
        request.num_questions
    )

    return {"questions": questions}


# ---------- AI ChatBot ----------

@app.post("/chat")
def chat(request: ChatRequest):

    answer = chat_with_lecture(
        request.question,
        request.transcript
    )

    return {"answer": answer}