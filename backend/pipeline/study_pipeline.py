import re

from backend.summarization.summary_service import (
    generate_summary,
    ollama_generate,
)
from backend.quiz.quiz_service import generate_quiz
from backend.concept_graph.graph_service import generate_concept_graph


# ---------- Study Metadata ----------

def estimate_study_time(text: str) -> int:
    words = len(text.split())

    # Average reading speed + revision overhead
    base = words / 160
    review_time = max(5, round(base + len(text.split(".")) / 40))

    return review_time


def estimate_difficulty(text: str) -> str:
    words = len(text.split())

    if words < 600:
        return "Easy"
    elif words < 2000:
        return "Intermediate"
    else:
        return "Advanced"


# ---------- Key Terms ----------

def extract_key_terms(text: str):

    prompt = f"""
You are an academic assistant.

Extract exactly 10 important academic terms.

Rules:
- single words or short phrases
- no numbering
- no duplicates
- no explanations

Text:

{text[:5000]}
"""

    result = ollama_generate(prompt, temperature=0.1)

    terms = []

    for line in result.splitlines():

        line = re.sub(r"^\d+[\).\-\s]*", "", line)
        line = line.strip("-• ").strip()

        if line and line not in terms:
            terms.append(line)

    return terms[:10]


# ---------- Flashcards ----------

def generate_flashcards(text: str):

    prompt = f"""
Create exactly 8 university revision flashcards.

Rules:
- Keep answers under 30 words.
- Focus on definitions, comparisons, and applications.
- Avoid copying long sentences.
- Make each card useful for quick revision.

Return exactly in this format:

Q: Question
A: Answer

Text:

{text[:7000]}
"""

    raw = ollama_generate(prompt, temperature=0.2)

    cards = []
    current = {}

    for line in raw.splitlines():

        line = line.strip()

        if line.startswith("Q:"):

            if current:
                cards.append(current)

            current = {
                "question": line[2:].strip()
            }

        elif line.startswith("A:"):

            current["answer"] = line[2:].strip()

    if current:
        cards.append(current)

    return cards[:8]


# ---------- Main Pipeline ----------


def build_study_package(
    text: str,
    file_type: str,
    progress_callback=None
):

    def update_progress(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    update_progress(5, "Generating AI study notes...")
    summary = generate_summary(text)

    update_progress(30, "Creating quiz questions...")
    quiz = generate_quiz(text, 5)

    update_progress(50, "Generating flashcards...")
    flashcards = generate_flashcards(text)

    update_progress(70, "Extracting important key terms...")
    key_terms = extract_key_terms(text)

    update_progress(85, "Building concept graph...")
    concept_graph = generate_concept_graph(text)

    update_progress(95, "Preparing study insights...")

    study_package = {
        "type": file_type,
        "text": text,
        "summary": summary,
        "quiz": quiz,
        "flashcards": flashcards,
        "key_terms": key_terms,
        "concept_graph": concept_graph,
        "metadata": {
            "word_count": len(text.split()),
            "estimated_study_time": estimate_study_time(text),
            "difficulty": estimate_difficulty(text)
        }
    }

    update_progress(100, "Study package ready!")

    return study_package
