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
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/KushAgrawal23BAI0024/EchoLearn.git
cd EchoLearn
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as a reference.

Configure these variables:

- `AI_PROVIDER=groq`
- `GROQ_API_KEY=your_groq_api_key`
- `GROQ_MODEL=openai/gpt-oss-20b`

Never upload your actual API key to GitHub.

### 6. Run the Backend

Open a terminal in the project root and run:

```bash
uvicorn backend.main:app --reload
```

### 7. Run the Frontend

Open a second terminal, activate the virtual environment, and run:

```bash
streamlit run frontend/app.py
```

The application will be accessible locally through the URL displayed by Streamlit.

### Additional Requirements

- FFmpeg is required for audio and video processing.
- Playwright with its Chromium browser is required for concept graph PDF export.

## Deployment Status

- Source code is publicly available on GitHub.
- Local setup and execution instructions are provided above.
- Cloud deployment is currently in progress.