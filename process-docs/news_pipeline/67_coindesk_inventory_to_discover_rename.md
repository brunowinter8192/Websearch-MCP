# 67 — CoinDesk `inventory/` → `discover/` rename

## Rationale

Cross-platform layout alignment. TheBlock stores its discovery output in
`data/news/theblock/discover/`. CoinDesk was using `data/news/coindesk/inventory/` — a
divergent name for the same artefact category (timeline-API URL shards written by the
`discover()` step). Renaming aligns both platforms under the same `discover/` convention.

## Exact Rename Set

**Path value (MANDATORY):**

| File | Old | New |
|---|---|---|
| `config.py:33` | `"inventory"` path segment + `INVENTORY_DIR` | `"discover"` + `DISCOVER_DIR` |
| `config.py:32` | comment `data/news/coindesk/inventory/coindesk_{year}.txt` | `data/news/coindesk/discover/coindesk_{year}.txt` |

**Identifier renames (src/ self-consistency):**

| Old | New | Locations |
|---|---|---|
| `INVENTORY_DIR` | `DISCOVER_DIR` | `config.py:33`; `discover.py` import + 3 uses; `__init__.py` import + call |
| `inventory_dir` param | `discover_dir` | `cursor_loop`, `_append_to_shard`, `load_discover`, `load_discover_filtered` — signatures + bodies |
| `load_inventory` | `load_discover` | `discover.py:327` def; `discover.py:44` call |
| `load_inventory_filtered` | `load_discover_filtered` | `discover.py:344` def; `__init__.py:9` import |

**Cosmetic wording (logs / comments / help texts):**

- `discover.py`: "Inventory loaded" → "Discover loaded"; "new to inventory" → "new to discover";
  comment "inventory shards" → "discover shards" (×3).
- `__init__.py`: cross-module comment + method comment updated.
- `pipeline.py:33` comment, `pipeline.py:50` comment, `pipeline.py:80` log line: "inventory" → "discover".
- `__main__.py` help texts: "inventory-update", "Read inventory", "from inventory", "inventory date range" → discover equivalents.

Shard filenames (`coindesk_{year}.txt`) and the `--scrape-only` / `--year` / `--from` / `--to`
flag names are unchanged — only help text wording updated.

## dev/ scope

`dev/news_pipeline/coindesk_proxy_riding/` (smoke_stage1.py, p3_url_sampler.py,
run_coindesk_riding.py) references `inventory/`. Left untouched — deprecated prototype,
slated for removal; not in scope.

## Orchestrator steps (post-branch)

The actual data migration and branch merge are performed by the orchestrator after a
verification run completes:

1. `mv data/news/coindesk/inventory data/news/coindesk/discover`
2. Merge `coindesk-inv-discover` into `main`

No data was moved and no merge was done as part of this rename task.
