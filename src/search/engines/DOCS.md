# src/search/engines/

## Role

Per-engine search implementations. Each module (except `base.py`) exports one `BaseEngine` subclass implementing `search(query, language, max_results) -> list[SearchResult]`. Two implementation styles: pydoll Chrome-tab scraping (DOM parse via injected JS) for engines with no public API, and direct `httpx` calls for engines with a JSON/XML API. Touch this package to add/modify an engine's parsing logic or its rate-limit registration; touch `search_web.py` to change which engines are wired into the default pool.

## Public Interface

`__init__.py` is empty. Consumers import engine classes directly, e.g. `from src.search.engines.google import GoogleEngine`.

## Flow

Query string in → engine-specific fetch (pydoll tab navigation + JS extraction, or `httpx` GET/POST) → HTML/JSON parse → `list[SearchResult]` out. Each module registers a `RateLimiter` into the shared `_limiters` registry (`src/search/rate_limiter.py`) at import time; `search_web._engine_with_timing` acquires a token before invoking `search()`.

## Modules

### base.py (18 LOC)

**Purpose:** Abstract `BaseEngine` parent. Declares `search()` (abstract) and default `search_with_reason()` (delegates to `search()`, returns `(results, None)`); Stage-2 engines override `search_with_reason` to return a sub-status empty_reason.
**Reads:** nothing.
**Writes:** nothing.
**Called by:** every engine module in this package (subclassed).
**Calls out:** `src.search.result.SearchResult` (type only).

---

### google.py (208 LOC)

**Purpose:** Google web search via pydoll Chrome tab. Navigates to search URL, sets `SOCS` consent cookie, waits for `div.MjjYud` result containers via polling JS, detects `/sorry/` CAPTCHA path and consent-domain redirects, extracts results via injected JS parse script.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `pydoll` (NetworkCommands, CookieSameSite), `src.search.browser` (`new_tab`, `kill_tab`).

---

### duckduckgo.py (164 LOC)

**Purpose:** DuckDuckGo HTML-endpoint search via pydoll Chrome tab (`html.duckduckgo.com/html/`). Waits for `#links > div.web-result` containers, detects challenge-form CAPTCHA selector, extracts via injected JS parse script. `_extract_date` populates `SearchResult.date` (day precision) from the optional bare `<span>` in `.result__extras__url` — identified by `:not(.result__icon)`, not position (a dated result has 3 children: icon span, url anchor, date span; undated is a clean 2-child div, no crash). Present only when the source page has structured date metadata (verified: absent on Wikipedia-type results, present on ~40-100% of results depending on query).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### mojeek.py (131 LOC)

**Purpose:** Mojeek search via pydoll Chrome tab (`safe=1` filter). Waits for `ul.results-standard > li > a.ob` anchors, extracts title/snippet/URL via injected JS parse script.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### startpage.py (184 LOC)

**Purpose:** Startpage (Google-index frontend) search via pydoll Chrome tab. Two-step form-driven flow — a direct GET to `/sp/search?query=...` silently returns zero results (missing per-session `sc` token): loads homepage, sets `#q` via the native `HTMLInputElement.value` setter + `input` event (React controlled input), real `.click()` on `button.search-btn` (NOT `form.submit()`, which bypasses React's handler). Waits for `div.result` containers, detects block/captcha markers + iframe challenges via body/title text scan, extracts via injected JS parse script. `_build_results`/`_classify_diagnosis` factored out as pure functions (unit-tested in `tests/test_startpage_engine.py`).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### brave.py (164 LOC)

**Purpose:** Brave Search (own index, not a Google/Bing frontend) via pydoll Chrome tab, headless — single GET `https://search.brave.com/search?q=<q>`, no consent/form step. Waits for `div[data-type="web"]` containers, extracts via injected JS parse script. Detects Brave's Proof-of-Work (PoW) CAPTCHA via title/body marker scan (`captcha`, `schieberegler ziehen`, `drag the slider`, `proof of work`) or `a[href*="pow-captcha"]` presence — a PoW hit returns `[], S.EMPTY_BLOCK` immediately (graceful empty, never an exception); this is the load-bearing design point, since Brave's PoW is IP/velocity-based, not defeated architecturally. `_build_results`/`_classify_diagnosis` factored out as pure functions (unit-tested in `tests/test_brave_engine.py`).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### bing.py (210 LOC)

**Purpose:** Bing web search (direct path to the Bing index — DuckDuckGo is the existing surrogate) via pydoll Chrome tab, headless. Single GET `https://www.bing.com/search?q=<q>`, no consent/form step (a Microsoft cookie banner is present in the DOM but does not gate result rendering). Waits for `li.b_algo` containers, extracts title/href/snippet via injected JS parse script. Every organic href arrives wrapped in a `bing.com/ck/a?...&u=<prefixed-base64>&...` tracking redirect — `_clean_url` unwraps it: parses the `u` query param, strips its 2-char prefix (observed `a1`), base64url-decodes with padding restored, graceful fallback to the raw wrapped href on any failure or missing `u` param. Block detection via EN+DE title/body marker scan; `_build_results`/`_classify_diagnosis` factored out as pure functions (unit-tested in `tests/test_bing_engine.py`, including a real captured `ck/a` sample for the unwrap). `_extract_date` populates `SearchResult.date` from `span.news_dt`'s localized display string (`"14. März 2023"` / `"May 20, 2026"`) via two regexes + DE/EN month-name maps — inconsistent across results (only present on some, e.g. news-style listings), an unrecognized shape (e.g. relative "vor N Tagen") or absent element returns `None`, never a guess. Deliberately no snippet-text fallback — a result with a plain-text date but no `news_dt` span (e.g. `"...Research May 20, 2026 …"`) gets no `date`.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### yandex.py (179 LOC)

**Purpose:** Yandex Search — a genuine INDEPENDENT web index (own crawler, new coverage, not a Google/Bing frontend like startpage/bing) — via pydoll Chrome tab, headless. GET `https://yandex.com/search/?text=<q>` (international domain, not `.ru`; auto-redirects to append an IP-geo `&lr=<region>` param, no consent step). Waits for `li.serp-item` containers, title+href from `a.OrganicTitle-Link` (direct destination href, no unwrap needed — unlike Bing's `ck/a`). Two refinements over the plain google/startpage/brave/bing pattern: (1) checks `tab.current_url` for a `showcaptcha`/`checkcaptcha`/`/captcha` redirect IMMEDIATELY after navigation, before the result-wait poll, so a blocked query returns `S.EMPTY_BLOCK` fast (~0.4-1.6s live) instead of burning the full ~6-8s poll budget; (2) `_build_results` drops any result whose hostname carries `yandex` as a dot-separated label (`_is_self_referential` — catches `yandex.com`/`*.yandex.*` self-links and video-carousel cards without false-positiving on a lookalike domain like `notyandex.com`). `_build_results`/`_classify_diagnosis`/`_is_block_url`/`_is_self_referential` factored out as pure functions (unit-tested in `tests/test_yandex_engine.py`).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### lobsters.py (147 LOC)

**Purpose:** Lobsters (lobste.rs) search via pydoll Chrome tab, `what=stories&order=relevance` endpoint. Waits for `li.story` containers, extracts direct hrefs — no CAPTCHA check (site has none). `_extract_date` populates `SearchResult.date` (day precision, truncated from the `<time datetime="YYYY-MM-DD HH:MM:SS">` attribute — no invented/kept time component) — the cleanest dedicated-date element of any of the 8 DOM-scraped engines (three machine-readable representations: `datetime`, `title`, `data-at-unix`).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### semantic_scholar.py (163 LOC)

**Purpose:** Semantic Scholar search via pydoll Chrome tab. Waits for `div.cl-paper-row` containers, detects backend error page (`error-message-block` test-id, 400/405 rate-limit signal), handles a cookie-consent accept button, extracts via injected JS parse script. `&sort=` URL param deliberately omitted — causes HTTP 400/405 from SS backend.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### crossref.py (154 LOC)

**Purpose:** CrossRef academic works search via `httpx` GET against `api.crossref.org/works` (JSON API, no browser). Iterative HTML-entity unescape (handles double-encoded entities) on titles. `_extract_date` reads `date-parts` at native precision (`"YYYY"`/`"YYYY-MM"`/`"YYYY-MM-DD"`), truncating at the first missing/null slot (never shifts a later value into a wrong position) — populates `SearchResult.date`. Shared `DATE_KEY_PRIORITY = ("issued", "published-online", "published-print")` module constant, used by both `_extract_date` and `_synthesize`'s year fallback, so the date and the snippet-embedded year can never disagree (`created`/`indexed` excluded — deposit/indexing timestamps, not publication dates).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### openalex.py (117 LOC)

**Purpose:** OpenAlex academic graph search via `httpx` GET against `api.openalex.org/works` (JSON API, no browser). Same entity-unescape treatment as `crossref.py`. `_extract_date` populates `SearchResult.date` from `publication_date` (day-accurate, nullable), falling back to `str(publication_year)` (year precision) when null.
**Reads:** `OPENALEX_MAILTO` env var (polite-pool identification, optional).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### stack_exchange.py (106 LOC)

**Purpose:** Stack Overflow search via `httpx` GET against `api.stackexchange.com/2.3/search/advanced` (JSON API, no browser). Warns once (module-level `_KEY_WARNED` flag) when no API key is configured (anonymous quota). `_extract_date` converts `creation_date` (Unix epoch int, part of the default `withbody` filter, always present) to a day-precision ISO string via `datetime.fromtimestamp(ts, tz=timezone.utc)` — populates `SearchResult.date`.
**Reads:** `STACK_EXCHANGE_API_KEY` env var (optional; anonymous quota if unset).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### open_library.py (88 LOC)

**Purpose:** Open Library book-catalog search via `httpx` GET against `openlibrary.org/search.json` (JSON API, no browser). `_extract_date` populates `SearchResult.date` from `first_publish_year` (year precision only).
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### marginalia.py (64 LOC)

**Purpose:** Marginalia Search — independent index (own crawler, "small/old/text-heavy/non-commercial web", new coverage on a different axis from the mainstream engines) — via `httpx` GET against `api2.marginalia-search.com/search` (JSON API, no browser), header `API-Key: public` (shared free key, no signup). Same 429/403 -> `None` -> `[]` rate-limit shape as `crossref.py`/`openalex.py`/`stack_exchange.py`/`open_library.py`, `logger.warning` on rate-limit exactly matching that precedent.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### scholar.py (119 LOC)

**Purpose:** Google Scholar search via `httpx` GET (no browser) — migrated off pydoll 2026-05-09. Detects concurrent-CAPTCHA via 30x redirect to `/sorry/`. Full logic lives in `search_with_reason`; `search()` is a legacy thin wrapper that swallows exceptions for dev-script compat.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** dev probe scripts only (`dev/search_pipeline/`) — NOT imported by `src/search/search_web.py`. Decoupled/parked from the production 14-engine pool.
**Calls out:** `httpx`, `lxml.html`.

## Gotchas

- All 14 production engines register a uniform `RateLimiter(max_requests=4, window_seconds=60)` into `_limiters` at module import time — adding a new engine requires this registration or `search_web._engine_with_timing` will KeyError on `get_limiter(name)`.
- `scholar.py` is fully wired (class, rate limiter, parse logic) but excluded from `search_web.py`'s imports — it is reachable code, not literally dead, but not part of any production call path. Re-enabling it means adding an import + entry to `_DEFAULT_ENGINES` in `filter_modes.py`.
- pydoll-based engines (`google`, `duckduckgo`, `mojeek`, `lobsters`, `semantic_scholar`) all use `finally: await kill_tab(tab)` — NOT `tab.close()`, which caused 65s hangs on `TIMEOUT_NONCOOP` cases (`Page.close` via tab connection → hung renderer → 60s pydoll fallback).
