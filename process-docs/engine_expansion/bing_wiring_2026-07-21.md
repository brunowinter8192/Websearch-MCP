# Bing Wired as Production Engine (2026-07-21)

**Engine:** `src/search/engines/bing.py` — `BingEngine(BaseEngine)`
**Registry:** `src/search/search_web.py` — added to `ENGINES`
**Default set:** `src/search/filter_modes.py` — added to `_DEFAULT_ENGINES`, and to all three mode-sets `_BOOKS_ENGINES`, `_PDF_ENGINES`, `_DOCS_ENGINES` (general web engine, same class as `google`/`duckduckgo`/`mojeek`/`startpage`/`brave`).

Follows the same-day `28_bing_probe.py` re-evaluation. This wiring completes the Bing-index redundancy pair: `bing` (direct major) alongside `duckduckgo` (the existing surrogate — DDG's web index IS Bing's under the hood). The point is redundancy, not new coverage — overlap between `bing` and `duckduckgo`'s result sets is expected and by design, exactly as `google` (direct) and `startpage` (Google-index surrogate) already coexist in the pool.

## Config values

- `ENGINE_MAX_RESULTS["bing"] = 10` — no result-count URL param; DOM renders a fixed 10 `li.b_algo` per page.
- **Deliberately NO `ENGINE_WATCHDOG_OVERRIDE` entry for `bing`.** The probe's measured latency maxed at ~2073ms, comfortably under the `ENGINE_WATCHDOG_TIMEOUT=3.6s` default — unlike `startpage`/`brave`/`open_library`/`semantic_scholar`/`crossref`, which each needed an explicit per-engine ceiling because their intrinsic latency profile pushed past 3.6s. Bing is the fastest browser-scraped engine in the pool by a wide margin; adding an override would have been unnecessary complexity.
- Rate limiter: uniform `RateLimiter(max_requests=4, window_seconds=60)`, same as every other production engine.

## The one non-trivial handling detail: the ck/a URL unwrap

Every organic Bing result href arrives wrapped in a `bing.com/ck/a?...&u=<prefixed-base64>&...` tracking redirect rather than a direct destination URL. `_clean_url` unwraps it: parse the `u` query parameter off the href, strip its observed 2-character prefix (`a1`), base64url-decode the remainder with padding restored, and return the decoded destination — falling back to the raw wrapped href on any decode failure or when no `u` param is present at all (never raises, never drops a result over a decode edge case). This is the one piece of Bing-specific logic beyond the standard mirror-the-existing-engines shape; everything else (browser session, rate limiter, status reporting, block handling) is structurally identical to `startpage.py`/`brave.py`.

## Graceful block→empty contract

Same contract as every other engine: a detected block/bot-check (EN+DE title/body marker scan) returns `[], S.EMPTY_BLOCK` directly, never an exception. Bing's bot-detection is understood to be milder than Google/Brave's and did not trigger at all during the day's probing or this wiring's live verification — but the graceful-degradation code path exists and is structurally in place regardless, matching every other engine in the pool.

## Verification — fully live-verified end-to-end, stronger than the Brave wiring

Unlike the Brave wiring (verified only at the graceful-block level, since that IP was already warm/blocked from the day's prior Brave probing), Bing was NOT blocked at verification time, so this wiring got a complete live confirmation:

- `BingEngine().search_with_reason()` run directly (production class) on 3 queries — all returned real, non-empty results (9, 10, 10 results respectively), `empty_reason=None` throughout.
- Every single returned URL across all 3 queries was checked and confirmed to NOT contain `bing.com/ck/a` — i.e., the unwrap is working correctly in the wired engine, not just in the standalone probe.
- Unit test coverage includes a real captured `ck/a` sample (from the probe's own exploration) decoding to its correct destination URL, plus a monkeypatched-exception case proving the fallback path is reachable and correct.
- CLI (`cli.py search_web "how does DNS work"`) showed the full 12-engine breakdown completing cleanly with `bing: 8` (post-dedup from a raw 10 — expected overlap with other engines, not a defect).

## The redundancy structure observed in action

The same CLI run that verified Bing's wiring happened to also show `google: 0` and `duckduckgo: 0` for that query (both empty that run, for reasons out of this task's scope to diagnose), while `startpage: 10` and `bing: 8` carried the query. This is a live, unplanned illustration of exactly the redundancy design this and the Startpage wiring were built for: when a "major" direct engine returns nothing on a given run, its surrogate/redundant counterpart is available to carry the query rather than the whole index being unavailable for that turn.
