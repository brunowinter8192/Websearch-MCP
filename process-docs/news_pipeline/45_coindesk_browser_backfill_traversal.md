# 45 — CoinDesk backfill traversal: false-DISABLED fix + DOM-growth measurement

Builds on the timeline API confirmed as the right pagination surface. This entry covers the
first implementation of the uncapped browser-driven backfill traversal, the premature termination
bug encountered in Stage A, the fix, and the open performance problem before a full run.

**NOT the chosen method — superseded by later HTTP-based work.** The browser DOM-scrape traversal works but is O(n)-bound
by the growing DOM (the perf problem below was never fully beaten). The chosen discovery method calls the
SAME timeline API directly over plain HTTP (no browser, no DOM, no O(n)) — a later stage in this area. This entry is kept for
the false-DISABLED-race finding and the DOM-growth measurement.

## Script

`dev/news_pipeline/exploration/03_coindesk_backfill_traversal.py` — pydoll headed Chrome
(`open -gna "Google Chrome"` + CDP), copy of production `discover.py` machinery (no src/ import),
plateau tolerance 3, DISABLED retry tolerance 3, crash-safe checkpoint every 50 clicks.
Output shape: identical to `build_entries()` — `{url, lastmod, publication_date, title, section}`.

## Stage A first run — false DISABLED at click 127

First bounded run (cap=400) stopped at click 127 with `button DISABLED` and oldest=2026-03-10
(~3 months back). Checkpoint had 2031 URLs, 24 live-blog URLs filtered, 2007 entries output.

**This was a false stop.** An earlier depth probe ran 150 clicks → 2414 URLs, oldest 2026-01-23
(~5 months back), button still ACTIVE. Same feed, same day. If 2026-03-10 were a genuine floor,
the depth probe could not have gone deeper.

**Investigation:** targeted pydoll test confirmed transient-disabled exists (250ms window,
seen at t=0.28s → active at t=0.53s, 1 of 5 clicks), but that window is far shorter than
the ~4.2s click cycle. A transient from click N cannot bleed into click N+1's pre-check
(4.2s later). The DISABLED at click 127 was a one-time race anomaly: the delayed-cursor-exhaustion
mechanism (React disabling button after last-cursor API response) fired during the
click 126 cycle, and the pre-check at click 127 caught the persistent-looking state before
the button could be re-evaluated. Root cause not fully deterministic — single anomalous timing.

## Fix — DISABLED retry tolerance

Added `DISABLED_RETRY_MAX = 3`, `DISABLED_RETRY_WAIT = 2.0s`. When pre-click check reads
`disabled=True`: wait 2s, scroll-to-bottom nudge, re-check. Repeat up to 3 times. Only stop
if still disabled after all retries (reason: `button DISABLED (persistent after 3 retries)`).
Otherwise recover and continue. Identical concept to plateau tolerance (tolerate transient
before concluding terminal).

## Validation re-run (cap=160)

Re-run with 160-click cap after fix:

| Metric | Value |
|--------|-------|
| Clicks done | 160 |
| Distinct URLs | 2 575 (2 551 after live-blog filter) |
| Oldest date reached | **2026-01-23** |
| Stop reason | `stage-A cap (160 clicks)` |
| Disabled-retry recoveries | **0** |
| Wall-clock | 10m 3s |

No DISABLED seen at all — not at click 127, not anywhere. Zero retry recoveries. The fix
prevents false stops structurally. Oldest date (2026-01-23) exactly matches the earlier depth probe,
confirming consistency.

**Button still active at click 160** — feed floor not yet reached. Depth is deeper than 5 months.

## DOM-growth measurement (the next blocker)

Per-click timing over 160 clicks:

| Metric | Value |
|--------|-------|
| First-10 avg | 2.55s |
| Last-10 avg | 5.78s |
| Trend | **+3.23s** |

The `timeLabel` DOM walk in `_JS_EXTRACT` (up to 10 parentElement traversals + querySelectorAll
per link) causes O(n) slowdown per click as DOM grows. At ~5 000 total clicks (Stage B estimate),
extrapolation gives ~40s/click at depth — unacceptable for a multi-hour run.

**Required before full run:** drop `timeLabel` from `_JS_EXTRACT` (unused by `build_entries`,
which derives date from URL path) + switch to delta extraction (only new URLs per click, not full
re-scan). Stage B projection at current pace (linear, uncorrected): ~5 190 clicks, ~5h 21m.
With delta extraction, the per-click time should stabilize regardless of DOM depth.

## Open

- Feed floor unknown — button active at click 160 / 2026-01-23 (~5 months back). Stage B will
  determine actual depth; may reach back to CoinDesk founding (~2013) or stop at a rolling window.
- Perf fix (timeLabel-drop + delta extraction) is the prerequisite for Stage B — not yet implemented.
  Must be a separate isolated change before the uncapped run.
