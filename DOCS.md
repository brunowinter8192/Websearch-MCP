# websearch/

## Role

CLI-driven web research toolkit for Claude Code. `cli.py` is the sole root-level `.py` file — a thin argparse dispatcher wiring the search, drilldown, and scrape workflows into 3 CLI subcommands. Touch this file when adding/removing a CLI subcommand or changing global logging setup; workflow logic itself lives in `src/search/` and `src/scraper/`.

## Modules

### cli.py (126 LOC)

**Purpose:** CLI entry-point. Configures daily-rotating file logging (no stderr handler) before any `src.*` import, then dispatches 3 argparse subcommands: `search_web` (query + mutex `--books`/`--pdf`/`--docs` flags → `search_web_workflow`), `search_engine_drilldown` (query + `--engine` + same mutex flags → cache-read-or-rerun, then `format_engine_pool`), `scrape_url` (url → `scrape_url_workflow`; rejects `.pdf` paths, tells the user to download manually).
**Reads:** CLI args (argparse), disk cache via `cache_read` (drilldown cache-miss path).
**Writes:** `src/logs/cli.log` (rotating log), stdout (result text).
**Called by:** invoked directly as the CLI entry-point (`python cli.py <subcommand>`), not imported elsewhere.
**Calls out:** `src.search.search_web.search_web_workflow`, `src.search.browser.kill_stale_chrome`, `src.search.cache.{cache_key,cache_read,format_engine_pool}`, `src.scraper.scrape_url.scrape_url_workflow`, `src.log_janitor.get_retention_days`.

## Gotchas

- Only 3 subcommands exist (`search_web`, `search_engine_drilldown`, `scrape_url`); `scrape_url` rejects `.pdf` URLs — PDF download is delegated to the user.
- Logging setup MUST run before any `src.*` import — module-load-time log calls from those imports would otherwise route to Python's default stderr `lastResort` handler instead of the file handler.
- `atexit.register(kill_stale_chrome)` ensures pydoll Chrome processes are killed on interpreter exit, including on uncaught exceptions.
