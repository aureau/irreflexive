from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent

def _ensure_backend_import_path() -> None:
    repo_root = str(REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


_ensure_backend_import_path()

import requests
import trafilatura as tf
from bs4 import BeautifulSoup

from backend.rss.rss_aggregator import get_latest_articles
from backend.rss.rss_config import Outlet, load_outlets


REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = "irreflexive-article-image-extractor/0.1"


@dataclass
class ExtractedArticle:
    outlet_id: str | None
    outlet: str | None
    outlet_uses_article_image_extraction: bool | None
    title: str | None
    url: str
    canonical_url: str | None
    image_url: str | None
    image_source: str | None
    extracted_text: str | None


def fetch_html(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not fetch article URL {url}: {exc}") from exc

    return response.text


def extract_article(url: str, outlet: Outlet | None = None) -> ExtractedArticle:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    title = _first_text(
        soup,
        [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            "title",
        ],
    )
    canonical_url = _first_attr(
        soup,
        [
            'meta[property="og:url"]',
            'link[rel="canonical"]',
        ],
    )
    image_url, image_source = _extract_image_url(soup)
    extracted_text = tf.extract(html, output_format="markdown")

    return ExtractedArticle(
        outlet_id=outlet.outlet_id if outlet is not None else None,
        outlet=outlet.display_name if outlet is not None else None,
        outlet_uses_article_image_extraction=(
            outlet.article_image_extraction if outlet is not None else None
        ),
        title=title,
        url=url,
        canonical_url=canonical_url,
        image_url=image_url,
        image_source=image_source,
        extracted_text=extracted_text,
    )


def extract_articles_from_latest_feed(outlet_id: str | None, per_outlet: int) -> list[ExtractedArticle]:
    outlets = load_outlets()

    selected_outlets = outlets
    if outlet_id is not None:
        selected_outlets = [outlet for outlet in outlets if outlet.outlet_id == outlet_id]
        if not selected_outlets:
            raise ValueError(f"Unknown outlet_id: {outlet_id}")

    latest = get_latest_articles(selected_outlets, per_outlet=per_outlet)
    extracted_articles = []
    for item in latest.items:
        outlet = _find_outlet(selected_outlets, item.outlet_id)
        extracted_articles.append(extract_article(item.url, outlet))

    return extracted_articles


def _find_outlet(outlets: list[Outlet], outlet_id: str) -> Outlet | None:
    for outlet in outlets:
        if outlet.outlet_id == outlet_id:
            return outlet
    return None


def _extract_image_url(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    selectors = [
        ('meta[property="og:image"]', "og:image"),
        ('meta[property="og:image:url"]', "og:image:url"),
        ('meta[name="twitter:image"]', "twitter:image"),
        ('meta[name="twitter:image:src"]', "twitter:image:src"),
        ('link[rel="image_src"]', "link[rel=image_src]"),
    ]

    for selector, source_name in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue

        content = node.get("content") or node.get("href")
        if isinstance(content, str) and content.strip():
            return content.strip(), source_name

    for candidate in _iter_image_candidates(soup):
        if candidate is not None:
            return candidate.url, candidate.source

    return None, None


@dataclass
class ImageCandidate:
    url: str
    source: str
    width: int


def _iter_image_candidates(soup: BeautifulSoup) -> list[ImageCandidate]:
    candidates: list[ImageCandidate] = []

    for selector in ["article img", "main img", "img"]:
        for node in soup.select(selector):
            image_candidate = _image_candidate_from_img(node)
            if image_candidate is None:
                continue

            candidates.append(image_candidate)

        if candidates:
            break

    return candidates


def _image_candidate_from_img(node: Any) -> ImageCandidate | None:
    srcset = node.get("srcset")
    if isinstance(srcset, str):
        srcset_candidate = _image_candidate_from_srcset(srcset)
        if srcset_candidate is not None:
            return srcset_candidate

    src = node.get("src")
    if isinstance(src, str):
        stripped_src = src.strip()
        if stripped_src and not _is_tracking_image(stripped_src):
            return ImageCandidate(url=stripped_src, source="img[src]", width=0)

    return None


def _image_candidate_from_srcset(srcset: str) -> ImageCandidate | None:
    best_url = None
    best_width = -1

    for part in srcset.split(","):
        candidate = part.strip()
        if not candidate:
            continue

        pieces = candidate.split()
        if not pieces:
            continue

        url = pieces[0].strip()
        if not url or _is_tracking_image(url):
            continue

        width = 0
        if len(pieces) > 1 and pieces[1].endswith("w"):
            width_text = pieces[1][:-1]
            if width_text.isdigit():
                width = int(width_text)

        if width > best_width:
            best_url = url
            best_width = width

    if best_url is None:
        return None

    return ImageCandidate(url=best_url, source="img[srcset]", width=best_width)


def _is_tracking_image(url: str) -> bool:
    lowercase_url = url.lower()
    return "tracking" in lowercase_url or "pixel" in lowercase_url


def _first_text(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue

        if node.name == "meta":
            content = node.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
            continue

        text = node.get_text(" ", strip=True)
        if text:
            return text

    return None


def _first_attr(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue

        if node.name == "meta":
            content = node.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        else:
            href = node.get("href")
            if isinstance(href, str) and href.strip():
                return href.strip()

    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract article metadata and image URLs from RSS-discovered article pages."
    )
    parser.add_argument("--url", help="Fetch and extract a single article URL.")
    parser.add_argument(
        "--outlet-id",
        help="Limit RSS discovery to one outlet_id before fetching article pages.",
    )
    parser.add_argument(
        "--per-outlet",
        type=int,
        default=3,
        help="How many RSS items to enrich per outlet when using feed discovery.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a human-friendly summary.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.url:
        result = extract_article(args.url)
        _print_result(result, args.json)
        return 0

    results = extract_articles_from_latest_feed(args.outlet_id, args.per_outlet)
    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            _print_result(result, False)
            print()

    return 0


def _print_result(result: ExtractedArticle, as_json: bool) -> None:
    if as_json:
        print(json.dumps(asdict(result), indent=2))
        return

    print(f"Title: {result.title or 'unknown'}")
    print(f"URL: {result.url}")
    if result.canonical_url:
        print(f"Canonical: {result.canonical_url}")
    if result.outlet:
        print(f"Outlet: {result.outlet}")
    print(f"Image: {result.image_url or 'none'}")
    if result.image_source:
        print(f"Image source: {result.image_source}")
    if result.extracted_text:
        print(f"Text length: {len(result.extracted_text)}")


if __name__ == "__main__":
    raise SystemExit(main())
