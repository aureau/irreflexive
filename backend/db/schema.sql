PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS outlets (
    outlet_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    rss_url TEXT NOT NULL,
    homepage TEXT
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    url_hash TEXT NOT NULL,
    outlet_id TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TEXT,
    rss_summary TEXT,
    body_text TEXT,
    body_hash TEXT,
    fetch_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (fetch_status IN ('pending', 'ok', 'failed')),
    first_seen_at TEXT NOT NULL,
    last_fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_outlet_id
    ON articles (outlet_id);

CREATE INDEX IF NOT EXISTS idx_articles_url_hash
    ON articles (url_hash);

CREATE INDEX IF NOT EXISTS idx_articles_last_fetched_at
    ON articles (last_fetched_at);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL,
    label TEXT NOT NULL CHECK (label IN ('left', 'right')),
    confidence REAL NOT NULL,
    model_version TEXT NOT NULL,
    scored_at TEXT NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE,
    UNIQUE (article_id, model_version)
);

CREATE INDEX IF NOT EXISTS idx_scores_article_id
    ON scores (article_id);

CREATE INDEX IF NOT EXISTS idx_scores_model_scored_at
    ON scores (model_version, scored_at);
