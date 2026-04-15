# search/

pydoll-based parallel search pipeline. Replaces the former `src/searxng/` SearXNG-Docker wrapper (deleted 2026-04-15 in engine-cut). Exposes one `search_web_workflow()` coroutine consumed by `server.py` + one `fetch_search_results()` sync wrapper consumed by dev scripts.

**Active engines (4):** google, bing, google scholar, crossref. See `decisions/stealth01_detection_layers.md` for the drop decision on brave / startpage / duckduckgo / mojeek / semantic scholar.

## search_web.py

**Purpose:** Search orchestrator. Fetches results from all active engines in parallel via `asyncio.gather`, deduplicates by URL, formats as `list[TextContent]`. Provides sync wrapper `fetch_search_results()` for dev scripts.
**Input:** Query string, category, language, time range, engine filter, page count.
**Output:** `list[TextContent]` with formatted markdown (workflow) OR `list[dict]` (sync wrapper).

## browser.py

**Purpose:** pydoll Chrome lifecycle. Starts a single shared Chrome instance on first call, creates a new tab per engine for isolation. Applies fingerprint patches (WebGL, canvas, permissions) at launch. Registered with `atexit` for cleanup.
**Input:** None (singleton on first access).
**Output:** pydoll Chrome instance and new tab contexts.

## rate_limiter.py

**Purpose:** Per-engine token bucket rate limiter with jitter + exponential backoff. Prevents bursts from tripping engine rate limits.
**Input:** Engine name.
**Output:** Async context that blocks until a token is available.

## result.py

**Purpose:** `SearchResult` dataclass (url, title, snippet, engine) used across all engine parsers.
**Input:** —
**Output:** —

## engines/

Per-engine parser modules. Each exports an `Engine` class with `search(query, language, max_results)` returning `list[SearchResult]`.

### engines/base.py

**Purpose:** Abstract `BaseEngine` parent class. Defines the engine interface (name, URL builder, parser, rate-limiter hook).

### engines/google.py

**Purpose:** Google Search via pydoll. Handles Google consent cookie injection (CDP `Network.setCookie` for SOCS cookie on `.google.com`) and DOM parsing via `#rso h3` + `.MjjYud` selectors.

### engines/bing.py

**Purpose:** Bing Search via pydoll. DOM parsing via `#b_results .b_algo`.

### engines/scholar.py

**Purpose:** Google Scholar via pydoll. DOM parsing via `.gs_r.gs_or.gs_scl` + `.gs_rt`.

### engines/crossref.py

**Purpose:** CrossRef REST API via httpx (no browser needed). Uses polite pool `mailto` header for higher rate limits. Returns bibliographic metadata as `SearchResult` entries.

## STEALTH_CONFIG.md

Historical reference — documents the pydoll stealth capabilities research from the initial 9-engine exploration. Superseded by `dev/search_pipeline/engines_eval/stealth_config.py` + `_stealth_builders.py` for active configuration. Kept for context.
