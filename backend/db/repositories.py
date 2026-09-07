from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend.db.connection import DB_PATH, get_connection, init_db
from backend.rss.rss_feed import FeedItem


FetchStatus = Literal["pending", "ok", "failed"]
ScoreLabel = Literal["left", "right"]


class Article(BaseModel):
    id: int
    url: str
    url_hash: str
    outlet_id: str
    title: str
    published_at: datetime | None = None
    rss_summary: str | None = None
    body_text: str | None = None
    body_hash: str | None = None
    fetch_status: FetchStatus = "pending"
    first_seen_at: datetime
    last_fetched_at: datetime


class ArticleScore(BaseModel):
    id: int
    article_id: int
    label: ScoreLabel
    confidence: float
    model_version: str
    scored_at: datetime


class LatestScoredArticle(BaseModel):
    article: Article
    score: ArticleScore


def upsert_article_from_feed_item(item: FeedItem, db_path: Path = DB_PATH) -> int:
    init_db(db_path)

    normalized_url = _normalize_url(item.url)
    now = _now_iso()
    published_at = _datetime_to_iso(item.published_at)

    with get_connection(db_path) as connection:
        existing = connection.execute(
            "SELECT id FROM articles WHERE url = ?",
            (normalized_url,),
        ).fetchone()
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO articles (
                    url,
                    url_hash,
                    outlet_id,
                    title,
                    published_at,
                    rss_summary,
                    fetch_status,
                    first_seen_at,
                    last_fetched_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    normalized_url,
                    _hash_text(normalized_url),
                    item.outlet_id,
                    item.title,
                    published_at,
                    item.summary,
                    now,
                    now,
                ),
            )
            return int(cursor.lastrowid)

        article_id = int(existing["id"])
        connection.execute(
            """
            UPDATE articles
            SET outlet_id = ?,
                title = ?,
                published_at = ?,
                rss_summary = ?,
                last_fetched_at = ?
            WHERE id = ?
            """,
            (
                item.outlet_id,
                item.title,
                published_at,
                item.summary,
                now,
                article_id,
            ),
        )
        return article_id


def get_article_by_url(url: str, db_path: Path = DB_PATH) -> Article | None:
    init_db(db_path)

    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM articles WHERE url = ?",
            (_normalize_url(url),),
        ).fetchone()

    if row is None:
        return None
    return _article_from_row(row)


def update_article_body_text(
    article_id: int,
    body_text: str,
    fetch_status: FetchStatus = "ok",
    db_path: Path = DB_PATH,
) -> Article:
    if fetch_status not in {"ok", "failed"}:
        raise ValueError("fetch_status must be 'ok' or 'failed' when updating article body text")

    init_db(db_path)
    cleaned_body = body_text.strip()
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE articles
            SET body_text = ?,
                body_hash = ?,
                fetch_status = ?,
                last_fetched_at = ?
            WHERE id = ?
            """,
            (
                cleaned_body or None,
                _hash_text(cleaned_body) if cleaned_body else None,
                fetch_status,
                _now_iso(),
                article_id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM articles WHERE id = ?",
            (article_id,),
        ).fetchone()

    if row is None:
        raise KeyError(f"Unknown article_id: {article_id}")
    return _article_from_row(row)


def mark_article_fetch_failed(article_id: int, db_path: Path = DB_PATH) -> Article:
    init_db(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE articles
            SET fetch_status = 'failed',
                last_fetched_at = ?
            WHERE id = ?
            """,
            (_now_iso(), article_id),
        )
        row = connection.execute(
            "SELECT * FROM articles WHERE id = ?",
            (article_id,),
        ).fetchone()

    if row is None:
        raise KeyError(f"Unknown article_id: {article_id}")
    return _article_from_row(row)


def save_score(
    article_id: int,
    label: ScoreLabel,
    confidence: float,
    model_version: str,
    db_path: Path = DB_PATH,
) -> ArticleScore:
    init_db(db_path)

    scored_at = _now_iso()
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO scores (
                article_id,
                label,
                confidence,
                model_version,
                scored_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(article_id, model_version) DO UPDATE SET
                label = excluded.label,
                confidence = excluded.confidence,
                scored_at = excluded.scored_at
            """,
            (article_id, label, confidence, model_version, scored_at),
        )
        row = connection.execute(
            """
            SELECT *
            FROM scores
            WHERE article_id = ? AND model_version = ?
            """,
            (article_id, model_version),
        ).fetchone()

    if row is None:
        raise KeyError(f"Unknown article_id: {article_id}")
    return _score_from_row(row)


def list_latest_scored(
    per_outlet: int = 3,
    model_version: str | None = None,
    db_path: Path = DB_PATH,
) -> list[LatestScoredArticle]:
    init_db(db_path)

    model_filter = "WHERE ranked_scores.score_rank = 1"
    params: list[object] = []
    if model_version is not None:
        model_filter += " AND ranked_scores.model_version = ?"
        params.append(model_version)
    params.append(per_outlet)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            f"""
            WITH ranked_scores AS (
                SELECT
                    scores.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY scores.article_id
                        ORDER BY scores.scored_at DESC, scores.id DESC
                    ) AS score_rank
                FROM scores
            ),
            scored_articles AS (
                SELECT
                    articles.id AS article_id,
                    articles.url,
                    articles.url_hash,
                    articles.outlet_id,
                    articles.title,
                    articles.published_at,
                    articles.rss_summary,
                    articles.body_text,
                    articles.body_hash,
                    articles.fetch_status,
                    articles.first_seen_at,
                    articles.last_fetched_at,
                    ranked_scores.id AS score_id,
                    ranked_scores.label,
                    ranked_scores.confidence,
                    ranked_scores.model_version,
                    ranked_scores.scored_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY articles.outlet_id
                        ORDER BY ranked_scores.scored_at DESC, ranked_scores.id DESC
                    ) AS outlet_rank
                FROM articles
                JOIN ranked_scores ON ranked_scores.article_id = articles.id
                {model_filter}
            )
            SELECT *
            FROM scored_articles
            WHERE outlet_rank <= ?
            ORDER BY scored_at DESC, score_id DESC
            """,
            tuple(params),
        ).fetchall()

    return [_latest_scored_from_row(row) for row in rows]


def clear_storage(db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        connection.execute("DELETE FROM scores")
        connection.execute("DELETE FROM articles")
        connection.execute("DELETE FROM outlets")


def _article_from_row(row) -> Article:
    return Article(
        id=int(row["id"]),
        url=row["url"],
        url_hash=row["url_hash"],
        outlet_id=row["outlet_id"],
        title=row["title"],
        published_at=_datetime_from_iso(row["published_at"]),
        rss_summary=row["rss_summary"],
        body_text=row["body_text"],
        body_hash=row["body_hash"],
        fetch_status=row["fetch_status"],
        first_seen_at=_datetime_from_iso(row["first_seen_at"]),
        last_fetched_at=_datetime_from_iso(row["last_fetched_at"]),
    )


def _score_from_row(row) -> ArticleScore:
    return ArticleScore(
        id=int(row["id"]),
        article_id=int(row["article_id"]),
        label=row["label"],
        confidence=float(row["confidence"]),
        model_version=row["model_version"],
        scored_at=_datetime_from_iso(row["scored_at"]),
    )


def _latest_scored_from_row(row) -> LatestScoredArticle:
    article = Article(
        id=int(row["article_id"]),
        url=row["url"],
        url_hash=row["url_hash"],
        outlet_id=row["outlet_id"],
        title=row["title"],
        published_at=_datetime_from_iso(row["published_at"]),
        rss_summary=row["rss_summary"],
        body_text=row["body_text"],
        body_hash=row["body_hash"],
        fetch_status=row["fetch_status"],
        first_seen_at=_datetime_from_iso(row["first_seen_at"]),
        last_fetched_at=_datetime_from_iso(row["last_fetched_at"]),
    )
    score = ArticleScore(
        id=int(row["score_id"]),
        article_id=int(row["article_id"]),
        label=row["label"],
        confidence=float(row["confidence"]),
        model_version=row["model_version"],
        scored_at=_datetime_from_iso(row["scored_at"]),
    )
    return LatestScoredArticle(article=article, score=score)


def _normalize_url(url: str) -> str:
    return url.strip()


def _hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return _datetime_to_iso(datetime.now(UTC))


def _datetime_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _datetime_from_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value).astimezone(UTC)
