# 55 — TheBlock Single Master URL List

## What changed

TheBlock's discover step previously wrote two artifacts per `run_pipeline()` call:
- A timestamped snapshot JSON: `data/news/theblock/discover/discover_<ts>.json`
- Per-year inventory shards: `data/news/theblock/inventory/theblock_{year}.txt`

`run_discover_only()` wrote nothing at all — it just returned.

After this change, both `run_discover_only()` and `run_pipeline()` write a single persistent master list:
- **Path:** `data/news/theblock/master_urls.txt`
- **Format:** `YYYY-MM-DD\t<url>` (date = `lastmod[:10]` from sitemap)
- **Semantics:** set-union append with existing file, sorted, deduped — idempotent on re-run

No snapshot JSON is written for TheBlock. No per-year shards are written for TheBlock.

## Why single list vs per-year shards

Per-year shards (mirroring CoinDesk's model) made sense for CoinDesk because its cursor loop
processes entries in chronological order and needs incremental per-shard streaming (`_append_to_shard`
in `coindesk/discover.py`). TheBlock's sitemap discovery returns all entries in a single batch
and has no streaming constraint — per-year sharding added complexity and made backfill inspection
harder (user must check N files instead of one). A single sorted file is directly grepable,
wc-able, and diffable without scripting.

Timestamped snapshots were write-once read-never: the user had no workflow consuming them,
and they accumulated without bound. The master list is the same data with history baked in
(set-union semantics) and zero accumulation.

## Mechanism: `uses_master_list` attribute

`TheBlockPlatform` gains `uses_master_list: bool = True` (in `__init__.py`).
`pipeline.py` reads it via `getattr(platform, "uses_master_list", False)` — absent → `False`.

This keeps CoinDesk entirely untouched:
- CoinDesk has no `uses_master_list` attribute → `getattr` returns `False`
- CoinDesk's browser path in `run_pipeline()` is structurally separate from the proxy_pool path
- CoinDesk's per-year inventory is written by `cursor_loop` in `coindesk/discover.py` — no pipeline.py involvement

## `_persist_inventory()` removal

`_persist_inventory()` in `pipeline.py` was called only from the proxy_pool path of `run_pipeline()`
(TheBlock only). After this change the proxy_pool path calls `_persist_master_list()` instead.
`_persist_inventory()` was dead — removed.

`_write_discover_snapshot()` was NOT removed: the browser path (CoinDesk) still calls it at
`run_pipeline()` line 207.

## Functions changed

| Function | File | Change |
|---|---|---|
| `run_discover_only()` | `pipeline.py` | Added master list write after discover when `uses_master_list` |
| `run_pipeline()` proxy_pool path | `pipeline.py` | Replaced snapshot + `_persist_inventory` with `_persist_master_list` dispatch |
| `_persist_inventory()` | `pipeline.py` | Removed (dead) |
| `_persist_master_list()` | `pipeline.py` | Added (new) |
| `TheBlockPlatform` | `theblock/__init__.py` | Added `uses_master_list = True` |

## Command

```bash
# Build/update master list for all subs (full backfill):
python -m src.news --source theblock --discover-only --timeframe full

# Recurring delta update (top-2 newest subs):
python -m src.news --source theblock --discover-only --timeframe delta

# Single sub test:
python -m src.news --source theblock --discover-only --timeframe sub:0
```
