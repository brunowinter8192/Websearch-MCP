# Five-URL sustained-load live check confirms the phantom signal; AXMain instrument removed from the dev harness (2026-08-27)

Continues the `camoufox_lane` area, closing the gap the 2026-08-26 entry left open: "all five runs
hit `example.com`, a fast static page, one launch at a time... nothing here rules out a steal under
[sustained load]" and "a harder test against multiple real URLs in sequence should precede the
removal, because the workload that produced the original complaint has not been reproduced." That
harder test ran on 2026-08-27, against code that already had the watchdog removed (see
`process-docs/camoufox_lane/2026-08-27_watchdog_removal_and_multi_url_probe.md`, milestone 1 of this
same multi-step effort). This entry records that test's result and the consequence executed on the
strength of it: the dev-harness AXMain instrument itself is now removed too.

## The sustained-load result

`dev/lane_choice/03_live_focus_probe.py`, extended with multi-URL support for exactly this test, ran
against 5 real URLs sequentially — one fresh Camoufox per URL, back-to-back, no watchdog anywhere in
the code — reproducing the original complaint's own workload shape for the first time (full sample
series: `dev/lane_choice/md/03_live_focus_probe_report_20260827T132824Z.md`):

| Metric | Value |
|---|---|
| URLs | 5, sequential, one fresh Camoufox each |
| Wall time | ~50s sustained load |
| Human verdict | ZERO perceived focus loss, at the keyboard throughout |
| Instrument 1 (frontmost) | 0/81 deviations |
| Instrument 2 (AXMain key-window) | 72/81 deviations, runs up to 12.37s continuous |

This is the decisive version of the same gap the 2026-08-26 entry's single-URL `example.com` runs
already showed (5-6 deviations, ~1.9s span) — here AXMain fires on nearly 9 of every 10 samples, for
runs over six times as long, with NO reclaim mechanism reacting to any of it, and the human still
lost no focus at all. Hypothesis A from the 2026-08-26 entry (the watchdog was winning too fast to
perceive) is now excluded outright: there is no watchdog in this code at all, and the result is the
same shape as the watchdog-enabled runs before it. Hypothesis B (AXMain on this LSUIElement accessory
process is a phantom signal, structurally decoupled from real focus) is confirmed under the
sustained-load, multi-URL workload the original complaint actually described, not just on a single
fast static page.

## Consequence executed: the AXMain instrument removed from `dev/lane_choice/`

With the signal proven uninformative under the workload that motivated it, the instrument itself
(not just the in-process watchdog that reacted to it, removed in milestone 1) was removed from both
harness scripts:

- `dev/lane_choice/02_focus_poll_smoke.py`: `get_key_window_owner`, `poll_key_window_loop`,
  `resolve_camoufox_app_name` (dead once nothing called it), the instrument-2 thread wiring, and its
  report section.
- `dev/lane_choice/03_live_focus_probe.py`: the same imports/thread/verdict-field/report-section
  removal, plus `resolve_target_app_name`/`_resolve_chromium_app_name` (existed solely to resolve
  instrument 2's poll target — dead once instrument 2 was gone), and the now-unused `asyncio`/
  `patchright.async_api` imports that only served that resolution.

Instrument 1 (frontmost-app poll) and the per-URL launch-span slicing added for this same test
(`run_urls_in_sequence`/`compute_per_url_verdicts`/`_samples_in_window`) are untouched — both remain
the harness's only focus-steal check going forward. No CLI/env-var surface to re-enable or disable
any part of this was added, matching the existing `dev/lane_choice/DOCS.md` Gotcha against exactly
that kind of permanent surface for a settled question.

## Verification boundary

- Live-check evidence itself: a real, human-judged, sustained-load run — the strongest verification
  level available for a UI-perception question, already executed before this entry (not repeated
  here).
- Instrument removal: `grep -rn "AXMain\|key_window" dev/lane_choice/` (`.py` files) returns nothing;
  full `dev/tests/` suite (250 tests, no dedicated test file exists for these two standalone dev
  scripts) still green, confirming no other file in the repo imported the removed symbols; `--help`
  on both scripts and a pure-function check of the remaining single-instrument verdict path
  (`compute_verdict`/`compute_per_url_verdicts` against a synthetic sample series) both passed
  without launching a real browser.
- NOT re-verified here: whether removing the instrument itself (as opposed to just the watchdog that
  reacted to it) changes anything about a future live run — it should not, since the instrument was
  read-only, but no live run was executed against the now-instrument-free harness as part of this
  step.
