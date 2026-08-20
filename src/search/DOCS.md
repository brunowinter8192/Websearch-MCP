# src/search/

## Role

pydoll-based parallel web-search pipeline behind the `search_web` and `search_engine_drilldown` CLI subcommands. Fans a single query out across 14 engines concurrently, dedups URLs into per-engine pools, caches the pools to disk, and returns an engine-breakdown table; the drilldown subcommand re-reads the cache to emit one engine's URLs. As of 2026-08-05, the drilldown path is ALSO logged (`record_type: "drilldown"` in `query_log.jsonl`, `cli.py`) — closing the "a scraped URL cannot be traced back to which engine(s) offered it" gap; see query_logger.py's module entry. Touch this package when changing engine fan-out, dedup/pool-building, the disk cache, or rate-limiting. Individual engine parsers live one level down in `engines/`.

## Public Interface

`__init__.py` is empty — modules are imported by path:

- `search_web_workflow(query, language="en", time_range=None, engines=None, …, query_modifier_map=None)` (search_web.py) — the `search_web` subcommand entry (`cli.py`). Returns `list[TextContent]` (one breakdown table).
- `fetch_search_results(...)` (search_web.py) — sync wrapper for dev scripts; returns the raw result list, no pool-building.
- `cache_key`, `cache_read`, `format_engine_pool` (cache.py) — the `search_engine_drilldown` subcommand path (`cli.py`).
- `log_query(record)` (query_logger.py) — called directly by `cli.py` (drilldown logging, as of 2026-08-05) in addition to `search_web.py`.
- `kill_stale_chrome()` (browser.py) — registered `atexit` in `cli.py`.

## Flow

`search_web_workflow` selects engines → `asyncio.gather` of `_engine_with_timing` tasks (each acquires a rate-limiter token, then runs the engine) → flat `raw_results` → `build_engine_pools` dedups by URL owner → post-dedup pool cap to Google's pool size (fallback 10) → `_format_breakdown` table → `cache_write` to `~/.cache/websearch/<key>.json`. `search_engine_drilldown` skips all of this: `cache_read` the per-engine pool → `format_engine_pool` numbers + cleans snippets.

## Modules

### search_web.py (360 LOC)

**Purpose:** Search orchestrator. Fans out across the 14 active engines via `asyncio.gather`, then builds pools → caps → formats → caches. Post-dedup pool cap (`_cap_pools`): K = `len(pools['google'])` if >0 else 10, each pool trimmed to `pool[:K]` (prevents CrossRef/OpenAlex/StackExchange/OpenLibrary drilldown floods). Three-tier timeout: `ENGINE_WATCHDOG_TIMEOUT=3.6s` default, `ENGINE_WATCHDOG_OVERRIDE` per-engine (open_library 6.0, semantic_scholar 5.0, crossref 6.0, startpage 6.0, brave 6.0) — `bing`, `yandex`, and `marginalia` deliberately have NO override entry: all three probed well under the default (yandex additionally short-circuits its own blocked-query path via an upfront `showcaptcha`-URL check; marginalia's httpx-API round-trip never approaches 3.6s regardless of rate-limit outcome). `RATE_WAIT_TIMEOUT=60.0s` acquire cap → RATE_SKIP. `_engine_with_timing` returns a 5-tuple `(results, rate_wait_ms, search_ms, status, drop_reason)` with sub-classified TIMEOUT/ERROR statuses — the exception-to-status mapping is `_classify_engine_exception` (one `except Exception` dispatching via isinstance, same match order as the original except chain it replaced). Two-record logging: `engine_run` after fanout, `workflow_summary` after pool-build — as of 2026-08-05, `workflow_summary` also carries `search_key` (the same value `cache_key(...)` computed for this call, threaded into `_build_query_log_entry`) — the join key a `cli.py` "drilldown" log record correlates back to; see query_logger.py. `fetch_search_results` is a sync dev wrapper (raw list, no pools). `_DEFAULT_ENGINES` (the 14-engine default set) is defined locally in this module's INFRASTRUCTURE section.
**Reads:** query + params; per-engine caps in `ENGINE_MAX_RESULTS`; default set via `_DEFAULT_ENGINES`.
**Writes:** disk cache `~/.cache/websearch/<key>.json` (via cache_write); query log (via log_query).
**Called by:** `cli.py` (search_web_workflow); dev scripts (fetch_search_results).
**Calls out:** `httpx`, `pydoll.exceptions`, `websockets.exceptions`, `mcp.types.TextContent`; `engines/` (all 14 engine classes); `cache` (cache_key, cache_write), `rate_limiter` (get_limiter), `merge` (build_engine_pools), `result` (SearchResult), `status`, `query_logger` (log_query).

### merge.py (37 LOC)

**Purpose:** Cross-engine URL dedup + per-engine pool builder. `build_engine_pools(results)` groups SearchResults by URL, assigns each URL to the owner engine (lowest position value, random tie-break), returns `{engine → [owned SearchResult, …]}` sorted by native position. Populates `engine_positions` on each result (all engines' positions for that URL). Constructs a FRESH `SearchResult` per winning URL — any field not explicitly named in that constructor call (e.g. `date`) is silently dropped, so new `SearchResult` fields must be threaded through here explicitly.
**Reads:** flat `list[SearchResult]` from fan-out.
**Writes:** none (returns the pool dict).
**Called by:** `search_web.py`.
**Calls out:** `result` (SearchResult).

### cache.py (118 LOC)

**Purpose:** Disk cache for per-engine pools, backing `search_engine_drilldown`. Cache key `sha256(query|language|engines|time_range)[:16]`; path `~/.cache/websearch/<key>.json`; 1h mtime TTL; atomic write via `tempfile.mkstemp` + `os.replace`. JSON holds the full per-engine pool dict with native positions. `format_engine_pool(pool, engine_name, query)` renders one engine's pool as a numbered list with snippet cleanup applied. `date` (ISO-8601 partial: `"YYYY"`/`"YYYY-MM"`/`"YYYY-MM-DD"`, or `None`) is serialized per entry and rendered as a `Date: <value>` line when present; read via `entry.get("date")` so cache files written before this field existed (no `date` key at all) still render without error.
**Reads:** cache files under `~/.cache/websearch/`.
**Writes:** `~/.cache/websearch/<key>.json`.
**Called by:** `cli.py` (cache_key, cache_read, format_engine_pool); `search_web.py` (cache_key, cache_write).
**Calls out:** `result` (SearchResult), `snippet` (_strip_bloat, _truncate, MAX_SNIPPET_LEN).

### snippet.py (63 LOC)

**Purpose:** Snippet text utilities for drilldown display. `_strip_bloat(text)` (HTML unescape + 9 bloat patterns), `_truncate(text, max_len)` (sentence-aware, `MAX_SNIPPET_LEN=500`).
**Reads:** raw snippet string.
**Called by:** `cache.py` (format_engine_pool).
**Calls out:** none (stdlib `html`, `re`).

### query_logger.py (106 LOC)

**Purpose:** Append-only JSONL query log. `log_query(record)` writes one line. Three record types: `engine_run` (per fanout), `workflow_summary` (after pool-build), and `drilldown` (as of 2026-08-05, written by `cli.py`'s `search_engine_drilldown` branch on every call — hit, cache-miss-then-searched, cache-miss-then-still-failed, and engine-not-in-pools all log; the `mode` field this record used to carry was dropped when the `--books`/`--pdf`/`--docs` flags were removed — absence means the record predates or postdates the field). `workflow_summary`/`drilldown` share a `search_key` field (`= cache.cache_key(...)`'s output for that search) — the exact join key correlating a drilldown back to the search it came from (or the fresh search it triggered on a cache miss); NOT a random per-run id — two separate searches of the same query correctly share one value. LIMIT, stated in the schema comment itself: this file is lazily pruned on a 14-day window, so a `drilldown` record can outlive the `workflow_summary` it points at — an unresolvable `search_key` is ordinary retention, not corruption. Correlation does NOT extend to `src/logs/scrape_log.jsonl` (separate file, no shared identifier) — a scraped URL still cannot be mechanically tied to the drilldown that offered it.
**Reads:** `WEBSEARCH_QUERY_LOG_PATH` env (fallback `src/logs/query_log.jsonl`).
**Writes:** `src/logs/query_log.jsonl`.
**Called by:** `search_web.py` (engine_run, workflow_summary); `cli.py` (drilldown, as of 2026-08-05).
**Calls out:** `src/log_janitor.py` (maybe_prune_jsonl).

### browser.py (156 LOC)

**Purpose:** pydoll Chrome lifecycle. One shared Chrome, headed by default and launched BACKGROUNDED via macOS `open -g -n` (never steals focus — `_open_background_process_creator` swapped onto `_browser_process_manager` after `Chrome(options)`, before `await browser.start()`; `WEBSEARCH_HEADLESS` env var forces headless instead, for debugging or a no-display machine — direct launch, no `open -g` needed). A new tab per engine for isolation (`new_tab()` — CDP-level, no new OS process). `BACKGROUNDING_FLAGS` (Playwright's own Chromium defaults) applied unconditionally; evidentiary status of their effect is honestly uncertain — see the code comment. No JS fingerprint patches, no UA override, no explicit `--window-size` — `process-docs/browser_posture/` (Milestones 1-2) found the prior JS screen/getComputedStyle patches and the hardcoded UA/window-size all contradicted observable reality under headed and removed them; Chrome now reports its own real values throughout. Cleanup paths: `kill_tab(tab)` (browser-level `Target.closeTarget`, 5s cap), `close_browser()` (in-loop shutdown for dev), `kill_stale_chrome()` (nuclear `pkill` fallback — the actual teardown for the backgrounded launch, since `open -g`'s Popen is a short-lived wrapper, not Chrome itself).
**Reads:** `WEBSEARCH_HEADLESS` env var (singleton browser on first access).
**Writes:** Chrome session dir under the user-data-dir.
**Called by:** `cli.py` (kill_stale_chrome, atexit); `engines/` (new_tab, kill_tab — google, duckduckgo, lobsters, semantic_scholar, scholar).
**Calls out:** `pydoll` (Chrome, ChromiumOptions, BrowserProcessManager, TargetCommands); `open`/`pkill` (macOS process control).

### rate_limiter.py (48 LOC)

**Purpose:** Per-engine token-bucket rate limiter. Module-level `_limiters` registry populated at engine import (`RateLimiter(max_requests=4, window_seconds=60)`); consumed via `get_limiter(name).acquire()` before engine work.
**Reads / Writes:** in-memory `_limiters` registry.
**Called by:** `search_web.py` (get_limiter); `engines/` (RateLimiter, _limiters).
**Calls out:** none (stdlib `asyncio`, `time`).

### result.py (16 LOC)

**Purpose:** `SearchResult` dataclass. Fields: `url, title, snippet, engine, position, preview, engines, snippets, engine_positions, date`. `engine_positions` populated by `build_engine_pools`; `engines`/`snippets`/`preview` retained for dev-script backward compat. `date: str | None` — ISO-8601 partial date at native precision (`"YYYY"`, `"YYYY-MM"`, or `"YYYY-MM-DD"`; the string's own shape is the precision signal, no separate precision field); populated only by `engines/openalex.py`, `engines/stack_exchange.py`, `engines/crossref.py`, `engines/open_library.py` — the other 10 engines leave it at the `None` default.
**Called by:** `search_web.py`, `merge.py`, `cache.py`, `engines/`.
**Calls out:** none (stdlib `dataclasses`).

### status.py (26 LOC)

**Purpose:** Engine-status string constants for the query log + audit — 17 total: 5 legacy (OK/EMPTY/TIMEOUT/ERROR/RATE_SKIP) + 5 EMPTY + 3 TIMEOUT + 4 ERROR sub-statuses.
**Called by:** `search_web.py`, `engines/` (imported as `status as S`).
**Calls out:** none.

## State

Two module-owned states. `rate_limiter._limiters` — the per-engine token-bucket registry, populated at engine import, read/mutated via `get_limiter().acquire()`. The disk cache (`~/.cache/websearch/`) — written by `cache.cache_write` (from search_web), read by `cache.cache_read` (from the drilldown path); 1h TTL, atomic writes. No cross-request in-memory search state — each `search_web_workflow` call is independent.

## Gotchas

- Active engines (9): google, duckduckgo, mojeek, lobsters, semantic_scholar (pydoll); crossref, openalex, stack_exchange, open_library (HTTP). Google Scholar (`engines/scholar.py`) is decoupled from the default pool. brave / startpage / bing were dropped.
- Two-call architecture: `search_web` returns counts only (no URLs); URLs come from `search_engine_drilldown` reading the cache. The drilldown query MUST match the prior `search_web` call or the cache key misses.
- Post-dedup pool cap keys off Google's pool size — if Google was CAPTCHA'd or excluded, K falls back to 10.
- Stealth config lives in `browser.py` (headed-backgrounded launch, `--disable-blink-features=AutomationControlled`, `BACKGROUNDING_FLAGS`, browser preferences) + per-engine files (SOCS cookie for Google) — no config file, no JS fingerprint patches or UA override (removed — see `browser.py`'s module history via `process-docs/browser_posture/`).
- `WEBSEARCH_HEADLESS` env var forces headless (debugging, or a machine with no display) — unset means headed, backgrounded, the default. Documented in `.env.example`.
- pydoll tab cleanup uses `kill_tab` (browser-level close), NOT `tab.close()` — the latter hung 65s on non-cooperative renderers.
- CLI dispatch hardcodes `language="en"`, `time_range=None`, `engines=None`; the full `search_web_workflow` signature is retained only for dev-script callers.
- **A URL can NEVER be attributed to exactly one engine** — engines overlap heavily; the same URL routinely appears in 3+ drilled engines' pools. Any log record or downstream tooling claiming "this URL came from engine X" is wrong by construction. What IS answerable (as of 2026-08-05, via `query_log.jsonl`'s `drilldown` records + `search_key`): "which engines offered this URL in this session" — possibly several, possibly none. The none-case is what motivated the drilldown logging in the first place (a scraped idealo.de product URL, id-recycled to a different product days later, with no record of which engine — if any — ever served it).
- `tests/test_query_logger.py`'s shared `_make_mock_engine` helper sets `.search` on the mock — but `_engine_with_timing` calls `.search_with_reason()` (returns `(results, empty_reason)`), a different, newer interface. This is the actual root cause of `test_engine_with_timing_ok/timeout/empty` + part of `test_search_web_workflow_writes_log` failing (pre-existing, out of scope) — those tests were written against an interface `search_web.py` no longer has, not a transient flake. Do not reuse `_make_mock_engine` for new engine-fanout tests; write a local mock exposing `search_with_reason` instead (see `_make_mock_engine_with_reason` for the pattern).
