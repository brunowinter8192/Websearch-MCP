# Rate Limiter — Fail-Fast Policy

*Snapshot as of 2026-06 — historical process record; the live current state is the source code, not this file.*

## Current State

`src/search/rate_limiter.py` (52 LOC) implements `RateLimiter` as a **pure token-bucket**. Exponential backoff removed 2026-05-22 (this branch).

**Token-bucket pacing:** sliding window `MAX_REQUESTS=10` per `WINDOW_SECONDS=60.0`. Per-engine singletons configured at module import time (e.g. `google.py` sets `max_requests=4, window_seconds=60`). `acquire()` waits for the oldest token to expire if the window is at capacity — normal rate management, not retry-after-failure.

`acquire()` has one code path: remove expired tokens → if at capacity wait for oldest to expire → append new token. No `_backoff_until` check, no sleep-on-failure. `RateLimiter` has no failure state: `_tokens` (sliding window timestamps), `_lock`, `_max_requests`, `_window_seconds` only.

**Fail-fast on CAPTCHA/429/Block:** engine detects failure → returns `([], S.EMPTY_BLOCK)` or analogous status immediately → `_engine_with_timing` in `search_web.py` records it in `engine_stats` → query log captures it. No retry, no session-scoped memory of the failure. Next query tries the engine again from scratch.

**`RATE_WAIT_TIMEOUT = 60.0`** (defined in `search_web.py`): outer `asyncio.wait_for` guard on `acquire()` calls. Fires if the token-bucket wait exceeds 60s → engine returns `RATE_SKIP` for that query. Under normal 4 req/min load this is dormant; it guards against genuine bucket saturation and asyncio event-loop starvation. Raised from 5.0 → 60.0 on 2026-05-21 after a Phase 3 probe identified tokencap-wait (not backoff) as the primary cascade mechanism.

**Bucket-uniformity invariant:** All 9 active engines fire on every query. `apply_filter_mode()` in `filter_modes.py` never restricts which engines participate — `excluded={}` in all code paths. Filter modes (`--books`, `--pdf`, `--docs`) apply per-engine query modifiers and post-merge URL filtering only.

Removed from all 9 engine files: every `limiter.backoff()`, `limiter.reset_backoff()`, orphan `limiter = get_limiter(self.name)` assignments, and `get_limiter` imports where no longer used.

## Evidence

**Pre-rip — backoff waste (2026-05-22, `value_eval_probe.py` 16-pair batch):**

| Pair | CAPTCHA event | Backoff applied | Google result |
|------|---------------|-----------------|---------------|
| 1 | yes | 34s (attempt 0: 30 + 4 jitter) | google=0 |
| 2 | yes | 65s (attempt 1: 60 + 5 jitter) | google=0 |
| 3 | (waited 60s = RATE_WAIT_TIMEOUT) | — | google=0 |
| 4 | yes | 123s (attempt 2: 120 + 3 jitter) | google=0 |
| 5–7 | (waited 60s each) | — | google=0 |
| 7 | yes | 244s (attempt 3: 240 + 4 jitter) | google=0 |
| 8-16 | (all waited 60s) | — | google=0 |

Net waste ≈466s; net benefit zero — Google's bot-detection state does not decay in seconds. Cascade mechanism diagnosed 2026-05-20.

**Post-rip — pipeline smoke baseline (2026-05-22, `dev/search_pipeline/11_pipeline_smoke.py`, 30 queries, language=en, engine_timeout=None):**
Report: `dev/search_pipeline/01_reports/no_backoff_baseline_20260522_211439.md`

Results: **30/30 queries with results**. **0 RATE_SKIP events** across all 30 queries × 9 engines.

Wallclock checkpoints:

| Milestone | Cumulative wall (s) | Avg/query in segment (s) | Engines OK | Engines RATE_SKIP |
|-----------|--------------------:|-------------------------:|-----------:|------------------:|
| Q4 | 30.3 | 7.6 | 19 | 0 |
| Q8 | 88.0 | 14.4 | 29 | 0 |
| Q12 | 146.4 | 14.6 | 30 | 0 |
| Q16 | 206.6 | 15.0 | 23 | 0 |
| Q20 | 267.1 | 15.1 | 23 | 0 |
| Q30 (estimated) | ~434 | ~16.7 | — | 0 |

total_ms distribution across 30 queries: min=4792ms / median=7773ms / mean=14459ms / max=41093ms. High mean driven by 6 queries hitting the token-bucket 4 req/min pacing wait (33–41s fanout_ms each — expected, not CAPTCHA-related).

Per-engine reliability (OK% / dominant failure mode):

| Engine | OK% | Dominant failure |
|--------|-----|-----------------|
| crossref | 97% | 3% TIMEOUT_WATCHDOG |
| duckduckgo | 97% | 3% ERROR_BROWSER |
| google | 73% | 23% EMPTY_BLOCK (CAPTCHA — still fires, no longer causes cascade) |
| lobsters | 57% | 37% EMPTY_NO_CONTAINER (topic-mismatch, expected for general queries on tech-niche site) |
| mojeek | 90% | 3% EMPTY_NO_CONTAINER |
| open_library | 30% | 67% coarse-EMPTY (mapped to ERROR_OTHER — HTTP engine returning `[]` on non-book queries; sub-status needs `search_with_reason()` for fine-grained labelling) |
| openalex | 80% | 13% coarse-EMPTY (same HTTP-engine sub-status note as open_library) |
| semantic_scholar | 73% | 20% EMPTY_NO_CONTAINER |
| stack_exchange | 50% | 50% coarse-EMPTY (HTTP engine; EMPTY_NO_RESULTS on queries without SO matches) |

Top-3 bottleneck engines (highest search_ms per query): semantic_scholar (11×), openalex (8×), open_library (4×).

**Comparison:** pre-rip, 466s was spent exclusively in backoff sleeps inside a 16-pair batch, yielding 0 Google results. Post-rip, ~434s is the total wallclock for 30 complete queries (30/30 with results, zero wasted in sleep-on-failure). The backoff pattern consumed more total time than 30 actual queries now take.

## Open Questions

- **Should we add an explicit "engine-failed-this-query" status that propagates to the query log?** Currently `EMPTY_BLOCK` is the umbrella reason (covers both CAPTCHA and HTTP-429 block-page detection). Per-type sub-statuses would help debugging without re-introducing retry logic.
- **Do the cross-encoder service (port 8082) and other downstream HTTP services follow the same fail-fast policy?** The project-wide no-backoff principle applies to every external service call; whether any retry-with-backoff has crept into the RAG-server-call paths (`search_web.py` / `preview.py`) is unverified.

## Sources

- Probe-run evidence: `/tmp/value_eval_probe_run.log`
