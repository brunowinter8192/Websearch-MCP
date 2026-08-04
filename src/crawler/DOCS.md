# src/crawler/

## Role

Full-site BFS discovery + capture-pipeline scrape step for offline documentation indexing (the capture-and-index workflow). Two standalone entry modules — neither is a `cli.py` subcommand. Touch this package to change discovery (BFS/link-following) or the raw batch-scrape step; single-URL in-chat scraping lives in `src/scraper/`.

## Public Interface

`__init__.py` is empty. Both entry modules run as `python -m src.crawler.<module>` and expose importable entry functions:

- `scrape_urls_workflow(...)` (pipe_scraper.py) — batch raw-markdown scrape of a URL list.
- `crawl_site_workflow(...)` (crawl_site.py) — discover (BFS) then crawl a seed domain.
- `discover_urls_playwright(...)`, `crawl_urls(...)`, `normalize_url(...)` (crawl_site.py).
- `log_pipe_scrape(record)` (pipe_scrape_logger.py) — called by pipe_scraper.py.

## Flow

pipe_scraper: URL list in → per-domain paced raw crawl → one `.md` per URL + a `/tmp` outcome report + a persistent per-URL JSONL log record (run/config-stamped). crawl_site: seed URL → Playwright BFS discovery (`discover_urls_playwright`) → parallel content crawl (`crawl_urls`) → markdown files, each with a `<!-- source: URL -->` header.

## Modules

### crawl_site.py (353 LOC)

**Purpose:** Discovery engine + content crawl. `discover_urls_playwright(seed, include/exclude_patterns, max_pages, max_depth, delay_s, page_timeout_ms, concurrency, stealth)` runs a manual Playwright-per-page BFS (`crawler.arun()` per URL, links from `result.links.internal` post-JS DOM), returning `(urls, meta)` with `stop_reason` ∈ {frontier_exhausted, max_pages_reached, 429_persistent}. `crawl_urls(urls)` does the parallel content crawl (`SemaphoreDispatcher(max_session_permit=10)`, `wait_until="networkidle"`). `normalize_url` strips query/fragment/@version/trailing-slash for visited-set dedup. CLI (`python -m src.crawler.crawl_site`): `--url` seed, `--output-dir`, `--depth` (3), `--max-pages` (100), `--include/exclude-patterns`, `--url-file` (skips discovery), `--delay` (3.0), `--page-timeout` (15000), `--concurrency` (1), `--stealth`.
**Reads:** seed URL / `--url-file` list.
**Writes:** per-URL `.md` to `--output-dir` (each with source header).
**Called by:** `crawl_site_workflow` (CLI entry); capture-and-index workflow.
**Calls out:** `crawl4ai` (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, UndetectedAdapter, AsyncPlaywrightCrawlerStrategy, DefaultMarkdownGenerator, SemaphoreDispatcher); `src.scraper.scrape_url.is_garbage_content`.

### pipe_scraper.py (316 LOC)

**Purpose:** Validated capture-pipeline scrape step. Crawls a URL list to raw markdown with Scrapy-style per-domain pacing (delay-gate + jitter + concurrency cap). CLI (`python -m src.crawler.pipe_scraper`): `--url-file` + `--output-dir` (both required), `--download-delay` (1.0), `--concurrency-per-domain` (8). `_build_configs()` (no params — the browser/run config does NOT depend on pacing values, only `_extract_pipe_config_stamp` does) sets a fixed anti-bot posture, optimized purely for reachability (not extraction quality — no content filter/`preserve_tags`, that's the Phase-3 LLM's job per the capture skill): `enable_stealth=True` (StealthAdapter, verified live against crawl4ai 0.9.2 + playwright-stealth 2.0.3, reachable because this module passes no custom adapter so `use_undetected` resolves False), `simulate_user=True` + `override_navigator=True` (mouse/scroll + navigator-override, taken individually), `magic=False` EXPLICITLY (magic would ALSO randomize the user-agent via `ValidUAGenerator` — 8 different UAs from one IP at `CONCURRENCY_PER_DOMAIN=8`, plus a UA/Chromium-version mismatch signal — rejected, not an oversight), `remove_consent_popups=True` (an un-dismissed consent wall is a LOST page here, since the capture skill deletes confirmed block pages rather than cleaning them — a reachability problem, not the quality-tuning role the same switch plays in `scrape_url.py`). `UndetectedAdapter` is NOT used (crawl4ai issue #1500: crashes above concurrency 1, incompatible with `CONCURRENCY_PER_DOMAIN=8`). Full sourced rationale for every value is in `_build_configs`'s own comments. Every URL result is also logged to a persistent JSONL log via `pipe_scrape_logger.log_pipe_scrape` — one `run_id` (uuid4) shared by every record of one `scrape_urls_workflow` invocation, plus a `config`/`config_hash` stamp read off the actual constructed `BrowserConfig`/`CrawlerRunConfig` objects and this module's own pacing constants (`_extract_pipe_config_stamp`, computed once per run in `_scrape_all`, not re-derived per URL). Reuses `hash_config`/`extract_crawl4ai_diagnosis` from `src/scraper/scrape_url.py` rather than re-implementing them (same algorithm, generic).
**Reads:** URL list from `--url-file` or caller-supplied list.
**Writes:** per-URL `.md` to `--output-dir` (with source header); `/tmp/<domain>_scrape_report.md` (per-URL outcome table); summary line to stdout; one JSONL record per URL via `log_pipe_scrape` (fail-soft, never breaks the scrape run).
**Called by:** capture-and-index skill Phase 2; importable as `scrape_urls_workflow()`.
**Calls out:** `crawl4ai` (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, DefaultMarkdownGenerator); `src.scraper.scrape_url` (hash_config, extract_crawl4ai_diagnosis); `src.crawler.pipe_scrape_logger` (log_pipe_scrape).

### pipe_scrape_logger.py (84 LOC)

**Purpose:** Per-URL JSONL log writer for pipe_scraper — separate file/schema from `src/scraper/scrape_log.jsonl` (the ad-hoc single-URL path): has `run_id`/`domain`, no sidecar/`content_path`/`mode` (pipe_scraper already writes every page's raw markdown to `--output-dir`; that IS the content record). `config` now also carries `simulate_user`/`override_navigator`/`magic`/`remove_consent_popups` (the anti-bot posture fields) alongside the original stealth/pacing fields. `config_hash` groups records that ran under the same config but is explicitly NOT a stable identity across schema versions — it changes whenever any stamped value changes, including a field being added to/removed from the stamp itself. `crawl4ai_fallback_fetch_used` is kept in the schema even though it reads `None`/`False` on every record today (no fallback fetch path exists yet, a later milestone) — deliberate, so pre- and post-fallback-path records stay structurally comparable.
**Reads:** `WEBSEARCH_PIPE_SCRAPE_LOG_PATH` env var (fallback `src/logs/pipe_scrape_log.jsonl`).
**Writes:** `src/logs/pipe_scrape_log.jsonl` (one line per URL). Gitignored.
**Called by:** `pipe_scraper.py` (`_log_pipe_record`).
**Calls out:** `src/log_janitor.py` (maybe_prune_jsonl).

## Gotchas

- pipe_scraper pacing is a Scrapy per-domain gate: `lastseen` dict + `asyncio.Lock` (serializes starts) + `asyncio.Semaphore(8)` cap, `DOWNLOAD_DELAY=1.0s`, jitter `uniform(0.5×,1.5×)` → ~1 req/s per domain. No batch loop, no inter-batch sleep, no retry/backoff.
- crawl_site discovery `--concurrency` > 1 risks WAF 429s (recommended max 10); BFS 429 policy is back-off-once-then-stop, surfaced as `stop_reason="429_persistent"`.
- pipe_scraper's per-URL `ts` MUST be stamped after `_gate_domain`, not before the domain semaphore — `asyncio.gather` starts every `_scrape_one` coroutine at once, so a pre-gate `ts` collapses to one near-identical value across an entire run's records regardless of real pacing (a real bug, caught and fixed; regression-guarded by `tests/test_pipe_scraper.py::test_scrape_one_ts_reflects_request_start_not_queue_time`).
- pipe_scraper's `_build_configs()` anti-bot posture is ONE fixed calibration derived from external sources (crawl4ai/playwright-stealth source + issue trackers), not a set of tunable knobs — do not add CLI flags for it, do not tune it against sampled domains (a sweep's result holds for the domains sampled, not the next unknown one; `src/logs/pipe_scrape_log.jsonl` is where real weak spots surface over time). `magic=False` in particular is a deliberate rejection, not an unset default — see the module's own comment before turning it on.
- `_build_configs()` takes no parameters on purpose — the browser/run config does not depend on `download_delay`/`concurrency_per_domain`. Only `_extract_pipe_config_stamp` needs those (to log the pacing values actually in effect). Do not thread pacing params back into `_build_configs()`'s signature — that was tried and reverted (signature asserted a dependency that did not exist).
