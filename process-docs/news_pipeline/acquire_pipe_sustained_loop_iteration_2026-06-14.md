# acquire_pipe: SUSTAINED Loop + Box/Janitor Layer Iteration, as of 2026-06-14

## Context

`dev/news_pipeline/theblock/acquire_pipe/` — production-candidate acquire pipeline for theblock.co content, fetching a defined TARGET (set of URLs) through a rotating proxy pool using curl_cffi chrome impersonation. Every request is a productive fetch, no separate proxy-check stage.

## Iteration Sequence (commit-anchored)

The SUSTAINED machine (sustained concurrent rotation loop + persistent cooldown) was built in stages, then a box/janitor layer (global lock + job lifecycle) was added on top:

1. Persistent cooldown store — added, later superseded by an in-memory revert (see below). Commit `5ee905b`.
2. Active buffer (`p6_buffer.py`) — commit `aab6eb4`.
3. 2-strikes lifecycle + buffer-draw loop — commit `91582db`.
4. 60-min refresh + wait-on-exhaustion + safety cap — commit `3e9a97c`.
5. `acquire_pipe.py` wiring — commit `e93f33c`.
6. Cooldown reverted to in-memory (undoing the earlier persistence step) — commit `fedc151`.
7. `box_lock.py` — global single-job flock, Mineru pattern — commit `d04dbf2`.
8. `p7_janitor.py` — pool-size logging + matplotlib plot — commit `9934b7c`.
9. Wiring — `box_lock` + janitor integrated into `acquire_pipe.py` — commit `1d7c166`.

## Rationale — Cooldown Persistence Reverted to In-Memory

A persistent (file-backed) cooldown store was tried first, then reverted to pure in-memory tracking. In-memory means each job starts with a fully fresh burn set — no cross-job cooldown inheritance, does not survive process restarts. This was the deliberate final choice: clean slate per job, no file I/O overhead, no stale-state risk between runs.

## Validated Run (as of 2026-06-14)

Run `20260614T190143Z`: 64/64 sub-sitemaps fetched, 47,128 unique article URLs discovered, ~18.6 minutes wall time, pool size 3,396 curated proxies. Persistent output at `acquire_pipe_jobs/20260614T190143Z/`.

Prior sitemap dev-run (single-pass machine, superseded by the SUSTAINED loop): 59/64 sub-sitemaps, 44k URLs (26,003 `/post/`).

## Design Notes Carried Forward

- Two chained targets: DEV-RUN (sitemap index → 64 sub-sitemap URLs → 44,041 unique URLs, 26,003 `/post/`, done) and BACKFILL (26k `/post/` article URLs → article page content, next stage at time of writing).
- `box_lock`: SIGTERM kills the Python process before the `finally` block runs, so the sidecar lock file stays — but the kernel releases the flock itself; the next `acquire()` call recovers via `cleanup_stale()` (dead-PID detection). Not observed as a problem in practice.
- `p7_janitor._write_plot` imports `matplotlib.pyplot` lazily — first call builds the font cache (~1s one-time cost).
- `acquire_pipe_jobs/` is the only persistent output directory; `acquire_pipe_logs/` and `acquire_pipe_reports/` are wiped at job start and end.
