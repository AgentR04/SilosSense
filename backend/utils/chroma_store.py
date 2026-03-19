from chromadb import PersistentClient
from pathlib import Path
from threading import Lock

CHROMA_PATH = Path(__file__).resolve().parent.parent / "chroma_db"
_client = None
_client_lock = Lock()


def _get_client() -> PersistentClient:
    global _client

    # Lazy-load ChromaDB client to avoid blocking service startup.
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = PersistentClient(path=str(CHROMA_PATH))
    return _client


def get_collection(name: str):
    client = _get_client()
    return client.get_or_create_collection(name=name)