# src/scraper/

## Role

URL scraping for the `scrape_url` CLI subcommand and the shared garbage classifier for batch crawling. Turns a single URL into clean, noise-filtered markdown via one stealth crawl4ai browser call (Crawl4AI v0.8.6). Touch this package when changing scrape extraction, cookie/consent handling, or garbage classification. Not the batch crawler itself — that is `src/crawler/`.

## Public Interface

`__init__.py` is empty — modules are imported by path:

- `scrape_url_workflow(url, max_content_length=15000)` (scrape_url.py) — imported by `cli.py` as the `scrape_url` subcommand entry. Returns `list[TextContent]`.
- `is_garbage_content(content) -> str | None` (scrape_url.py) — imported by `src/crawler/crawl_site.py` for batch-crawl garbage filtering.
- `log_scrape(record)`, `write_sidecar(url, ts, content, outcome, mode)` (scrape_logger.py) — called by scrape_url.py.

## Flow

`scrape_url_workflow` → `try_scrape(url)` runs one stealth crawl4ai call → content selected (fit_markdown if ≥200 chars, else raw_markdown fallback) → `is_garbage_content` classifies → cookie_wall retried once via `strip_consent_prefix` → `truncate_content` to max length → result + metadata logged via scrape_logger (JSONL record + content sidecar) → markdown (or per-type error string) returned.

## Modules

### scrape_url.py (252 LOC)

**Purpose:** Scrape orchestrator. One crawl4ai browser call with native anti-bot baseline (`enable_stealth` + `UndetectedAdapter` + `magic=True` + `wait_until="load"`, `page_timeout=60000`, `max_retries=0`, no phase escalation). Selects `fit_markdown` (PruningContentFilter 0.48) or `raw_markdown` fallback, classifies via `is_garbage_content` (7 categories), recovers cookie-wall pages via `strip_consent_prefix`, truncates to max length, returns markdown in `TextContent` or a per-type error message from `_GARBAGE_MESSAGES`. The `except Exception` handler in `try_scrape` additionally distinguishes a browser-launch/executable-missing failure (`is_browser_launch_error`, matched on the exception message) from a genuine empty/blocked page, mapping it to its own `browser_missing` outcome instead of the generic empty-content message. Also exports `is_garbage_content` as the shared classifier for batch crawl.
**Reads:** `url` arg + optional `max_content_length` (default 15000 = `DEFAULT_MAX_CONTENT_LENGTH`).
**Writes:** result content + metadata via scrape_logger (no direct file writes).
**Called by:** `cli.py` (scrape_url_workflow); `src/crawler/crawl_site.py` (is_garbage_content).
**Calls out:** `crawl4ai` (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter, AsyncPlaywrightCrawlerStrategy, PruningContentFilter, DefaultMarkdownGenerator); `mcp.types.TextContent`; `scrape_logger` (log_scrape, write_sidecar).

### scrape_logger.py (88 LOC)

**Purpose:** Per-URL structured logging for scrape_url. Two outputs per call: one JSONL record appended to the scrape log, one sidecar `.md` holding the exact content the caller received. No sidecar on empty outcome; sidecar IS written on garbage outcome (the classified content is preserved for inspection).
**Reads:** `WEBSEARCH_SCRAPE_LOG_PATH` env var (fallback `src/logs/scrape_log.jsonl`); sidecar dir `<log_dir>/scrape_content/`.
**Writes:** `src/logs/scrape_log.jsonl` (one line per call); `<log_dir>/scrape_content/<ts>_<slug>.md` (per-call sidecar). Both gitignored.
**Called by:** `scrape_url.py` (end of scrape_url_workflow).
**Calls out:** `src/log_janitor.py` (maybe_prune_jsonl, maybe_prune_sidecars).

## State

No shared in-memory state — each `scrape_url_workflow` call is independent. The only persistence is the JSONL log + content sidecars written by scrape_logger and pruned by log_janitor.

## Gotchas

- `remove_overlay_elements` is NOT used — it misclassifies legitimate DOM (e.g. Wikipedia content) as overlays and destroys content. Cookie removal is done via `excluded_selector=COOKIE_CONSENT_SELECTOR` instead.
- `cky-modal` MUST stay in `COOKIE_CONSENT_SELECTOR` — CookieYes stores the full 12K+ char consent dialog there; without it only the 236-char banner is stripped.
- `is_garbage_content` order matters — `minimal_content` (`<50` chars) is checked FIRST. The 7 categories: `minimal_content`, `crawl4ai_error`, `http_error`, `nav_dump` (≥20 lines, >60% bare link lines), `cookie_wall`, `login_wall`, `cloudflare`. `status_code >= 400` short-circuits to `http_error`.
- `fit_markdown < 200` chars (`MIN_CONTENT_THRESHOLD`) triggers `raw_markdown` fallback — table-heavy pages filter to near-empty otherwise.
- `strip_consent_prefix` only fires when CONSENT_WORDS density in the first 3000 chars exceeds `CONSENT_DENSITY_THRESHOLD` (5); it searches for the first heading after `CONSENT_SKIP_OFFSET` (300 chars).
- crawl4ai captures stdout — write debug to files, never `print()`.
- `get_plugin_hint` is a stub returning `""` (domain blocking removed).
- Missing/failed patchright chromium binary looks IDENTICAL to a genuinely empty page unless caught: launch fails in ~300ms with `http_status:null`, `bytes_raw_markdown:null` — exactly the same shape as a blocked/empty scrape. `is_browser_launch_error` guards against this by matching launch-exception substrings (`executable doesn't exist`, `playwright install`, `browsertype.launch`); on match the outcome is `browser_missing` (logged at ERROR, not WARNING) with a message naming the fix: `./venv/bin/python -m patchright install chromium`.
