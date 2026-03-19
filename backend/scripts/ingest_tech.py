import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.text_processing import chunk_text
from utils.chroma_store import get_collection
from utils.embedding_model import embed_text

BASE_DIR = Path(__file__).resolve().parent.parent
TECH_DATA_PATH = BASE_DIR / "data" / "tech"

SUPPORTED_TECH_EXTENSIONS = {".md", ".markdown", ".txt", ".doc"}

def load_tech_docs():
    documents = []

    for file_path in sorted(TECH_DATA_PATH.glob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_TECH_EXTENSIONS:
            continue

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            documents.append({
                "source": file_path.name,
                "text": f.read()
            })

    return documents

def ingest_tech_docs():
    collection = get_collection("tech_docs")

    documents = load_tech_docs()

    ids = []
    texts = []
    metadatas = []
    embeddings = []

    counter = 0

    for doc in documents:
        chunks = chunk_text(doc["text"], chunk_size=500, overlap=100)

        for chunk in chunks:
            ids.append(f"tech_{counter}")
            texts.append(chunk)
            metadatas.append({"source": doc["source"]})
            embeddings.append(embed_text(chunk))
            counter += 1

    if ids:
        try:
            existing = collection.get()
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except:
            pass

        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )

        print(f"Ingested {len(ids)} TECH chunks into ChromaDB.")
    else:
        print("No tech documents found.")

if __name__ == "__main__":
    ingest_tech_docs()