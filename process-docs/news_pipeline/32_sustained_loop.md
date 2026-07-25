# 32 — Sustained acquire-pipe loop (single-pass → multi-cycle machine)

## Problem

The built `p4_loop` was a SINGLE-PASS loop with an IN-PROCESS cooldown
(`p2_cooldown.CooldownManager`, `time.monotonic()`, resets each run). It drained the readily
available proxies once, then gapped — the 61/64 gap on the sitemap dev-run was
exactly this: within an 11-min run nothing ever became re-eligible (60-min cooldown never elapses
in-run), and there was no persistent state, no pool refresh, no wait.

The original design intent was always a SUSTAINED drain-cooldown machine
("candidate → working/drained → burned → 60min cooldown → eligible again"). The implementation
fell short of the design. This theme builds the sustained machine.

## Confirmed spec (user ↔ Opus, this session)

1. **Persistent cooldown** — every unique proxy's cooldown lives in the log as a `cooled_at`
   timestamp. Extend the existing `proxy_status_log.json` (git-tracked per-unique-proxy store).
   Eligibility = `now − cooled_at ≥ 3600s` OR never burned. Survives runs/cycles.
2. **Active buffer + batches** — build a buffer of up to 1280 ELIGIBLE proxies (socks4-first) from
   the full pool; fetch 128 concurrently per round; refill the buffer from the pool as proxies burn.
   (1280 = 10× concurrency; both CLI params.)
3. **2-strikes lifecycle** — a passer rides across URLs; **2 CONSECUTIVE fails → burn → cooldown**;
   a success resets the per-proxy fail counter. Uniform: any finished proxy ends in 60-min cooldown.
4. **60-min refresh** — every 3600s re-fetch the full pool and rebuild the buffer from the
   now-eligible set (cooled proxies whose 60 min elapsed are back in).
5. **Wait-on-exhaustion** — when buffer + working-set are empty, do NOT gap; SLEEP until the earlier
   of (next cooldown expiry, next refresh), then continue. Hard wall-time safety cap.
6. **Logging** — the streaming JSONL stays; `proxy_status_log.json` additionally
   carries `cooled_at` = the cooldown source of truth.

Resolved parameters: extend `proxy_status_log.json` (not a 2nd log); 1280 = 10× concurrency;
2-strikes = consecutive (success resets); on full exhaustion wait-and-continue (not gap).

## Build — 5 sequential stages (each committed + reviewed before the next)

| Stage | Commit | What |
|---|---|---|
| 1 | 5ee905b | Persistent cooldown store: `proxy_status_log.load_cooled_at()` + `mark_cooled_batch()`; `p2_cooldown.PersistentCooldownManager` (wall-clock UTC, in-memory cache + dirty set, `flush()` = one I/O per batch). `CooldownManager` alias keeps p4_loop import intact. |
| 2 | aab6eb4 | `p6_buffer.py` (new): `build_active_buffer()` (delegates eligibility+ordering to cm), `refill_buffer()` (immutable top-up, set-dedup). `BUFFER_SIZE=1280`, `DEFAULT_CONCURRENCY=128`. |
| 3 | 91582db | `p4_loop` rewrite: buffer-draw batches, 2-strikes (`_consec_fail` dict, success resets), burn → `cm.mark_burned` + remove from buf/wset, `cm.flush()` once per batch. |
| 4 | 3e9a97c | Outer time-loop: `pool_provider` callback, 60-min refresh tick, wait-on-exhaustion (`_compute_sleep` = min(next cooldown expiry via `cm.earliest_eligible_at()`, next refresh), clamped to cap), `max_wall_s` safety cap. `_sleep` module attr (mockable). |
| 5 | e93f33c | `acquire_pipe.py` wiring: `PersistentCooldownManager`, `pool_fn` (curated/backfill), CLI `--concurrency/--buffer_size/--max_hours/--pool`. `buffer_size` threaded through run_loop. |

### Key design choices
- **Wall-clock UTC, not monotonic** — cooldown must survive process restarts; monotonic resets.
- **Batch flush** — `mark_burned` is in-memory + dirty-set; `flush()` writes the whole log once per
  batch (one I/O regardless of burns/batch). Watch-point: at ~22k log entries a full-rewrite per
  batch is I/O-heavy over a multi-hour run — revisit (flush-every-N-seconds) if it bottlenecks.
- **`pool_provider` callback** — run_loop is decoupled from `curated_sources`; refresh + Stage-4
  smoke mock the provider, no network in unit tests.
- **Additive schema** — existing log entries have no `cooled_at` → treated as never-burned (eligible);
  no migration. `mark_cooled_batch` creates a minimal entry for pool proxies never seen by `record_run`.
- **Single-pass run_loop is gone** — the function is now the sustained loop. `acquire_pipe.py`'s
  default target is still the 64 sub-sitemaps; pointing it at the 26k article URLs is the actual backfill.

## Validation

Per-stage unit tests (no network, prod log untouched): Stage 1 (8 asserts), Stage 2 (8), Stage 3
(6, incl. success-resets-counter proof), Stage 4 (6, incl. wait-on-exhaustion + safety-cap clamp).

**End-to-end smoke (Stage 5, REAL network, temp log, 36s cap):** 5 `/post/` article URLs target,
curated provider, concurrency 64, buffer 256. Result: 5/5 done in 34.3s, 19 attempts / 5 successes /
6 burns, **all 6 burned proxies written to the log with `cooled_at`** — persistent cooldown verified.
Temp log deleted, prod `proxy_status_log.json` untouched.

**NOT yet validated:** the actual sustained multi-cycle behavior over hours (60-min refresh tick,
wait-on-exhaustion across a real cooldown window, safety-cap on a long run) is only unit-tested with
mocked time/provider — no real multi-hour run yet.

## Next
- The real backfill run: `acquire_pipe.py --pool backfill --max_hours N`, target = the 26k article
  URLs (not the sitemaps) — which is simultaneously the real sustained-economics measurement (B,
  fail/success, throughput-over-time on the 22k pool over real cooldown cycles).
- Watch the per-batch log-rewrite I/O at 22k entries; switch to flush-every-N-seconds if needed.
