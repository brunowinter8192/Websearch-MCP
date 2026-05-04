# search05 — Engine Expansion

## Bing dropped (2026-05-04)

**Engine:** `src/search/engines/bing.py` — deleted; `BingEngine` import + ENGINES entry removed from `src/search/search_web.py`
**Dropped by:** Bruno verdict

**Reason:** No added value over DuckDuckGo. DDG's web index IS Bing — DDG queries Bing under the hood and re-ranks with its own snippet generation. Adding Bing-direct gave us only snippet-and-ranking variation on the same URL set, not actual coverage. Plus Bing's selector `#b_results .b_algo` had drifted (DOM change since the engine was wired) and required a repair effort that didn't pay back. DDG remains as the Bing-index access path; a Bing-direct re-eval can be revisited later if a clear use case emerges (own snippet quality vs. DDG, Bing News / Images sub-pipelines).

---

## HN dropped (2026-05-04)

**Engine:** `src/search/engines/hn.py` — deleted  
**Dropped by:** Bruno verdict

**Reason:** HN Algolia's backoff behavior is rate-limit-cascade-hostile in the parallel engine architecture. Any query that yields 0 results (link-stories EMPTY, German queries, non-tech topics) triggers `limiter.backoff()` because `_wait_for_results` returns False on empty content — the engine cannot distinguish "rate limited" from "no matching content". In a 4-engine parallel gather, this compounds exponentially across consecutive empty queries (attempt 0: 34s → attempt 1: 63s → attempt 2: 125s → ...), effectively stalling the entire search gather on sequences of non-HN queries. Replaced by Stack Exchange API which returns empty result list cleanly without backoff penalty.

---

## Stack Exchange — Implementiert (2026-05-04)

**Endpoint:** `https://api.stackexchange.com/2.3/search/advanced?site=stackoverflow&filter=withbody` (GET, JSON)  
**Engine:** `src/search/engines/stack_exchange.py` — BaseEngine subclass, httpx, 4 req/min  
**Smoke:** `dev/search_pipeline/10_stack_exchange_smoke.py` — 30-query baseline, report in `01_reports/se_smoke_*.md`

**Why Stack Exchange:** Programmatic Q&A content from stackoverflow.com. Complements general web engines with structured developer answers that rarely surface at the top of general search. Free API, no browser needed. `filter=withbody` returns the question body for real snippet content vs. pure metadata. Anonymous quota 300 req/day; 10k/day with free registered API key.

**Fields used:** `link` (URL), `title` (HTML-decoded), `body` (HTML stripped to plaintext, truncated 500 chars), `score`, `answer_count`, `tags` (fallback snippet when body absent).

**Smoke baseline (2026-05-04):** `dev/search_pipeline/01_reports/se_smoke_20260504_012742.md`
- 15/30 OK — German queries (6× EMPTY expected), pydoll/crawl4ai/trafilatura/SPLADE niche queries EMPTY (no SO matches)
- No rate-limit block — anonymous 300/day quota not exhausted; 4 req/min token bucket paces correctly (59s wait every 4 queries)
- Live CLI harness: 26 results for "python asyncio best practices" with body snippets + preview

**Sources:** Stack Exchange API docs — `api.stackexchange.com/docs/search`

---

## Lobsters — Implementiert (2026-05-03)

**Endpoint:** `https://lobste.rs/search?q={query}&what=stories&order=relevance` (GET, server-rendered HTML, no JS required)  
**Engine:** `src/search/engines/lobsters.py` — BaseEngine subclass, pydoll Chrome, 4 req/min  
**Smoke:** `dev/search_pipeline/07_lobsters_smoke.py` — 30-query baseline, report in `01_reports/lobsters_smoke_*.md`

**Why Lobsters:** Link-aggregator focused on tech/programming. Curated community with high signal-to-noise for developer queries. Complements Google/DDG/Mojeek with community-filtered content rather than crawl-ranked results. Free, no auth, no API-key, no bot challenge observed.

**Phase-A DOM probe findings (2026-05-03):**
- Selectors verified live: `li.story` (20 hits), `a.u-url` (20 hits, href = direct destination URL), `a.domain` (domain-as-displayed string)
- `a.u-url.href` is direct destination URL — no redirect wrapper, no `_clean_url` needed
- No CAPTCHA form, no cookie banner, no bot-block on first contact. html_bytes = 47870 (normal page).
- `page_title` pattern: `"Search | Lobsters"` — used in `_derive_status` BLOCKED check (`"Lobsters" not in title`)
- No URL redirect on navigation — `current_url` matches input URL exactly
- `a.domain` shows Lobsters' display domain which may include path prefix for GitHub (e.g. `github.com/joaocarvalhoopen`) — correct link-aggregator behavior, not a parsing error

**Snippet caveat:** Lobsters search page has no body text — only title + domain + tags + comments-count + submitter. Snippet = `a.domain` (domain-as-displayed) by design. `og:description` from preview-fetch fills the description field downstream.

**Smoke baseline (2026-05-03):** `dev/search_pipeline/01_reports/lobsters_smoke_20260503_224702.md`
- 16/30 OK at 0-delay stress — 11× EMPTY (German queries + content-empty: crawl4ai, pydoll, epidemiology, climate change), 3× SUSPECT (3 results, low domain diversity)
- No rate-limit block observed — EMPTY = Lobsters simply has no matching content for those queries
- Nav timing: mean 488ms / max 1639ms; DOM-wait mean 477ms / max 613ms
- Production 4 req/min limiter stays within burst threshold

**Sources:** `searxng/searxng searx/engines/lobsters.py` (selector reference)

---

## Mojeek — Implementiert (2026-05-03)

**Endpoint:** `https://www.mojeek.com/search?q={query}&safe=1` (GET, server-rendered HTML, no JS required)  
**Engine:** `src/search/engines/mojeek.py` — BaseEngine subclass, pydoll Chrome, 4 req/min  
**Smoke:** `dev/search_pipeline/06_mojeek_smoke.py` — 30-query baseline, report in `01_reports/mojeek_smoke_*.md`

**Why Mojeek:** Own crawler index (not Bing-derivative). After Google + DDG, the first engine with a genuinely independent index in the stack. Free, non-commercial-friendly, no API-key, no free-tier limit.

**Phase-A DOM probe findings (2026-05-03):**
- Selectors verified live: `ul.results-standard > li > a.ob` (10 hits), `li h2 a` (title), `li p.s` (snippet)
- `a.ob.href` is direct destination URL — no redirect wrapper, no `_clean_url` needed
- No CAPTCHA form (`captcha_cf=0`, `captcha_gen=0`), no cookie banner (`cookie_ban_elements=0`) on first contact
- In-page "×Mojeek User Survey" notification does not block result parsing
- `page_title` pattern: `"{query} - Mojeek Search"` — used in `_derive_status` BLOCKED check

**Smoke baseline (2026-05-03):** `dev/search_pipeline/01_reports/mojeek_smoke_20260503_193022.md`
- 7/30 OK at 0-delay stress — 403 block kicks in at query 10 (~9 queries in 7.5s = ~1.2 req/s burst)
- 2× SUSPECT: valid results (10 hits) with low domain diversity (4 domains) — not a detection signal
- Production 4 req/min limiter (1 query per 15s) stays well within burst threshold
- Nav timing queries 1-9: mean 286ms / max 1033ms

**Sources:** `searxng/searxng searx/engines/mojeek.py` (selector reference, s-param note)

---

## DuckDuckGo — Implementiert (2026-05-03)

**Endpoint:** `https://html.duckduckgo.com/html/?q={query}&kl=wt-wt` (GET, server-rendered HTML, no JS required)  
**Engine:** `src/search/engines/duckduckgo.py` — BaseEngine subclass, pydoll Chrome, 4 req/min  
**Smoke:** `dev/search_pipeline/04_ddg_smoke.py` — 30-query baseline, report in `01_reports/ddg_smoke_*.md`

**Phase-A DOM probe findings (2026-05-03):**
- Selectors verified live: `#links > div.web-result` (containers), `h2 a` (title+href), `a.result__snippet` (snippet)
- No consent banner on first contact — no CDP cookie injection needed
- No bot challenge (`form#challenge-form` = 0) with real Chrome + Mac UA
- URL cleaning required: `a.href` → `https://duckduckgo.com/l/?uddg=<encoded_target>` → extract `uddg` param
- Sec-Fetch-* headers sent automatically by Chrome via `Page.navigate` — no `Network.setExtraHTTPHeaders` call

**Sources:** `searxng/searxng searx/engines/duckduckgo.py` (selector reference, header rationale)

---

## Status Quo (IST)

Aktive Engines (Stand 2026-05-01):
- **Google** — pydoll Chrome, ~4 req/min empirisches Detection-Limit, 28/30 OK in burst smoke
- **Bing** — pydoll Chrome, broken seit Block-A-Smoke (Selektor `#b_results .b_algo` liefert 0 Ergebnisse, vermutlich DOM-Drift)
- **Google Scholar** — pydoll Chrome, Status unverifiziert
- **CrossRef** — pure HTTP via httpx, stabil

User-Profil: science / GitHub / reddit / Dokumentation / general hard-info — wenig news, wenig boulevard. GitHub und reddit über separate Plugins gelöst, vergleichbare Engines fehlen für (a) general-purpose Suche mit technischem Bias und (b) HackerNews / StackExchange als Discussion- / Q&A-Plattformen.

Architektur-Klassen: bisher dominant browser-basiert (3 von 4 Engines via pydoll Chrome). API-basierte Engines (nur CrossRef) sind ressourcen-billig — kein Browser-Tab im Pool, kein Stealth, kein CAPTCHA-Risiko, eigenständige Rate-Limits unabhängig vom Google-Detection-Limit.

## Evidenz

Recherche-Pass GitHub-Search 2026-05-01 zur Frage: welche Engines erweitern den Stack mit Bias auf technische Quellen ohne neue Browser-Last.

**Stract** (StractOrg/stract, 2,4k Stars, aktiv April 2026): Open-source Web-Search-Engine mit eigenem Index, Optics-System für ranking-Customization (Domain-Boosts wie github.com / *.readthedocs.io frei konfigurierbar), DDG-Style !bang, Wikipedia + StackOverflow Sidebar nativ eingebaut. Self-Description: "targeted towards tinkerers and developers". Hosted-API unter docs.stract.com. **Verworfen** — kommerzieller API-Zugang $27/Monat, fällt per User-Vorgabe raus.

**Marginalia** (MarginaliaSearch/MarginaliaSearch, 1,8k Stars, aktiv April 2026): Self-Description "Internet search engine for text-oriented websites. Indexing the small, old and weird web." Java-Stack, eigener Crawler. README: "non-commercial share-alike is always free, commercial API licenses available". API-Key + per-Key Rate-Limiting in DB-Schema (Migrations V23_06_0_006__api_key + V26_04_0_002__api_key_site_info_rate). User-facing API-Doku im docs.marginalia.nu Repo nicht vorhanden. Self-Hosting nicht praktikabel — README spezifiziert 32 GB RAM Minimum + mehrere TB Storage für Index. **Deferred** — try-or-drop am Hosted-Endpoint search.marginalia.nu nach HN+SE-Stabilisierung.

**HN Algolia API** (hn.algolia.com/api/v1): Frei, kein Auth, kein API-Key. Mehrere aktive Wrapper auf GitHub als Reference-Implementations: cyanheads/hn-mcp-server (Apache-2.0, April 2026), voska/hn-cli (Go, April 2026), wei/hn-mcp-server. Endpoints: `/search?query=` (Relevance), `/search_by_date?query=` (Recency), `/items/<id>`, `/users/<username>`. Filter via `tags` (story / comment / ask_hn / show_hn / front_page) und `numericFilters` (points / created_at_i). Response JSON mit `hits[]`-Array. Rate-Limit nicht prominent dokumentiert — Community-Wrapper laufen mit hohen Volumes ohne sichtbare Issues, empirisch zu bestimmen. cyanheads-Default-Concurrency: 10 parallele Requests.

**Stack Exchange API** (api.stackexchange.com): Frei. Multiple Sprach-Wrapper aktiv (lucjon/Py-StackExchange, gepflegt bis Januar 2026). 300 Requests/Tag anonym, 10.000/Tag mit kostenlos registriertem Key. Whole network: stackoverflow.com + serverfault.com + unix.stackexchange.com + math.stackexchange.com + ~170 weitere Sites adressierbar via `site=`-Parameter.

**SearXNG** (searxng/searxng, 29k Stars): Dominant in Metasearch-Aggregation. Pattern-Reference, nicht selbst zu hosten — User hat den Stack im Engine-Cut 2026-04-15 bewusst entfernt zugunsten der pydoll-Direct-Architektur.

**Kagi-Skill** (hffmnnj/kagi-skill, 6 Stars): Existiert als Claude-Skill für Kagi Search / Summarizer / FastGPT, aber Kagi-Subscription kostet — fällt per User-Vorgabe ("zahlen wir auf keinen Fall") raus.

## Recommendation (SOLL)

**HN-Algolia** als nächste Engine implementieren. Pure HTTP analog zu CrossRef, eigene Datei `src/search/engines/hn.py`. Bricht aus pydoll-Architektur aus — keine Browser-Last, keine Konkurrenz mit Google um Tabs, keine CAPTCHA-Hölle. Erstes Smoke-Script `dev/search_pipeline/03_hn_smoke.py` analog zu `01_google_smoke.py`. 30/30 Baseline-Test mit den existierenden Queries, Default-Filter `tags=story` damit nur Posts gelistet werden, Fallback-URL `news.ycombinator.com/item?id=` für hits ohne externen Link.

**Stack-Exchange-API** als zweite API-Engine direkt nach HN. Selbes httpx-Pattern. Routing-Frage: alle SE-Sites in einem Aufruf via Multi-Site oder pro Site separat. Erstmal eine generische SE-Engine die per Default stackoverflow.com + serverfault.com + unix.stackexchange.com abfragt und Treffer dedupliziert. Anonymous-Mode (300/Tag) reicht zum Anfangen, API-Key bei Volume-Bedarf nachträglich.

**Marginalia** Re-Eval erst nach HN+SE-Stabilisierung. Try-or-drop Probe am Hosted-Endpoint. Wenn zugänglich: dritte API-Engine. Wenn nicht: gestrichen, kein Email-Klärungsprozess.

**Bing** Status separat klären (broken, nicht Teil dieser Erweiterung — Selektor-Drift wahrscheinlich, nicht Rate-Limit).

**Domain-Boost-Layer** über Google+Bing-Treffer: deferred. HN-Algolia und SE liefern bereits direkt Treffer aus den relevanten Plattformen — Re-Rank-Heuristik wird unnötig wenn die Engines selbst die Quellen sind.

## Offene Fragen

- HN-Algolia Rate-Limit: empirisch beim ersten Smoke-Run zu messen. Community-Wrapper laufen ohne sichtbare Limits, exakte Schwelle nicht dokumentiert.
- SE-API: ohne Key 300/Tag — reicht das für agentic-search-Volume oder direkt mit kostenlosem Key starten?
- Marginalia Hosted-API: existiert ein offener Endpoint ohne API-Key, oder ist alles per-Key? Klärt sich beim ersten HTTP-Probe.
- Engine-Routing & Dedup: HN- und SE-Treffer-Domains weichen stark von Google/Bing-Treffern ab. Dedup-Logik im Search-Workflow muss prüfen ob URLs aus unterschiedlichen Engines korrekt mergen (HN-Hits führen oft zu denselben URLs wie Google-Treffer plus zusätzlicher Diskussion).

## Scholar Re-Eval (2026-05-03)

**Status before:** "Engine-Crash 0/0, cause unklar" (2026-04-21 SearXNG stack).

**Phase-A findings (2026-05-03, pydoll stack):**
- DOM probe: page loads correctly, no CAPTCHA, no `/sorry/` redirect, 170 KB HTML
- Selectors `div.gs_r.gs_or.gs_scl` = 10, `.gs_rt` = 10, `h3.gs_rt a` = 10 — all correct
- `ScholarEngine().search()` returns 0 results despite correct DOM
- Root cause (confirmed via raw pydoll result dict): `_JS_PARSE` is a Python triple-quoted string starting with `\nreturn JSON.stringify(...)`. Pydoll's `execute_script` wraps single-line scripts in a function context that permits `return`, but passes multi-line scripts raw to Chrome's `Runtime.evaluate`, where a top-level `return` statement is illegal → `SyntaxError: Illegal return statement`. `_extract_value()` silently returns `None` → `_parse_results()` returns `[]`.

**Fix applied (2026-05-03):** Rewrote `_JS_PARSE` as flat JS: variable declarations first (`var _n`, `var _o`, for-loop), `return JSON.stringify(_o)` as the final statement. No IIFE wrapper. Pattern matches config.yml selector blocks (mojeek/DDG/Lobsters). Selectors unchanged. Rate limit unchanged (3 req/60s — stricter than general engines).

**Smoke baseline:** `dev/search_pipeline/01_reports/scholar_smoke_*.md` (2026-05-03).

---

## OpenAlex — Implementiert (2026-05-03)

**Endpoint:** `https://api.openalex.org/works?search={query}&per_page=10[&mailto={email}]` (GET, JSON, no auth)  
**Engine:** `src/search/engines/openalex.py` — BaseEngine subclass, httpx-only, 4 req/min  
**Smoke:** `dev/search_pipeline/09_openalex_smoke.py` — 30-query baseline, report in `01_reports/openalex_smoke_*.md`

**Why OpenAlex:** Successor to Microsoft Academic Graph. ~250M works (papers, preprints, books, datasets). Free, open, no API key required. Provides rich structured metadata including abstracts (as inverted index), citation counts, author lists, and external IDs (arXiv, DOI, PMID, MAG). Strongest academic coverage in the HTTP-engine category — complements CrossRef (DOI-focused), HN (tech discussion). No CAPTCHA, no browser load, no stealth concerns.

**Abstract inverted index:** OpenAlex stores abstracts as `{word: [position1, position2, ...]}`. Reconstruction: build position→word mapping, sort by position, join with spaces. ~5 lines of Python. Not all papers have abstracts (some only have `tldr`-equivalent from the works API).

**URL strategy:** `ids.arxiv` (full URL `https://arxiv.org/abs/...`, best for CS/ML papers) > `doi` (full URL `https://doi.org/...`, journal papers) > `id` (full URL `https://openalex.org/W...`, always present, lowest signal value).

**Rate limiting:** Anonymous polite-pool: no published hard limit, but OpenAlex asks for `mailto=` parameter to identify polite users. Set `OPENALEX_MAILTO` env var — engine includes it in all requests when present. No default (don't hardcode an email). Production 4 req/min limiter stays well within observed anonymous limits.

**Semantic Scholar drop rationale:** Tested 2026-05-03. Anonymous tier blocked after 3 rapid requests; 429 persisted for > 180s. Even with 4 req/min limiter, startup/warmup scenarios (prior session already hit the API) would cause persistent 429. Free key requires academic-institution email gate. OpenAlex provides equivalent academic metadata without the rate-cascade risk.

---

## Quellen

- StractOrg/stract — Stract Search Engine (Repo, dropped: $27/mo commercial API)
- MarginaliaSearch/MarginaliaSearch — Marginalia Engine (Repo, deferred: try-or-drop later)
- MarginaliaSearch/docs.marginalia.nu — Marginalia Self-Hosting Docs (Repo)
- cyanheads/hn-mcp-server — HN MCP Reference Implementation (Repo)
- voska/hn-cli — HN CLI Reference (Repo)
- lucjon/Py-StackExchange — Stack Exchange Python Wrapper (Repo)
- searxng/searxng — Metasearch Pattern Reference (Repo)
- hffmnnj/kagi-skill — Kagi Claude Skill (Repo, dropped: paid)
