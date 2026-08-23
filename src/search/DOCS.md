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

### search_web.py (354 LOC)

**Purpose:** Search orchestrator — fans out across the 14 active engines via `asyncio.gather`, then builds pools, caps each to Google's pool size, formats a breakdown table, and caches the result. Threshold/timeout-tier/logging derivation: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** query + params; per-engine caps in `ENGINE_MAX_RESULTS`; default set via `_DEFAULT_ENGINES`.
**Writes:** disk cache `~/.cache/websearch/<key>.json` (via cache_write); query log (via log_query).
**Called by:** `cli.py` (search_web_workflow); dev scripts (fetch_search_results).
**Calls out:** `httpx`, `pydoll.exceptions`, `websockets.exceptions`, `mcp.types.TextContent`; `engines/` (all 14 engine classes); `cache` (cache_key, cache_write), `rate_limiter` (get_limiter), `merge` (build_engine_pools), `result` (SearchResult), `status`, `query_logger` (log_query).

### merge.py (32 LOC)

**Purpose:** Cross-engine URL dedup + per-engine pool builder — groups results by URL, assigns each to its lowest-position owner engine, and returns a per-engine pool dict sorted by native position. Constructor/field-drop detail: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** flat `list[SearchResult]` from fan-out.
**Writes:** none (returns the pool dict).
**Called by:** `search_web.py`.
**Calls out:** `result` (SearchResult).

### cache.py (117 LOC)

**Purpose:** Disk cache for per-engine pools, backing `search_engine_drilldown` — atomic-write JSON keyed by a query/language/engines/time_range hash, 1h TTL, plus `format_engine_pool` for numbered-list rendering with snippet cleanup. Key/TTL/date-field derivation: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** cache files under `~/.cache/websearch/`.
**Writes:** `~/.cache/websearch/<key>.json`.
**Called by:** `cli.py` (cache_key, cache_read, format_engine_pool); `search_web.py` (cache_key, cache_write).
**Calls out:** `result` (SearchResult), `snippet` (_strip_bloat, _truncate, MAX_SNIPPET_LEN).

### snippet.py (60 LOC)

**Purpose:** Snippet text utilities for drilldown display — HTML-unescape + bloat-pattern stripping, plus sentence-aware truncation.
**Reads:** raw snippet string.
**Called by:** `cache.py` (format_engine_pool).
**Calls out:** none (stdlib `html`, `re`).

### query_logger.py (27 LOC)

**Purpose:** Append-only JSONL query log (`log_query(record)`) — three record types (`engine_run`, `workflow_summary`, `drilldown`), correlated via a shared `search_key`. Full record-type schema and correlation-limit derivation: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** `WEBSEARCH_QUERY_LOG_PATH` env (fallback `src/logs/query_log.jsonl`).
**Writes:** `src/logs/query_log.jsonl`.
**Called by:** `search_web.py` (engine_run, workflow_summary); `cli.py` (drilldown, as of 2026-08-05).
**Calls out:** `src/log_janitor.py` (maybe_prune_jsonl).

### browser.py (121 LOC)

**Purpose:** pydoll Chrome lifecycle — one shared, headed, backgrounded (macOS `open -g -n`) Chrome, one tab per engine for isolation, no JS fingerprint patches or UA override. Backgrounding-flag/cleanup-path derivation: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** nothing (singleton browser on first access).
**Writes:** Chrome session dir under the user-data-dir.
**Called by:** `cli.py` (kill_stale_chrome, atexit); `engines/` (new_tab, kill_tab — google, duckduckgo, lobsters, semantic_scholar, scholar).
**Calls out:** `pydoll` (Chrome, ChromiumOptions, BrowserProcessManager, TargetCommands); `open`/`pkill` (macOS process control).

### rate_limiter.py (44 LOC)

**Purpose:** Per-engine token-bucket rate limiter — module-level `_limiters` registry populated at engine import, consumed via `get_limiter(name).acquire()` before engine work.
**Reads / Writes:** in-memory `_limiters` registry.
**Called by:** `search_web.py` (get_limiter); `engines/` (RateLimiter, _limiters).
**Calls out:** none (stdlib `asyncio`, `time`).

### result.py (16 LOC)

**Purpose:** `SearchResult` dataclass — `url, title, snippet, engine, position, preview, engines, snippets, engine_positions, date`, the last populated only by the 4 API engines with native date metadata.
**Called by:** `search_web.py`, `merge.py`, `cache.py`, `engines/`.
**Calls out:** none (stdlib `dataclasses`).

### status.py (22 LOC)

**Purpose:** Engine-status string constants for the query log + audit — 17 total, 5 legacy coarse plus EMPTY/TIMEOUT/ERROR sub-statuses. Full enumeration: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Called by:** `search_web.py`, `engines/` (imported as `status as S`).
**Calls out:** none.

## State

Two module-owned states. `rate_limiter._limiters` — the per-engine token-bucket registry, populated at engine import, read/mutated via `get_limiter().acquire()`. The disk cache (`~/.cache/websearch/`) — written by `cache.cache_write` (from search_web), read by `cache.cache_read` (from the drilldown path); 1h TTL, atomic writes. No cross-request in-memory search state — each `search_web_workflow` call is independent.

## Gotchas

- Active engines (9): google, duckduckgo, mojeek, lobsters, semantic_scholar (pydoll); crossref, openalex, stack_exchange, open_library (HTTP). Google Scholar (`engines/scholar.py`) is decoupled from the default pool. brave / startpage / bing were dropped.
- Two-call architecture: `search_web` returns counts only (no URLs); URLs come from `search_engine_drilldown` reading the cache. The drilldown query MUST match the prior `search_web` call or the cache key misses.
- Post-dedup pool cap keys off Google's pool size — if Google was CAPTCHA'd or excluded, K falls back to 10.
- Stealth config lives in `browser.py` (headed-backgrounded launch, `--disable-blink-features=AutomationControlled`, `BACKGROUNDING_FLAGS`, browser preferences) + per-engine files (SOCS cookie for Google) — no config file, no JS fingerprint patches or UA override (removed — see `browser.py`'s module history via `process-docs/browser_posture/`).
- pydoll tab cleanup uses `kill_tab` (browser-level close), NOT `tab.close()` — the latter hung 65s on non-cooperative renderers.
- CLI dispatch hardcodes `language="en"`, `time_range=None`, `engines=None`; the full `search_web_workflow` signature is retained only for dev-script callers.
- **A URL can NEVER be attributed to exactly one engine** — engines overlap heavily; the same URL routinely appears in 3+ drilled engines' pools. Any log record or downstream tooling claiming "this URL came from engine X" is wrong by construction. What IS answerable (as of 2026-08-05, via `query_log.jsonl`'s `drilldown` records + `search_key`): "which engines offered this URL in this session" — possibly several, possibly none.
- `tests/test_query_logger.py`'s engine mocks must expose `.search_with_reason(query, language, max_results) -> (results, empty_reason)` — `_engine_with_timing` calls that, not `.search()`. Fixed 2026-08-20 (the file's one shared mock helper, `_make_mock_engine`, set `.search` and was removed along with the drift it caused — see `_make_mock_engine_with_reason`, now the file's only engine-mock helper).
- `search_web_workflow` writes TWO log records per call, not one: `"engine_run"` (from `_query_engines_concurrent`) then `"workflow_summary"` (from `_build_query_log_entry`) — a test asserting exactly one JSONL line after a workflow call is checking the wrong invariant; filter by `record_type` instead (see `test_search_web_workflow_writes_log`).
- `query_logger.py` has no `LOG_PATH` module attribute — the log path is read fresh from `WEBSEARCH_QUERY_LOG_PATH` (env var) inside `log_query()` on every call. Tests must `monkeypatch.setenv("WEBSEARCH_QUERY_LOG_PATH", ...)`, not `patch.object(query_logger, "LOG_PATH", ...)`.
- `log_janitor.maybe_prune_jsonl` (called at the end of every `log_query()`) drops any JSONL line whose `"ts"` field is older than the 14-day retention window — a test writing a record with a hardcoded past-dated `ts` literal (or no `ts` at all — a missing key is treated as unparseable and also dropped) will see its own line silently pruned away as real time passes. Always use a freshly-computed current timestamp in test payloads that include `ts`.
