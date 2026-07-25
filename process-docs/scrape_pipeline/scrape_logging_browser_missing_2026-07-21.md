# Scrape Pipeline — browser_missing Outcome vs. Genuine Empty

*Dated entry — historical record of the investigation; the live current state is the source code, not this file.*

## Problem Observed

As of 2026-07, a missing/failed patchright chromium binary produced a `scrape_log.jsonl` signature indistinguishable from a genuinely empty or blocked page: `outcome:"empty"`, `total_wall` ~300-400ms, `http_status:null`, `bytes_raw_markdown:null`. `try_scrape`'s broad `except Exception` caught the `AsyncWebCrawler` launch error (patchright's pinned chromium v1208, "Google Chrome for Testing", was not installed) and folded it into the same generic empty-content path as an actual empty/blocked scrape.

Consequence: a whole debugging session investigated the scraping strategy (gates, selectors, phase escalation) under the belief that content extraction was inadequate, when the real cause was an uninstalled browser executable — every URL, including trivial static sites like `example.com`, failed identically in ~300ms with "No content extracted".

## Root Cause

`try_scrape`'s `except Exception` block had no branching — any exception (network timeout, DNS failure, browser launch failure, page crash) collapsed to the same `{**_empty_meta}` return, logged at WARNING, surfaced to the user as the generic "No content extracted" message. Browser-launch failures are an environment defect (affects every URL uniformly, persists until fixed), categorically different from a per-URL scrape miss (affects one URL, may be transient/site-specific) — but the code did not distinguish them.

## Fix Evaluated and Applied

Added `is_browser_launch_error(exc) -> bool` in `src/scraper/scrape_url.py`: lowercases `str(exc)` and checks substring membership against `_BROWSER_LAUNCH_SIGNATURES = ("executable doesn't exist", "playwright install", "browsertype.launch")`. These three phrases are specific to Playwright/patchright's own launch-failure message format and were confirmed (via unit test) not to appear in ordinary per-URL exception text (`Timeout 60000ms exceeded`, `net::ERR_CONNECTION_REFUSED`, `net::ERR_NAME_NOT_RESOLVED`).

On match: `try_scrape` returns `garbage_type: "browser_missing"` and logs at ERROR (not WARNING) — signaling "fix the environment", not "this page failed". `_GARBAGE_MESSAGES["browser_missing"]` names the concrete fix: `./venv/bin/python -m patchright install chromium`. All other exceptions keep the prior generic behavior unchanged.

**Alternative considered and rejected:** narrowing the `except` clause to a specific Playwright exception type (e.g. catching a hypothetical `BrowserExecutableNotFoundError`). Rejected because Playwright/patchright do not expose a distinct exception class for this — the launch failure surfaces as a generic `Error` with a distinguishing message string, so substring matching on the message is the only available seam without depending on unstable internal exception hierarchies.

## Verification

Simulated via `monkeypatch` on `AsyncWebCrawler.__aenter__` raising a synthetic exception carrying the real patchright message shape (`"BrowserType.launch: Executable doesn't exist at /fake/chrome"`) — confirms `try_scrape` maps it to `garbage_type: "browser_missing"` at ERROR level, and that an ordinary timeout exception through the same path keeps `garbage_type: None`. Not verified against a real uninstalled-binary environment (would require uninstalling patchright's chromium in the working dev environment).

## Sources

None — internal defect investigation, no external sources.
