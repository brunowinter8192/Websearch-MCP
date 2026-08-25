# src/crawler/

## Role

Full-site BFS discovery + capture-pipeline scrape step for offline documentation indexing (the capture-and-index workflow). Two standalone entry modules — neither is a `cli.py` subcommand. Touch this package to change discovery (BFS/link-following) or the raw batch-scrape step; single-URL in-chat scraping lives in `src/scraper/`.

## Public Interface

`__init__.py` is empty. Both entry modules run as `python -m src.crawler.<module>` and expose importable entry functions:

- `scrape_urls_workflow(urls, output_dir, download_delay, concurrency_per_domain=None, engine="chromium", block_images=False)` (pipe_scraper.py) — batch raw-markdown scrape of a URL list. `engine` is a per-RUN choice ("chromium" default/unchanged behavior, or "camoufox" — a deliberate second lane, never auto-selected); `concurrency_per_domain=None` resolves to the ENGINE'S OWN default.
- `crawl_site_workflow(...)` (crawl_site.py) — discover (BFS) then crawl a seed domain.
- `discover_urls_playwright(...)`, `crawl_urls(...)`, `normalize_url(...)` (crawl_site.py).
- `log_pipe_scrape(record)` (pipe_scrape_logger.py) — called by pipe_scraper.py.

## Flow

pipe_scraper: URL list in → per-domain paced raw crawl → one `.md` per URL + a `/tmp` outcome report + a persistent per-URL JSONL log record (run/config-stamped). crawl_site: seed URL → Playwright BFS discovery (`discover_urls_playwright`) → parallel content crawl (`crawl_urls`) → markdown files, each with a `<!-- source: URL -->` header.

## Modules

### crawl_site.py (359 LOC)

**Purpose:** Discovery engine + content crawl — Playwright-per-page BFS from a seed URL (`discover_urls_playwright`) followed by a parallel content crawl (`crawl_urls`) writing one markdown file per URL.
**Reads:** seed URL / `--url-file` list.
**Writes:** per-URL `.md` to `--output-dir` (each with source header).
**Called by:** `crawl_site_workflow` (CLI entry); capture-and-index workflow.
**Calls out:** `crawl4ai` (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, UndetectedAdapter, AsyncPlaywrightCrawlerStrategy, DefaultMarkdownGenerator, SemaphoreDispatcher); `src.scraper.chromium_scrape.is_garbage_content`.

### pipe_scraper.py (114 LOC) — entry point

**Purpose:** Entry point + orchestrator for the capture-pipeline scrape step — dispatches a URL list per-RUN (never per-URL, never auto-selected) to one of two acquisition engines (chromium: shared crawler; camoufox: fresh browser per URL).
**Reads:** URL list from `--url-file` or caller-supplied list.
**Writes:** delegates all actual writing to sibling modules (see below); prints the console summary and writes the `/tmp` report itself via `pipe_scraper_report.py`.
**Called by:** capture-and-index skill Scrape step; importable as `scrape_urls_workflow()`.
**Calls out:** `crawl4ai` (AsyncWebCrawler); `src.scraper.chromium_scrape` (hash_config); `pipe_scraper_constants.py`, `pipe_scraper_config.py`, `pipe_scraper_acquisition.py`, `pipe_scraper_report.py` (all below).

### pipe_scraper_constants.py (9 LOC)

**Purpose:** Pacing/timeout/threshold constants shared by 3+ of pipe_scraper's sibling modules — full sourced rationale lives in this file's own Gotchas entries below, not restated per-constant.
**Called by:** `pipe_scraper.py`, `pipe_scraper_config.py`, `pipe_scraper_acquisition.py`.
**Calls out:** none.

### pipe_scraper_pacing.py (26 LOC)

**Purpose:** Per-domain Scrapy-style pacing gate (`_ensure_domain_state`, `_gate_domain`) — delay-gate + jitter + concurrency cap, engine-agnostic (used by both chromium and camoufox executors).
**Called by:** `pipe_scraper_acquisition.py`.
**Calls out:** none (stdlib only).

### pipe_scraper_config.py (56 LOC)

**Purpose:** `_build_configs()` sets a fixed anti-bot posture for the chromium engine, optimized purely for reachability, not extraction quality (stealth + `magic=False` + `remove_consent_popups=True`); wires the curl_cffi fallback (path a) into `CrawlerRunConfig.fallback_fetch_function`.
**Called by:** `pipe_scraper.py` (`_scrape_all`).
**Calls out:** `crawl4ai` (BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator); `pipe_scraper_acquisition.py` (`_fallback_fetch`); `pipe_scraper_constants.py`.

### pipe_scraper_acquisition.py (172 LOC)

**Purpose:** Per-URL engine executors for both acquisition engines (`_scrape_one` chromium, `_scrape_one_camoufox` camoufox) plus the chromium engine's two independent curl_cffi fallback paths for when the browser is the weaker client.
**Reads:** URL list passed in from `pipe_scraper._scrape_all`.
**Writes:** per-URL `.md` to `--output-dir` (with source header, including path-(b)-rescued content, or camoufox-engine content — markdown OR raw HTML, see `content_is_raw_html`); one JSONL record per URL via `pipe_scraper_records.py`.
**Called by:** `pipe_scraper.py` (`_scrape_all`).
**Calls out:** `crawl4ai` (AsyncWebCrawler, CrawlerRunConfig); `curl_cffi.requests` (AsyncSession); `src.scraper.chromium_scrape` (extract_crawl4ai_diagnosis); `src.scraper.camoufox_scrape` (try_scrape_camoufox); `pipe_scraper_pacing.py`; `pipe_scraper_records.py`; `pipe_scraper_constants.py`.

### pipe_scraper_records.py (41 LOC)

**Purpose:** Assembles and writes one JSONL record per URL via `pipe_scrape_logger.log_pipe_scrape` — a chromium-engine function and a sibling camoufox-engine function, kept separate since the fallback fields are chromium-lane-only.
**Called by:** `pipe_scraper_acquisition.py` (`_scrape_one`, `_scrape_one_camoufox`).
**Calls out:** `src.crawler.pipe_scrape_logger` (log_pipe_scrape).

### pipe_scraper_report.py (36 LOC)

**Purpose:** `/tmp/<domain>_scrape_report.md` per-URL outcome table + one-line console summary, both consumed only by `scrape_urls_workflow` at the end of a run.
**Called by:** `pipe_scraper.py` (`scrape_urls_workflow`).
**Calls out:** none (stdlib only).

### pipe_scrape_logger.py (27 LOC)

**Purpose:** Per-URL JSONL log writer for pipe_scraper — one record per URL (`run_id`-grouped, `ts`=request start), shared by both acquisition engines (`"engine"` field discriminates), separate schema/file from `src/logs/scrape_log.jsonl`.
**Reads:** `WEBSEARCH_PIPE_SCRAPE_LOG_PATH` env var (fallback `src/logs/pipe_scrape_log.jsonl`).
**Writes:** `src/logs/pipe_scrape_log.jsonl` (one line per URL). Gitignored.
**Called by:** `pipe_scraper_records.py` (`_log_pipe_record` for the chromium engine, `_log_pipe_camoufox_record` for the camoufox engine).
**Calls out:** `src/log_janitor.py` (maybe_prune_jsonl).

## Gotchas

- pipe_scraper pacing is a Scrapy per-domain gate: `lastseen` dict + `asyncio.Lock` (serializes starts) + `asyncio.Semaphore(8)` cap, `DOWNLOAD_DELAY=1.0s`, jitter `uniform(0.5×,1.5×)` → ~1 req/s per domain. No batch loop, no inter-batch sleep, no retry/backoff.
- crawl_site discovery `--concurrency` > 1 risks WAF 429s (recommended max 10); BFS 429 policy is back-off-once-then-stop, surfaced as `stop_reason="429_persistent"`.
- pipe_scraper's per-URL `ts` MUST be stamped after `_gate_domain`, not before the domain semaphore — `asyncio.gather` starts every `_scrape_one` coroutine at once, so a pre-gate `ts` collapses to one near-identical value across an entire run's records regardless of real pacing (a real bug, caught and fixed; regression-guarded by `dev/tests/test_pipe_scraper.py::test_scrape_one_ts_reflects_request_start_not_queue_time`).
- pipe_scraper's `_build_configs()` (`pipe_scraper_config.py`) anti-bot posture is ONE fixed calibration derived from external sources (crawl4ai/playwright-stealth source + issue trackers), not a set of tunable knobs — do not add CLI flags for it, do not tune it against sampled domains (a sweep's result holds for the domains sampled, not the next unknown one; `src/logs/pipe_scrape_log.jsonl` is where real weak spots surface over time). `magic=False` in particular is a deliberate rejection, not an unset default — see the `pipe_scraper_hardening` area for the full reasoning before turning it on.
- `_build_configs()`'s `enable_stealth=True` reachability depends on pipe_scraper passing NO custom `crawler_strategy`/adapter to `AsyncWebCrawler` — crawl4ai's `browser_manager.py` only builds the `StealthAdapter` when `enable_stealth and not use_undetected`, and `use_undetected` resolves from `isinstance(self.adapter, UndetectedAdapter)`. If this module ever starts passing a custom adapter, re-verify `use_undetected` still resolves False (`dev/tests/test_pipe_scraper.py::test_build_configs_produces_live_stealth_adapter` is the wiring test to re-run).
- `pipe_scraper.py`'s `--block-images`/`--no-block-images` share `dest='block_images'` — argparse resolves a shared dest's default from the FIRST `add_argument` call added that lacks a namespace value yet, so `--block-images`'s own `default=False` (not `--no-block-images`'s) governs omission. Do not reorder the two `add_argument` calls without re-verifying which default wins.
- `_build_configs()` takes no parameters on purpose — the browser/run config does not depend on `download_delay`/`concurrency_per_domain`. Only `_extract_pipe_config_stamp` needs those (to log the pacing values actually in effect). Do not thread pacing params back into `_build_configs()`'s signature — that was tried and reverted (signature asserted a dependency that did not exist).
- `max_retries` stays at 0 (crawl4ai's library default, never set by this module) — DELIBERATELY, not an oversight. Raising it would let crawl4ai's own fallback_fetch_function (path a) also reach the browser-exception case, but at the cost of a full second browser attempt (~2×`page_timeout`, unconditionally) before that rescue is even considered — same failed attempt, same config, same IP, same target, on the bet the retry differs from the first. Do not raise it to "fix" path (b)'s existence; path (b) exists specifically because raising `max_retries` was rejected on that cost analysis.
- A crawl4ai-own-fallback (path a) success ALWAYS logs `http_status=200` — crawl4ai hardcodes this on any non-empty `fallback_fetch_function` return, regardless of what actually happened. It is NOT distinguishable from a real browser 200 by `http_status` alone; `crawl4ai_resolved_by == "fallback_fetch"` is the only honest discriminator. `pipe_scraper`'s own path (b) does not repeat this: its `http_status=200` is only ever set when `pipe_fallback_resolved` is True, i.e. curl_cffi itself genuinely returned 200 — see `_own_fallback_rescue`.
- **`landed_url` is `null` on path (a) specifically (`crawl4ai_fallback_fetch_used=True`) — never trust `result.redirected_url` on that route.** Verified in crawl4ai 0.9.2 source: path (a) hardcodes `redirected_url=url` (the requested URL, not what curl_cffi actually followed), and `_fallback_fetch`'s str-only return contract (crawl4ai calls it directly and consumes the return value as HTML text) leaves no channel to carry the real value out. Path (b) (`pipe_fallback_used=True`) is DIFFERENT and DOES carry a real `landed_url`: `_own_fallback_rescue` calls `_curl_cffi_get` directly (not through crawl4ai) and reads curl_cffi's own `response.url` (libcurl's `EFFECTIVE_URL` — confirmed live, this venv, curl_cffi 0.16.0: a request to `rfc-editor.org/rfc/rfc2616` returns `response.url=rfc-editor.org/info/rfc2616/`).
- **No `same_target` verdict exists in this module anymore, and none is stored in the log.** `is_same_target` (`src/scraper/chromium_scrape.py`) and the `same_target` field it fed both existed for a period and were REMOVED — a deliberate reversal after review, not a partial rollback (see `src/scraper/DOCS.md`'s own Gotcha on the same reversal for the full reasoning: the log is read only by an agent, after the fact, with `url`/`landed_url`/`crawl4ai_fallback_fetch_used`/`pipe_fallback_used` already in the same record — everything needed to derive a verdict is already there, so storing one too was a re-derivable conclusion kept as data). The comparison rule moved to the calling agent (`skills/websearch-web-research/SKILL.md`, updated separately outside this module) rather than disappearing. Do not reintroduce `is_same_target`/`same_target` here on the assumption it was simply forgotten.
- **`CAMOUFOX_CONCURRENCY_PER_DOMAIN=1` is NOT the same kind of number as `CONCURRENCY_PER_DOMAIN=8` — do not "fix" the apparent inconsistency by raising it to match.** The chromium default was measured/validated (`process-docs/pipe_scraper_hardening/2026-08-04_stealth_concurrency_probe.md`, 0 crashes at 8) for N requests sharing ONE already-launched browser. The camoufox engine launches a FRESH, real, headed Firefox process per in-flight request — concurrency=8 there would mean up to 8 simultaneous heavy processes per domain, unmeasured, against field evidence that Camoufox's memory footprint is already heavier per-instance than patchright/undetected-chromium. 1 is the conservative default absent evidence, not a final number — raise it only with the same kind of measurement that earned chromium's 8, never by assumption.
- **The pipe-engine log's `"config"` shape is NOT comparable across `"engine"` values, ever — a config_hash collision across engines means nothing.** Chromium's `config` is the FULL pacing/stealth surface, computed once for the whole run off the real shared browser objects; camoufox's own `config` (headless/os/block_images/timeout/executable_path/total_budget_s) is computed PER URL, off that call's own `try_scrape_camoufox` meta, and has no pacing/stealth keys at all (there is no shared browser to read them off). Grouping/comparing records by `config_hash` only makes sense WITHIN one `"engine"` value.
- **Open question, NOT investigated further — a real question about the EXISTING fallback design, not about the landed_url work itself.** Attempting to build a real (non-fake) trigger for path (b) during milestone-4 verification, a controlled local server was built to force Playwright's `net::ERR_ABORTED` (a download-triggering response, `accept_downloads=False` — this module's default). It fired exactly as the crawl4ai source predicts (`crawl4ai_error_message` in the real logged record confirms the exact `RuntimeError`), but crawl4ai's own `_crawl_web` wrapper — a layer neither the 2026-08-05 fallback-path work nor this milestone had previously inspected — caught it internally and returned a normal `success=False` `CrawlResult` rather than letting it propagate to `_scrape_one`'s own `except Exception:` block. Path (b) was therefore NOT reached by this trigger, even though the browser genuinely failed. This raises a real, open question about how often path (b) is reachable at all in this crawl4ai version — the earlier verification (`process-docs/pipe_scraper_hardening/2026-08-05_curl_cffi_fallback_acquisition_path.md`) used a DIFFERENT failure shape (a connection that never responds, forcing a timeout) to reach it, not this one. Not chased further here — left as a question for whoever next touches this fallback design to pick up.
