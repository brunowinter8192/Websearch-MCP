# Headed-launch feasibility for the ad-hoc chromium (patchright) scrape lane (2026-08-22)

Milestone 1 of 2 toward switching `src/scraper/scrape_url.py`'s `try_scrape` from
`headless=True`/`UndetectedAdapter` to a headed-backgrounded default — this area's prior entries
covered the pydoll-driven DOM search engines (`src/search/browser.py`); this is a different lane
(patchright, via crawl4ai's `use_undetected` switch) and a different downstream consumer, joined to
this area because the underlying questions (executable identity, backgrounding-flag defaults,
no-focus-steal viability) are the same investigative axis applied to a new stack. Draws on this
area's own flag-measurement precedent AND `process-docs/camoufox_lane/`'s `LSUIElement` mechanism
(a second area — the reason this stayed in `browser_posture` rather than spinning up a third: no
single reference area is the sole foundation). Probe: `dev/browser_posture/04_headed_chromium_probe.py`,
report in `dev/browser_posture/md/`.

## Executable resolution: confirmed via the real launched process, not registry metadata

Through `try_scrape`'s exact `BrowserConfig`+`UndetectedAdapter`+`AsyncPlaywrightCrawlerStrategy`
shape, `psutil` on the real launched PID: `headless=True` runs `chrome-headless-shell` under
`chromium_headless_shell-1228`; `headless=False` runs `Google Chrome for Testing.app` under
`chromium-1228`. Both hypotheses confirmed, both launches succeeded with no error.

## Backgrounding flags: 2 of 3 from crawl4ai, 1 driver-injected

Read `crawl4ai==0.9.2`'s `browser_manager.py` directly: `try_scrape`'s `BrowserConfig` (no
`cdp_url`/`use_managed_browser`/`use_persistent_context`) takes the plain
`playwright.chromium.launch()` path, whose `_build_browser_args()` unconditionally includes
`--disable-renderer-backgrounding` and `--disable-background-timer-throttling`, but NOT
`--disable-backgrounding-occluded-windows` (only added when `config.light_mode=True`, which
`try_scrape` never sets). The real launched cmdline (both headless and headed) showed all three
flags present — the third is patchright's own internal driver default, not crawl4ai's doing. This
matters for a future Milestone 2: no code change is needed to get any of the three flags; they're
already there regardless of which lever adds the headed default.

## LSUIElement: NOT VIABLE on this bundle — differs from the Camoufox precedent

Set `LSUIElement=true` on the resolved chromium-1228 `Google Chrome for Testing.app` bundle
(hard-verified the resolved path contained `chromium-1228` before writing; chromium-1223, Playwright's
own separate revision, was never touched). Launch reliably CRASHED: `TargetClosedError`, browser log
`icudtl.dat not found in bundle` / `Invalid file descriptor to ICU data received`, SIGTRAP. Reproduced
3x across this session (the tracked probe run plus two manual repros during investigation). Isolated
the cause from the plist FILE FORMAT: a control launch against the identical bundle in XML format
with the key ABSENT succeeded — the crash tracks the `LSUIElement` key specifically, not binary-vs-XML
encoding. This differs from the `process-docs/camoufox_lane/` precedent,
where the same mechanism worked cleanly on `Camoufox.app`. Root cause not chased further (out of
scope for a Milestone 1 probe) — plausibly this bundle's ICU-data resource lookup depends on
`NSApplicationActivationPolicy`/regular-app startup sequencing that `LSUIElement` changes.
**Verdict: a future Milestone 2 needs a DIFFERENT no-focus-steal lever for this lane** — `LSUIElement`
is not a transferable pattern across different Chromium-family bundles.

For contrast (plist untouched), a headed launch DID steal focus: 8/10 focus-poll samples (80%,
per the tracked probe report) showed `Google Chrome for Testing` frontmost during a 3s-dwell run — confirming the no-focus-steal
problem is real for this lane too, same as the pydoll and Camoufox lanes before it; only the fix
mechanism doesn't transfer.

## Plist mutation hygiene: two bugs caught and fixed on the same bundle, mid-session

**Bug 1 — format loss on revert.** First implementation reverted `LSUIElement` via a `plistlib.load`
→ mutate → `plistlib.dump` round-trip. `plistlib.dump()` defaults to XML; the bundle's original
`Info.plist` was binary (`bplist00`). The revert was content-correct (key removed) but silently left
the file in XML format — a real, persistent side effect on a real, machine-shared bundle that a
purely content-level "is LSUIElement absent?" check would never catch. Fixed: raw-bytes backup
(`plist_path.read_bytes()`) taken before any write, restored via `write_bytes()` on the SAME bytes,
byte-exact — not a re-serialization. Verified the repair worked by converting the corrupted state
back to binary via `plutil -convert binary1` and confirming a subsequent launch still succeeded, then
built the byte-exact fix into the script itself and re-ran clean.

**Bug 2 — orphaned processes the script's own teardown didn't catch.** First run reported 0 orphans
immediately after exit, but manual re-checks minutes later repeatedly found a FRESH `Google Chrome
for Testing` main process alive (new PID, not a slow-dying old one). Traced to macOS itself: Run C's
crash makes `launchd` register a per-app supervision job
(`application.com.google.chrome.for.testing.<ids>`, visible via `launchctl list`) that auto-relaunches
the full browser 10-20s after process exit — a mechanism entirely outside `AsyncWebCrawler`/
Playwright's own context-manager teardown (Run A/B, which never crash, left 0 orphans with no
launchd job involved at all). A plain `psutil`/`pgrep` process kill cannot stop this; only
`launchctl remove <label>` does. Fixed: `kill_survivors()` now removes any matching launchd job every
sweep round in addition to killing processes (multi-round, 1.5s settle between rounds). Verified this
is a one-shot-per-crash effect, not a repeating loop, via a 100s manual monitoring window after the
final tracked run (10 checks x 10s): clean at t+10s, one delayed respawn found and cleaned at t+20s,
clean for the remaining 8 consecutive checks through t+100s. The in-script sweep alone is NOT proven
sufficient — documented as an explicit caveat in both the report and `dev/browser_posture/DOCS.md`'s
gotchas: verify manually ~20s after running this probe rather than trusting its own "0 orphans" line.

## What remains open

Milestone 2 (the actual `src/scraper/scrape_url.py` production change) needs a different no-focus-steal
lever than `LSUIElement` for this lane — not identified in this milestone, out of scope for a probe-only
session. The backgrounding-flags finding means Milestone 2 likely needs no flag changes at all (already
present via crawl4ai + patchright defaults); only the `headless=True` → headed switch itself and
whatever replaces `LSUIElement` are the actual open implementation questions.
