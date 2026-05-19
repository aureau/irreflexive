import argparse
import sys
from pathlib import Path

import numpy as np


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from chunking import extract_chunk_and_clean_article
from model import score_article


DEFAULT_ARTICLE = BACKEND_DIR / "test-articles" / "mjn.html"
CORP_BASELINES_DIR = BACKEND_DIR / "baselines" / "corp-baselines"


def load_corpus_bias_axis() -> np.ndarray:
    v_left = np.load(CORP_BASELINES_DIR / "left-corpus-vector.npy")
    v_right = np.load(CORP_BASELINES_DIR / "right-corpus-vector.npy")
    v_center = np.load(CORP_BASELINES_DIR / "center-corpus-vector.npy")

    v_left_shifted = v_left - v_center
    v_right_shifted = v_right - v_center
    raw_axis = v_right_shifted - v_left_shifted
    return raw_axis / np.linalg.norm(raw_axis)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a saved article with the legacy corpus axis.")
    parser.add_argument(
        "--article",
        default=DEFAULT_ARTICLE,
        help="Path to a saved HTML article file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    article_path = Path(args.article)

    if not article_path.exists():
        raise FileNotFoundError(f"Missing article file: {article_path}")

    chunks = extract_chunk_and_clean_article(str(article_path), True)
    axis = load_corpus_bias_axis()
    score = score_article(chunks, axis, True)

    print(f"Article: {article_path}")
    print("Legacy corpus-axis score:")
    print(score)


if __name__ == "__main__":
    main()
