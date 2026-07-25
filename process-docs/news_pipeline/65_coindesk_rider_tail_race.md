# 65 — CoinDesk rider tail-starvation: slot racing at the tail

**Branch:** `coindesk-watchdog`. This corrects `_run_slot` in the CoinDesk proxy-riding src/ port. TheBlock's proxy_pool loop had an earlier tail-race fix on the same concept.

## Problem

The inner `while burn_count < state.burn_threshold` loop in `_run_slot` pulled URLs via
`await asyncio.wait_for(state.url_queue.get(), timeout=10.0)`. Each URL exists in the queue
exactly once. When unresolved URLs < n_slots (64), surplus slots timeout after 10 s and
`continue` — spinning idle while the handful of active slots process one URL each per cycle.
Observed in a real 500-URL run: the last ~45 URLs produced a ~400 s plateau (sequential
proxy-per-URL per 10 s cycle). Worst case: a wedged URL with bad luck on proxy assignment
fires the stall watchdog.

## Concept (mirrors the earlier TheBlock fix)

TheBlock's `proxy_pool` loop had the identical tail-starvation: when pending < concurrency,
126 of 128 slots sat idle, stubborn URLs got exactly one proxy per round. Fix there: replicate
open URLs round-robin across free slots so every open URL gets parallel proxy coverage.

The rider is queue/slot-based (not batch-synchronous like proxy_pool), so the fix is different
in location but identical in intent: surplus slots that find the queue empty immediately race an
open URL with their current proxy — no 10 s wait.

## Mechanism

### New `RiderState` fields

| Field | Type | Default | Purpose |
|---|---|---|---|
| `target_urls` | `frozenset` | required | All distinct target URLs; open = `target_urls − done_urls`. |
| `done_urls` | `set` | `field(default_factory=set)` | URLs written to raw/; first-writer guard; drives `all_resolved`. |

Passed from `scrape_entries_riding` (which has `urls = [e["url"] for e in entries]`) to
`run_riding_pool` → stored in `RiderState`.

### `all_resolved` — new definition

```python
return len(self.done_urls) >= len(self.target_urls)
```

Replaces `url_queue.empty() and in_flight == 0`. With racing, `in_flight` can count multiple
fetches of the same URL; queue-empty is no longer the completion signal. `len(target_urls)` is
the distinct count (frozenset), robust against hypothetical duplicate queue entries.

### `_run_slot` delta (five additions)

**`get_nowait` replaces `wait_for(get(), 10.0)`** — eliminates the 10 s stall at the tail:

```python
dequeued = True
try:
    url = state.url_queue.get_nowait()
    if url in state.done_urls:
        continue    # stale queue entry — already won by a racer
except asyncio.QueueEmpty:
    if state.all_resolved:
        break
    open_list = sorted(state.target_urls - state.done_urls)
    if not open_list:
        break
    url = open_list[slot_id % len(open_list)]
    dequeued = False
```

**`sorted(…)[slot_id % len]`** distributes surplus slots round-robin across open URLs:
50 surplus slots racing 5 open URLs → 10 slots per URL, no thundering-herd on one URL.
`sorted()` gives every slot the same ordering; `slot_id % len` assigns disjoint primaries.

**Stale-dequeue guard** (`if url in state.done_urls: continue`): a URL won by a racer
while it was still in the queue is discarded without fetching.

**First-writer guard** in `status == "ok"` branch:

```python
if url not in state.done_urls:
    state.done_urls.add(url)
    out = _write_raw(_url_hash(url), html, state.output_dir)
    job.file = str(out); state.n_ok += 1; ride_ok += 1
    state.last_progress_mono = time.monotonic()
else:
    print(f"[slot {slot_id}] dup-race discarded …")
    continue    # skip job_records.append
```

`done_urls.add(url)` and `_write_raw(…)` have no `await` between them → atomic in asyncio's
single-threaded event loop. Dup-race winner skips `job_records.append` (no double-count in
reporter stats).

**Requeue guard** in all non-ok branches — only requeue if the URL was dequeued AND not yet done:

```python
if dequeued and url not in state.done_urls:
    state.url_queue.put_nowait(url)
```

Raced URLs (dequeued=False) that fail are not re-enqueued — they remain in
`target_urls − done_urls` and are picked again by the next race cycle. Dequeued URLs that fail
are still requeued as before.

### `scrape.py` change

`run_riding_pool` receives new `target_urls=frozenset(urls)` kwarg. One line added.

## Edge cases

**Fail-before-success (race + dequeue concurrent):** asyncio single-threaded — `done_urls.add`
and `_write_raw` run without interruption between them. If slot A (raced, dequeued=False) fails
and slot B (dequeued=True) succeeds: A's fail → no requeue, B writes → done. If dequeued-A fails
first and requeues: when that copy is eventually dequeued, stale-dequeue guard fires (url in
done_urls from B's write) → skipped. No double-write in any interleaving. ✓

**Stall watchdog unchanged:** `last_progress_mono` advances only inside the first-writer guard
(not on dup-race discards or failures). If all races fail continuously → no progress →
watchdog fires as before. ✓

**No tight spin:** queue-empty → `await _fetch_one_url(…)` is the yield point (page_timeout_ms
= 8 s per URL). Even on fast-fail (connect_fail in ms), proxy burn/fail thresholds
(burn_threshold=2, FAIL_THRESHOLD=2) bound the fast-fail loop to ≤4 fetches before proxy
rotation. Stall check at the outer-while top bounds the no-progress ceiling. ✓

## Test coverage

`dev/news_pipeline/coindesk_proxy_riding/test_tail_race.py` — 5 deterministic cases,
all src/ imports lazy (inside function bodies), `_fetch_one_url` + `_next_proxy` mocked:

| Case | Scenario | Key assertion |
|---|---|---|
| 1 | 2 URLs, 6 slots | done_urls=={A,B}, n_ok==2 (racing, no double-count) |
| 2 | 1 URL, 3 slots all racing | n_ok==1, exactly 1 raw file |
| 3a | url_x pre-done, stale in queue + url_y open | url_x never fetched, url_y done |
| 3b | url_x not done, queue empty, fail then ok | no put_nowait for url_x after raced-fail |
| 4 | 4 URLs, 4 slots, normal path | n_ok==4, 4 raw files, no racing |
| 5 | 1 URL, fail then ok, 1 slot | fetch called twice, n_ok==1, done exactly once |

All 5 tests pass (exit 0). (Suite later extended to 7 — test_6 wedge-after-all_resolved,
test_7 pool refresh, added in subsequent sessions.)

## Live verification (4×16 baseline, 2026-06-20)

Run `--year 2019 --limit 500` at 4 browsers × 16 (n_slots=64), job `20260620T010358Z`:

| Metric | Value |
|---|---|
| OK / Target | 500 / 500 |
| Termination | `all-done` (clean — no hang; watchdog-hang fix from a later session in place) |
| Wall-clock | 1531 s (~25.5 min) — vs the ~2251 s pre-tail-race reference, ~32% faster |
| OK URLs/min | 19.6 → 61k projection ~52 h at 4×16 |
| cumulative.png | constant slope held to URL 500, **no tail plateau** (the ~400 s plateau the tail-race targeted is gone) |

The tail-race is confirmed: every URL resolved, the slow tail eliminated, the run terminates cleanly.
Eligible-pool trajectory from the same run is captured in a subsequent process doc on the refresh-interval evidence.
