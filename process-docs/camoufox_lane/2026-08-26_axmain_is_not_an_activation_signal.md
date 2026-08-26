# AXMain is not an activation signal — live human verification overturns the 2026-08-25 reading (2026-08-26)

Continues the `camoufox_lane` area. The 2026-08-25 two-layer focus-steal entry closed two gaps
(`ignore_default_args=["-foreground"]`, an in-process AXMain watchdog) and left a residual it
described as a real window-creation-time steal bounded to a ~1.45s flicker. This entry records
five live runs with a human at the keyboard that contradict that reading, plus the Gecko source
mechanism and the external-configuration search that framed them. The measurements from 2026-08-25
are not disputed; their interpretation is. The probe harness used here lives in
`process-docs/lane_choice/`.

## The live result: AXMain fires, the human notices nothing

Five consecutive runs of the ad-hoc Camoufox lane against `https://example.com`, each with the
human switched into another application and typing throughout, each judged by that human live:

| Runs | Watchdog | AXMain deviations | First deviation | Observed deviation span | Human verdict |
|---|---|---|---|---|---|
| 3 | enabled | 5-6 per run | t≈4.84-5.08s | ~1.9s | no focus lost |
| 2 | disabled | 6 per run | t≈5.07-5.08s | ~1.9s | no focus lost |

The watchdog was disabled for the last two runs by a single-line throwaway edit on a never-merged
branch, reverted in the same session. Its presence or absence made no difference to the recorded
signal at all: with the watchdog live the deviation offsets started at 5.06/5.07/5.08s, with it
disabled at 5.07/5.08s, and the per-sample series were otherwise indistinguishable.

Two readings were open before these runs. Hypothesis A: the watchdog is genuinely winning, polling
at 0.25s against a probe sampling only every ~1.1s, so it reclaims focus before anyone perceives
it. Hypothesis B: AXMain on a named process does not imply the app was activated, so the signal is
a phantom. The watchdog-disabled runs decide it — under A, removing the reclaim mechanism would
have produced a visibly worse signal and a human-perceptible steal; neither happened.

The mechanism that makes B coherent: `_ensure_no_focus_steal` sets `LSUIElement=true`, which makes
Camoufox an accessory app that is never activated. A window of such an app can still be that app's
own main window, which is exactly what `AXMain of front window` reports. The 2026-08-25 entry read
the frontmost-app instrument's permanent zero as blindness and AXMain as the truth; the opposite is
the better-supported reading — frontmost-app was correct, and AXMain was measuring something that
carries no consequence for the user.

Scope limit, stated plainly: all five runs hit `example.com`, a fast static page, one launch at a
time. The original complaint arose under sustained load, one fresh Camoufox per scraped URL across
a 106-URL backfill. Nothing here rules out a steal under that workload.

## Gecko: what actually raises a window, read from source

`widget/cocoa/nsCocoaWindow.mm` (fetched via `gh-cli download_files` into `/tmp` and grepped
locally — GitHub's code-search index is absent for `mozilla/gecko-dev`, see the `gh-cli` project's
own `repo_exploration` area):

- `nsCocoaWindow::Show(true)` ends in `[mWindow makeKeyAndOrderFront:nil]` for a normal top-level
  window. That call is the raise-and-take-focus path, and it fires at window show, which matches
  the measured t≈5s offset rather than process start.
- Immediately beside it sits a non-activating branch: `if (mAlwaysOnTop || mIsAlert) [mWindow
  orderFront:nil]`, with the source comment "We don't want alwaysontop / alert windows to pull
  focus when they're opened". A non-activating show path exists in Gecko; normal browser windows
  simply do not take it.
- `nsCocoaWindow::Resize` → `DoResize` early-returns unless position or size actually change, and
  otherwise only calls `[mWindow setFrame:display:]`, which neither raises nor makes key. An
  earlier hypothesis blamed Camoufox's `browser-init.patch`, which injects an unconditional
  `window.resizeTo(1280, 1040)` into the browser chrome. That hypothesis is dead: resizing cannot
  raise a window.

## External configuration: a negative result worth recording

Neither a Firefox command-line argument nor a documented preference can suppress the activation.
The full Mozilla command-line reference and the mozillazine about:config reference were captured
into `websearch-reference` (10 and 142 chunks) and searched. The only activation-related argument
is `-foreground` ("Make this instance the active application"), already removed. There is no
window-position argument, so the offscreen-placement idea recorded in
`process-docs/engine_expansion/` cannot be reached from the CLI at all, and there is no background
or hide argument — no Firefox analog of macOS `open -g`. On the preference side,
`dom.disable_window_flip` governs only JavaScript `focus()` calls on windows and
`browser.tabs.loadDivertedInBackground` governs tabs, with its own note that the browser still
comes to the front. Caveat: the mozillazine page is Firefox-1-to-3 era, and the modern
authoritative list is `modules/libpref/init/StaticPrefList.yaml`, not consulted here.

Upstream offers nothing either. Playwright issue #4822 was closed with "I don't think we can do
anything about it (focusing)", #8301 was answered by a maintainer with "not a trivial fix for us,
use headless or Xvfb", PR #41282 (`createPagesInBackground`) was closed unmerged, and #41306 is
Chromium-only and labelled P3-collecting-feedback. That same #41306 states headed Firefox no
longer steals focus on current builds once `-foreground` is dropped — consistent with what the
live runs show.

Reddit was searched across four distinct formulations (browser focus steal on macOS, LSUIElement
background apps, Camoufox specifically, headful browsers in the background) over r/webscraping,
r/Python, r/mac, r/swift, r/iOSProgramming and r/macapps. It returned end-user threads about
Finder and Dock only, and nothing about whether an accessory app can be hidden and keep rendering.
Recorded so the next session does not repeat the search.

## Consequences, none of them executed here

- `_key_window_steal_watchdog` in `src/scraper/camoufox_scrape.py` has no measurable effect and
  costs several `osascript` subprocesses every 0.25s for the whole acquisition span. Removal is the
  indicated next step, together with the AXMain instrument in `dev/lane_choice/`.
- The upstream report `daijro/camoufox#739` describes this residual as a real steal and is, on this
  evidence, a false report that should be corrected.
- A harder test against multiple real URLs in sequence should precede the removal, because the
  workload that produced the original complaint has not been reproduced.
- Camoufox issues #148 and #418 report the browser freezing or throttling when its window is
  occluded or backgrounded, with `widget.windows.window_occlusion_tracking.enabled=false` offered
  as a workaround. Any future attempt to hide the window rather than let it show must account for
  that.
