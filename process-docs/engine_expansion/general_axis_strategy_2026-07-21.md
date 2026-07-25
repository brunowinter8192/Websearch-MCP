# General Web Axis — Index-Family Model & Expansion Strategy (2026-07-21)

Chat-level synthesis of the strategy that drove the 2026-07-21 general-engine expansion (startpage, brave, bing, yandex, marginalia). The per-engine reasoning is in the sibling reeval/wiring records; this is the connective model — why these engines, and the principle behind the pool shape.

## Index-family model

Search engines cluster by the underlying WEB INDEX they read. Truly independent indexes (own crawler) are few, and for Western/German queries essentially: **Google, Bing, Mojeek, Brave, Yandex, Marginalia**. Everything else (DuckDuckGo, Startpage, Ecosia, Qwant, Searx) is a FRONTEND on Google or Bing.

Consequence, and the load-bearing distinction:
- **New coverage (distinct URLs)** comes ONLY from an independent index. Adding a Google/Bing reskin adds zero new URLs.
- **Access-path redundancy** is what a reskin adds: an alternate way to reach the SAME index when the direct engine is blocked. DuckDuckGo IS Bing's index; Startpage IS Google's index fetched server-side.

## Surrogate principle (as of 2026-07-21, user-driven)

For each MAJOR LICENSED index, hold BOTH a direct "major" engine AND a surrogate — two independent access paths, so no single point of failure. Achievable only for Google and Bing (they license third-party frontends):
- Google index: `google` (direct) + `startpage` (surrogate). Google CAPTCHAs ~23%+; startpage carries the Google index when it does.
- Bing index: `bing` (direct) + `duckduckgo` (surrogate). DDG is the reliable carrier; bing-direct is the insurance path.

Mojeek, Brave, Yandex, Marginalia are STANDALONE by nature — no third party fronts them, so no free surrogate exists. A block on one simply removes that index for that round; the pool carries via the others (each independent index is domain-specific — a Brave PoW does not affect google.com).

## Keep-criterion (relaxed, use-case-driven)

Real usage = the web-research skill fires 2-4 near-simultaneous `search_web` queries per session, then days idle (drilldown reads cache, no re-query). At that volume:
- **KEEP** if an engine returns some USABLE hits before any block — integrate with graceful block→empty. A block after a few clean hits is a non-event (the low volume sits inside the observed clean window; other engines carry).
- **DROP** only if there is truly no through — blocked from the first query, never a usable result.
- **Quality is a separate axis, reported honestly** — an accessible-but-junk engine (e.g. Mojeek "garbage" on some queries) is not a block-drop but its low value is stated, not hidden.

## Pool map as of 2026-07-21 (8 general web engines)

| Engine | Index | Access | Reliability caveat |
|---|---|---|---|
| google | Google | browser (pydoll) | ~23%+ CAPTCHA |
| startpage | Google (surrogate) | browser | reliable |
| bing | Bing | browser | reliable, fastest; ck/a URL-unwrap |
| duckduckgo | Bing (surrogate) | browser | reliable carrier |
| mojeek | Mojeek (own) | browser | independent but quality-weak |
| brave | Brave (own) | browser | IP/velocity PoW — hits a few then blocks; graceful empty |
| yandex | Yandex (own) | browser | SmartCaptcha after ~7; good German quality (IP-geo); graceful empty |
| marginalia | Marginalia (own) | HTTP API | shared "public" key rate-limits (429); English/text-web niche, off-axis for German local |

Academic/community/catalog engines (crossref, openalex, semantic_scholar, stack_exchange, open_library, lobsters) are a separate axis, not general web.

## What is NOT achievable

The independent-index well is dry after these six. No free surrogate exists for Mojeek/Brave/Yandex/Marginalia. Remaining independent indexes are out: Stract (paid API), Baidu (non-Western). Dead: Cliqz, Neeva, Gigablast. So this pool is close to the ceiling of what independent Western web search offers.

## Sources

- `src/search/search_web.py` (ENGINES registry, ENGINE_MAX_RESULTS, ENGINE_WATCHDOG_OVERRIDE, K=google_count pool cap), `src/search/filter_modes.py` (_DEFAULT_ENGINES + mode-sets), `src/search/engines/{startpage,brave,bing,yandex,marginalia}.py`.
- `github_issues` (patchright #113/#103, camoufox #538) for the headed/anti-bot landscape underpinning the browser-engine choices.
