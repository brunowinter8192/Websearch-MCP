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

`REGWALL_SIGNALS` uses precise match strings deliberately — do NOT loosen to generic markers like
"subscribe"/"register": those fire on ordinary article footers, producing false regwall positives.
`CALL_DELAY = 0.3` (seconds between cursor calls). `REWARM_EVERY = 240.0` (seconds; proactive re-warm
interval — see `discover.py`'s proactive-rewarm gating note). `CLICKS_WARMUP = 8` — CoinDesk's SSR
buffer clears at ~click 6; 8 gives margin. `FULL_MODE_FLOOR = "2018-01-01"` — Binance candle data
(used for cross-referencing) starts 2017-08, so full-mode backfill doesn't need to go earlier.

### browser.py (169 LOC)

**Purpose:** Chrome browser launch + pydoll HAR-capture machinery for the initial feed warmup.
`browser_load_feed(n_clicks)` launches Chrome via `open -gna`, navigates to latest-crypto-news,
clicks "More stories" n times under HAR record, captures the first `/api/v1/articles/timeline`
request (URL + headers + first response body). Returns `(headers, api_url, body_bytes)`.
**Called by:** `discover.py:discover`, `discover.py:try_rewarm`.
**Calls out:** `pydoll` (Chrome CDP), `httpx` (first response replay).

### discover.py (402 LOC)

**Purpose:** Timeline-API cursor loop + master discover management.
`discover(timeframe)` orchestrates: warmup → load discover → `cursor_loop` →
incremental discover write → return entry list `[{url, lastmod, publication_date, title, section, _new}]`.

Cursor loop pages backward in reverse-chronological order. Each 16-article batch: parse, filter
live-blogs, append genuinely new URLs to per-year discover shards (`data/news/coindesk/discover/
coindesk_{year}.txt`, format `YYYY-MM-DD\t<url>`). Termination: oldest article in batch < stop_date.
Re-warm strategy: httpx feedpage GET first; browser re-warm as fallback. Crash-safe: URLs written
per-article; re-run skips already-present URLs via load_discover() diff. Proactive re-warm fires
every `REWARM_EVERY` seconds mid-loop (in addition to the reactive on-failure path above), but ONLY
once `httpx_rewarm_confirmed` is set — i.e. only after a prior reactive re-warm has proven the cheap
httpx-feedpage-GET method works for the current session; never fires on a session that has re-warmed
exclusively via full browser re-warm.

**Called by:** `__init__.py:CoinDeskPlatform.discover`.
**Calls out:** `httpx` (cursor loop), `browser.py:browser_load_feed` (warmup + re-warm).

Timeframe parsing: `"full"` → FULL_MODE_FLOOR (`"2018-01-01"`);
integer string N → today − N days; anything else (incl. `"delta"`) → DEFAULT_DELTA_DAYS (30).

`load_discover_filtered(discover_dir, year, from_date, to_date, limit)` — standalone function (not part of `discover()`). Reads per-year shards `coindesk_{year}.txt`; applies optional date-range filter (`from_date`/`to_date` as `YYYY-MM-DD`); caps result at `limit`. Returns `[{url, publication_date}]`. Called by `__init__.py:load_scrape_entries` for the `--scrape-only` flow.

`cursor_loop` (2026-08-20, 138→63 code lines): run-wide accumulators (`ok_calls`, `fallback_count`,
`rewarm_count`, `httpx_rewarm_confirmed`, `oldest_date`, `last_rewarm_t`) bundled into a
`_CursorLoopStats` scratch dataclass (mirrors `proxy_riding/rider.py`'s `_RideProgress` pattern).
`_process_batch` — per-batch entry build/live-blog-filter/dedup/shard-write/oldest-date tracking.
`_fetch_next_page` — the cursor-fallback-URL loop (tries up to `MAX_CURSOR_FALLBACKS` trailing
articles as pagination anchors). `_handle_cursor_exhaustion` — the re-warm-on-exhaustion path;
returns `(headers, body, fatal: bool)` so the caller can distinguish "re-warm failed, stop now" from
"no fallback candidate existed at all, stop via the generic no-body check" WITHOUT printing both
stop messages on the fatal path (the two checks are sequential in the original, and only the second
one's message must fire when the first one's `fatal=True`). The outer `while True:` loop's own
control flow (empty-response check, stop-date-floor termination check, proactive-rewarm check, the
two-stage exhaustion/no-body break sequence) stays inline in `cursor_loop` itself.

### cleanup.py (120 LOC)

**Purpose:** Strip CoinDesk page chrome from raw crawl4ai markdown → pure article body.
Logic: H1 start-anchor → first end-anchor (_END_ANCHORS: MORE_FOR_YOU, PRIVACY, TAG_FOOTER) →
clean_body (tag-footer strip, image strip, byline/date strip, inline-link substitution, paragraph normalization).
Not called by `run_pipeline` or `run_scrape_only` — reserved for future cleanup skill against raw corpus.
**Called by:** NOT called by any active pipeline path. Available to future cleanup skill.
**Calls out:** stdlib re only.

No H1 found → returns `raw_markdown.strip()` (fallback, logged upstream).
`cleanup(raw_markdown, entry)`'s `entry` param is currently unused — kept for future extension (a
platform-generic `Platform.cleanup(raw_markdown, entry)` signature); do not remove it as dead.

`_RE_TAG_FOOTER` (end-anchor detection, requires ≥2 concatenated `[text](url)` groups) vs
`_RE_TAG_LINE` (body strip, 1+ groups — broader, because orphan single-tag lines also appear
mid-body) are deliberately different patterns for the same visual shape; `_RE_TAG_LINE` is applied
in `_strip_and_substitute_lines` BEFORE inline-link substitution so the `[text](url)` form is still
matchable at that point.
`find_end_anchor`'s `end_idx` is exclusive — the body slice is `body_lines[start_idx:end_idx]`;
no anchor found → `(len(body_lines), "NONE")`.

`clean_body` (2026-08-20, 52→8 code lines): the two comment-delineated passes extracted 1:1 —
`_strip_and_substitute_lines` (Pass 1: per-line strip/substitute rules + trailing-ws count) and
`_normalize_paragraphs` (Pass 2: paragraph-boundary blank-line insertion + blank-run collapse). The
leading/trailing blank-line trim stayed in `clean_body` itself (operates on Pass 2's already-built
result, too small to be its own helper).

Gotcha: at 60 k+ article scale, a fixed cleaner is fragile — CoinDesk articles occasionally retain the
full site footer even after cleanup (observed during scrape-job runs). Per-shape diagnosis against the
full raw corpus is the recommended approach before cleanup at scale.

### __init__.py (44 LOC)

**Purpose:** `CoinDeskPlatform` class wrapping config + discover + cleanup + scrape-entry loading; auto-registers on import.
`scrape_engine = "proxy_riding"` — routes `run_scrape_only` to the proxy-riding engine (bypasses
browser chunking). `riding_scrape_config = RidingScrapeConfig()` — production defaults: `n_slots=64`,
`n_browsers=4`, `stall_timeout_s=300.0`, `burn_threshold=2`, `page_timeout_ms=8_000`. Raw output is
`.html` (not `.md`) — `data/news/coindesk/raw/{hash}.html`. `proxy_scrape_config = None`.
Attribute `timeframe: str = "30"` set by `__main__` via `--timeframe`.
`load_scrape_entries(year, from_date, to_date, limit)` delegates to `discover.py:load_discover_filtered` — exposes the `--scrape-only` interface required by `run_scrape_only()` in `pipeline.py`.
**Called by:** `__main__.py` (side-effect import); `pipeline.py:run_scrape_only` (via `platform.load_scrape_entries`, `platform.scrape_engine`); `pipeline.py:_run_scrape_only_riding` (via `platform.riding_scrape_config`).
