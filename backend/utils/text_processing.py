import re
from typing import List

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    text = clean_text(text)
    chunks = []

    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks