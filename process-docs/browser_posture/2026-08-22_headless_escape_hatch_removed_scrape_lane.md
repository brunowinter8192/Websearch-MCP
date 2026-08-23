# WEBSEARCH_HEADLESS escape hatch removed from the scrape lane — single headed-CDP path (2026-08-22)

Follow-on to this area's same-day cdp-headed-route production entry, which shipped the
headed-CDP default and KEPT `WEBSEARCH_HEADLESS` as an operator-forced headless-direct escape hatch
for no-display machines. This entry removes that escape hatch from `src/scraper/scrape_url.py`
entirely: `try_scrape` now unconditionally runs the cdp-headed path.

## Why removed

Decided in the orchestrator↔user exchange, on two grounds:

- **Policy: no fallbacks.** This project rejects fallback/alternate-path machinery in the acquisition
  lanes (the same principle that removed the fit→raw fallback and the camoufox-as-chromium-fallback
  avoidance). The escape hatch was a second acquisition path selectable at runtime — even though it
  was operator-explicit (env var), never automatic, it is still a second path to maintain and test.
- **No real consumer.** The hatch's stated justification was a no-display machine (where headed
  cannot render). This project's real environment is a Mac with a display; it does not run on a
  headless server. The path was dead weight — carried, tested, documented, never exercised in prod.

The distinction that made the hatch *defensible* while it existed (an explicit operator switch, not
a silent auto-fallback) is exactly why it was low-harm to carry — but "low-harm and never used" is
still removable weight once the no-display justification is ruled out for this deployment.

## What changed

- Removed `_acquire_headless_direct`, `_headless_env_forced`, `_FALSY_ENV_VALUES`, the `os` import,
  and the `WEBSEARCH_HEADLESS` env read. `try_scrape` calls `_acquire_cdp_headed` directly, no branch.
- `TOTAL_SCRAPE_BUDGET_HEADLESS_S` deleted; `TOTAL_SCRAPE_BUDGET_CDP_S` renamed back to
  `TOTAL_SCRAPE_BUDGET_S=245.8` (no second budget to distinguish from).
- `launch_mode` kept as a value but as a fixed module constant `LAUNCH_MODE="cdp_headed_backgrounded"`
  — `extract_config_stamp` drops the `launch_mode` PARAMETER (dead flexibility, could never vary), but
  the log field stays (truthful posture stamp, schema continuity with prior records that carry it).
- Config-stamp shape change again (the `launch_mode` param removal) — accepted `config_hash`-boundary
  change, same kind as the other 2026-08-22 stamp changes.

## The shared-var subtlety, and what was deliberately NOT touched

`WEBSEARCH_HEADLESS` is a SHARED env var: `src/search/browser.py`'s 9 DOM search engines still read
it (their own `_FALSY_ENV_VALUES` at `browser.py` lines 23/42) to force their own headless. That lane
was left completely untouched — it is a separate acquisition surface with its own decision. Because
the var stays live for the search lane, `.env.example`'s `WEBSEARCH_HEADLESS` block was NOT deleted
(that would leave a live var undocumented) but REWRITTEN to document the search-engine lane only,
dropping the scraper sentence. Removing the same hatch from the search lane is tracked as its own
follow-up, not folded in here.

## Verification

Two real `cli.py scrape_url` runs, default env and with `WEBSEARCH_HEADLESS=1` explicitly set —
identical result both times (HTTP 200, identical content, log record `launch_mode:
"cdp_headed_backgrounded"`, `total_budget_s: 245.8`, clean teardown), proving the var is now genuinely
inert for the scraper. Test suite: 209 passed (down from 225 — 16 now-dead tests removed: the 12-case
falsy-value matrix, 2 dual-dispatch, 1 headless-budget-timeout, 1 headless-launch_mode stamp), zero
failures. `src/search/browser.py` grep-confirmed unchanged.
