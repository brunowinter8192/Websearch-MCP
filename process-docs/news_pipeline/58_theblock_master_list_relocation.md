# 58 — TheBlock master_urls.txt relocation into discover/

**Date:** 2026-07-06. **Branch:** `theblock-clean-pass` (stacked on the in-pipe clean-pass work).
**Prior art:** the single-master-list entry.

## Decision

`data/news/theblock/master_urls.txt` → `data/news/theblock/discover/master_urls.txt`.

## Why

The prior stage introduced the single master list and explicitly noted that timestamped snapshot JSONs
were "write-once read-never". For TheBlock, `uses_master_list=True` means no snapshot is
ever written to `discover/` — the directory existed only for the (now-suppressed) JSON
snapshots. `discover/` is therefore the natural home for the master list: it is TheBlock's
only discover-stage artifact, and co-location makes the per-platform data layout self-evident.

## What changed

Two `master_path` call sites in `pipeline.py`:

- `run_discover_only` (~line 42)
- `run_pipeline` proxy_pool branch (~line 163)

Both changed from:
```python
master_path = DATA_ROOT / platform.name / "master_urls.txt"
```
to:
```python
master_path = DATA_ROOT / platform.name / "discover" / "master_urls.txt"
```

`_persist_master_list` already calls `master_path.parent.mkdir(parents=True, exist_ok=True)`,
so `discover/` is auto-created on first write — no separate mkdir needed.

No other code reads `master_urls.txt`: grep across `src/` confirms the only reader is
`_persist_master_list` itself (union-append on re-run), and the only writers are the two
call sites above.

## Data file note

The existing `data/news/theblock/master_urls.txt` (~3 MB, gitignored, not present in worktrees)
must be moved to `data/news/theblock/discover/master_urls.txt` in the main tree by Opus before
the next pipeline run. No code change is required for this — it is a plain `mv`.
