# Both acquisition budgets re-booked to the proven cold-start ceiling + render-wait mechanism swap (2026-08-11)

Milestone 2 of grounding the Camoufox acquisition budget, continuing the same-day milestone-1 entry
(launch-timeout enforcement probe + cold-start ceiling source read). Applies those findings: the
1.1s cold-start summand in both `TOTAL_CAMOUFOX_BUDGET_S` (`src/scraper/camoufox_scrape.py`) and
`TOTAL_SCRAPE_BUDGET_S` (`src/scraper/scrape_url.py`) was a measured TYPICAL duration transferred
from a different lane (`src/search/browser.py`), not a countable maximum — violating R9 of the
time-budget config rules (`process-docs/time_budget/`: "the total cap is the sum of the countable
maxima"). Replaced with the proven ceiling from milestone 1:
`DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS=180000` — Playwright's own enforced fallback
when no `timeout` kwarg is passed to a browser launch, which is exactly what both lanes' throwaway
markdown/acquisition browsers do (`crawl4ai/browser_manager.py`'s `_build_browser_args()` never
sets one).

## New totals

- `TOTAL_CAMOUFOX_BUDGET_S`: 66.1 -> **245.0** (30.0 launch + 30.0 nav + 5.0 render wait + 180.0
  cold start)
- `TOTAL_SCRAPE_BUDGET_S`: 42.4 -> **221.3** (180.0 cold start + 30.0 nav + 5.0 render wait + 1.3
  consent + 5.0 date extraction)

## A per-lane distinction surfaced while re-booking `TOTAL_SCRAPE_BUDGET_S`

`scrape_url.py`'s `try_scrape` constructs `BrowserConfig(headless=True, verbose=False,
enable_stealth=True)` with `UndetectedAdapter()` — this launches via **patchright**, not plain
playwright (`crawl4ai/async_crawler_strategy.py`'s `use_undetected` switch flips on `enable_stealth`
selecting `UndetectedAdapter`). `camoufox_scrape.py`'s `_html_to_markdown` throwaway crawler leaves
`enable_stealth` at its default `False`, so it launches via plain playwright instead. Both still
land on the same 180000ms ceiling: patchright carries an identical
`DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS=180000` constant/mechanism
(`patchright/_impl/_helper.py:253-263`, confirmed in milestone 1), and `_build_browser_args()` is
the same shared crawl4ai function regardless of which adapter selected it — no `timeout` kwarg
either way. The value is unaffected; the code comments now correctly attribute patchright vs. plain
playwright per lane rather than treating the two as interchangeable ("crawl4ai/patchright" in the
prior comment text was imprecise).

## Render-wait mechanism swap: `page.wait_for_timeout` -> `asyncio.sleep`

`camoufox_scrape.py`'s post-navigation render wait switched from Playwright's own
`page.wait_for_timeout` (vendor-marked "Discouraged": "Never wait for timeout in production" — the
warning was first recorded, without being acted on, in the `cloudflare_render_wait` area
(`process-docs/cloudflare_render_wait/`)) to `asyncio.sleep`. R3 of the time-budget config rules
(`process-docs/time_budget/`: "only
deterministically bounded waiting is admissible") does not prefer one mechanism over the other — both
are fixed sleeps, not event-based waits. Trade-off weighed and accepted: `page.wait_for_timeout` is
a page-bound RPC that raises immediately on a mid-wait browser crash; `asyncio.sleep` has no page
dependency, so a mid-wait crash is only detected on the next page call (`page.url`), costing up to
`CAMOUFOX_RENDER_WAIT_S` (5.0s) of wasted wall time in that rare case. Accepted as negligible: the
whole span sits inside a 245.0s outer guard with the same broad exception handling either way — the
failure is still caught, only its timing shifts.

## Test-suite side effect and fix

`tests/test_camoufox_scrape.py`'s `_FakePage.wait_for_timeout` stub had absorbed the render wait for
free (no-op). `asyncio.sleep` is a real stdlib call the fakes cannot intercept — the 5 tests
exercising the happy-path `_acquire()` flow would each incur a genuine 5s sleep (25s added to the
suite) without a fix. Fixed by monkeypatching `CAMOUFOX_RENDER_WAIT_S=0` in those 5 tests (mirroring
the existing pattern already used for `TOTAL_CAMOUFOX_BUDGET_S` in the budget-exhaustion test) and
removing the now-dead `_FakePage.wait_for_timeout` stub.

## Verification

Full suite (`tests/`, 192 tests): 9 failed / 183 passed — the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py`), unchanged by this work, confirmed by identical
failure names before and after. Suite runtime unaffected (~3.4-4.3s across runs), confirming the
`CAMOUFOX_RENDER_WAIT_S=0` monkeypatches worked as intended. Targeted
(`test_camoufox_scrape.py`+`test_scrape_url.py`, 53 tests): all passing. All budget-constant
assertions in both test files read the constants dynamically off the module
(`camoufox_scrape.TOTAL_CAMOUFOX_BUDGET_S`, `scrape_url.TOTAL_SCRAPE_BUDGET_S`), confirmed via grep
before editing — no hardcoded-literal assertion needed touching.

## What this milestone did NOT do

No other calibration value touched (goto timeout, render-wait duration, consent-handling budget,
date-extraction timeout all unchanged). No CLI/pipe wiring. No further re-derivation of the 30000ms
explicit launch-timeout override itself — kept as-is, now with its enforcement proven rather than
assumed (milestone 1) and its provenance comment corrected to no longer claim it as "Playwright's
own default" for the launch phase specifically.
