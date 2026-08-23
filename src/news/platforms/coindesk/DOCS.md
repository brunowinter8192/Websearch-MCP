# src/news/platforms/coindesk/

## Role

CoinDesk platform implementation. Imported for side-effects by `__main__.py` — the import
registers `CoinDeskPlatform()` into the registry. No other module should import from here directly.

## Public Interface

`__init__.py` exports `CoinDeskPlatform` (implements `Platform` Protocol).
Auto-registers via `register(CoinDeskPlatform())` at module end.

## Modules

### config.py (34 LOC)

**Purpose:** Platform constants — REGWALL_SIGNALS, SCRAPE_CONFIG (ScrapeConfig()), timeline-API
discovery params (TIMELINE_BASE, COINDESK_BASE, TARGET_URL, CALL_DELAY, REWARM_EVERY,
CLICKS_WARMUP, CLICKS_REWARM, MAX_CURSOR_FALLBACKS, CHECKPOINT_EVERY, DEFAULT_DELTA_DAYS,
FULL_MODE_FLOOR, DISCOVER_DIR, SKIP_HEADERS).
**Called by:** `browser.py`, `discover.py`, `__init__.py`.

### browser.py (169 LOC)

**Purpose:** Chrome browser launch + pydoll HAR-capture machinery for the initial feed warmup.
`browser_load_feed(n_clicks)` launches Chrome via `open -gna`, navigates to latest-crypto-news,
clicks "More stories" n times under HAR record, captures the first `/api/v1/articles/timeline`
request (URL + headers + first response body). Returns `(headers, api_url, body_bytes)`.
**Called by:** `discover.py:discover`, `discover.py:try_rewarm`.
**Calls out:** `pydoll` (Chrome CDP), `httpx` (first response replay).

### discover.py (402 LOC)

**Purpose:** Timeline-API cursor loop + master discover management — `discover(timeframe)` orchestrates warmup → load discover → `cursor_loop` (backward-paging, crash-safe per-article shard writes) → incremental discover write.
**Called by:** `__init__.py:CoinDeskPlatform.discover`; `__init__.py:load_scrape_entries` (via the standalone `load_discover_filtered`, the `--scrape-only` interface).
**Calls out:** `httpx` (cursor loop), `browser.py:browser_load_feed` (warmup + re-warm).

### cleanup.py (120 LOC)

**Purpose:** Strip CoinDesk page chrome from raw crawl4ai markdown → pure article body (H1 start-anchor → first end-anchor → `clean_body` strip/normalize passes).
**Called by:** NOT called by any active pipeline path. Available to future cleanup skill.
**Calls out:** stdlib re only.

### __init__.py (44 LOC)

**Purpose:** `CoinDeskPlatform` class wrapping config + discover + cleanup + scrape-entry loading; auto-registers on import; `scrape_engine = "proxy_riding"`, raw output `.html`.
**Called by:** `__main__.py` (side-effect import); `pipeline.py:run_scrape_only` (via `platform.load_scrape_entries`, `platform.scrape_engine`); `pipeline.py:_run_scrape_only_riding` (via `platform.riding_scrape_config`).

## Gotchas

- `REGWALL_SIGNALS` uses precise match strings deliberately — do NOT loosen to generic markers like "subscribe"/"register": those fire on ordinary article footers, producing false regwall positives.
- `cleanup(raw_markdown, entry)`'s `entry` param is unused but part of the platform-generic signature — do not remove as dead.
- At 60k+ article scale the fixed cleaner is fragile — articles occasionally retain the full site footer after cleanup; per-shape diagnosis against the full raw corpus is recommended before cleanup at scale.
