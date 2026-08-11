# Camoufox Launch-Timeout Enforcement + Cold-Start Ceiling — Findings

Produced by `dev/camoufox_lane/01_launch_timeout_probe.py` (live run 2026-08-11) plus a source read
of the installed `crawl4ai`/`playwright`/`patchright` packages. Milestone 1 of the camoufox-budget
acquisition-budget grounding work. Scope: enforcement + ceiling facts only — no budget re-booking
recommendation (later milestone).

## (a) Probe outcome: launch-timeout kwarg IS enforced

Two runs through the SAME chain `src/scraper/camoufox_scrape.py`'s `_acquire()` uses (kwargs ->
`camoufox.launch_options()` -> `AsyncCamoufox(from_options=...)`):

| Run | timeout_ms | outcome | wall time | exception |
|---|---|---|---|---|
| LOW | 1 | exception | 0.293s | `playwright._impl._errors.TimeoutError` |
| CONTROL | 30000 (production default) | launched cleanly | 1.465s | none |

**LOW run — verbatim traceback:**

```
Traceback (most recent call last):
  File ".../dev/camoufox_lane/01_launch_timeout_probe.py", line 66, in attempt_launch
    async with AsyncCamoufox(from_options=resolved) as browser:
               ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File ".../venv/lib/python3.14/site-packages/camoufox/async_api.py", line 41, in __aenter__
    self.browser = await AsyncNewBrowser(_playwright, **self.launch_options)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../venv/lib/python3.14/site-packages/camoufox/async_api.py", line 125, in AsyncNewBrowser
    browser = await playwright.firefox.launch(**from_options)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../venv/lib/python3.14/site-packages/playwright/async_api/_generated.py", line 16307, in launch
    await self._impl_obj.launch(
    ...<17 lines>...
    )
  File ".../venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py", line 98, in launch
    await self._channel.send(
        "launch", TimeoutSettings.launch_timeout, params
    )
  File ".../venv/lib/python3.14/site-packages/playwright/_impl/_connection.py", line 69, in send
    return await self._connection.wrap_api_call(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File ".../venv/lib/python3.14/site-packages/playwright/_impl/_connection.py", line 559, in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
playwright._impl._errors.TimeoutError: BrowserType.launch: Timeout 1ms exceeded.
```

**CONTROL run:** `outcome=launched`, `wall=1.465s`, no exception — `browser.new_page()` and
`page.close()` both succeeded.

**Conclusion:** the `timeout` kwarg `camoufox_scrape.py` passes into `_build_camoufox_kwargs()` is
forwarded, unmutated, all the way to Playwright's `BrowserType.launch()` and IS enforced at
runtime — confirmed by direct observation (`TimeoutError` raised at the exact call site the
production module also uses), not inferred from source reading alone.

## (b) Cold-start launch ceiling: `_html_to_markdown`'s browser DOES have a countable ceiling — 180000ms (180s)

Traced the exact path `_html_to_markdown` (`src/scraper/camoufox_scrape.py`) triggers via
`AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False))`:

1. `BrowserConfig.enable_stealth` defaults `False` (`crawl4ai/async_configs.py:826`), unset by
   `_html_to_markdown` → `AsyncPlaywrightCrawlerStrategy` uses the default `PlaywrightAdapter`, not
   `UndetectedAdapter` (`crawl4ai/async_crawler_strategy.py:93`) → `BrowserManager(...,
   use_undetected=isinstance(self.adapter, UndetectedAdapter))` = `False`
   (`crawl4ai/async_crawler_strategy.py:114-117`).
2. `use_undetected=False` → **plain `playwright.async_api` is used, NOT patchright**
   (`crawl4ai/browser_manager.py:805-806`: `if self.use_undetected: from patchright.async_api ...
   else: from playwright.async_api import async_playwright`).
3. `BrowserConfig.use_persistent_context`/`use_managed_browser`/`cdp_url` all default
   `False`/`None` (`crawl4ai/async_configs.py:786-794`) and are unset by `_html_to_markdown` → the
   plain-launch branch executes: `self.browser = await self.playwright.chromium.launch(**browser_args)`
   (`crawl4ai/browser_manager.py:938`), `browser_type` defaulting to `"chromium"`
   (`crawl4ai/browser_manager.py:137`).
4. `browser_args` is built by `_build_browser_args()` (`crawl4ai/browser_manager.py:1057-1122`) —
   **no `"timeout"` key is ever set in it** (confirmed: no occurrence of a `"timeout"` dict key
   anywhere in `browser_manager.py`).
5. With no `timeout` param, Playwright's own `BrowserType.launch()`
   (`playwright/_impl/_browser_type.py:66-104`) sends the `"launch"` RPC via `self._channel.send("launch",
   TimeoutSettings.launch_timeout, params)` (`_browser_type.py:98-99`). `_augment_params`
   (`playwright/_impl/_connection.py:648-656`) computes `params["timeout"] =
   timeout_calculator(params.get("timeout"))` — since `params.get("timeout")` is `None`,
   `TimeoutSettings.launch_timeout(None)` (`playwright/_impl/_helper.py:296-302`) returns
   `DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS` = **180000** (`playwright/_impl/_helper.py:290`).

**Cold-start ceiling: 180000ms (180s), enforced by Playwright itself, not unbounded.** This is a
LAUNCH timeout, categorically separate from PAGE/NAVIGATION timeouts: the page-level default
(`DEFAULT_PLAYWRIGHT_TIMEOUT_IN_MILLISECONDS = 30000`, `playwright/_impl/_helper.py:289`, used by
`TimeoutSettings.timeout()` for `goto`/other page ops) governs a different call path and is never
reached here — `_html_to_markdown` calls `crawler.arun(url=f"raw:{html}", ...)`, a `raw:`
pseudo-URL that performs no real navigation.

**Patchright carries the identical mechanism and value** (`patchright/_impl/_helper.py:253-263`:
same `DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS = 180000` constant,
`patchright/_impl/_browser_type.py:83`: same `TimeoutSettings.launch_timeout` calculator) — the
180000ms ceiling would hold identically if `_html_to_markdown` ever ran with `enable_stealth=True`
(the `UndetectedAdapter`/patchright branch) instead.

## (c) Vendor-docstring vs. enforced-default discrepancy (confirmed orchestrator-side, this session)

Two different sources inside the SAME installed `playwright` package disagree on what `launch()`'s
timeout defaults to:

- **Docstring** (`playwright/async_api/_generated.py:16269`, and identically at `:16445` for
  `launch_persistent_context`): "Maximum time in milliseconds to wait for the browser instance to
  start. Defaults to `30000` (30 seconds). Pass `0` to disable timeout."
- **Enforced value** (`playwright/_impl/_helper.py:290`): `DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS
  = 180000`, returned by `TimeoutSettings.launch_timeout()` (`_helper.py:296-302`) whenever no
  explicit `timeout` is supplied — the actual value placed into `params["timeout"]`
  (`playwright/_impl/_connection.py:648-656`, `_augment_params`) and sent to the driver for every
  `launch`/`launch_persistent_context`/`connectOverCDP` RPC call
  (`playwright/_impl/_browser_type.py:99,167,210`, all three keyed off the same
  `TimeoutSettings.launch_timeout` calculator).

Stated as fact, both sides cited by `file:line`; no interpretation or re-booking recommendation
drawn from it here.
