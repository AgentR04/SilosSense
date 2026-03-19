import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import fitz
from utils.text_processing import chunk_text
from utils.chroma_store import get_collection
from utils.embedding_model import embed_text

BASE_DIR = Path(__file__).resolve().parent.parent
HR_DATA_PATH = BASE_DIR / "data" / "hr"

def extract_text_from_pdf(file_path: Path) -> str:
    if not file_path.exists():
        return ""

    text = ""
    pdf = fitz.open(file_path)
    for page in pdf:
        text += page.get_text() + "\n"
    pdf.close()
    return text

def load_hr_documents():
    documents = []

    for file_path in sorted(HR_DATA_PATH.glob("*.pdf")):
        documents.append({
            "source": file_path.name,
            "text": extract_text_from_pdf(file_path)
        })

    return documents

def ingest_hr_docs():
    collection = get_collection("hr_docs")

    documents = load_hr_documents()

    ids = []
    texts = []
    metadatas = []
    embeddings = []

    counter = 0

    for doc in documents:
        chunks = chunk_text(doc["text"], chunk_size=500, overlap=100)
        for chunk in chunks:
            ids.append(f"hr_{counter}")
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

        print(f"Ingested {len(ids)} HR chunks into ChromaDB.")
    else:
        print("No HR documents found.")

if __name__ == "__main__":
    ingest_hr_docs()