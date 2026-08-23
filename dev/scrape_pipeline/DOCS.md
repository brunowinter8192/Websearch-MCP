# dev/scrape_pipeline/

## Role
Quality monitoring and configuration testing for the URL scraper module (`src/scraper/`). Own-level scripts cover the GH REST API docs pipe-scraper eval, dual-mode A/B comparison, raw-scrape baseline, and Cloudflare markdown-adoption probing. Sub-suites (`filter_eval/`, `browser_eval/`, `garbage_eval/`, `03_cleanup/`, `04_overview_sweep/`, `05_paper_mode/`) each document their own modules.

## Modules

### p1_pipe_scraper.py (97 LOC)

**Purpose:** Core scraper probe — `scrape_urls(urls, delay_s, page_timeout_ms, concurrency, output_dir)` → per-URL metrics dicts. Config locked to: browser, `wait_until="domcontentloaded"`, `delay_before_return_html`, hard `page_timeout`, `DefaultMarkdownGenerator()` raw, no `PruningContentFilter`, no garbage-drop. Saves `<!-- source: url -->\n\nraw_md` per URL when `output_dir` set.
**Calls out:** `crawl4ai` (AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, DefaultMarkdownGenerator).
**Called by:** `07_pipe_scrape_eval.py`.

### 07_pipe_scrape_eval.py (482 LOC)

**Purpose:** Eval harness — three phases via argparse: `phase1` (concurrency/WAF sweep), `phase2` (delay sweep, completeness proxy), `phase3` (full 316-URL run: WAF probe + batched pacing + position-tracked 429s + retry pass).
**Reads:** URL list (hardcoded 316-URL corpus / stratified subset for phase1/2).
**Writes:** `md/07_concurrency_sweep_<ts>.md` (phase1), `md/07_delay_sweep_<ts>.md` (phase2, incl. WAF-contamination note), `md/07_full_run_<ts>.md` (phase3 summary); phase3 also `07_pipe_scrape_eval_data/full_run_<ts>/` — raw markdown corpus, one .md per URL.
**Calls out:** `p1_pipe_scraper.scrape_urls`.
**Called by:** CLI only. `./venv/bin/python dev/scrape_pipeline/07_pipe_scrape_eval.py {phase1,phase2,phase3}`.

### 01_dual_mode_smoke.py (373 LOC)

**Purpose:** A/B comparison harness — parses URLs from a chosen query in a search-results markdown report, scrapes each URL through BOTH production CLI modes in parallel via asyncio: Mode 1 (`scrape_url_raw`, raw markdown to file, no filter) and Mode 2 (`scrape_url`, PruningContentFilter@0.48, 15K char cap, in-memory). Reusable for library A/B testing — replace the cli.py-subprocess invocation with another extraction library.
**Reads:** `--input <path-to-search-md>` (required, e.g. `dev/search_pipeline/md/pipeline_smoke_*.md`), `--query <id-or-text>` (default 1).
**Writes:** `--output-dir` (default `01_dual_mode_data/<ts>/`) — per-mode subdirs (`mode1_raw/`, `mode2_filtered/`) with one .md per URL, plus `01_dual_mode_report.md` at parent level (per-URL byte sizes, garbage detection, first content lines).
**Called by:** CLI only.

### 02_raw_smoke.py (208 LOC)

**Purpose:** Dev-only Mode 1 raw scrape — Crawl4AI direct via `arun_many`, no prod imports, no `cli.py` subprocess. Parses Q24 URLs from a search smoke report, scrapes all in parallel. Slug includes full-URL md5 hash to prevent query-string collisions (e.g. HN `?id=N` URLs both preserved). NO fallback chain (single Crawl4AI config), NO garbage detection, NO cookie strip — fail fast, see what's actually there. Clean baseline for downstream cleanup work + comparison against filter outputs.
**Reads:** `--input <path-to-search-md>`, `--query 24`.
**Writes:** `02_raw_data/<ts>/` — 20 `<slug>_<6-char-md5>.md` files + `02_raw_report.md` triage table. Status `empty` includes optional annotation `(PDF)` or `(plugin-domain: github)`.
**Called by:** CLI only.

### 06_cloudflare_md_adoption.py (282 LOC)

**Purpose:** Adoption probe for the `Accept: text/markdown` server-side markdown convention (Cloudflare Markdown-for-Agents, Vercel edge, others). Probes a curated 29-URL set across three categories (Cloudflare-owned positive controls, likely-CF-fronted candidate sites, non-CF negative controls) with the markdown Accept header via httpx async (Semaphore concurrency 10, 15s timeout). For URLs responding `text/markdown`, fetches a baseline HTML GET to compute byte-reduction. Baseline measurement for Phase-0-fast-path adoption (`fetch_markdown_fastpath` in production); re-run periodically to track adoption growth.
**Reads:** hardcoded 29-URL set.
**Writes:** `md/06_cf_md_adoption_<YYYYMMDD_HHMMSS>.md` — per-URL table (URL, CF-fronted, MD-served, status, content-type, x-md-tokens, HTML-bytes, MD-bytes, byte-reduction, response-ms) plus summary (counts, mean/median byte-reduction on positives, positive-case URL list for run-to-run comparison, server header distribution among CF-fronted hits).
**Called by:** CLI only. `--output-dir` overridable.

## State
`domains.txt` — shared test URL list for `browser_eval/` and `filter_eval/` scripts, one URL per line, `#` comments. `failures.jsonl` (gitignored) — persistent failure log from production `scrape_url` runs; written by `log_scrape_failure()` in `src/scraper/scrape_url.py` at the final failure exit in `scrape_url_workflow()`. Fields: `ts` (ISO 8601 UTC), `url`, `garbage_type` (`http_error`/`cookie_wall`/`login_wall`/`cloudflare`/`nav_dump`/`crawl4ai_error`/null), `status_code` (int/null). Local analysis only — accumulates across production MCP tool calls, not committed.

## Gotchas
`failures.jsonl` inspection: `cat dev/scrape_pipeline/failures.jsonl | jq .`; by garbage_type: `jq -r '.garbage_type // "none"' | sort | uniq -c | sort -rn`; 404s only: `jq 'select(.status_code == 404)'`.
