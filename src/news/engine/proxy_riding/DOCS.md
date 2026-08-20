# src/news/engine/proxy_riding/

## Role

Third scrape engine: browser + rotating proxies. Purpose: defeat CoinDesk's IP-rate regwall for the
61k article-body backfill. Each URL gets a fresh crawl4ai browser context bound to a distinct proxy;
the proxy is burned after `burn_threshold` regwall hits or `FAIL_THRESHOLD` (2) failed/empty strikes
and a new one is picked from the shuffled pool. A timer-based asyncio watchdog (`_watchdog`) runs
independently of the slot tasks and hard-aborts via `os._exit(1)` if no progress occurs for
`stall_timeout_s` seconds — immune to wedged Playwright I/O.

**Active as CoinDesk's `run_scrape_only` path.** `platform.scrape_engine == "proxy_riding"` dispatched
in `pipeline.py:run_scrape_only`; `RidingScrapeConfig` consumed via `getattr` (not in Protocol);
`filter_new_entries` raw_ext reconciliation done (`.html` for riding path).

Touch this package when changing proxy-riding engine behaviour. Do NOT touch `engine/scrape.py` or
`engine/proxy_pool/` — those engines are strictly independent.

## Public Interface

`__init__.py` is empty. Entry paths:

- `scrape_entries_riding(entries, output_dir, riding_cfg, job_dir)` in `scrape.py` — async; called by
  `pipeline.py:run_scrape_only`. Returns `tuple[list[dict], RiderState]`: manifest
  `[{url, hash, status, file, char_count, error}]` + full rider state (for `write_riding_report`).
  `job_dir` is threaded to the watchdog so stall-abort writes land in `scrape_jobs/{job_id}/` (same as
  normal completion), not the platform root.
- `RidingScrapeConfig` in `scrape.py` — dataclass with production defaults
  (`n_browsers=4, n_slots=64, stall_timeout_s=300.0, burn_threshold=2, page_timeout_ms=8_000`).
- `write_riding_report(state, job_dir, t_job_start)` in `reporter.py` — called by
  `pipeline.py:run_scrape_only` (normal completion) and by `abort.py`'s `_abort_stall` / `_abort_done` /
  `_abort_interrupted` (late import, abort paths).
- `run_riding_pool(url_queue, proxy_pool, cooldown_mgr, output_dir, job_dir, target_urls, …)` in
  `rider.py` — async; called by `scrape_entries_riding`. Stable entry point — this import path does
  not change even as the package's internals are split across modules.
- `RiderState`, `RideRecord`, `JobRecord`, `FAIL_THRESHOLD`, `RAW_SUBDIR` defined in `state.py`;
  re-imported (not re-defined) into `rider.py` so `rider.RiderState` etc. still resolve for existing
  callers.

## Flow

1. `scrape_entries_riding` builds URL queue from entries, loads pool via `load_backfill_pool()`,
   filters to `{"http","socks5"}`, shuffles, constructs `RidingCooldownManager(policy=riding_cfg.cooldown_policy)`.
2. `run_riding_pool` spawns B `AsyncWebCrawler` instances + N slot tasks + 1 watchdog task.
3. Each slot draws a proxy from the shuffled pool (cursor-atomic under `proxy_lock`), rides URLs
   until burn_threshold regwall or FAIL_THRESHOLD failed/empty, then rotates to the next proxy.
   **Tail-race:** when `url_queue` is empty (unresolved URLs < n_slots), slots immediately race an
   open URL (`sorted(target_urls − done_urls)[slot_id % len]`) with their current proxy — no 10 s
   wait. `asyncio.QueueEmpty` → race path; `asyncio.Queue.get_nowait()` replaces `wait_for(…, 10s)`.
4. Ok fetches write `raw/{hash}.html` guarded by first-writer check (`done_urls`); dup-race arrivals
   are discarded without write or n_ok increment. State accumulates `job_records` + `ride_records`.
5. Termination: `all_resolved = len(done_urls) >= len(target_urls)` (not queue-empty + in_flight==0).
   `state.termination` transitions from `"running"` → one of `"all-done"` | `"stall"` |
   `"pool-exhausted"` | `"interrupted"` (signal abort).
6. `scrape_entries_riding` maps `state.job_records` → manifest via `_build_manifest`.

## Modules

### cooldown.py (95 LOC)

**Purpose:** Riding-specific proxy cooldown manager (`RidingCooldownManager`). Isolated from the
theblock-shared `proxy_pool/cooldown.py` (`PersistentCooldownManager`) — the theblock path is
untouched. Supports two policies selectable per-run via `RidingScrapeConfig.cooldown_policy`:
`"fixed"` (60-min flat cooldown, byte-identical to current production control arm) and `"exp"`
(exponential backoff with full jitter, ported from scrapy-rotating-proxies: base=300s, cap=3600s;
reset-on-productive-ride: if `ride_ok >= 1` the `failed_attempts` counter resets before computing
the backoff, so a proxy that delivered a successful fetch re-enters the eligible pool quickly).
`cooldown_count()` correct under both policies — counts proxies with `now < next_eligible` (exp) or
`now - burned_at < 3600s` (fixed), used by the watchdog's `pool_samples` A/B telemetry.
Read-only `.policy` property exposes the active policy string for the reporter.
**Reads:** `_burned_at` / `_next_eligible` / `_failed_attempts` (in-memory dicts keyed by `proxy_key`).
**Writes:** same dicts on `mark_burned(proto, hp, ride_ok=0)`.
**Called by:** `rider.py:_finalize_ride` (via `state.cooldown_mgr.mark_burned`);
`rider.py:_next_proxy` (via `state.cooldown_mgr.eligible_candidates`);
`rider.py:_watchdog` (via `state.cooldown_mgr.eligible_candidates` + `cooldown_count`);
`scrape.py:scrape_entries_riding` (instantiation: `RidingCooldownManager(policy=riding_cfg.cooldown_policy)`);
`reporter.py:_write_md` (via `state.cooldown_mgr.policy`).
**Calls out:** `src.news.engine.proxy_pool.proxy_key.proxy_key`.

---

### state.py (87 LOC)

**Purpose:** Shared riding dataclasses + calibrated constants — the concern split out of the
original monolithic `rider.py` so every other module (and the reporter, and dev/ tests) has one
canonical import source instead of going through `rider.py`.
**Reads:** n/a (data-shape module).
**Writes:** n/a.
**Called by:** `rider.py` (imports all of it), `fetch.py` (`DELAY_BEFORE_HTML`, `RAW_SUBDIR`),
`abort.py` (`RiderState` type hint), `reporter.py` (`RiderState`, `FAIL_THRESHOLD`), `scrape.py`
(`RiderState`), dev/ tests under `dev/news_pipeline/coindesk_proxy_riding/`.
**Calls out:** `src.news.engine.proxy_riding.cooldown.RidingCooldownManager` (type hint on
`RiderState.cooldown_mgr`).

Dataclasses: `RiderState` (shared mutable job state — fields: `output_dir` raw writes, `job_dir`
report writes, `target_urls` frozenset of all distinct targets, `done_urls` set of written URLs,
`pool_samples` list of `(elapsed_s, n_eligible, n_cooldown)` tuples appended by `_watchdog` each poll,
`pool_provider` async callable `() -> list[tuple[str,str]]` for 30-min refresh (None = static pool),
`proxy_pool` raw `(proto, host_port)` tuples from `load_backfill_pool()`;
`all_resolved = len(done_urls) >= len(target_urls)`); `JobRecord` (per-URL outcome — `status` ∈
`{ok, regwall, connect_fail, failed, empty}`); `RideRecord` (per-proxy-ride summary — `positions` is
a list of `(url, status, elapsed_s)` tuples, one per URL attempted on that proxy).

`JobRecord.load_s: float | None` — navigation load time for OK fetches only, computed as
`max(0, elapsed_s − DELAY_BEFORE_HTML)`. crawl4ai's `CrawlResult` exposes no dedicated nav-timing
field; subtracting the fixed 0.5 s post-load delay approximates the navigation phase (shifts the
curve right by ~constant context-setup overhead, reads the timeout conservatively). Non-OK fetches
leave `load_s = None`.

`RiderState.connect_fail_records: list` — list of `(elapsed_s: float, subtype: str)` tuples, one per
connect_fail fetch, appended in `rider.py:_apply_fetch_result` BEFORE the `"break"` that exits the
proxy ride (connect_fail is never appended to `job_records`). Populated even on stall/abort —
available in every `write_riding_report` call path.

### fetch.py (108 LOC)

**Purpose:** Per-URL fetch + outcome classification — the crawl4ai call, regwall detection,
connect-fail subtype classification, and raw-HTML persistence. Isolated from slot orchestration so
it can be monkeypatched wholesale in `dev/` tests (`_fetch_one_url` replaced with a deterministic
stub) without touching `rider.py`'s loop control.
**Reads:** n/a (pure per-call).
**Writes:** `output_dir/raw/{url_hash}.html` (`_write_raw`, called from `rider.py:_apply_fetch_result`
on first-writer OK).
**Called by:** `rider.py:_run_slot` (`_fetch_one_url`), `rider.py:_apply_fetch_result`
(`_write_raw`, `_url_hash`, `_classify_connect_fail`).
**Calls out:** `crawl4ai` (`AsyncWebCrawler`, `CrawlerRunConfig`, `CacheMode`, `ProxyConfig`,
`DefaultMarkdownGenerator`).

`_fetch_one_url` always closes the Playwright session (`kill_session`) in a `finally`, regardless of
outcome, so fresh cookies are guaranteed on the next fetch even after an exception.
`_classify_crawl_result` maps a crawl4ai `CrawlResult` to `(status, html, markdown_len, err)`:
not-success → `connect_fail` if the lowercased error matches `_PROXY_ERR` substrings else `failed`;
no `result.html` → `empty`; regwall signal in `raw_markdown` → `regwall`; else `ok`.

### abort.py (96 LOC)

**Purpose:** The three watchdog/signal abort paths (`_abort_done`, `_abort_interrupted`,
`_abort_stall`) plus their shared write-report-and-exit helper. Split out of `rider.py` because all
three previously triplicated ~40 lines of report-write-with-fallback logic; `_abort_write_report_and_exit`
is the single mechanical dedup of that logic, parametrized by log prefix / exit code / fallback title
/ extra fallback-stub lines. Output is byte-identical to the pre-split triplicated version.
**Reads:** `RiderState` (in-memory, for the report + fallback stub).
**Writes:** `state.job_dir/job.md` (+ `cumulative.png`/histograms via `write_riding_report`, or the
minimal fallback stub on any reporter error).
**Called by:** `rider.py:_watchdog` (`_abort_done`, `_abort_stall`); `rider.py:run_riding_pool`
(`_abort_interrupted`, registered as the SIGINT/SIGTERM handler).
**Calls out:** late import of `reporter.write_riding_report` inside `_abort_write_report_and_exit`
(avoids a circular top-level import — `reporter.py` imports `RiderState`/`FAIL_THRESHOLD` from
`state.py`, not from `abort.py`, but the cycle would still exist through `rider.py`).

Each of the three public functions sets `state.termination` and prints its own log line BEFORE
calling the shared helper (log line content differs per trigger — done/stall use `[watchdog]`,
interrupted uses `[rider]`); the helper reads `state.termination` back out for the fallback stub's
`termination:` line, so the three callers stay thin (10-13 lines each).

### rider.py (321 LOC)

**Purpose:** Entry module — orchestrates the browser pool + slot tasks + watchdog
(`run_riding_pool`), and owns the two loops that need to stay attribute-patchable by
`dev/news_pipeline/coindesk_proxy_riding/` tests (`_run_slot`, `_watchdog` — `unittest.mock.patch.object`
on `_fetch_one_url`/`_next_proxy`/`POOL_REFRESH_INTERVAL_S`/`os` only takes effect if the patched
name is looked up through THIS module's globals, i.e. the patched-against function must be defined
here, not in `fetch.py`/`state.py`). Manages B `AsyncWebCrawler` instances, N slot coroutines,
per-URL proxy context, burn/fail rotation, 30-min pool refresh. Installs SIGINT/SIGTERM handlers so
manual aborts also produce a report.
**Reads:** URL queue (asyncio.Queue), proxy pool list, `RidingCooldownManager` (shared state).
**Writes:** `output_dir/raw/{hash}.html` for each ok URL (via `fetch.py:_write_raw`); triggers
`state.job_dir/job.md` + `cumulative.png` writes on abort (via `abort.py`).
**Called by:** `scrape.py:scrape_entries_riding` (via `run_riding_pool`).
**Calls out:** `crawl4ai` (`AsyncWebCrawler`, `BrowserConfig`); `state.py` (`RiderState`,
`RideRecord`, `JobRecord`, constants); `fetch.py` (`_fetch_one_url`, `_classify_connect_fail`,
`_write_raw`, `_url_hash`); `abort.py` (`_abort_done`, `_abort_interrupted`, `_abort_stall`).

`_run_slot` (outer proxy-acquisition loop + inner burn loop) delegates the per-fetch status branch
to `_apply_fetch_result` (returns `"continue"|"append"|"break"` — mirrors the original inline
`continue`/`break`/fall-through-to-append control flow exactly: `connect_fail` and
fail-threshold-reached both `"break"` WITHOUT appending to `job_records`; `ok`/`regwall`/below-threshold
`failed`/`empty` `"append"`; dup-race `ok` `"continue"`s without appending) and the `finally`-block
`RideRecord` construction to `_finalize_ride`. Both helpers mutate a local `_RideProgress` scratch
dataclass (`burn_count`, `fail_count`, `ride_ok`, `positions`, `cf_broke`) — ephemeral per-ride
bookkeeping, never persisted, never reaches a report.

`run_riding_pool` signal handler lifecycle: after `state` is constructed, installs
`loop.add_signal_handler(SIGINT/SIGTERM, _abort_interrupted, state, signum)`. Removed in
`_teardown_pool` (before `watchdog.cancel()`) so they don't fire during the normal-completion
`write_riding_report` call in `pipeline.py`.

`_watchdog` poll loop (every `min(30, stall_timeout_s/4)` s), in order:
1. Append pool sample `(elapsed_s, n_eligible, n_cooldown)`.
2. **Pool refresh** (if `pool_provider` set and `POOL_REFRESH_INTERVAL_S = 1800` elapsed): `await
   state.pool_provider()` via `run_in_executor` thread; guard against empty result; atomic assign
   `state.proxy_pool = new_pool`; `cooldown_mgr` persists unchanged.
3. `all_resolved AND in_flight == 0` → `return` (clean drain).
4. `all_resolved AND in_flight > 0` → `_abort_done(state)`: report + `os._exit(0)` (wedge-after-done).
5. `idle > stall_timeout_s` → `_abort_stall(state, idle)`: report + `os._exit(1)` (genuine stall).

### reporter.py (384 LOC)

**Purpose:** Job report writer — `job.md` (counts, throughput, proxy-riding stats, eligible-pool-over-time
table, regwall counts, connect-fail breakdown, success load-time distribution) + `cumulative.png`
(step-plot of cumulative OK fetches over time) + `success_load_hist.png` (histogram of OK-fetch load
times) + `connect_fail_hist.png` (histogram of connect-fail elapsed times).
**Reads:** `RiderState` (in-memory), `t_job_start` (datetime).
**Writes:** `{job_dir}/job.md`; `{job_dir}/cumulative.png`;
`{job_dir}/success_load_hist.png` (only when ≥2 OK `load_s` values);
`{job_dir}/connect_fail_hist.png` (only when ≥2 `connect_fail_records`).
All histograms: 0.25 s bins, x-axis auto-ranges to data max, page_timeout_s red vertical line.
**Called by:** `pipeline.py:run_scrape_only` (normal completion, via `write_riding_report`);
`abort.py:_abort_stall` (late import, stall abort); `abort.py:_abort_done` (late import,
wedge-after-done); `abort.py:_abort_interrupted` (late import, SIGINT/SIGTERM abort).
**Calls out:** `matplotlib` (lazy import inside plot functions); `statistics` (stdlib, incl.
`statistics.quantiles` with `method='inclusive'` — bounds p-values within observed [min, max]);
`math` (stdlib, bin count); `src.news.engine.proxy_riding.state` (`RiderState`, `FAIL_THRESHOLD`).

`_compute_stats` additions:
- `load_times` / `load_perc` — OK-fetch load times + inclusive percentiles (None when <2 samples)
- `cf_times` / `cf_perc` — connect-fail elapsed times + inclusive percentiles (None when <2 samples)
- `cf_subtype_counts` — dict of subtype → count (`page_timeout`, `net_timed_out`, `proxy_connect`, `other`)
- `page_timeout_s` — from `state.page_timeout_ms / 1000`, shared axis reference for both histograms

job.md section **"Connect-fail breakdown"** (between Regwall and Success load-time): percentile table
(p50/p90/p95/p99/max, n=count) + subtype table (count + share) computed over `connect_fail_records`.
Subtypes shown in fixed order (page_timeout, net_timed_out, proxy_connect, other) for cross-run
comparability. `_Fewer than 2 connect-fail records_` note + no histogram when <2 samples.

job.md section **"Success load-time distribution"**: percentile table computed over OK fetches only.
`_Fewer than 2 OK fetches_` note when unavailable.

### scrape.py (116 LOC)

**Purpose:** Pipeline entry point + manifest adapter. Loads pool, shuffles, calls `run_riding_pool`,
maps `RiderState.job_records` → pipeline manifest.
**Reads:** entries list (in-memory), `RidingScrapeConfig`, proxy pool (network via `load_backfill_pool`).
**Writes:** delegates to `rider.py` (raw HTML writes to `output_dir/raw/{hash}.html`); writes nothing directly.
**Called by:** `pipeline.py:run_scrape_only` (proxy_riding dispatch arm).
**Calls out:** `src.news.engine.proxy_pool.pool_loaders.load_backfill_pool`;
`src.news.engine.proxy_riding.cooldown.RidingCooldownManager`;
`src.news.engine.proxy_riding.rider.run_riding_pool`;
`src.news.engine.proxy_riding.state.RiderState`.

`_pool_provider()` — shared async helper used for BOTH initial pool load (at `scrape_entries_riding`
start) AND as the `pool_provider` callable threaded into `RiderState` for 30-min watchdog refresh.
Runs `load_backfill_pool()` in `run_in_executor` (blocking network I/O), filters to
`BROWSER_ELIGIBLE_PROTOS = {"http","socks5"}`, shuffles. Single source of truth — no separate
init-vs-refresh code paths.

Returns `tuple[list[dict], RiderState]` — manifest + state. State is consumed by caller
(`pipeline.py`) to call `write_riding_report`; manifest is consumed to build `ok_manifest_entries`
for `_append_to_raw_manifest`. `output_dir` must be `platform_dir` (`data/news/{name}/`) so the
engine writes to `platform_dir/raw/{hash}.html` = the path dedup checks. `job_dir` must be
`platform_dir/"scrape_jobs"/{job_id}` (computed in `pipeline.py` before the call).

Status mapping in `_build_manifest`: if any `job_record` for a URL has `status == "ok"` (and a
written file) → manifest `"ok"`; all other outcomes (regwall, connect_fail, failed, empty, never
reached) → `"failed"`. No `"dead"` status (CoinDesk doesn't 404/410 through proxy; it regwalls).

## State

`RiderState` (defined in `state.py`, re-exported through `rider.py`) is the shared mutable state
across all slot coroutines and the watchdog. Owned and mutated by `rider.py:run_riding_pool`,
`rider.py:_run_slot`, `rider.py:_apply_fetch_result`, `rider.py:_finalize_ride`. Read by
`reporter.py:write_riding_report` and `scrape.py:_build_manifest` (read-only, after run completes).
`asyncio` single-threaded: `set.add/discard` on `in_flight_urls` and `int` increments on counters
are safe without explicit locking. `proxy_lock` (asyncio.Lock) guards `proxy_cursor` advancement.

## Gotchas

- `file` field in manifest points to `.html` (not `.md`). `dedup.py:filter_new_entries` mode `"raw"`
  now accepts `raw_ext` param — pass `".html"` for riding path (done in `pipeline.py:run_scrape_only`).
  `pipeline.py:_run_clean_pass` still hardcodes `{h}.md` but is NOT on CoinDesk's path (proxy_pool /
  TheBlock only) — out of scope unless CoinDesk gains a clean-pass step.
- `output_dir` passed to `scrape_entries_riding` must be `platform_dir` (`data/news/{name}/`), NOT
  `raw_dir`. The rider writes to `output_dir/raw/{hash}.html`; passing `raw_dir` puts files at
  `raw/raw/` (wrong), breaking dedup.
- All three abort functions (`_abort_stall`, `_abort_done`, `_abort_interrupted`, in `abort.py`) call
  `os._exit` — no Python teardown, no atexit, no `browser.close()`. Raw files flushed before the call
  are durable; in-flight writes at the moment of abort are lost. All write to `state.job_dir`
  (= `scrape_jobs/{job_id}/`), NOT to `output_dir`; each creates the dir itself (`mkdir`) before
  the first write because the dir may not exist at abort time. Exit codes follow Unix signal-kill
  convention: 130 = 128+SIGINT(2), 143 = 128+SIGTERM(15); 0 = wedge-after-done (work complete), 1 = stall.
- Late import of `reporter.write_riding_report` inside `abort.py`'s shared helper is intentional:
  `reporter.py` imports from `state.py`; importing `reporter` at `abort.py`'s top level would still
  create a cycle through `rider.py` (which imports both `state.py` and `abort.py`).
- Pool load (`load_backfill_pool`) is blocking network I/O, run via `run_in_executor` to avoid
  blocking the event loop during the async entry point.
- Regwall detection (`fetch.py:_is_regwall`) checks `result.markdown.raw_markdown` (browser-rendered
  visible text), NOT `result.html` — `REGWALL_SIGNALS` are embedded as hidden React components in the
  raw HTML of every CoinDesk page, so an html-based check would silently never fire.
- `state.py:STALL_TIMEOUT_S = 3600.0` is only the module-level fallback default (used when
  `run_riding_pool`/`RiderState` are constructed without an explicit `stall_timeout_s`). Production
  runs override it via `RidingScrapeConfig.stall_timeout_s = 300.0` — don't read the module constant
  as "the" production stall timeout.
