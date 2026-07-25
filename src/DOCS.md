# src/

## Role

Root of the source tree. `log_janitor.py` is the only `.py` module directly at this level — a shared log-retention utility used by `cli.py` and the sub-packages below. All functional packages (`search/`, `scraper/`, `crawler/`, `news/`) live one level down, each with its own `DOCS.md`.

## Modules

### log_janitor.py (88 LOC)

**Purpose:** 14-day log retention janitor. On-write trigger with 1h marker-throttled slow path. Three public functions: `get_retention_days()` (env override), `maybe_prune_jsonl(log_path)` (timestamp-based JSONL filter + atomic rewrite), `maybe_prune_sidecars(sidecar_dir)` (mtime-based `.md` unlink). All failures logged as WARNING and swallowed.
**Reads:** JSONL log files, sidecar `.md` directories, `WEBSEARCH_LOG_RETENTION_DAYS` env var.
**Writes:** rewrites pruned JSONL atomically, unlinks stale sidecar files.
**Called by:** `src/search/query_logger.py`, `src/scraper/scrape_logger.py`, `cli.py` (imports `get_retention_days` for `TimedRotatingFileHandler` backupCount).
**Calls out:** none (stdlib only).
