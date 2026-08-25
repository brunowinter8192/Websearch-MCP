# dev/tests/

## Role
The project's pytest suite. Regression coverage for `src/search/`, `src/scraper/`, `src/crawler/`,
`src/news/engine/proxy_pool/`, and `src/news/platforms/theblock/` — pure-logic branch coverage,
library-upgrade guards (live calls into installed `crawl4ai`), and production-failure regression
repros. No network/browser dependency: I/O boundaries (HTTP clients, browser automation,
subprocess) are mocked per-test; production logic itself is exercised for real. Touch this
directory when adding/removing test coverage for the modules above; do not touch when only
production behavior changes without an assertion needing to change.

## Public Interface
`__init__.py` is empty — collected via `pytest` from the repo root (`pytest.ini`: `testpaths =
dev/tests`, `pythonpath = .`). No importable package surface.

## Flow
Synthetic/captured-sample inputs (JSON items, HTML fixtures, monkeypatched clients) → real
production function/class under test → assert on real output (parsed results, rendered
markdown/job.md, JSONL records, classification verdicts). `tmp_path`/`monkeypatch` isolate
filesystem and environment per test; no test writes outside `tmp_path` or reads the real
production log paths.

## Modules

### test_bing_engine.py (91 LOC)
**Purpose:** `src/search/engines/bing.py` — `_clean_url` (ck/a redirect unwrap, real captured
sample), `_build_results`, `_classify_diagnosis`.
**Calls out:** none (pure function tests, one `monkeypatch` on `base64.urlsafe_b64decode`).

### test_brave_engine.py (61 LOC)
**Purpose:** `src/search/engines/brave.py` — `_build_results`, `_classify_diagnosis` (PoW/CAPTCHA).

### test_startpage_engine.py (61 LOC)
**Purpose:** `src/search/engines/startpage.py` — `_build_results`, `_classify_diagnosis` (iframe
challenge).

### test_yandex_engine.py (106 LOC)
**Purpose:** `src/search/engines/yandex.py` — `_is_self_referential`, `_is_block_url`,
`_build_results` (self-link filtering), `_classify_diagnosis`.

### test_marginalia_engine.py (106 LOC)
**Purpose:** `src/search/engines/marginalia.py` — `_parse_results`; `_fetch_results`/
`MarginaliaEngine.search` 429/403 → empty, `httpx.AsyncClient` faked.

### test_browser_lock.py (91 LOC)
**Purpose:** `src/search/browser_lock.py` — real-flock behavior against `tmp_path` (no mocking):
immediate acquire when free, genuine blocking until a background thread's `release()`, and the
stale-takeover path (a real held flock + a backdated sidecar triggers `on_stale` then reacquires).

### test_browser.py (247 LOC)
**Purpose:** `src/search/browser.py` — `_reap_session_profile`/`_record_own_pids`/
`_terminate_then_kill` pgrep-output parsing and psutil dispatch (subprocess+psutil mocked);
`get_tab()`'s critical-section ordering (lock -> reap -> launch -> record-own-pids, the exact
sequence the browser-lifecycle milestone's live parallel-run bug depended on getting right);
`kill_own_chrome()`'s full teardown sequence, its no-op path when the browser was never touched,
and the PID-safety-net-and-lock-release-still-run path when `close_browser()` itself raises
(Chrome already dead mid-sweep).

### test_query_logger.py (319 LOC)
**Purpose:** `src/search/query_logger.py` (`log_query` fail-soft JSONL write) + per-engine timing
capture in `src/search/search_web.py` (`_engine_with_timing`, `search_web_workflow` log shape,
`search_key` matches real `cache.cache_key`) + `cli.py:_log_drilldown` via an isolated subprocess.
**Gotchas:** the subprocess test resolves repo root as `Path(__file__).parent.parent.parent`
(three levels — `dev/tests/<file>` → `dev/tests` → `dev` → repo root); this depth was silently
wrong (`.parent.parent`) for one relocation cycle when the file lived at `tests/` before the
milestone-2 move to `dev/tests/` and must be re-checked on any future relocation.

### test_dedup_exclude.py (132 LOC)
**Purpose:** `src/news/engine/dedup.py:filter_new_entries` — `exclude_urls` param precedence over
raw-file-exists skip, mixed-entry counts, `None`/empty-set backward compat.

### test_theblock_clean_pass.py (138 LOC)
**Purpose:** `src/news/clean_pass.py:_run_clean_pass` — good-article clean-file write, bodyless
URL recording/union-merge, raw-file read-only invariant, stats.

### test_theblock_discover.py (169 LOC)
**Purpose:** `src/news/platforms/theblock/discover.py` — `_subs_in_range`, `_sub_by_index`,
`discover()`'s `sub:A-B` dispatch error paths (A>B, non-int, no match).

### test_proxy_pool.py (573 LOC)
**Purpose:** `src/news/engine/proxy_pool/` — `janitor.py` window stats + job.md rendering
(distinct-URL vs. total-attempt counters, pool-source breakdown section), `pool_retry.
fetch_with_retry` backoff/re-raise, `pool_loaders.load_backfill_pool` per-source isolation,
`logger.AcquireLogger`/`_group_pool_sources`, `loop.run_loop` refresh-boundary integration
(pool swap + wset state-continuity, confirmed production-correct not a test bug).

### test_camoufox_scrape.py (606 LOC)
**Purpose:** `src/scraper/camoufox_scrape.py` — `try_scrape_camoufox` acquisition-error states
(budget/browser_missing/exception), the "Invalid IPv6 URL" urlsplit regression, HTML-preserved-
on-markdown-conversion-failure, calibration surface (`_build_camoufox_kwargs`/
`_extract_camoufox_config_stamp`/config_hash stability), `scrape_url_camoufox_workflow` logging,
`_format_camoufox_output`, no-focus-steal launch (`_find_app_bundle`/`_ensure_no_focus_steal`,
real plistlib round-trip).

### test_chromium_scrape.py (736 LOC)
**Purpose:** `src/scraper/chromium_scrape.py` — `is_browser_launch_error`, `try_scrape` acquisition-
error classification + HTTP-error-with-real-content preservation, `_format_scrape_output`,
`extract_config_stamp`, cdp-headed self-launch teardown-on-every-exit-path, self-launch mechanics
(`_wait_for_devtools_port`/`_find_app_bundle`, real filesystem), live `crawl4ai.browser_manager.
ManagedBrowser.build_browser_flags` parity guard + `_build_self_launch_flags` GPU/window-size.

### test_pipe_scraper.py (952 LOC)
**Purpose:** `src/crawler/pipe_scraper*.py` — config stamp extraction off real
BrowserConfig/CrawlerRunConfig, live crawl4ai `AsyncPlaywrightCrawlerStrategy`/`StealthAdapter`
wiring guard, `pipe_scrape_logger.log_pipe_scrape` fail-soft JSONL, `_scrape_all` (run_id sharing,
request-start `ts` timing regression, config hash), `is_blocked` real branch distinction,
`pipe_scraper_acquisition._fallback_fetch`/`_own_fallback_rescue` (via the real `_scrape_one`
except path), `landed_url` correctness across all three engines/routes, camoufox-engine dispatch
switch (default/concurrency/block_images/record shape/error mapping).

## Gotchas
Any file under this directory that resolves its own path to locate the repo root (subprocess
`cwd`, `sys.path` injection) breaks silently on relocation — the depth is baked into `Path(
__file__).parent...` chains, not derived from a fixture. Grep for `Path(__file__).parent` before
moving this directory again.
