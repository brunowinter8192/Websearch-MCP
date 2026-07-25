# 59 — TheBlock failure-URL diff exclusion from dedup

**Date:** 2026-07-06. **Branch:** `theblock-clean-pass` (stacked on the prior clean-pass + master-list-relocation work).
**Prior art:** the poison-URL re-scrape problem, the stall-termination entry (failure logging — source of dead/failed lists).

## Problem

`filter_new_entries(mode="raw")` marks an entry "new" iff `raw/{hash}.md` is absent.
Failure URLs — `dead` (404/410 from origin) and `failed` (not fetched within the 60-min
no-progress stall window) — have no raw MD and therefore surfaced as "new" on EVERY
subsequent run, re-consuming the full proxy budget on poison URLs that can never succeed.
This was the poison-URL problem manifesting at dedup time.

## Decision

Both failure classes are permanently excluded from the diff. No retry mechanism — user decision.

## Implementation

### `dedup.py` — `exclude_urls` param

`filter_new_entries` gains an optional `exclude_urls: set[str] | None = None` parameter.
When provided, entries whose URL is in the set are counted as `n_excluded` and skipped
BEFORE the raw-file existence check (exclusion takes priority over the raw skip).

Return type extended from `(list, int)` to `(list, int, int)` = `(new_entries, n_skip_raw, n_excluded)`.
`n_excluded` is always 0 when `exclude_urls=None`, preserving full backward compatibility.

### `pipeline.py` — proxy_pool branch only

Before the `filter_new_entries` call in Stage 2:

```python
failure_urls: set[str] = set()
for _fname in ("dead_urls.txt", "failed_urls.txt"):
    _p = raw_dir / _fname
    if _p.exists():
        failure_urls |= {u for u in _p.read_text(encoding="utf-8").splitlines() if u}
new_entries, n_skip_raw, n_excluded = filter_new_entries(
    entries, raw_dir, platform.name, mode="raw",
    exclude_urls=failure_urls if failure_urls else None,
)
log.info(
    f"dedup → {len(entries)} total, {n_skip_raw} already in raw, "
    f"{n_excluded} known-failures excluded, {len(new_entries)} new"
)
```

`dead_urls.txt` and `failed_urls.txt` live in `raw_dir/` and are written by
`_update_blocked_urls` after each proxy_pool scrape run (same directory, same file names).
Files are absent on first run — the `if _p.exists()` guard makes first-run safe.

### Scope — TheBlock / proxy_pool only

- **Browser branch** (`run_pipeline` else arm): `new_entries, n_skip, _ = filter_new_entries(...)`
  — no `exclude_urls`, unchanged behaviour.
- **`run_scrape_only`** (CoinDesk backfill): `new_entries, n_skip, _ = filter_new_entries(...)`
  — no `exclude_urls`, unchanged behaviour.

## Failure class semantics

| Status | Source | Meaning | Retry? |
|--------|--------|---------|--------|
| `dead` | `dead_urls.txt` | 404/410 from origin — article deleted/never existed | No |
| `failed` | `failed_urls.txt` | Not fetched within 60-min stall window | No |

Both are treated identically by the exclusion: permanently out of the diff.
Re-enabling a URL requires manual removal from the relevant file.

## Test

`tests/test_dedup_exclude.py` — 7 unit tests on `filter_new_entries` directly:
excluded+no-raw, not-excluded+no-raw, not-excluded+raw, excluded+raw (exclusion first),
mixed-4-entry count check, None default (no exclusions), empty-set (no exclusions).
All 7 pass.
