# search/

pydoll-based parallel search pipeline. Replaces the former `src/searxng/` SearXNG-Docker wrapper (deleted 2026-04-15 in engine-cut). Exposes `search_web_workflow()` (single-query, fan-out across engines via asyncio.gather) and `search_batch_workflow()` (N queries sequentially in one warm-Chrome session, used by the CLI `search_batch` subcommand) — both consumed by `cli.py`. Plus `fetch_search_results()` sync wrapper consumed by dev scripts.

**Active engines (7):** google, bing, google scholar, duckduckgo, mojeek (pydoll); crossref, hn (HTTP). See `decisions/stealth00_engine_status.md` for the drop decision on brave / startpage / semantic scholar. See `decisions/search05_engine_expansion.md` for HN-Algolia + DDG + Mojeek integration rationale + roadmap (Stack-Exchange next, Marginalia deferred).

## search_web.py

**Purpose:** Search orchestrator. Two entry points:
- `search_web_workflow(query, ...)` — single query, fan-out across all active engines via `asyncio.gather`, deduplicates by URL, formats as `list[TextContent]`.
- `search_batch_workflow(queries, ...)` — N queries sequentially through `search_web_workflow` in the SAME process (Chrome stays warm via shared singleton in `browser.py`), `close_browser()` in finally clause keeps teardown inside the active event loop. Used by `cli.py search_batch` subcommand to amortize Chrome cold-start across multiple queries (~5s boot + ~1s/query vs ~5s boot per query in subprocess-per-call mode).
- `fetch_search_results()` — sync wrapper for dev scripts.

**Input:** Query string (or list), category, language, time range, engine filter, page count.
**Output:** `list[TextContent]` (single workflow), `list[list[TextContent]]` (batch workflow), or `list[dict]` (sync wrapper).

## browser.py

**Purpose:** pydoll Chrome lifecycle. Starts a single shared Chrome instance on first call, creates a new tab per engine for isolation. Applies fingerprint patches (WebGL, canvas, permissions) at launch. Two cleanup paths:
- `close_browser()` — async, used inside an active event loop (e.g. by `search_batch_workflow` in finally). Issues CDP `Browser.close` and waits for response.
- `kill_stale_chrome()` — sync `pkill -f "user-data-dir=<SESSION_DIR>"`, registered as `atexit` handler in `cli.py`. Replaces the previous async-CDP atexit which incurred a deterministic 60s timeout per CLI invocation (event-loop mismatch — see `decisions/`/session 2026-04-30 forensic).

**Input:** None (singleton on first access).
**Output:** pydoll Chrome instance and new tab contexts.

## rate_limiter.py

**Purpose:** Per-engine token bucket rate limiter with exponential backoff. Prevents bursts from tripping engine rate limits. Jitter (formerly 1-3s sleep per `acquire`) was removed 2026-04-30 — added pure overhead in CLI subprocess mode (each call gets a fresh limiter) without empirical benefit (dev's standalone smoke runs 30 queries with 0 delay and lands 30/30 OK).
**Input:** Engine name.
**Output:** Async context that blocks until a token is available.

## preview.py

**Purpose:** Async preview fetcher. `fetch_previews(results, top_n=20)` hits the top-N result URLs in parallel (concurrency=8, timeout=3s per URL), extracts `og:description` + `meta name="description"` via lxml xpath, attaches as `preview: dict | None` to each `SearchResult` via `dataclasses.replace`. Silent skip on any fetch failure. Called from `search_web_workflow` after dedup, before format. Also used by `05_search_smoke.py`.
**Input:** `list[SearchResult]`, optional `top_n` int.
**Output:** `list[SearchResult]` with `preview` field populated for top-N (None for rest or failed fetches).

## result.py

**Purpose:** `SearchResult` dataclass (url, title, snippet, engine, position, preview). `preview: dict | None = None` field carries `{"og": str|None, "meta": str|None}` from `preview.py`. All engine constructors leave it at default `None`.
**Input:** —
**Output:** —

## engines/

Per-engine parser modules. Each exports an `Engine` class with `search(query, language, max_results)` returning `list[SearchResult]`.

### engines/base.py

**Purpose:** Abstract `BaseEngine` parent class. Defines the engine interface (name, URL builder, parser, rate-limiter hook).

### engines/google.py

**Purpose:** Google Search via pydoll. Three-layer consent handling: (1) SOCS cookie injection per-tab via `Network.setCookie` BEFORE navigation (primary bypass), (2) inline-consent body-text detection ("Before you continue" / "We use cookies and data") + button click on the search URL, (3) `consent.google.com` redirect handler as fallback. DOM parsing via `#rso h3` + `.MjjYud` selectors, parse_js without IIFE (pydoll's `execute_script` already wraps in function scope). Wait timeouts calibrated to dev p95: `MAX_WAIT_CYCLES=3`, `WAIT_INTERVAL=0.2s`. Rate-limit pre-registered at `max_requests=5, window_seconds=60` (capacity 5 per minute per process).

### engines/bing.py

**Purpose:** Bing Search via pydoll. DOM parsing via `#b_results .b_algo`.

### engines/scholar.py

**Purpose:** Google Scholar via pydoll. DOM parsing via `.gs_r.gs_or.gs_scl` + `.gs_rt`.

### engines/crossref.py

**Purpose:** CrossRef REST API via httpx (no browser needed). Uses polite pool `mailto` header for higher rate limits. Returns bibliographic metadata as `SearchResult` entries.

### engines/hn.py

**Purpose:** HN Algolia REST API via httpx (no browser, no auth). Default filter `tags=story` excludes comment hits. Snippet synthesized from points + num_comments + author metadata (HN doesn't expose body text for link-stories). Fallback URL `news.ycombinator.com/item?id={objectID}` for hits with empty external `url` (Ask-HN, Show-HN with story-text). Returns story metadata as `SearchResult` entries.

### engines/duckduckgo.py

**Purpose:** DuckDuckGo web search via pydoll (`html.duckduckgo.com/html/` GET endpoint). No consent handling needed — DDG html-endpoint does not show a consent banner. No cookie injection needed — `kl=wt-wt` (worldwide, no region filter) is included directly in the GET URL. DOM-based CAPTCHA detection (`form#challenge-form`). URL cleaning extracts the actual destination from DDG's redirect wrapper (`duckduckgo.com/l/?uddg=<encoded>`). Rate-limit pre-registered at `max_requests=4, window_seconds=60` (uniform 4 req/min policy). Selectors: `#links > div.web-result` (result containers), `h2 a` (title + href), `a.result__snippet` (snippet) — verified live 2026-05-03.

### engines/mojeek.py

**Purpose:** Mojeek web search via pydoll (mojeek.com/search GET endpoint). Own crawler index — not Bing-derivative, third independent index after Google + DDG. No consent handling, no CAPTCHA detection (none observed in DOM probe 2026-05-03), no URL cleaning (direct hrefs, no redirect wrapper). Rate-limit pre-registered at `max_requests=4, window_seconds=60`. Selectors: `ul.results-standard > li > a.ob` (container anchor with direct `href`), `li h2 a` (title text), `li p.s` (snippet) — verified live 2026-05-03.

## Stealth Decisions

Active stealth configuration: `dev/search_pipeline/01_google_smoke.py` (JS patches, SOCS cookie injection, browser options) + `dev/search_pipeline/config.yml` (all parameters). Historical research from the 9-engine exploration is documented in `decisions/stealth00_engine_status.md` (overview + dropped-engine verdicts) and `decisions/stealth01_fingerprint.md` through `stealth07_captcha.md` (per-layer detail).
