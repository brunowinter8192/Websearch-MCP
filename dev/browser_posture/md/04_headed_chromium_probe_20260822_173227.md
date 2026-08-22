# Headed Chromium (patchright) Launch Probe — 20260822_173227

Dev-only probe (macOS). All three launches use `try_scrape`'s exact BrowserConfig/adapter/strategy shape against a local throwaway page (never a third-party site). `crawl4ai==0.9.2`, `patchright==1.61.2`.

## 1. Executable resolution

| Run | headless | launch success | PID | executable |
|-----|----------|-----------------|-----|------------|
| A | True | True | 60275 | `/Users/brunowinter2000/Library/Caches/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-mac-arm64/chrome-headless-shell` |
| B | False | True | 60697 | `/Users/brunowinter2000/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing` |

- Headless hypothesis (`chrome-headless-shell` under `chromium_headless_shell-1228`): CONFIRMED
- Headed hypothesis (`Google Chrome for Testing.app` under `chromium-1228`): CONFIRMED
- Run A error: none
- Run B error: none

## 2. Backgrounding flags

Attribution: **crawl4ai arg list** = present in the installed `browser_manager.py`'s `_build_browser_args()` unconditional output (read directly off the installed package this session). **driver-injected** = present on the real cmdline but NOT in that list — patchright/playwright's own internal default, not crawl4ai's doing.

| Flag | headless (Run A) | headed (Run B) |
|------|-------------------|------------------|
| `--disable-background-timer-throttling` | present — crawl4ai arg list | present — crawl4ai arg list |
| `--disable-backgrounding-occluded-windows` | present — driver-injected (not in crawl4ai's _build_browser_args output) | present — driver-injected (not in crawl4ai's _build_browser_args output) |
| `--disable-renderer-backgrounding` | present — crawl4ai arg list | present — crawl4ai arg list |

## 3. LSUIElement viability

- Bundle: `/Users/brunowinter2000/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app`
- Original `LSUIElement`: `None` (None = key absent, macOS default)
- End state (reverted): `None`, byte-exact restore of original file: True (`Info.plist` written back from a raw-bytes backup taken before any edit, not a plistlib round-trip — `plistlib.dump()` defaults to XML and would have silently converted the bundle's original binary (`bplist00`) plist to XML even on a content-correct revert; caught during this probe, fixed before this run)
- Codesign verify BEFORE edit: rc=1 — /Users/brunowinter2000/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app: code has no resources but signature indicates they must be present (pre-existing on the untouched bundle, not caused by this probe)
- Codesign verify AFTER `LSUIElement=true` edit: rc=1 — /Users/brunowinter2000/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app: code has no resources but signature indicates they must be present

| Run | plist state | launch success | focus samples | chrome frontmost | % chrome frontmost | distinct apps seen |
|-----|-------------|-----------------|----------------|-------------------|----------------------|----------------------|
| B (no fix) | LSUIElement=None | True | 10 | 8 | 80% | ['Google Chrome for Testing', 'firefox'] |
| C (with fix) | LSUIElement=True | False | 1 | 0 | 0% | ['firefox'] |

- Run C error: TargetClosedError: BrowserType.launch: Target page, context or browser has been closed
Browser logs:

<launching> /Users/brunowinter2000/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing --disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-breakpad --no-default-browser-check --disable-dev-shm-usage --disable-edgeupdater --disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate,AutoDeElevate,RenderDocument,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion --enable-features=CDPScreenshotNewSurface --disable-hang-monitor --disable-prompt-on-repost --disable-renderer-backgrounding --force-color-profile=srgb --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --export-tagged-pdf --disable-search-engine-choice-screen --edge-skip-compat-layer-relaunch --disable-infobars --disable-search-engine-choice-screen --disable-sync --disable-blink-features=AutomationControlled --no-sandbox --disable-gpu --disable-gpu-compositing --disable-software-rasterizer --no-sandbox --disable-dev-shm-usage --no-first-run --no-default-browser-check --disable-infobars --window-position=0,0 --ignore-certificate-errors --ignore-certificate-errors-spki-list --disable-blink-features=AutomationControlled --window-position=400,0 --disable-renderer-backgrounding --disable-ipc-flooding-protection --force-color-profile=srgb --mute-audio --disable-background-timer-throttling --disable-features=OptimizationHints,MediaRouter,DialMediaRouteProvider --disable-component-update --disable-domain-reliability --window-size=1080,600 --user-data-dir=/var/folders/t2/_8msw65s0glfkr10g1mp_4g40000gn/T/playwright_chromiumdev_profile-eQYAAh --remote-debugging-pipe --no-startup-window
<launched> pid=61125
[pid=61125][err] [0822/173226.738734:ERROR:base/i18n/icu_util.cc:177] icudtl.dat not found in bundle
[pid=61125][err] [0822/173226.738884:ERROR:base/i18n/icu_util.cc:232] Invalid file descriptor to ICU data received.
Call log:
  - <launching> /Users/brunowinter2000/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing --disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-breakpad --no-default-browser-check --disable-dev-shm-usage --disable-edgeupdater --disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate,AutoDeElevate,RenderDocument,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion --enable-features=CDPScreenshotNewSurface --disable-hang-monitor --disable-prompt-on-repost --disable-renderer-backgrounding --force-color-profile=srgb --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --export-tagged-pdf --disable-search-engine-choice-screen --edge-skip-compat-layer-relaunch --disable-infobars --disable-search-engine-choice-screen --disable-sync --disable-blink-features=AutomationControlled --no-sandbox --disable-gpu --disable-gpu-compositing --disable-software-rasterizer --no-sandbox --disable-dev-shm-usage --no-first-run --no-default-browser-check --disable-infobars --window-position=0,0 --ignore-certificate-errors --ignore-certificate-errors-spki-list --disable-blink-features=AutomationControlled --window-position=400,0 --disable-renderer-backgrounding --disable-ipc-flooding-protection --force-color-profile=srgb --mute-audio --disable-background-timer-throttling --disable-features=OptimizationHints,MediaRouter,DialMediaRouteProvider --disable-component-update --disable-domain-reliability --window-size=1080,600 --user-data-dir=/var/folders/t2/_8msw65s0glfkr10g1mp_4g40000gn/T/playwright_chromiumdev_profile-eQYAAh --remote-debugging-pipe --no-startup-window
  - <launched> pid=61125
  - [pid=61125][err] [0822/173226.738734:ERROR:base/i18n/icu_util.cc:177] icudtl.dat not found in bundle
  - [pid=61125][err] [0822/173226.738884:ERROR:base/i18n/icu_util.cc:232] Invalid file descriptor to ICU data received.
  - [pid=61125] <gracefully close start>
  - [pid=61125] <kill>
  - [pid=61125] <will force kill>
  - [pid=61125] exception while trying to kill process: Error: kill ESRCH
  - [pid=61125] <process did exit: exitCode=null, signal=SIGTRAP>
  - [pid=61125] starting temporary directories cleanup
  - [pid=61125] finished temporary directories cleanup
  - [pid=61125] <gracefully close end>


**Verdict: NOT VIABLE as a direct lever on this bundle.** Reproduced 2x (this run plus one manual repro during investigation): `LSUIElement=true` on the chromium-1228 `Google Chrome for Testing.app` bundle reliably breaks the launch itself — `TargetClosedError`, browser log shows `icudtl.dat not found in bundle` / `Invalid file descriptor to ICU data received`. Isolated from the plist FORMAT (binary vs XML): a control launch against the identical bundle in XML format with the key ABSENT succeeded — the failure tracks the `LSUIElement` key specifically, not the file encoding. Differs from the Camoufox precedent (`process-docs/camoufox_lane/pipe_switch_and_no_focus_steal_2026-08-20.md`), where the same mechanism worked cleanly on `Camoufox.app`. Root cause not investigated further (out of scope for this probe) — plausibly this bundle's ICU-data resource lookup path depends on `NSApplicationActivationPolicy`/regular-app startup sequencing that `LSUIElement` changes. A future milestone needs a DIFFERENT no-focus-steal lever for this lane.

## Teardown

Orphan processes/launchd jobs immediately after this script's own `check_orphans()` call: 0.

**Confirmed root cause (found during this probe's development, NOT fully bounded by the in-script sweep below — verify manually ~20s after this script exits, e.g. `pgrep -fl "ms-playwright/chromium"` + `launchctl list | grep chrome.for.testing`).** Run C's crash (`icudtl.dat not found in bundle`, SIGTRAP) makes macOS itself register a launchd per-app supervision job, `application.com.google.chrome.for.testing.<ids>` (`launchctl list`), which auto-relaunches the FULL browser (new PID: main process + crashpad + GPU/utility helpers) on a delay observed to range ~10-20s after process exit — outside what any bounded in-script sleep can reliably wait out. This is NOT the AsyncWebCrawler/Playwright context-manager's own teardown failing (Run A/B, which never crash, leave 0 orphans with no launchd job involved at all) — it is macOS's own crash-recovery, triggered specifically because Run C's launch crashes. `kill_survivors()` removes any matching launchd job every sweep round (`remove_stray_launchd_jobs()`) in addition to killing processes; `check_orphans()` reports residual launchd jobs too, not just processes. One-shot-per-crash, not a repeating loop.

**This run's actual hand-off state (manual monitoring, 10 checks x 10s = 100s after script exit, since the in-script sweep alone is not proven sufficient — see above):** clean at t+10s; FOUND at t+20s (1 launchd job + 11 processes: main + 2x crashpad_handler + gpu + 2x utility + renderer helpers) — removed manually (`launchctl remove` + `kill`); clean at every check from t+30s through t+100s (8 consecutive checks). Independent final verification after the monitoring window: `pgrep -fl "ms-playwright/chromium"` → no match, `launchctl list | grep chrome.for.testing` → no match, `Info.plist` confirmed `Apple binary property list` format with `LSUIElement` absent (byte-exact original), chromium-1223's `Info.plist` MD5 unchanged throughout this whole probe session.