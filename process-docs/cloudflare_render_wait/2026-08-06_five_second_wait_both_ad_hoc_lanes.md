# Cloudflare-documented 5s render wait, applied to both ad-hoc scrape lanes — 2026-08-06

## Problem

Both ad-hoc lanes (`scrape_url.py`'s crawl4ai/chromium path, `camoufox_scrape.py`'s Camoufox/Firefox
path) captured self-resolving Cloudflare challenge pages too early — the interstitial, not the real
destination page.

## Single-domain measurement (corroborating, not the basis)

guenstiger.de, 2026-08-05, varying only the render wait: 2.0s captured the interstitial, 6.0s the real
product page, 12.0s and 20.0s added ~50 bytes over 6.0s (flat past 6.0s). One domain, one page — not
generalized into a value on its own.

## Basis for the value: Cloudflare's own documentation

developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/, section
"Non-Interactive Challenges" (page last updated 2026-07-06): the visitor must wait until the browser
finishes processing the challenge JavaScript, which "typically takes less than five seconds". Taken
as-is as the render-wait value on both lanes — no invented safety margin added on top, and no attempt
to fit a project-specific number to the single guenstiger.de data point (which sits comfortably inside
the documented range anyway: 6.0s captured the real page, close to the "less than five seconds"
processing figure plus network/paint overhead).

## Chromium lane (scrape_url.py)

`delay_before_return_html`: 2.0 -> 5.0. The prior 2.0 came from a different investigation
(crawl4ai issue #1665's third-party JS-heavy-page saturation-knee measurement, discounted against
`remove_consent_popups`'s own ~1s forced wait) — unrelated to Cloudflare challenges, and too short for
them. `TOTAL_SCRAPE_BUDGET_S`: 39.4 -> 42.4 (the +3.0s delta from the render-wait change carries
through unchanged elsewhere in the budget composition).

## Camoufox lane (camoufox_scrape.py)

This lane had NO render wait at all before this change — raw Playwright, no crawl4ai
`delay_before_return_html` equivalent. Added `CAMOUFOX_RENDER_WAIT_S = 5.0`, applied via
`page.wait_for_timeout(5000)` right after `page.goto`, before `page.content()`.

Separately, `page.goto`'s `wait_until` changed from Playwright's own `"load"` default to
`"domcontentloaded"`: a Cloudflare challenge page holds the request and serves its own full page while
the challenge runs, so the real destination's `load` event cannot fire during that phase — observed
live as a 30s `Page.goto` timeout against guenstiger.de under the unmodified `"load"` default.
`domcontentloaded` fires once the challenge page's own DOM is ready, letting `goto` return; the new
5.0s render wait is what actually gives the challenge JS time to finish and the browser to land on the
real page before capture. `src/crawler/pipe_scraper.py`'s engine already used `"domcontentloaded"` for
its own `goto` calls — this brings the ad-hoc Camoufox lane in line with it (pipe_scraper.py itself was
out of scope for this change).

`TOTAL_CAMOUFOX_BUDGET_S`: 61.1 -> 66.1 (the new 5.0s render-wait summand).

## Not changed

`page_timeout=30000` (chromium lane) and `_PLAYWRIGHT_DEFAULT_TIMEOUT_MS=30000` (Camoufox lane's
navigation cap) — both untouched; only the render wait and, on the Camoufox lane only, `wait_until`
changed. Chromium lane's own `wait_until="load"` also untouched — the `load`-vs-challenge-page failure
mode was observed on the Camoufox lane specifically; the chromium lane was not tested against it in
this session.

## Verification

`tests/test_camoufox_scrape.py` (`_FakePage.goto` extended to accept `wait_until`, a no-op
`wait_for_timeout` added — no assertion depends on exact timing since the fake never actually sleeps)
and `tests/test_scrape_url.py` both pass in full (53 tests) after the change; config-stamp/budget
assertions read the constants dynamically off the module, so they track the new values without being
individually updated. 9 pre-existing failures in `test_proxy_pool.py`/`test_query_logger.py`
(unrelated `src.search.search_web` API drift) were present before this change too, left untouched.
