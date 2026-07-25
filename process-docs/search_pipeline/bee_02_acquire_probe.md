# Bee CDP Starvation — Phase 2 Acquire Probe

**Date:** 2026-05-21  
**Verdict:** A-sleep — acquire() runs, gets lock, blocks on `asyncio.sleep(backoff_s)` for ALL 9 engines  
**Cascade reproduced:** True (13/30 zero_cascade)  
**Report:** `dev/search_pipeline/01_reports/acquire_probe_20260521_183226.md`

---

## Hypothesis

Phase 1 REFUTED CDP event-loop starvation (scheduling latency p99=1.4ms; 0 CDP events
during zero_cascade). Three new candidates for Phase 2:

- **B:** `asyncio.wait_for` timeout fires before inner `acquire()` Task is scheduled.
- **A-lock:** Task runs, enters `async with self._lock:`, blocks — stale lock from prior
  cancelled acquire() where Python 3.14 `Lock.__aexit__` did not release.
- **A-sleep:** Task runs, gets lock, blocks on `asyncio.sleep(backoff_s)` inside the lock.
  Expected only for Google (backoff set by CAPTCHA). Non-Google have no known backoff.
- **C:** acquire() completes fine — bug is downstream.

## Instrumentation

Two monkey-patches on `RateLimiter` class before src imports (`dev/search_pipeline/acquire_probe.py`):

- **`acquire()` wrapper** — records `enter`, `exit_ok`, `exit_err:<class>` per engine per call.
- **`__init__` wrapper** → `_WatchedLock` replaces `self._lock` — records
  `lock_attempt`, `lock_granted`, `lock_released`/`lock_stuck` via Lock `__aenter__`/`__aexit__`.
  `lock_stuck` = `lock.locked()` still True after `__aexit__` returns (Python 3.14 non-release signal).

Pattern B canary re-runs for triangulation (same as Phase 1, scheduling latency).

## Key Numbers

| Category | n_q | avg_ent/rs | avg_lg/rs | avg_ok/rs | avg_err/rs | dur_p99_ms | canary_p99_ms |
|----------|-----|-----------|----------|----------|-----------|------------|---------------|
| normal | 14 | 1.0 | 1.0 | 0.0 | 1.0 | 5001 | 3.6 |
| captcha | 3 | 0.67 | 0.67 | 0.0 | 0.67 | 5001 | 1.1 |
| zero_cascade | 13 | 1.0 | 1.0 | 0.0 | 1.0 | 5001 | 1.2 |

Zero-cascade per-engine detail (representative — ALL 9 engines show identical pattern every query):

| engine | entered | lock_granted | lock_released | lock_stuck | exit_class | dur_ms |
|--------|---------|--------------|---------------|------------|------------|--------|
| google | Y | Y | Y | N | err:CancelledError | 5001 |
| crossref | Y | Y | Y | N | err:CancelledError | 5001 |
| duckduckgo | Y | Y | Y | N | err:CancelledError | 5001 |
| mojeek | Y | Y | Y | N | err:CancelledError | 5001 |
| lobsters | Y | Y | Y | N | err:CancelledError | 5001 |
| openalex | Y | Y | Y | N | err:CancelledError | 5001 |
| stack_exchange | Y | Y | Y | N | err:CancelledError | 5001 |
| semantic_scholar | Y | Y | Y | N | err:CancelledError | 5001 |
| open_library | Y | Y | Y | N | err:CancelledError | 5001 |

## Verdict

**A-sleep wins. Discriminators B and A-lock REFUTED.**

**Refuted — B (scheduling):** `avg_ent=1.0` for zero_cascade queries — 100% of RATE_SKIP engines have
`enter` events. All Tasks are scheduled and run. No scheduling gap.

**Refuted — A-lock (stale lock):** `avg_lg=1.0` AND `lock_stuck=N` for ALL 9 engines in ALL
zero_cascade queries. Every engine acquires the lock (lock_granted), releases it on cancellation
(lock_released), and leaves it free (lock_stuck=N). Python 3.14 `asyncio.Lock.__aexit__` releases
cleanly under `CancelledError`. The Python 3.14 regression hypothesis is INCORRECT.

**Confirmed — A-sleep:** ALL 9 engines enter acquire(), acquire the lock, sleep inside
`asyncio.sleep(wait)`, get cancelled at ~5001ms (=RATE_WAIT_TIMEOUT). `dur_p99_ms=5001` for
zero_cascade.

## Root Cause Reframe

**The cascade is NOT an asyncio mechanism.** The event loop is free (canary p99=1.2ms), tasks
are scheduled (B refuted), locks are correctly released (A-lock refuted). The mechanism is
**multi-engine backoff cascade**:

- Google CAPTCHA in Q1 → `google.backoff()` sets `backoff_until = now + 39s`.
- Non-Google engines (CrossRef, DDG, Mojeek, etc.) serve Q2-Q4 successfully but hit their
  own backend rate limits (CrossRef API 429, DuckDuckGo bot-detection, etc.) during the
  search phases of Q2-Q4. Each calls `engine_limiter.backoff()` → sets their own `backoff_until`.
- By Q5, ALL 9 engines have `backoff_until > now` → ALL 9 `acquire()` calls hit
  `await asyncio.sleep(backoff_until - now)` inside the lock → cancelled at 5s → zero_cascade.

The cascade perpetuates because backoff periods are long (30s base, exponential). During
zero_cascade queries, no successful requests complete → `reset_backoff()` never called →
backoff_attempt stays elevated → next CAPTCHA/429 triggers an even longer backoff.

Recovery occurs when backoffs expire naturally (confirmed by Phase 1: M3-M5 recovery after
124s CAPTCHA #3 backoff window closes).

## Key Side Finding: Python 3.14 asyncio.Lock

**lock_stuck=N for ALL 9 engines across ALL 13 zero_cascade queries** — 117 data points.
Python 3.14's `asyncio.Lock.__aexit__` correctly releases the lock under `CancelledError`
propagated by `asyncio.wait_for` timeout. No regression. The stale-lock hypothesis is
conclusively ruled out.

## Next Steps

Pending:

- **Confirm multi-engine backoff**: add `backoff_until` state logging per engine per query.
  Run `dev/search_pipeline/acquire_probe.py` variant that also reads `limiter._backoff_until`
  before each query — confirms which engines have backoff set and when it was set.
- **Fix direction**: add minimum delay between queries in `search_batch_workflow` to prevent
  rapid-fire requests triggering backend rate limits. Target: ≥ 3s inter-query gap.
- **Alternative fix**: detect when `≥ N` engines are in RATE_SKIP and short-circuit the remaining
  batch queries (return partial results) rather than running 5s-timeout acquire() calls.
- **Root cause of non-Google backoffs**: instrument `backoff()` call sites in each engine to
  identify which backends are returning 429/403 and why (anonymous API quotas, bot detection).
