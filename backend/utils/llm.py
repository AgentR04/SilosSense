import os
from groq import Groq

_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=_api_key) if _api_key else None

def generate_answer(query: str, context: str) -> str:
    if client is None:
        return (
            "LLM response is unavailable because GROQ_API_KEY is not set. "
            "Please configure GROQ_API_KEY to enable generated answers.\n\n"
            f"Query: {query}\n"
            "Context preview: "
            f"{context[:400]}"
        )

    prompt = f"""
You are an enterprise assistant.

User question:
{query}

Context from company documents:
{context}

Instructions:
- Answer clearly and concisely
- Extract the exact answer
- Do not repeat unnecessary text
- If amount/value exists, state it directly
- Keep it professional

Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()