# 35 — Pool Visibility + Index-Fetch Pool Fix

## Problem

Two bugs discovered after flipping `--pool` default to `backfill`:

1. **No console visibility of pool load.** `pool_fn()` was called inside `run_loop` (p4_loop.py line 59), result went only to `logger.record_pool_refresh()` (JSONL). Operator had no stdout confirmation that the 22k backfill pool was actually loaded.

2. **Sitemap index-fetch hardwired to curated pool.** `p3_target._fetch_index_via_proxy()` always called `load_curated_proxies()` unconditionally (p3_target.py line 53). With `--pool backfill`, the index fetch still used the ~3.4k curated pool, producing the misleading console line `[sitemap] Proxy fallback: 3347 candidates` (curated count, not backfill).

## Investigation

### Code paths read

- `p3_target.py` (68 LOC pre-fix): `build_sitemap_target()` → `_fetch_index_via_proxy()` → hardcoded `load_curated_proxies()`.
- `acquire_pipe.py` (131 LOC pre-fix): `pool_fn` defined line 43, passed to `run_loop` as callable. Pool loaded inside `run_loop`, not in orchestrator. Sitemap fetch at line 46, before box_lock, receives no pool argument.
- `p4_loop.py` (189 LOC, unchanged): `pool_provider()` called at three sites — startup (line 59), 60-min refresh (line 71), exhaustion wakeup (line 90). Startup call result goes to `logger.record_pool_refresh`, no stdout.

### Design alternatives evaluated

**Where to print pool size:**
- Option A: inside `p4_loop.run_loop` after `pool_22k = pool_provider()` — only the count is known, not the pool name string; print would be `[loop] Pool loaded: N proxies` without pool name.
- Option B: eager-load in `acquire_pipe.py` before `build_sitemap_target` — orchestrator knows `pool_name`, print can be `[acquire_pipe] Loaded backfill pool: 22347 proxies`. ✅ chosen.

**How to avoid double-load** (`pool_fn()` eager in orchestrator + `pool_fn()` again at run_loop startup):
- Option A (simpler): pass eager pool to sitemap, let run_loop call `pool_fn()` again at startup — two calls to the same loader at start, correct refreshes after. Pool is the same, but loaded twice.
- Option B (single-load): closure in orchestrator that returns `initial_pool` on first call, delegates to `pool_fn()` on subsequent calls. `p4_loop.py` untouched. ✅ chosen.

```python
_used = [False]
def _pool_provider():
    if not _used[0]:
        _used[0] = True
        return initial_pool
    return pool_fn()
run_loop(_pool_provider, ...)
```

**How to thread pool into `p3_target`:**
- Module-level state (import pool at module load) — rejected, creates load-order coupling.
- `build_sitemap_target(pool=None)` optional parameter, passed through to `_fetch_index_via_proxy(pool)` — clean, no coupling. Pool is `None`-safe: if direct fetch succeeds, pool is never used; if fallback needed and pool is `[]`, existing `RuntimeError("all candidates exhausted")` fires. ✅ chosen.
- `curated_sources` import removed from `p3_target.py`.

## Result

- `acquire_pipe.py` (131 → 140 LOC): eager pool load + print before `build_sitemap_target`; `_pool_provider` closure for `run_loop`.
- `p3_target.py` (68 → 64 LOC): `curated_sources` import removed; `build_sitemap_target(pool=None)`, `_fetch_index_via_proxy(pool)`.
- `p4_loop.py`: unchanged.

Console output after fix (with `--pool backfill`):
```
[acquire_pipe] Loaded backfill pool: 22347 proxies
[acquire_pipe] Building sitemap target...
[sitemap] Direct fetch: status=403, no XML marker — proxy fallback
[sitemap] Proxy fallback: <N backfill candidates>
```
