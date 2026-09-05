# Document HTTP Status Capture for Browser Engines — 2026-09-05

## Problem

The diagnosis snapshot added earlier (`process-docs/search_pipeline/`, the diagnosis-snapshot
milestone) proved mojeek answers `EMPTY_BLOCK` runs with a page titled `"Captcha"`. It could not say
what the SERVER answered — a plain request to the same mojeek search URL returns HTTP 403 with the
title `403 - Forbidden`, while a browser-shaped request could equally return HTTP 200 carrying a
captcha page. Those are two different situations with two different consequences, and DOM facts alone
(title/marker/url/readyState) cannot separate them. `src/scraper/chromium_scrape.py` had already
solved the equivalent problem in the scraper lane: `document_status_chain`, a `before_goto`-armed
`page.on("response")` listener collecting the ordered chain of main-frame document responses, with the
LAST entry — not the first hop of a redirect chain — as the real status, because a same-document JS
navigation (e.g. a challenge resolving) can update the document status after the initial navigation
already returned.

## Mechanism translated from Playwright to pydoll/CDP

pydoll has no `page.on("response")`/`frame` object, but the same CDP primitives underneath. Read
`pydoll/browser/tab.py` (`tab.enable_network_events()` → `Network.enable`, one CDP command;
`tab.on(event_name, callback)` → a purely local callback registration, no CDP round trip) and
`pydoll/protocol/network/events.py` (`Network.responseReceived` carries `params.type`, `params.frameId`,
`params.response.status`). The main-frame filter uses `tab._target_id` — confirmed as the correct
"target's own top-level frame ID" value both by reading pydoll's own OOPIF code
(`IFrameContext(frame_id=target_id, ...)`, tab.py) and by the fact that `browser.py`'s existing
`kill_tab` already reads `tab._target_id` directly. No `Page.getFrameTree` round trip needed.

`start_document_status_capture(tab)` (new module, `src/search/document_status.py`, shared by all 7
browser engines rather than duplicated per-engine — these engines already share `browser.py`'s tab
lifecycle, unlike the scraper package's chromium/camoufox lanes, which duplicate their own small
mechanism deliberately because they run on genuinely independent stacks) arms the listener as the
first statement inside each engine's `try:`, before the engine's first navigation — mirroring
`before_goto`'s timing so the very first response is caught too. `attach_document_status(diag,
status_chain)` is a pure, after-the-fact merge called at each engine's existing `return` site, adding
`document_status_chain` (the raw ordered list) and `http_status` (`chain[-1]`, `None` — never a
fabricated default — when nothing was observed) to the diagnosis dict. `_classify_diagnosis` is never
touched or passed these values; the merge happens strictly after the status is already decided.

## Widening the attachment rule (correction during review)

The first cut kept the milestone-1 rule "attach a diagnosis whenever `empty_reason` is non-`None`."
That rule silently drops the exact fact this milestone exists for on `openalex.py`'s 403 branch: that
branch already holds a real observed HTTP status in hand, returns `reason=None` (a deliberate,
pre-existing "plain empty" design, unchanged), and would have logged as a bare `EMPTY` — structurally
the same information loss as mojeek's pre-milestone-1 `EMPTY_BLOCK` records. Corrected to: a diagnosis
is attached whenever an engine returns WITHOUT results, regardless of whether a reason string exists.
Success paths with non-empty results stay diagnosis-free (no engine pays for a diagnose call it does
not need). For the 7 browser engines this changes nothing observable — every one of their non-success
branches already carried an explicit reason, so "without results" and "non-`None` reason" were already
the same set. For `openalex.py` and `scholar.py` it means their 403/captcha-form/zero-results branches
now carry `{"http_status": <code>}` even where `reason` stays `None`, while no `status`/`reason` value
changed anywhere.

## What was deliberately left alone

`brave.py`'s single top-of-function DOM diagnosis (`_diagnose(tab)`) is reused for both its immediate
PoW/CAPTCHA branch and its post-`_wait_for_results`-failure branch — a PRE-EXISTING pattern that
predates this milestone and the diagnosis-snapshot milestone both, and whose classification already
ran off that same (up to ~6s stale, since `_wait_for_results` polls between the two checks) snapshot
before either milestone touched this file. Corrected mid-review: an earlier documentation pass had
wrongly described this reuse as "safe because nothing async happens between the two checks," which is
false — `_wait_for_results` does run between them. That inaccurate sentence was not the process record
of this reuse decision itself (which was never re-litigated here), just a documentation bug, fixed in
`engines/DOCS.md` (the continuously-maintained surface) without touching the earlier process-docs
entry it appeared alongside, per this project's write-once rule for those entries. The new
`document_status_chain`/`http_status` fields are, by contrast, read FRESH at each of brave's three
return sites — `attach_document_status` reads the live `status_chain` list at call time, a cheap
in-memory operation, not a DOM round trip — so the network fact stays current even where the DOM fact
is knowingly stale. This was a deliberate design choice, not an oversight: folding the network read
into the once-per-function DOM diagnosis would have inherited the same staleness for no reason, since
reading the list costs nothing.

## Verification

**Cost:** an isolated dev probe (8 fresh tabs, `/tmp`, not committed) measured `tab.enable_network_events()`
alone at mean 10.02ms (range 7.05-13.72ms across 8 samples); `tab.on(...)` registration (purely local,
no CDP round trip) at mean 0.04ms; the full `start_document_status_capture` helper end-to-end at mean
10.57ms (range 7.13-14.55ms). Against the uniform 6.0s per-engine watchdog (`search_web.py`'s
`ENGINE_WATCHDOG_TIMEOUT`) this is roughly 0.2% of budget. Live `cli.py search_web` runs (2026-09-05,
same day as the diagnosis-snapshot milestone) showed per-engine `search_ms` in the same
network-latency-dominated ranges observed before this change (mojeek ~823-1018ms, google
~1132-1657ms, bing ~557-788ms, brave ~2437-2814ms across every run in this line of work) — no
attributable regression.

**Correctness:** two live `cli.py search_web` runs against real search engines. The showcase result:
a `mojeek` `EMPTY_BLOCK` record carried `diagnosis.title="Captcha"`, `diagnosis.marker="captcha"`, AND
`diagnosis.http_status=200` in the same snapshot — resolving the exact ambiguity this milestone exists
for: mojeek answers its challenge page with HTTP 200, not 403. Also observed: `google` with
`EMPTY_NO_RESULTS`/`EMPTY_NO_CONTAINER` carrying `http_status=200`; `yandex`'s `EMPTY_BLOCK`
early-redirect branch carrying `http_status=200` (the SmartCaptcha page itself is served 200, not a
3xx); `openalex`'s generic `EMPTY` status carrying `diagnosis={"http_status": 200}` under the widened
rule; every `OK`-status engine and the one observed `TIMEOUT_WATCHDOG` (startpage) carrying
`diagnosis=None`, exactly as designed — a watchdog timeout never reaches `search_with_reason`'s return,
so no diagnosis mechanism applies there. Full test suite: 393 passed, including a new
`dev/tests/test_document_status.py` (a fake-tab harness exercising the real
`start_document_status_capture`/`attach_document_status` filter and merge logic without any real CDP
connection) and two rewritten `openalex` tests proving the widened attachment rule.
