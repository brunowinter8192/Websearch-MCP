# src/news/

## Role

Multi-platform news ingestion pipeline, run as `python -m src.news --source <platform>`. Discovers articles, dedups against the raw corpus, scrapes raw markdown/HTML into `data/news/{name}/raw/`. For The Block (proxy_pool engine) the pipeline also runs an in-pipe clean-pass that writes cleaned articles into the RAG collection dir. Indexing stays fully decoupled — no `rag-cli index` call in any pipe path. Touch this package to add a news source or change pipeline orchestration; the generic scrape engines live in `engine/`, platform implementations in `platforms/`. Do NOT import from `src/crawler/` or `src/scraper/` — this package is self-contained.

## Public Interface

`__init__.py` is empty; the package runs as a module (`python -m src.news` → `__main__.py`). Direct async entry: `run_pipeline(platform)`, `run_discover_only(platform)`, `run_scrape_only(platform, year=…, limit=…)` in pipeline.py — import path unchanged across the 2026-08-20 module split (pipeline.py stays the entry module; `pipeline_support.py`/`clean_pass.py` are internal-only, no external caller imports from them except `tests/test_theblock_clean_pass.py` → `clean_pass._run_clean_pass`).

## Flow

`__main__` parses args, imports the platform module (side-effect registers it), looks it up via `registry.get`, and calls one of pipeline's three entries. `run_pipeline`: discover → dedup(raw) → scrape → raw persist (+ clean-pass for proxy_pool/TheBlock). `run_scrape_only`: date-filtered backfill, discover-free, dispatched on `platform.scrape_engine`. `run_discover_only`: discover + persist only. Scrape dispatch key is `platform.scrape_engine` ∈ {browser, proxy_pool, proxy_riding}.

## Modules

### pipeline.py (349 LOC)

**Purpose:** Entry module — 3 CLI-facing async orchestrators (`run_pipeline`, `run_scrape_only`,
`run_discover_only`; import path unchanged, still what `__main__.py` calls) + their engine-arm
helpers. `run_pipeline` dispatches `_run_pipeline_proxy_pool` (TheBlock: box_lock+Janitor lifecycle
spans discover→dedup→scrape, then `_persist_proxy_pool_results` runs the clean-pass) or
`_run_pipeline_browser` (CoinDesk-style: discover→dedup→scrape with `RegwallGuardError` recovery —
the manifest returned in the exception is used as-is, scrape is treated as complete not failed).
`run_scrape_only` (decoupled backfill path) dispatches `_run_scrape_only_riding` (bypasses chunking
— engine owns concurrency/watchdog/requeue) or `_run_scrape_only_browser` (200-URL chunks via
`scrape_chunks_raw`). `_build_ok_manifest_entries` is the one shared helper behind all 3 arms that
build `ok_manifest_entries` for `_append_to_raw_manifest`.
**Reads:** `data/news/{name}/raw/`, `discover/` (dead_urls.txt, failed_urls.txt, per-year shards, master_urls.txt).
**Writes:** `raw/{hash}.{md,html}`, `raw/manifest.jsonl`, `discover/` block-lists, `scrape_jobs/{job_id}/` reports (via reporters); delegates marker/snapshot/master-list writes to `pipeline_support.py`, clean-pass writes to `clean_pass.py`.
**Called by:** `__main__.py`.
**Calls out:** `platform` (Platform); `engine.dedup` (filter_new_entries); `engine.scrape` (scrape_entries, RegwallGuardError); `engine.proxy_pool` (box_lock, Janitor, AcquireLogger, scrape_entries_proxy); `engine.scrape_job` (scrape_chunks_raw, _append_to_raw_manifest, _update_blocked_urls); `engine.browser_reporter` (write_scrape_report); `engine.proxy_riding` (scrape_entries_riding, RidingScrapeConfig, write_riding_report); `pipeline_support.py` (run bookkeeping + `PROJECT_ROOT`/`LOG_DIR`); `clean_pass.py` (`_run_clean_pass`).

`_run_pipeline_proxy_pool`/`_run_pipeline_browser` return `bool`: `True` = ran to completion (caller
logs `"=== complete ==="` + writes the marker), `False` = aborted early (the arm already wrote the
marker inline before returning — matches the pre-split function's behavior of skipping the trailing
log line + double marker-write on early abort; `run_pipeline`'s own trailing code only runs `if
completed`).

`_run_pipeline_proxy_pool`: `start_job` BEFORE `AcquireLogger` construction so `Janitor` wipes
`log_dir` before the JSONL is opened — reordering this would truncate the run's own JSONL log.
`box_lock.acquire(...)` scopes the ENTIRE discover+dedup+scrape stage (a `with` block); `j.end_job`
+ `logger.close()` run in a `finally` nested inside that `with`, guaranteeing Janitor bookkeeping
closes even on an exception, before the lock releases.

### pipeline_support.py (86 LOC)

**Purpose:** Generic run bookkeeping shared by all 3 `pipeline.py` orchestrators — logging setup,
connectivity precondition, and the 3 small state-writer helpers (master URL list, discover JSON
snapshot, last-run marker). Split out of `pipeline.py` because none of these five are specific to
any one engine arm or orchestrator; `PROJECT_ROOT`/`LOG_DIR` live here (not in `pipeline.py`) since
both this module's `_setup_logging`/`_write_marker` AND `pipeline.py`'s 3 orchestrators need `LOG_DIR`
— `pipeline.py` imports it from here rather than the reverse, to avoid a cycle (`pipeline.py`
already depends on this module for the 5 functions).
**Reads:** `platform.precondition_url` (via `urllib`); existing `master_urls.txt` (set-union merge).
**Writes:** `LOG_DIR/news_{name}_{date}.log`, `LOG_DIR/news_{name}_last_run.txt`, `discover/master_urls.txt`, `discover/discover_{ts}.json`.
**Called by:** `pipeline.py` (all 3 orchestrators + `_run_pipeline_proxy_pool`/`_run_pipeline_browser`).
**Calls out:** none (stdlib `logging`, `urllib.request`, `json`).

`_persist_master_list`: format is `YYYY-MM-DD\t<url>` (date from `entries[i]["lastmod"][:10]`,
entries without `lastmod` or `url` skipped), set-union merged with the existing file content, sorted
before write. TheBlock-specific — called only when `platform.uses_master_list` is `True`.

### clean_pass.py (55 LOC)

**Purpose:** The proxy_pool/TheBlock clean-pass stage (`_run_clean_pass`) — isolated from
`pipeline_support.py`'s generic helpers because it's stage-specific business logic (reads
`raw/{hash}.md`, calls `platform.cleanup()`, writes to the RAG collection dir), not run
bookkeeping, and has its own independent test file.
**Reads:** `raw_dir/{hash}.md` for each ok entry; existing `clean/bodyless_urls.txt` (set-union merge).
**Writes:** `collection_dir/theblock__{pubdate}__{hash}.md` per cleaned entry; `raw_dir.parent/clean/bodyless_urls.txt` (body-less URLs, set-union, sorted); progress logged every 200 entries.
**Called by:** `pipeline.py:_persist_proxy_pool_results` (proxy_pool arm, only when `n_ok > 0`).
**Calls out:** `engine.publish.pub_date_str` (the `{pubdate}` slug in the output filename).

Returns `{"n_cleaned", "n_bodyless", "total"}`. Empty `ok_entries` short-circuits to
`{0, 0, 0}` without creating `collection_dir`.

### __main__.py (132 LOC)

**Purpose:** argparse entry point. Flags: `--source`, `--skip-index` (no-op, CLI compat), `--timeframe`, `--discover-only`, `--scrape-only` (+ `--year/--from/--to/--limit/--browsers/--slots/--cooldown-policy/--page-timeout`). Imports the platform modules for side-effect registration, resolves via `registry.get`, dispatches to the matching pipeline entry. When `--timeframe` is not `delta` and not `--discover-only`, auto-forces `skip_index=True` and prints the manual index reminder.
**Reads:** CLI args.
**Writes:** stdout.
**Called by:** the `python -m src.news` entry point.
**Calls out:** `platforms.coindesk`, `platforms.theblock` (side-effect register); `registry` (get); `pipeline` (run_pipeline, run_discover_only, run_scrape_only).

### platform.py (35 LOC)

**Purpose:** The extension seam. Defines the `Platform` Protocol (name, collection, precondition_url, regwall_signals, scrape_engine, scrape_config, proxy_scrape_config; `discover()` + `cleanup()`), plus the `ScrapeConfig` and `ProxyScrapeConfig` dataclasses. `scrape_engine` ∈ {browser, proxy_pool, proxy_riding} is the pipeline dispatch key. Optional attrs (`riding_scrape_config`, `timeframe`, `uses_master_list`) are consumed via `getattr` in pipeline.py, deliberately NOT in the Protocol.
**Called by:** `pipeline.py`, `registry.py`, `platforms/*`, `engine/*`.
**Calls out:** none (stdlib `typing`, `dataclasses`).

### registry.py (19 LOC)

**Purpose:** Name → Platform registry. `register(instance)` (called at platform-module import) and `get(name)` (called by `__main__`).
**Reads / Writes:** in-memory registry dict.
**Called by:** `__main__.py` (get); `platforms/*/__init__.py` (register).
**Calls out:** `platform` (Platform).

## State

`registry`'s in-memory name→Platform dict — populated at platform-module import (side-effect), read by `__main__`. On disk, per-platform corpus under `data/news/{name}/` (raw/, discover/, clean/, scrape_jobs/) is the durable state; `raw/manifest.jsonl` + the discover block-lists (dead/failed/regwall/empty) drive dedup and make re-runs resumable.

## Gotchas

- To add a platform: create `platforms/<name>/__init__.py` defining a `Platform` class that calls `register(instance)` at import, then import that module in `__main__.py` for side-effect registration.
- `--skip-index` is accepted but a no-op — no path ever runs `rag-cli index`.
- proxy_riding (CoinDesk current) writes raw `.html`; browser/proxy_pool write raw `.md`. `filter_new_entries` takes `raw_ext` accordingly.
- `run_scrape_only` reporters are engine-specific: `write_riding_report` for proxy_riding, `write_scrape_report` for browser. They are NOT interchangeable — the browser reporter needs `t_chunk_start`/`elapsed_s` fields absent from riding manifests and would crash.
- Both normal completion and the stall-abort path write the job report to the same `scrape_jobs/{job_id}/` dir; the platform root is never written to by the report step.
- `publish.py` remains on disk but is not called in any path.
- `_run_pipeline_browser`'s `RegwallGuardError` recovery: `scrape_entries` raising mid-run means the
  guard tripped (too many regwalls) — the exception's `.manifest` (partial, already-persisted
  results) is used AS the final manifest, not discarded; the arm proceeds to persist it normally
  (not treated as a hard failure — `n_ok`/raw files up to the abort point are kept).
