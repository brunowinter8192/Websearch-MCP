# 50 — CoinDesk Scrape Job (Stage 2: decoupled backfill + per-job report)

**Date:** 2026-06-18.
**Upstream:** the discovery src/ port — inventory in place before Stage 2 starts.

## What we built

### Stage 2a — Decoupled scrape job

New `run_scrape_only()` orchestrator in `pipeline.py`. Entry point:

```
python -m src.news --source coindesk --scrape-only --year YYYY [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--limit N] [--skip-index]
```

No browser warmup, no discover stage. Flow:

1. **inventory** — `platform.load_scrape_entries(year, from_date, to_date, limit)` reads per-year shards `data/news/coindesk/inventory/coindesk_{year}.txt`.
2. **MD-diff** — `filter_new_entries()` (mode=`"pubdate"`) skips URLs already in the RAG collection.
3. **chunked scrape→clean→publish** — `scrape_chunks()` in `engine/scrape_job.py` processes 200-URL chunks; each chunk is published before moving on. Chunk dirs wiped after publish.
4. **report** — `write_scrape_report()` (Stage 2b) writes `data/news/coindesk/scrape_jobs/{job_id}/job.md` + `cumulative.png`.

New files:
- `src/news/engine/scrape_job.py` — `scrape_chunks()` + `run_cleanup()`, extracted from `run_pipeline()` to serve both full-pipeline and scrape-only paths.
- `src/news/platforms/coindesk/discover.py:load_inventory_filtered()` — standalone inventory reader for the scrape-only path.
- `src/news/platforms/coindesk/__init__.py:load_scrape_entries()` — wraps `load_inventory_filtered`, exposes it as `platform.load_scrape_entries` per `run_scrape_only()` contract.

### Stage 2b — Per-job report

New `src/news/engine/browser_reporter.py` — generic browser-scrape reporter:

`write_scrape_report(job_dir, job_records, t_job_start, n_target, filter_desc, regwall_abort) → None`

Produces:
- `job.md` — counts (target/ok/regwall/empty/failed), regwall rate (⚠ REGWALL ABORT if true), throughput (wall-clock, mean/median s/URL, URLs/min), backfill projection (61 k / urls_per_min → hours), char-count percentiles p10/p25/p50/p75/p90/p95 of ok bodies (low p50 ⇒ silent-regwall / truncation risk), failure table (up to 20 rows).
- `cumulative.png` — step-plot of cumulative ok count vs elapsed seconds. x per ok record: `(t_chunk_start − t_job_start).total_seconds() + elapsed_s`.

Wired into `run_scrape_only()` in `pipeline.py`: `job_dir = DATA_ROOT / platform.name / "scrape_jobs" / job_id` created and passed to reporter after `scrape_chunks()` returns.

## Resumability lesson (same as a later Block finding)

A later entry documents The Block's monolithic scrape-all → clean-all → publish-all design: when the proxy loop
stalls on 8 poison URLs for 21h, all 22,995 raw scrapes are unprocessed at kill time (clean/ empty,
collection unchanged). The same lesson applies to CoinDesk backfill at 61 k URLs: a monolithic single-
pass with one terminal publish would strand all output on any crash or RegwallGuardError.

Stage 2a's chunked design prevents this: publish is durable per 200-URL chunk. The MD-diff dedup means
re-run skips already-published chunks and resumes from the next unseen URL. A RegwallGuardError in
chunk N+1 does not affect chunks 0..N.

## Job record shape

`scrape_chunks()` returns `job_records: [{t_chunk_start: datetime(UTC), url, hash, file, char_count, status, error, wait_strategy, elapsed_s}]`.
- `elapsed_s` is set for ok/regwall/empty; may be absent on failed (exception path in `scrape.py`).
- `t_chunk_start` is the wall-clock time at the start of the chunk containing the record.
- `browser_reporter._compute_stats()` handles None `elapsed_s` via `.get()` guards.

## Char-count health signal

Regwall pages on CoinDesk return ~23–26 k chars; real articles 34 k+. A low p50 in the char-count
distribution is an indicator of silent regwall (regwall pages not caught by keyword signals) or
truncation. The `job.md` p50 row carries an explicit note: "low p50 ⇒ silent-regwall / truncation risk".
`_BACKFILL_TOTAL = 61_000` is the estimated full backfill size used for the throughput projection.

## Decision / status

Stage 2a+2b: complete ✓. Smoke tested: inventory discover (30-day) → scrape-only --year 2026 --limit 10 → job.md + cumulative.png produced.
