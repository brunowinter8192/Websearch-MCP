# Scrape Pipeline — Setting page_timeout / delay_before_return_html On Rule Basis

*Dated entry — historical record of the investigation; the live current state is the source code, not this file.*

## Problem Observed

As of 2026-08, the outer `TOTAL_SCRAPE_BUDGET_S=39.4` guard's own composition comment named five
countable maxima (browser cold start 1.1s, navigation cap 30s, render wait 2.0s, consent handling
1.3s, date extraction 5.0s) while the actual `CrawlerRunConfig` still ran `page_timeout=60000` and
left `delay_before_return_html` at the library's implicit `0.1` default — the stated composition
and the real configuration contradicted each other on two of the five summands.

## page_timeout: 60000 -> 30000

60000 was never a derived figure. crawl4ai's own CHANGELOG documents it as a replacement for a
previously hardcoded 30-second timeout, justified only as "better handling for slow-loading
pages" — no measurement cited. The library that actually executes the timeout, patchright 1.61.2
(`DEFAULT_PLAYWRIGHT_TIMEOUT_IN_MILLISECONDS`, `_impl/_helper.py`), itself defaults to 30000;
crawl4ai's own docs/examples scatter across 10000/30000/60000/80000/120000/200000 with no
consistent pattern. Rule applied: a phase cap is not raised above the default of the layer that
actually executes it without evidence for the raise. No such evidence existed, so the value falls
back to the executing layer's own default, 30000.

## delay_before_return_html: implicit 0.1 -> explicit 2.0

crawl4ai issue #1665 carries a third-party measurement of this exact parameter on a JS-heavy page:
0s captured 12,376 chars (partial), 3s captured 33,874 chars (full), 5s and 20s captured the
identical 33,874 — a saturation knee at 3s, flat above it across nearly an order of magnitude of
extra wait, so raising further only costs wall time with no content benefit.

Set to 2.0, not 3.0, because `remove_consent_popups=True` (already on in this project) spends its
own unconditional ~1s of render wait on every page before HTML capture — two fixed 500ms sleeps,
one inside crawl4ai's `remove_consent_popups.js` itself, one on the Python side after the JS eval
returns. This project had already reproduced that ~1s as a genuine render-wait effect, not a
consent-JS side effect: an identical 126-byte `raw_markdown` diff on rfc-editor.org from
`delay_before_return_html=1.1` ALONE, with `remove_consent_popups=False` (documented in this
area's `avoid_ads_and_consent_popups_2026-08-03.md`). The two windows are therefore counted
against each other, not added: ~1s consent-forced wait + 2.0s explicit = ~3s effective render
window, matching the #1665 knee.

## Config Stamp

`extract_config_stamp` already read `page_timeout_ms` off `run_config.page_timeout` (no code
change needed for that value to appear in `scrape_log.jsonl`). `delay_before_return_html` was
never previously an explicit kwarg, so it was never stamped; added `delay_before_return_html_s`
reading `run_config.delay_before_return_html` directly, applying this module's existing rule
("every kwarg this codebase explicitly passes is load-bearing, hence stamped") to a kwarg this
change newly makes explicit. Real record (`https://www.rfc-editor.org/rfc/rfc2119` via `cli.py
scrape_url`): `config_hash="371d434adf"`, `config.page_timeout_ms=30000`,
`config.delay_before_return_html_s=2.0`.

## Verification — Differential Test, Not a Single Run

A single scrape at the new value proves nothing about whether `delay_before_return_html` did any
work — a page that renders fully at 0.1s would pass identically at 2.0s. Ran the SAME URL
(rfc-editor.org, the one page in this project already documented as sensitive to render-wait
timing via its Nuxt.js hydration) through `cli.py scrape_url` twice: once with
`delay_before_return_html` temporarily reverted to the library default `0.1` (local edit,
reverted immediately after, never committed), once at the new `2.0`.

Result: `bytes_raw_markdown` IDENTICAL both times (11218), wall time 2166ms vs 4246ms. Read
honestly: `remove_consent_popups=True`'s own forced ~1s wait already crosses this page's
hydration window even at the 0.1s default, so under the CURRENT full config (both switches on
together) rfc-editor.org does not exercise `delay_before_return_html` at all — the earlier
126-byte diff was only observable in isolation (`remove_consent_popups=False`). This run is
evidence of no-regression on this page only, not evidence the 2.0s wait does observable work
under production config. No alternate page was tried in this pass.

## Test Suite

Full suite before and after: `11 failed, 103 passed` both times — identical, all 11 failures
pre-existing and unrelated to this package (`test_proxy_pool`, `test_query_logger`,
`test_sigint_report`). `tests/test_scrape_url.py`: `13 passed` both times — no new test added
for the two value changes themselves; the existing `extract_config_stamp` test still passes
since the returned dict grew a superset key.
