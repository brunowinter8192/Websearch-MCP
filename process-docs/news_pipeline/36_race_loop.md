# 36 — Tail-race: intended surgical change, over-scoped into a regression

## The intended change (small)

The sustained batch loop (`p4_loop.run_loop`) had a **straggler tail**: batch-synchronous
(each round waits for its slowest of 128 before the next), and one-proxy-per-URL-per-round. At the
tail, when 1-2 sub-sitemaps remained, only 1-2 of 128 slots were used — a stubborn sitemap got one
proxy per ≤15s round, strictly sequential. On the 64er this dragged the total to ~18.6 min.

The agreed fix was **surgical**: *fire the 128 always, distribute over the targets, and at the tail
let surplus slots race the remaining URLs (multiple proxies per remaining URL).* One behavior. The
buffer, working-set, 2-strikes, proxy-reuse, cooldown — all of that was working (it got 64/64 on the
curated pool) and was intended to STAY.

## What was actually done (the error)

Instead of a delta to `run_loop`, the whole loop was **rewritten**: `run_loop` replaced by `run_race`
(`p4_race.py`), and the load-bearing machinery dropped — no working-set, no 2-strikes, no reuse, no
cooldown. **Each proxy used at most once.** A from-scratch new design, where only a surgical patch
was wanted. Full retrospective covers the session errors of 2026-06-15.

## Result — REGRESSION

64er race run `20260614T233209Z`: **2 of 64 sub-sitemaps** (vs the old loop's **64/64** on the
SMALLER curated pool 3396). Pool 20478, exhausted in 20s.

- The 20s + clean return (job.md was written) proves the pool was fully consumed: `run_race` only
  returns when all workers exit, and with 62 URLs pending that means proxy-cursor exhaustion → all
  ~20478 tried. 20478 attempts in 20s ⇒ fast failures (~125ms avg: connection-refused / CF-403), NOT
  15s timeouts — that is exactly why it finished so fast.
- 20478 attempts → 2 successes = **0.01%**, ~30× below the probe's implied ~0.3%. Unexplained
  (no-reuse + large `/post/` sitemaps + concurrent CF load are candidates) — and the per-attempt
  JSONL was wiped by `janitor.end_job` (`jsonl_path.unlink()`), so the run could not be dissected.
- **Root cause:** dropping proxy-reuse. In the old loop a single good (CF-passing) proxy fetched many
  sub-sitemaps. With each proxy used once, over 64 targets, the limited good-proxy budget is spent
  before completion. The smaller curated pool WITH reuse beat the larger backfill pool WITHOUT reuse,
  decisively. Reuse was load-bearing.

## State as of this stage (reverted)

- `acquire_pipe.py` reverted to `run_loop` (sustained, working) — point restored.
- `p4_race.py` kept on disk as the continuous-dispatch / tail-race REFERENCE (the "128er" idea).
- Nothing was deleted at any point: `p4_loop` + `p2_cooldown` + `p6_buffer` are byte-for-byte intact;
  the race commit only changed an import in `acquire_pipe.py` and added `p4_race.py`.

## Correct next step

Port ONLY the tail-race into `run_loop` as a surgical delta: when pending URLs < free concurrency
slots, let surplus slots draw the same remaining URLs so several proxies race each leftover; keep the
buffer, working-set, 2-strikes, reuse, cooldown untouched. Then re-run the 64er and verify 64/64 with
no tail. `p4_race.py` is the reference for the distribution logic, not a drop-in replacement.

## Open

- Why 0.01% on the race run — only relevant if the race model is ever reconsidered; with the surgical
  delta on top of reuse, the question is moot (reuse restores the budget).
