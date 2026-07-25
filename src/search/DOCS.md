# src/search/

## Role

pydoll-based parallel web-search pipeline behind the `search_web` and `search_engine_drilldown` CLI subcommands. Fans a single query out across 14 engines concurrently, dedups URLs into per-engine pools, caches the pools to disk, and returns an engine-breakdown table; the drilldown subcommand re-reads the cache to emit one engine's URLs. Touch this package when changing engine fan-out, dedup/pool-building, the disk cache, rate-limiting, or the three filter flags. Individual engine parsers live one level down in `engines/`.

## Public Interface

`__init__.py` is empty — modules are imported by path:

- `search_web_workflow(query, language="en", time_range=None, engines=None, …, query_modifier_map=None)` (search_web.py) — the `search_web` subcommand entry (`cli.py`). Returns `list[TextContent]` (one breakdown table).
- `fetch_search_results(...)` (search_web.py) — sync wrapper for dev scripts; returns the raw result list, no pool-building.
- `cache_key`, `cache_read`, `format_engine_pool` (cache.py) — the `search_engine_drilldown` subcommand path (`cli.py`).
- `kill_stale_chrome()` (browser.py) — registered `atexit` in `cli.py`.

## Flow

`search_web_workflow` selects engines → `asyncio.gather` of `_engine_with_timing` tasks (each acquires a rate-limiter token, then runs the engine) → flat `raw_results` → `filter_urls_by_mode` (if a filter flag set) → `build_engine_pools` dedups by URL owner → post-dedup pool cap to Google's pool size (fallback 10) → `_format_breakdown` table → `cache_write` to `~/.cache/websearch/<key>.json`. `search_engine_drilldown` skips all of this: `cache_read` the per-engine pool → `format_engine_pool` numbers + cleans snippets.

## Modules

### search_web.py (353 LOC)

**Purpose:** Search orchestrator. Fans out across the 14 active engines via `asyncio.gather`, then filters → builds pools → caps → formats → caches. Post-dedup pool cap: K = `len(pools['google'])` if >0 else 10, each pool trimmed to `pool[:K]` (prevents CrossRef/OpenAlex/StackExchange/OpenLibrary drilldown floods). Three-tier timeout: `ENGINE_WATCHDOG_TIMEOUT=3.6s` default, `ENGINE_WATCHDOG_OVERRIDE` per-engine (open_library 6.0, semantic_scholar 5.0, crossref 6.0, startpage 6.0, brave 6.0) — `bing`, `yandex`, and `marginalia` deliberately have NO override entry: all three probed well under the default (yandex additionally short-circuits its own blocked-query path via an upfront `showcaptcha`-URL check; marginalia's httpx-API round-trip never approaches 3.6s regardless of rate-limit outcome). `RATE_WAIT_TIMEOUT=60.0s` acquire cap → RATE_SKIP. `_engine_with_timing` returns a 5-tuple `(results, rate_wait_ms, search_ms, status, drop_reason)` with sub-classified TIMEOUT/ERROR statuses. Two-record logging: `engine_run` after fanout, `workflow_summary` after pool-build. `fetch_search_results` is a sync dev wrapper (raw list, no pools).
**Reads:** query + params; per-engine caps in `ENGINE_MAX_RESULTS`; default set via `_DEFAULT_ENGINES`.
**Writes:** disk cache `~/.cache/websearch/<key>.json` (via cache_write); query log (via log_query).
**Called by:** `cli.py` (search_web_workflow); dev scripts (fetch_search_results).
**Calls out:** `httpx`, `pydoll.exceptions`, `websockets.exceptions`, `mcp.types.TextContent`; `engines/` (all 14 engine classes); `cache` (cache_key, cache_write), `rate_limiter` (get_limiter), `merge` (build_engine_pools), `result` (SearchResult), `status`, `query_logger` (log_query), `filter_modes` (apply_filter_mode, filter_urls_by_mode, _DEFAULT_ENGINES).

### merge.py (36 LOC)

**Purpose:** Cross-engine URL dedup + per-engine pool builder. `build_engine_pools(results)` groups SearchResults by URL, assigns each URL to the owner engine (lowest position value, random tie-break), returns `{engine → [owned SearchResult, …]}` sorted by native position. Populates `engine_positions` on each result (all engines' positions for that URL).
**Reads:** flat `list[SearchResult]` from fan-out.
**Writes:** none (returns the pool dict).
**Called by:** `search_web.py`.
**Calls out:** `result` (SearchResult).

### filter_modes.py (78 LOC)

**Purpose:** Engine restriction + URL filtering for the `--books`/`--pdf`/`--docs` flags, plus `_DEFAULT_ENGINES`. `apply_filter_mode(...)` resolves the 3-way mutex (`pdf > docs > books`), sets the per-engine query-modifier map, returns `(selected, qmm, mode_id, excluded)`. `filter_urls_by_mode(raw_results, mode)` applies the post-fanout URL filter on the flat list BEFORE pool-build. Engine subsets are modifier-target sets, not restriction sets — all engines still fire on every query.
**Reads:** selected engines + flag booleans.
**Writes:** none.
**Called by:** `search_web.py`.
**Calls out:** `book_whitelist` (is_book_url), `pdf_filter` (is_pdf_url), `docs_filter` (is_docs_url).

### book_whitelist.py (145 LOC)

**Purpose:** `is_book_url(url)` — book-domain whitelist match for the `--books` filter.
**Reads:** URL string.
**Called by:** `filter_modes.py`.
**Calls out:** none (stdlib `urllib` only).

### pdf_filter.py (88 LOC)

**Purpose:** `is_pdf_url(url)` — PDF-host / `.pdf`-path match for the `--pdf` filter.
**Reads:** URL string.
**Called by:** `filter_modes.py`.
**Calls out:** none (stdlib `urllib` only).

### docs_filter.py (73 LOC)

**Purpose:** `is_docs_url(url)` — documentation-host match + noise blacklist for the `--docs` filter.
**Reads:** URL string.
**Called by:** `filter_modes.py`.
**Calls out:** none (stdlib `urllib` only).

### cache.py (117 LOC)

**Purpose:** Disk cache for per-engine pools, backing `search_engine_drilldown`. Cache key `sha256(query|language|engines|time_range[|modifier_id])[:16]`; path `~/.cache/websearch/<key>.json`; 1h mtime TTL; atomic write via `tempfile.mkstemp` + `os.replace`. JSON holds the full per-engine pool dict with native positions. `format_engine_pool(pool, engine_name, query)` renders one engine's pool as a numbered list with snippet cleanup applied.
**Reads:** cache files under `~/.cache/websearch/`.
**Writes:** `~/.cache/websearch/<key>.json`.
**Called by:** `cli.py` (cache_key, cache_read, format_engine_pool); `search_web.py` (cache_key, cache_write).
**Calls out:** `result` (SearchResult), `snippet` (_strip_bloat, _truncate, MAX_SNIPPET_LEN).

### snippet.py (63 LOC)

**Purpose:** Snippet text utilities for drilldown display. `_strip_bloat(text)` (HTML unescape + 9 bloat patterns), `_truncate(text, max_len)` (sentence-aware, `MAX_SNIPPET_LEN=500`).
**Reads:** raw snippet string.
**Called by:** `cache.py` (format_engine_pool).
**Calls out:** none (stdlib `html`, `re`).

### query_logger.py (64 LOC)

**Purpose:** Append-only JSONL query log. `log_query(record)` writes one line. Two record types: `engine_run` (per fanout) and `workflow_summary` (after pool-build).
**Reads:** `WEBSEARCH_QUERY_LOG_PATH` env (fallback `src/logs/query_log.jsonl`).
**Writes:** `src/logs/query_log.jsonl`.
**Called by:** `search_web.py`.
**Calls out:** `src/log_janitor.py` (maybe_prune_jsonl).

### browser.py (166 LOC)

**Purpose:** pydoll Chrome lifecycle. One shared Chrome, a new tab per engine for isolation, fingerprint patches (WebGL, canvas, permissions) at launch. Cleanup paths: `kill_tab(tab)` (browser-level `Target.closeTarget`, 5s cap), `close_browser()` (in-loop shutdown for dev), `kill_stale_chrome()` (nuclear `pkill` fallback).
**Reads:** none (singleton on first access).
**Writes:** Chrome session dir under the user-data-dir.
**Called by:** `cli.py` (kill_stale_chrome, atexit); `engines/` (new_tab, kill_tab — google, duckduckgo, lobsters, semantic_scholar, scholar).
**Calls out:** `pydoll` (Chrome, ChromiumOptions, PageCommands, TargetCommands).

### rate_limiter.py (48 LOC)

**Purpose:** Per-engine token-bucket rate limiter. Module-level `_limiters` registry populated at engine import (`RateLimiter(max_requests=4, window_seconds=60)`); consumed via `get_limiter(name).acquire()` before engine work.
**Reads / Writes:** in-memory `_limiters` registry.
**Called by:** `search_web.py` (get_limiter); `engines/` (RateLimiter, _limiters).
**Calls out:** none (stdlib `asyncio`, `time`).

### result.py (15 LOC)

**Purpose:** `SearchResult` dataclass. Fields: `url, title, snippet, engine, position, preview, engines, snippets, engine_positions`. `engine_positions` populated by `build_engine_pools`; `engines`/`snippets`/`preview` retained for dev-script backward compat.
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
- Two-call architecture: `search_web` returns counts only (no URLs); URLs come from `search_engine_drilldown` reading the cache. The drilldown query + filter flags MUST match the prior `search_web` call or the cache key misses.
- Post-dedup pool cap keys off Google's pool size — if Google was CAPTCHA'd or excluded, K falls back to 10.
- All engines fire on every query regardless of filter flag — the flags add a query modifier + post-fanout URL filter, they do NOT restrict the engine set.
- Stealth config is hardcoded in `browser.py` (JS patches, UA, window size, Chrome options) + per-engine files (SOCS cookie for Google) — no config file.
- pydoll tab cleanup uses `kill_tab` (browser-level close), NOT `tab.close()` — the latter hung 65s on non-cooperative renderers.
- CLI dispatch hardcodes `language="en"`, `time_range=None`, `engines=None`; the full `search_web_workflow` signature is retained only for dev-script callers.
