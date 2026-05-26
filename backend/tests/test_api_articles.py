from datetime import UTC, datetime

from fastapi.testclient import TestClient

from api.main import app
from backend.rss.rss_aggregator import AggregatedFeedResult, OutletFetchError
from backend.rss.rss_feed import FeedItem


client = TestClient(app)


def test_latest_articles_route_returns_json_shape(monkeypatch):
    def fake_get_latest_articles(outlets, per_outlet=3):
        return AggregatedFeedResult(
            items=[
                FeedItem(
                    outlet_id="example",
                    source="Example News",
                    title="Example Story",
                    url="https://example.com/story",
                    published_at=datetime(2026, 5, 19, 12, 30, tzinfo=UTC),
                    summary="Example summary.",
                    image_url="https://example.com/story-image.jpg",
                )
            ],
            errors=[],
        )

    monkeypatch.setattr("api.main.get_latest_articles", fake_get_latest_articles)

    response = client.get("/api/articles/latest")

    assert response.status_code == 200
    payload = response.json()
    assert "fetched_at" in payload
    assert payload["errors"] == []
    assert len(payload["articles"]) == 1
    assert payload["articles"][0] == {
        "outlet_id": "example",
        "outlet": "Example News",
        "title": "Example Story",
        "url": "https://example.com/story",
        "published_at": "2026-05-19T12:30:00Z",
        "summary": "Example summary.",
        "image_url": "https://example.com/story-image.jpg",
        "image_status": "rss",
        "image_source": "rss",
        "scored": False,
        "label": None,
        "confidence": None,
        "model_version": None,
        "scoring_error": None,
    }


def test_latest_articles_route_returns_partial_failures_as_200(monkeypatch):
    def fake_get_latest_articles(outlets, per_outlet=3):
        return AggregatedFeedResult(
            items=[],
            errors=[
                OutletFetchError(
                    outlet_id="broken",
                    source="Broken Feed",
                    message="network failed",
                )
            ],
        )

    monkeypatch.setattr("api.main.get_latest_articles", fake_get_latest_articles)

    response = client.get("/api/articles/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["articles"] == []
    assert payload["errors"] == [
        {
            "outlet": "Broken Feed",
            "message": "network failed",
        }
    ]
    assert "fetched_at" in payload


def test_latest_articles_route_does_not_score_articles(monkeypatch):
    def fake_get_latest_articles(outlets, per_outlet=3):
        return AggregatedFeedResult(
            items=[
                FeedItem(
                    outlet_id="example",
                    source="Example News",
                    title="Example Story",
                    url="https://example.com/story",
                    published_at=datetime(2026, 5, 19, 12, 30, tzinfo=UTC),
                    summary=None,
                    image_url=None,
                )
            ],
            errors=[],
        )

    monkeypatch.setattr("api.main.get_latest_articles", fake_get_latest_articles)
    monkeypatch.setattr(
        "api.main._score_article_url",
        lambda url: (_ for _ in ()).throw(AssertionError("latest route should not score")),
    )

    response = client.get("/api/articles/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["errors"] == []
    assert payload["articles"][0]["outlet_id"] == "example"
    assert payload["articles"][0]["image_url"] is None
    assert payload["articles"][0]["image_status"] == "missing"
    assert payload["articles"][0]["image_source"] is None
    assert payload["articles"][0]["scored"] is False
    assert payload["articles"][0]["label"] is None
    assert payload["articles"][0]["confidence"] is None
    assert payload["articles"][0]["model_version"] is None
    assert payload["articles"][0]["scoring_error"] is None


def test_latest_articles_route_is_rss_first(monkeypatch):
    def fake_get_latest_articles(outlets, per_outlet=3):
        return AggregatedFeedResult(
            items=[
                FeedItem(
                    outlet_id="example",
                    source="Example News",
                    title="Example Story",
                    url="https://example.com/story",
                    published_at=datetime(2026, 5, 19, 12, 30, tzinfo=UTC),
                    summary=None,
                    image_url=None,
                )
            ],
            errors=[],
        )

    monkeypatch.setattr("api.main.get_latest_articles", fake_get_latest_articles)
    monkeypatch.setattr(
        "api.main.extract_article_page",
        lambda url, outlet=None: (_ for _ in ()).throw(
            AssertionError("latest route should not use article extraction")
        ),
    )

    response = client.get("/api/articles/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["articles"][0]["image_url"] is None
    assert payload["articles"][0]["image_status"] == "missing"
    assert payload["articles"][0]["image_source"] is None


def test_article_image_route_resolves_single_article(monkeypatch):
    class FakeExtractedArticle:
        image_url = "https://example.com/extracted-image.jpg"
        image_source = "og:image"

    monkeypatch.setattr(
        "api.main.extract_article_page",
        lambda url, outlet=None: FakeExtractedArticle(),
    )

    response = client.post(
        "/api/articles/image",
        json={
            "url": "https://example.com/story",
            "outlet_id": "bbc_world",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "url": "https://example.com/story",
        "outlet_id": "bbc_world",
        "image_url": "https://example.com/extracted-image.jpg",
        "image_source": "og:image",
        "image_status": "article_extract",
        "message": None,
    }
