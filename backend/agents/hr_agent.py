from utils.chroma_store import get_collection
from utils.embedding_model import embed_text
from utils.llm import generate_answer


def handle_hr_query(message: str):
    collection = get_collection("hr_docs")
    query_embedding = embed_text(message)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2,
        include=["documents", "metadatas", "distances"]
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "agent": "HR Agent",
            "reply": "I could not find relevant HR information.",
            "source": "HR Vector Store",
            "debug": []
        }

    context = "\n\n".join(documents)
    clean_answer = generate_answer(message, context)

    sources = sorted(set(
        meta["source"] for meta in metadatas
        if meta and "source" in meta
    ))

    retrieval_debug = []
    for i in range(len(documents)):
        retrieval_debug.append({
            "chunk": documents[i],
            "source": metadatas[i].get("source", "Unknown"),
            "score": round(distances[i], 4)
        })

    return {
        "agent": "HR Agent",
        "reply": clean_answer,
        "source": ", ".join(sources),
        "debug": retrieval_debug
    }