# src/search/engines/

## Role

Per-engine search implementations. Each module (except `base.py`) exports one `BaseEngine` subclass implementing `search(query, language, max_results) -> list[SearchResult]`. Two implementation styles: pydoll Chrome-tab scraping (DOM parse via injected JS) for engines with no public API, and direct `httpx` calls for engines with a JSON/XML API. Touch this package to add/modify an engine's parsing logic or its rate-limit registration; touch `search_web.py` to change which engines are wired into the default pool.

## Public Interface

`__init__.py` is empty. Consumers import engine classes directly, e.g. `from src.search.engines.google import GoogleEngine`.

## Flow

Query string in → engine-specific fetch (pydoll tab navigation + JS extraction, or `httpx` GET/POST) → HTML/JSON parse → `list[SearchResult]` out. Each module registers a `RateLimiter` into the shared `_limiters` registry (`src/search/rate_limiter.py`) at import time; `search_web._engine_with_timing` acquires a token before invoking `search()`.

## Modules

### base.py (18 LOC)

**Purpose:** Abstract `BaseEngine` parent — declares `search()` (abstract) and a default `search_with_reason()` (delegates to `search()`), which Stage-2 engines override to return a sub-status empty_reason.
**Reads:** nothing.
**Writes:** nothing.
**Called by:** every engine module in this package (subclassed).
**Calls out:** `src.search.result.SearchResult` (type only).

---

### google.py (206 LOC)

**Purpose:** Google web search via pydoll Chrome tab — navigates to the search URL, sets the `SOCS` consent cookie, waits for `div.MjjYud` result containers, detects the `/sorry/` CAPTCHA path and consent-domain redirects, and extracts results via an injected JS parse script.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `pydoll` (NetworkCommands, CookieSameSite), `src.search.browser` (`new_tab`, `kill_tab`).

---

### duckduckgo.py (171 LOC)

**Purpose:** DuckDuckGo HTML-endpoint search via pydoll Chrome tab (`html.duckduckgo.com/html/`) — waits for `#links > div.web-result` containers, detects the challenge-form CAPTCHA selector, and populates `SearchResult.date` (day precision) from the optional dated `<span>` in `.result__extras__url` when present.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### mojeek.py (129 LOC)

**Purpose:** Mojeek search via pydoll Chrome tab (`safe=1` filter) — waits for `ul.results-standard > li > a.ob` anchors and extracts title/snippet/URL via an injected JS parse script.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### startpage.py (178 LOC)

**Purpose:** Startpage (Google-index frontend) search via pydoll Chrome tab — two-step React-form flow (homepage load, native-setter query fill, real button click) to obtain a per-session `sc` token, then waits for `div.result` containers and detects block/captcha markers.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### brave.py (161 LOC)

**Purpose:** Brave Search (own index) via pydoll Chrome tab, headed — single GET, waits for `div[data-type="web"]` containers, and returns a graceful `S.EMPTY_BLOCK` (never an exception) on Proof-of-Work CAPTCHA detection.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### bing.py (204 LOC)

**Purpose:** Bing web search (direct path to the Bing index) via pydoll Chrome tab, headed — single GET, waits for `li.b_algo` containers, unwraps the `bing.com/ck/a?...&u=<base64>` tracking redirect on every href, and detects blocks via an EN+DE marker scan.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### yandex.py (171 LOC)

**Purpose:** Yandex Search (independent index) via pydoll Chrome tab, headed — waits for `li.serp-item` containers, extracts direct hrefs from `a.OrganicTitle-Link` (no unwrap needed), with fast CAPTCHA-redirect short-circuit and self-referential-result filtering.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### openalex.py (135 LOC)

**Purpose:** OpenAlex academic graph search via `httpx` GET against `api.openalex.org/works` (JSON API, no browser) — iterative HTML-entity unescape on titles, `SearchResult.date` from `publication_date` (day-accurate) falling back to `publication_year` (year precision), `SearchResult.pdf_url` from `best_oa_location.pdf_url` (`_pick_url`'s arxiv > doi > id choice stays the canonical `url`). `per_page` clamped to the vendor's 100-max. Overrides `search_with_reason`: a 429 (daily/per-second budget exceeded) surfaces as `S.EMPTY_BLOCK` instead of a silent empty result; 403 (forbidden resource) stays a plain empty with no reason.
**Reads:** `OPENALEX_API_KEY` env var (optional free API key, sent as `api_key` query param — raises the daily budget from $0.10 to $1; `mailto` is never sent, ignored by the API since 2026-02).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### scholar.py (116 LOC)

**Purpose:** Google Scholar search via `httpx` GET (no browser, migrated off pydoll) — detects concurrent-CAPTCHA via 30x redirect to `/sorry/`; not wired into `search_web.py`'s production engine pool.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** dev probe scripts only (`dev/search_pipeline/`) — NOT imported by `src/search/search_web.py`. Decoupled/parked from the production 8-engine pool.
**Calls out:** `httpx`, `lxml.html`.

## Gotchas

- All 8 production engines register a uniform `RateLimiter(max_requests=4, window_seconds=60)` into `_limiters` at module import time — adding a new engine requires this registration or `search_web._engine_with_timing` will KeyError on `get_limiter(name)`.
- `scholar.py` is fully wired (class, rate limiter, parse logic) but excluded from `search_web.py`'s imports — it is reachable code, not literally dead, but not part of any production call path. Re-enabling it means adding an import + entry to `_DEFAULT_ENGINES` in `filter_modes.py`.
- pydoll-based engines (`google`, `duckduckgo`, `mojeek`, `startpage`, `brave`, `bing`, `yandex`) all use `finally: await kill_tab(tab)` — NOT `tab.close()`, which caused 65s hangs on `TIMEOUT_NONCOOP` cases (`Page.close` via tab connection → hung renderer → 60s pydoll fallback).
- As of the engine-reduction milestone (2026-09), `openalex.py` is the only remaining HTTP (non-pydoll) engine — its `httpx.AsyncClient(timeout=3.6)` already matches the uniform `ENGINE_WATCHDOG_TIMEOUT`; no more hand-aligned per-engine timeout to track.
