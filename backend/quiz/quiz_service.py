import json
import re

from backend.summarization.summary_service import ollama_generate

# ---------- Extract JSON ----------

def extract_json(raw):

    match = re.search(r"\[\s*{.*}\s*\]", raw, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return []

    return []


# ---------- Validation ----------

def validate_questions(questions):

    valid = []
    seen = set()

    for q in questions:

        if not isinstance(q, dict):
            continue

        if (
            "question" in q
            and "options" in q
            and "answer" in q
            and len(q["options"]) == 4
            and q["answer"] in ["A", "B", "C", "D"]
        ):

            question_text = q["question"].strip()

            if question_text not in seen:
                seen.add(question_text)
                valid.append(q)

    return valid


# ---------- Main ----------

def generate_quiz(transcript, num_questions=5):

    prompt = f"""
You are an experienced university professor creating revision questions.

Read the study material and identify the MAIN concepts that are actually taught.

Create exactly {num_questions} multiple-choice questions.

Strict rules:

- Every question must test UNDERSTANDING, not memorization.
- Each question must focus on a DIFFERENT concept.
- Do NOT use "Which is NOT..." questions.
- Do NOT use fill-in-the-blank questions.
- Do NOT copy long sentences from the material.
- Keep each question under 25 words.
- Each question must have exactly four options.
- Only one option is correct.
- Wrong options should be realistic.
- Never contradict the source.
- Use ONLY information present in the study material.

Return ONLY valid JSON.

Example:

[
  {{
    "question":"Why are transformer architectures important in NLP?",
    "options":[
      "They improve language understanding",
      "They replace programming languages",
      "They create computer hardware",
      "They reduce internet speed"
    ],
    "answer":"A"
  }}
]

Study Material:

{transcript[:15000]}
"""

    raw = ollama_generate(prompt, temperature=0.2)

    questions = validate_questions(extract_json(raw))

    # ---------- Fallback generation ----------

    if len(questions) < num_questions:

        remaining = num_questions - len(questions)

        existing = "\n".join(
            f"- {q['question']}" for q in questions
        )

        fallback_prompt = f"""
Create {remaining} NEW multiple-choice questions.

Do NOT repeat these questions:

{existing}

Use ONLY this study material.

Return ONLY valid JSON.

Study Material:

{transcript[:15000]}
"""

        extra = validate_questions(
            extract_json(
                ollama_generate(
                    fallback_prompt,
                    temperature=0.25
                )
            )
        )

        questions.extend(extra)

    return questions[:num_questions]