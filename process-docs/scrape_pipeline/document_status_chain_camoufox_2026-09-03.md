# Camoufox lane: last main-frame document response status + the status chain as a fact (2026-09-03)

Sibling fix to this area's same-day chromium-lane document-status-chain entry (the chromium
lane, M1) — same contract, same field name, applied to `src/scraper/camoufox_scrape.py`'s
`try_scrape_camoufox`, driven through plain Playwright directly rather than a crawl4ai hook.

## Problem

`_acquire_camoufox` read `status_code = response.status` straight off the `page.goto` Response,
fixed at goto-return time. `CAMOUFOX_RENDER_WAIT_S` (5.0s, `asyncio.sleep` between `goto` and
`page.content()`) is the exact same self-resolving-challenge window M1 fixed on the chromium lane —
a Cloudflare challenge answers goto with a stale status, then its own JS navigates the main frame
again during the render wait; the captured HTML is the real page, the recorded status stays stale.

## Mechanism

Camoufox drives plain `playwright.async_api` directly (`AsyncCamoufox(PlaywrightContextManager)`,
confirmed by reading `camoufox/async_api.py`) — there is no crawl4ai hook system on this lane to
attach through. `_make_document_status_listener(page, status_chain)` registers a plain
`page.on("response", ...)` listener directly on the `Page` object, called BEFORE `page.goto(...)` so
the goto response itself becomes the chain's first entry. Same filter and guard as M1's version:
`request.resource_type == "document"` AND `request.frame is page.main_frame` (not
`is_navigation_request()` alone), with `request.frame` access guarded in try/except (it raises for a
navigation request issued before its own frame exists).

Duplicated from `chromium_scrape.py`'s version rather than imported — consistent with this module's
existing precedent (`_find_app_bundle`'s own comment) of not sharing small lane-specific mechanisms
across the two independent acquisition lanes.

`status_code` becomes `document_status_chain[-1]` when the chain is non-empty; an empty chain (the
listener saw nothing at all) falls back to the goto Response's own status unchanged, matching M1's
never-invent-a-status rule. `document_status_chain` lands in `meta`,
`scrape_url_camoufox_workflow`'s log record, `pipe_scraper_records.py`'s
`_log_pipe_camoufox_record`, and `_format_camoufox_output`'s own rendered line — same fact-not-
verdict caveat text as M1.

## Callers proven, not just asserted

`src/crawler/pipe_scraper_acquisition.py`'s `_scrape_one_camoufox` maps `status >= 400` to outcome
`http_error`, reading `meta['status_code']` directly — no code change was needed there, since it
already only ever reads that one field. The behavior change (a resolved-challenge page now yielding
`ok` instead of `http_error`) is the INTENDED effect of the acquisition-primitive fix flowing
through unchanged wiring, not a new branch. Proven with a new test
(`dev/tests/test_pipe_scraper.py::test_scrape_all_camoufox_resolved_challenge_status_yields_ok`)
feeding a faked `try_scrape_camoufox` meta shaped exactly like a resolved challenge
(`status_code=200`, `document_status_chain=[403, 302, 200]`) through the real `_scrape_all` ->
`_scrape_one_camoufox` -> JSONL-record path, asserting `outcome == "ok"` and the chain field's
presence in the written record. `pipe_scraper_config.py`, `pipe_scraper_constants.py`, the chromium
engine (`_scrape_one`), and `chromium_scrape.py` were left untouched, per scope.

## Test fakes extended

`dev/tests/test_camoufox_scrape.py`'s `_FakePage` previously had no `.on()`, no `main_frame`, and
its `goto()` just returned a canned `_FakeResponse`. Extended with `.on("response", handler)`
storage, a `main_frame` attribute, a `_FakeRequest` wrapper (`resource_type`/`frame`), and a
`fire_response(status, resource_type="document", frame=None)` helper. Since
`CAMOUFOX_RENDER_WAIT_S` is zeroed in every test using this fake (a pre-existing convention, not new
here), there is no real "later" window to inject events into between `goto()` returning and
`page.content()` being awaited — `goto()` instead fires the configured `document_statuses` sequence
(plain ints for main-frame document responses, or `(status, resource_type, frame)` tuples for the
excluded-response cases) entirely before returning. This is a deliberate, equivalent stand-in for
"redirect chain plus a same-document JS navigation that resolves during the wait": the production
code under test never inspects WHEN an event fired, only that the chain is complete by the time it
reads `document_status_chain` after `page.content()`. The RETURNED goto Response's own status is
kept independently configurable (`status=` param, defaulting to `document_statuses[-1]` when the
list is omitted) so the override test can prove the fix actually overrides a genuinely different
value, not one that coincidentally matches.

## Verification

`dev/tests/test_camoufox_scrape.py`: 34 -> the extended file passes in full (`pytest
dev/tests/test_camoufox_scrape.py -q`). New cases: 403->302->200 chain overriding a distinct goto
status of 403 to 200; a single-entry ordinary-page chain (unchanged pre-fix behavior); an empty
chain falling back to the goto Response's own status; a stylesheet response and a document response
on a different (non-main) frame both excluded from the chain; the browser_missing path carrying an
empty chain like every other acquisition-error field; the workflow log record and
`_format_camoufox_output`'s rendered line both carrying the new fact.

Full `dev/tests/` suite: 369 passed / 0 failed (integration baseline 361 + 8 new tests across
`test_camoufox_scrape.py`/`test_pipe_scraper.py`, no regressions).

Live run, direct Python call (`scrape_url_camoufox_workflow`, no CLI wiring — this lane is not
exposed via `cli.py` as of 2026-08-27, per `src/scraper/DOCS.md`'s Gotchas) against the SAME repro
URL as M1, `skeptics.stackexchange.com/questions/2566/does-baking-soda-remove-odors`: `document_status_chain`
`[403, 302, 200]`, `status_code` 200 — Camoufox observed the identical challenge-then-resolve shape
chromium did on this host (as anticipated going in: a live Playwright probe on this same URL had
already seen 403 -> 302 -> 200 on both browser engines before this milestone started). The JSONL
record (`src/logs/scrape_log.jsonl`, last line at the time) carries `"document_status_chain": [403,
302, 200]` alongside `"http_status": 200`, `"outcome": "ok"`, `"engine": "camoufox"`.

## Scope held

No content judgment, marker matching, or "blocked"/"solved" verdict introduced — the chain stays an
ordered list of numbers, read only for its last entry and its emptiness. `pipe_scraper_config.py`,
`pipe_scraper_constants.py`, `_scrape_one` (chromium engine), and `chromium_scrape.py` were not
touched.
