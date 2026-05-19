import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scorer import score_article_file


DEFAULT_ARTICLE = BACKEND_DIR / "test-articles" / "ridt.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a saved article with the trained bias head.")
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

    result = score_article_file(article_path)
    print(f"Article: {article_path}")
    print(f"Label: {result['label']}")
    print(f"Confidence: {result['confidence']:.4f}")


if __name__ == "__main__":
    main()
