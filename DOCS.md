# websearch/

## Role

CLI-driven web research toolkit for Claude Code. `cli.py` is the sole root-level `.py` file — a thin argparse dispatcher wiring the search, drilldown, and scrape workflows into 4 CLI subcommands. Touch this file when adding/removing a CLI subcommand or changing global logging setup; workflow logic itself lives in `src/search/` and `src/scraper/`.

## Modules

### cli.py (147 LOC)

**Purpose:** CLI entry-point. Configures daily-rotating file logging (no stderr handler) before any `src.*` import, then dispatches 4 argparse subcommands: `search_web` (query + mutex `--books`/`--pdf`/`--docs` flags → `search_web_workflow`), `search_engine_drilldown` (query + `--engine` + same mutex flags → cache-read-or-rerun, then `format_engine_pool`), `scrape_url_chromium` (url → `scrape_url_chromium_workflow`, the crawl4ai/chromium lane; rejects `.pdf` paths, tells the user to download manually), `scrape_url_camoufox` (url → `scrape_url_camoufox_workflow`, the Camoufox/Playwright-Firefox lane — a deliberate SECOND acquisition engine chosen explicitly by name, not a fallback of `scrape_url_chromium`; same `.pdf` rejection).
**Reads:** CLI args (argparse), disk cache via `cache_read` (drilldown cache-miss path).
**Writes:** `src/logs/cli.log` (rotating log), stdout (result text).
**Called by:** invoked directly as the CLI entry-point (`python cli.py <subcommand>`), not imported elsewhere.
**Calls out:** `src.search.search_web.search_web_workflow`, `src.search.browser.kill_own_chrome_atexit`, `src.search.cache.{cache_key,cache_read,format_engine_pool}`, `src.scraper.chromium_scrape.scrape_url_chromium_workflow`, `src.scraper.camoufox_scrape.scrape_url_camoufox_workflow`, `src.log_janitor.get_retention_days`.

## Gotchas

- 4 subcommands exist (`search_web`, `search_engine_drilldown`, `scrape_url_chromium`, `scrape_url_camoufox`); both scrape subcommands reject `.pdf` URLs — PDF download is delegated to the user. `scrape_url_chromium`/`scrape_url_camoufox` are two independent acquisition lanes (crawl4ai/chromium vs Camoufox/Firefox) — the agent picks one deliberately by which subcommand it invokes; there is no auto-selection or fallback between them anywhere in this codebase.
- Logging setup MUST run before any `src.*` import — module-load-time log calls from those imports would otherwise route to Python's default stderr `lastResort` handler instead of the file handler.
- `atexit.register(kill_own_chrome_atexit)` — PID-scoped last-resort backstop (never a profile-pattern kill) for interpreter exit paths that skip `search_web_workflow`'s own `finally: kill_own_chrome()` (e.g. an uncaught exception before that point).
