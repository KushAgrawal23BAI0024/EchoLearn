import ollama

MODEL = "mistral:latest"

def ask_mistral(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert university teaching assistant. "
                    "Identify actual learning concepts instead of repeating transcript sentences."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]