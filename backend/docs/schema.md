# SQLite Storage Plan

Date: 2026-05-19

This is the locked storage shape for the RSS -> extract -> score -> display pipeline. It is documentation only for now: do not create `backend/data/irreflexive.db`, `schema.sql`, or migrations until the DB implementation phase.

## Engine

Use SQLite for the personal/demo version.

- Database path: `backend/data/irreflexive.db`
- Schema source when implemented: `backend/db/schema.sql`
- Python driver: stdlib `sqlite3` unless there is a clear reason to add an ORM
- Git policy: commit schema files, ignore generated database files

## Tables

### outlets

Optional for MVP. `backend/rss_config.py` can remain the source of truth until persistence needs outlet metadata.

| column | notes |
| --- | --- |
| `outlet_id` | Primary key; matches RSS config |
| `display_name` | Human-readable source name |
| `rss_url` | Feed URL |
| `homepage` | Nullable |

### articles

One row per canonical article URL. URL is the dedupe key.

| column | notes |
| --- | --- |
| `id` | Integer primary key |
| `url` | Unique canonical link from RSS |
| `url_hash` | Optional SHA256 of normalized URL for fast dedupe |
| `outlet_id` | Foreign key to `outlets.outlet_id` later, or plain string for MVP |
| `title` | From RSS |
| `published_at` | Nullable |
| `rss_summary` | Nullable; never used for scoring |
| `body_text` | Nullable; filled after article extraction |
| `body_hash` | Nullable SHA256 of extracted text to detect changes |
| `fetch_status` | `pending`, `ok`, or `failed` |
| `first_seen_at` | Timestamp when first observed in RSS |
| `last_fetched_at` | Timestamp for latest RSS/extraction touch |

### scores

One row per article and model version.

| column | notes |
| --- | --- |
| `id` | Integer primary key |
| `article_id` | Foreign key to `articles.id` |
| `label` | `left` or `right` |
| `confidence` | Float |
| `model_version` | Example: `head_v1_2class` |
| `scored_at` | Timestamp when scoring completed |

Recommended uniqueness: one active row per `(article_id, model_version)`. If historical score runs become useful later, add a separate run/version field instead of changing the article table.

## Field Alignment

Keep in-memory objects close to table names so storage wiring stays mechanical.

- RSS `FeedItem`: `outlet_id`, `title`, `url`, `published_at`, `summary`
- Article storage: `outlet_id`, `title`, `url`, `published_at`, `rss_summary`
- Score storage: `article_id`, `label`, `confidence`, `model_version`

`summary` from RSS maps to `rss_summary` at the storage boundary. It must not be used as model input.

## Refresh Rules

| event | DB behavior |
| --- | --- |
| New URL in RSS | Insert into `articles` with `fetch_status = pending` |
| URL seen again | Update `title`, `published_at`, `rss_summary`, and `last_fetched_at`; do not duplicate |
| Body extracted | Set `body_text`, `body_hash`, `fetch_status = ok`, and `last_fetched_at` |
| Body extraction failed | Set `fetch_status = failed` and `last_fetched_at` |
| Score run | Insert or update `scores` for the same `(article_id, model_version)` |
| Frontend latest list | Read joined articles plus latest scores, top 3 per outlet |

## Future File Layout

```text
backend/
  data/
    irreflexive.db
  db/
    schema.sql
    connection.py
    repositories.py
  storage.py
```

`backend/storage.py` is the boundary RSS, extraction, scoring, and API code should call. SQL stays behind that boundary when the SQLite phase starts.

## Not Yet

- No migration framework.
- No Postgres.
- No full HTML storage unless debugging requires it.
- No scoring from RSS summaries.
- No blocking RSS/API work on database persistence.
