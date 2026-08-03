# src/scraper/

## Role

URL scraping for the `scrape_url` CLI subcommand and the shared garbage classifier for batch crawling. Turns a single URL into clean, noise-filtered markdown via one stealth crawl4ai browser call (Crawl4AI v0.8.6). Touch this package when changing scrape extraction, cookie/consent handling, or garbage classification. Not the batch crawler itself — that is `src/crawler/`.

## Public Interface

`__init__.py` is empty — modules are imported by path:

- `scrape_url_workflow(url, max_content_length=15000)` (scrape_url.py) — imported by `cli.py` as the `scrape_url` subcommand entry. Returns `list[TextContent]`.
- `is_garbage_content(content) -> str | None` (scrape_url.py) — imported by `src/crawler/crawl_site.py` for batch-crawl garbage filtering.
- `log_scrape(record)`, `write_sidecar(url, ts, content, outcome, mode)` (scrape_logger.py) — called by scrape_url.py.

## Flow

`scrape_url_workflow` → `try_scrape(url)` runs one stealth crawl4ai call → `extract_date` pulls a publication date from the raw HTML (independent of markdown quality) → content selected (fit_markdown if ≥200 chars, else raw_markdown fallback) → `is_garbage_content` classifies → cookie_wall retried once via `strip_consent_prefix` → `truncate_content` to max length → result + metadata logged via scrape_logger (JSONL record + content sidecar) → markdown, optionally prefixed with a `Published:` line, (or per-type error string) returned.

## Modules

### scrape_url.py (367 LOC)

**Purpose:** Scrape orchestrator. One crawl4ai browser call with native anti-bot baseline (`enable_stealth` + `UndetectedAdapter` + `magic=True` + `wait_until="load"`, `page_timeout=60000`, `max_retries=0`, no phase escalation). Selects `fit_markdown` (PruningContentFilter 0.48) or `raw_markdown` fallback, classifies via `is_garbage_content` (7 categories), recovers cookie-wall pages via `strip_consent_prefix`, truncates to max length, returns markdown in `TextContent` or a per-type error message from `_GARBAGE_MESSAGES`. The `except Exception` handler in `try_scrape` additionally distinguishes a browser-launch/executable-missing failure (`is_browser_launch_error`, matched on the exception message) from a genuine empty/blocked page, mapping it to its own `browser_missing` outcome instead of the generic empty-content message. Also exports `is_garbage_content` as the shared classifier for batch crawl. `extract_date(html, url)` pulls the original publication date (day-precision ISO) from `result.html` — the raw pre-cleaning HTML crawl4ai captures on every fetch, read here for the first time — via `htmldate.find_date(extensive_search=True, original_date=True)`; runs off the event loop with a 5s hard timeout (`asyncio.wait_for(asyncio.to_thread(...))`), any exception/timeout/absence degrades to `None`. Called inside `try_scrape` right after `raw_md` is computed, BEFORE the cookie-wall/garbage branches (a consent-walled markdown extract can still sit on top of HTML with real date metadata) — result stored as `meta["date"]`, never the raw HTML itself, which stays local to `try_scrape`. Rendered as an optional `Published: <date>` line between the `# Content from:` header and the blank-line/body boundary; omitted entirely when absent. `extract_crawl4ai_diagnosis(result)` reads crawl4ai's own anti-bot verdict off the result object (`success`, `error_message`, `crawl_stats["attempts"|"resolved_by"|"fallback_fetch_used"]`) right after `status_code`/`content_type` are read, before any garbage/http_error branching — recorded into `meta` for the scrape log only, never consulted by this module's own classification. `extract_config_stamp(browser_config, adapter, crawler_strategy, run_config)` reads the scrape-governing kwargs back off the just-constructed config objects (never re-declares their values) right after `run_config` is built — always present in `meta["config"]` on every return path, including the total-failure branch, since the configs exist before the network call. `build_config_record(scrape_config, max_content_length)` (called once in `scrape_url_workflow`, right after `try_scrape` returns) merges that stamp with the two post-processing params only the caller knows (`max_content_length`, `MIN_CONTENT_THRESHOLD`); `hash_config(config)` derives a 10-hex-char sha256 grouping key from it — both `config` (full values, for inspection) and `config_hash` (cheap equality grouping) go into the log record.
**Reads:** `url` arg + optional `max_content_length` (default 15000 = `DEFAULT_MAX_CONTENT_LENGTH`).
**Writes:** result content + metadata via scrape_logger (no direct file writes).
**Called by:** `cli.py` (scrape_url_workflow); `src/crawler/crawl_site.py` (is_garbage_content).
**Calls out:** `crawl4ai` (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter, AsyncPlaywrightCrawlerStrategy, PruningContentFilter, DefaultMarkdownGenerator); `htmldate` (find_date); `mcp.types.TextContent`; `scrape_logger` (log_scrape, write_sidecar).

### scrape_logger.py (102 LOC)

**Purpose:** Per-URL structured logging for scrape_url. Two outputs per call: one JSONL record appended to the scrape log, one sidecar `.md` holding the exact content the caller received. No sidecar on empty outcome; sidecar IS written on garbage outcome (the classified content is preserved for inspection). JSONL record carries `published_date` (htmldate-extracted, `"ok"` outcome only); the sidecar header does NOT — the date is already visible in both the returned content and the JSONL log, a third copy was judged redundant. JSONL record also carries crawl4ai's own anti-bot diagnosis verbatim (`crawl4ai_success`, `crawl4ai_error_message`, `crawl4ai_attempts`, `crawl4ai_resolved_by`, `crawl4ai_fallback_fetch_used`, all `null` when no result was ever obtained) — recorded for later analysis only, never fed back into this module's own `outcome`/`garbage_type` verdict (crawl4ai's block detector has documented false positives). JSONL record also carries a `config`/`config_hash` stamp of the scrape config in effect for that call (see scrape_url.py's `extract_config_stamp`/`build_config_record`/`hash_config`) — adds ~450 bytes/record; deliberate given this is a slow-growing log (~160 records/2 weeks of real use), not a high-volume stream, and the whole point is comparing outcomes across config changes over weeks of accumulation.
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
- `extract_date`'s `original_date=True` prevents htmldate from preferring a last-modified date WHEN a real publication-date candidate exists, but on a page with NO such candidate (e.g. Sphinx-generated docs with a "Last updated on <date>" footer and no JSON-LD/meta tags) htmldate's extensive-mode cascade can still latch onto that footer text as its only signal — a real, observed false-positive-shaped result, not a bug in this wiring (the code never adds its own guess; it forwards htmldate's own found value, consistent with the library's documented ~90% accuracy). Reference/docs-style pages are a poor domain for this feature in general.
