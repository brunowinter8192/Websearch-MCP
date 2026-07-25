# 52 — Pipe raw-only: cleanup + publish decoupled from ALL news pipes

**Date:** 2026-06-18. **State:** implemented across Stage A (run_scrape_only) + Stage B (run_pipeline both engines).

## Decision

Every scrape path — `run_scrape_only` AND `run_pipeline` (both browser + proxy_pool branches) — is
**raw-only**: scrape → `data/news/{name}/raw/{hash}.md` + `manifest.jsonl` + blocked-URL lists.
`cleanup.py` and `publish.py` remain on disk but are never called by any pipe path.
Cleanup + index become a separate ad-hoc skill, run against the full raw corpus after sufficient
volume accumulates or when quality diagnosis warrants it.

## Why

### Fixed cleaner is fragile at scale

During CoinDesk scrape-job testing (~20–30 articles at a time), at least one article retained the full
site footer after `cleanup.py` ran. At 60 k+ articles the same latent shape variance would produce
a polluted corpus without visible signal until after indexing. The right response is:

1. Accumulate the raw corpus (durable, verbatim, scrape-time artifact).
2. Diagnose cleanup shapes against the full corpus before running cleanup at scale.
3. Fix the cleaner per-shape, then run cleanup as a one-shot batch against raw.

This "capture-and-index" model mirrors the trading capture skill: record first, structure later.
Diagnosing shape variance against 60 k raw files is tractable; patching a corrupted 60 k RAG
collection after a bad cleanup run is not.

### Dedup-on-raw enables safe re-scraping

`filter_new_entries(entries, raw_dir, mode="raw")` deduplicates on `{hash}.md` existence in raw_dir.
This means re-runs are safe: already-scraped URLs are skipped regardless of whether cleanup has run.
The raw file is the single source of truth for "already fetched".

### Blocked-URL persistence per run

Regwall / empty / dead / failed URLs are accumulated into per-status text files in raw_dir:
- Browser path: `regwall_urls.txt`, `empty_urls.txt`
- Proxy_pool path: `dead_urls.txt`, `failed_urls.txt`

These lists are union-merged on each run (read existing → union new → write sorted). They enable
future per-shape triage without re-running the full scrape.

## Regwall instability observation

During scrape-job smoke testing on CoinDesk, regwall rate varied significantly:
- Initial smoke (50 URLs, fresh IP): ~6.7% regwall
- Repeat smoke (10 URLs, same IP, same day): ~80% regwall (4/5)

This suggests an IP-rate component in CoinDesk's regwall: repeated hits from the same IP within
a session trigger escalating blocking. The 20% threshold guard (`REGWALL_FAIL_THRESHOLD`) fires
early on repeat runs, which is the correct behavior — it prevents wasting time on a hot IP.
Resolution: separate investigation (IP rotation or session reset strategy). Not a pipe bug.

## What changed (Stage A — run_scrape_only)

`run_scrape_only` in `pipeline.py` switched from `scrape_chunks()` (scrape→clean→publish per chunk)
to `scrape_chunks_raw()` in `engine/scrape_job.py`:
- Scrapes directly into `raw_dir` (not ephemeral `scrape/{job_id}/chunk_*/`)
- Per-chunk: `_append_to_raw_manifest()` + `_update_blocked_urls({"regwall":…,"empty":…})`
- `RegwallGuardError` now carries `.manifest` on the exception → ok files recovered from `exc.manifest`
  even on abort (no raw data loss)
- No cleanup, no publish

New helpers in `scrape_job.py`: `scrape_chunks_raw()`, `_append_to_raw_manifest()`, `_update_blocked_urls()`.

## What changed (Stage B — run_pipeline both engines)

### Both branches: dedup mode

`filter_new_entries()` now called with `mode="raw"` against `raw_dir` (not `mode="pubdate"` or
`mode="hash_only"` against `collection_dir`). `COLLECTION_BASE` removed from `pipeline.py`.

### Proxy_pool branch (The Block)

Before Stage B: discover → dedup(collection) → scrape(scrape_dir) → cleanup → publish.
After Stage B: discover → **inventory persist** → dedup(raw) → scrape(raw_dir) → raw persist.

- `scrape_entries_proxy(new_entries, raw_dir, ...)` — scrapes into raw_dir directly (was scrape_dir)
- `_persist_inventory(entries, inventory_dir, platform.name)` — new helper in `pipeline.py` called
  after discover; writes `data/news/{name}/inventory/{name}_{year}.txt` (YYYY-MM-DD\t{url}, deduped
  per shard); mirrors CoinDesk's inventory format so The Block gets a master URL list
- `_append_to_raw_manifest(raw_dir, ok_entries)` + `_update_blocked_urls(raw_dir, manifest, {"dead":…,"failed":…})`
  — called after Janitor lifecycle closes (not inside the job context)
- Janitor lifecycle (box_lock, start_job/end_job, AcquireLogger) preserved — only cleanup/publish removed

### Browser branch (CoinDesk run_pipeline)

Before Stage B: discover → dedup(collection) → scrape(scrape_dir) → cleanup → publish.
After Stage B: discover → dedup(raw) → scrape(raw_dir) → raw persist.

- `scrape_entries(new_entries, raw_dir, ...)` — scrapes into raw_dir directly
- `RegwallGuardError`: `exc.manifest` recovered → ok entries persisted even on abort
- `_append_to_raw_manifest` + `_update_blocked_urls({"regwall":…,"empty":…})`

### Dead code removed

`scrape_chunks()` (scrape→clean→publish chunk loop) and `run_cleanup()` removed from
`scrape_job.py` — no live callers after Stage B. `publish_articles` import and `shutil` / `subprocess`
imports removed from `pipeline.py`. `_clear_working_dirs()` and `_check_preconditions()` removed from
`pipeline.py` — `_check_internet()` used directly instead.

`cleanup.py` and `publish.py` kept on disk (not deleted) — available to future skill.

## Relationship to prior process history

- The earlier CoinDesk scrape-job entry — Stage 2a introduced `scrape_chunks()` (scrape→clean→publish per chunk) and chunked crash-safety. Stage A of this decoupling replaced `scrape_chunks` with `scrape_chunks_raw` in `run_scrape_only`.
- The Block poison-URLs entry — The Block's 21h stuck-loop (8 poison URLs, no per-URL cap) and the 22,995 raw files stranded in scrape/ because cleanup ran only after the scrape completed. Stage B's raw-only decoupling means future The Block runs accumulate raw files incrementally — even if the proxy loop terminates early, whatever scrape succeeded is durable in raw/. The poison-URL fix (per-URL attempt cap) remains a separate session.
