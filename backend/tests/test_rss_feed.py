from pathlib import Path

import pytest

from backend.rss_config import Outlet
from backend.rss_feed import FeedParseError, fetch_feed, parse_feed_xml


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def read_fixture(filename: str) -> str:
    return (FIXTURE_DIR / filename).read_text(encoding="utf-8")


def test_parse_sample_rss_returns_normalized_items_sorted_newest_first():
    outlet = Outlet(
        outlet_id="example_rss",
        display_name="Example RSS",
        rss_url="https://example.com/rss.xml",
    )

    items = parse_feed_xml(read_fixture("rss_sample.xml"), outlet)

    assert len(items) == 3
    assert items[0].outlet_id == "example_rss"
    assert items[0].source == "Example RSS"
    assert items[0].title == "Newest RSS Story"
    assert items[0].url == "https://example.com/newest-rss-story"
    assert items[0].published_at.isoformat() == "2026-05-19T10:30:00+00:00"
    assert items[0].summary == "Newest RSS summary."
    assert items[0].image_url == "https://example.com/newest-rss-image.jpg"
    assert items[1].title == "Older RSS Story"
    assert items[1].image_url == "https://example.com/older-rss-guardian-style.jpg?width=700&quality=85"
    assert items[2].title == "NPR Encoded Image Story"
    assert items[2].image_url == "https://npr.brightspotcdn.com/story-image.jpg"


def test_parse_sample_atom_returns_normalized_items_sorted_newest_first():
    outlet = Outlet(
        outlet_id="example_atom",
        display_name="Example Atom",
        rss_url="https://example.com/atom.xml",
    )

    items = parse_feed_xml(read_fixture("atom_sample.xml"), outlet)

    assert len(items) == 2
    assert items[0].outlet_id == "example_atom"
    assert items[0].source == "Example Atom"
    assert items[0].title == "Newest Atom Story"
    assert items[0].url == "https://example.com/newest-atom-story"
    assert items[0].published_at.isoformat() == "2026-05-19T11:00:00+00:00"
    assert items[0].summary == "Newest Atom summary."
    assert items[0].image_url == "https://example.com/newest-atom-image.jpg"


def test_missing_pubdate_returns_item_with_null_published_at():
    outlet = Outlet(
        outlet_id="missing_date",
        display_name="Missing Date",
        rss_url="https://example.com/rss.xml",
    )

    items = parse_feed_xml(read_fixture("rss_missing_pubdate.xml"), outlet)

    assert len(items) == 1
    assert items[0].title == "No Date Story"
    assert items[0].published_at is None


def test_malformed_xml_raises_clear_error():
    outlet = Outlet(
        outlet_id="broken_feed",
        display_name="Broken Feed",
        rss_url="https://example.com/rss.xml",
    )

    with pytest.raises(FeedParseError, match="Malformed RSS XML"):
        parse_feed_xml(read_fixture("rss_malformed.xml"), outlet)


def test_empty_feed_returns_empty_list():
    outlet = Outlet(
        outlet_id="empty_feed",
        display_name="Empty Feed",
        rss_url="https://example.com/rss.xml",
    )

    items = parse_feed_xml(read_fixture("rss_empty.xml"), outlet)

    assert items == []


def test_fetch_feed_uses_http_response_text(monkeypatch):
    outlet = Outlet(
        outlet_id="example_rss",
        display_name="Example RSS",
        rss_url="https://example.com/rss.xml",
    )

    class FakeResponse:
        text = read_fixture("rss_sample.xml")

        def raise_for_status(self):
            return None

    def fake_get(url, timeout, headers):
        assert url == "https://example.com/rss.xml"
        assert timeout == 15
        assert headers["User-Agent"] == "irreflexive-rss/0.1"
        return FakeResponse()

    monkeypatch.setattr("backend.rss_feed.requests.get", fake_get)

    items = fetch_feed(outlet)

    assert len(items) == 3
    assert items[0].title == "Newest RSS Story"


def test_parse_cnn_media_group_uses_largest_image():
    outlet = Outlet(
        outlet_id="cnn_topstories",
        display_name="CNN Top Stories",
        rss_url="http://rss.cnn.com/rss/cnn_topstories.rss",
    )

    xml_text = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CNN Top Stories</title>
    <item>
      <title>CNN Story</title>
      <link>https://example.com/cnn-story</link>
      <pubDate>Tue, 19 May 2026 10:30:00 GMT</pubDate>
      <media:group xmlns:media="http://search.yahoo.com/mrss/">
        <media:content medium="image" url="https://cdn.cnn.com/cnn-small.jpg" width="300" height="200" type="image/jpeg" />
        <media:content medium="image" url="https://cdn.cnn.com/cnn-large.jpg" width="1100" height="619" type="image/jpeg" />
      </media:group>
    </item>
  </channel>
</rss>
"""

    items = parse_feed_xml(xml_text, outlet)

    assert len(items) == 1
    assert items[0].image_url == "https://cdn.cnn.com/cnn-large.jpg"


def test_parse_abc_thumbnails_use_largest_image():
    outlet = Outlet(
        outlet_id="abc_us_headlines",
        display_name="ABC News US Headlines",
        rss_url="https://abcnews.com/abcnews/usheadlines",
    )

    xml_text = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>ABC News Headlines</title>
    <item>
      <title>ABC Story</title>
      <link>https://example.com/abc-story</link>
      <pubDate>Tue, 19 May 2026 10:30:00 GMT</pubDate>
      <media:thumbnail xmlns:media="http://search.yahoo.com/mrss/" url="https://s.abcnews.com/images/story_144.jpg" width="144" height="108" />
      <media:thumbnail xmlns:media="http://search.yahoo.com/mrss/" url="https://s.abcnews.com/images/story_608.jpg" width="608" height="456" />
      <media:thumbnail xmlns:media="http://search.yahoo.com/mrss/" url="https://s.abcnews.com/images/story_1600.jpg" width="1600" height="900" />
    </item>
  </channel>
</rss>
"""

    items = parse_feed_xml(xml_text, outlet)

    assert len(items) == 1
    assert items[0].image_url == "https://s.abcnews.com/images/story_1600.jpg"
