# dev/browser_posture/

## Role
Milestone probes backing the headed-vs-headless browser posture decision (`src/search/browser.py`
switch from headless to headed-backgrounded). Milestone 1: launch/navigation latency and the
Playwright-default backgrounding-flag effect, plus the everyday parallel-user-Chrome collision case.
Milestone 2: whether `src/search/browser.py`'s existing JS fingerprint patches (written for headless)
still make sense under headed. Does NOT measure block/CAPTCHA rates — see
`process-docs/engine_expansion/` for why that axis was rejected as a same-IP same-day confound.
Backs `process-docs/browser_posture/`.

## Modules

### _lib.py (307 LOC)

**Purpose:** Shared launch/teardown/measurement primitives for all probe scripts — isolated probe
profile dirs, the proven `open -g` headed-backgrounded process_creator, a throwaway local HTTP
server (timer-harness page at `/`, system-color artifact page at `/artifact`), tick-drift/latency-
stats helpers, CDP script injection (`inject_before_navigation`, mirrors `apply_fingerprint_patches`),
system-color/screen-window property readers, and a settle-poll helper for heavy client-side pages.
**Reads:** nothing (pure infra + subprocess/CDP calls it makes itself).
**Writes:** nothing directly — returns data to callers; spawns/kills Chrome processes as a side effect.
**Called by:** `01_launch_latency_probe.py`, `02_parallel_chrome_probe.py`, `03_fingerprint_patch_probe.py`.
**Calls out:** `pydoll` (Chrome, ChromiumOptions, BrowserProcessManager, PageCommands).

---

### 01_launch_latency_probe.py (270 LOC)

**Purpose:** Measures 4 configs (headless-direct / headed-backgrounded-no-flags / headed-backgrounded
+3-flags / headless+3-flags control) x N=5 for start-to-drivable-tab + one-navigation latency, and
x N=3 for background-timer-throttling drift (setInterval(100ms) actual-vs-expected over a local page).
**Reads:** nothing (self-contained; serves its own local HTTP target).
**Writes:** MD report to `md/01_launch_latency_probe_<ts>.md`. Progress to stderr.
**Called by:** CLI only. Run: `./venv/bin/python dev/browser_posture/01_launch_latency_probe.py`.
**Calls out:** `pydoll` (via `_lib`).

---

### 02_parallel_chrome_probe.py (202 LOC)

**Purpose:** Determines what happens when a headed-backgrounded launch (`open -g -n -a "Google
Chrome"`) targets the REAL production shared profile (`src/search/browser.py` SESSION_DIR) while a
Chrome instance is already running — the everyday "user already has Chrome open" case. Simulates
the already-running Chrome via a throwaway profile (never touches the user's real default profile).
**Reads:** nothing.
**Writes:** MD report to `md/02_parallel_chrome_probe_<ts>.md`. Progress to stderr.
**Called by:** CLI only. Run: `./venv/bin/python dev/browser_posture/02_parallel_chrome_probe.py`.
**Calls out:** `pydoll` (via `_lib`), `osascript`/`open`/`pgrep`/`pkill` (macOS process + focus control).

---

### 03_fingerprint_patch_probe.py (439 LOC)

**Purpose:** Per-block KEEP/DROP evidence for `src/search/browser.py`'s `JS_FINGERPRINT_PATCHES`
under headed. 4 variants (full patch set / screen-window-overrides-only / getComputedStyle-Proxy-only
/ none) + 1 headless reference (artifact test only), each against: the local system-color artifact
page (`ActiveText`/`LinkText`/`VisitedText`, not a resting `<a>`), real screen/window properties,
bot.sannysoft.com, and CreepJS (settle-polled, not fixed-sleep).
**Reads:** nothing (self-contained; serves its own local artifact page via `_lib`).
**Writes:** MD report to `md/03_fingerprint_patch_probe_<ts>.md`. Progress to stderr.
**Called by:** CLI only. Run: `./venv/bin/python dev/browser_posture/03_fingerprint_patch_probe.py`.
**Calls out:** `pydoll` (via `_lib`); live HTTP to `bot.sannysoft.com` and
`abrahamjuliot.github.io/creepjs` — these are detection test pages, the intended target of this probe,
not production engines.

---

## Gotchas

- Both scripts open real, visible Chrome windows on macOS (headed configs) — not safe to run on a
  headless CI runner; developed and verified interactively on the target Mac.
- `01`'s timer-drift measurement could NOT confirm real window occlusion in this environment
  (`document.visibilityState` stayed `visible` even with a same-geometry, `-g`-backgrounded coverer
  window on top) — the machine runs multiple concurrent real login sessions, so window-stacking
  assumptions don't hold. The drift numbers in the report are labeled "occlusion unconfirmed"; do not read a "no
  drift" result as proof the three flags make no difference under genuine occlusion.
- Full-screen `screencapture` was used once during development to debug the occlusion gap above and
  incidentally captured live, unrelated session content on this shared machine — deleted immediately,
  not part of either script. Do not add screenshot-based verification to these scripts without a
  window-specific (not full-screen) capture target.
- All probe profile dirs live under `~/.websearch/browser-posture-probe/` — isolated from
  `src/search/browser.py`'s shared `SESSION_DIR`, EXCEPT `02_parallel_chrome_probe.py`, which
  deliberately targets the real `SESSION_DIR` (that's the scenario under test).
- `03`'s CreepJS extraction does NOT look for "Trust Score"/"N lies" text — the live build (checked
  directly, not assumed from memory of another version) renders no such summary at all; every
  "trust"/"lie" substring in the page is a false positive (e.g. "CLIENT" contains "lie"). The real
  signal extracted is the "Headless" section's three percentages plus "confidence: &lt;level&gt;"
  notes. Re-verify this against the live page before reusing the extraction if CreepJS's UI changes.
- `03`'s getComputedStyle artifact test is `color: ActiveText` on a dedicated element, NOT a resting
  `<a>` — a plain link computes to the ordinary link color in every mode and never exercises what the
  patch targets (CSS ActiveText, the link's ACTIVE-state system color).
