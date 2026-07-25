# bee_fix — RATE_WAIT_TIMEOUT + Bucket-Uniformity + Scholar Removal (2026-05-21)

Three production changes applied 2026-05-21 (commit on branch `engine-uniformity`). This file documents what was changed and why.

## Production Changes Applied

**1. `RATE_WAIT_TIMEOUT` raised 5.0 → 60.0**
`RATE_WAIT_TIMEOUT: float = 60.0` in `src/search/search_web.py`. The outer `asyncio.wait_for(get_limiter(engine.name).acquire(), timeout=RATE_WAIT_TIMEOUT)` no longer cancels legitimate token-bucket waits (Phase 3 identified these as the primary cascade mechanism). Google's escalated backoff (>60s) still trips the timeout → RATE_SKIP for that engine only; the other 8 proceed normally.

**2. Bucket-uniformity invariant**
All 9 active engines fire on every query, regardless of filter mode (`--books`, `--pdf`, `--docs`). Filter modes resolved via post-merge URL filtering (`filter_urls_by_mode`) and per-engine query modifiers only. `apply_filter_mode()` in `src/search/filter_modes.py` passes `selected` dict through unchanged; returns `excluded={}`. `_BOOKS_ENGINES`, `_PDF_ENGINES`, `_DOCS_ENGINES` are modifier-target sets, not restriction sets.

**3. Google Scholar fully removed**
- `src/search/engines/scholar.py` L35 `_limiters["google_scholar"] = ...` removed — no limiter registration at import
- `src/search/search_web.py`: `ScholarEngine` import removed; `"google_scholar": 6.0` removed from `ENGINE_WATCHDOG_OVERRIDE`; `"google_scholar": 20` removed from `ENGINE_MAX_RESULTS`; `"google scholar": ScholarEngine()` removed from `ENGINES` dict
- `_select_engines()` default path returns full 9-engine set with `excluded={}`
- `scholar.py` file stays in tree (class + HTTP logic intact) for future re-integration via pooling-rework. The file is inert — nothing imports it.

## Evidence

Three probe phases preceding the fix:

**Phase 1 — CDP starvation REFUTED** (report `dev/search_pipeline/01_reports/cdp_probe_20260521_174959.md`)
Scheduling latency p99 = 1.4ms during zero_cascade (vs 3.0ms normal). Event loop completely free. CDP events = 0 during cascade. Starvation mechanism excluded.

**Phase 2 — A-sleep confirmed, backoff-cascade narrative INCORRECT** (report `dev/search_pipeline/01_reports/acquire_probe_20260521_183226.md`)
All 9 engines enter `acquire()`, acquire lock, sleep in `asyncio.sleep(wait)`, cancelled at ~5001ms. Lock released cleanly under CancelledError (Python 3.14 asyncio.Lock regression excluded). Phase 2 inferred "multi-engine backoff cascade" — this inference was not probe-verified and was superseded by Phase 3.

**Phase 3 — Tokencap-path wins** (report `dev/search_pipeline/01_reports/branch_probe_20260521_192646.md`)
18/30 zero_cascade queries measured. Two cascade types:
- **Type 1 (12/18):** pure tokencap — all 9 engines hit `len(tokens) >= max_requests` branch (NOT backoff). After 4 successful queries in <60s, the 5th acquire() waits `60s − age_of_oldest_token` (38.5s at Q5 → 8.4s at Q11) → cancelled at 5s by `asyncio.wait_for`. Recovery is natural: cascade lasts until oldest token expires.
- **Type 2 (6/18):** tokencap (8 engines) + Google backoff (1 engine). Following a CAPTCHA, Google-only fires backoff; other 8 hit tokencap independently.
Immune engines (crossref, openalex, stack_exchange, open_library) NEVER fired backoff branch — 0 `backoff_sleep_attempt` across all 18 queries. Phase 2 multi-engine-backoff narrative INCORRECT.

**Fix verification** (20-query smoke run, 2026-05-21)

| Milestone | Cumulative wall (s) | Avg/query in segment (s) | Engines OK | Engines RATE_SKIP |
|-----------|--------------------:|-------------------------:|-----------:|------------------:|
| Q4 | 29.5 | 7.4 | 22 | 0 |
| Q8 | 92.4 | 15.7 | 30 | 0 |
| Q12 | 174.4 | 20.5 | 28 | 0 |
| Q16 | 234.3 | 15.0 | 21 | 0 |
| Q20 | 294.3 | 15.0 | 23 | 0 |

Per-engine status across all 20 queries: crossref 19 OK, duckduckgo 17 OK, google 17 OK, lobsters 10 OK, mojeek 20 OK, open_library 5 OK, openalex 14 OK, semantic_scholar 12 OK, stack_exchange 10 OK. RATE_SKIP = 0 across all engines across all queries. Total wall 294s ≈ 4.9 min (9 engines, 20 queries, zero cascade).

## Open Questions

- Pooling-rework: which pool definitions place Scholar in a Google-free set? What inter-session CAPTCHA behavior is expected at 4/min in a Scholar-only pool?
- `max_requests` per-engine: currently hardcoded at 4 in each engine constructor call. Phase 3 showed the module default is 10. Should all engines use the module default (wider headroom before tokencap)? Not urgent while RATE_WAIT_TIMEOUT=60 covers the wait correctly.

## Sources

| Source | Relevance |
|--------|-----------|
| Phase 1 probe | CDP starvation REFUTED |
| Phase 2 probe | A-sleep confirmed, lock clean |
| Phase 3 probe | tokencap-path verdict |
| Scholar decoupling investigation (2026-05-09) | Scholar HTTP migration + Google decoupling history |
