"""
Step 1: build (X, y) for the classifier head.

WRONG (baseline / corpus — one vector per class):
    for bias in ['left', 'right']:
        texts = all articles with that label
        corpus_vector = mean(every article_vector in texts)   # ONE vector per class

RIGHT (head training — N vectors, one per article):
    for each row in train.csv:
        article_vector = embed(this article only)
        append article_vector to X
        append this row's label to y

Binary MVP result:
    X.shape == (num_articles, 384)
    y.shape == (num_articles,)  # labels are "left" or "right"
"""

from pathlib import Path

import langchain_text_splitters as lc
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Set to an int (e.g. 500) for a quick test run; None = full train.csv
LIMIT = None

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
CSV_PATH = BASE_DIR.parent / "datasets" / "train-test-datasets" / "train.csv"

model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")
text_splitter = lc.RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)

bias_map = {
    "left": "left",
    "leaning-left": "left",
    "leaning-right": "right",
    "right": "right",
}


def article_to_vector(text: str) -> np.ndarray | None:
    """One article's page_text -> one 384-dim unit vector."""
    chunks = text_splitter.split_text(text)
    if not chunks:
        return None

    chunk_embeddings = model.encode(chunks, batch_size=32, show_progress_bar=False)

    if chunk_embeddings.ndim == 1:
        chunk_embeddings = chunk_embeddings.reshape(1, -1)

    # mean-pool chunks -> article vector -> L2 normalize
    article_vector = np.mean(chunk_embeddings, axis=0)
    norm = np.linalg.norm(article_vector)
    if norm == 0:
        return None
    return article_vector / norm


def main():
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=["bias", "page_text"])
    df["mapped_bias"] = df["bias"].map(bias_map)
    df = df.dropna(subset=["mapped_bias"])

    if LIMIT is not None:
        df = df.head(LIMIT)

    # --- THIS is the loop you want: one iteration = one article ---
    X_list: list[np.ndarray] = []
    y_list: list[str] = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Embedding articles"):
        text = row["page_text"]
        label = row["mapped_bias"]  # e.g. "left", not bias[i]

        vec = article_to_vector(text)
        if vec is None:
            continue

        X_list.append(vec)
        y_list.append(label)

    X = np.stack(X_list)  # (N, 384)
    y = np.array(y_list)  # (N,) strings: "left", "right"

    np.save(ARTIFACTS_DIR / "train_X.npy", X)
    np.save(ARTIFACTS_DIR / "train_y.npy", y)

    print(f"Saved {X.shape[0]} article vectors to {ARTIFACTS_DIR}/")
    print(f"  train_X.npy  shape {X.shape}")
    print(f"  train_y.npy  shape {y.shape}")
    print("Label counts:", pd.Series(y).value_counts().to_dict())


if __name__ == "__main__":
    main()
