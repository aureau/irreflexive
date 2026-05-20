from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError, field_validator


class FeedConfigError(ValueError):
    pass


class Outlet(BaseModel):
    outlet_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    rss_url: str = Field(min_length=1)
    homepage: str | None = None

    @field_validator("outlet_id", "display_name", "rss_url", "homepage", mode="before")
    @classmethod
    def strip_string_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("rss_url", "homepage")
    @classmethod
    def validate_http_url(cls, value: str | None) -> str | None:
        if value is None:
            return value

        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL must be a valid http or https URL")

        return value


DEFAULT_OUTLETS: list[dict[str, str]] = [
    {
        "outlet_id": "guardian_us",
        "display_name": "The Guardian - US News",
        "rss_url": "https://www.theguardian.com/us-news/rss",
        "homepage": "https://www.theguardian.com/us-news",
    },
    {
        "outlet_id": "abc_us_headlines",
        "display_name": "ABC News US Headlines",
        "rss_url": "https://abcnews.com/abcnews/usheadlines?nc=1779255631142&_rnd=uxou0g&noCache=true",
        "homepage": "https://abcnews.go.com/",
    },
    {
        "outlet_id": "npr_news",
        "display_name": "NPR News",
        "rss_url": "https://feeds.npr.org/1001/rss.xml",
        "homepage": "https://www.npr.org/sections/news/",
    },
    {
        "outlet_id": "nyt_home",
        "display_name": "The New York Times",
        "rss_url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "homepage": "https://www.nytimes.com/",
    },
        {
        "outlet_id": "cnn_topstories",
        "display_name": "CNN Top Stories",
        "rss_url": "http://rss.cnn.com/rss/cnn_topstories.rss",
        "homepage": "https://www.cnn.com/",
    },
    {
        "outlet_id": "bbc_world",
        "display_name": "BBC News - World",
        "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "homepage": "https://www.bbc.com/news/world",
    },
]


def load_outlets(raw_outlets: list[dict[str, Any]] | None = None) -> list[Outlet]:
    outlet_configs = DEFAULT_OUTLETS if raw_outlets is None else raw_outlets

    outlets = []
    try:
        for outlet_config in outlet_configs:
            outlets.append(Outlet.model_validate(outlet_config))
    except ValidationError as exc:
        raise FeedConfigError(f"Invalid outlet config: {exc}") from exc

    outlet_id_counts = {}
    for outlet in outlets:
        if outlet.outlet_id not in outlet_id_counts:
            outlet_id_counts[outlet.outlet_id] = 0
        outlet_id_counts[outlet.outlet_id] += 1

    duplicate_ids = []
    for outlet_id, count in outlet_id_counts.items():
        if count > 1:
            duplicate_ids.append(outlet_id)

    duplicate_ids.sort()
    if duplicate_ids:
        raise FeedConfigError(f"Duplicate outlet_id values: {', '.join(duplicate_ids)}")

    return outlets
