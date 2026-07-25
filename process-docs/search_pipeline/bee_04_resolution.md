# Bee CDP Starvation — Phase 4 Resolution

**Date:** 2026-05-21  
**Status:** RESOLVED  
**Production changes:** `src/search/search_web.py`, `src/search/engines/scholar.py`, `src/search/filter_modes.py`  
**Verification:** `dev/search_pipeline/01_reports/pipeline_smoke_20260521_200557.md`

---

## Investigation Arc

### Phase 1 — CDP starvation REFUTED

**Hypothesis:** Chrome CDP events during CAPTCHA navigation create a near-non-yielding event loop busy-loop that starves all 9 engines' `asyncio.wait_for(acquire(), 5.0)` tasks simultaneously.

**Verdict: REFUTED.** Scheduling latency p99 = 1.4ms during zero_cascade (event loop completely free). Zero CDP events during cascade queries — Chrome is silent between queries. CDP mechanism cannot operate.

### Phase 2 — A-sleep confirmed, backoff-cascade narrative INCORRECT

**Hypothesis:** `asyncio.wait_for` timeout fires before acquire() is scheduled (B), OR Python 3.14 `asyncio.Lock.__aexit__` fails to release under CancelledError (A-lock), OR acquire() enters sleep inside the lock (A-sleep).

**Verdict: A-sleep confirmed.** All 9 engines enter acquire(), acquire lock, sleep in `asyncio.sleep(wait)`, cancelled at ~5001ms = RATE_WAIT_TIMEOUT. `lock_stuck=N` for ALL 9 engines across ALL 13 zero_cascade queries — Python 3.14 Lock regression EXCLUDED.

**Inference in Phase 2:** "multi-engine backoff cascade — non-Google engines hit 429/bot-detect during Q2-Q4 and call `.backoff()`". This was NOT probe-verified. Superseded by Phase 3.

### Phase 3 — Tokencap-path wins

**Hypothesis split:** two branches in `acquire()` — backoff (`self._backoff_until > now`) vs tokencap (`len(tokens) >= max_requests`). Phase 2 A-sleep confirmation couldn't distinguish them.

**Verdict: Tokencap-path wins (primary mechanism).** 18/30 zero_cascade queries measured:

- **Type 1 (12/18):** Pure tokencap. ALL 9 engines hit `len(tokens) >= max_requests` (ba=N, tc=Y). After 4 successful queries in <60s, the 5th `acquire()` waits `60s − age_of_oldest_token`. With RATE_WAIT_TIMEOUT=5s, the wait_for cancels at 5s → RATE_SKIP → cascade. Token expiry provides natural recovery (Q5 wait=38.5s → Q11 wait=8.4s → Q12 recovered).
- **Type 2 (6/18):** Mixed. Tokencap for 8 engines + Google backoff independently (CAPTCHA → `limiter.backoff()`). The 8 non-Google engines were in tokencap regardless of Google's state.

**Phase 2 multi-engine backoff narrative INCORRECT.** Non-Google engines (crossref, openalex, stack_exchange, open_library) showed `backoff_sleep_attempt=N` in ALL 18 zero_cascade queries. No 429 or bot-detect calls during the probe run. The immune engines' structural discriminator (no `.backoff()` call in source) proved clean.

---

## Resolution

Three production changes applied in this commit:

### 1. `RATE_WAIT_TIMEOUT` 5.0 → 60.0

Root fix. The outer `asyncio.wait_for(..., timeout=RATE_WAIT_TIMEOUT)` was cancelling legitimate token-bucket waits. With RATE_WAIT_TIMEOUT = WINDOW_SECONDS = 60.0, the wait completes naturally (oldest token expires, acquire() appends new token, engine proceeds). Google's escalated backoff (>60s) still trips the timeout — acceptable single-engine RATE_SKIP, does not cascade.

### 2. Bucket-uniformity invariant

Structural prevention for future filter-mode regressions. `apply_filter_mode()` in `filter_modes.py` no longer restricts the `selected` engine dict. All 9 engines fire on every query; filter modes operate via (a) per-engine query modifiers and (b) post-merge URL filtering only. Bucket state stays synchronized at every point.

### 3. Scholar fully removed

Scholar was dormant in `_DEFAULT_ENGINES` (not in the default fanout) but still registered in `ENGINES` and `_limiters`. The `_limiters["google_scholar"]` line in `scholar.py` fired at module import (triggered by `search_web.py` importing `ScholarEngine`). With Scholar in `ENGINES` but not in `_DEFAULT_ENGINES`, its limiter was registered but never used — harmless in isolation, but a latent co-fire trigger if `_DEFAULT_ENGINES` is ever widened. Fully removed to give pooling-rework a clean slate.

---

## Verification

`dev/search_pipeline/01_reports/pipeline_smoke_20260521_200557.md` — 20 queries, 9 engines:

- **RATE_SKIP = 0** across all 20 queries and all 9 engines (confirmed via timing checkpoints Q4/Q8/Q12/Q16/Q20)
- **20/20 queries with results**
- **Total wall: 294.3s ≈ 4.9 min** (within expected 4-5 min for 20 queries at 4/min per engine)
- Per-engine aggregate: all 9 engines appear with non-zero OK counts; no cascade entries

---

## Remaining open items (not this commit)

- **merge.py hygiene:** `ACADEMIC = {"google_scholar", ...}` and `ACADEMIC_PRIORITY = {"google_scholar": 2, ...}` are inert dead references. Follow-up hygiene pass.
- **Pooling-rework:** Scholar re-integration path. `scholar.py` HTTP logic preserved in tree.
- **`max_requests` per-engine:** currently 4 (hardcoded in each engine). Module default is 10. With RATE_WAIT_TIMEOUT=60 the tokencap wait is now bounded and recoverable — `max_requests` tuning is a separate optimization, not urgent.
