# Playwright timeout defaults verified against the vendor docs — 2026-08-06

Orchestrator-side record: RAG research in chat, no worker counterpart. Written the same day as the
five-second render-wait change in this area, after that change had already been merged.

## What was unverified

`camoufox_scrape.py`'s budget comment described both 30.0s summands as "Playwright's own default"
for `BrowserType.launch()` and `Frame.goto()`. That description rested on assistant training
knowledge, not on a fetched source — no Playwright documentation was indexed in this project at that
point (`websearch-reference` held the full camoufox.com tree plus both camoufox GitHub READMEs, and
nothing from playwright.dev).

## What the vendor docs say

13 pages of `playwright.dev/python/docs` indexed into `websearch-reference` (7 API class pages, 6
guides, culled from 87 discovered).

- `browser_type.launch`, option `timeout`: "Maximum time in milliseconds to wait for the browser
  instance to start. Defaults to `30000` (30 seconds). Pass `0` to disable timeout."
- `page.goto`, option `timeout`: "Maximum operation time in milliseconds, defaults to 30 seconds,
  pass `0` to disable timeout."
- `page.goto`, option `wait_until`: "defaults to `load`", with four values — `load`,
  `domcontentloaded`, `networkidle` (marked **DISCOURAGED**), `commit`.
- `launch_persistent_context` carries the same 30000 default as `launch`.

Both figures matched the claim. The assumption held; it is now sourced rather than asserted.

## Counter-evidence found in the same pass, against this project's own new code

`page.wait_for_timeout` — the call the Camoufox lane now uses for its render wait — carries a
"Discouraged" box in Playwright's own reference: "Never wait for timeout in production. Tests that
wait for time are inherently flaky. Use Locator actions and web assertions that wait automatically."

Reading recorded at the time: the warning targets test code, where an assertion exists to wait on
instead. A scraper facing a third-party challenge page has no such assertion — no selector whose
appearance could be awaited without knowing the challenge's internals — so the alternative Playwright
offers does not exist in this position. That is a judgement, not a refutation: the vendor discourages
the mechanism this project adopted, and that stands on the record.

`networkidle` being marked DISCOURAGED by the vendor is a separate item, relevant to this project's
earlier investigation into networkidle's cost.

## Provenance of the budget summands after this check

| Summand | Value | Provenance as of 2026-08-06 |
|---|---|---|
| Camoufox browser launch | 30.0s | vendor-documented (Playwright `launch` timeout default) |
| Page navigation | 30.0s | vendor-documented (Playwright `goto` timeout default) |
| Post-navigation render wait | 5.0s | vendor-documented (Cloudflare challenge-page processing figure) |
| Markdown-conversion cold start | 1.1s | internal measurement, reused from the chromium lane as a proxy |

One caveat the check did NOT close: whether camoufox's `launch_options`/`AsyncCamoufox` actually
forwards the `timeout` kwarg this project passes, so that the launch ceiling is really in force. The
navigation ceiling is provably enforced — a live guenstiger.de run hit it as a 30s `Page.goto`
timeout. Nothing comparable has been observed for the launch phase.

Second caveat, category rather than provenance: two summands are CEILINGS, one is an expected
duration, one is a typical duration. Their sum is neither a true worst case nor a realistic
expectation. It functions as an outer guard against hangs, which is what it is used for; it is not a
statement about runtime.
