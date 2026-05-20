# RSS Article Extractor Notes

## Phase 0 - Scope Lock

Date: 2026-05-19

### Principles

- RSS is link discovery only. RSS metadata is not scoring input.
- The backend owns RSS fetching and parsing. The frontend only displays API JSON.
- Build one pipeline in small tested stages:
  `feeds config -> fetch/parse RSS -> pick top N per outlet -> fetch article body -> score -> API JSON -> frontend list`.
- For this MVP slice, stop after parsed metadata:
  `title`, `link`, `source`, and `published_at`.

### In Scope

- Use 4 outlets, one RSS URL each.
- Return 3 items per outlet.
- Sort newest first by `published_at` when present.
- Fall back to feed order when `published_at` is missing.
- Use fetch-on-request or in-memory results only.
- Create a simple config fixture shape that Phase 1 tests can reuse.

### Out Of Scope

- Full article extraction.
- Scoring.
- Database or persistent cache.
- Cron jobs, schedulers, or background refresh.
- Frontend display beyond consuming backend API JSON later.

### Phase 0 Outlet Fixture

| outlet_id | display_name | rss_url | homepage |
| --- | --- | --- | --- |
| `bbc_world` | BBC News - World | `https://feeds.bbci.co.uk/news/world/rss.xml` | `https://www.bbc.com/news/world` |
| `npr_news` | NPR News | `https://feeds.npr.org/1001/rss.xml` | `https://www.npr.org/sections/news/` |
| `guardian_us` | The Guardian - US News | `https://www.theguardian.com/us-news/rss` | `https://www.theguardian.com/us-news` |
| `nyt_home` | The New York Times | `https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml` | `https://www.nytimes.com/` |

### Future Config Shape

```json
[
  {
    "outlet_id": "bbc_world",
    "display_name": "BBC News - World",
    "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "homepage": "https://www.bbc.com/news/world"
  }
]
```

### Done Criteria

- Phase 0 is done when this document has the locked scope and outlet fixture above.
- No tests are required in Phase 0.
- Phase 1 starts with turning this fixture into a validated feed config.

## Phase 1 - Feed Config + Validation

Date: 2026-05-19

### Goal

Create one trusted source of truth for which RSS feeds the backend polls.

### Built

- Added a static outlet config in `backend/rss_config.py`.
- Added a typed `Outlet` model with:
  - `outlet_id`
  - `display_name`
  - `rss_url`
  - optional `homepage`
- Added `load_outlets()` to validate and return the outlet list.
- Added `FeedConfigError` for clear config failures.

### Validation Rules

- Required fields must be present.
- `rss_url` and `homepage` must be valid `http` or `https` URLs.
- `outlet_id` values must be unique.
- String fields are stripped before validation.

### Tests

- Valid config loads.
- Missing `rss_url` raises an error.
- Duplicate `outlet_id` raises an error.
- Invalid URL raises an error.

### Done Criteria

- Phase 1 is done when `load_outlets()` returns a typed list of trusted outlets.
- Phase 1 is done when `backend/tests/test_rss_config.py` passes.
- Phase 2 starts with RSS fetch and parse using this config.

## Phase 2 - RSS Fetch + Parse

Date: 2026-05-19

### Goal

Given one outlet feed, return normalized article metadata without fetching full article bodies.

### Built

- Added `backend/rss_feed.py`.
- Added `FeedItem` with:
  - `outlet_id`
  - `source`
  - `title`
  - `url`
  - optional `published_at`
  - optional `summary`
- Added `fetch_feed(outlet)` for HTTP RSS fetching with timeout and user-agent.
- Added `parse_feed_xml(xml_text, outlet)` for deterministic fixture-based parsing.
- Supports RSS 2.0 `<item>` and Atom `<entry>` feeds.
- Sorts parsed items newest-first when dates exist, falling back to feed order for missing dates.

### Tests

- Parse sample RSS 2.0 into normalized items.
- Parse sample Atom into normalized items.
- Missing `pubDate` returns `published_at = None`.
- Malformed XML raises a clear parse error.
- Empty feed returns an empty list.
- `fetch_feed()` is covered with a mocked HTTP response, not live network.

### Done Criteria

- Phase 2 is done when `backend/tests/test_rss_feed.py` passes.
- Phase 3 starts with multi-outlet aggregation and the `3 per outlet` rule.

## Phase 3 - Multi-Outlet Aggregation

Date: 2026-05-19

### Goal

Collect latest feed metadata across all configured outlets while applying the `3 per outlet` rule.

### Built

- Added `backend/rss_aggregator.py`.
- Added `get_latest_articles(outlets, per_outlet=3)`.
- Added `AggregatedFeedResult` with:
  - `items`
  - `errors`
- Added `OutletFetchError` so one broken feed does not kill the whole batch.
- Added optional URL dedupe, enabled by default.
- Added `backend/scripts/print_latest_rss.py` for manual live-feed smoke checks.

### Tests

- Mocked feed with 10 items returns only 3.
- One outlet failure still returns articles from healthy outlets.
- Duplicate URLs are kept once by default.
- Duplicate URLs can be kept when dedupe is disabled.

### Manual Smoke

```bash
.venv/bin/python backend/scripts/print_latest_rss.py
```

Expected MVP shape: 4 outlets times 3 items each, minus any live feed failures or duplicate URLs.

### Done Criteria

- Phase 3 is done when `backend/tests/test_rss_aggregator.py` passes.
- Phase 3 is done when the live smoke script can print current feed rows when network is available.
- Phase 4 starts with the next requested layer; no article body extraction, scoring, DB, scheduler, or API route wiring is part of Phase 3.

## Phase 4 - API Layer

Date: 2026-05-19

### Goal

Expose the latest RSS article metadata as stable JSON for curl, Postman, or the frontend.

### Built

- Added `GET /api/articles/latest` in `api/main.py`.
- Route calls `load_outlets()` and `get_latest_articles(outlets, per_outlet=3)`.
- Response shape:
  - `articles`
  - `errors`
  - `fetched_at`
- Each article includes:
  - `outlet`
  - `title`
  - `url`
  - optional `published_at`
  - optional `summary`
- Partial feed failures return `200` with `errors` populated instead of failing the whole response.

### Tests

- Mocked aggregator returns `200` and the expected JSON article shape.
- Mocked partial failure returns `200` with `errors` populated.

### Done Criteria

- Phase 4 is done when `backend/tests/test_api_articles.py` passes.
- Phase 4 is done when `/api/articles/latest` can show JSON in browser/Postman/curl.
- Phase 5 starts with the next requested layer; no article body extraction, scoring, DB, scheduler, or frontend work is part of Phase 4.

## Phase 5 - Frontend Display

Date: 2026-05-20

### Goal

Show latest RSS article metadata in the frontend as cards with outlet, title, link, and time.

### Built

- Added a same-origin frontend proxy route at `frontend/src/app/api/articles/latest/route.ts`.
- The proxy forwards to FastAPI `GET /api/articles/latest` using `IRREFLEXIVE_API_BASE_URL` or `http://127.0.0.1:8000`.
- Replaced the mock `ExploreLatest` section with a live fetch from `/api/articles/latest`.
- Added grouped outlet sections, article cards, loading state, global error state, partial feed error display, and a refresh button.
- Updated footer copy from mock/disconnected language to live RSS metadata.

### Tests

- TypeScript typecheck should pass.
- Manual browser check should show latest articles when both backend and frontend dev servers are running.

### Done Criteria

- Phase 5 is done when the frontend can display latest RSS cards from `/api/articles/latest`.
- Phase 5 does not include article body extraction, scoring badges, DB-backed reads, or scheduler work.

## Phase 6 - Wire Scoring

Date: 2026-05-20

### Goal

Attach bias labels and confidence to the same latest RSS article cards, without using the database yet.

### Built

- `GET /api/articles/latest` now attempts to score each RSS item URL independently.
- Per article flow:
  - fetch article URL
  - extract body text with `trafilatura`
  - chunk text
  - score chunks with the trained head
- Article response now includes:
  - `scored`
  - optional `label`
  - optional `confidence`
  - optional `model_version`
  - optional `scoring_error`
- One extraction/scoring failure marks only that article as `scored: false`; the endpoint still returns `200`.
- Frontend cards now show a bias/confidence badge or `Not scored`.

### Tests

- Mocked extractor and scorer return a fixed label/confidence.
- Extract failure returns article metadata with `scored: false`, not a route-level `500`.
- Existing partial feed failure behavior still returns `200` with feed errors.

### Done Criteria

- Phase 6 is done when backend API tests and frontend typecheck pass.
- Phase 7 remains the database/cache phase; no scheduler or DB-backed frontend read is part of Phase 6.
