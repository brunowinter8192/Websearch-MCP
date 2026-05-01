# search05 — Engine Expansion

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

## Quellen

- StractOrg/stract — Stract Search Engine (Repo, dropped: $27/mo commercial API)
- MarginaliaSearch/MarginaliaSearch — Marginalia Engine (Repo, deferred: try-or-drop later)
- MarginaliaSearch/docs.marginalia.nu — Marginalia Self-Hosting Docs (Repo)
- cyanheads/hn-mcp-server — HN MCP Reference Implementation (Repo)
- voska/hn-cli — HN CLI Reference (Repo)
- lucjon/Py-StackExchange — Stack Exchange Python Wrapper (Repo)
- searxng/searxng — Metasearch Pattern Reference (Repo)
- hffmnnj/kagi-skill — Kagi Claude Skill (Repo, dropped: paid)
