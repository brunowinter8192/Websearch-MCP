# 61 — CoinDesk backfill: browser proxy-riding engine (IP rotation against the regwall)

Process doc for the CoinDesk 61k article-body backfill. Discovery is done (timeline API → inventory
`data/news/coindesk/inventory/coindesk_{year}.txt`, 61,628 URLs). The blocker is the **scrape**: CoinDesk's
regwall is IP-rate metered, so a single-IP browser scrape (`src/news/engine/scrape.py` as of this session)
cannot finish the corpus — the IP goes "hot". This theme builds the IP-rotating backfill engine. All work
lives in `dev/news_pipeline/coindesk_proxy_riding/`; `src/` is UNCHANGED.

## Premise (user-decided, fixed)

- Keep the **crawl4ai browser** fetcher (CoinDesk's body is JS-rendered). Browser path is fixed.
- Defeat the regwall by **riding proxies**: a proxy rides URLs; **fresh cookie context per URL on the same
  IP** (keeps the cookie-fix, so the only regwall signal is IP-rate); burn the proxy at a cumulative
  regwall threshold (default 2) → rotate IP.
- Regwall detection on `result.markdown.raw_markdown` (visible text), NOT `result.html` (the regwall marker
  `"Create a FREE account…"` is a hidden React component present on EVERY page's raw HTML). Store full
  `result.html` (lossless). No cleanup this session — raw corpus only; cleanup built later on the full corpus.
- **Only termination criterion = global 60-min stall** (no progress → remaining URLs to failure log). No
  per-URL give-up (see Abort-criteria fix).

## Iteration 1 — per-browser-process + curl_cffi alive-feeder

Architecture: a 128-wide curl_cffi alive-feeder pre-validates raw pool proxies (reachable+200 on a CoinDesk
page) and feeds http/socks5 ones to N browser slots; each slot = a fresh `AsyncWebCrawler` PER PROXY with
`BrowserConfig(proxy_config=…)` (proxy at browser-launch = one Chrome PROCESS per proxy).

### 500-run (concurrency 20), `data/news/coindesk/riding_test_500/job.md`

| Metric | Value |
|---|---|
| OK / target | 499 / 500 (1 fail = a Spanish-locale 403) |
| Regwall | 11 (2.2%), ALL recovered on a fresh IP via requeue |
| Connect-fail fetches | 704 |
| Proxies burned | 727 (only 95 produced ≥1 ok) |
| Ride length (URLs/proxy) | mean 1.7, median 1, min 0, max 63 |
| Wall / throughput | 4032s (67min) → **61k projection ≈ 137h** |
| HTML p50 / markdown p50 | 501 KB / 17,168 chars (full bodies, no truncation) |

Feeder smoke: pool 26,540; ~141 browser-eligible proxies/min, 28.4% alive — feeder over-supplies the slots
~13×, slots never proxy-starved.

**Findings:** (a) Premise validated — regwall is a non-issue (11/500, all recovered); good proxies ride long
(max 63). (b) Throughput is killed by **connect-fail churn**, NOT the browser render: a clean fetch is ~7s, so
all-good proxies → ~6h for 61k. The 137h is ~95% wasted slot-time on junk proxies (each junk = full Chrome
launch ~2-3s + 12s page_timeout + teardown). Median ride 1 = half the proxies die after ≤1 URL. (c) The
bottleneck is the per-proxy browser cost, not proxy supply.

## Iteration 2 — per-context proxy redesign (the crawl4ai finding)

Source read of `crawl4ai/browser_manager.py`:
- `BrowserConfig.proxy_config` → browser LAUNCH args (`browser_args["proxy"]`, ~line 1137) = one Chrome
  process per proxy (Iteration 1, expensive).
- `CrawlerRunConfig.proxy_config` → `context_settings["proxy"]` (lines 1334-1341) via `self.browser.new_context()`
  = per-CONTEXT, inside the existing browser process. `_make_config_signature` includes `proxy_config`
  (lines 1401-1409) → one context per distinct proxy, all in ONE browser. `arun()` concurrent-safe across
  riders (contexts_by_config under `_contexts_lock`).

Redesign (`p2_browser_rider.py`): ONE shared `AsyncWebCrawler` (no browser-level proxy) + N rider tasks;
per URL `arun(CrawlerRunConfig(session_id=uuid, proxy_config=ProxyConfig(server=…), page_timeout=8000…))` →
fresh context+cookies+proxy, then `kill_session`. Riders draw RAW proxies directly from the pool (alive-feeder
`p1` DELETED — see Alive-check decision). Proxy switch = `new_context` (~50-100ms) instead of Chrome launch
(~2-3s).

### Findings — two walls hit

- **RAM not free:** Chromium spawns a separate RENDERER PROCESS per context. The 128 attempt showed 135
  renderer processes (+ ~6 gpu/utility) in ONE browser instance. Shared GPU/network/main process saves some
  overhead vs N full browsers, but RAM still scales with concurrency (~17 GB est. at 128). The "one light
  browser" RAM hope is only partly real.
- **128 contexts in one browser DEADLOCKS:** the 128-concurrency / 150-URL smoke hung 12+ min, `arun()`
  never returned for any slot, zero crawl activity. A single browser process cannot coordinate 128
  simultaneous contexts/navigations. **20 works** (12 chrome processes = one tree, ok-scrapes flow).
  → High concurrency needs a POOL of browser PROCESSES (B browsers × C contexts), not one browser × 128.

### Alive-check decision (dropped)

Under per-context, a junk context is nearly as cheap as a curl thread (same ~12s/8s timeout, light cookie-jar
+ CDP target, ~100-200ms create/close). The pre-check's "protect expensive slots" rationale (valid for 20-40
RAM-heavy processes) collapses; it also COSTS one CoinDesk regwall-budget request per proxy. So the
alive-feeder was removed — raw proxies straight to contexts, high concurrency absorbs junk. Cost of dropping
it = more CHURN per URL (connect-fails before a good proxy), NOT lost URLs (completeness is a requeue/retry
question, orthogonal). The only residual pro-filter argument left is the single-browser CPU bottleneck — moot
once we go multi-browser-pool.

## Fixes landed this session

- **socks4 filter** (`run_coindesk_riding.py`, `7935ec6`): raw pool 26,492 → 20,794 browser-eligible after
  `BROWSER_ELIGIBLE_PROTOS = {"http","socks5"}` (~22% was socks4, which Playwright cannot drive → instant
  connect-fail). The deleted alive-feeder used to do this proto-filter; restored at pool-load.
- **Abort-criteria removal** (`p2_browser_rider.py`, `09480d2`): the worker had invented two per-URL give-up
  criteria that were never agreed — `MAX_URL_RETRIES=3` (regwall gives up after 3) and 403/empty → immediate
  terminal `n_failed`. Both removed. ALL non-ok outcomes (regwall, connect_fail, 403/empty) now requeue
  unbounded; `last_progress_mono` stamps only on `ok`; the 60-min global stall is the sole terminator. (The
  20-smoke's 27 "failures" were ALL 403 anti-bot marked terminal — a 403 is IP-specific, succeeds on a fresh
  IP, so terminal-fail was wrong.)

## Dev state as of this session

`dev/news_pipeline/coindesk_proxy_riding/` on `dev`: `p0_pool` (pool + 60-min cooldown via
`PersistentCooldownManager`, `COOLDOWN_S=3600`, The-Block-copied), `p2_browser_rider` (**multi-browser pool**:
B `AsyncWebCrawler` instances, slots round-robin `i % B`; per-context proxy; **fail-rotation**: 2-strike drop
of failed/empty proxies, `FAIL_THRESHOLD=2`), `p3_url_sampler` (proportional 500 across years), `p4_reporter`
(job.md + 3 plots; Browsers / Contexts-per-browser / Failed-rotations rows), `run_coindesk_riding` (CLI:
`--browsers --concurrency --burn-threshold --n-urls --page-timeout --output-dir`; raises RLIMIT_NOFILE to
16384; http/socks5 filter; empty-pool guard). `p1_alive_feeder` deleted. `src/` untouched. See Iteration 3.

## Resolved questions — the research that drove Iteration 3

Both questions below were answered this session and implemented (see Iteration 3). Kept for the evidence trail.

1. **Contexts-per-browser limit** — goal: the safe C between our measured 20 (works) and 128 (hangs).

   **Finding — Chromium renderer-process cap (resolved).** Source: `GetMaxRendererProcessCount()` in
   `content/browser/renderer_host/render_process_host_impl.cc` (chromium/chromium, read via gh-cli). Desktop
   (non-Android) formula:
   `max_count = clamp( (TotalRAM_MiB / 2) / kEstimatedWebContentsMemoryUsage , 3 , GetPlatformMaxRendererProcessCount() )`
   - `kEstimatedWebContentsMemoryUsage = 85 MB` on 64-bit (60 MB on 32-bit).
   - `GetPlatformMaxRendererProcessCount() = GetPlatformProcessLimit() / 2`, **hard-capped at 82**. macOS hits
     the 82-cap path (unlimited/unknown platform limit). → on any machine ≥ ~14 GB RAM the cap is **82
     renderer processes**. Source RAM table (64-bit): 16 GB→96 (pre-clamp), 4 GB→24, 1 GB→6.
   - It is a **soft** limit: above 82 Chromium REUSES renderer processes (consolidates site-instances) instead
     of spawning new ones. Our arch (fresh BrowserContext + distinct proxy per URL = distinct storage/network
     partition) DEFEATS reuse → 128 contexts spawned the measured 135 renderer processes, ~1.6× over the 82
     ceiling, exactly the regime the cap exists to prevent. **128-deadlock explained:** operating above the
     design ceiling where process-reuse + navigation coordination collapses.
   - **Implication:** 82 = absolute design ceiling, NOT a target. Safe C is well below it; exact value between
     20 and 82 is an empirical-sweep question. Multi-browser pool (Q2): keep per-browser C clearly under 82,
     scale throughput via B browser processes, not more contexts per browser.

   **Still open within Q1:** Playwright-side concurrency behaviour (known "many concurrent contexts hang"
   issues + "use multiple browser instances for parallelism" guidance); crawl4ai's own concurrency knobs
   (`arun_many`, `MemoryAdaptiveDispatcher`, max sessions — local in `venv/.../crawl4ai/`). These set the
   practical C below the 82 hard ceiling.
2. **Multi-browser pool** — B browser processes × C contexts each = total concurrency, sidestepping the
   single-browser deadlock + spreading CPU/crash-radius. Depends on (1).

   **Finding — crawl4ai concurrency primitives** (gh-cli `index_issues unclecode/crawl4ai`, indexed into the
   volatile `github_issues` collection — synthesis preserved here). crawl4ai exposes NO multi-browser-PROCESS
   pool; concurrency within ONE `AsyncWebCrawler` (= one browser process) is governed by a **dispatcher**:
   - `MemoryAdaptiveDispatcher` (default for `arun_many`): `max_session_permit` default **20** (matches our
     empirically-validated 20) + `memory_threshold_percent` (default ~90%, community uses 70-85%) which PAUSES
     new sessions when RAM exceeds threshold → directly addresses the renderer-RAM wall (Iteration-2 finding).
   - `SemaphoreDispatcher`: fixed `max_session_permit` cap, no RAM adaptivity.
   - **Gotcha (#1818, #1584):** `CrawlerRunConfig.semaphore_count` / `mean_delay` / `max_range` are SILENTLY
     IGNORED by the default dispatcher — to control concurrency you MUST pass an explicit dispatcher with
     `max_session_permit`. (Wired-up fix in PR #1861; pass-explicit-dispatcher is the safe pattern regardless.)
   - **Pool = B independent `AsyncWebCrawler` instances** (B browser processes), each with its own dispatcher
     capped at C ≈ 20. No built-in process pool; community does manual batching (fresh crawler per batch).

   **Finding — high-concurrency race pathology** (#1367, `github_issues`). At high concurrency, per-context
   proxies + React/SPA navigation cause `net::ERR_ABORTED` / context-recycle races / hangs. Mitigations
   (several already in our design): `use_persistent_context=False` (we use fresh context/URL ✓),
   `wait_until="domcontentloaded"` not `networkidle` (we use domcontentloaded ✓); proxy-rotation is the most
   abort-prone path; React pages are the most navigation-sensitive (**CoinDesk IS React**). Memory-leak /
   unbounded-growth in 0.6–0.7.8 was fixed in 0.8.0+ (browser-context LRU eviction, CDP leak fixes, browser
   recycling); we run 0.8.6. → the 128-deadlock is the Chromium renderer-cap (>82, Q1 finding) COMPOUNDED by
   this race pathology under extreme per-context-proxy concurrency.

   **Pool design (converging):** B browsers × C ≈ 20 contexts, a `MemoryAdaptiveDispatcher` per browser for
   the RAM throttle; keep per-browser C well under the 82 renderer ceiling, scale via B.

## Iteration 3 — multi-browser pool + fail-rotation fix + first 20×6 run

Built on the Q1/Q2 research above. Two engine changes (`dev/` only, `src/` untouched), each worker-built +
smoke-verified, merged to `dev`.

### Multi-browser pool (commit `1ebd1c5`)

`run_riding_pool()` now creates B `AsyncWebCrawler` instances (was one), starts all via
`asyncio.gather(*[c.start() …])`, distributes the N slots round-robin (`slot i → crawlers[i % B]`), closes all
with `return_exceptions=True`. New `--browsers` flag (default 1 = byte-identical to the old single-browser
path). `_run_slot` / `_fetch_one_url` unchanged (already took a crawler param). `RiderState` carries
`n_browsers` + `n_slots`; reporter surfaces Browsers + Contexts-per-browser. Rationale: keep per-browser
contexts well under the 82 renderer ceiling (Q1), scale concurrency via B processes (Q2). **Smoke (2 browsers ×
2 contexts):** both browsers launch, 54 ok, rotation + regwall detection work, raw HTML written, **no deadlock**.

### Fail-rotation fix (commit `cb2fb46`)

Bug surfaced by the multi-browser smoke: with the alive-precheck removed (Iteration 2), the engine rides RAW
garbage proxies — and a proxy returning status `failed`/`empty` was **requeued but never rotated** (the ride
loop only rotated on `connect_fail` and counted `regwall` toward burn). A garbage proxy that `failed` every URL
was ridden forever (observed slot at ride-position **353**). Fix (mirrors The Block): per-ride `fail_count`,
`FAIL_THRESHOLD=2` — on the 2nd failed/empty strike the ride ends (`break`), which falls through to the existing
`finally → cooldown_mgr.mark_burned`, giving the dropped proxy the 60-min cooldown for free (no new cooldown
logic). **Smoke delta:** max ride-position **353 → 6**; failed proxies drop exactly at `r=2`; queue drains
continuously instead of stalling.

### First real run — launched, result pending

`run_coindesk_riding.py --browsers 20 --concurrency 120 --n-urls 500 --output-dir
data/news/coindesk/riding_mb20x6_500` — 20 browsers × 6 contexts = 120 concurrency. Self-terminates on
queue-drain or 60-min stall. **Next session: read `job.md`** — wall-time + 61k projection vs the 137h
Iteration-1 baseline; the open item is now purely the measured throughput at 20×6, no longer a research
question.

## Iteration 4 — progress watchdog + hard-abort (the 12h-hang fix)

### Symptom

The `--browsers 20 --concurrency 120 --n-urls 500` run (`riding_mb20x6_500`) wrote **469 raw HTML files in
a 31-minute window (03:16–03:47), then zero new files for ~11.5 hours** until a manual Ctrl+C. No `job.md`
was ever written. The Ctrl+C teardown traceback was stuck inside `browser.close()` — browsers were wedged
at shutdown. The `STALL_TIMEOUT_S = 3600` cooperative terminator (the "60-min stall") never fired despite
11.5 hours of no progress.

### Root cause

The stall check in `_run_slot` is at the **top of a while loop**, evaluated only when the slot coroutine
has CPU time:

```python
if time.monotonic() - state.last_progress_mono > state.stall_timeout_s:
    state.termination = "stall"
    break
```

The coroutine is permanently suspended here:

```python
status, ... = await _fetch_one_url(crawler, url, pstr, state.page_timeout_ms)
# internally: result = await crawler.arun(url=url, config=run_cfg)
```

When Playwright browsers enter a zombie state (process alive, WebSocket connection open, but no CDP
messages ever returned — consistent with the 11.5 h silence and the `browser.close()` hang on teardown),
`crawler.arun()` never resolves. Its asyncio future never becomes ready. The slot coroutine stays
permanently suspended at the `await` — it never gets CPU time again, never reaches the top of the while
loop, never runs the stall check.

With 120 slots sharing 20 browsers, as each browser wedges its 6 slots pile up in the same permanently
suspended state. Once all 20 browsers are zombie, all 120 slots are permanently suspended. The asyncio
event loop has 120 tasks all blocked on I/O futures that will never fire. **There are no remaining
runnable tasks and no scheduled timer callbacks.** The event loop's `select()` blocks indefinitely on file
descriptors that will never deliver data. The 60-min check is cooperative — it requires a slot to be
scheduled. With zero schedulable slots, it never fires.

`kill_session` in `_fetch_one_url`'s `finally` block also cannot run for the same reason: the coroutine
never exits the `await crawler.arun()` call. The Ctrl+C teardown then hit `browser.close()` on the same
zombie connections, explaining the observed traceback.

### Fix — independent asyncio.sleep-based watchdog

A separate `asyncio.create_task(_watchdog(state, output_dir))` is created in `run_riding_pool` before the
slot tasks, and cancelled in the `finally` block when slots return normally. The watchdog polls via
`asyncio.sleep(min(30, stall_timeout_s / 4))`. Because `asyncio.sleep()` registers a monotonic-clock
timer via `loop.call_later()`, the event loop's `select()` timeout is bounded to the poll interval — the
watchdog fires on a timer **even when all slot tasks are permanently suspended on wedged browser I/O**. No
I/O event is needed; the timer wakes the event loop and resumes the watchdog coroutine.

When `time.monotonic() - state.last_progress_mono > state.stall_timeout_s` is true, the watchdog calls
`_abort_stall(state, output_dir, idle_s)`, which never returns.

### `_abort_stall` — hard abort sequence

1. Set `state.termination = "stall"`.
2. Drain `state.url_queue` via `get_nowait()` loop → `queued: list[str]`.
3. Snapshot `sorted(state.in_flight_urls)` → the wedged URLs (diagnostically valuable).
4. Write `output_dir/remaining_urls.txt` with two clearly labelled sections:
   - `# never attempted (queue) — N URLs` + the drained queue URLs
   - `# in-flight / wedged at abort — N URLs` + the in-flight URL set
5. Late-import `write_riding_report` from `p4_reporter` (late import avoids circular at module level) →
   write `job.md` from accumulated `state` data. Fallback: minimal stub `job.md` if reporter raises (e.g.
   matplotlib absent), so the run is never completely silent.
6. `sys.stderr.flush()` then **`os._exit(1)`** — bypasses asyncio teardown, `browser.close()`, all Python
   atexit hooks. The OS reaps Chrome processes. Raw files + `remaining_urls.txt` + `job.md` are already
   flushed to disk before `os._exit` is reached.

### `in_flight_urls` set

`RiderState` gains `in_flight_urls: set` (default empty). In `_run_slot`, `state.in_flight_urls.add(url)`
immediately after `state.in_flight += 1`; `state.in_flight_urls.discard(url)` immediately after
`state.in_flight -= 1`. Crucially, this is NOT in a `try/finally`: when a slot wedges at
`await _fetch_one_url()`, the `discard` is never called — the URL remains in `in_flight_urls` until abort,
exactly capturing the set of wedged fetches. `asyncio` is single-threaded so `set.add/discard` are
atomic.

### `RiderState.t_job_start`

Added as `datetime = field(default_factory=lambda: datetime.now(timezone.utc))`. Used by `_abort_stall`
when calling `write_riding_report(state, output_dir, state.t_job_start)` — the watchdog has no other
access to the job start time.

### `--stall-timeout` flag

`run_coindesk_riding.py` gains `--stall-timeout FLOAT` (default `3600.0`). Threaded through
`run_riding_pool(stall_timeout_s=args.stall_timeout)` → `RiderState(stall_timeout_s=...)`. Allows smoke
tests to set a short threshold (e.g. `--stall-timeout 25`) to exercise the watchdog without a 60-min
wait.

### Deterministic test (`test_watchdog.py`)

Two tests, no browser or proxy infrastructure required:

- **test 1 — watchdog task:** constructs `RiderState` with `last_progress_mono` aged 200 s past a 1 s
  threshold, 2 queued URLs, 1 in-flight URL in `in_flight_urls`. Patches `os._exit` to raise
  `SystemExit(code)`. Runs `_watchdog(state, tmp_dir, poll_interval=0.1)` inside `asyncio.run()`. The
  watchdog fires after one 0.1 s sleep, calls `_abort_stall`, which calls the patched `os._exit(1)` →
  `SystemExit(1)` caught. Asserts: `exit_calls == [1]`; `remaining_urls.txt` exists with both section
  headers and all 3 URLs; `job.md` exists with `stall` in content. **PASS.**

- **test 2 — `_abort_stall` directly:** same state, calls `_abort_stall(state, tmp_dir, idle_s=999.0)`.
  Asserts: same file checks + `"999"` present in the header line. **PASS.**

### What was deliberately NOT done

Per-fetch `asyncio.wait_for` around `crawler.arun()` is **NOT added** in this iteration. It is
evidence-gated: we need the re-run with `--stall-timeout 60` (or similar) to produce a `remaining_urls.txt`
and failure log that shows whether slots wedge systematically. If wedging is confirmed, per-fetch timeouts
are the follow-up. Adding `wait_for` before seeing the failure log is speculative.

`src/` remains untouched. Engine is dev-only (`dev/news_pipeline/coindesk_proxy_riding/`).

## Iteration 5 — config tuning (C-sweep) + throughput measurement + prod config

After the watchdog (Iteration 4) made runs hang-safe, this iteration measured the load-vs-concurrency
curve and the real verified-URL throughput, and decided the production config. (Engine still dev-only
here; the src/ port is covered in a later session.)

### Hang corrected, not a stall

The Iteration-3 "result pending" 20×6 run did NOT self-terminate — the operator aborted it after ~12 h.
It hung exactly as Iteration 4 describes (cooperative stall-check unreachable while all slots are
suspended on wedged-browser awaits). No throughput data came from it.

### Load-vs-concurrency sweep (isolated, clean)

The binding constraint at scale is **CPU**, not RAM: each context is its own Chromium renderer process,
so renderers = total concurrency C; junk-proxy contexts are cheap connect-fail churns (~100 MB, most
never render). Machine: 48 GB / 14 cores. Clean isolated numbers (ONE run at a time, killed after a
~60 s sample — overlapping runs contaminate the readings, a lesson learned the hard way mid-session):

| Concurrency C | CPU busy |
|---|---|
| 16 (2×8)  | ~30% |
| 64 (4×16) | ~55-60% (peaks ~70%) |
| 120 (the original choke) | ~97% (saturated) |

~Linear (~0.64%/context above a ~15% baseline). **Browser count is minor** (fixed infra-process set per
browser); the renderers (= C) are the load. Redistributing B↔C at constant C does NOT cut load — only
lowering C does. (Initial 20→6 browser change at constant C=120 barely helped — the misstep that
surfaced this.)

### Verified-URL throughput

A C=64 (4×16) run: **280 verified URLs (ok) in 12 min 13 s → ~23/min average, ~28-30/min in the steady
minutes** (per-minute raw-write counts, NOT collapsing — highest at the end). 93% of fetch attempts are
connect-fails on dead proxies = the churn cost, not a blocker; at C=64 the engine churns fast enough to
sustain ~23-30/min. **61k projection ≈ 35-45 h.** Throughput is **proxy-supply-bound, not
concurrency-bound** — the 2×8 smoke already projected ~33 h, so higher C buys little speed but more CPU.

### Production config

- **C = 64 (4 browsers × 16 contexts)** — ~55% CPU, ample headroom, negligible RAM, clean teardown.
  Chosen for utilization+safety margin, not raw speed (proxy-bound above ~64).
- **Stall timeout 300 s (5 min), not 3600.** At ~23/min, 5 min of zero raw is unambiguously stuck. The
  tail (few URLs left → naturally larger gaps) is handled by `remaining_urls.txt` + re-queue, NOT by
  tail-aware logic — a "too-early" abort is cheap (stragglers defer to the next run). Tighten from real
  long-run gap data later.
- **Pool shuffle.** The pool was consumed sequentially in repo-order (`_next_proxy` cursor over the
  repo-concatenated pool) → early quality depended on whichever repo was first. `random.shuffle` at
  pool-load removes the repo-order bias and avoids long junk-streaks from one bad repo → consistent
  pool quality + steadier good-proxy supply (does not raise average quality, only removes front-load
  variance).
- **socks4 stays filtered** (`BROWSER_ELIGIBLE_PROTOS = {http, socks5}`) — technical limit (Playwright
  cannot drive socks4), not a tuning choice.
- **Alive-feeder NOT reintroduced** — alive ≠ delivers-the-target (rejected earlier, also dropped for
  The Block); drive proxy throughput at the target directly.

These values become the `RidingScrapeConfig` defaults in the src/ port.
