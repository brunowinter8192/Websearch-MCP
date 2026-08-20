# src/news/engine/

## Role

Generic, platform-agnostic pipeline engine modules. Called by `pipeline.py`; no platform-specific
logic lives here. All modules accept platform parameters explicitly (no hardcoded source names).

`pipeline.py` dispatches on `platform.scrape_engine`: `"browser"` → `scrape.py` (via
`scrape_chunks_raw` in `run_scrape_only`); `"proxy_pool"` → `proxy_pool/scrape.py` (via
`run_pipeline`); `"proxy_riding"` → `proxy_riding/scrape.py` (via `run_scrape_only`, CoinDesk
backfill path — chunk-bypass, full entry set, returns `(manifest, state)`). All three engines wired.

`publish.py` is kept on disk but is NOT called by any pipe path — cleanup+publish are decoupled
to a future ad-hoc skill.

## Modules

### scrape.py (202 LOC)

**Purpose:** Browser-engine scraper — fresh `AsyncWebCrawler` per URL, Scrapy gate pacing, regwall guard. Active when `platform.scrape_engine == "browser"`.
**Reads:** entries list (in-memory), ScrapeConfig, regwall_signals list.
**Writes:** `{hash}.md` (BODY ONLY, no frontmatter) to output_dir (raw_dir in all call paths).
**Called by:** `pipeline.py:_run_pipeline_browser`, `scrape_job.py:_scrape_one_chunk`.
**Calls out:** `crawl4ai` (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig).

`RegwallGuardError` is raised (not sys.exit) when regwall fraction ≥ `REGWALL_FAIL_THRESHOLD` (0.20).
`.manifest` attribute on the exception carries the full per-entry manifest (including ok entries
written before abort) so callers can persist raw data from aborted runs.

`_fetch_one` delegates its ok/regwall/empty classify-and-log branch to `_classify_fetch` (2026-08-20
extraction, mirrors `proxy_riding/fetch.py:_classify_crawl_result`) — returns the status-specific
`result_entry` update fields; write-to-disk (`_write_body`) happens only on `ok`.

### dedup.py (62 LOC)

**Purpose:** Filter discover entries to those not yet in the raw corpus by checking file existence; optionally exclude known-failure URLs permanently.
**Reads:** entries list (in-memory), dir (filesystem), source name, mode, optional exclusion set.
**Writes:** nothing (pure filter).
**Called by:** `pipeline.py:_run_pipeline_proxy_pool` / `_run_pipeline_browser` (mode=`"raw"`), `pipeline.py:run_scrape_only` (mode=`"raw"`).
**Calls out:** stdlib only.

`filter_new_entries(entries, collection_dir, source, mode="pubdate", exclude_urls=None, raw_ext=".md") → (new_entries, n_skip_raw, n_excluded)`:
- `raw_ext: str` — file extension for `mode="raw"` existence check. Default `".md"` (browser, proxy_pool — unchanged). Pass `".html"` for `proxy_riding` (CoinDesk). All existing callers that omit this param retain `.md` behaviour.
- `exclude_urls: set[str] | None` — when provided, URLs in the set are permanently excluded (counted as `n_excluded`) before the raw-file existence check. Only the proxy_pool branch of `run_pipeline` passes this (loaded from `dead_urls.txt` + `failed_urls.txt`).

Three modes via `mode` param:
- `"raw"` (all pipe paths): exact match `{hash}{raw_ext}` in raw_dir — dedup on raw corpus.
- `"pubdate"`: exact match `{source}__{pubdate}__{hash}.md` — legacy, collection-based.
- `"hash_only"`: glob `{source}__*__{hash}.md` — legacy, collection-based, no pubdate.

### publish.py (134 LOC)

**Purpose:** Copy cleaned MDs to RAG collection dir; write/merge URL manifest; optionally run `rag-cli index`.
**Reads:** clean_manifest (in-memory), clean_dir (filesystem), existing `{collection}__index.jsonl` if present.
**Writes:** `{source}__{pubdate}__{hash}.md` to collection_dir; `{collection_name}__index.jsonl` in collection_dir.
**Called by:** NOT called by any active pipeline path. Kept on disk for future cleanup+publish skill.
**Calls out:** `rag-cli` (subprocess).

### scrape_job.py (110 LOC)

**Purpose:** Raw-only chunked scrape orchestration for `run_scrape_only()` and shared raw-persist helpers.
**Reads:** chunks (list of entry lists), platform config.
**Writes:** `{hash}.md` into raw_dir per ok entry; appends to `raw/manifest.jsonl`; updates `regwall_urls.txt` / `empty_urls.txt`.
**Called by:** `pipeline.py:_run_scrape_only_browser` (`scrape_chunks_raw`); `pipeline.py:_persist_proxy_pool_results` / `_run_pipeline_browser` (`_append_to_raw_manifest`, `_update_blocked_urls`).
**Calls out:** `scrape.py:scrape_entries`.

`scrape_chunks_raw(chunks, raw_dir, platform, log)` — outer per-chunk loop, delegates each chunk to
`_scrape_one_chunk` (2026-08-20 extraction — `scrape_entries()` → `_append_to_raw_manifest()` →
`_update_blocked_urls({"regwall":…,"empty":…})`, mutates the running `totals` dict in place).
`RegwallGuardError`: `exc.manifest` recovered, ok files preserved, `_scrape_one_chunk` signals
`aborted=True`, outer loop stops. Returns `(totals, job_records, regwall_abort)`.

`_append_to_raw_manifest(raw_dir, ok_entries)` — append `{hash,url,publication_date}` lines to `raw/manifest.jsonl`. Append-only; no dedup (dedup happens upstream via `filter_new_entries(mode="raw")`).

`_update_blocked_urls(raw_dir, manifest, status_filenames)` — read existing blocked-URL file, union with new URLs from manifest by status, write back sorted. `status_filenames` keys: `"regwall"/"empty"` (browser), `"dead"/"failed"` (proxy_pool).

`job_records`: `[{t_chunk_start: datetime, url, hash, file, char_count, status, error, wait_strategy, elapsed_s}]` — consumed by `browser_reporter.py`.
`regwall_abort`: True when `RegwallGuardError` terminates the chunk loop early.

### browser_reporter.py (205 LOC)

**Purpose:** Per-job report writer for browser-engine scrape jobs. Produces `job.md` + `cumulative.png` from `job_records`.
**Reads:** `job_records` (in-memory list from `scrape_chunks_raw`), `t_job_start`.
**Writes:** `{job_dir}/job.md` (counts, regwall rate, throughput, backfill projection, char-count percentiles p10–p95, failure table); `{job_dir}/cumulative.png` (step-plot of cumulative ok count vs elapsed seconds).
**Called by:** `pipeline.py:_run_scrape_only_browser`.
**Calls out:** `matplotlib` (lazy import inside `_write_plot`), `statistics` (stdlib).

Key metric: `completion_s ≈ (t_chunk_start − t_job_start).total_seconds() + elapsed_s` per ok record — used as x-axis of the cumulative plot.
Backfill projection extrapolates from URLs/min → hours to scrape `_BACKFILL_TOTAL` (61 k) articles.

`_write_md` (2026-08-20 split, mirrors `proxy_riding/reporter.py`'s pattern): one section-builder
helper per `job.md` heading — `_md_header`, `_md_char_distribution`, `_md_failure_list`, and a single
shared `_md_url_list_section(title, job_records, status, limit=50)` for the Regwall-URLs/Empty-URLs
tables (verbatim-duplicate blocks before the split). Output byte-identical (verified via
synthetic-state before/after diff — no test suite coverage exists for this module).

## Sub-Engines

Two scrape engines live in their own subpackages (own-level docs there): `proxy_pool/` (proxy-rotation engine, entry `scrape_entries_proxy` in `proxy_pool/scrape.py`, active when `scrape_engine == "proxy_pool"`) and `proxy_riding/` (browser + rotating-proxy engine, entry `scrape_entries_riding` in `proxy_riding/scrape.py` returning `(manifest, state)`, active when `scrape_engine == "proxy_riding"` from `run_scrape_only`).
