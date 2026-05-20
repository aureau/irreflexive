from pydantic import BaseModel

from backend.rss_config import Outlet
from backend.rss_feed import FeedItem, fetch_feed
from backend.storage import upsert_article_from_feed_item


class OutletFetchError(BaseModel):
    outlet_id: str
    source: str
    message: str


class AggregatedFeedResult(BaseModel):
    items: list[FeedItem]
    errors: list[OutletFetchError]


def get_latest_articles(
    outlets: list[Outlet],
    per_outlet: int = 3,
    dedupe_urls: bool = True,
) -> AggregatedFeedResult:
    items = []
    errors = []
    seen_urls = set()

    for outlet in outlets:
        try:
            outlet_items = fetch_feed(outlet)
        except Exception as exc:
            errors.append(
                OutletFetchError(
                    outlet_id=outlet.outlet_id,
                    source=outlet.display_name,
                    message=str(exc),
                )
            )
            continue

        kept_for_outlet = 0
        for item in outlet_items:
            if kept_for_outlet >= per_outlet:
                break

            if dedupe_urls and item.url in seen_urls:
                continue

            items.append(item)
            upsert_article_from_feed_item(item)
            seen_urls.add(item.url)
            kept_for_outlet += 1

    return AggregatedFeedResult(items=items, errors=errors)
