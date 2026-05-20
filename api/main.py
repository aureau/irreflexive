import logging
from pathlib import Path
import sys
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import requests
import trafilatura as tf
from fastapi import FastAPI, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field, HttpUrl

from backend.rss_aggregator import get_latest_articles
from backend.rss_config import Outlet, load_outlets
from backend.scripts.extract_image_article import extract_article as extract_article_page


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"
HEAD_MODEL_PATH = BACKEND_DIR / "baselines" / "head-training" / "artifacts" / "bias_head.pkl"

RAW_TEXT_CHUNK_CHAR_THRESHOLD = 512
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
REQUEST_TIMEOUT_SECONDS = 15
MODEL_VERSION = "head_v1_2class"

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Irreflexive Article Scoring API",
    version="0.1.0",
    description="API skeleton for scoring article bias and preparing future article ingestion.",
)


def _ensure_backend_import_path() -> None:
    backend_path = str(BACKEND_DIR)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


@lru_cache(maxsize=1)
def _load_score_chunks():
    _ensure_backend_import_path()
    from scorer import score_chunks

    return score_chunks

# remember to create universal split and chunk text function, its redundant
def _split_text(content: str, force_chunking: bool = False) -> list[str]:
    cleaned_content = content.strip()
    if not cleaned_content:
        raise HTTPException(status_code=400, detail="Article content cannot be empty.")

    if not force_chunking and len(cleaned_content) <= RAW_TEXT_CHUNK_CHAR_THRESHOLD:
        return [cleaned_content]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = [chunk.strip() for chunk in splitter.split_text(cleaned_content) if chunk.strip()]
    if not chunks:
        raise HTTPException(status_code=400, detail="Article content produced no chunks.")

    return chunks


def _extract_html_to_text(html: str) -> str:
    cleaned_html = html.strip()
    if not cleaned_html:
        raise HTTPException(status_code=400, detail="HTML content cannot be empty.")

    extracted = tf.extract(cleaned_html, output_format="markdown")
    if not extracted:
        raise HTTPException(status_code=400, detail="Could not extract article text from HTML.")

    return extracted


def _extract_html_to_chunks(html: str) -> list[str]:
    return _split_text(_extract_html_to_text(html), force_chunking=True)


def _fetch_url_content(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": "irreflexive-api/0.1"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Could not fetch article URL: {exc}") from exc

    return response.text


def _score_chunks(chunks: list[str]) -> dict[str, Any]:
    try:
        score_chunks = _load_score_chunks()
        return score_chunks(chunks)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Scoring model is unavailable: {exc}") from exc


def _score_response(
    chunks: list[str],
    request: "BaseScoreRequest",
    content_type: str,
) -> "ScoreResponse":
    result = _score_chunks(chunks)
    return ScoreResponse(
        label=result["label"],
        confidence=result["confidence"],
        chunk_count=len(chunks),
        metadata=ScoreMetadata(
            title=request.title,
            source=request.source,
            url=str(request.url) if request.url else None,
            content_type=content_type,
            chunk_char_threshold=RAW_TEXT_CHUNK_CHAR_THRESHOLD,
            model_version=MODEL_VERSION,
        ),
    )


def _score_article_url(url: str) -> dict[str, Any]:
    html = _fetch_url_content(url)
    extracted_text = _extract_html_to_text(html)
    chunks = _split_text(extracted_text, force_chunking=True)
    return _score_chunks(chunks)


@app.get("/")
def read_root() -> dict[str, Any]:
    return {
        "name": app.title,
        "version": app.version,
        "routes": {
            "health": "/health",
            "model_status": "/model/status",
            "score_text": "/score/text",
            "score_html": "/score/html",
            "score_url": "/score/url",
            "latest_articles": "/api/articles/latest",
            "articles": "/articles",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/model/status")
def model_status() -> dict[str, Any]:
    return {
        "status": "ready" if HEAD_MODEL_PATH.exists() else "missing",
        "head_model_path": str(HEAD_MODEL_PATH),
        "head_model_exists": HEAD_MODEL_PATH.exists(),
    }


# Pydantic models are kept together near the bottom while route handlers below use them.
class BaseScoreRequest(BaseModel):
    title: str | None = Field(default=None, description="Optional article title.")
    source: str | None = Field(default=None, description="Optional source or publisher name.")
    url: HttpUrl | None = Field(default=None, description="Optional canonical article URL.")


class TextScoreRequest(BaseScoreRequest):
    content: str = Field(..., min_length=1, description="Raw article text to score.")


class HtmlScoreRequest(BaseScoreRequest):
    content: str = Field(..., min_length=1, description="Raw article HTML to extract and score.")


class UrlScoreRequest(BaseScoreRequest):
    url: HttpUrl = Field(..., description="Article URL to fetch, extract, and score.")


class ScoreMetadata(BaseModel):
    title: str | None = None
    source: str | None = None
    url: str | None = None
    content_type: str
    chunk_char_threshold: int
    model_version: str


class ScoreResponse(BaseModel):
    label: str
    confidence: float
    chunk_count: int
    metadata: ScoreMetadata


class PlaceholderResponse(BaseModel):
    status: str
    message: str


class ArticleResponse(BaseModel):
    outlet_id: str
    outlet: str
    title: str
    url: str
    published_at: datetime | None = None
    summary: str | None = None
    image_url: str | None = None
    image_status: str
    image_source: str | None = None
    scored: bool
    label: str | None = None
    confidence: float | None = None
    model_version: str | None = None
    scoring_error: str | None = None


class ArticleErrorResponse(BaseModel):
    outlet: str
    message: str


class LatestArticlesResponse(BaseModel):
    articles: list[ArticleResponse]
    errors: list[ArticleErrorResponse]
    fetched_at: datetime


@app.post("/score/text", response_model=ScoreResponse)
def score_text(request: TextScoreRequest) -> ScoreResponse:
    chunks = _split_text(request.content)
    return _score_response(chunks, request, "text")


@app.post("/score/html", response_model=ScoreResponse)
def score_html(request: HtmlScoreRequest) -> ScoreResponse:
    extracted_text = _extract_html_to_text(request.content)
    chunks = _split_text(extracted_text, force_chunking=True)
    return _score_response(chunks, request, "html")


@app.post("/score/url", response_model=ScoreResponse)
def score_url(request: UrlScoreRequest) -> ScoreResponse:
    html = _fetch_url_content(str(request.url))
    extracted_text = _extract_html_to_text(html)
    chunks = _split_text(extracted_text, force_chunking=True)
    return _score_response(chunks, request, "url")


@app.get("/api/articles/latest", response_model=LatestArticlesResponse)
def latest_articles() -> LatestArticlesResponse:
    outlets = load_outlets()
    result = get_latest_articles(outlets, per_outlet=3)

    articles = []
    for item in result.items:
        articles.append(
            ArticleResponse(
                outlet_id=item.outlet_id,
                outlet=item.source,
                title=item.title,
                url=item.url,
                published_at=item.published_at,
                summary=item.summary,
                image_url=item.image_url,
                image_status="rss" if item.image_url is not None else "missing",
                image_source="rss" if item.image_url is not None else None,
                scored=False,
                label=None,
                confidence=None,
                model_version=None,
                scoring_error=None,
            )
        )

    errors = []
    for error in result.errors:
        errors.append(
            ArticleErrorResponse(
                outlet=error.source,
                message=error.message,
            )
        )

    return LatestArticlesResponse(
        articles=articles,
        errors=errors,
        fetched_at=datetime.now(UTC),
    )


class ArticleImageRequest(BaseModel):
    url: HttpUrl = Field(..., description="Article URL to fetch and extract an image from.")
    outlet_id: str | None = Field(
        default=None,
        description="Optional outlet identifier for logging and outlet-specific rules.",
    )


class ArticleImageResponse(BaseModel):
    url: str
    outlet_id: str | None = None
    image_url: str | None = None
    image_source: str | None = None
    image_status: str
    message: str | None = None


@app.post("/api/articles/image", response_model=ArticleImageResponse)
def resolve_article_image(request: ArticleImageRequest) -> ArticleImageResponse:
    outlets = load_outlets()
    outlet = None
    if request.outlet_id is not None:
        for candidate in outlets:
            if candidate.outlet_id == request.outlet_id:
                outlet = candidate
                break

    return _resolve_article_image(str(request.url), outlet)


def _resolve_article_image(url: str, outlet: Outlet | None) -> ArticleImageResponse:
    try:
        extracted = extract_article_page(url, outlet)
    except Exception as exc:
        logger.warning(
            "Article image extraction failed",
            extra={
                "url": url,
                "outlet_id": outlet.outlet_id if outlet is not None else None,
                "outlet": outlet.display_name if outlet is not None else None,
                "error": str(exc),
            },
        )
        return ArticleImageResponse(
            url=url,
            outlet_id=outlet.outlet_id if outlet is not None else None,
            image_url=None,
            image_source=None,
            image_status="missing",
            message=str(exc),
        )

    if extracted.image_url:
        logger.info(
            "Filled article image from article page",
            extra={
                "url": url,
                "outlet_id": outlet.outlet_id if outlet is not None else None,
                "outlet": outlet.display_name if outlet is not None else None,
                "image_source": extracted.image_source,
            },
        )
        return ArticleImageResponse(
            url=str(url),
            outlet_id=outlet.outlet_id if outlet is not None else None,
            image_url=extracted.image_url,
            image_source=extracted.image_source,
            image_status="article_extract",
            message=None,
        )

    return ArticleImageResponse(
        url=str(url),
        outlet_id=outlet.outlet_id if outlet is not None else None,
        image_url=None,
        image_source=None,
        image_status="missing",
        message="No usable image was found on the article page.",
    )


@app.get("/articles", response_model=PlaceholderResponse)
def list_articles() -> PlaceholderResponse:
    return PlaceholderResponse(
        status="not_implemented",
        message="Article listing will be wired after an external article API is selected.",
    )


@app.post("/articles/ingest", response_model=PlaceholderResponse)
def ingest_articles() -> PlaceholderResponse:
    return PlaceholderResponse(
        status="not_implemented",
        message="Article ingestion is reserved for future external API integration.",
    )
