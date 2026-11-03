import json
import re

from backend.summarization.summary_service import ollama_generate


def generate_concept_graph(text):

    prompt = f"""
You are an AI knowledge graph generator.

From this study material, identify the 8 most important learning concepts.

Return ONLY valid JSON.

Format:

{{
  "nodes":[
    "Concept 1",
    "Concept 2"
  ],
  "edges":[
    ["Concept 1","Concept 2"],
    ["Concept 2","Concept 3"]
  ]
}}

Rules:
- Use short academic concept names.
- No numbering.
- No explanations.
- Every edge must connect two concepts.

Material:

{text[:7000]}
"""

    raw = ollama_generate(prompt, temperature=0.1)

    match = re.search(r"\{.*\}", raw, re.DOTALL)

    if not match:
        return {
            "nodes": [],
            "edges": []
        }

    try:
        graph = json.loads(match.group())

        graph.setdefault("nodes", [])
        graph.setdefault("edges", [])

        return graph

    except Exception:

        return {
            "nodes": [],
            "edges": []
        }