import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.rss.rss_aggregator import get_latest_articles
from backend.rss.rss_config import load_outlets


def main() -> None:
    outlets = load_outlets()
    result = get_latest_articles(outlets, per_outlet=3)

    for item in result.items:
        published_at = item.published_at.isoformat() if item.published_at else "no-date"
        print(f"{item.source} | {published_at} | {item.title} | {item.url}")

    if result.errors:
        print("\nFeed errors:")
        for error in result.errors:
            print(f"{error.source} ({error.outlet_id}): {error.message}")


if __name__ == "__main__":
    main()
