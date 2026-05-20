from datetime import UTC, datetime

from backend.rss_aggregator import get_latest_articles
from backend.rss_config import Outlet
from backend.rss_feed import FeedItem


def test_storage_upsert_is_called_for_kept_items(monkeypatch):
    outlet = make_outlet("example")
    persisted_urls = []

    def fake_fetch_feed(_outlet):
        return [make_feed_item(_outlet, 1)]

    def fake_upsert_article_from_feed_item(item):
        persisted_urls.append(item.url)

    monkeypatch.setattr("backend.rss_aggregator.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr(
        "backend.rss_aggregator.upsert_article_from_feed_item",
        fake_upsert_article_from_feed_item,
    )

    result = get_latest_articles([outlet], per_outlet=3)

    assert persisted_urls == [result.items[0].url]


def make_outlet(outlet_id: str, display_name: str | None = None) -> Outlet:
    if display_name is None:
        display_name = outlet_id

    return Outlet(
        outlet_id=outlet_id,
        display_name=display_name,
        rss_url=f"https://example.com/{outlet_id}.xml",
    )


def make_feed_item(outlet: Outlet, index: int, url: str | None = None) -> FeedItem:
    if url is None:
        url = f"https://example.com/{outlet.outlet_id}/story-{index}"

    return FeedItem(
        outlet_id=outlet.outlet_id,
        source=outlet.display_name,
        title=f"{outlet.display_name} Story {index}",
        url=url,
        published_at=datetime(2026, 5, 19, 12, index, tzinfo=UTC),
    )


def test_get_latest_articles_takes_three_per_outlet(monkeypatch):
    outlet = make_outlet("example")

    def fake_fetch_feed(_outlet):
        items = []
        for index in range(10):
            items.append(make_feed_item(_outlet, index))
        return items

    monkeypatch.setattr("backend.rss_aggregator.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr("backend.rss_aggregator.upsert_article_from_feed_item", lambda item: None)

    result = get_latest_articles([outlet], per_outlet=3)

    assert len(result.items) == 3
    assert result.errors == []
    assert result.items[0].title == "example Story 0"
    assert result.items[2].title == "example Story 2"


def test_one_outlet_failure_keeps_other_outlet_results(monkeypatch):
    good_outlet = make_outlet("good", "Good Feed")
    bad_outlet = make_outlet("bad", "Bad Feed")

    def fake_fetch_feed(outlet):
        if outlet.outlet_id == "bad":
            raise RuntimeError("network failed")
        return [make_feed_item(outlet, 1)]

    monkeypatch.setattr("backend.rss_aggregator.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr("backend.rss_aggregator.upsert_article_from_feed_item", lambda item: None)

    result = get_latest_articles([bad_outlet, good_outlet], per_outlet=3)

    assert len(result.items) == 1
    assert result.items[0].outlet_id == "good"
    assert len(result.errors) == 1
    assert result.errors[0].outlet_id == "bad"
    assert result.errors[0].source == "Bad Feed"
    assert result.errors[0].message == "network failed"


def test_duplicate_urls_are_kept_once_by_default(monkeypatch):
    first_outlet = make_outlet("first")
    second_outlet = make_outlet("second")
    shared_url = "https://example.com/shared-story"

    def fake_fetch_feed(outlet):
        return [make_feed_item(outlet, 1, url=shared_url)]

    monkeypatch.setattr("backend.rss_aggregator.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr("backend.rss_aggregator.upsert_article_from_feed_item", lambda item: None)

    result = get_latest_articles([first_outlet, second_outlet], per_outlet=3)

    assert len(result.items) == 1
    assert result.items[0].outlet_id == "first"


def test_duplicate_urls_can_be_kept_when_dedupe_disabled(monkeypatch):
    first_outlet = make_outlet("first")
    second_outlet = make_outlet("second")
    shared_url = "https://example.com/shared-story"

    def fake_fetch_feed(outlet):
        return [make_feed_item(outlet, 1, url=shared_url)]

    monkeypatch.setattr("backend.rss_aggregator.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr("backend.rss_aggregator.upsert_article_from_feed_item", lambda item: None)

    result = get_latest_articles([first_outlet, second_outlet], per_outlet=3, dedupe_urls=False)

    assert len(result.items) == 2
