# 46 — Pool fetch resilience + job.md source-list + metric fix

## Motivation

A full `theblock` backfill crashed at the 60-min mark after producing 1486 articles cleanly in
the first hour. The scheduled `run_loop` refresh called `pool_provider()` = `load_backfill_pool()`,
which fetches monosans first (sequentially, no error handling). A transient local DNS blip
(`httpx.ConnectError: [Errno 8] nodename nor servname provided`) hit that fetch; the uncaught
exception propagated `load_backfill_pool` → `run_loop` → `scrape_entries_proxy` → `run_pipeline`
→ process crash, losing ~428 queued articles.

Root problem: `load_backfill_pool` was all-or-nothing — one source failure at any point killed
the entire pool refresh and the pipeline with it. The GitHub proxy-list sources are normally
100% reliable; the crash vector is transient network outages (DNS blip, local connectivity spike),
not flaky sources.

Three deliverables addressed this:

---

## D1 — Retry resilience (`pool_retry.py`, `monosans_loader.py`, `pool_loaders.py`, `loop.py`, `platform.py`, `discover.py`)

**What changed:** New `pool_retry.py` with `fetch_with_retry(fn)` — 5 attempts, exponential
backoff 1/2/4/8s (~90s max envelope at `FETCH_TIMEOUT=15`). Applied to all four low-level httpx
fetch functions: `monosans_loader._fetch_json`, `pool_loaders._fetch_bare_txt`,
`_fetch_roosterkid`, `_fetch_proxifly`. Retry is transparent in the normal (no-failure) case.

`load_backfill_pool` restructured from a sequential loader-call loop to a per-URL iteration with
`_try_source(url, fn, entries, sources)`: each URL is fetched independently; if retries exhaust,
the source is recorded as `{ok: False, count: 0}` and the loop continues — never raises. Return
type changed from `list[tuple[str,str]]` to `tuple[list[tuple[str,str]], list[dict]]` (pool +
per-source results). Both call sites in `loop.py` (startup + 60-min refresh), the `platform.py`
type annotation, and `discover.py:_fetch_xml`'s flat-extend of `load_backfill_pool()` were all
updated to unpack the tuple.

**Why:** The 60-min refresh must never be able to crash the pipeline. Retry rides out the blip
(the common failure mode); per-source isolation handles a genuinely dead/renamed URL (the
uncommon case) by skipping that source rather than aborting all fetches.

---

## D2 — Source-list section in job.md (`logger.py`, `loop.py`, `janitor.py`)

**What changed:** New JSONL event type `pool_source` (`{event, url, ok, count, ts}`) emitted by
`AcquireLogger.record_pool_source`. `loop.py` calls it once per source URL immediately after
`record_pool_refresh` at both startup and 60-min refresh. `janitor._group_pool_sources` groups
`pool_source` events by the preceding `pool_refresh` in JSONL order. `janitor._write_md` appends
a `## Pool source breakdown` section at the bottom of `job.md` with one `### Refresh N` subsection
per refresh (0 = startup), each containing a `| URL | Result | Count |` table. A note inline
explains that per-source raw counts sum above Pool size due to cross-repo dedup in
`load_backfill_pool()`. Section is omitted entirely when no `pool_source` events exist, keeping
old JSONL files backward-compatible.

**Why:** With per-source failure isolation (D1), it became important to see WHICH sources failed
in a given run and HOW MUCH each repo contributes to the pool. The job.md is the only persistent
artifact after the JSONL is deleted — this tracking goes there so pool composition and repo health
are visible over time without re-running the fetch.

---

## D3 — Fix "URLs handled" + add Fetch-Versuche column (`janitor.py`)

**What changed:** `_compute_window_stats` previously set `urls_handled = len(win_events)` (total
attempt events). This was mislabeled — the overnight run showed 37381 when ~2003 URLs were the
real target. Fixed: `urls_handled = len({e["url"] for e in win_events})` (distinct target URLs).
The old value (total attempts) is now exposed as `fetch_attempts` and rendered as a separate
`Fetch-Versuche` column in the per-window table. Both signals are preserved: "URLs handled" is
the article-coverage signal; "Fetch-Versuche" is the proxy-economics signal (how many
proxy × URL pairs were dispatched to reach that coverage).

**Why:** The mislabel made it impossible to distinguish "we served 2003 URLs" from "we burned
37381 proxy slots doing it". Separating the two makes the per-window table the complete proxy
efficiency picture.

---

## Tests

`tests/test_proxy_pool.py` — 21 unit tests, all self-contained (synthetic JSONL, mocked httpx, no
network). Staged coverage:
- D3: 6 tests — `_compute_window_stats` distinct-vs-total divergence, two-window split,
  `_write_md` column header + row values.
- D1: 6 tests — `fetch_with_retry` recovery, reraise, no-sleep-on-first; `load_backfill_pool`
  tuple shape, monosans-fail isolation (pool non-empty), per-source count.
- D2: 9 tests — `record_pool_source` JSONL event, `_group_pool_sources` (single/two refreshes,
  empty), job.md section present/absent, dedup note, two-refresh subsections, count values.

---

## Swap empirically verified

The 60-min pool swap in `run_loop` had never been exercised before a full prod run — no prior test
crossed the refresh boundary. Two integration tests added to `tests/test_proxy_pool.py` (23 total,
all green) drive `run_loop` over at least one refresh and assert the state-continuity contract:

**Seams controlled:** `pool_provider` (Mock with side_effect Pool A → Pool B), `fetch_url`
(patched at `loop.fetch_url`, always ok), `time.monotonic` (patched at `loop.time.monotonic` with
a controlled sequence that fires the refresh exactly once after the first batch), `loop._sleep`
(patched, safety net — never called since buf always has proxies). `PersistentCooldownManager`,
`build_active_buffer`, `refill_buffer`, `_build_batch`, `ThreadPoolExecutor` run real.

**What the tests prove (no bugs found — refresh block is correct as written):**

`test_run_loop_refresh_swaps_pool_and_preserves_state` (concurrency=1, Pool A=[A1,A2], Pool B=[B1,B2],
3 URLs, refresh after iter 1):
- `pool_provider` called exactly 2× (startup + refresh). ✓
- All 3 URLs in `done`, `gap=[]` — queue survives the swap intact. ✓
- `record_pool_refresh` called 2× with `[len(Pool_A), len(Pool_B)]`. ✓
- `fetch_url` call #2 (url2, first URL dispatched post-refresh) used proxy `A1:80` (Pool A proxy
  from `wset`) — proves `wset` is untouched by the refresh block (lines 62-68 of loop.py). ✓

`test_run_loop_refresh_fresh_candidates_from_new_pool` (concurrency=3, Pool A=[A1] single proxy,
Pool B=[B1,B2], 4 URLs, refresh after iter 1):
- `pool_provider` called 2×. ✓
- All 4 URLs in `done`. ✓
- Dispatched proxy set contains both `A1:80` (wset survivor) AND at least one of `{B1:80, B2:80}`
  (Pool B proxy from rebuilt buf) — proves `buf` is rebuilt from new pool and fresh candidates are
  immediately active alongside the surviving wset proxy. The iter-2 batch is
  `[(A1,url2),(B1,url3),(B2,url4)]` — all three dispatched in the same ThreadPoolExecutor call. ✓

State locals confirmed to survive the swap (`queue`, `done`, `dead`, `wset`, `_consec_fail`, `cm`);
locals confirmed to be replaced (`pool`, `buf`, `_last_refresh`).

---

## Pending final verification — live backfill across the 60-min boundary

Unit tests prove the swap MECHANICS (state continuity, no crash) but cannot prove runtime
behaviour at scale. The final gate is a real `theblock` backfill over sub-sitemaps 24–27 — sized
to exceed one hour of scraping so it crosses ≥1 real 60-min refresh. Run from `dev` (carries the
fix). What only the live run can confirm:

- A real transient blip at the refresh tick is actually ridden out by `fetch_with_retry` at
  runtime (the unit test mocks the fetch; it does not reproduce a live DNS hiccup).
- Good-proxy replenishment per refresh sustains throughput across multiple hours (the open
  economics question below).
- `job.md` renders the per-refresh `## Pool source breakdown` and the corrected `URLs handled` /
  `Fetch-Versuche` columns on a real multi-window run.

## One-hour economics baseline (from the crashed run — single clean hour)

The crashed run produced exactly one clean hour before dying at the first refresh — the only
backfill economics data to date (its window 1 = the crash boundary, ~132 attempts, NOT a signal):

- Pool **33615** proxies; **17731 distinct tried** in hour 1 (~53% of pool grazed), avg ~2.1
  attempts per distinct proxy.
- **~37500 fetch attempts → 1486 articles landed** = ~4% success per attempt, ~25 attempts per
  delivered article (CF-heavy theblock — most proxies 403/dead/timeout).
- **426 distinct CF-passing proxies** (~2.4% of those tried) carried delivery via reuse (~3.5
  articles each).
- Single-hour extrapolation: ~1486 articles/h → the full ~27k backfill ≈ ~18h IF good-proxy
  supply sustains. NOT verified — depends on per-refresh replenishment, which the pending live run
  is the first to measure (no prior run survived a refresh).
