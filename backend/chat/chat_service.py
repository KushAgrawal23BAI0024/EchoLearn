import re

from backend.summarization.summary_service import ollama_generate


# ---------- Chunk Transcript ----------

def chunk_transcript(text, chunk_size=300):

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


# ---------- Retrieve Relevant Chunks ----------

def retrieve_chunks(question, transcript, top_k=3):

    question_words = set(re.findall(r"\w+", question.lower()))

    scored = []

    for chunk in chunk_transcript(transcript):

        chunk_words = set(re.findall(r"\w+", chunk.lower()))

        score = len(question_words & chunk_words)

        scored.append((score, chunk))

    scored.sort(reverse=True)

    return [c for s, c in scored[:top_k] if s > 0]


# ---------- Main ----------

def chat_with_lecture(question, transcript):

    context = retrieve_chunks(question, transcript)

    if not context:
        return "I couldn't find that in this lecture."

    prompt = f"""
You are an AI teaching assistant.

Answer ONLY using the lecture context.

Rules:
- Do not invent information.
- If the answer is not present, say:
  "I couldn't find that in this lecture."
- Explain clearly for a beginner.

Question:
{question}

Lecture Context:

{"\n\n".join(context)}
"""

    return ollama_generate(prompt)