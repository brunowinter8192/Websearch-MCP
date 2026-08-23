# DOCS.md format salvage — browser_posture surface (2026-08-23)

Content cut from `dev/browser_posture/DOCS.md` during the 2026-08-23 doccheck compression
(Purpose one sentence). Snapshot as of the cut date.

**_lib.py** (cut Purpose enumeration): primitives provided — isolated probe profile dirs, the
proven `open -g` headed-backgrounded process_creator, a throwaway local HTTP server (timer-harness
page at `/`, system-color artifact page at `/artifact`), tick-drift/latency-stats helpers, CDP
script injection (`inject_before_navigation`, mirrors the old `apply_fingerprint_patches`),
system-color/screen-window property readers, and a settle-poll helper for heavy client-side pages.

**03_fingerprint_patch_probe.py** (cut Purpose detail): 4 variants (full patch set /
screen-window-overrides-only / getComputedStyle-Proxy-only / none) + 1 headless reference
(artifact test only), each against: the local system-color artifact page
(`ActiveText`/`LinkText`/`VisitedText`, not a resting `<a>`), real screen/window properties,
bot.sannysoft.com, and CreepJS (settle-polled, not fixed-sleep).

**04_headed_chromium_probe.py** (cut Purpose detail): through `try_scrape`'s exact
`BrowserConfig`/`UndetectedAdapter`/`AsyncPlaywrightCrawlerStrategy` shape: (1) which binary runs
under headless=True vs False (read off the real launched process via `psutil`, not registry
metadata), (2) `LSUIElement=true` viability on the resolved chromium-1228 bundle — launch success +
continuous frontmost-app poll, with and without the fix, (3) whether the three Playwright-default
backgrounding flags are on the real cmdline and, per flag, whether crawl4ai's
`_build_browser_args()` put it there or patchright's driver injected it.

**05_cdp_headed_probe.py** (cut Purpose detail): self-launches the chromium-1228 bundle via
`open -g -n -a <bundle> --args --remote-debugging-port=0 --user-data-dir=<throwaway>
--no-startup-window ...` (no pre-existing tab, deliberately forcing crawl4ai's `get_page()` to call
`context.new_page()` — the page-creation-over-CDP moment playwright#42343 flags, confirmed by
reading crawl4ai's page-reuse-vs-create logic first), waits for `DevToolsActivePort`, connects via
`BrowserConfig(cdp_url=..., browser_mode="custom", enable_stealth=True, cdp_cleanup_on_close=True)`
+ `UndetectedAdapter` + `AsyncPlaywrightCrawlerStrategy`, runs a real `arun()`. Stage-labeled
continuous frontmost-app poll across the whole sequence, split "route under test"
(self_launch/cdp_port_wait/cdp_connect_page_navigate/teardown) vs. internal "reference_launch"
(direct un-backgrounded patchright launch, cmdline-baseline only) — never aggregated into one
headline number.
