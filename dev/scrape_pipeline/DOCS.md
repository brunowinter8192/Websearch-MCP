# Scrape Pipeline

Quality monitoring and configuration testing for the URL scraper module.

## Shared Config (pipeline root)

### domains.txt

Test URLs for scripts in browser_eval/ and filter_eval/. One URL per line, comments with `#`.

### failures.jsonl

**Purpose:** Persistent failure log from production `scrape_url` runs. Every URL where all 3 scrape attempts are exhausted (normal networkidle, normal domcontentloaded, stealth networkidle) gets appended as one JSONL line.

**Written by:** `log_scrape_failure()` in `src/scraper/scrape_url.py` — called automatically at the final failure exit in `scrape_url_workflow()`.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ts` | ISO 8601 UTC string | Timestamp of the failure |
| `url` | string | URL that failed to scrape |
| `garbage_type` | string \| null | Last detected garbage type (`http_error`, `cookie_wall`, `login_wall`, `cloudflare`, `nav_dump`, `crawl4ai_error`) or null if no content was returned |
| `status_code` | int \| null | HTTP status code from the last attempt that returned one, or null if not available |

**Usage:**

```bash
# Show all failures
cat dev/scrape_pipeline/failures.jsonl | jq .

# Count by garbage_type
cat dev/scrape_pipeline/failures.jsonl | jq -r '.garbage_type // "none"' | sort | uniq -c | sort -rn

# Find all 404s
cat dev/scrape_pipeline/failures.jsonl | jq 'select(.status_code == 404)'

# Recent failures
tail -20 dev/scrape_pipeline/failures.jsonl | jq .
```

The file is gitignored — it accumulates across production MCP tool calls and is for local analysis only.

## browser_eval/ → decisions/scrape01_browser

### 01_baseline.py

**Purpose:** Scrapes all test domains using the production `scrape_url_workflow` and saves results as numbered iterations with metadata (char count, word count, timestamp).
**Input:** `domains.txt` (pipeline root)
**Output:** `01_baselines/<domain>/iteration_<N>.md` + `metadata_<N>.json`

```bash
./venv/bin/python dev/scrape_pipeline/browser_eval/01_baseline.py
```

### 02_regression.py

**Purpose:** Compares the last two iterations per domain to detect regressions. Generates unified diffs and classifies changes by magnitude (IDENTICAL, MINOR_CHANGE, MODERATE_CHANGE, MAJOR_CHANGE).
**Input:** `01_baselines/`
**Output:** `02_reports/diff_report_<timestamp>.txt`

```bash
./venv/bin/python dev/scrape_pipeline/browser_eval/02_regression.py
```

### 03_browser.py

**Purpose:** Tests multiple Crawl4AI browser configurations for JS-heavy sites that fail with default settings. Compares content yield (char count, word count) across configs with different wait strategies: domcontentloaded baseline, networkidle, extended delay, CSS selector wait, and full page scan.
**Output:** `03_reports/<domain>_<slug>_<config>.md`

```bash
./venv/bin/python dev/scrape_pipeline/browser_eval/03_browser.py
./venv/bin/python dev/scrape_pipeline/browser_eval/03_browser.py https://docs.trychroma.com/docs/overview/telemetry
```

## filter_eval/ → decisions/scrape02_filtering

### 04_filtering.py

**Purpose:** Tests multiple Crawl4AI content filter configurations (PruningFilter at various thresholds, BM25ContentFilter, raw) against test URLs. Saves raw and fit markdown for each config. Includes code block integrity check.
**Input:** `domains.txt` (pipeline root)
**Output:** `04_reports/<domain>_<config>_raw.md` / `_fit.md`

URLs are processed in parallel (PARALLEL_URLS=5, Semaphore). The 5 configs per URL run serially (fast, no benefit from parallelism).

```bash
./venv/bin/python dev/scrape_pipeline/filter_eval/04_filtering.py
./venv/bin/python dev/scrape_pipeline/filter_eval/04_filtering.py https://example.com
```

### 05_filter_debug.py

**Purpose:** Instruments the scraping pipeline step-by-step to show what each filter removes at each stage. Reports include node counts, character counts, percentage deltas, and markdown previews of removed content. Used during active profile development.
**Input:** `domains.txt` (pipeline root)
**Output:** `05_reports/<profile>/<domain>_<timestamp>.txt`

```bash
./venv/bin/python dev/scrape_pipeline/filter_eval/05_filter_debug.py https://de.wikipedia.org/wiki/Biber
./venv/bin/python dev/scrape_pipeline/filter_eval/05_filter_debug.py --profile wiki
./venv/bin/python dev/scrape_pipeline/filter_eval/05_filter_debug.py --all
```

### 06_content_source.py

**Purpose:** Tests Crawl4AI's `content_source` parameter across many URLs per domain. Scrapes each URL with 6 configurations in parallel (5 URLs concurrent, 6 configs per URL concurrent) and saves the raw markdown output as individual .md files for manual inspection. Max 20 URLs per domain.
**Input:** Explore pipeline reports from `../../explore_pipeline/01_reports/*.json`
**Output:** `05_content_source/<domain>/<config>/<NN>_<slug>.md`

Configs tested:

| Config | content_source | Filter | Markdown Field |
|--------|---------------|--------|----------------|
| cleaned_html | cleaned_html | none | raw_markdown |
| cleaned_html_pruning | cleaned_html | PruningFilter 0.48 | fit_markdown |
| raw_html | raw_html | none | raw_markdown |
| raw_html_pruning | raw_html | PruningFilter 0.48 | fit_markdown |
| fit_html | fit_html | none | raw_markdown |
| fit_html_pruning | fit_html | PruningFilter 0.48 | fit_markdown |

```bash
./venv/bin/python dev/scrape_pipeline/filter_eval/06_content_source.py --all
./venv/bin/python dev/scrape_pipeline/filter_eval/06_content_source.py --domain searxng_docs
./venv/bin/python dev/scrape_pipeline/filter_eval/06_content_source.py --url https://example.com
```

## garbage_eval/ → decisions/scrape03_garbage

### 07_result_inspect.py

**Purpose:** Inspects the full Crawl4AI `CrawlResult` object to discover available metadata fields. Scrapes 3 URLs (normal, 404, consent-heavy) and enumerates all result attributes with types and values. Key finding: `result.status_code` is available and reliable (404 for error pages, 200 for good pages). `result.success` is always True and unreliable.
**Output:** `07_reports/result_inspect_<timestamp>.md`

```bash
./venv/bin/python dev/scrape_pipeline/garbage_eval/07_result_inspect.py
```

### 08_garbage_edge_cases.py

**Purpose:** Tests `is_garbage_content()` against known edge case URLs (consent-prefix sites, padded 404 pages) and baseline URLs. Scrapes raw and filtered content, runs garbage detection on both, and tests header-zone (first 500 chars) detection for padded 404s.
**Output:** `08_reports/garbage_edge_cases_<timestamp>.md`

```bash
./venv/bin/python dev/scrape_pipeline/garbage_eval/08_garbage_edge_cases.py
```

### 09_garbage_fix_prototype.py

**Purpose:** Prototypes and validates garbage detection improvements. Tests two fixes: (1) status_code based 404 detection, (2) consent prefix stripping. Validates against edge case and baseline URLs to confirm no false positives.
**Output:** `09_reports/garbage_fix_prototype_<timestamp>.md`

```bash
./venv/bin/python dev/scrape_pipeline/garbage_eval/09_garbage_fix_prototype.py
```

### 10_live_garbage_test.py

**Purpose:** Live integration test for garbage detection. Two modes: `--search QUERY` fires a live SearXNG search, scrapes the top 10 results, and runs garbage detection on each. `--edge-cases` scrapes known problem URLs (consent-prefix, padded 404, paywall). Results logged to `failures.jsonl` and saved as report.
**Input:** Live SearXNG search or hardcoded edge-case URLs
**Output:** `10_reports/live_garbage_test_<timestamp>.md`

```bash
./venv/bin/python dev/scrape_pipeline/garbage_eval/10_live_garbage_test.py --search "cookie policy GDPR compliance"
./venv/bin/python dev/scrape_pipeline/garbage_eval/10_live_garbage_test.py --edge-cases
```

### 12_scrape_methods.py

**Purpose:** Bulk scrape comparison across 3 browser methods. Reads URLs from engine isolation reports (`dev/search_pipeline/weights_eval/11_reports/engine_*.md`), deduplicates, and scrapes each URL 3 times with different configs: (1) networkidle, (2) domcontentloaded, (3) stealth+networkidle. Measures timing, content length, and garbage type per scrape.
**Input:** `engine_*.md` files from `dev/search_pipeline/weights_eval/11_reports/`
**Output:** `12_reports/url_pool.txt` (deduplicated URL list) + `12_reports/method_1_networkidle/`, `method_2_domcontentloaded/`, `method_3_stealth/` (one .md per URL with metadata header) + `12_reports/summary.md`

```bash
./venv/bin/python dev/scrape_pipeline/browser_eval/12_scrape_methods.py
```

Full run: ~5-6 hours for 660 URLs × 3 methods. Each .md includes metadata header (url, method, status_code, chars, time_seconds, garbage_type).

## Workflows

### Regression (browser_eval 01 → 02)

Standard workflow when changing the production scraper. Run baseline, then compare with previous iteration.

### Browser Debug (browser_eval 03)

For JS-heavy sites that fail with default settings. Compare wait strategies to find what works.

### Filter Exploration (filter_eval 04 → 05)

Explore filter configurations. 04 gives broad comparison, 05 gives step-by-step pipeline transparency.

### Content Source (filter_eval 06)

Large-scale comparison of which HTML source + filter combination produces the best markdown for downstream cleanup agents. Requires explore_pipeline/01_reports as input. Output is raw .md files for manual review.

### Garbage Investigation (garbage_eval 07 → 08 → 09)

Investigate edge cases in garbage detection. 07 discovers available metadata. 08 reproduces failures. 09 prototypes and validates fixes before production code changes.
