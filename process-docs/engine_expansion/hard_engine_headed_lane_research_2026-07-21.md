# Hard-Engine Headed Lane — Research (2026-07-21)

GitHub research pass (gh-cli-search over `github_issues` + pydoll source) into how to run a **headed** browser in the background on the local macOS host, to serve engines whose anti-bot (PoW/CAPTCHA) defeats headless — Brave being the concrete case. Goal: a reusable "hard-engine lane" (isolated headed browser) rather than per-engine special-casing.

## Finding 1 — headed is the industry-standard undetected path (fact)

Not a project quirk. The patchright maintainer (Vinyzu), the most credible source in this space, states in `github_issues` patchright#113: *"It is not possible to be undetected headless without a custom chromium fork, but if you run Linux you can use xvfb."* Patchright officially recommends **headful** as best practice and does not claim undetectable headless (patchright#103). This corroborates the Brave probe result the same day (headless → PoW; a real-Chrome binary passed only headed).

## Finding 2 — Xvfb is Linux-only and IRRELEVANT on the local Mac (fact + correction)

Xvfb (X Virtual FrameBuffer) is a virtual, in-RAM X11 display; it lets a headed browser render with no physical monitor. It exists ONLY to give a headed browser a screen on a **headless server (no monitor)**. On a normal Mac with a real screen it is neither available (macOS uses WindowServer/Quartz, no Xvfb) nor needed — headed simply renders to the real display. Camoufox's own macOS params run `headless: False` (a real visible window) precisely because there is no mac virtual-display trick. Earlier framing that "macOS has no Xvfb" as a *problem* was wrong: on a machine with a screen there is no problem to solve. Xvfb only re-enters if this ever runs on a headless Linux host.

## Finding 3 — focus/window handling on macOS (fact + inference)

- `open -g -a "<App>" --args ...` launches the app in the background without foreground activation (no focus steal). This is the macOS lever for "headed but non-intrusive". (fact)
- Window-minimize / `--window-size=1,1` do NOT reliably hide the window and an "inhumane" window size can itself get flagged by anti-bot (patchright#113). Offscreen `--window-position` is the least-bad hide, unverified whether it stays undetected. (fact / open)
- Screen-lock/display-sleep throttling of a headed browser on macOS is a plausible real-world wrinkle for a background service — unmeasured. (inference)

## Finding 4 — pydoll launch mechanism + the clean integration hook (fact)

`pydoll/browser/managers/browser_process_manager.py`: the default `BrowserProcessManager._default_process_creator` spawns Chrome directly via `subprocess.Popen([binary, "--remote-debugging-port=PORT", *args], ...)`. Crucially it accepts a **`process_creator` callback** — *"Custom function to create browser processes. Must accept command list and return subprocess.Popen object."* So the launch can be overridden WITHOUT patching pydoll: inject a `process_creator` that runs Chrome via `open -g` with the same `--remote-debugging-port` pydoll assigns, then pydoll connects over CDP as normal. This is cleaner than a separate launch-and-`connect_over_cdp` dance (the initial hypothesis, discarded after reading the code).

**Caveat (fact):** `open -g` returns immediately, so the `subprocess.Popen` handed back is the short-lived `open` wrapper, not Chrome. pydoll's `stop_process` (terminate/kill) therefore won't kill Chrome — teardown must be handled externally (pkill on the isolated `--user-data-dir`, already the pattern in the dev probe scripts).

**Inference:** a dedicated isolated `--user-data-dir` is needed anyway (block-isolation from the shared engine profile) AND doubles as the fix for macOS Chrome single-instance behavior (`open` focusing an existing instance instead of applying `--args`).

## Approach chosen for the probe

pydoll with a custom `process_creator` launching the system Google Chrome headed via `open -g`, in an isolated user-data-dir, self-managed Chrome-kill. Measure Brave over a query set: results returned, PoW-triggered?, per-query latency. Gate: ≤5s AND a usable run of consecutive successes (user's relaxed bar: 3-4 clean in a row before a block is sufficient for most cases) → candidate; else DROP.

## Sources

- `github_issues`: Kaliiiiiiiiii-Vinyzu/patchright#113, #103; daijro/camoufox#538 (macOS params).
- `autoscrape-labs/pydoll` — `pydoll/browser/managers/browser_process_manager.py` (`process_creator` hook), `pydoll/browser/chromium/`, `pydoll/browser/options.py`.
