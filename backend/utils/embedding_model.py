from threading import Lock
from sentence_transformers import SentenceTransformer

_model = None
_model_lock = Lock()


def _get_model() -> SentenceTransformer:
    global _model

    # Load model on first use to avoid blocking service startup on cold boot.
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str):
    model = _get_model()
    return model.encode(text).tolist()