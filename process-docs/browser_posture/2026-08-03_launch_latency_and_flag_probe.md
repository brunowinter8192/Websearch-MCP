# Launch-latency + flag probe for a headed-background Chrome launch (2026-08-03)

Milestone 1 of 3 toward switching `src/search/browser.py`'s 9 DOM search engines from headless to a
headed-but-backgrounded default (`process-docs/engine_expansion/2026-08-02_headed_vs_headless_external_evidence.md`
covers the WHY of that switch on external evidence). This milestone measures the first of two named
risks: what a headed background launch costs in time, and what happens with the flags Playwright sets
by default on every Chromium it launches. Probe: `dev/browser_posture/01_launch_latency_probe.py` +
`02_parallel_chrome_probe.py`, reports in `dev/browser_posture/md/`.

## Why a new area, not a continuation of `engine_expansion`

`engine_expansion`'s prior entries (the pydoll `process_creator` mechanism research, the Brave
headed-lane probe) are a shared foundation used by other engine work too, not this line's private
predecessor — and this milestone is the first of three in its own strand (browser posture: latency,
then two more risk axes still to come), matching the "new area" criterion on that basis alone.

## Launch + navigation latency (N=5 per config)

Four configs, `open -g -n -a "Google Chrome"` for the backgrounded ones (the mechanism proven in
`dev/search_pipeline/27_brave_headed_lane_probe.py`), a throwaway local HTTP page (not a third-party
site) for navigation:

| Config | start->drivable ms (min/median/max) | navigation ms (min/median/max) |
|---|---|---|
| 1. headless, direct (today's shape) | 1016/1016/1019 | 25/28/33 |
| 2. headed, backgrounded, no flags | 1016/1017/1019 | 15/19/26 |
| 3. headed, backgrounded, +3 flags | 1017/1019/1102 | 14/16/23 |
| 4. headless, direct, +3 flags (control) | 1016/1017/1024 | 26/30/35 |

Worst case across all four configs: 1102ms start-to-drivable. Against the watchdog budget
(`ENGINE_WATCHDOG_TIMEOUT = 3.6s`, per-engine overrides up to 6.0s in `src/search/search_web.py`):
**headed-backgrounded startup fits comfortably inside both the 3.6s default and the 6.0s override
ceiling** — roughly a third of the tighter budget, with ~2.5s of headroom even in the worst observed
case. Headed-vs-headless launch cost is NOT the bottleneck this measurement was worried about;
`~1s` of it is Chrome's own cold-start-to-CDP-ready time, present in all four configs equally.
Navigation itself (15-35ms range, local page) is negligible next to launch cost either way.

## Background-timer-throttling drift: measured, but the occlusion condition could not be confirmed

The three Playwright-default flags (`--disable-background-timer-throttling`,
`--disable-backgrounding-occluded-windows`, `--disable-renderer-backgrounding`) govern OCCLUDED-window
behavior specifically — a window covered by another window, not merely unfocused. A static
third-party page has nothing running to throttle, so the probe instead served a local page running
`setInterval(100ms)` for 40 ticks (~4s nominal) and compared actual-vs-expected tick count: Chromium's
documented background-page throttling clamps to roughly once per second, so a throttled run would show
~4-5 ticks in that window instead of ~40 — an order-of-magnitude, unambiguous signal when present.

To exercise "occluded" rather than merely "unfocused," a second, identically-positioned Chrome window
(throwaway profile, `-g` backgrounded, no CDP) was spawned on top of the automation window right after
navigation. All four configs showed 40/40 ticks, ~100ms mean interval, no observable drift — but
`document.visibilityState` on the automation tab stayed `"visible"` throughout, even with the coverer
window at matching `--window-position`/`--window-size`. Diagnosed live: this machine runs multiple
concurrent real login sessions (`who` showed an active console session plus many active tty sessions,
one of them a live, unrelated full-screen terminal session at the time of the diagnostic) — window
placement across macOS Spaces on a machine like this cannot be assumed to put the coverer window
actually on top of the automation window. A full-screen `screencapture` taken to debug this
incidentally showed that live, unrelated session's content; deleted immediately, not repeated, not
part of either probe script.

**Reading: no drift was observed under `open -g` backgrounding with occlusion state unconfirmed —
this is NOT evidence that the three flags make no difference under genuine window occlusion.** The
flag-effect question this milestone specifically set out to answer stays open. A follow-up needs
either a single-user/single-session machine for a clean window-stacking test, or a CDP-level way to
force renderer occlusion that does not depend on real window-manager state.

## Deliberately excluded: `--disable-new-content-rendering-timeout`

Considered, not added as a config. It suppresses blanking of stale COMPOSITOR/visual output after a
stalled paint — a purely on-screen concern. Production never screenshots or reads rendered pixels;
every signal it consumes is CDP/DOM (`execute_script`, `Runtime.evaluate`). A blanked compositor frame
is invisible to every signal this probe or production reads. Revisit only if a future milestone adds
screenshot-based extraction.

## Parallel-Chrome collision (the everyday case)

Production uses a SHARED profile (`~/.websearch/browser-session`) for the 9 DOM engines. Tested
whether `open -g -n -a "Google Chrome" --args ... --user-data-dir=<that real shared dir>` reaches a
genuinely new, correctly-argumented instance when a Chrome process is already running (macOS `open`
is known to sometimes address an existing instance and silently drop `--args`). The already-running
Chrome was SIMULATED via a throwaway profile — never the user's real default profile, so no real
session/window was touched. First draft of the simulation spawned it via plain `open -n -a "Google
Chrome"` (no `-g`), which does foreground — an actual focus-stealing defect in the probe itself,
caught and fixed after an initial report wrongly read "no focus steal" without the code guaranteeing
it. Fixed: `spawn_plain_chrome` (`_lib.py`) now always launches via `open -g`, same mechanism as the
production launch — used identically for the simulated user Chrome here and for the timer-drift
occluder window in the latency probe. Re-verified with a continuous frontmost-app poll (0.5s
interval, `osascript`/System Events) running for the full duration of both probe scripts, not just
before/after snapshots: across ~240 samples spanning both runs, frontmost was only ever `CotEditor`
or `ghostty` (the apps in real use on this machine at the time) — `Google Chrome` never appeared once.

Result: the backgrounded launch against the real shared profile connected over CDP in ~1.0-1.15s and
the tab was immediately drivable, while the simulated already-running instance kept running
undisturbed under its own profile — `-n` plus a distinct `--user-data-dir` reliably forced a separate
process rather than `open` silently addressing the existing one and dropping `--args`. No focus steal
was observed from either spawn, confirmed both by per-step frontmost snapshots in the script's own
report and by the independent continuous poll above. Caveat that still stands: this session runs in
an agent-driven execution context rather than a fully interactive human login — the OS-level
frontmost-app signal is the level of proof reached here; a human visual spot-check remains the
stronger confirmation for the visual/attention-stealing claim specifically. Teardown was clean both
runs: zero processes pinned to either profile dir after each run (`pgrep -f user-data-dir=...`).

Noted for the record, not built on now: macOS `open` also has a `--hide` option (launches the app
hidden rather than merely non-activated) — a possible future lever if `-g` alone ever proves
insufficient, out of scope for this milestone.

## Net read for the headed-default decision

Nothing measured here blocks the switch on latency grounds — headed-backgrounded launch cost is
within budget with wide margin, and the collision risk (silently addressing an existing Chrome
instance, dropping our args) did not materialize against the real production profile path. The open
item is the flag-effect measurement itself, which needs a cleaner environment to actually resolve.
