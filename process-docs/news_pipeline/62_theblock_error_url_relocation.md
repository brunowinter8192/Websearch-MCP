# 62 — TheBlock dead_urls.txt + failed_urls.txt relocation into discover/

**Date:** 2026-06-19. **Branch:** `errorurl-reloc`.
**Prior art:** master_urls.txt moved to discover/ in a prior session.

## Decision

`dead_urls.txt` and `failed_urls.txt` move from `data/news/theblock/raw/` to
`data/news/theblock/discover/`.

## Why

Both files were buried in `raw/` alongside ~27k raw HTML files, making them invisible to
anyone inspecting the per-platform data layout. `discover/` already holds `master_urls.txt` —
it is the natural home for all TheBlock discover-stage / pipeline-control artifacts.
Co-locating the failure lists there makes the layout self-evident.

## What changed

Two sites in `pipeline.py`, both changed from `raw_dir` to `discover_dir`:

- **READ site** (line 173, dedup stage): loop over `("dead_urls.txt", "failed_urls.txt")` now
  reads from `discover_dir / _fname` instead of `raw_dir / _fname`.
- **WRITE site** (line 212, persist stage): `_update_blocked_urls` call now passes `discover_dir`
  instead of `raw_dir` as the target directory.

`_update_blocked_urls` itself (`engine/scrape_job.py` lines 88–96) is unchanged — it already
uses its first argument generically as the write target.

`discover_dir` is computed at `pipeline.py` line 132 (`platform_dir / "discover"`) and is already
in scope at both sites. No new variable needed.

**Scope boundary:** TheBlock / proxy_pool path only. The browser path (CoinDesk) calls
`_update_blocked_urls(raw_dir, manifest, {"regwall": …, "empty": …})` at line 264 — untouched.
`scrape_job.py:scrape_chunks_raw` also calls `_update_blocked_urls(raw_dir, …, regwall/empty)` at
line 61 — untouched.

## Data file note

The existing `data/news/theblock/raw/dead_urls.txt` and `data/news/theblock/raw/failed_urls.txt`
(gitignored, not present in worktrees) must be moved to `data/news/theblock/discover/` in the
main tree by Opus before the next pipeline run. No code change is required — plain `mv`.
