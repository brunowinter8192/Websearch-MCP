# Watchdog removal executed, multi-URL live probe built for the still-open harder test (2026-08-27)

Continues the `camoufox_lane` area, executing the consequence the 2026-08-26 AXMain entry
(`process-docs/camoufox_lane/`) left unexecuted: `_key_window_steal_watchdog` had no measurable
effect and cost several `osascript` subprocesses every 0.25s for the whole acquisition span. Also
extends the live probe harness (`process-docs/lane_choice/`) for the harder, still-outstanding test
that same entry called for.

## What changed in `src/scraper/camoufox_scrape.py`

Removed entirely: `_key_window_steal_watchdog`, its three osascript primitives
(`_get_frontmost_app`, `_activate_app`, `_is_key_window_owner`), `KEY_WINDOW_POLL_INTERVAL_S`, the
watchdog task creation and `finally`-cancel wiring in `_acquire_camoufox`, and the now-unused
`subprocess` import. 314 LOC → 237 LOC. `_ensure_no_focus_steal`/`_find_app_bundle` (the
`LSUIElement` layer) and `ignore_default_args=["-foreground"]` in `_build_camoufox_kwargs` — the two
mechanisms the 2026-08-26 entry's live runs actually validated — are untouched; confirmed by
inspecting the diff directly (`git diff -- src/scraper/camoufox_scrape.py`), not by re-running the
removed watchdog's own tests. The no-focus-steal launch fix is now two mechanisms, not three.

8 mock-level tests removed from `dev/tests/test_camoufox_scrape.py` alongside the removed code
(`test_get_frontmost_app_parses_osascript_stdout`, `test_activate_app_invokes_osascript_with_app_name`,
both `test_is_key_window_owner_*`, `test_key_window_steal_watchdog_reactivates_last_other_app_on_steal`,
all three `test_acquire_camoufox_*watchdog*` tests) plus the now-unused
`_RaisingAsyncCamoufoxWithYield` helper. 810 LOC → 625 LOC. Full suite: 250 passed (down from the
258 recorded in the 2026-08-25 two-layer entry — 258 minus the 8 removed, no other regressions).

## Order-of-operations note: removal executed before the harder test

The 2026-08-26 entry explicitly flagged: "A harder test against multiple real URLs in sequence
should precede the removal, because the workload that produced the original complaint has not been
reproduced" — all five live human runs to date hit `example.com` once each, never the
sustained-load, one-fresh-Camoufox-per-URL shape of the original complaint. This session's removal
went ahead of that harder test anyway, on explicit two-milestone instruction: milestone 1 (this
entry) removes the watchdog and builds the tool for the harder test; milestone 2 (not yet run) is
the harder test itself, against the now-watchdog-free code. Recorded here so a future reader does
not read the removal as evidence the harder test already happened — it has not.

## `dev/lane_choice/03_live_focus_probe.py`: multi-URL sequence support

Extended to run MULTIPLE URLs in one invocation — the workload shape the harder test needs. Surface:
`--url` is now `action="append"` (repeatable; zero flags still defaults to `[DEFAULT_URL]`, one
`--url` behaves identically to the pre-existing single-URL path). Behavior: ONE countdown up front
(not per URL), then `run_urls_in_sequence` fires one fresh-browser `cli.py scrape_url_camoufox`/
`scrape_url_chromium` subprocess per URL back-to-back, recording each URL's own launch span (elapsed
seconds since the countdown ended, from the same `t0` both instrument threads use). Both instruments
(frontmost-app poll, AXMain key-window poll, reused from `02_focus_poll_smoke.py`) poll continuously
across the WHOLE sequence rather than restarting per URL — a single unbroken sample series, matching
how the instruments already worked for one URL. `compute_per_url_verdicts`/`_samples_in_window`
slice that one series back down per URL afterwards (inclusive-boundary window filter), so both an
overall pooled verdict and a per-URL breakdown print to the terminal and land in the `md/` report.
No watchdog-disable surface was added — `dev/lane_choice/DOCS.md`'s existing Gotcha against exactly
that was left intact (reworded only to drop the now-removed function's name, not to weaken the
prohibition).

## Verification boundary

Pure-function / mock-level only, matching the removed code's own original verification depth:
- 250/250 `dev/tests/` passing (mock-level integration tests: real function calls against faked
  `AsyncCamoufox`/`launch_options`/subprocess boundaries, no real browser, no real `osascript`).
- `03_live_focus_probe.py --help` and a standalone `argparse` probe confirmed `--url` accepts
  repetition (`--url a --url b` → `['...a', '...b']`) and defaults to one URL when omitted — no real
  browser launched for this check, correctly matching the milestone's own dry-demonstration scope.
- `compute_per_url_verdicts`/`_samples_in_window`/`print_url_runs`/`print_per_url_verdicts` checked
  against a synthetic two-URL sample series (hand-constructed, not a real probe run): per-URL
  deviation counts summed consistently with the pooled overall verdict.
- NOT verified: no real Camoufox/Chromium launch, no real live human focus-loss judgment, no real
  `03_live_focus_probe.py --url ... --url ...` end-to-end run. That is precisely milestone 2's job —
  the harder, multi-URL, sustained-load live test the 2026-08-26 entry called for and this session's
  tool now supports but has not yet run.
