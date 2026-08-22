# cdp_url route for the ad-hoc chromium lane's headed switch (2026-08-22)

Milestone 1b, continuing this area's `2026-08-22_headed_chromium_ad_hoc_lane_probe.md` entry —
that milestone killed `LSUIElement` (crashes the chromium-1228 bundle). External research (digested
into the milestone prompt, not searched independently this session) established: Playwright/patchright
have no built-in no-focus-steal option for headed Chromium (playwright#4822 closed unfixed, #41282
closed unmerged); an occluded window throttles unless `--disable-backgrounding-occluded-windows`
(already on our cmdline per the prior milestone's finding); creating a window activates the Chrome
app even with `focused: false` (playwright#42343); the documented field workaround (playwright#35836)
is self-launching Chrome with `--remote-debugging-port` + a separate `--user-data-dir`, then
`connect_over_cdp`. Probe: `dev/browser_posture/05_cdp_headed_probe.py`, report in
`dev/browser_posture/md/`.

## crawl4ai's cdp_url path, read before writing any code

Traced `browser_manager.py` end to end rather than assuming from the launch-path reading done for
the prior milestone: `BrowserConfig(cdp_url=...)` forces `use_managed_browser=True` at RUNTIME
(`BrowserManager.start()`) regardless of `browser_mode`, so `browser_mode="custom"` is semantic
clarity only, not functionally required — confirmed by reading the `__init__`-time branch (only
fires for `browser_mode=="custom"`) against the runtime branch (fires for any truthy `cdp_url`).
`enable_stealth` validation only rejects `browser_mode="builtin"`, never `"custom"`/`"dedicated"` —
safe with cdp_url. `use_undetected` (patchright vs. plain playwright) is decided purely by
`isinstance(adapter, UndetectedAdapter)`, applied identically to `connect_over_cdp` — patchright's
CDP-level behavior still applies even though we launch the underlying process ourselves; only the
*binary* is "vanilla" (same chromium-1228 bundle patchright itself uses for headed launches, per the
prior milestone). `headless` field is DEAD on this path — never read inside the `cdp_url` branch of
`start()`; headed-ness is entirely a property of how the external process was spawned, not this
config field.

**The load-bearing find**: `get_page()`'s branch for `use_managed_browser=True` + no
`create_isolated_context`/`storage_state`/`target_id` REUSES an existing not-in-use page from
`context.pages` if one exists, calling `context.new_page()` only when none does. This makes whether
the flagged risk (page-creation-over-CDP, playwright#42343) is even exercised fully controllable by
whether the self-launched Chrome already has a blank tab open at connect time. Deliberately launched
with `--no-startup-window` (matching patchright's own captured headed-launch flag from the prior
milestone) specifically to force `context.new_page()` and exercise the real risk, rather than
accidentally dodging it via a leftover default tab — a decision surfaced explicitly before
implementing, not made silently.

## Result: the route itself shows zero focus steal, once correctly isolated

Real config: `BrowserConfig(cdp_url=f"http://127.0.0.1:{port}", browser_mode="custom",
enable_stealth=True, cdp_cleanup_on_close=True)` + `UndetectedAdapter` +
`AsyncPlaywrightCrawlerStrategy`, self-launch via `open -g -n -a <resolved chromium-1228 bundle
path> --args --remote-debugging-port=0 --user-data-dir=<throwaway> --no-startup-window --no-first-run
--no-default-browser-check`, port read from Chromium's own `DevToolsActivePort` file (avoids a
pre-probed-port TOCTOU race). CDP endpoint came up every run; a real `arun()` against a local
throwaway page succeeded (335 bytes — the local page itself trips crawl4ai's own minimal-text
anti-bot heuristic, an artifact of the throwaway page's content, not a route defect).

Stage-labeled continuous frontmost-app poll (0.25s interval), split into the actual route under test
(`self_launch` → `cdp_port_wait` → `cdp_connect_page_navigate` → `teardown`) vs. an internal
`reference_launch` stage (a direct, un-backgrounded patchright launch used ONLY to capture a fresh
real cmdline for the args-delta, never part of the route). Across 3 consecutive post-fix runs: route
Chrome-frontmost count 0/8 samples (0%) every time, including the `cdp_connect_page_navigate` stage
that bundles the flagged page-creation moment. `reference_launch` showed 80% frontmost every time —
expected (zero backgrounding mitigation by design) and NOT evidence against the route; the two must
never be aggregated into one headline figure.

## Two bugs caught and fixed during this probe's own development

**Bug 1 — event-loop starvation hid two stages entirely.** First draft called
`wait_for_devtools_port` (a blocking `time.sleep` loop), `self_launch_chrome`, `kill_by_profile`,
`kill_survivors` directly from the async orchestrator instead of via `asyncio.to_thread`. Their
blocking calls starved the concurrently-running focus-poll coroutine of event-loop turns, so
`cdp_port_wait` and `teardown` silently showed 0 samples — read at first as "these stages are just
fast," actually an instrumentation defect hiding real data. Fixed by wrapping all of them in
`asyncio.to_thread`; the very next run produced real samples for both stages (1 each), still 0%
Chrome-frontmost.

**Bug 2 — aggregating the reference launch into the headline would have misrepresented the result.**
The first working run (before stage separation) reported "18%"/"50%" Chrome-frontmost in different
runs, aggregating `reference_launch`'s expected 80% steal together with the actual route's 0%. A
reader skimming only the headline number would have wrongly concluded the cdp_url route itself
steals focus. Fixed by adding a `stage` label (mutated by the orchestrator as it progresses) to every
focus sample and computing the headline strictly over `ROUTE_STAGES`, with `reference_launch`
reported separately and explicitly marked "NOT part of the route under test."

## cmdline delta: what this route would make us own

Only 4 flags common to both cmdlines (`--user-data-dir`, `--no-startup-window`, `--no-first-run`,
`--no-default-browser-check` — the ones this probe's minimal self-launch args happened to already
match). ~34 flags present on patchright's own direct-launch cmdline are absent from the self-launch:
the full stealth/backgrounding/sandbox/first-run/GPU suite (`--disable-blink-features`,
`--disable-renderer-backgrounding`, `--disable-backgrounding-occluded-windows`, `--no-sandbox`,
`--disable-gpu*`, etc. — full list in the report). Notably `--remote-debugging-pipe` appears only on
patchright's own direct launch (it uses a stdio pipe transport when launching directly, not the HTTP
port at all) — this route's `--remote-debugging-port` is the one flag present only on our side, by
necessity. Measured, not fixed — a future Milestone 2 decides which of these 34 flags to backfill
onto the self-launch.

## Teardown: clean and boring, as expected

0 orphan processes, no launchd supervision job, every run (5 total: 2 before the stage-labeling fix,
3 after) — consistent with "no crash expected on this route," a genuine positive contrast against
the prior milestone's `LSUIElement` finding (which reliably crashed and triggered launchd
auto-relaunch). No plist edits anywhere this session.

## What remains open

The cmdline delta (34 flags) is the concrete next question for a production implementation: which of
patchright's own flags need backfilling onto a self-launch, and whether any matter functionally
(vs. purely as anti-detection signal) for this project's actual scrape targets. Not measured here —
this milestone's deliverable was proving the route works end to end with zero focus steal, not
closing the flag gap.
