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

**Purpose:** Startpage (Google-index frontend) search via pydoll Chrome tab — two-step React-form flow (homepage load, native-setter query fill, real button click) to obtain a per-session `sc` token, then waits for `div.result` containers and detects block/captcha markers. Form-flow rationale: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### brave.py (161 LOC)

**Purpose:** Brave Search (own index) via pydoll Chrome tab, headed — single GET, waits for `div[data-type="web"]` containers, and returns a graceful `S.EMPTY_BLOCK` (never an exception) on Proof-of-Work CAPTCHA detection. PoW-detection detail: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### bing.py (204 LOC)

**Purpose:** Bing web search (direct path to the Bing index) via pydoll Chrome tab, headed — single GET, waits for `li.b_algo` containers, unwraps the `bing.com/ck/a?...&u=<base64>` tracking redirect on every href, and detects blocks via an EN+DE marker scan. Unwrap/date-extraction detail: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### yandex.py (171 LOC)

**Purpose:** Yandex Search (independent index) via pydoll Chrome tab, headed — waits for `li.serp-item` containers, extracts direct hrefs from `a.OrganicTitle-Link` (no unwrap needed), with fast CAPTCHA-redirect short-circuit and self-referential-result filtering. Refinement detail: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### lobsters.py (145 LOC)

**Purpose:** Lobsters (lobste.rs) search via pydoll Chrome tab, `what=stories&order=relevance` endpoint — waits for `li.story` containers, extracts direct hrefs (no CAPTCHA check, site has none), and populates `SearchResult.date` from the `<time datetime>` attribute.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### semantic_scholar.py (158 LOC)

**Purpose:** Semantic Scholar search via pydoll Chrome tab — waits for `div.cl-paper-row` containers, detects the backend rate-limit error page, handles a cookie-consent accept button, and deliberately omits the `&sort=` URL param (causes HTTP 400/405 from the SS backend).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### crossref.py (146 LOC)

**Purpose:** CrossRef academic works search via `httpx` GET against `api.crossref.org/works` (JSON API, no browser) — iterative HTML-entity unescape on titles, and `date-parts`-derived `SearchResult.date` at native precision via a shared `DATE_KEY_PRIORITY` used consistently for both the date field and the snippet-embedded year.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### openalex.py (115 LOC)

**Purpose:** OpenAlex academic graph search via `httpx` GET against `api.openalex.org/works` (JSON API, no browser) — same entity-unescape treatment as `crossref.py`, `SearchResult.date` from `publication_date` (day-accurate) falling back to `publication_year` (year precision).
**Reads:** `OPENALEX_MAILTO` env var (polite-pool identification, optional).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### stack_exchange.py (104 LOC)

**Purpose:** Stack Overflow search via `httpx` GET against `api.stackexchange.com/2.3/search/advanced` (JSON API, no browser) — warns once on missing API key (anonymous quota), `SearchResult.date` from the `creation_date` Unix epoch.
**Reads:** `STACK_EXCHANGE_API_KEY` env var (optional; anonymous quota if unset).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### open_library.py (86 LOC)

**Purpose:** Open Library book-catalog search via `httpx` GET against `openlibrary.org/search.json` (JSON API, no browser) — `SearchResult.date` from `first_publish_year` (year precision only).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### marginalia.py (61 LOC)

**Purpose:** Marginalia Search (independent "small/old/text-heavy" index) via `httpx` GET against `api2.marginalia-search.com/search` (JSON API, no browser, shared public API key) — same 429/403 rate-limit handling shape as the other 4 API engines.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### scholar.py (116 LOC)

**Purpose:** Google Scholar search via `httpx` GET (no browser, migrated off pydoll) — detects concurrent-CAPTCHA via 30x redirect to `/sorry/`; not wired into `search_web.py`'s production engine pool. Migration/timeout derivation: `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md`.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** dev probe scripts only (`dev/search_pipeline/`) — NOT imported by `src/search/search_web.py`. Decoupled/parked from the production 14-engine pool.
**Calls out:** `httpx`, `lxml.html`.

## Gotchas

- All 14 production engines register a uniform `RateLimiter(max_requests=4, window_seconds=60)` into `_limiters` at module import time — adding a new engine requires this registration or `search_web._engine_with_timing` will KeyError on `get_limiter(name)`.
- `scholar.py` is fully wired (class, rate limiter, parse logic) but excluded from `search_web.py`'s imports — it is reachable code, not literally dead, but not part of any production call path. Re-enabling it means adding an import + entry to `_DEFAULT_ENGINES` in `filter_modes.py`.
- pydoll-based engines (`google`, `duckduckgo`, `mojeek`, `lobsters`, `semantic_scholar`) all use `finally: await kill_tab(tab)` — NOT `tab.close()`, which caused 65s hangs on `TIMEOUT_NONCOOP` cases (`Page.close` via tab connection → hung renderer → 60s pydoll fallback).
- `crossref.py`/`open_library.py`'s `httpx.AsyncClient(timeout=6.0)` is hand-aligned with `search_web.py`'s `ENGINE_WATCHDOG_OVERRIDE` entry for that engine (both `6.0`) — not derived from it automatically. Changing one without the other silently decouples the client-side timeout from the watchdog it's meant to race under; re-check both when tuning either engine's override.
