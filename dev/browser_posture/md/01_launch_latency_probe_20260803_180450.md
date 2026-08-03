# Launch Latency + Flag Probe — 20260803_180450

Dev-only probe (macOS): headless-direct vs headed-backgrounded Chrome launch latency, one local-page navigation, and background-timer-throttling drift. N=5 per config for launch/nav, N=3 per config for the (more expensive, fixed ~4.8s wait) timer-drift measurement.

## Configurations

| # | Config | headless | backgrounded (`open -g`) | flags |
|---|--------|----------|---------------------------|-------|
| 1 | headless, direct | True | False | (none) |
| 2 | headed, backgrounded, no flags | False | True | (none) |
| 3 | headed, backgrounded, +3 flags | False | True | --disable-background-timer-throttling, --disable-backgrounding-occluded-windows, --disable-renderer-backgrounding |
| 4 | headless, direct, +3 flags (control) | True | False | --disable-background-timer-throttling, --disable-backgrounding-occluded-windows, --disable-renderer-backgrounding |

## Launch + Navigation Latency (ms, min/median/max, N=5)

| Config | start->tab | start->drivable | navigation | nav failures |
|--------|-----------|------------------|------------|--------------|
| 1. headless, direct | 1012/1012/1014 | 1016/1016/1019 | 25/28/33 | 0/5 |
| 2. headed, backgrounded, no flags | 1011/1012/1014 | 1016/1017/1019 | 15/19/26 | 0/5 |
| 3. headed, backgrounded, +3 flags | 1012/1013/1092 | 1017/1019/1102 | 14/16/23 | 0/5 |
| 4. headless, direct, +3 flags (control) | 1012/1012/1015 | 1016/1017/1024 | 26/30/35 | 0/5 |

## Background-Timer-Throttling Drift (expected 40 ticks / ~4000ms nominal, N=3)

| Config | actual ticks (per rep) | mean interval ms | max single gap ms | occlusion confirmed |
|--------|-------------------------|-------------------|--------------------|----------------------|
| 1. headless, direct | [40, 40, 40] | 100.0 | 101 | n/a (headless, no window) |
| 2. headed, backgrounded, no flags | [40, 40, 40] | 100.0 | 102 | NOT CONFIRMED |
| 3. headed, backgrounded, +3 flags | [40, 40, 40] | 100.0 | 102 | NOT CONFIRMED |
| 4. headless, direct, +3 flags (control) | [40, 40, 40] | 100.0 | 102 | n/a (headless, no window) |

**Occlusion NOT confirmed for configs 2/3.** `document.visibilityState` stayed `visible` throughout, despite spawning a same-geometry foregrounded coverer window on top of the automation window. This machine has multiple concurrent real login sessions (`who` showed an active console session plus many tty sessions); the coverer and/or automation window may be placed in a different macOS Space than assumed, so true screen-occlusion could not be verified here without a privacy-invasive full-screen capture (deliberately not repeated after one such capture incidentally showed live, unrelated session content — deleted immediately, not part of this deliverable). **Read the drift numbers above as: 'no throttling observed under `open -g` backgrounding, occlusion state unconfirmed' — NOT as proof the flags make no difference under genuine window occlusion.** This is a real gap against the milestone's own goal of measuring the flags' effect; a follow-up needs either a single-user, single-session machine, or a CDP-level way to force renderer occlusion that does not depend on real window-manager stacking.

## Watchdog Fit

- **1. headless, direct**: worst-case start->drivable = 1019ms — fits the 3.6s default watchdog, fits the 6.0s override ceiling.
- **2. headed, backgrounded, no flags**: worst-case start->drivable = 1019ms — fits the 3.6s default watchdog, fits the 6.0s override ceiling.
- **3. headed, backgrounded, +3 flags**: worst-case start->drivable = 1102ms — fits the 3.6s default watchdog, fits the 6.0s override ceiling.
- **4. headless, direct, +3 flags (control)**: worst-case start->drivable = 1024ms — fits the 3.6s default watchdog, fits the 6.0s override ceiling.

## Excluded: `--disable-new-content-rendering-timeout`

Not measured. It governs blanking of stale COMPOSITOR output after a stalled paint — a purely visual concern. Production never screenshots or reads rendered pixels (every signal is CDP/DOM: `execute_script`, `Runtime.evaluate`), so a blanked compositor frame is invisible to every signal this probe or production consumes. Revisit only if a future milestone adds screenshot-based extraction.

## Teardown

Orphan Chrome processes pinned to any `browser-posture-probe` profile after the run: 0