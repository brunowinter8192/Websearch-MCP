# Camoufox lane: two-layer focus-steal fix (2026-08-25)

Continues the `camoufox_lane` area. The milestone-3 `LSUIElement=true` fix
(`pipe_switch_and_no_focus_steal_2026-08-20.md`) suppresses the OS's PASSIVE default
activation-on-launch policy. This session closes two further gaps confirmed live: an EXPLICIT
launch-time activation call `LSUIElement` cannot override, and a residual window-creation-time
steal `LSUIElement` was never meant to cover at all.

## Layer 1 gap: Playwright's own `-foreground` flag

Playwright's Firefox launcher unconditionally injects `-foreground` whenever `headless=False`
(confirmed by reading the installed playwright driver bundle directly) — an explicit macOS Cocoa
activation call that overrides the passive `LSUIElement` plist patch. External grounding:
playwright#41306 states this is launch-time only, with `ignoreDefaultArgs:['-foreground']` as
Playwright's own documented opt-out; the issue is explicit that no juggler (Firefox) equivalent of
Chromium's `background:true` launch option exists — `ignoreDefaultArgs` is the only lever
available for this browser engine.

Fix: `ignore_default_args=["-foreground"]` added to `_build_camoufox_kwargs`. argv-verified
effective — the flag is confirmed gone from the real spawned process's command line, not just
absent from the intended kwargs dict.

## Layer 2 gap: window-creation-time key-window steal (no upstream fix exists)

Even with both `LSUIElement` and `ignore_default_args` in place, Camoufox can still win true
key-window (AXMain) status — confirmed live: the steal window falls at t=3.6-6.6s into a real
scrape, well after launch, i.e. WINDOW-CREATION-time activation, not launch-time — the Camoufox
analog of the chromium lane's own playwright#42343 gap (`process-docs/browser_posture/`). No
upstream camoufox or Firefox preference exists for this residual; raised upstream as
daijro/camoufox#739. Absent an upstream fix, this session closes it in-process instead, mirroring
the chromium lane's own `_focus_steal_watchdog` pattern (`src/scraper/chromium_scrape.py`) as
closely as the two engines' mechanics allow.

`_key_window_steal_watchdog(app_name)`: an `asyncio.Task` created around the whole acquisition
span (`_acquire_camoufox`), scoped to the REAL resolved Camoufox `.app` name (`_find_app_bundle`'s
own resolution, never hardcoded — matches the chromium lane's own dynamic-resolution precedent).
Every `KEY_WINDOW_POLL_INTERVAL_S=0.25s`, polls whether Camoufox's own front window holds AXMain
via `osascript`/System Events (`tell process "<app_name>" to return value of attribute "AXMain" of
front window` — queried PER-NAMED-PROCESS, not a system-wide `whose` filter, which throws a hard
Accessibility-permission error in this environment); on a hit, re-activates whichever app was
truly frontmost the moment before, tracked dynamically as the loop runs, never hardcoded. Cancelled
(and awaited) in `_acquire_camoufox`'s `finally` — an in-process task, so it cannot outlive a
crashed CLI process and leak a poll loop the way a detached watchdog subprocess could.

This required a SECOND poll instrument in the smoke harness
(`dev/lane_choice/02_focus_poll_smoke.py`): the pre-existing frontmost-app poll is blind to this
class entirely, because Camoufox is LSUIElement (accessory) and never registers as "frontmost" in
the System Events/NSWorkspace sense that instrument reads — confirmed directly: frontmost-app
showed 0 deviations throughout every measurement below, camoufox-only AND unfixed alike, while
AXMain caught the steal both times.

## Measurements

Isolated dev-side measurement (before the harness-wrapper gap below was found): 9/12 sustained
AXMain-True samples with no watchdog, down to 1/3 isolated sub-second flicker with the watchdog —
small-N, treated as directional only.

**The `websearch` PATH-wrapper gap (discovered this session, documented as a Gotcha in
`dev/lane_choice/DOCS.md`):** `01_backfill_pairs.py`'s `WEBSEARCH_CMD="websearch"` resolves via a
fixed shell wrapper pinned to the MAIN repo's `cli.py`, never a worktree's own code. A 2-URL
`02_focus_poll_smoke.py --limit 57` run through this official pipeline (2 chromium + 2 camoufox,
0 frontmost deviations, exit 0) showed AXMain **sustained** True for ~4.84s and ~6.04s continuous
blocks — indistinguishable from pre-fix behavior, because it WAS pre-fix behavior: confirmed by
`grep`ping the main repo's own `camoufox_scrape.py`, which carries neither `ignore_default_args`
nor the watchdog. This run is not evidence about the fix in either direction.

Direct verification instead invoked the worktree's own `venv/bin/python cli.py
scrape_url_chromium/scrape_url_camoufox <url>` for the same 2 real URLs
(`www.rmv.de/.../faq-deutschland-ticket`, `www.bahn.de/.../faq-deutschlandticket`), bypassing the
PATH wrapper entirely. Result: 0 frontmost deviations; 45 AXMain samples, 33 True but broken into
~21 separate runs, MAX single-run duration 1.45s — vs. the unfixed path's two multi-second
continuous blocks. The watchdog visibly toggles True/False rapidly (Camoufox re-grabbing,
watchdog reclaiming) rather than losing the fight outright, bounding the steal to a flicker rather
than eliminating the underlying contest — consistent with the small-N dev-side measurement above,
though "isolated flicker" here tops out at 1.45s rather than strictly sub-second.

## Verification

9 new tests, `dev/tests/test_camoufox_scrape.py` (mock-level, no real launches): `ignore_default_args`
kwarg presence; `_get_frontmost_app`/`_activate_app`/`_is_key_window_owner` (subprocess mocked);
`_key_window_steal_watchdog`'s reactivation logic driven by faked polling primitives inside a real
`asyncio.Task`; `_acquire_camoufox`'s watchdog creation/cancellation on success, on the browser
context raising, and its absence when no `.app` ancestor resolves. Full suite: 258 passed (249
pre-existing + 9 new), no regressions.

Real end-to-end evidence: entry-point level (`cli.py` real subprocess → real Camoufox/Chromium
launches → real macOS AXMain polling) against the worktree's own code, per the direct-invocation
measurement above — NOT via the shared `websearch`/`01_backfill_pairs.py` pipeline, which
structurally cannot reach unmerged worktree code (see Gotcha). Whether the main-repo deployment
(post-merge) reproduces the same 1.45s-max figure is unverified — that depends on the merge itself,
outside this session's scope.
