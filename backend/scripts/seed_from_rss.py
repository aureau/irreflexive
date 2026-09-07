import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.rss.rss_aggregator import get_latest_articles
from backend.rss.rss_config import load_outlets
from backend.storage import upsert_article_from_feed_item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed article metadata from configured RSS feeds.")
    parser.add_argument(
        "--per-outlet",
        type=int,
        default=5,
        help="Number of RSS items to upsert per outlet.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outlets = load_outlets()
    result = get_latest_articles(outlets, per_outlet=args.per_outlet)

    article_ids = []
    for item in result.items:
        article_ids.append(upsert_article_from_feed_item(item))

    print(f"Fetched {len(result.items)} RSS items from {len(outlets)} outlets.")
    print(f"Upserted {len(article_ids)} article rows.")

    if article_ids:
        print(f"Article id range: {min(article_ids)}-{max(article_ids)}")

    if result.errors:
        print("\nFeed errors:")
        for error in result.errors:
            print(f"{error.source} ({error.outlet_id}): {error.message}")


if __name__ == "__main__":
    main()
