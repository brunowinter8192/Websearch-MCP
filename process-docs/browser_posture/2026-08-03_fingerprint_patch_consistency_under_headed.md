# Fingerprint-patch consistency under headed (2026-08-03)

Milestone 2 of 3 toward the headed-default switch (`2026-08-03_launch_latency_and_flag_probe.md` in
this area covers milestone 1). `src/search/browser.py`'s `JS_FINGERPRINT_PATCHES` was written for a
headless browser and had never run under a headed one. Probe:
`dev/browser_posture/03_fingerprint_patch_probe.py`, report in `dev/browser_posture/md/`.

## The artifact test had to target the right CSS state

First plan used a plain, resting `<a>` element to test the getComputedStyle patch's claimed
`rgb(255,0,0)` artifact. Caught before implementation: the patch's own comment names CSS ActiveText —
the system color for a link in its ACTIVE state, not a link at rest, which just computes to the
ordinary link color (`rgb(0, 0, 238)`) in every mode. A resting-link test would have read blue
everywhere and concluded the artifact doesn't occur under headed, for the wrong reason — never having
touched the thing the patch corrects. Fixed: a dedicated element with an explicit `color: ActiveText`
CSS declaration, read via `getComputedStyle`, alongside `LinkText`/`VisitedText` (to tell an
ActiveText-specific divergence apart from a broader system-color one) and the resting `<a>` kept only
as a contrast datapoint.

## Does the rgb(255,0,0) artifact occur under headed? Yes — and in headless too

Four headed-backgrounded variants (full patch set / screen-window-overrides-only / getComputedStyle-
Proxy-only / no patches) plus one headless reference (no patches), all reading `getComputedStyle` on
the `ActiveText` element:

| Mode | ActiveText (no patches) |
|---|---|
| headed | `rgb(255, 0, 0)` |
| headless | `rgb(255, 0, 0)` |

Red occurs in BOTH modes. The patch's own premise — that `rgb(255,0,0)` is a headless-only artifact —
does not hold on this Chrome (150.0.7871.187, macOS 26.5.2 arm64): ActiveText resolves to red
regardless of mode. This is the discriminating question the milestone was built to answer, and the
headless-reference variant is exactly what makes the discrimination possible — without it, "red under
headed" alone would be uninterpretable (headless-only-artifact vs. Chrome-general-behavior are
observationally identical from the headed side alone).

**Block B (getComputedStyle Proxy) verdict: DROP under headed.** Since the condition it "corrects" is
not headless-specific, the Proxy wrapper is not fixing an anomaly — it's rewriting a value real Chrome
reports in every mode into one no real Chrome reports (`rgb(0, 102, 204)`), while leaving behind a
permanently-detectable deviation (`window.getComputedStyle` replaced by a `Proxy`) for a condition
that, per this data, was never mode-specific to begin with.

## Screen/window overrides: which specific values diverge, which coincide

Real headed values (no patches, this session): `screenWidth/Height` 1728x1117, `availWidth/Height`
1728x998, `colorDepth`/`pixelDepth` 30/30, `devicePixelRatio` 2 (CSS-pixel values — this machine's
real 3456x2234 Retina panel at devicePixelRatio 2 reads as 1728x1117 in `screen.width/height`, which
report CSS pixels, not device pixels). Against the hardcoded set (1920x1080, avail 1920x1057,
colorDepth/pixelDepth 30, devicePixelRatio 2):

- **Diverge:** `screenWidth`, `screenHeight`, `availWidth`, `availHeight` — real values differ from
  the hardcoded external-monitor numbers.
- **Coincide (by accident of this specific machine):** `colorDepth`, `pixelDepth`, `devicePixelRatio`
  — this Mac happens to also be 30-bit-color and devicePixelRatio 2, so these three particular
  hardcoded values are not currently wrong, but that is a property of this machine, not something the
  patch established.
- **outerHeight formula also measured off:** real `outerHeight - innerHeight` = 87 on this run, not
  the hardcoded 85.

**Block A (screen/window overrides) verdict: DROP under headed.** Under headless there was no real
display for these values to contradict. Under headed there is a real window with real, observable
dimensions — reporting values that don't match what a fingerprinter can cross-check against other
signals (actual rendered viewport, devicePixelRatio-dependent canvas/font rendering) is exactly the
contradiction class detectors score, which was the concern this milestone set out to test, now
confirmed with real numbers rather than assumed. If a future headed default needs a deliberately
different (non-real) screen profile, the values must be internally consistent with each other and
with what the renderer actually produces — carried forward as a Milestone 3 concern, not resolved here.

## What the two live detection targets actually showed

bot.sannysoft.com: 57 rows, 0 failed, identically across all 4 variants — this check does not
discriminate between any of the patch combinations tested; whatever it's sensitive to, these two
blocks are not it (in either direction).

CreepJS (`abrahamjuliot.github.io/creepjs`, direct reconnaissance this session, not assumed from
memory of another version of the tool): the current live build renders no "Trust Score" or "N lies"
summary anywhere — every "trust"/"lie" substring match in the full rendered HTML is a false positive
(e.g. "CLIENT" contains "lie", `TrustedTypePolicy*` global names contain "trust"). The actual
inconsistency-scoring surface in this build is the "Headless" section's three percentages ("N% like
headless", "N% headless", "N% stealth") plus scattered "confidence: <level>" notes. All 4 variants
produced the identical reading (31% like headless, 0% headless, 0% stealth, confidence: high) —
CreepJS's headless-detection module doesn't discriminate between these patch combinations either.
Settle-detection (poll `document.body.textContent.length` until two consecutive reads match, cap
25s) reported `settled: True` for every variant — reading a finished result, not a half-rendered one,
was not the open question this run left; the finding itself (no dedicated lies/trust summary in this
build) is.

## Net read

Neither live detection target's pass/fail signal moved with any patch combination — so nothing in
this data argues FOR keeping either block on live-detection grounds. Both direct, controlled tests
(the ActiveText artifact, the real-vs-hardcoded properties) argue for dropping both blocks under
headed: Block B corrects a condition that isn't mode-specific, Block A hardcodes values that
contradict this real, observable window. Milestone 3 (rebuild of `browser.py`) is where these
verdicts get implemented — not addressed in this probe.
