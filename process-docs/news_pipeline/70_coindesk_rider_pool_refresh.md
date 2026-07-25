# 70 — CoinDesk rider: pool refresh (60 min → 30 min)

**Branch:** `riding-report-trim`.
A prior session set up the initial pool load + scrape.py structure and added the eligible-pool-over-time
metric to job.md; the refresh will now appear as eligible-pool jumps in the 10-min window table.

## Problem

`scrape_entries_riding` (`scrape.py`) loads the pool once at job start via `load_backfill_pool()`,
filters to `BROWSER_ELIGIBLE_PROTOS = {"http","socks5"}`, shuffles. The pool snapshot is static for
the entire run.

The risk over a multi-hour backfill (~74 h projected) is NOT hard exhaustion. The 60-min cooldown
recycles burned proxies, so the eligible set reaches a steady state (~`burn_rate × cooldown_window`
in cooldown at any moment) and never hits zero. Measured: the 2251 s / ~500-URL run burned 9559
proxies ≈ **255/min** (NOT 64 — 64 is `n_slots`, not a rate), and eligible bottomed at ~16k of ~26k —
no exhaustion in that window.

The real risk is **live-fraction decay**. The static snapshot's live proxies die over the hours, while
the source lists rotate in new live proxies the rider can never pull in. Cooldown recycling only
re-tries the SAME (increasingly dead) proxies — it adds no fresh supply. So over a long run the live
fraction of the eligible set monotonically drops → more wasted fetches on dead proxies → throughput
degrades. A 60-min re-fetch re-aligns the pool with the current live source-list state (drops proxies
that died and fell off the lists, adds new ones), holding the live fraction up. The eligible-pool
metric makes this visible: each refresh shows as an eligible jump in the 10-min window table.

TheBlock's `proxy_pool` engine refreshes every 60 min via `pool_provider()` in `run_loop`
(`src/news/engine/proxy_pool/loop.py`, `REFRESH_INTERVAL_S = 3600`). The rider had no equivalent.

## Mechanism

### Import structure — pool_provider callable

`rider.py` cannot import from `scrape.py` (circular: `scrape.py` → `rider.py` at top level). Instead,
`scrape.py` defines a shared async helper `_pool_provider()` and passes it as a callable to
`run_riding_pool`. The rider watchdog calls `await state.pool_provider()` at refresh time — no import
of `scrape.py` from `rider.py` at any level.

### `_pool_provider()` — `scrape.py`

```python
async def _pool_provider() -> list[tuple[str, str]]:
    loop        = asyncio.get_running_loop()
    raw_pool, _ = await loop.run_in_executor(None, load_backfill_pool)
    pool        = [(p, hp) for p, hp in raw_pool if p in BROWSER_ELIGIBLE_PROTOS]
    random.shuffle(pool)
    return pool
```

Used for BOTH initial load (`proxy_pool = await _pool_provider()` at scrape start) AND as the
`pool_provider` arg to `run_riding_pool`. Single code path — init and refresh stay in sync on filter
and shuffle without any duplication.

### `RiderState` + `run_riding_pool` — `rider.py`

`RiderState` gains `pool_provider: object = None` (optional, default None = static pool — backward
compatible). `run_riding_pool` gains `pool_provider=None` param threaded to state. `POOL_REFRESH_INTERVAL_S`
constant in INFRASTRUCTURE: initially `3600.0` (mirrors `loop.py`); tightened to `1800.0` (30 min)
after baseline measurement — see below.

### Refresh in `_watchdog` — poll loop order

```
await asyncio.sleep(interval)
1. append pool sample
2. if pool_provider and monotonic() - _last_refresh_mono >= POOL_REFRESH_INTERVAL_S:
       new_pool = await state.pool_provider()
       if new_pool:
           state.proxy_pool = new_pool          ← atomic single assignment
           _last_refresh_mono = time.monotonic()
           log("pool refresh: {old_n} → {new_n} proxies")
       else:
           log("pool refresh returned empty — keeping current pool")
3. if all_resolved: (clean return or _abort_done)
4. if idle > stall_timeout_s: _abort_stall
```

`_last_refresh_mono = time.monotonic()` captured before the `while True` loop — at watchdog start,
which is approximately job start (constructed immediately after `run_riding_pool` begins).

**Atomic replace safety:** `state.proxy_pool = new_pool` is a single STORE_ATTR bytecode. asyncio is
single-threaded and cooperative: while `await state.pool_provider()` suspends the watchdog, slot tasks
run and read the OLD `state.proxy_pool` through `_next_proxy` / `eligible_candidates`. After the await
returns, the assignment executes without interruption before any slot resumes. `proxy_cursor` uses
`% len(eligible)` (from `eligible_candidates` on the new pool) — wraps naturally. No `proxy_lock`
needed: the lock guards cursor advancement only, not the pool reference.

**`cooldown_mgr` persistence:** not reset on refresh. A burned proxy that reappears in the new list
stays excluded by `eligible_candidates` until its 60-min cooldown expires. This is correct — a proxy
burned in this job was unreliable; its slot in the new source list doesn't undo that.

**`run_in_executor` cadence:** `load_backfill_pool()` takes ~1 s (multi-source HTTP fetches run in a
thread via `run_in_executor(None, …)`). During that 1 s the watchdog coroutine is suspended; slot tasks
run normally. Stall detection is time-based — a 1 s delay in one poll iteration is immaterial.

**Empty pool guard:** `if new_pool:` — if all sources fail (network outage), skip assignment, log
warning, keep current pool. Prevents a failed refresh from clearing the pool.

### Eligible-pool metric

`state.pool_samples` is appended BEFORE the refresh check (step 1). The pre-refresh eligible count
is recorded; the new count appears in the NEXT poll sample. In the 10-min window table the refresh
shows as a jump in `avg_eligible` / `min_eligible` — exactly the intended signal.

## Interval tightened: 3600 s → 1800 s (30 min)

**Baseline run:** job `20260620T010358Z`, config 4 browsers × 16 slots = 64 concurrent.

Key measurements from `job.md`:
- Browser-eligible pool at job start: **19,576** (http + socks5 only — NOT the raw 23-26 k total;
  other protocols filtered by `BROWSER_ELIGIBLE_PROTOS`).
- Completed URLs in 1,531 s: 8,627 → burn rate **≈ 338 proxies/min** (each proxy burned once
  and enters 60-min cooldown).
- Extrapolation: at 60 min, cumulative burned ≈ 338 × 60 = **20,280 proxies** in cooldown.
  19,576 eligible < 20,280 → the eligible set would hit zero around t ≈ 58 min, just before
  the 60-min refresh would fire. The rider would stall on an empty eligible pool in the last ~2 min.
- At 30 min: cumulative burned ≈ 338 × 30 = **10,140** in cooldown → 9,436 eligible remain → safe margin.
  Pool refresh at t=30 re-injects the full live source-list snapshot; cooldown recycling then
  starts returning burned proxies (first batch at t=60, 30 min after they were burned).

**Cooldown stays at 60 min** (`cooldown.py` — unchanged). 30-min refresh and 60-min cooldown are
orthogonal: refresh widens the eligible pool; cooldown controls re-use of burned proxies.

**Validation target:** 5 browsers × 16 slots = 80-slot run. Burn rate expected ~5/4 × 338 ≈ 422/min.
At 30 min: ~12,660 in cooldown → 6,916 eligible still safe. If burn rate scales higher, interval
may need further tightening; will update after the next production run.

## Test

`test_7_watchdog_pool_refresh` added to `dev/news_pipeline/coindesk_proxy_riding/test_tail_race.py`:

- `pool_a` (2 entries) → initial `state.proxy_pool`.
- `mock_provider` async callable → returns `pool_b` (3 entries); `refresh_count[0]` incremented.
- `POOL_REFRESH_INTERVAL_S` patched to `0.0` → first poll always satisfies the interval check.
- `state.done_urls = {url_done}`, `all_resolved=True`, `in_flight=0` → watchdog returns cleanly after refresh.
- `poll_interval=0.05 s` → test completes in ~50 ms.
- Assertions: `refresh_count[0] >= 1`; `state.proxy_pool is pool_b` (identity — same object returned by provider).
- Result: PASS (7/7 total).
