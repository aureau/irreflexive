from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any
from xml.etree import ElementTree

import requests
from pydantic import BaseModel

# personal modules
from backend.rss.rss_config import Outlet


REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = "irreflexive-rss/0.1"


class FeedFetchError(RuntimeError):
    pass


class FeedParseError(ValueError):
    pass


class FeedItem(BaseModel):
    outlet_id: str
    source: str
    title: str
    url: str
    published_at: datetime | None = None
    summary: str | None = None
    image_url: str | None = None


def fetch_feed(outlet: Outlet) -> list[FeedItem]:
    try:
        response = requests.get(
            outlet.rss_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FeedFetchError(f"Could not fetch RSS feed for {outlet.outlet_id}: {exc}") from exc

    return parse_feed_xml(response.text, outlet)


def parse_feed_xml(xml_text: str, outlet: Outlet) -> list[FeedItem]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise FeedParseError(f"Malformed RSS XML for {outlet.outlet_id}: {exc}") from exc

    root_name = _local_name(root.tag)
    if root_name == "rss":
        items = _parse_rss_items(root, outlet)
    elif root_name == "feed":
        items = _parse_atom_entries(root, outlet)
    else:
        raise FeedParseError(f"Unsupported feed format for {outlet.outlet_id}: {root_name}")

    return _sort_items_by_date(items)


def _parse_rss_items(root: ElementTree.Element, outlet: Outlet) -> list[FeedItem]:
    channel = _find_direct_child(root, "channel")
    if channel is None:
        return []

    feed_items = []
    for item in _find_direct_children(channel, "item"):
        title = _child_text(item, "title")
        url = _child_text(item, "link")
        if not title or not url:
            continue

        feed_items.append(
            FeedItem(
                outlet_id=outlet.outlet_id,
                source=outlet.display_name,
                title=title,
                url=url,
                published_at=_parse_datetime(_child_text(item, "pubDate")),
                summary=_child_text(item, "description"),
                image_url=_rss_image_url(item),
            )
        )

    return feed_items


def _parse_atom_entries(root: ElementTree.Element, outlet: Outlet) -> list[FeedItem]:
    feed_items = []
    for entry in _find_direct_children(root, "entry"):
        title = _child_text(entry, "title")
        url = _atom_link(entry)
        if not title or not url:
            continue

        published_at = _parse_datetime(_child_text(entry, "published"))
        if published_at is None:
            published_at = _parse_datetime(_child_text(entry, "updated"))

        summary = _child_text(entry, "summary")
        if summary is None:
            summary = _child_text(entry, "content")

        feed_items.append(
            FeedItem(
                outlet_id=outlet.outlet_id,
                source=outlet.display_name,
                title=title,
                url=url,
                published_at=published_at,
                summary=summary,
                image_url=_atom_image_url(entry),
            )
        )

    return feed_items


def _sort_items_by_date(items: list[FeedItem]) -> list[FeedItem]:
    indexed_items = []
    for index, item in enumerate(items):
        indexed_items.append((index, item))

    def sort_key(indexed_item: tuple[int, FeedItem]) -> tuple[int, float, int]:
        index, item = indexed_item
        if item.published_at is None:
            return (0, 0.0, -index)
        return (1, item.published_at.timestamp(), -index)

    indexed_items.sort(key=sort_key, reverse=True)

    sorted_items = []
    for _index, item in indexed_items:
        sorted_items.append(item)

    return sorted_items


def _parse_datetime(raw_value: str | None) -> datetime | None:
    if raw_value is None:
        return None

    try:
        parsed_datetime = parsedate_to_datetime(raw_value)
    except (TypeError, ValueError):
        try:
            parsed_datetime = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed_datetime.tzinfo is None:
        return parsed_datetime.replace(tzinfo=UTC)

    return parsed_datetime.astimezone(UTC)


def _atom_link(entry: ElementTree.Element) -> str | None:
    fallback_url = None
    for child in entry:
        if _local_name(child.tag) != "link":
            continue

        href = _strip_or_none(child.attrib.get("href"))
        if href is None:
            continue

        rel = child.attrib.get("rel")
        if rel is None or rel == "alternate":
            return href

        if fallback_url is None:
            fallback_url = href

    return fallback_url


def _rss_image_url(item: ElementTree.Element) -> str | None:
    media_image = _media_image_url(item)
    if media_image is not None:
        return media_image

    for child in item:
        if _local_name(child.tag) != "enclosure":
            continue

        url = _strip_or_none(child.attrib.get("url"))
        mime_type = _strip_or_none(child.attrib.get("type"))
        if url is not None and mime_type is not None and mime_type.startswith("image/"):
            return url

    encoded_image = _encoded_html_image_url(item)
    if encoded_image is not None:
        return encoded_image

    return None


def _atom_image_url(entry: ElementTree.Element) -> str | None:
    media_image = _media_image_url(entry)
    if media_image is not None:
        return media_image

    for child in entry:
        if _local_name(child.tag) != "link":
            continue

        rel = child.attrib.get("rel")
        if rel not in {"enclosure", "image", "thumbnail"}:
            continue

        url = _strip_or_none(child.attrib.get("href"))
        mime_type = _strip_or_none(child.attrib.get("type"))
        if url is not None and (mime_type is None or mime_type.startswith("image/")):
            return url

    return None


def _media_image_url(parent: ElementTree.Element) -> str | None:
    best_image_url = None
    best_image_width = -1

    for child in parent:
        child_name = _local_name(child.tag)
        if child_name == "group":
            image_url, image_width = _media_image_url_from_container(child)
        elif child_name in {"thumbnail", "content"}:
            image_url, image_width = _media_image_candidate(child)
        else:
            continue

        if image_url is None:
            continue

        if image_width > best_image_width:
            best_image_url = image_url
            best_image_width = image_width

    return best_image_url


def _media_image_url_from_container(container: ElementTree.Element) -> tuple[str | None, int]:
    best_image_url = None
    best_image_width = -1

    for child in container:
        child_name = _local_name(child.tag)
        if child_name not in {"thumbnail", "content"}:
            continue

        image_url, image_width = _media_image_candidate(child)
        if image_url is None:
            continue

        if image_width > best_image_width:
            best_image_url = image_url
            best_image_width = image_width

    return best_image_url, best_image_width


def _media_image_candidate(child: ElementTree.Element) -> tuple[str | None, int]:
    url = _strip_or_none(child.attrib.get("url"))
    if url is None:
        return None, -1

    width = _parse_positive_int(child.attrib.get("width"))
    if width is None:
        width = 0

    child_name = _local_name(child.tag)
    if child_name == "thumbnail":
        return url, width

    medium = child.attrib.get("medium")
    mime_type = _strip_or_none(child.attrib.get("type"))
    is_image_content = medium == "image" or (mime_type is not None and mime_type.startswith("image/"))
    if not is_image_content and not _looks_like_image_url(url):
        return None, -1

    return url, width


def _parse_positive_int(raw_value: Any) -> int | None:
    if raw_value is None:
        return None

    try:
        parsed_value = int(raw_value)
    except (TypeError, ValueError):
        return None

    if parsed_value <= 0:
        return None

    return parsed_value


def _encoded_html_image_url(parent: ElementTree.Element) -> str | None:
    for child in parent:
        if _local_name(child.tag) != "encoded":
            continue

        encoded_html = _strip_or_none(child.text)
        if encoded_html is None:
            continue

        parser = ImageSrcParser()
        parser.feed(encoded_html)
        for image_url in parser.image_urls:
            if _is_tracking_image(image_url):
                continue
            return image_url

    return None


def _looks_like_image_url(url: str) -> bool:
    lowercase_url = url.lower()
    image_extensions = (".jpg", ".jpeg", ".png", ".webp", ".gif")

    for extension in image_extensions:
        if extension in lowercase_url:
            return True

    return False


def _is_tracking_image(url: str) -> bool:
    lowercase_url = url.lower()
    return "tracking" in lowercase_url or "rss-pixel" in lowercase_url or "pixel.png" in lowercase_url


class ImageSrcParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img":
            return

        for attr_name, attr_value in attrs:
            if attr_name != "src":
                continue

            image_url = _strip_or_none(attr_value)
            if image_url is not None:
                self.image_urls.append(image_url)
            return


def _find_direct_child(parent: ElementTree.Element, child_name: str) -> ElementTree.Element | None:
    for child in parent:
        if _local_name(child.tag) == child_name:
            return child
    return None


def _find_direct_children(parent: ElementTree.Element, child_name: str) -> list[ElementTree.Element]:
    children = []
    for child in parent:
        if _local_name(child.tag) == child_name:
            children.append(child)
    return children


def _child_text(parent: ElementTree.Element, child_name: str) -> str | None:
    child = _find_direct_child(parent, child_name)
    if child is None:
        return None
    return _strip_or_none(child.text)


def _strip_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    stripped_value = value.strip()
    if not stripped_value:
        return None

    return stripped_value


def _local_name(tag: str) -> str:
    if "}" not in tag:
        return tag
    return tag.rsplit("}", 1)[1]
