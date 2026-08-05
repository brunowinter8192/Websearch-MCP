# Pipe path's own fallback route reports a real landed URL (2026-08-12)

Follow-up to `process-docs/scrape_pipeline/landed_url_wired_into_pipe_path_2026-08-10.md`'s
milestone-3 decision. That session recorded `(landed_url=None, same_target=None)` on BOTH of
`src/crawler/pipe_scraper.py`'s fallback routes, reasoning that `redirected_url` is untrustworthy on
both. Review measured curl_cffi directly (this venv, curl_cffi 0.16.0): a request to
`https://www.rfc-editor.org/rfc/rfc2616` returns `response.status_code=200`,
`response.url=https://www.rfc-editor.org/info/rfc2616/`, `response.redirect_count=1` — curl_cffi
follows redirects itself and reports exactly where it landed. `_fallback_fetch` was discarding that
information at pipe_scraper's OWN call site (returning only `response.text`), before crawl4ai ever
got a chance to overwrite it. The fix belonged in this module, not in crawl4ai — this session made
it.

## Why the two fallback routes needed different fixes

Path (a) — `fallback_fetch_function=_fallback_fetch`, crawl4ai's own mechanism — calls
`_fallback_fetch` FROM INSIDE crawl4ai. Confirmed in the source
(`async_webcrawler.py`): `_fallback_html = await _fallback_fn(url)` is consumed directly as HTML
text (`sanitize_input_encode(_fallback_html)`). The function's `str | None` return is a CONTRACT
with crawl4ai, not this module's own choice — changing it to a tuple would break that wiring. There
is also no channel back out of that internally-mediated call for the landed URL crawl4ai itself
does not surface (crawl4ai forces `redirected_url=url`, the requested URL, on this route
regardless of what curl_cffi followed). A module-level dict keyed by URL was considered as a
side-channel and explicitly rejected: `_scrape_all` runs `asyncio.gather` over hundreds of URLs at
once, and anything keyed that loosely risks cross-contamination if the same URL is ever in flight
twice in one run, with no clean ownership/cleanup story either. Path (a) stays `(None, None)` —
correct, not merely unfixed.

Path (b) — `_own_fallback_rescue`, called directly from `_scrape_one`'s own `except Exception:`
block — calls `_fallback_fetch` too, but this call is OUR OWN, not crawl4ai-mediated. The fix:
split the curl_cffi call into a new shared low-level `_curl_cffi_get(url)` returning the raw
curl_cffi `Response` (or `None` on any exception — same fail-soft posture). `_fallback_fetch`
becomes a thin wrapper over it (unchanged signature, still crawl4ai's `fallback_fetch_function`).
`_own_fallback_rescue` calls `_curl_cffi_get` DIRECTLY instead, reading `response.url` itself. This
required updating the two existing tests that mocked `_fallback_fetch` to simulate path b (they now
mock `_curl_cffi_get`, since the internal call graph genuinely changed) — legitimate test
maintenance, not scope creep, since the whole point of the change was giving path (b) a call site
`_fallback_fetch` structurally cannot provide.

`same_target` on this log is tri-state (`True`/`False`/`None`) since milestone 3, for a reason that
now applies asymmetrically across the two routes: `None` on path (a) means "structurally
untrustworthy, will never be fixed here"; `None` on path (b) means only "the curl_cffi fetch never
completed this specific time" (exception/timeout) — a real distinction a later reader must not
collapse. Computed as `is_same_target(url, landed_url) if landed_url else None` at both call sites,
not via `is_same_target`'s own missing-input convention (`True` on `None`) — that default fits a
normal caller with nothing to compare, but here a `None` landed_url specifically means "nothing was
observed," and claiming "same" from that would be the exact class of fabrication
`content_judgment_removal_2026-08-05.md` already eliminated once elsewhere.

## Verification

26 tests in `tests/test_pipe_scraper.py` (was 25): the two pre-existing path-b integration tests
updated to mock `_curl_cffi_get` (their own assertions about `pipe_fallback_used`/`resolved`/
`http_status` unchanged, now also asserting real `landed_url` values); a new redirecting-fetch test
(real landed_url, `same_target=False`); a new total-fetch-failure test (`landed_url`/`same_target`
both `None`); and a concurrency test — 3 URLs on 3 different domains (no per-domain pacing gate
serializing them) rescued at once via `asyncio.gather`, with DELIBERATELY reverse completion order
(the first-requested URL finishes last) so a shared-state bug would surface as swapped values, not
just as correct-by-luck ordering — asserts each record's `landed_url` matches its own request.

Full suite: `9 failed, 175 passed`. `FAILED` list diffed against the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py`) — identical, no drift.

## Real-run attempts: one live, one controlled — both real results, not fabricated proof

Live: `api.crossref.org` (a DOI works-endpoint) + `rfc-editor.org` through the real CLI. The
browser succeeded on both this run — the crossref browser-weakness recorded in
`process-docs/pipe_scraper_hardening/2026-08-05_curl_cffi_fallback_acquisition_path.md` (0/23 empty
in 2026-08) did not reproduce; path (b) never triggered live.

Controlled: a local HTTP server (302 redirect → `Content-Type: application/octet-stream` +
`Content-Disposition: attachment`) built specifically to trigger Playwright's `net::ERR_ABORTED`
(confirmed in crawl4ai's `async_crawler_strategy.py`: unswallowed since `accept_downloads=False`,
this module's default). It fired exactly the predicted `RuntimeError` — the real logged
`crawl4ai_error_message` field quotes it verbatim (`"Failed on navigating ACS-GOTO:\nPage.goto:
Download is starting"`).

## The finding this attempt actually surfaced — an open question about the EXISTING fallback design

That `RuntimeError` did NOT reach `_scrape_one`'s own `except Exception:` block (path b never
fired: `pipe_fallback_used=False` on the resulting record). crawl4ai's own `_crawl_web` wrapper —
a layer neither the original 2026-08-05 fallback-path work nor this session had previously
inspected — caught it internally and returned a normal `success=False` `CrawlResult` instead of
letting the exception propagate out of `crawler.arun()`. The 2026-08-05 verification that path (b)
IS reachable at `max_retries=0` used a DIFFERENT failure shape entirely (a local TCP server that
accepts a connection and never responds, forcing a genuine navigation TIMEOUT) — that shape was not
re-tested this session. Open, unresolved question this raises: how often is path (b) actually
reachable in this crawl4ai version, given that at least one real, source-confirmed browser
exception (`net::ERR_ABORTED`) is absorbed internally by crawl4ai before it ever reaches this
module's own exception handler, while a bare navigation timeout is not. Not investigated further in
this session — a question about the fallback design that predates this session's own change, left
for whoever next touches `_own_fallback_rescue`/path (b) reachability to pick up.
