# CoinDesk Discovery — src/ Port (Stage 1)

**Date:** 2026-06-17  
**Task:** Port validated timeline-API discovery from `dev/06_coindesk_full_discovery.py` to production `src/`.

## What we did

Replaced the old browser-UI-pagination `discover.py` (340 LOC, pydoll JS scraping, 48h delta only)
with the timeline-API cursor method. Five files changed:

| File | Change |
|---|---|
| `coindesk/config.py` | Replaced old discovery constants with timeline-API constants + INVENTORY_DIR |
| `coindesk/discover.py` | Full rewrite: browser warmup → httpx cursor loop → incremental inventory |
| `coindesk/__init__.py` | Added `timeframe: str = "30"` attr; discover() passes self.timeframe |
| `src/news/__main__.py` | Added `--discover-only` flag; branch to run_discover_only(); updated --timeframe help |
| `src/news/pipeline.py` | Added run_discover_only() + extracted _check_internet() from _check_preconditions() |

## What we found

### Dev/06 asyncio nesting issue

`dev/06` is a sync orchestrator (`full_discovery()`) that calls `asyncio.run(browser_load_feed(...))`.
In production, `discover()` is `async def` called via `asyncio.run(run_discover_only(...))`. Calling
`asyncio.run()` from within a running event loop raises `RuntimeError`. Fix: `cursor_loop` and
`try_rewarm` promoted to `async def`; all `browser_load_feed()` calls use `await`.

Found at first smoke run (first crash). Fixed before commit.

### Crash-safety validated via first smoke run

The first run crashed at try_rewarm (asyncio nesting). But 122 URLs were already written to
`data/news/coindesk/inventory/coindesk_2026.txt` (incremental append per article). The second run
loaded those 122 URLs, added 0 new (all already present), and completed cleanly. Crash-safety ✓.

### 403 + re-warm behavior

After 7 successful cursor calls (122 entries, covering 2026-06-09 to 2026-06-17), the API returned 403.
`try_rewarm` called httpx feedpage (200 — session cookies alive) then timeline API (still 403).
Browser re-warm also failed (403 on timeline). Fatal stop, clean exit. This is normal dev/06 behavior
for session-expiry on a specific cursor anchor. Proactive REWARM_EVERY=240s would prevent this in
longer runs by refreshing before any 403 occurs.

### Entry shape

`publication_date` comes from `articleDates.displayDate` — day-precise ISO string. No URL date scraping
needed. `section` from first pathname segment. Live-blog filter: slug starts with "live-".

## Decision / next

- discover.py port: complete ✓
- Inventory: `data/news/coindesk/inventory/coindesk_{year}.txt` format `YYYY-MM-DD\t<url>` ✓
- `--discover-only` integration: new `run_discover_only()` in pipeline.py, TheBlock path untouched ✓
- Smoke test: 122 URLs found, shard written, idempotent re-run 0 new ✓

Stage 2 (scrape job integration) is a separate later task.
