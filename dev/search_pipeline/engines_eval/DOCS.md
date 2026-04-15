# engines_eval/

Engine evaluation and stealth testing scripts for the search pipeline (pydoll-based custom engines).

Maps to: `decisions/stealth01_detection_layers.md` (detection layers, patch matrix, drop decision).

## Config Files

### engine_selectors.py

**Purpose:** Declarative selector config for all search engines used in stealth tests. Per-engine: URL builder, pydoll wait/parse JS, proxy, settle_seconds, captcha detection JS, consent cookies. HTTPX engines marked with `{"type": "httpx"}`.
**Used by:** `27_stealth_test.py`, `28_stress_test.py`

Active engines: google, google scholar, bing, crossref
Parked (commented out): brave — see "Parked: Brave & Dropped Engines" below

### stealth_config.py

**Purpose:** Global stealth configuration dataclass (`StealthConfig`) with all pydoll levers: browser launch args, JS fingerprint patches (webgl, canvas, permissions, computed_style), CDP settings (UA override, extra headers, network emulation), rate limits per engine. `build_chrome_args()`, `build_js_patches()`, `build_cdp_config()` generate the runtime config from the dataclass.
**Used by:** `27_stealth_test.py`, `28_stress_test.py`

Tune here, test with `27_stealth_test.py`. One config change = one test run.

## Test Scripts

### 01_engines.py

**Purpose:** Run all test queries against the search API with profile-based parameters and generate a markdown quality report. Reads `queries.txt` + `profiles.yml` (pipeline root), paginates up to 3 pages, deduplicates, reports top domains and per-query result tables.
**Output:** `01_reports/search_report_<timestamp>.md`

```bash
# Standard run
./venv/bin/python dev/search_pipeline/engines_eval/01_engines.py

# A/B compare mode: each query run with its profile AND general
./venv/bin/python dev/search_pipeline/engines_eval/01_engines.py --compare
```

**Known Breakage Phase 2:** `compute_settings_hash()` references `src/searxng/settings.yml` (deleted in engine-cut). Script will throw `FileNotFoundError` on startup. Fix: remove `compute_settings_hash()` and the `settings_hash` column from the report, or replace with a different config fingerprint.

### 25_engine_breakpoint.py

**Purpose:** Find the breakpoint query for a single engine — run queries from `queries.txt` sequentially until the engine fails (zero results or error). Reports per-query result counts and the first failure point.
**Output:** `25_reports/breakpoint_<engine>_<timestamp>.md`

```bash
./venv/bin/python dev/search_pipeline/engines_eval/25_engine_breakpoint.py --engine google
./venv/bin/python dev/search_pipeline/engines_eval/25_engine_breakpoint.py --engine bing --limit 20
```

### 26_all_engines_smoke.py

**Purpose:** Smoke test all engines with a small query set — 1 query per engine, checks that each returns results. Faster than a full stresstest; used to verify production is live after config changes.
**Output:** `26_reports/smoke_<timestamp>.md`

```bash
./venv/bin/python dev/search_pipeline/engines_eval/26_all_engines_smoke.py
./venv/bin/python dev/search_pipeline/engines_eval/26_all_engines_smoke.py --engine google
```

**Note:** ENGINES list still contains the old 9-engine set. After engine-cut, only the 4 survivor engines will return results; the others will produce errors/zero results but won't break the script.

### 27_dom_inspect.py

**Purpose:** One-shot DOM inspector — navigate Google with a pydoll browser, dump the result container structure to stdout. Used to reverse-engineer CSS selectors when Google changes its DOM layout.
**Output:** JSON DOM dump to stdout (no report file)

```bash
./venv/bin/python dev/search_pipeline/engines_eval/27_dom_inspect.py
```

### 27_dom_inspect_all.py

**Purpose:** Inspect DOM structure for all pydoll engines in one Chrome session. Navigates each engine, dumps the result container structure. Used to bulk-check selector validity after engine DOM changes.
**Output:** JSON DOM dump to stdout per engine (no report file)

```bash
./venv/bin/python dev/search_pipeline/engines_eval/27_dom_inspect_all.py
```

### 27_stealth_test.py

**Purpose:** Single-engine, single-query stealth test. Launches a pydoll browser with the current `DEFAULT_CONFIG`, navigates to the engine, detects consent/captcha/results, optionally saves a screenshot. Core diagnostic tool for the single-variable testing protocol.
**Output:** `27_reports/reports/<engine>_<timestamp>.md` + optional `27_reports/screenshots/<engine>_<timestamp>.png`

```bash
./venv/bin/python dev/search_pipeline/engines_eval/27_stealth_test.py google "python asyncio"
./venv/bin/python dev/search_pipeline/engines_eval/27_stealth_test.py google "python asyncio" --screenshot
./venv/bin/python dev/search_pipeline/engines_eval/27_stealth_test.py google "python asyncio" --headed
```

CLI flags: `engine` (positional), `query` (positional), `--headed` (visible browser), `--screenshot`

### 28_stress_test.py

**Purpose:** Full 30-query stress test across all active engines in parallel (asyncio.gather). Each pydoll engine gets its own Chrome browser instance. Measures X/30 success rate, first failure point, timing per engine. Primary tool for engine-cut decisions.
**Output:** `28_reports/stress_<timestamp>.md`

```bash
# All active engines, all queries
./venv/bin/python dev/search_pipeline/engines_eval/28_stress_test.py

# Single engine, 30 queries
./venv/bin/python dev/search_pipeline/engines_eval/28_stress_test.py --engine google --limit 30

# Headed browser (for visual debugging)
./venv/bin/python dev/search_pipeline/engines_eval/28_stress_test.py --engine bing --headed
```

CLI flags: `--engine <name>` (filter to one engine), `--limit N` (only first N queries), `--headed`

## Parked: Brave & Dropped Engines

### Drop Decision

5 engines dropped after 30-query stresstest 2026-04-07. Full rationale: `decisions/stealth01_detection_layers.md` → "Verdict" section.

| Engine | Score | Reason |
|--------|-------|--------|
| Brave | 1–10/30 | PoW CAPTCHA, no patch combination reaches 30/30 |
| Startpage | 0/30 | Zero results, root cause unknown |
| DuckDuckGo | 6/30 | Redirects to Bing via ddgs library bug |
| Mojeek | 15/30 | IP-based rate limit (15 req/60s, not bypassable) |
| Semantic Scholar | 3/30 | 429 rate limit (API) |

Core architecture incompatibility: all CAPTCHA solutions require per-engine timeouts or retries. In `asyncio.gather`, the slowest engine blocks the aggregate response. Google: ~0.2s. Brave CAPTCHA: 10–15s minimum.

### Brave Park State

Brave config is preserved in dev files for future testing sessions:

- **`engine_selectors.py`**: Brave entry commented out with `# PARKED`. URL builder `_brave_url` also commented out.
- **`stealth_config.py`**: Brave `rate_limits` entry remains active (needed when testing via `27_stealth_test.py` directly).
- **`28_stress_test.py`**: Brave commented out in `PYDOLL_ENGINES` list.

Startpage, DuckDuckGo, Mojeek, Semantic Scholar: fully removed from all dev files (not parked).

### Scripts Relevant for Survivor Engines vs Brave-Only

| Script | Survivor Engines | Brave Testing |
|--------|-----------------|---------------|
| `28_stress_test.py` | Yes (4 engines active) | `--engine brave` after un-commenting PYDOLL_ENGINES entry |
| `27_stealth_test.py` | Yes (google, bing, google scholar) | `brave` engine still in ENGINE_SELECTORS when un-commented |
| `27_dom_inspect_all.py` | Yes | Needs brave entry un-commented in engine_selectors.py |
| `26_all_engines_smoke.py` | Yes (with errors for dropped engines) | Not useful for Brave (browser-based, not httpx) |
| `25_engine_breakpoint.py` | Yes | Yes (via `--engine brave`) |
| `01_engines.py` | Yes (via profiles.yml) | Not directly — uses httpx wrapper, no pydoll |

### How to Resume Brave Testing

1. Un-comment Brave entry in `engine_selectors.py` (search for `# PARKED`)
2. Un-comment `_brave_url` in `engine_selectors.py`
3. Un-comment Brave in `PYDOLL_ENGINES` in `28_stress_test.py`
4. Run: `./venv/bin/python dev/search_pipeline/engines_eval/27_stealth_test.py brave "test query" --screenshot`
5. See `decisions/stealth01_detection_layers.md` → "Wie Brave-Arbeit fortgesetzt werden kann"
