# Camoufox launch-timeout enforcement probe + markdown-conversion cold-start ceiling source read (2026-08-11)

Milestone 1 of grounding `TOTAL_CAMOUFOX_BUDGET_S`'s summands (`src/scraper/camoufox_scrape.py`) in
verified fact rather than assumption. Closes two specific open items: whether the `timeout` kwarg
this module forwards to Camoufox's launch is actually enforced (left open by the playwright-defaults
verification work), and whether the 1.1s markdown-conversion cold-start summand (a duration reused
from a different lane's measurement, not a ceiling) has any countable ceiling at all. Dev artifacts:
`dev/camoufox_lane/01_launch_timeout_probe.py`, `dev/camoufox_lane/md/01_launch_timeout_probe_findings.md`.

## Launch-timeout enforcement: confirmed by live probe, not just source

Sent `timeout=1` through the exact production chain (`_build_camoufox_kwargs`-equivalent kwargs ->
`camoufox.launch_options()` -> `AsyncCamoufox(from_options=...)`) and observed
`playwright._impl._errors.TimeoutError: BrowserType.launch: Timeout 1ms exceeded.` after 0.293s wall
— the exact call site (`camoufox/async_api.py:125`, `playwright/_impl/_browser_type.py:98`)
production's own `_acquire()` uses. A control run at 30000ms (the production value) launched cleanly
in 1.465s, `new_page()`/`close()` both succeeding. The `timeout` kwarg
`_PLAYWRIGHT_DEFAULT_TIMEOUT_MS` forwards through `launch_options`'s catch-all kwargs
(`camoufox/utils.py:493,858`) is real enforcement, not a value Camoufox/Playwright silently drops.

## Cold-start ceiling: 180000ms (180s), not unbounded — but NOT the vendor-docstring number either

Traced `_html_to_markdown`'s `AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False))`
launch path end to end: `enable_stealth=False` default (`crawl4ai/async_configs.py:826`) means the
default `PlaywrightAdapter` is used, not `UndetectedAdapter`
(`crawl4ai/async_crawler_strategy.py:93,114-117`) -> `use_undetected=False` ->
**plain `playwright.async_api`, not patchright** (`crawl4ai/browser_manager.py:805-806`). No
persistent-context/managed-browser/CDP config is set by `_html_to_markdown`, so the plain-launch
branch runs: `self.playwright.chromium.launch(**browser_args)` (`crawl4ai/browser_manager.py:938`).
`_build_browser_args()` (`browser_manager.py:1057-1122`) never sets a `"timeout"` key. With no
explicit timeout, Playwright's own `TimeoutSettings.launch_timeout()`
(`playwright/_impl/_helper.py:296-302`) falls back to
`DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS = 180000` (`_helper.py:290`) — the value actually
placed into the launch RPC's `params["timeout"]` (`playwright/_impl/_connection.py:648-656`).
Patchright carries the identical constant/mechanism (`patchright/_impl/_helper.py:253-263`), so the
ceiling is the same 180000ms even on the stealth/undetected branch, which this call site does not
take. This is a LAUNCH timeout, distinct from the page/navigation timeout default (also 30000ms,
`playwright/_impl/_helper.py:289`) — moot here anyway since `_html_to_markdown` passes a `raw:`
pseudo-URL that performs no real navigation.

Separately, and orthogonal to the above: the installed `playwright` package's own generated stub
docstring (`playwright/async_api/_generated.py:16269`, same text again at `:16445` for
`launch_persistent_context`) states the launch timeout "Defaults to `30000` (30 seconds)" — this
does NOT match the value actually enforced by the implementation
(`DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS = 180000`, `_helper.py:290`). Two sources inside
the same installed package disagree; the enforced value is the one read from `_impl/_helper.py`, not
the docstring. No re-derivation of `_PLAYWRIGHT_DEFAULT_TIMEOUT_MS` or any budget summand was made
from this — out of this milestone's scope, recorded as fact only.

## What this milestone did NOT do

No budget re-booking. `TOTAL_CAMOUFOX_BUDGET_S`, `TOTAL_SCRAPE_BUDGET_S`, and the 1.1s cold-start
summand were read but not touched. Whether/how the newly-confirmed 180000ms cold-start ceiling
should change any booked figure is explicitly a later milestone's decision.
