# src/search/engines/

## Role

Per-engine search implementations. Each module (except `base.py`) exports one `BaseEngine` subclass implementing `search(query, language, max_results) -> list[SearchResult]`. Two implementation styles: pydoll Chrome-tab scraping (DOM parse via injected JS) for engines with no public API, and direct `httpx` calls for engines with a JSON/XML API. Touch this package to add/modify an engine's parsing logic or its rate-limit registration; touch `search_web.py` to change which engines are wired into the default pool.

## Public Interface

`__init__.py` is empty. Consumers import engine classes directly, e.g. `from src.search.engines.google import GoogleEngine`.

## Flow

Query string in → engine-specific fetch (pydoll tab navigation + JS extraction, or `httpx` GET/POST) → HTML/JSON parse → `list[SearchResult]` out. Each module registers a `RateLimiter` into the shared `_limiters` registry (`src/search/rate_limiter.py`) at import time; `search_web._engine_with_timing` acquires a token before invoking `search()`.

## Modules

### base.py (18 LOC)

**Purpose:** Abstract `BaseEngine` parent — declares `search()` (abstract) and a default `search_with_reason()` (delegates to `search()`), returning the uniform `(results, empty_reason, diagnosis)` 3-tuple with `diagnosis=None`. `empty_reason` is `None` for every real engine as of the guessed-verdict-removal milestone — no engine has a non-`None` value left to return from inside `search_with_reason`.
**Reads:** nothing.
**Writes:** nothing.
**Called by:** every engine module in this package (subclassed).
**Calls out:** `src.search.result.SearchResult` (type only).

---

### google.py (224 LOC)

**Purpose:** Google web search via pydoll Chrome tab — navigates to the search URL, sets the `SOCS` consent cookie, waits for `div.MjjYud` result containers, detects the `/sorry/` CAPTCHA path and consent-domain redirects, and extracts results via an injected JS parse script. Every non-success branch (the `/sorry/` short-circuit, the post-wait-failure branch, the zero-parsed-results branch) returns `reason=None` and attaches a `_diagnose(tab)` snapshot (`marker` always `None` here — Google's signal is the URL path, not a text marker — plus `title`/`url`/`ready_state`/`containers_found`), merged with `document_status.attach_document_status` for the `document_status_chain`/`http_status` facts (see `document_status.py`'s module entry). `_classify_diagnosis` was removed (the guessed-verdict-removal milestone) — its BLOCK/CONSENT/CONCURRENT_RACE/NO_CONTAINER outputs are all fully re-derivable from `url`/`ready_state`, already in the snapshot.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `pydoll` (NetworkCommands, CookieSameSite), `src.search.browser` (`new_tab`, `kill_tab`).

---

### duckduckgo.py (189 LOC)

**Purpose:** DuckDuckGo HTML-endpoint search via pydoll Chrome tab (`html.duckduckgo.com/html/`) — waits for `#links > div.web-result` containers, detects the `form#challenge-form` CAPTCHA element, and populates `SearchResult.date` (day precision) from the optional dated `<span>` in `.result__extras__url` when present. Every non-success branch returns `reason=None` and attaches a `_diagnose(tab)` snapshot (`title`/`url`/`ready_state`/`containers_found` plus its own `challenge_form: bool`, since the block signal is structural — an element count, not text — so `marker` stays `None`, never overloaded with a selector string). `document_status.attach_document_status` merges in `document_status_chain`/`http_status`. `_classify_diagnosis` was removed (the guessed-verdict-removal milestone) — its BLOCK/CONCURRENT_RACE/NO_CONTAINER outputs are fully re-derivable from `challenge_form`/`ready_state`, already in the snapshot.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### mojeek.py (157 LOC)

**Purpose:** Mojeek search via pydoll Chrome tab (`safe=1` filter) — waits for `ul.results-standard > li > a.ob` anchors and extracts title/snippet/URL via an injected JS parse script. Every non-success branch returns `reason=None` and attaches a `_diagnose(tab)` snapshot (`title`/`url`/`ready_state`/`containers_found`; `marker` comes from `_match_marker` scanning `document.title` against a fixed block-keyword list). `document_status.attach_document_status` merges in `document_status_chain`/`http_status` — live-confirmed this is the engine that resolves the mojeek 403-vs-captcha question the whole diagnosis-snapshot line of work traces back to: a real empty run showed `title: "Captcha"` AND `http_status: 200`, meaning mojeek answers challenge pages with 200, not 403 — and the query `roboter-bausatz.de Versandkosten versandkostenfrei ab` (whose title contains "roboter", matching the `robot` block keyword) is live-confirmed to log the exact same shape as a genuine block, indistinguishable by verdict alone; the snapshot is what makes it distinguishable. `_classify_diagnosis` was removed (the guessed-verdict-removal milestone) — its BLOCK/CONCURRENT_RACE/NO_CONTAINER outputs are fully re-derivable from `marker`/`ready_state`, already in the snapshot; `_match_marker` stays, since it populates `marker` directly rather than only feeding a classify decision.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### startpage.py (176 LOC)

**Purpose:** Startpage (Google-index frontend) search via pydoll Chrome tab — two-step React-form flow (homepage load, native-setter query fill, real button click) to obtain a per-session `sc` token, then waits for `div.result` containers and detects block/captcha markers. Every non-success branch returns `reason=None` and attaches a `_diagnose(tab)` snapshot (`marker`/`title`/`url`/`ready_state`/`containers_found` plus the engine-specific `iframe_challenge: bool`), merged with `document_status_chain`/`http_status` via `document_status.attach_document_status` — status capture is armed before `_submit_search`'s own homepage `go_to`, so the chain also covers the homepage load, not just the post-form-submit result page. `_classify_diagnosis` was removed (the guessed-verdict-removal milestone) — its BLOCK/CONCURRENT_RACE/NO_CONTAINER outputs are fully re-derivable from `marker`/`iframe_challenge`/`ready_state`, already in the snapshot.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### brave.py (160 LOC)

**Purpose:** Brave Search (own index) via pydoll Chrome tab, headed — single GET, waits for `div[data-type="web"]` containers, and returns a graceful empty result (never an exception, `reason=None`) on Proof-of-Work CAPTCHA detection. `_diagnose(tab)` runs once, right after navigation (before the wait); every non-success branch attaches a snapshot — the immediate PoW/CAPTCHA branch and the post-wait-failure branch reuse that same (pre-existing, stale-by-design) DOM snapshot, the zero-parsed-results branch takes a fresh one. Snapshot carries `marker`/`title`/`url`/`ready_state`/`containers_found` (`None` on the immediate branch — `_wait_for_results` was never called — `False`/`True` on the other two) plus the engine-specific `pow_link: bool`. `document_status_chain`/`http_status` are read fresh at EACH of the three return sites regardless (a cheap list read, no CDP round trip) via `document_status.attach_document_status` — so the network fact stays current even where the DOM fact is intentionally reused, see Gotchas. `_classify_diagnosis` was removed (the guessed-verdict-removal milestone) — its BLOCK/CONCURRENT_RACE/NO_CONTAINER outputs are fully re-derivable from `marker`/`pow_link`/`ready_state`, already in the snapshot.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### bing.py (201 LOC)

**Purpose:** Bing web search (direct path to the Bing index) via pydoll Chrome tab, headed — single GET, waits for `li.b_algo` containers, unwraps the `bing.com/ck/a?...&u=<base64>` tracking redirect on every href, and detects blocks via an EN+DE marker scan. Every non-success branch returns `reason=None` and attaches a `_diagnose(tab)` snapshot (`marker`/`title`/`url`/`ready_state`/`containers_found`), merged with `document_status_chain`/`http_status` via `document_status.attach_document_status`. `_classify_diagnosis` was removed (the guessed-verdict-removal milestone) — its BLOCK/CONCURRENT_RACE/NO_CONTAINER outputs are fully re-derivable from `marker`/`ready_state`, already in the snapshot.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### yandex.py (170 LOC)

**Purpose:** Yandex Search (independent index) via pydoll Chrome tab, headed — waits for `li.serp-item` containers, extracts direct hrefs from `a.OrganicTitle-Link` (no unwrap needed), with fast CAPTCHA-redirect short-circuit and self-referential-result filtering. Every non-success branch returns `reason=None` and attaches a `_diagnose(tab)` snapshot (`marker`/`title`/`url`/`ready_state`/`containers_found`, `None` on the redirect short-circuit — `_wait_for_results` was never called), including the CAPTCHA-redirect short-circuit (a fresh snapshot taken once the redirect is confirmed), merged with `document_status_chain`/`http_status` via `document_status.attach_document_status` — live-confirmed the SmartCaptcha redirect page itself serves HTTP 200, not a 3xx. `_classify_diagnosis` was removed (the guessed-verdict-removal milestone) — its BLOCK/CONCURRENT_RACE/NO_CONTAINER outputs are fully re-derivable from `marker`/`url`/`ready_state`, already in the snapshot; `_is_block_url` stays, since it is also the early short-circuit optimization inside `search_with_reason`, independent of the removed verdict.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `src.search.browser` (`new_tab`, `kill_tab`).

---

### openalex.py (142 LOC)

**Purpose:** OpenAlex academic graph search via `httpx` GET against `api.openalex.org/works` (JSON API, no browser) — iterative HTML-entity unescape on titles, `SearchResult.date` from `publication_date` (day-accurate) falling back to `publication_year` (year precision), `SearchResult.pdf_url` from `best_oa_location.pdf_url` (`_pick_url`'s arxiv > doi > id choice stays the canonical `url`). `per_page` clamped to the vendor's 100-max. `reason` is always `None` — the 429 branch used to surface a guessed `EMPTY_BLOCK` verdict, removed (the guessed-verdict-removal milestone) since it carried no information the observed `http_status` (already in diagnosis) didn't already carry; 403 (forbidden resource) was already `reason=None` beforehand, unchanged. `diagnosis` is `{"http_status": <the observed status_code>}` on every branch that returns WITHOUT results (429, 403, and a 200 that parsed to zero results), `None` only when results are non-empty — no DOM diagnosis mechanism (HTTP API, no browser to inspect), but the one fact this engine already holds (the real HTTP status) is no longer discarded.
**Reads:** `OPENALEX_API_KEY` env var (optional free API key, sent as `api_key` query param — raises the daily budget from $0.10 to $1; `mailto` is never sent, ignored by the API since 2026-02).
**Writes:** none (network only).
**Called by:** `src/search/search_web.py`.
**Calls out:** `httpx`.

---

### scholar.py (119 LOC)

**Purpose:** Google Scholar search via `httpx` GET (no browser, migrated off pydoll) — detects concurrent-CAPTCHA via 30x redirect to `/sorry/`; not wired into `search_web.py`'s production engine pool. `reason` is always `None` — the redirect and inline-captcha-form branches used to surface guessed `EMPTY_BLOCK`/`EMPTY_NO_RESULTS` verdicts, both removed (the guessed-verdict-removal milestone). The redirect's fact (the observed HTTP status) was already in diagnosis; the inline-captcha-form fact was NOT — `_parse_response` now returns `(results, captcha_form: bool)` instead of `(results, reason)`, and `captcha_form` moved into `diagnosis` alongside `http_status` before the verdict it fed was removed. `diagnosis` is `{"http_status": <the observed status_code>}` (redirect branch) or `{"http_status": ..., "captcha_form": bool}` (post-fetch branches) on every branch that returns WITHOUT results, `None` only when results are non-empty — same "one fact already in hand" treatment as `openalex.py`, extended by one field here since scholar had a second signal (`captcha_form`) that only ever fed a classification, never a snapshot, before this milestone.
**Reads:** none (network only).
**Writes:** none (network only).
**Called by:** dev probe scripts only (`dev/search_pipeline/`) — NOT imported by `src/search/search_web.py`. Decoupled/parked from the production 8-engine pool.
**Calls out:** `httpx`, `lxml.html`.

## Gotchas

- All 8 production engines register a uniform `RateLimiter(max_requests=4, window_seconds=60)` into `_limiters` at module import time — adding a new engine requires this registration or `search_web._engine_with_timing` will KeyError on `get_limiter(name)`.
- `scholar.py` is fully wired (class, rate limiter, parse logic) but excluded from `search_web.py`'s imports — it is reachable code, not literally dead, but not part of any production call path. Re-enabling it means adding an import + entry to `_DEFAULT_ENGINES` in `filter_modes.py`.
- pydoll-based engines (`google`, `duckduckgo`, `mojeek`, `startpage`, `brave`, `bing`, `yandex`) all use `finally: await kill_tab(tab)` — NOT `tab.close()`, which caused 65s hangs on `TIMEOUT_NONCOOP` cases (`Page.close` via tab connection → hung renderer → 60s pydoll fallback).
- As of the engine-reduction milestone (2026-09), `openalex.py` is the only remaining HTTP (non-pydoll) engine — its `httpx.AsyncClient(timeout=3.6)` already matches the uniform `ENGINE_WATCHDOG_TIMEOUT`; no more hand-aligned per-engine timeout to track.
- **`search_with_reason` is a uniform 3-tuple across all 9 engines: `(results, empty_reason, diagnosis)`.** `diagnosis` is a `dict | None`. The attachment rule is "whenever the engine returns WITHOUT results" — not "whenever `empty_reason` is non-`None`" — because `openalex.py`'s 403 branch returns `reason=None` while still holding a real observed HTTP status that would otherwise be thrown away exactly like a guessed verdict is. `diagnosis` is `None` only when `results` is non-empty (a real success, diagnosis-free by design — no engine pays for a diagnose call it doesn't need). As of the guessed-verdict-removal milestone, `empty_reason` is `None` on EVERY branch of EVERY engine — there is no longer any code path that returns a non-`None` value from inside `search_with_reason` (the fact-based statuses — `TIMEOUT_*`/`ERROR_*`/`RATE_SKIP`/`OK` — are all assigned later, in `search_web._engine_with_timing`, never inside an engine). A new engine MUST return this exact 3-tuple shape or `search_web._engine_with_timing`'s unpack raises.
- **Diagnosis snapshot field names are consistent across the 7 browser engines: `marker` (`str | None`, the matched block-keyword text, or `None` when the engine's own block signal isn't text-based — google's is a URL path, ddg's is an element count), `title` (`document.title`, raw casing), `url` (`window.location.href`), `ready_state` (`document.readyState`), `containers_found` (`bool | None` — `True` when `_wait_for_results` succeeded but parsing still produced zero items, `False` when it failed, `None` on a branch that short-circuits before ever calling `_wait_for_results` — never observed, never fabricated as `False`), `document_status_chain` (`list[int]`, ordered main-frame document response statuses observed via CDP — see `document_status.py`'s module entry in `src/search/DOCS.md`), `http_status` (`int | None`, `document_status_chain[-1]`, `None` — never a fabricated default — when nothing was observed).** Engine-specific extras keep their own names and never get folded into `marker`: `pow_link` (brave), `iframe_challenge` (startpage), `challenge_form` (duckduckgo), `captcha_form` (scholar). This is what lets a later reader compare engines without a per-engine lookup table — do not add a new common-sounding key without adding it to every engine's `_diagnose`, and do not repurpose `marker` for a structural (non-text) signal. `openalex.py`/`scholar.py`'s diagnosis shape is deliberately narrower — no DOM fields at all (there is no DOM) — not a partial/broken implementation of the 7-engine shape.
- Each browser engine's `_diagnose(tab)` (the DOM-fact half of the snapshot) is called fresh at each site that needs one (typically once per empty branch) — EXCEPT `brave.py`, whose single top-of-function `diag` is reused for both the immediate PoW/CAPTCHA branch and the post-wait-failure branch. **This reuse is PRE-EXISTING (predates the diagnosis-snapshot work entirely) and is NOT "safe because nothing async happens between" — `_wait_for_results` polls for up to `MAX_WAIT_CYCLES × WAIT_INTERVAL` (6s) between the two checks, so the reused DOM snapshot can be stale by that much.** `document_status_chain`/`http_status`, by contrast, ARE read fresh at each of brave's three return sites regardless — `attach_document_status` reads the live `status_chain` list at call time, a cheap in-memory operation, not a fresh DOM round trip — so the network fact stays current even where the DOM fact is knowingly stale.
- **HTTP status (the real server response code) is captured via `document_status.py`, a CDP `Network.responseReceived` listener armed before each browser engine's first navigation — see that module's entry in `src/search/DOCS.md`.** It answers exactly the question the DOM-only snapshot (marker/title/url/readyState) cannot: mojeek's empty runs carry `title: "Captcha"` AND `http_status: 200`, live-confirmed — the server answers challenge pages with 200, never a 403, on this engine. Measured cost: `tab.enable_network_events()` (the one added CDP round trip, once per engine) averaged ~10ms across 8 fresh tabs (7-14ms range) — under 0.2% of the 6.0s per-engine watchdog, invisible against the hundreds-of-ms network jitter these engines already show call to call.
- **The EMPTY_* sub-statuses (`EMPTY_BLOCK`, `EMPTY_NO_CONTAINER`, `EMPTY_CONCURRENT_RACE`, `EMPTY_CONSENT`, `EMPTY_NO_RESULTS`) and every `_classify_diagnosis` (and scholar's inline captcha-form classification) were removed — they were verdicts guessed from a title/body keyword scan or a URL pattern-match, and the log now records the observation instead of the guess. A concrete case that motivated this: `roboter-bausatz.de Versandkosten versandkostenfrei ab` logged as `EMPTY_BLOCK` for mojeek purely because the query's substring `roboter` contains `robot`, one of mojeek's block keywords — indistinguishable from a genuine block by verdict alone, live-confirmed still true after the snapshot exists (`marker: "captcha"`) but now honestly labeled `status: "EMPTY"`.** Every engine now returns `reason=None` on every branch; `_engine_with_timing` maps that to the generic `EMPTY` status. Per-verdict mapping (the check performed branch by branch before deleting anything, per engine — all facts were already in the snapshot except two, added here): `EMPTY_BLOCK`/`EMPTY_CONSENT` (google) → `url`; `EMPTY_BLOCK` (duckduckgo) → `challenge_form`; `EMPTY_BLOCK` (mojeek/bing/startpage/brave/yandex) → `marker` (also `pow_link` for brave, `iframe_challenge` for startpage, `url` for yandex); `EMPTY_CONCURRENT_RACE` (all 7) → `ready_state`; `EMPTY_NO_CONTAINER` (all 7) → re-derivable as "none of the above", no field needed; `EMPTY_NO_RESULTS` (all 7) → **new field `containers_found`**, since neither `marker` nor `ready_state` could tell "wait succeeded, zero parsed" apart from "wait failed"; `EMPTY_BLOCK` (openalex, 429) → `http_status` (verified in code: `_fetch_results` returns the same `status_code` for 429 as diagnosis already carries); `EMPTY_BLOCK` (scholar, 30x redirect) → `http_status`; `EMPTY_BLOCK` (scholar, inline captcha form) → **new field `captcha_form`**, since that fact previously fed `_parse_response`'s verdict and nowhere else. `status.py` shrank from 17 to 10 constants — `OK`/`EMPTY`/`RATE_SKIP`/3×`TIMEOUT_*`/4×`ERROR_*` — the ones that describe our own runtime, never a guess about the remote side; the unused bare `TIMEOUT` (zero usages anywhere) and bare `ERROR` (one dev-script-only usage, never in `src/search/`) were dropped too, since `_classify_engine_exception` never produced either.
