# websearch/

## Role

CLI-driven web research toolkit for Claude Code. `cli.py` is the sole root-level `.py` file — a thin argparse dispatcher wiring the search, drilldown, and scrape workflows into 3 CLI subcommands. Touch this file when adding/removing a CLI subcommand or changing global logging setup; workflow logic itself lives in `src/search/` and `src/scraper/`.

## Modules

### cli.py (132 LOC)

**Purpose:** CLI entry-point. Configures daily-rotating file logging (no stderr handler) before any `src.*` import, then dispatches 3 argparse subcommands: `search_web` (query + mutex `--books`/`--pdf`/`--docs` flags → `search_web_workflow`), `search_engine_drilldown` (query + `--engine` + same mutex flags → cache-read-or-rerun, then `format_engine_pool`), `scrape_url_chromium` (url → `scrape_url_chromium_workflow`, the crawl4ai/chromium lane; rejects `.pdf` paths, tells the user to download manually).
**Reads:** CLI args (argparse), disk cache via `cache_read` (drilldown cache-miss path).
**Writes:** `src/logs/cli.log` (rotating log), stdout (result text).
**Called by:** invoked directly as the CLI entry-point (`python cli.py <subcommand>`), not imported elsewhere.
**Calls out:** `src.search.search_web.search_web_workflow`, `src.search.browser.kill_own_chrome_atexit`, `src.search.cache.{cache_key,cache_read,format_engine_pool}`, `src.scraper.chromium_scrape.scrape_url_chromium_workflow`, `src.log_janitor.get_retention_days`.

## Gotchas

- 3 subcommands exist (`search_web`, `search_engine_drilldown`, `scrape_url_chromium`); the scrape subcommand rejects `.pdf` URLs — PDF download is delegated to the user. There is exactly ONE ad-hoc acquisition lane, so there is no lane choice, no auto-selection and no fallback on this path.
- **`scrape_url_camoufox` was REMOVED here on 2026-08-27 — do not re-add it as a "missing" subcommand.** The Camoufox module, its calibrated config and its tests are all still present and untouched, which makes the absent subcommand look like an oversight; it is a decision (see `process-docs/lane_choice/`). Reactivation means re-adding the import plus the subparser/dispatch branch, and nothing else. The batch pipeline's own `--engine camoufox` (`src/crawler/`) is a different consumer and was never part of this removal.
- Logging setup MUST run before any `src.*` import — module-load-time log calls from those imports would otherwise route to Python's default stderr `lastResort` handler instead of the file handler.
- `atexit.register(kill_own_chrome_atexit)` — PID-scoped last-resort backstop (never a profile-pattern kill) for interpreter exit paths that skip `search_web_workflow`'s own `finally: kill_own_chrome()` (e.g. an uncaught exception before that point).
