# Yandex Wired as Production Engine (2026-07-21)

**Engine:** `src/search/engines/yandex.py` — `YandexEngine(BaseEngine)`
**Registry:** `src/search/search_web.py` — added to `ENGINES`
**Default set:** `src/search/filter_modes.py` — added to `_DEFAULT_ENGINES`, and to all three mode-sets `_BOOKS_ENGINES`, `_PDF_ENGINES`, `_DOCS_ENGINES` (general web engine, same class as `google`/`duckduckgo`/`mojeek`/`startpage`/`brave`/`bing`).

Follows the same-day `29_yandex_probe.py` re-evaluation. Unlike `bing` (direct-major alongside DuckDuckGo's surrogate) and `startpage` (a Google-index frontend, redundant to direct `google`), **Yandex is a genuine NEW-COVERAGE engine** — its own independent crawler and index, not a second path to an index already represented elsewhere in the pool.

## Config values

- `ENGINE_MAX_RESULTS["yandex"] = 10` — no result-count URL param; DOM renders a fixed 10 `li.serp-item` per page.
- **Deliberately NO `ENGINE_WATCHDOG_OVERRIDE` entry**, same treatment as `bing`. Two reasons stack here: the probe's clean-query latency maxed at ~2083ms, comfortably under the `ENGINE_WATCHDOG_TIMEOUT=3.6s` default; AND the engine's own blocked-query path (see refinement 1 below) returns fast on a block rather than approaching that ceiling either way. Both the clean and the blocked path stay well inside the default watchdog.
- Rate limiter: uniform `RateLimiter(max_requests=4, window_seconds=60)`, same as every other production engine.

## Two refinements over the plain mirror-the-existing-engines pattern

The probe surfaced two Yandex-specific issues beyond the standard shape (browser session, rate limiter, status reporting, graceful block→empty — all identical to `brave.py`/`bing.py`):

1. **Early block detection.** The probe measured blocked queries taking 6-8s wall time because diagnosis only ran after the result-wait poll timed out. `search_with_reason()` now checks `tab.current_url` for a `showcaptcha`/`checkcaptcha`/`/captcha` redirect substring IMMEDIATELY after navigation, before entering `_wait_for_results` at all. Live-verified: blocked queries in production now return `S.EMPTY_BLOCK` in 425-1572ms — a dramatic improvement over the probe's 6-8s, and comfortably inside every other engine's latency profile.
2. **Self-referential URL filter.** The probe found a `yandex.com/video/preview/...` self-link mixed into one result set (the generic `li.serp-item` selector also matches video-carousel SERP cards, not just organic results). `_build_results()` now drops any item whose destination hostname carries `"yandex"` as a dot-separated label via `_is_self_referential()` — checked against `hostname.split(".")`, not a raw substring, specifically so a real external domain like `notyandex.com` is never misclassified as self-referential (verified with a dedicated test case).

No URL-unwrap step is needed (unlike Bing's `ck/a`) — Yandex's `a.OrganicTitle-Link` href is already the direct destination URL.

## Graceful block→empty contract

Same contract as every other engine in the pool: a detected block returns `[], S.EMPTY_BLOCK` directly, never an exception — reinforced here by two independent paths (the upfront URL check, and the same check repeated inside `_classify_diagnosis` as a fallback if a block manifests without leaving the `/search/` path).

## Verification — fully live-verified end-to-end, including both refinements under real conditions

This wiring got a complete live confirmation, not just a synthetic test pass:

- 7 of 10 live production queries returned real, non-empty results (10 each) — e.g. `gebrauchte waschmaschine frankfurt` → `kleinanzeigen.de`, `quoka.de`, `wmz-horn.de`, `markt.de`, `ebay.de`; `python asyncio tutorial` → `realpython.com`, Medium, YouTube, `docs.python.org`. Zero self-links present across every sample checked.
- 3 of 10 queries hit the CAPTCHA redirect live, in production, and returned gracefully in 425-1572ms each — directly observing refinement 1 working under a real block, not just a mocked/simulated one.
- Unit tests (`tests/test_yandex_engine.py`, 14 cases) cover both refinements at the pure-function level: `_is_block_url` on real redirect-shaped URLs, `_is_self_referential` including the `notyandex.com` negative case, and `_build_results` dropping a synthetic `yandex.com/video/preview/...` item while keeping real external results.
- CLI (`cli.py search_web "beste kaffeemaschine test"`) showed the full 13-engine breakdown completing cleanly with `yandex: 5`.
- Full test suite: same 9 pre-existing `test_query_logger`/`test_proxy_pool` failures as before this change, no new failures.

This is a stronger verification level than the Brave wiring (which was only block-path-verified, since that IP was already warm at verification time) — Yandex's wiring observed BOTH the clean-result path and the block-and-recover path live, in the same verification session, with both refinements exercised against real production traffic rather than only against test fixtures.
