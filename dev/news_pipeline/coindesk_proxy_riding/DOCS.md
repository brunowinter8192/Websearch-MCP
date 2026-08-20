# dev/news_pipeline/coindesk_proxy_riding/

## Role
Standalone dev suite for scraping CoinDesk article HTML at scale via rotating proxies. Architecture: B Playwright browser processes (pool, default B=1); N concurrent rider tasks (default 20) distributed round-robin across the B browsers (slot i → browsers[i % B]). Each task pulls raw proxies directly from the pool (no pre-validation). Each URL fetch uses `CrawlerRunConfig(proxy_config=ProxyConfig(server=...))` → fresh Playwright BrowserContext per proxy via crawl4ai's config-signature mechanism + `session_id` + `kill_session()` (fresh cookies per URL, browser stays alive). Regwall detection on `result.markdown.raw_markdown` (not raw HTML — REGWALL_SIGNALS are hidden React components always present in HTML). A proxy is burned and rotated when cumulative regwall hits reach the burn threshold. Self-contained: no imports from `src/` at module load (test modules import `src/news/engine/proxy_riding/` lazily, inside function bodies, for validating a ported production package).

## Modules

### p0_pool.py (221 LOC)

**Purpose:** Local copy of proxy pool machinery — loaders, cooldown manager, retry helper. Exports `load_backfill_pool()`, `PersistentCooldownManager`, `proxy_key()`, `fetch_with_retry()`.
**Reads:** proxy source lists (via loaders).
**Writes:** none (pure helpers).
**Called by:** `run_coindesk_riding.py`, `p2_browser_rider.py`.
**Gotcha:** local copy, not an import from `src/` — hookify blocks `from src.` imports in dev/ scripts.

### p2_browser_rider.py (498 LOC)

**Purpose:** Core riding pool — B `AsyncWebCrawler` instances (browser pool, default B=1); N rider tasks distributed round-robin across browsers. Each task pulls raw proxies via `_next_proxy()` (atomic cursor over `eligible_candidates()`). Per-URL: `CrawlerRunConfig(proxy_config=ProxyConfig(server=pstr))` → fresh context per config-signature; `kill_session()` closes context after each fetch (fresh cookies). `page_timeout_ms` (CLI-configurable, default 8s) is the dead-proxy timeout lever. Status routing: ok → write HTML; regwall → requeue URL, increment burn_count, rotate after `burn_threshold` hits; connect_fail → requeue URL, rotate proxy immediately; failed/empty → requeue URL, increment fail_count, rotate after `FAIL_THRESHOLD=2` hits (2-strike drop) — ride ends, `finally` calls `mark_burned()` → 60-min cooldown. Watchdog (`_watchdog`, asyncio task, cancelled on normal slot return) polls via `asyncio.sleep(min(30, stall_timeout_s/4))`; on stall (default 3600s, configurable) with no new raw written → `_abort_stall`: drain queue + in-flight URLs → `remaining_urls.txt` + `job.md` via reporter → `os._exit(1)` (bypasses async teardown so wedged Chrome processes cannot re-hang shutdown). `RiderState.in_flight_urls` — set tracking currently-fetching URLs, deliberately NOT in try/finally (wedged slots never reach discard, keeping wedged URL visible until abort — diagnostic capture).
**Reads:** proxy pool (via `p0_pool`), URL queue.
**Writes:** `raw/<12-char-sha256-hash>.html` per ok URL; on stall, `remaining_urls.txt`.
**Called by:** `run_coindesk_riding.py`, `smoke_stage1.py`.
**Exports:** `run_riding_pool(n_browsers=1, stall_timeout_s=3600)`, `RiderState`, `RideRecord`, `JobRecord`, `FAIL_THRESHOLD`, `_watchdog`, `_abort_stall`.

### p3_url_sampler.py (136 LOC)

**Purpose:** Proportional 500-URL sampler from CoinDesk inventory shards (2017-2026); floor 5 URLs/year. Resolves `data/news/coindesk/inventory/` from main repo root via `git rev-parse --git-common-dir` (works inside worktrees).
**Reads:** `data/news/coindesk/inventory/` shards.
**Writes:** returns sampled URL list (in-memory).
**Called by:** `run_coindesk_riding.py`.
**Exports:** `sample_urls(n_total, seed)`.

### p4_reporter.py (344 LOC)

**Purpose:** Generates `job.md` + 3 plots from a completed `RiderState`. Metrics: counts/throughput/61k-backfill projection; HTML size percentiles (`char_count = len(result.html)`); markdown length percentiles (`markdown_len` — body-level truncation signal); proxy churn + 61k estimate; ride-length distribution; regwall-position curve; retry outcomes; wasted-fetch ratio. Counts table includes `Browsers` and `Contexts/browser` (`n_slots // n_browsers`) for self-documenting runs.
**Reads:** `RiderState`.
**Writes:** `job.md`, `cumulative.png`, `ride_lengths.png`, `regwall_position.png`.
**Called by:** `run_coindesk_riding.py`, `p2_browser_rider.py` (on abort).
**Exports:** `write_riding_report(state, job_dir, t_job_start)`.

### run_coindesk_riding.py (115 LOC)

**Purpose:** CLI orchestrator — loads pool via `load_backfill_pool()`, wires `run_riding_pool` + `write_riding_report` end-to-end; raises `RLIMIT_NOFILE` at startup.
**Reads:** CLI args (`--n-urls` default 500, `--concurrency` default 20, `--burn-threshold` default 2, `--output-dir` default `output`, `--page-timeout` default 8000, `--browsers` default 1, `--stall-timeout` default 3600).
**Writes:** `<output-dir>/raw/*.html`, `<output-dir>/job.md`, `<output-dir>/cumulative.png`, `<output-dir>/ride_lengths.png`, `<output-dir>/regwall_position.png`.
**Called by:** CLI only. Entry point `__main__` via `asyncio.run(_run(_parse_args()))`. `./venv/bin/python dev/news_pipeline/coindesk_proxy_riding/run_coindesk_riding.py --n-urls 500 --concurrency 20 --burn-threshold 2 --output-dir data/news/coindesk/riding_output`.

### analyze_write_times.py (258 LOC)

**Purpose:** Reconstructs proxy-riding throughput from `raw/*.html` file mtimes. Used when `job.md`/`cumulative.png` are missing (manual abort before fix, or any crash that skips the report write). Reads mtime of every `.html` in `--raw-dir`, optionally filters to a `--since` cutoff (needed when `raw/` is a cumulative dedup corpus spanning multiple runs), plots cumulative OK fetches over time (top) and per-bin rate + rolling mean + 30-min pool-refresh markers (bottom).
**Reads:** `--raw-dir` (default `data/news/coindesk/raw`, resolved from repo root via `git rev-parse --git-common-dir`).
**Writes:** `png/raw_write_times_<YYYYMMDD>[_since<stamp>].png`. Stdout: filter summary, files, span, mean/median rate, longest gap.
**Called by:** CLI only. `--bin-minutes` (default 1), `--rolling` (default 5), `--since 'YYYY-MM-DD HH:MM'`.

### test_cooldown_policy.py (251 LOC)

**Purpose:** Deterministic tests for `RidingCooldownManager` (both `fixed` and `exp` policies). No browser or proxy infrastructure needed. `src/` imports lazy (worktree-root `sys.path` insert). 8 tests: fixed 60min eligibility boundary, fixed-default equivalence, exp unproductive-burn backoff bounds, exp cap at 3600s, exp reset on productive ride, exp eligible-after-backoff, exp `cooldown_count()` gate (A/B correctness gate for watchdog pool_samples), fixed `cooldown_count()` mirror check.
**Reads:** none (in-memory state construction).
**Writes:** stdout PASS/FAIL, exit code.
**Called by:** CLI only. `./venv/bin/python dev/news_pipeline/coindesk_proxy_riding/test_cooldown_policy.py`.

### smoke_stage1.py (254 LOC)

**Purpose:** Stage 1 smoke — validates `src/news/engine/proxy_riding/` package (`rider.py`/`state.py`/
`fetch.py`/`abort.py`/`reporter.py`/`scrape.py` — package split into these modules 2026-08-20; import
lines here point at each symbol's owning module, e.g. `RiderState`/`FAIL_THRESHOLD` from `state.py`,
`_abort_stall` from `abort.py`, `run_riding_pool`/`_watchdog` still from `rider.py`). Three sections:
import check (no network — also greps `abort.py`'s source for the late-import-of-reporter pattern,
not `rider.py`'s); deterministic watchdog test (patches `os._exit`, no network/browser — pre-existing
stale `RiderState` construction, fails independent of the module split); mini live run (10 inventory
URLs, 2 slots, 1 browser, 300s stall — validates manifest shape, shuffle, raw `.html` writes).
**Reads:** `src/news/engine/proxy_riding/` package (import validation); 10 inventory URLs (live run).
**Writes:** live-run raw `.html` files to a temp dir.
**Called by:** CLI only, run from main checkout: `./venv/bin/python .claude/worktrees/<worktree>/dev/news_pipeline/coindesk_proxy_riding/smoke_stage1.py`.

### test_sigint_report.py (213 LOC)

**Purpose:** Deterministic SIGINT/SIGTERM report tests for `src/news/engine/proxy_riding/abort.py`'s
`_abort_interrupted` (`RiderState`/`JobRecord`/`RideRecord` from `state.py`). No browser or proxy
infrastructure needed; `src/` imports lazy (inside function bodies). Test 1 — `_abort_interrupted`
SIGINT: constructs `RiderState` with partial job data, patches `os._exit` to raise `SystemExit`,
calls `_abort_interrupted` directly, asserts exit code 130, `job.md` + `cumulative.png` written,
`termination=interrupted`. Test 2 — same with SIGTERM → exit code 143.
**Reads:** none (constructed state).
**Writes:** `job.md`, `cumulative.png` to a temp dir (assertion targets).
**Called by:** CLI only. `./venv/bin/python dev/news_pipeline/coindesk_proxy_riding/test_sigint_report.py`.

### test_tail_race.py (445 LOC)

**Purpose:** Deterministic tail-race tests for `src/news/engine/proxy_riding/rider.py`'s `_run_slot`/
`_watchdog` (`RiderState`/`RAW_SUBDIR` from `state.py`). No browser or proxy infrastructure needed —
`_fetch_one_url` and `_next_proxy` mocked via `unittest.mock.patch.object(rider_mod, ...)`, which
only works because both stay defined in `rider.py` (attribute-patching resolves through the
*defining* module's globals, not the importing module's) — see the `refactor_sweep` area for the
finding that shaped the 2026-08-20 module split. `src/` imports lazy. 5 cases: surplus-slots race (2 URLs, 6 slots → both done, no double-write); write-exactly-once (1 URL, 3 racing slots → exactly 1 raw file); no-spurious-requeue (stale dequeue → no fetch; raced-fail → not re-queued); normal path (4 URLs, 4 slots, no racing); fail-before-success (fails first fetch, re-queued, succeeds second → done exactly once).
**Reads:** none (mocked fetch/proxy).
**Writes:** none beyond test assertions.
**Called by:** CLI only. `./venv/bin/python dev/news_pipeline/coindesk_proxy_riding/test_tail_race.py`.

### test_watchdog.py (159 LOC)

**Purpose:** Deterministic watchdog verification — no browser or proxy infrastructure needed. `test_watchdog_task_fires_and_writes_files`: constructs `RiderState` with `last_progress_mono` aged 200s past a 1s threshold + 2 queued + 1 in-flight URL; patches `os._exit` → `SystemExit(code)`; runs `_watchdog(poll_interval=0.1)`; asserts `os._exit(1)` called, `remaining_urls.txt` has both section headers + all 3 URLs, `job.md` exists with `stall`. `test_abort_stall_directly`: same assertions via direct `_abort_stall(idle_s=999.0)` call; also checks `"999"` in the header line.
**Reads:** none (constructed state).
**Writes:** `remaining_urls.txt`, `job.md` to a temp dir (assertion targets).
**Called by:** CLI only. `./venv/bin/python dev/news_pipeline/coindesk_proxy_riding/test_watchdog.py`.

## State
`raw/` — one HTML per ok URL fetched (output-dir scoped, not committed). `png/` — historical throughput reconstruction plots (tracked).

## Gotchas
`--page-timeout` (default 8000ms) is the dead-proxy timeout lever — dead proxies hit this before rotating. Regwall detection reads `result.markdown.raw_markdown`, not raw HTML (REGWALL_SIGNALS are hidden React components always present in HTML, so raw-HTML matching would false-positive on every page).
