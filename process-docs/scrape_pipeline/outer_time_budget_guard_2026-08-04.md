# Scrape Pipeline — Outer Time-Budget Guard for the Ad-Hoc Scrape Path

*Dated entry — historical record of the investigation; the live current state is the source code, not this file.*

## Problem Observed

As of 2026-08, `scrape_url_workflow`/`try_scrape` in `src/scraper/scrape_url.py` had no bounded
total wall time. `page_timeout=60000` bounds only Playwright's `page.goto`. Everything after a
*successful* goto was unbounded from this project's own code: crawl4ai's two internal,
non-configurable 30s waits (`async_crawler_strategy.py` — `wait_for_selector("body",
state="attached")` and the visibility poll via `csp_compliant_wait`), `remove_consent_popups` JS
+ its Python-side wait, and markdown generation + `PruningContentFilter` (synchronous CPU, no
timeout anywhere). A caller had no maximum.

## Fix — One Outer Guard, Value Fixed at 39.4s

A pre-decided, fixed budget (39.4s — not re-derived, not rounded, not a CLI arg) implemented as
`TOTAL_SCRAPE_BUDGET_S` in `src/scraper/scrape_url.py`, enforced via a single
`asyncio.wait_for(_acquire(), timeout=TOTAL_SCRAPE_BUDGET_S)` — one guard over the whole
acquisition rather than more per-phase tuning (the alternative — bounding each of goto/render
wait/consent handling/markdown gen individually — was explicitly out of scope for this pass and
would have meant touching `page_timeout`, `wait_until`, `delay_before_return_html`,
`remove_consent_popups`, and content-filter settings, all frozen for a separate milestone).

## Guard Placement — Acquisition Only, Not the Whole Call

`try_scrape`'s existing body (browser launch → `crawler.arun()` → `extract_date` → classification)
was moved into a nested `async def _acquire()`, called via `asyncio.wait_for`. Two things
deliberately sit OUTSIDE the guarded span:

- **Config construction** (before `_acquire`) — instant, and its output (`_empty_meta`, the config
  stamp) must exist on every return path including a timeout.
- **Post-acquisition local work** (`truncate_content`, `write_sidecar`, `log_scrape`, all in
  `scrape_url_workflow`) — a budget-exhausted record must still be writable, so logging cannot sit
  inside the guarded span. Consequence: `timings_ms.total_wall` in `scrape_log.jsonl` can exceed
  39.4s by that post-processing cost — the guard bounds ACQUISITION, not the full logged wall time.

## Two Things The Guard Does NOT Cover (documented, not fixed)

1. `asyncio.wait_for` only cancels at await points. Markdown generation + `PruningContentFilter`
   run as synchronous CPU inside crawl4ai's `arun()` — a pathological synchronous parse can overrun
   the budget before the guard gets a chance to fire. No thread-offload/executor was added; this is
   a documented limit (comment on `TOTAL_SCRAPE_BUDGET_S`, `DOCS.md` Gotchas), not a bug to chase.
2. crawl4ai's two internal 30s waits and the consent-popup 500ms×2 sleeps stay untouched, as
   directed — they run *inside* the guarded span, not worked around.

## Failure Shape and Log Distinguishability

On timeout, `try_scrape` returns `("", {"garbage_type": "budget_exhausted", ...})` — identical
shape to every other failure branch (`http_error`, `browser_missing`, etc.), logged via the same
`_GARBAGE_MESSAGES` lookup (`"Scrape exceeded the total time budget (39.4s)"`) and the same
`log_scrape` call. `outcome`/`garbage_type` = `"budget_exhausted"` in `scrape_log.jsonl`
distinguishes it from every other failure mode. `TimeoutError` is caught in its own `except`
clause, ahead of the generic `except Exception` (which still separately classifies
`browser_missing` via `is_browser_launch_error`).

## Config Stamp

`extract_config_stamp` gains `total_budget_s`, read directly off `TOTAL_SCRAPE_BUDGET_S` — same
"read the real value off the constant, never re-declare it" rule the stamp already followed for
`page_timeout_ms`/`cache_mode`/etc. This is not a crawl4ai kwarg (no config object carries it); it
is this module's own guard value, included so the stamp still changes if the guard value changes.

## Verification

- Regression guard: `tests/test_scrape_url.py` — `AsyncWebCrawler` monkeypatched to hang,
  `TOTAL_SCRAPE_BUDGET_S` monkeypatched to 0.05s for a fast test; asserts `garbage_type ==
  "budget_exhausted"` and a matching log message.
- Real-budget evidence: a raw-socket TCP server on `127.0.0.1` that accepts the connection but
  never writes a response (Playwright hangs mid-navigation, distinct from a `net::ERR_*` refusal).
  `scrape_url_workflow` against it: wall time 39.45–39.46s, logged `outcome="budget_exhausted"`,
  `timings_ms.total_wall=39446`.
- Real unaffected-scrape evidence: `https://www.rfc-editor.org/rfc/rfc2119` — wall time 2.94s,
  `outcome="ok"`, real published-date extraction (`1997-03-01`) intact.
- Full suite before/after: 11 pre-existing failures unrelated to this package unchanged;
  `tests/test_scrape_url.py` 10→13 passing (3 new).

Not verified at the `cli.py` entry-point level (the `scrape_url` subcommand) — only
`scrape_url_workflow`/`try_scrape` called directly; `cli.py`'s own arg-parsing/routing around the
call was not re-exercised in this pass.
