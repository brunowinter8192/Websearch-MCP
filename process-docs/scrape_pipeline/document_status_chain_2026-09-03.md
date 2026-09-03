# Chromium lane: last main-frame document response status + the status chain as a fact (2026-09-03)

## Problem, reproduced live

`src/scraper/chromium_scrape.py` reported `http_status` off crawl4ai's `CrawlResult.status_code`.
Reading `async_crawler_strategy.py`'s "Walk the redirect chain" block (the code right after
`page.goto` in `AsyncPlaywrightCrawlerStrategy`) showed it walks `response.request.redirected_from`
backwards from the `page.goto` response and keeps the EARLIEST hop's status — a value fixed at
`goto`-return time and never touched again.

A self-resolving Cloudflare "Just a moment" page answers `goto` with 403, then its own JS navigates
the main frame again during `delay_before_return_html` (5.0s, `process-docs/scrape_pipeline/
2026-08-06_five_second_wait_both_ad_hoc_lanes.md`). The real page lands at 200 and IS what
`chromium_scrape.py` returns as content — but the recorded status stayed 403, and crawl4ai's own
`is_blocked()` (`antibot_detector.py`) treats any 403-with-HTML as blocked unconditionally
(`"HTTP {status} with HTML content"`, no pattern match required for large pages), reporting
`success=False` on a fully present page.

Live repro before the fix, `skeptics.stackexchange.com/questions/2566/does-baking-soda-remove-odors`:
`HTTP status: 403`, `success=False`, `error_message="Blocked by anti-bot protection: HTTP 403 with
HTML content (356575 bytes)"`, alongside 29714 bytes of real raw markdown (the actual question
page). This is the same 403-stays-stuck behaviour `2026-08-06_five_second_wait_both_ad_hoc_lanes.md`
already recorded on guenstiger.de and left unfixed at the time ("Two behaviours observed as
unchanged... the recorded HTTP status stays 403 even though the complete product page came back").

## Mechanism chosen

Read `async_crawler_strategy.py`'s hook system (`self.hooks` dict, `execute_hook`, `set_hook`): one
callable per hook name, called with live `page`/`context` objects. `before_goto` (fired at the point
right before `page.goto()`, and also before the `raw:`/`file://` local-content branch) was unused by
this module — attaching a listener there needed no change to the existing `on_page_context_created`
hook (`_reject_popup_pages`), avoiding the "one function per hook name" constraint entirely.

`_make_document_status_listener(status_chain)` returns a `before_goto`-shaped hook that registers
`page.on("response", ...)`, filtering to main-frame document navigations exactly as Playwright's own
maintainer guidance describes: `request.resource_type == "document"` AND `request.frame is
page.main_frame` (not `request.is_navigation_request()` alone, which is also true for iframe
navigations). `request.frame` access is guarded in try/except — confirmed via `patchright/async_api/
_generated.py`'s own docstring: it raises when "navigation request is issued before the
corresponding frame is created" (iframes/popups). Each matching response's status is appended, in
order, to a plain list closed over by the hook — no crawl4ai patching, no second function on an
already-used hook name.

State carry-out: since `_acquire_cdp_headed` constructs a fresh `AsyncPlaywrightCrawlerStrategy` per
`try_scrape` call, the list lives as a local in `_acquire_cdp_headed` and is passed through as an
explicit parameter to `_acquire_scrape`, which reads it after `crawler.arun()` returns — no shared
module state, consistent with this module's existing "no shared in-memory state" contract (DOCS.md).

## Field and override rule

New fact: `document_status_chain` (a list, e.g. `[403, 302, 200]`), carried in `meta`, the JSONL log
record, and rendered as its own `_format_scrape_output` line, explicitly labeled a fact and not a
verdict — the same caveat this module already puts on crawl4ai's own diagnosis line.

`status_code` (and therefore `http_status`) becomes `document_status_chain[-1]` when the chain is
non-empty — the response of the page whose content was actually captured. When the chain is empty
(no main-frame document response observed at all — a `raw:` input never calls `page.goto`, so the
hook's listener never fires), `status_code` falls back to crawl4ai's own `result.status_code`
unchanged; no status is ever invented. On an ordinary page with no redirect, the chain has exactly
one entry and `status_code` matches today's pre-fix value bit for bit.

crawl4ai's own diagnosis (`extract_crawl4ai_diagnosis`, the `crawl4ai_*` fields, the rendered
"OBSERVATION" line) was deliberately left untouched — this module still never overrides or
suppresses it. Live-confirmed on the repro URL post-fix: `document_status_chain` is `[403, 302,
200]`, `status_code` is now 200, and crawl4ai's own diagnosis line STILL reports
`success=False`/`"Blocked by anti-bot protection: HTTP 403 with HTML content (388825 bytes)"` on the
exact same result — proof the two facts are independent, and that crawl4ai's diagnosis keeps its own
documented false-positive shape (`status_gate_removal_evidence_2026-08-05.md`, the guenstiger.de
6.0s case) rather than being reconciled or hidden.

## Verification

`dev/tests/test_chromium_scrape.py` extended with fakes that exercise the real `_acquire_cdp_headed`/
`_acquire_scrape` code path: a fake `AsyncWebCrawler.arun` calls `crawler_strategy.execute_hook(
"before_goto", ...)` itself (the same call crawl4ai's own source makes) against a fake page/request/
response trio, then fires main-frame document responses in order before returning a result. Cases
covered: 403→302→200 (chain recorded in full, `status_code` becomes 200, overriding a distinct
crawl4ai-reported 403); a single 200 (ordinary-page shape, unchanged behaviour); an empty chain
(fallback to crawl4ai's own `result.status_code`, e.g. 403, never invented); a non-document response
(stylesheet) and a document response on a non-main frame (a fake iframe object) both correctly
excluded from the chain. `_empty_meta` and the browser-launch-failure path both carry an explicit
`document_status_chain: []`, matching every other acquisition-error field's treatment.

Full `dev/tests/` suite: 354 passed / 0 failed before this change (verified via `git stash` on this
branch, `challenge-status`), 361 passed / 0 failed after (354 + 7 new tests, no regressions). No
`test_query_logger.py`/`test_proxy_pool.py` failures were present on this branch at the time — an
earlier documented standing-failure count for those files does not describe this branch's state as
of 2026-09-03.

Live runs, both via `cli.py scrape_url_chromium`:
- `skeptics.stackexchange.com/questions/2566/does-baking-soda-remove-odors` (the motivating repro):
  `HTTP status: 200`, `Document status chain: [403, 302, 200]`, crawl4ai diagnosis line unchanged in
  shape (still its own `success=False`/403-block observation).
- `www.rfc-editor.org/rfc/rfc2119` (control): `HTTP status: 200`, `Document status chain: [302,
  200]` — this control URL redirects at the HTTP layer to `/info/rfc2119/` (`landed_url` differs from
  the requested URL), so its chain legitimately shows the goto-redirect hop rather than a single
  entry; this is the documented "ordinary page, chain may show goto redirect hops" shape, not a
  challenge-page case. The JSONL record for this run (`src/logs/scrape_log.jsonl`, last line at the
  time) carries `"document_status_chain": [302, 200]` alongside the existing fields.

## Scope held

`src/scraper/camoufox_scrape.py` and everything under `src/crawler/` were untouched, per the
milestone's explicit scope — camoufox's own status-staleness (the Camoufox lane reads status off the
`goto` `Response` directly, recorded as unfixed in
`2026-08-06_five_second_wait_both_ad_hoc_lanes.md`) is a separate, later milestone. No content
judgment, marker matching, or "blocked"/"solved" verdict was introduced anywhere — the chain is
read only as an ordered list of numbers, never pattern-matched or interpreted.
