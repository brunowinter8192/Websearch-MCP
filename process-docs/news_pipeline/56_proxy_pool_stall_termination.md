# 56 — Proxy-pool scrape loop: global stall-termination

**Date:** 2026-06-18. **State:** design decided (chat-derived); implementation in `loop.py` by worker.
**Resolves:** non-termination on persistent-fail URLs, documented in the poison-URLs backfill entry.

## Problem (recap)

`run_loop` (`src/news/engine/proxy_pool/loop.py`) terminates only when every queued URL resolves
to `done` (fetched) or `dead` (404/410). A failed fetch re-appends the URL to the back of the queue
(`queue.append(url)`). URLs that are NEITHER fetchable NOR origin-dead (The Block's 8 poison URLs:
mis-encoded slugs / CF-hard) rotate forever → the queue never empties → the loop never terminates.
Last full run: ~3h of zero new fetches at the tail (~19,963 `fail` vs ~0 success per 20k events),
killed after 21h. There was no per-URL terminal "failed" state.

## Decision

A **global stall-detector**, NOT per-URL proxy-weighting and NOT a per-URL attempt-cap.

- Track `_last_progress` (monotonic), updated whenever a URL resolves to **done OR dead** (i.e. when
  the queue actually shrinks). A `fail` does NOT update it (the URL is re-queued; queue does not shrink).
- In the `while queue:` loop, if `now - _last_progress >= STALL_TIMEOUT_S` (= 3600s, one full pool
  refresh/cooldown cycle) → `break`. The loop returns `gap = list(queue)` = every still-unresolved URL.
- `gap` flows through the existing chain unchanged: `_build_manifest` marks those URLs `status="failed"`
  → `_update_blocked_urls(raw_dir, manifest, {"dead":"dead_urls.txt","failed":"failed_urls.txt"})`
  appends them to `data/news/{name}/raw/failed_urls.txt`. The two block-lists the user asked for:
  `dead_urls.txt` (origin 404/410) + `failed_urls.txt` (persistently unreachable).

Threshold `STALL_TIMEOUT_S = 3600` = `REFRESH_INTERVAL_S` = `COOLDOWN_S`: after a full cycle, a fresh
pool has loaded AND every cooled-down proxy has returned — zero progress across that cycle = the
remaining URLs are genuinely unreachable.

## Why this, not the alternatives

**Rejected — per-URL distinct-proxy attempt-cap (abandon after N distinct proxies fail a URL).**
The user vetoed proxy-weighting. It also has real downsides the stall-detector avoids:

- **Bulk-safety by construction.** The bulk phase always produces successes (clean run: hundreds of
  URLs complete per 60-min window — URLs-handled 2939→2277→1507→310 over 4 windows). So the stall timer
  NEVER fires in the bulk. An attempt-cap, by contrast, needs a queue-independent N tuned to avoid
  abandoning the slow-but-fetchable middle (in the bulk a URL gets only ~1–2 distinct proxies per window
  because it rotates to the queue tail after each fail; a 1-window time cap would have abandoned most of
  the corpus).
- **Preserves a slow-but-progressing tail.** As long as ANY remaining URL keeps resolving, `_last_progress`
  moves and the loop continues — the stubborn tail grinds to completion. An attempt-cap would wrongly abandon
  a slow-but-fetchable tail URL once it crossed N proxy attempts (the tail-race hammers each leftover URL
  with ~128 proxies/batch, so N is reached in minutes regardless of fetchability).
- **Minimal + queue-independent.** One global timer, no per-URL bookkeeping, no arbitrary N, no proxy
  weighting. Fits the existing queue algo and the already-wired `failed_urls.txt` machinery — the only
  file touched is `loop.py`.

The signal is also the strongest available: the empirical fail-pattern of the last run was a 3h flatline.
A full-cycle (60-min) flatline is an unambiguous "nothing left is reachable".

The single cost vs the attempt-cap: at a genuine tail-stall, the loop grinds one full 60-min cycle before
terminating (vs ~1 min for an attempt-cap). One-time, at the very end of a multi-hour backfill → negligible.

## Edge case (accepted)

If the ENTIRE proxy pool collapses (all GitHub source lists 404 at once), 60 min of zero progress is an
infra failure, not dead URLs → those URLs land in `failed_urls.txt` falsely. Mitigation: they are
retryable (next run, no `.md` on disk → re-attempted) AND the pool-source breakdown in `job.md` shows the
collapse explicitly. Not worth guarding against.

## Implementation

`src/news/engine/proxy_pool/loop.py`: add `STALL_TIMEOUT_S = 3600`; init `_last_progress` at loop start;
stall-check at the top of `while queue:` (before the refresh check); update `_last_progress` on the
done-branch and the dead-branch (inside the `if url not in batch_done:` guard, alongside `done.append` /
`dead.append`). No change to `scrape.py` (`_build_manifest`) or `pipeline.py` (`_update_blocked_urls`) —
the gap→failed chain already exists. Behavior documented in `src/news/engine/proxy_pool/DOCS.md`.

## Data backing this

- `data/news/theblock/proxy_pool_logs/acquire_events_20260616T212912Z.jsonl` (178 MB) — the killed-run
  events: the 3h tail flatline.
- `data/news/theblock/proxy_pool_jobs/20260616T180239Z/job.md` — a clean run: per-60-min-window ~18k
  distinct proxies tried, ~37k fetch-attempts, hundreds of successes/window; the 4-window completion
  pattern that proves the bulk always progresses.
