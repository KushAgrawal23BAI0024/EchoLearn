# EchoLearn

**Making learning more interactive, accessible, and intelligent.**

EchoLearn is an AI-powered learning assistant that transforms educational materials into interactive study resources. It helps students understand and revise lecture content through AI-generated summaries, quizzes, flashcards, key terms, and concept graphs.

## Features

- Audio and video transcription
- PDF, PowerPoint, Word document, and image processing
- AI-generated study notes and summaries
- Automatic quiz generation
- Interactive revision flashcards
- Important key-term extraction
- Concept graph generation
- AI-powered tutor for learning assistance

## Technology Stack

### Frontend
- Streamlit
- Python
- HTML and CSS

### Backend
- FastAPI
- Python
- Uvicorn

### AI and Machine Learning
- Groq API
- Faster-Whisper
- EasyOCR

### Other Libraries
- PyMuPDF
- python-docx
- python-pptx
- FFmpeg
- PyVis
- ReportLab
- Playwright

## Project Structure

```text
EchoLearn/
├── backend/
│   ├── ai/
│   ├── chat/
│   ├── concept_graph/
│   ├── ingestion/
│   ├── pipeline/
│   ├── quiz/
│   ├── summarization/
│   ├── transcription/
│   └── main.py
├── frontend/
│   ├── components/
│   ├── styles/
│   └── app.py
├── lib/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

