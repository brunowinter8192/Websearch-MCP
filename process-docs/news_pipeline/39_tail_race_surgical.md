# 39 — Tail-race: surgical delta to run_loop (correct next step)

## Origin

Prior process history documented the intended surgical fix and why the earlier rewrite-attempt regressed
to 2/64. The correct next step was quoted verbatim: "Port ONLY the tail-race into `run_loop` as a
surgical delta." This file documents that delta.

## Problem

The sustained batch loop (`p4_loop.run_loop`) is batch-synchronous: each round waits for its slowest
future among `concurrency` slots before the next round starts. When only 1–2 sub-sitemaps remain
pending, `_build_batch` exhausts `url_iter` after 1–2 assignments; the other 126 of 128 slots sit
idle. A stubborn remaining URL gets exactly ONE proxy per ≤15s round — strictly sequential. On the
64er this dragged total wall time to ~18.6 min. The straggler tail fires on every run when pending
URLs < concurrency (i.e., the last O(concurrency) URLs of any large target set).

One file was touched: `dev/news_pipeline/theblock/acquire_pipe/p4_loop.py`.

## Three Changes

### Change 1 — `_build_batch` Phase 2 (tail-race distribution)

After the existing Phase 1 loops (wset-first, then buf, each proxy gets the next distinct URL from
`url_iter`), add Phase 2:

```
if len(batch) < concurrency and batch:
    pending_urls = [url for _, _, url in batch]   # distinct URLs from Phase 1
    url_idx = 0
    for proto, hp in list(wset) + buf:
        if len(batch) >= concurrency: break
        if (proto, hp) in assigned_proxies: continue
        batch.append((proto, hp, pending_urls[url_idx % len(pending_urls)]))
        assigned_proxies.add((proto, hp))
        url_idx += 1
```

Guard fires only when url_iter ran out before filling all concurrency slots AND at least one URL was
assigned. Iterates `list(wset) + buf` (wset-first, same priority order as Phase 1), skips already-
assigned proxies via `assigned_proxies`. Cycles `pending_urls` round-robin. Normal path (enough URLs
to fill all slots) is untouched — `len(batch) < concurrency` is false.

### Change 2 — `n_urls_consumed` for popleft count

```python
# was:  for _ in batch: queue.popleft()
n_urls_consumed = len({url for _, _, url in batch})
for _ in range(n_urls_consumed):
    queue.popleft()
```

In Phase 2, some URLs appear multiple times in `batch`. The set deduplicates to the count actually
consumed from the front of the queue (= Phase 1 batch size). In the normal path all URLs are distinct
so `n_urls_consumed == len(batch)` — identical to the original.

### Change 3 — Post-loop re-queue with `batch_done` / `batch_failed`

**In-loop (result processing):**
- `batch_done: set[str]` — success branch: `if url not in batch_done: batch_done.add(url); content_handler(...); done.append(url)`. Guards first-success-wins. Proxy accounting (`wset.add`, `psuccess`, `_consec_fail.pop`) stays **unconditional** — a success counts for that proxy regardless.
- `batch_failed: set[str]` — failure branch: `batch_failed.add(url)`. Proxy accounting (2-strikes, burn) stays **unconditional**.

**Post-loop (after all futures settled):**
```python
for url in batch_failed:
    if url not in batch_done:
        queue.append(url)
```

## Why Post-Loop Instead of In-Loop

The initial plan was to guard re-queue in-loop:
```python
# first attempt (wrong):
if url not in batch_done and url not in batch_requeued:
    queue.append(url)
    batch_requeued.add(url)
```

This fails at the tail: `as_completed` delivers futures in completion order. A bad proxy fails fast
(~125ms connection-refused/CF-403); a good proxy takes 1–8s for the real fetch. So at the tail, a
fail-future for URL X arrives IN-LOOP before the success-future for the same URL X. With the in-loop
guard: fail-future sees X not in `batch_done` → `queue.append(X)`, `batch_requeued.add(X)`. Later,
success-future → `batch_done.add(X)`, `done.append(X)`. Result: X in both `done` and `queue`. Next
round re-fetches X → duplicate in `done`. Bounded (at most 1 extra fetch per URL) but fires on
practically EVERY tail URL, which is the exact case being optimized.

Post-loop eliminates the ordering dependency entirely: by the time re-queue runs, `batch_done` is
complete. `batch_failed` as a set gives at-most-once per URL automatically. Post-loop pass checks
`url not in batch_done` — any success anywhere in the batch blocks the re-queue, regardless of when
it arrived relative to the fails.

## Unchanged Machinery

All load-bearing machinery is byte-for-byte unchanged in behavior:
- **Proxy-reuse / wset**: wset-first in Phase 1 AND Phase 2; `wset.add(key)` unconditional on success
- **2-strikes burn**: `_consec_fail[key]` + `cm.mark_burned` + buf filter — all unconditional per proxy
- **Cooldown**: `p2_cooldown.py` untouched
- **Buffer**: `build_active_buffer` / `refill_buffer` / `p6_buffer.py` untouched
- **60-min pool refresh**: tick unchanged
- **Exhaustion wait**: `_compute_sleep` + sleep + refresh block unchanged
- `p2_cooldown.py`, `p6_buffer.py`, `acquire_pipe.py`, `p3_target.py`, `p5_logger.py`, `p4_race.py` — not modified

## Verification

Mocked smoke (`/tmp/tail_race_smoke.py`, throwaway — not committed). All 5 points green:

1. **Tail batch has racers**: `_build_batch` with 2 URLs, 8 proxies → batch=8, url_X×4, url_Y×4.
2. **First-success-wins**: done has each URL exactly once; `content_handler` called once per URL.
3. **No spurious re-queue**: gap is empty; failed racers on already-done URL do not re-queue it.
4. **Normal path unchanged**: 8 URLs × 8 proxies → all distinct, no racing.
5. **Fail-before-success ordering**: url_A's fail (0.02s) arrives before its success (0.12s) in
   `as_completed`; url_A ends up in `done` exactly once and NOT in `gap`.

```
=== Tail-Race Smoke ===

[1] PASS  batch=8, url_X×4, url_Y×4  — surplus slots race the same pending URLs
[4] PASS  normal path: 8 URLs × 8 proxies, all distinct, no racing
    done=['url_A', 'url_B']  gap=[]  handler_calls=['url_A', 'url_B']  url_B total fetch calls=6
[2] PASS  done has each URL exactly once; content_handler called once per URL
[3] PASS  no spurious re-queue; gap is empty
[5] PASS  fail-before-success: url_A done exactly once despite fail arriving before success

=== ALL PASS ===
```

## Live 64er Run — PENDING

The real 64er run on the curated ~3.4k proxy pool (target: 64/64 sub-sitemaps with shorter wall time
than ~18.6 min) **has not been run yet**. It will be executed by the user. Pass/fail and timing are
unknown. The mocked smoke covers logic correctness; the live run covers performance and real-proxy
behavior.
