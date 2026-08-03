# Fingerprint-Patch Consistency Probe — 20260803_183746

Dev-only probe (macOS, headed-backgrounded only): does `src/search/browser.py`'s `JS_FINGERPRINT_PATCHES` (written for headless) still make sense under headed? 4 variants + 1 headless reference (artifact test only). Targets: local artifact page (system colors + screen/window props), bot.sannysoft.com, CreepJS.

## getComputedStyle artifact: does the rgb(255,0,0) ActiveText artifact occur under headed?

Tested on `color: ActiveText` directly (not a resting `<a>`, which computes to the ordinary link color in every mode and never touches what the patch targets).

| Variant | plainLink | activeText | linkText | visitedText |
|---|---|---|---|---|
| 1. full patch set (A+B, today's shape) | rgb(0, 0, 238) | rgb(0, 102, 204) | rgb(0, 0, 238) | rgb(85, 26, 139) |
| 2. without getComputedStyle Proxy (A only) | rgb(0, 0, 238) | rgb(255, 0, 0) | rgb(0, 0, 238) | rgb(85, 26, 139) |
| 3. without screen/window overrides (B only) | rgb(0, 0, 238) | rgb(0, 102, 204) | rgb(0, 0, 238) | rgb(85, 26, 139) |
| 4. no patches (baseline) | rgb(0, 0, 238) | rgb(255, 0, 0) | rgb(0, 0, 238) | rgb(85, 26, 139) |
| headless reference (no patches) | rgb(0, 0, 238) | rgb(255, 0, 0) | rgb(0, 0, 238) | rgb(85, 26, 139) |

**ActiveText under headed, no patches: `rgb(255, 0, 0)`** (IS `rgb(255, 0, 0)`).
**ActiveText under headless, no patches: `rgb(255, 0, 0)`** (IS `rgb(255, 0, 0)`).

**Red occurs in BOTH modes.** The patch's own comment claims headless-only (`rgb(255, 0, 0)` for ActiveText); the data above shows red occurs in BOTH modes — ActiveText resolves to rgb(255, 0, 0) under headed too, which is what real Chrome reports, not a headless artifact; the patch's premise does not hold.

## Real vs. hardcoded screen/window properties (all 4 variants + headless reference)

| Variant | screenW | screenH | availW | availH | colorDepth | pixelDepth | dPR | innerW | innerH | outerW | outerH |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. full patch set (A+B, today's shape) | 1920 | 1080 | 1920 | 1057 | 30 | 30 | 2 | 900 | 613 | 900 | 698 |
| 2. without getComputedStyle Proxy (A only) | 1920 | 1080 | 1920 | 1057 | 30 | 30 | 2 | 900 | 613 | 900 | 698 |
| 3. without screen/window overrides (B only) | 1728 | 1117 | 1728 | 998 | 30 | 30 | 2 | 900 | 613 | 900 | 700 |
| 4. no patches (baseline) | 1728 | 1117 | 1728 | 998 | 30 | 30 | 2 | 900 | 613 | 900 | 700 |
| headless reference (no patches) | 800 | 600 | 800 | 600 | 24 | 24 | 1 | 756 | 469 | 756 | 556 |

**Hardcoded by the patch:** screenW/H=1920x1080, availW/H=1920x1057, colorDepth/pixelDepth=30, devicePixelRatio=2, outerW=innerW, outerH=innerH+85.
**Real values under headed, no patches** (variant 4 above): screenW/H=1728x1117, availW/H=1728x998, colorDepth/pixelDepth=30/30, devicePixelRatio=2 — this machine has a real 3456x2234 Retina display; the window geometry is whatever `--window-size`/position the launch used, not the hardcoded external-monitor values.

## bot.sannysoft.com

| Variant | total rows | failed rows |
|---|---|---|
| 1. full patch set (A+B, today's shape) | 57 | 0 |
| 2. without getComputedStyle Proxy (A only) | 57 | 0 |
| 3. without screen/window overrides (B only) | 57 | 0 |
| 4. no patches (baseline) | 57 | 0 |

All 4 variants: 0 failed rows. sannysoft does not discriminate between any of these patch combinations — neither block's presence or absence is visible to this particular check.

## CreepJS

No literal "Trust Score"/"N lies" summary exists in this live build (checked directly — every "trust"/"lie" substring hit in the full page HTML is a false positive, e.g. "CLIENT" containing "lie", or "TrustedTypePolicy"). The actual inconsistency-scoring surface here is the "Headless" section's three percentages plus scattered "confidence: &lt;level&gt;" notes.

| Variant | settled | headless signals (%, label) | confidence notes | literal lie/trust wording? |
|---|---|---|---|---|
| 1. full patch set (A+B, today's shape) | True | [('31', 'like headless'), ('0', 'headless'), ('0', 'stealth')] | ['highgpu', 'high'] | False |
| 2. without getComputedStyle Proxy (A only) | True | [('31', 'like headless'), ('0', 'headless'), ('0', 'stealth')] | ['highgpu', 'high'] | False |
| 3. without screen/window overrides (B only) | True | [('31', 'like headless'), ('0', 'headless'), ('0', 'stealth')] | ['highgpu', 'high'] | False |
| 4. no patches (baseline) | True | [('31', 'like headless'), ('0', 'headless'), ('0', 'stealth')] | ['highgpu', 'high'] | False |

All 4 variants produced the IDENTICAL headless-signal reading. CreepJS's headless-detection module does not discriminate between any of these patch combinations either.

## Per-Block Verdict

**Block B (getComputedStyle Proxy): DROP under headed.** Evidence: the ActiveText artifact table above shows the rgb(255,0,0) condition does not discriminate headless-only as the patch's comment assumes — red occurs in BOTH modes — ActiveText resolves to rgb(255, 0, 0) under headed too, which is what real Chrome reports, not a headless artifact; the patch's premise does not hold. Keeping an always-on Proxy wrapper around `window.getComputedStyle` under headed adds a detectable deviation (a native function replaced by a Proxy) for a condition that, per the data above, is not what it was written to fix in this mode.

**Block A (screen/window overrides): DROP under headed.** Evidence, precisely: `screenWidth, screenHeight, availWidth, availHeight` diverge from their hardcoded values on this machine's real headed window (real vs. hardcoded — see property table above); `colorDepth, pixelDepth, devicePixelRatio` happen to coincide with the hardcoded values on this specific machine (this Mac is itself 30-bit-color, devicePixelRatio 2) — that coincidence does not generalize to a different machine. The outerHeight formula (innerHeight+85) is also off by itself: real outerHeight-innerHeight = 87 here, not 85. Under headless there was no real display to contradict; under headed there is a real window with real, observable dimensions, and reporting values that don't match what a fingerprinter can cross-check against other signals (the actual rendered viewport, devicePixelRatio-dependent canvas/font rendering) is exactly the kind of contradiction detectors score. If a headed default ever needs a DIFFERENT consistent screen profile (not this machine's real one), values must be internally consistent with each other and with what the renderer actually does — Milestone 3's concern.

## Teardown

Orphan Chrome processes pinned to any `browser-posture-probe` profile after the run: 0