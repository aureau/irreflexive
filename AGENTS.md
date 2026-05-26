---
description: 
alwaysApply: true
---

---
description: 
alwaysApply: false
---

# Repository Guidelines

## Project Structure & Module Organization

This repository is organized around a Python backend for article bias scoring and a placeholder frontend.

- `backend/main.py` is the current executable entry point for local scoring experiments.
- `backend/chunking.py`, `backend/downloader.py`, and `backend/model.py` contain article extraction, HTML downloading, embedding, and scoring logic.
- `backend/baselines/` stores baseline vectors, corpus calculation scripts, datasets, and downloaded reference pages.
- `backend/test-articles/` contains saved HTML articles used for manual scoring checks.
- `backend/early-article-scraping/` contains earlier scraping experiments and ad hoc tests.
- `frontend/src/` exists but is currently empty.

Keep generated data, downloaded pages, and model artifacts under `backend/baselines/` or another clearly named data directory rather than mixing them with source modules.

## Build, Test, and Development Commands

No project-level package manager or test runner is configured yet. Use direct Python commands from the repository root:

- `python backend/main.py` runs the current local scoring flow against a saved test article.
- `python backend/early-article-scraping/test.py` runs the existing scraping test script, if its local inputs are present.
- `python backend/baselines/baseline_calculation.py` recalculates baseline vectors from the baseline data.

Several scripts use relative paths such as `baselines/...` and `test-articles/...`; if a script cannot find files from the repo root, run it from `backend/`.

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation. Prefer small, direct functions with descriptive snake_case names, matching the existing modules (`embed_article`, `score_article`, `extract_chunk_and_clean_article`). Keep script-style experimentation behind `if __name__ == "__main__":` blocks so modules can be imported without side effects.

Avoid committing `__pycache__`, `.DS_Store`, temporary notebooks, or large generated artifacts unless they are required reproducible baselines.

## Testing Guidelines

Testing is currently manual and script-based. When changing scoring, chunking, or downloading behavior, run `python backend/main.py` and compare output against articles in `backend/test-articles/`. Add focused tests near the code they exercise or introduce a formal `tests/` directory before expanding coverage.

Name future tests after the behavior under test, for example `test_chunking.py` or `test_score_article.py`.

## Commit & Pull Request Guidelines

Recent commit messages are informal and short, so use clearer messages going forward: `Add baseline scoring script`, `Fix article chunk cleanup`, or `Document backend workflow`.

Pull requests should include a concise description, commands run, affected data/model artifacts, and screenshots only when frontend UI changes are included. Link related issues or notes when the change affects project direction or evaluation assumptions.
