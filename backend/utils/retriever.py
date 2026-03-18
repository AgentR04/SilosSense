from collections import Counter
from typing import List, Tuple
import re

def tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())

def score_chunk(query: str, chunk: str) -> int:
    query_tokens = tokenize(query)
    chunk_tokens = tokenize(chunk)

    chunk_counter = Counter(chunk_tokens)

    score = 0
    for token in query_tokens:
        score += chunk_counter[token]

    return score

def retrieve_top_chunks(query: str, chunks: List[str], top_k: int = 2) -> List[Tuple[str, int]]:
    scored = []

    for chunk in chunks:
        score = score_chunk(query, chunk)
        scored.append((chunk, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]