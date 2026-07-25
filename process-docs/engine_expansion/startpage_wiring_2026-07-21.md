# Startpage Wired as Production Engine (2026-07-21)

**Engine:** `src/search/engines/startpage.py` — `StartpageEngine(BaseEngine)`
**Registry:** `src/search/search_web.py` — added to `ENGINES`
**Default set:** `src/search/filter_modes.py` — added to `_DEFAULT_ENGINES`, and to all three mode-sets `_BOOKS_ENGINES`, `_PDF_ENGINES`, `_DOCS_ENGINES` (same class of general web engine as `google`/`duckduckgo`/`mojeek` — receives the mode query modifier + participates in the mode's URL post-filter, no new behavior beyond matching that trio's membership).

Follows on from the dev-only scrapeability probe (`dev/search_pipeline/25_startpage_probe.py`) that established the working mechanism.

## Config values and rationale

- `ENGINE_MAX_RESULTS["startpage"] = 10` — no result-count URL param exists; DOM renders a fixed 10 `div.result` per page regardless of query, consistent with `duckduckgo`/`mojeek` treatment.
- `ENGINE_WATCHDOG_OVERRIDE["startpage"] = 6.0` — the engine's own two-step flow (homepage load → set query → click → wait for `div.result`) measured 2.7-4.1s end-to-end in the probe run, already exceeding the `ENGINE_WATCHDOG_TIMEOUT=3.6s` default on the slowest query. Same pattern as the existing `open_library` (6.0), `semantic_scholar` (5.0), `crossref` (6.0) overrides — engines whose intrinsic latency profile doesn't fit the 3.6s watchdog get an explicit per-engine ceiling rather than a global bump.
- Rate limiter: uniform `RateLimiter(max_requests=4, window_seconds=60)` registered into the shared `_limiters` dict, same as every other production engine — no Startpage-specific throttling was added.

## Live-verify evidence (production path, not the probe script)

`StartpageEngine().search_with_reason()` run directly, 3 queries, all `empty_reason=None`, 10/10 results each: `gebrauchte waschmaschine frankfurt` (kleinanzeigen.de, wmz-horn.de, hgs-horn.de, ebay.de), `python asyncio tutorial` (realpython.com, docs.python.org, YouTube, Medium), `best noise cancelling headphones 2025` (nytimes.com/Wirecutter, whathifi.com, rtings.com, faz.net).

CLI-level (`cli.py search_web "gebrauchte waschmaschine frankfurt"`, run inside the worktree — the globally-installed `searxng-cli` wrapper points at the separate main-repo checkout, not this worktree): engine breakdown showed `google 0`, `startpage 9` for the same query in the same run. **This is an observed data point from a single run, not a claim about cause** — the `google=0` could reflect a CAPTCHA/empty state, a transient block, or something query-specific; no diagnosis of Google's empty reason was performed as part of this task. What it does show: on this run, Startpage returned results for a query where the direct Google engine returned none, which is the scenario Startpage was reintroduced to cover (a Google-index access path when direct-Google comes back empty) — demonstrated as a single co-occurrence, not established as a general/reliable fallback relationship.

`search_engine_drilldown --engine startpage` for the same query printed 10 real titles/URLs/snippets (Kleinanzeigen, HGS-Horn, eBay, Facebook Marketplace, markt.de, etc.). The breakdown count (9) vs. drilldown listing (10) discrepancy is the existing cross-engine URL dedup in `build_engine_pools` (one Startpage URL also returned by `mojeek`), not a Startpage-specific defect.

## Test coverage

`tests/test_startpage_engine.py` — 7 pure-function tests against two seams factored out of the DOM-driven engine (no network/browser): `_build_results` (field mapping, missing-url skip, max_results cap) and `_classify_diagnosis` (block-marker, iframe-challenge, page-still-loading race, clean-no-container). Full suite after wiring: 9 pre-existing failures in `test_query_logger`/`test_proxy_pool` (unrelated, present before this change), 71 passing — no new failures introduced by the wiring.
