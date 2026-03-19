from chromadb import PersistentClient
from pathlib import Path

CHROMA_PATH = Path(__file__).resolve().parent.parent / "chroma_db"
client = PersistentClient(path=str(CHROMA_PATH))

def get_collection(name: str):
    return client.get_or_create_collection(name=name)