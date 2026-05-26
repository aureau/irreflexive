import pytest

from backend.rss.rss_config import FeedConfigError, load_outlets


def test_valid_config_loads():
    outlets = load_outlets()

    assert len(outlets) == 6
    assert outlets[0].outlet_id == "guardian_us"
    assert outlets[0].rss_url == "https://www.theguardian.com/us-news/rss"
    assert outlets[1].outlet_id == "abc_us_headlines"
    assert outlets[4].outlet_id == "cnn_topstories"
    assert outlets[5].outlet_id == "bbc_world"


def test_missing_rss_url_raises_error():
    raw_outlets = [
        {
            "outlet_id": "missing_rss",
            "display_name": "Missing RSS",
            "homepage": "https://example.com",
        }
    ]

    with pytest.raises(FeedConfigError, match="rss_url"):
        load_outlets(raw_outlets)


def test_duplicate_outlet_id_raises_error():
    raw_outlets = [
        {
            "outlet_id": "duplicate",
            "display_name": "First Feed",
            "rss_url": "https://example.com/first.xml",
        },
        {
            "outlet_id": "duplicate",
            "display_name": "Second Feed",
            "rss_url": "https://example.com/second.xml",
        },
    ]

    with pytest.raises(FeedConfigError, match="Duplicate outlet_id"):
        load_outlets(raw_outlets)


def test_invalid_url_raises_error():
    raw_outlets = [
        {
            "outlet_id": "invalid_url",
            "display_name": "Invalid URL",
            "rss_url": "not-a-url",
        }
    ]

    with pytest.raises(FeedConfigError, match="valid http or https URL"):
        load_outlets(raw_outlets)
