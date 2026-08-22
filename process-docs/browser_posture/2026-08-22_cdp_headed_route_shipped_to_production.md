# cdp_url headed-backgrounded route shipped to production (2026-08-22)

Milestone 2, closing out the arc this area's two same-day entries opened: `LSUIElement` killed
(crashes the chromium-1228 bundle's launch), the `cdp_url` route proven end-to-end (0% focus steal,
working config shape, clean teardown). This entry is the production change itself —
`src/scraper/scrape_url.py`'s `try_scrape` now defaults to the cdp-headed-backgrounded route,
`WEBSEARCH_HEADLESS` forces the old direct headless-shell launch. Draws on this area's own probe
findings as its foundation; cross-references `process-docs/time_budget/`'s R-rules and
`process-docs/camoufox_lane/`'s 2026-08-11 budget-rebooking entries for the budget-derivation
methodology specifically (a reused methodology, not this milestone's foundation — the reason this
stayed in `browser_posture` rather than becoming a new area).

## Flag parity: the milestone brief's premise corrected before implementing

The brief asked for "full parity" with patchright's RPC-launched headed cmdline (probe 05's 34-flag
delta), framed as a sourcing-mechanism choice (runtime derivation vs. a pinned list + rot-guard
test). Traced `ManagedBrowser.start()` (crawl4ai's own "launch Chrome as a subprocess, connect over
CDP" mechanism) before implementing: it launches via a raw `subprocess.Popen`, never through
patchright/playwright's `browserType.launch()` RPC. The 34-flag delta comes from patchright's
internal Node driver constructing an RPC call specifically — a mechanism no raw-subprocess launcher
can ever trigger, crawl4ai's own `ManagedBrowser` included. "Full parity" with the literal RPC
cmdline is not achievable by any sourcing mechanism, not a maintenance problem to guard against.

What IS achievable, fully driftproof, zero pinning: `ManagedBrowser.build_browser_flags(config)` —
a `@staticmethod`, called LIVE with a throwaway `BrowserConfig(enable_stealth=True)`, so it can
never drift from whatever crawl4ai version is installed (no copy to go stale). One deliberate 3-flag
deviation even within this reachable surface, confirmed and kept: `build_browser_flags()` gates
`--disable-gpu`/`--disable-gpu-compositing`/`--disable-software-rasterizer` behind `not
enable_stealth` (its own comment: keep WebGL working via SwiftShader under stealth); the OLDER
direct-launch path's near-duplicate sibling function (`_build_browser_args()`) includes those three
unconditionally, ignoring `enable_stealth` — an existing inconsistency in installed crawl4ai 0.9.2,
confirmed by reading both functions side by side, not replicated here. Full parity would have meant
disabling GPU under a config whose entire point is stealth — kept off instead. Per Opus's explicit
requirement, added a loud-failure guard (`test_build_browser_flags_symbol_resolves_and_is_callable`)
that resolves the symbol, checks its signature, and makes a real call — a crawl4ai upgrade that
renames/removes/reshapes it turns this test red, not a silent posture change.

## Bundle-path resolution: the same driftproof principle, one level deeper

`crawl4ai.utils.get_chromium_path()` is NOT usable for resolving the self-launch target — it
unconditionally imports `playwright.async_api`, not patchright, so it resolves Playwright's OWN
separate chromium revision (probe 04's finding: a genuinely different directory from patchright's).
Confirmed empirically instead: `patchright.async_api`'s `BrowserType.executable_path` property
resolves patchright's real, currently-installed bundle dynamically — measured ~0.15-0.25s across 3
calls this session. Production resolves this EVERY call (no caching, no hardcoded revision string
like probes 04/05's "chromium-1228") — a future patchright upgrade that moves to a different
revision directory is followed automatically rather than silently broken, consistent with this
module's existing no-shared-state architecture.

## Budget re-derivation: the brief's "replaces the launch phase" framing was wrong

Verified via `patchright/_impl/_browser_type.py` before booking any number: `connect_over_cdp`
resolves its own timeout via `"connectOverCDP", TimeoutSettings.launch_timeout, params` — the
IDENTICAL `DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS=180000` fallback that governed the old
`launch()`-based path (established in this project's 2026-08-11 camoufox-lane entries), since
crawl4ai passes no explicit timeout to `connect_over_cdp` either. The 180s ceiling does not go away
on the cdp route — it moves from `launch()` to `connect_over_cdp()`, with two NEW summands added IN
FRONT of it, not instead of it: 1.0s (bundle-path resolution, measured + margin, not independently
`wait_for`'d — same treatment as this project's original cold-start summand) + 10.0s
(`DevToolsActivePort` wait, this module's own bounded loop) + 15.5s (crawl4ai's own
`_verify_cdp_ready`: 5 attempts × 2s `aiohttp.ClientTimeout` + backoff sum
`0.5×Σ(1.4ⁿ, n=0..4)=5.4728`, precisely re-derived from source, not estimated) + 180.0s
(`connect_over_cdp` fallback) + 30.0s (nav) + 5.0s (render wait) + 1.3s (consent) + 5.0s (date) =
**247.8s** — UP from 221.3s, not down, the opposite of what "replaces the launch phase" implied.
Reported this correction to Opus before implementing rather than silently booking the brief's
assumed lower figure; confirmed and accepted as the honest R9 answer. The forced-headless escape
hatch keeps `TOTAL_SCRAPE_BUDGET_HEADLESS_S=221.3` exactly as before (that whole path is unchanged),
requiring two named constants rather than one shared figure.

## Config stamp: `launch_mode` replaces `headless` entirely, not just on the new path

`browser_config.headless` is dead on the cdp path (never read inside crawl4ai's `cdp_url` branch of
`browser_manager.py`'s `start()`, confirmed by source during the milestone-1b probe). Rather than
stamping `headless` only when meaningful (asymmetric, easy to misread), `extract_config_stamp`
dropped the boolean field entirely in favor of one `launch_mode` string
(`"cdp_headed_backgrounded"` | `"headless_direct_forced"`) present and truthful on both paths — a
stamp-shape change, breaking `config_hash` grouping across the boundary (same accepted trade-off as
the 2026-08-05 shape change when `max_content_length` was dropped).

## A real bug found only by live verification, not by any mock

First live `cli.py scrape_url` run: correct content, HTTP 200, 0/24 focus-poll samples on Chrome —
but a real, non-empty leftover profile directory under the OS temp dir survived teardown. Root
cause: `_kill_by_profile`'s first implementation was a plain `pkill`, which returns as soon as the
signal is SENT, not once Chrome actually exits — racing against the immediately-following
`shutil.rmtree`. No mock-based test could have caught this (it's a real-process-timing race, not a
logic error); only a live run surfaced it. Fixed with `psutil`: terminate → `wait_procs` (bounded,
3s) → force-kill any stragglers, all BEFORE the caller's `rmtree` runs. Re-ran live: 0/23
focus-poll samples, confirmed clean `pgrep`/`launchctl`/temp-dir state. `psutil` added to
`requirements.txt` as an explicit direct dependency (was previously only pulled in transitively via
crawl4ai's own `browser_manager.py`).

## Verification

Full suite: 220 passed / 0 failed, both before and after this change — the milestone brief's stated
baseline ("9 failed") was stale, already fixed by an earlier merged session; zero failures either
way satisfies "no new failures." `tests/test_scrape_url.py` grew from ~30 to 55 tests: existing
`AsyncWebCrawler`-mocking tests updated to also mock the new self-launch/port-wait/teardown seam
(`_patch_cdp_launch_mechanics`) so they keep exercising the REAL default path rather than being
silently redirected to the escape hatch; new coverage for launch-mode dispatch, the `WEBSEARCH_HEADLESS`
falsy-value matrix (12 cases, mirroring `src/search/browser.py`'s own), teardown-fires-on-every-exit-path
(exception AND budget-timeout), `_wait_for_devtools_port`'s real bounded-loop behavior (tmp_path,
unmocked), and the flag-parity guard.

Two real end-to-end `cli.py scrape_url https://example.com` runs (default path): HTTP 200, real
content, 9.2-9.5s wall time, 0/23 and 0/24 Chrome-frontmost focus-poll samples, clean teardown after
the `_kill_by_profile` fix. One real `WEBSEARCH_HEADLESS=1` run: HTTP 200, `launch_mode:
"headless_direct_forced"`, `total_budget_s: 221.3`. Fresh `scrape_log.jsonl` records inspected
directly for both — all pre-existing fields intact, `launch_mode`/`total_budget_s` truthful, no
stale `headless` field.

## What remains open

The 34-flag gap between this route's self-launch and patchright's RPC-launched cmdline is now
understood as structural (see above) rather than an open measurement — no further work expected
there short of a fundamentally different launch mechanism. Not otherwise revisited: whether the
extra ~26.5s the cdp route's worst-case budget costs relative to the old figure ever matters in
practice (real observed run time is ~9s, far under either budget) — the scrape log's own
`total_budget_s`/`launch_mode` stamp exists precisely so this stays comparable over time if it ever
does.
