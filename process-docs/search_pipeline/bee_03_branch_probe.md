# Bee CDP Starvation — Phase 3 Branch Probe

**Date:** 2026-05-21  
**Verdict:** tokencap  
**Cascade reproduced:** True (18/30 zero_cascade)  
**Report:** `dev/search_pipeline/01_reports/branch_probe_20260521_192646.md`

---

## Hypothesis

Phase 2 confirmed A-sleep: all 9 engines enter `acquire()`, get lock, sleep, get
cancelled at ~5001ms. Phase 2 inferred backoff-cascade (Google CAPTCHA sets
`backoff_until`, non-Google engines follow suit via their own 429/bot-detect calls).
That inference was NOT probe-verified — Phase 2 instrumentation was a wrapper around
the original `acquire()` and did not distinguish which of the two `asyncio.sleep`
branches fired.

Two branches in `acquire()` (rate_limiter.py):
- **backoff branch** (line 36): `if now < self._backoff_until:` — fires only if engine
  called `.backoff()`. 6 engines have `.backoff()` in source; 4 do NOT.
- **tokencap branch** (line 47): `if len(self._tokens) >= self._max_requests:` — fires
  when 4 tokens in the 60s window. After 4 successful queries in <60s, ANY engine hits this.

Structural discriminator: crossref, openalex, stack_exchange, open_library have NO
`.backoff()` call in engine source. If they show `backoff_sleep_attempt=Y`, an unknown
code path calls `.backoff()` on them — that would be a new finding.

## Instrumentation

- **Layer 1** — `_snapshot_limiters()`: per-engine `{backoff_remaining_s, len_tokens}`
  captured immediately before each `search_web_workflow` call.
- **Layer 2** — `_replacement_acquire()`: full replacement of `RateLimiter.acquire()`
  (NOT a wrapper around original). Byte-identical body + `backoff_sleep_attempt` /
  `tokencap_sleep_attempt` events emitted before each `await asyncio.sleep`.
  Event tuple: `(engine, event, ts_mono, wait_s)`.
- **Layer 3** — canary task (Pattern B, identical to Phase 1+2): scheduling latency.

No `_WatchedLock` / `__init__` patch (Phase 2 proved lock_granted=Y; lock events unneeded).

## Key Numbers

| Category | n_q | avg_backoff_eng/q | avg_tokencap_eng/q | avg_neither_eng/q | canary_p99_ms |
|----------|-----|------------------:|-------------------:|------------------:|:--------------|
| zero_cascade | 18 | 0.04 | 0.96 | 0.0 | 1.2 |

## Verdict

**tokencap-path wins (primary mechanism).** Two cascade types observed across 18 zero_cascade queries:

**Type 1 — Pure tokencap (12/18 queries, incl. ALL 4 immune engines every query):**
ALL 9 RATE_SKIP engines hit the `len(tokens) >= max_requests` branch (ba=N, tc=Y for every engine). Backoff branch never fired. Trigger: 4 rapid normal queries saturate each engine's 4/60s token bucket WITHOUT any CAPTCHA. The cascade is purely mechanical: after 4 successful batch queries in <60s, the 5th acquire() finds 4 tokens, sleeps for `wait = 60s − age_of_oldest_token` (measured: 38.5s at Q5 → decreasing ~5s per cancelled query → 8.4s at Q11). `asyncio.wait_for` cancels at 5s → CancelledError → RATE_SKIP. Recovery when oldest token expires (measured: 7 consecutive zero_cascade queries spanning Q5–Q11 before Q12 recovered).

**Type 2 — Mixed: tokencap (8 engines) + backoff (Google only, 6/18 queries):**
Following a CAPTCHA at Q15, Google's backoff fires (ba=Y, pre_br=30.5→5.4s decreasing). The other 8 engines (including all 4 immune engines) hit tokencap (tc=Y, pre_tok=4). Google's unique backoff is expected — it's the only engine with a `.backoff()` call triggered by EMPTY_BLOCK (CAPTCHA).

**Immune engines NEVER showed backoff** — crossref, openalex, stack_exchange, open_library: ba=N in ALL 18 zero_cascade queries. No unknown `.backoff()` call site. The structural discriminator is clean.

**Phase 2 multi-engine backoff-cascade narrative INCORRECT.** The narrative inferred "non-Google engines hit 429/bot-detect and call `.backoff()` during Q2-Q4". The data shows the opposite: non-Google engines never fired the backoff branch in ANY query. The cascade is token saturation — no 429 or backoff propagation needed. The backoff() calls in non-Google engine source exist but did NOT fire during this probe run.

## Next Steps

Pending:
- **Fix (tokencap):** token saturation is the root cause. Three fix directions:
  (a) raise per-engine `max_requests` from 4 toward the `MAX_REQUESTS=10` default
      (4 was set by each engine's explicit `RateLimiter(max_requests=4, …)` — it suppresses
      the 10/min module default). 10/min means 10 rapid queries before saturation, giving
      much wider headroom for typical batch runs.
  (b) add a minimum inter-query delay in `search_batch_workflow` (≥15s with max_requests=4,
      or ≥6s with max_requests=10) so consecutive queries cannot saturate the window.
  (c) detect pre-acquire saturation (`len(tokens) >= max_requests`) and skip engine
      immediately rather than sleeping 20-40s then getting cancelled at 5s.
- **Token bucket wait decreasing per query** (38.5→8.4s across Q5-Q11) is a recoverable
  cascade: the engine naturally recovers when the oldest token expires. Duration is bounded
  by `window_seconds` (60s) minus the age of the oldest token when cascade starts.
- **Google backoff (Type 2 cascade)** is a secondary contributor, only when CAPTCHA fires.
  Already isolated by Phase 2; backoff duration is the binding constraint for Google
  specifically, not the primary zero_cascade trigger.
