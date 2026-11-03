from dotenv import load_dotenv
load_dotenv()

import requests
import re
import hashlib
import os
import time

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
).rstrip("/") + "/api/generate"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ---------- Cache ----------

summary_cache = {}

# ---------- Helper ----------



def ollama_generate(prompt: str, temperature=0.2, max_tokens=900):

    # ---------- Local Ollama ----------
    if AI_PROVIDER == "ollama":

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 8192,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                },
            },
            timeout=600,
        )

        if response.status_code != 200:
            raise Exception(
                f"Ollama returned {response.status_code}: {response.text}"
            )

        return response.json()["response"].strip()

    # ---------- Cloud Groq ----------
    elif AI_PROVIDER == "groq":

        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured.")

        if not GROQ_MODEL:
            raise ValueError("GROQ_MODEL is not configured.")

        max_retries = 4

        for attempt in range(max_retries + 1):

            response = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_completion_tokens": max(max_tokens, 2048),
                    "reasoning_effort": "low",
                    "reasoning_format": "hidden",
                },
                timeout=600,
            )

            # Retry when Groq rate limit is reached
            if response.status_code == 429:

                if attempt == max_retries:
                    raise Exception(
                        f"Groq rate limit exceeded after "
                        f"{max_retries} retries: {response.text}"
                    )

                retry_delay = response.headers.get("Retry-After")

                if retry_delay:
                    try:
                        wait_time = float(retry_delay)
                    except ValueError:
                        wait_time = 5
                else:
                    match = re.search(
                        r"try again in ([\d.]+)s",
                        response.text,
                        re.IGNORECASE
                    )

                    wait_time = (
                        float(match.group(1)) + 1
                        if match else 5
                    )

                print(
                    f"Groq rate limit reached. "
                    f"Retrying in {wait_time:.1f} seconds "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )

                time.sleep(wait_time)
                continue

            if response.status_code != 200:
                raise Exception(
                    f"Groq returned {response.status_code}: {response.text}"
                )

            result = response.json()["choices"][0]["message"]
            content = result.get("content")

            if not content or not content.strip():
                raise Exception(
                    f"Groq returned an empty response. "
                    f"Reasoning: {result.get('reasoning', '')}"
                )

            return content.strip()

    else:
        raise ValueError(
            f"Unsupported AI_PROVIDER: {AI_PROVIDER}"
        )


# ---------- Chunk Text ----------


def chunk_text(text, chunk_size=1800):
    words = text.split()

    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

# ---------- Chunk Summarizer ----------


def summarize_chunk(chunk):
    prompt = f"""
You are an expert academic document analyst.

Analyze the following section of uploaded material.

Extract all important information explicitly supported
by the source. Prioritize completeness and accuracy.

Rules:
- Do not introduce outside knowledge or assumptions.
- Preserve important names, dates, numbers, titles,
  qualifications, achievements and technical terms.
- Retain the author's motivations, goals, research interests
  and stated reasons wherever present.
- Preserve project descriptions, methodologies,
  applications, results and contributions.
- Do not omit meaningful details simply because they
  are not technical concepts.
- Exclude greetings, irrelevant conversation and
  administrative announcements.
- Do not complete missing or unfinished information.
- Do not repeat information unnecessarily.

For each important topic or piece of information, provide:
- Topic or detail
- Source-based explanation
- Exact example, evidence or application mentioned,
  if any

If no example is provided, write:
"No explicit example provided."

Lecture section:

{chunk}
"""

    return ollama_generate(
        prompt,
        temperature=0.1,
        max_tokens=500,
    )

# ---------- Main ----------

def generate_summary(text: str):

    if len(text.strip()) < 20:
        return "Text is too short."

    cache_key = hashlib.md5(
        ("document_aware_v2:" + text).encode()
    ).hexdigest()

    if cache_key in summary_cache:
        return summary_cache[cache_key]

    chunks = chunk_text(text)

    # Extract source-supported concepts
    chunk_summaries = []

    for chunk in chunks:
        chunk_summaries.append(summarize_chunk(chunk))

    combined = "\n\n".join(chunk_summaries)

    final_prompt = f"""
You are an expert academic assistant specializing in
document analysis, summarization, and educational content.

Your task is to transform the extracted information into
comprehensive, accurate, well-organized study notes.

The uploaded material may be a lecture, statement of purpose,
research paper, project report, technical document, assignment,
or another type of academic or professional document.

FIRST: Identify the document type and adapt the summary
to its actual content and purpose.

IMPORTANT SOURCE-GROUNDING RULES:

- Treat the uploaded material as the primary and authoritative source.
- Preserve the original meaning, terminology, facts and context.
- Do not invent facts, experiences, achievements, qualifications,
  project functionality, research contributions or intentions.
- Do not exaggerate the author's experience or accomplishments.
- Never attribute general knowledge to the uploaded source.
- Do not silently correct, reinterpret or replace information
  from the original material.
- If information is unclear or missing, explicitly say so.
- Avoid unnecessary repetition.
- Do not introduce unrelated concepts.
- Cover all major sections of the original document.
- Give important information appropriate attention rather
  than selecting topics based only on technical terminology.

Return well-structured Markdown using the following format.

# AI Study Notes

## Document Overview

Identify the apparent document type and its main purpose.

Provide a concise overview using ONLY information supported
by the uploaded material.

## Main Topics and Important Information

Identify the most important themes and sections based on
the document's actual content.

Adapt the topics to the document type.

For example:

For a Statement of Purpose:
- Academic Background
- Technical Skills and Coursework
- Projects and Practical Experience
- Research Interests
- University and Program Motivation
- Faculty and Research Alignment
- Personal Background and Motivation
- Career Goals and Future Plans
- Leadership and Extracurricular Activities

Include only sections that are actually relevant and
supported by the source.

For a Lecture or Technical Document:
- Important Concepts
- Definitions and Explanations
- Methods and Processes
- Examples and Applications
- Important Findings or Conclusions

For a Research Paper:
- Research Problem
- Objectives
- Methodology
- Proposed Approach
- Results and Findings
- Limitations
- Conclusions and Future Work

For a Project Report:
- Problem Statement
- Objectives
- Proposed Solution
- System Architecture
- Technologies Used
- Implementation
- Results
- Limitations and Future Scope

These are examples, not mandatory sections.
Do not force irrelevant headings into the summary.

For each major topic, use the following structure
where appropriate:

### Topic Name

**Source-Based Explanation:**

Explain what the uploaded material actually states.
Preserve important details, names, dates, technical terms
and relationships.

**Examples or Evidence from Source:**

Include relevant examples, projects, statements,
methodologies or evidence explicitly present in the source.

If none exists, write:
"No explicit example provided."

**AI-Enhanced Explanation:**

Provide additional background knowledge only when it
genuinely helps explain the topic.

Clearly distinguish this additional knowledge from
information in the uploaded material.

Never present AI-generated explanations as source facts.

## Important Details

Extract significant information that could be overlooked
in a short overview.

Depending on the document, this may include:
- Names of people, institutions and organizations
- Dates and timelines
- Qualifications and certifications
- Project names and descriptions
- Technical skills and tools
- Research interests
- Important numerical information
- Goals and future plans

Include only details supported by the source.

Do not force irrelevant categories.

## Key Takeaways

Provide 5-10 concise bullet points capturing the most
important information from the original document.

These must be based ONLY on the uploaded material.

## Information Gaps

Mention important information that the document does not
provide, where relevant.

Do not invent missing information or make assumptions.

FINAL QUALITY CHECK:

Before responding, verify that:
1. All major sections of the source are represented.
2. Important facts and names have been preserved accurately.
3. No unsupported personal or professional claims were added.
4. Source-based information is clearly separated from
   AI-enhanced explanations.
5. The summary reflects the actual document type.

Extracted source information:

{combined}
"""


    notes = ollama_generate(
        final_prompt,
        temperature=0.1,
        max_tokens=2400,
    )

    notes = notes.strip()

    summary_cache[cache_key] = notes

    return notes
