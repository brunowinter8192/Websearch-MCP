# Scrape Pipeline — avoid_ads Rejected, remove_consent_popups Adopted

*Dated entry — historical record of the investigation; the live current state is the source code, not this file.*

## Scope

Two unused crawl4ai `BrowserConfig`/`CrawlerRunConfig` booleans, evaluated independently against the
installed 0.9.2 source and real pages — not from documentation. Both corrections below were caught by
reading source directly, not by trusting the task brief that initiated this investigation.

## Correction 1 — Config Object Placement

`avoid_ads` is a `BrowserConfig` parameter (`async_configs.py:827`, inside the `BrowserConfig.__init__`
spanning lines 669-1110), NOT `CrawlerRunConfig` (which starts at line 1330). This determines which
config object a future change would need to touch.

## Correction 2 — CookieYes Coverage Claim

The originating brief for this investigation claimed CookieYes is absent from crawl4ai's
`remove_consent_popups` provider list. False per source: `remove_consent_popups.js` (installed 0.9.2)
explicitly covers CookieYes — click selectors `.cky-btn-accept` / `[data-cky-tag="accept-button"]`
(lines 53-54), container selectors `.cky-consent-container` / `.cky-overlay` (lines 400-401), body-class
cleanup `cky-modal-open` (line 693). No live CookieYes reproduction was found this session (2 candidate
German retail sites with `cky-` string hints in raw HTML showed no actual CookieYes DOM node rendered
in either mode) — that is an inconclusive empirical check, not a contradiction of the source finding.

## Switch 1 — `avoid_ads`: Rejected

**Mechanism** (`browser_manager.py:1302-1322,1386-1388`): on every new browser context,
`context.route(pattern, lambda route: route.abort())` is registered for 21 hardcoded glob patterns
(`ad_tracker_patterns`) — Google Analytics, GTM, googlesyndication, doubleclick, adservice.google,
adsystem.com, adzerk, adnxs, LinkedIn ads, facebook.net, Twitter analytics/ads, Hotjar, Clarity,
scorecardresearch, pixel.wp.com, amazon-adsystem, Mixpanel, Segment. Fixed list — no constructor
parameter to extend or override it.

**Empirical test on BfN.de** (`https://www.bfn.de/artenportraits/castor-fiber`, the exact page behind
this project's own recorded 61s-networkidle cost — `phase_escalation_networkidle_cost_2026-05-24.md`):
via `result.network_requests` (`capture_network_requests=True`), only 3 domains were ever requested —
`www.bfn.de`, `code.etracker.com`, `www.etracker.de`. Zero of 16 requests failed/blocked with
`avoid_ads=True`. etracker is absent from crawl4ai's list. This switch would not have helped the case
that motivated interest in it.

**Pattern-matching defect, proven with real Playwright routing** (not `fnmatch` approximation): a
standalone probe (`context.route("**/google-analytics.com/**", handler)` against three URLs) showed
the handler fired ONLY for the bare-domain URL `https://google-analytics.com/analytics.js` — NOT for
`https://www.google-analytics.com/analytics.js` or `https://ssl.google-analytics.com/ga.js`. The glob
requires a literal `/` immediately preceding the domain; real tracker scripts are served from
subdomains (`www.`, `ssl.`, region-specific) almost universally, so this pattern list is largely inert
against real-world traffic even for domains nominally on it. Confirmed via a synthetic local test page
(`<script src="https://www.google-analytics.com/analytics.js">`) through the actual production
`BrowserConfig(avoid_ads=True)` path: the request went through unblocked in both modes.

**Decision: leave off.** No measured benefit on the motivating page, a demonstrated defect that
neuters even nominal coverage, not configurable to work around from this project's side.

## Switch 2 — `remove_consent_popups`: Adopted, Alongside the Existing Three Layers

**Execution order vs `excluded_selector`, determined from source**
(`async_crawler_strategy.py:1044-1046` vs `content_scraping_strategy.py:371,685`):
`remove_consent_popups(page)` runs on the LIVE browser page — click "Accept All" across ~100+
CMP-specific selectors (ordered by market share) plus generic/text-pattern/shadow-DOM/iframe
fallbacks, then CMP JS APIs (IAB TCF, Didomi, Cookiebot, Osano, Klaro), then removes ~140 known CMP
container selectors, then CMP iframes, then restores body scroll — all BEFORE `html = await
page.content()` captures HTML (line 1085). `excluded_selector` (this project's own hand-maintained
list) runs LATER, on the captured HTML STRING, inside a completely separate code path
(`content_scraping_strategy.py`, lxml/cssselect). No collision possible — sequential and
complementary. Added alongside `excluded_selector`, `is_garbage_content`, and `strip_consent_prefix`,
none of which were removed or altered.

**Real recovered content — azubiyo.de** (`https://www.azubiyo.de/bewerbung/layout/`, a page previously
flagged for a `consent_prefix` edge case in `dev/scrape_pipeline/garbage_eval/10_live_garbage_test.py`,
2026-03): with `excluded_selector` active but `remove_consent_popups=False`, ~3400 chars of German
consent-banner text ("Auf Azubiyo.de und anderen Webseiten der FUNKE Works GmbH verwenden wir
Cookies...") leaked into `raw_markdown` — this project's own selector list does not catch this
banner. With `remove_consent_popups=True`: gone, real content ("Übersicht... Berufswahltest...")
starts immediately. Verified through the real CLI (not just an isolated filter test):
`bytes_raw_markdown` 41583→37988, `bytes_returned` 15098→14392, `outcome`/`garbage_type` unchanged
(`ok`/`null`).

**Neutral case — stepstone.de:** identical content whether the switch is on or off — this project's
existing `excluded_selector` already fully handles this specific page's banner. No harm, no gain here.

**Unconditional cost, precisely sourced:** TWO separate 500ms sleeps fire on every page regardless of
whether a consent popup exists — one inside `remove_consent_popups.js` itself (line 332, `await new
Promise(r => setTimeout(r, 500))`, the "wait for CMP animations/transitions" step, unconditional) and
one in Python after the JS eval returns (`async_crawler_strategy.py:1581`,
`page.wait_for_timeout(500)`). Measured end-to-end on `rfc-editor.org` (no consent layer): +0.96s wall
time (1.93s→2.89s), matching the two-sleep prediction from source almost exactly. Recorded as an
explicit code comment at the `CrawlerRunConfig` construction site — this is the figure the future
determinism work needs: ~1s spent on EVERY scrape to help only the subset of pages with a consent
layer.

**125-byte content diff on the no-consent-layer control — root-caused, not dismissed as minor.**
The same RFC control page showed a 126-byte `raw_markdown` diff (540353→540479) even though no CMP
action ever fired there. Investigation: reproduced the IDENTICAL diff (byte-for-byte, same extra text
line) by setting `delay_before_return_html=1.1` alone, with `remove_consent_popups=False` — the
consent-removal JS never ran in that test. This isolates the cause to wait time, not a DOM mutation
from `remove_consent_popups`'s own actions. Traced the exact injected text via occurrence-counting in
the raw captured HTML (2 occurrences of the title string without the extra delay — `<title>` tag and
`og:title` meta — vs 3 with it): the third occurrence sits inside a `<span>` with inline CSS matching
the standard "visually-hidden but accessible" pattern (`clip: rect(0px,0px,0px,0px); clip-path:
inset(50%); height:1px; width:1px; overflow:hidden; position:absolute; ...` — CSS-clip-hidden, NOT
`display:none`). `rfc-editor.org` is a Nuxt.js SPA (`<meta name="generator" content="Nuxt">`); this is
a Nuxt SEO/accessibility hydration artifact that finishes rendering into the DOM sometime between the
default ~0.1s and ~1.1s wait windows. crawl4ai's markdown extraction works off the static captured
HTML string and does not distinguish CSS-clip-hidden from genuinely visible content, so it gets swept
in. Conclusion: a generic "waited longer before capture on a still-hydrating page" artifact — any
config change adding comparable wait time would produce the same class of diff on this kind of page,
independent of what `remove_consent_popups`'s own JS does.

**Anomaly, investigated, not reproduced:** one run against stepstone.de hit the full 60.32s
`page_timeout` with zero content, `remove_consent_popups=True`. Retested 3× immediately after — both a
minimal config (no content filter/excluded_selector) and the exact production-matching config — all
completed cleanly in ~4s with consistent `raw_len=7144` output. Logged as an unattributed,
non-reproduced anomaly; not blocking the decision, flagged in `DOCS.md` as a watch-item.

**Decision: on, alongside the existing three consent-handling layers.** Evidence: genuine incremental
content-quality recovery on a real page current selectors miss (azubiyo.de), confirmed non-conflicting
execution order, and a bounded, precisely measured, now-documented cost (~1s) — acceptable for this
ad-hoc single-URL scrape path given the milestone's own motivating open question (a click dismisses a
popup the way a user would; DOM removal alone can leave an overlay backdrop behind, per
`scrape_pipeline.md`'s Open Questions).

## Sources

crawl4ai `browser_manager.py`, `async_crawler_strategy.py`, `async_configs.py`,
`js_snippet/remove_consent_popups.js` (installed 0.9.2, read directly, not from documentation);
BfN.de, azubiyo.de, stepstone.de, rfc-editor.org (live fetches during this session, 2026-08-03, not
archived); a synthetic local test page and a direct Playwright `context.route()` probe (both
throwaway, not persisted).
