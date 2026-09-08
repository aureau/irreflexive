from pathlib import Path

import joblib
import numpy as np

from backend.scripts.chunking import extract_chunk_and_clean_article
from backend.scoring.model import embed_article


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
HEAD_MODEL_PATH = BACKEND_DIR / "baselines" / "head-training" / "artifacts" / "bias_head.pkl"


def load_bias_head(model_path: str | Path = HEAD_MODEL_PATH):
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Missing trained bias head: {model_path}")
    return joblib.load(model_path)


def chunks_to_article_vector(chunks: list[str]) -> np.ndarray:
    if not chunks:
        raise ValueError("Cannot score an article with no extracted chunks")

    chunk_embeddings = embed_article(chunks)
    if chunk_embeddings.ndim == 1:
        chunk_embeddings = chunk_embeddings.reshape(1, -1)

    article_vector = np.mean(chunk_embeddings, axis=0)
    norm = np.linalg.norm(article_vector)
    if norm == 0:
        raise ValueError("Cannot score an article with a zero-length embedding")

    return article_vector / norm


def score_chunks(chunks: list[str], head=None) -> dict:
    if head is None:
        head = load_bias_head()

    article_vector = chunks_to_article_vector(chunks).reshape(1, -1)
    label = str(head.predict(article_vector)[0])

    if not hasattr(head, "predict_proba"):
        raise ValueError("Trained bias head does not support confidence scores")

    probabilities = head.predict_proba(article_vector)[0]
    confidence = float(np.max(probabilities))

    return {
        "label": label,
        "confidence": confidence,
    }


def score_article_file(article_path: str | Path) -> dict:
    chunks = extract_chunk_and_clean_article(str(article_path), True)
    return score_chunks(chunks)
