#!/usr/bin/env python3
"""Fingerprint-patch consistency probe (macOS) — Milestone 2 of the headed-default decision.

src/search/browser.py's JS_FINGERPRINT_PATCHES was written for a HEADLESS browser and has never run
under a headed one. Two of its parts are suspect under headed, for opposite reasons: the
getComputedStyle Proxy corrects a CSS artifact its own comment claims is headless-only (if true
under headed, the Proxy wrapper itself becomes the only detectable deviation); the screen/window
overrides hardcode values that contradicted nothing when there was no real display, but this machine
has a real 3456x2234 Retina display and a real window under headed.

Four variants, headed-backgrounded only (never foreground — `_lib.py`'s `open -g` mechanism):
1. full patch set (screen/window overrides + getComputedStyle Proxy, today's shape)
2. without the getComputedStyle Proxy (screen/window overrides only)
3. without the screen/window overrides (getComputedStyle Proxy only)
4. no patches at all (baseline)
Plus ONE headless reference run (no patches) for the artifact test only — the only way to tell
"headless-only artifact" apart from "Chrome says this regardless of mode".

The getComputedStyle artifact test does NOT use a plain resting link — the patch comment names CSS
ActiveText, the system color for a link in its ACTIVE state, not a link at rest (which just computes
to the ordinary link color in every mode). The artifact page (`_lib.py` ARTIFACT_HTML) declares
`color: ActiveText` explicitly, alongside LinkText/VisitedText (broader-divergence contrast) and a
plain link (contrast datapoint) — read directly via getComputedStyle, per variant.

Targets bot.sannysoft.com and CreepJS (abrahamjuliot.github.io/creepjs) are detection test pages
whose entire purpose is being measured against — scraping them IS the intended use here, not a
block-rate/anti-bot-evasion measurement, and no production search engine is a target. CreepJS is
heavy client-side JS; settle-detection polls document.body.textContent.length until two consecutive
reads match rather than trusting a fixed sleep.

CreepJS finding from live reconnaissance (this build, checked directly rather than assumed from
memory of another version): there is no literal "Trust Score" or "N lies" summary anywhere in the
rendered output — every "trust"/"lie" substring hit in the full HTML is either a false-positive
substring (e.g. "CLIENT" containing "lie", "TrustedTypePolicy") or a "confidence: <level>" note. The
actual inconsistency-scoring surface in this build is the "Headless" section's three percentages
("N% like headless", "N% headless", "N% stealth") plus scattered "confidence: <level>" notes — that
is what this probe extracts and reports as CreepJS's signal, instead of forcing a extraction for
wording the live page does not use.
"""

# INFRASTRUCTURE
import asyncio
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (  # noqa: E402
    launch_chrome, stop_chrome, profile_dir, start_probe_server, stop_probe_server,
    inject_before_navigation, read_system_colors, read_screen_window_props,
    wait_for_stable_content, extract_value,
)

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"

SANNYSOFT_URL = "https://bot.sannysoft.com/"
CREEPJS_URL = "https://abrahamjuliot.github.io/creepjs/"
SANNYSOFT_SETTLE_S = 3.0
CREEPJS_MAX_WAIT_S = 25.0

# Verbatim copies of the two independent IIFEs in src/search/browser.py's JS_FINGERPRINT_PATCHES —
# duplicated per dev-script isolation, composable independently since neither references the other
SCREEN_WINDOW_PATCH = """
(function() {
    // Screen dimensions: 1920x1080 (external Mac monitor)
    Object.defineProperty(screen, 'width', { get: () => 1920 });
    Object.defineProperty(screen, 'height', { get: () => 1080 });
    Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
    Object.defineProperty(screen, 'availHeight', { get: () => 1057 });
    Object.defineProperty(screen, 'colorDepth', { get: () => 30 });
    Object.defineProperty(screen, 'pixelDepth', { get: () => 30 });

    // devicePixelRatio: Retina Mac
    Object.defineProperty(window, 'devicePixelRatio', { get: () => 2 });

    // outerWidth/outerHeight: real browser has toolbar (~85px)
    Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
    Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight + 85 });
})();
"""

GETCOMPUTEDSTYLE_PATCH = """
(function() {
    // CSS ActiveText: headless renders rgb(255,0,0) — patch getComputedStyle (#39)
    var _origGCS = window.getComputedStyle;
    window.getComputedStyle = function(element, pseudoElt) {
        var style = _origGCS.apply(this, arguments);
        return new Proxy(style, {
            get: function(target, name) {
                var value = target[name];
                if (name === 'color' && value === 'rgb(255, 0, 0)') {
                    return 'rgb(0, 102, 204)';
                }
                return typeof value === 'function' ? value.bind(target) : value;
            }
        });
    };
})();
"""

VARIANTS = [
    {"slug": "full", "label": "1. full patch set (A+B, today's shape)", "script": SCREEN_WINDOW_PATCH + GETCOMPUTEDSTYLE_PATCH},
    {"slug": "screen_only", "label": "2. without getComputedStyle Proxy (A only)", "script": SCREEN_WINDOW_PATCH},
    {"slug": "style_only", "label": "3. without screen/window overrides (B only)", "script": GETCOMPUTEDSTYLE_PATCH},
    {"slug": "none", "label": "4. no patches (baseline)", "script": ""},
]

HARDCODED_PROPS = {
    "screenWidth": 1920, "screenHeight": 1080, "availWidth": 1920, "availHeight": 1057,
    "colorDepth": 30, "pixelDepth": 30, "devicePixelRatio": 2,
}


# ORCHESTRATOR

async def run_probe() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    server, thread, port = start_probe_server()
    artifact_url = f"http://127.0.0.1:{port}/artifact"
    results = {}
    try:
        for variant in VARIANTS:
            print(f"=== {variant['label']} ===", file=sys.stderr)
            results[variant["slug"]] = await run_variant(variant, artifact_url)
        print("=== headless reference (no patches, artifact test only) ===", file=sys.stderr)
        results["headless_reference"] = await run_headless_reference(artifact_url)
    finally:
        stop_probe_server(server, thread)

    orphans = check_orphans()
    report_path = write_report(results, orphans)
    print(f"\nReport: {report_path}", file=sys.stderr)
    print(f"Orphan Chrome processes after run: {len(orphans)}", file=sys.stderr)


# FUNCTIONS

# Run one headed-backgrounded variant: inject script, read local artifact colors/props, then hit
# both external detection targets
async def run_variant(variant: dict, artifact_url: str) -> dict:
    profile = profile_dir(f"fp-{variant['slug']}")
    browser, tab, _, _ = await launch_chrome(profile, headless=False, extra_flags=[], backgrounded=True)
    data = {"label": variant["label"]}
    try:
        await inject_before_navigation(tab, variant["script"])

        print("  artifact page (system colors + screen/window props)", file=sys.stderr)
        await tab.go_to(artifact_url, timeout=15.0)
        data["colors"] = await read_system_colors(tab)
        data["props"] = await read_screen_window_props(tab)

        print("  bot.sannysoft.com", file=sys.stderr)
        await tab.go_to(SANNYSOFT_URL, timeout=20.0)
        await asyncio.sleep(SANNYSOFT_SETTLE_S)
        data["sannysoft"] = await extract_sannysoft(tab)

        print("  creepjs", file=sys.stderr)
        await tab.go_to(CREEPJS_URL, timeout=30.0)
        _, settled = await wait_for_stable_content(
            tab, "document.body.textContent.length", interval=2.0, max_wait=CREEPJS_MAX_WAIT_S
        )
        data["creepjs"] = await extract_creepjs(tab)
        data["creepjs"]["settled"] = settled
    finally:
        await stop_chrome(browser, profile)
    return data


# Headless, no-patches reference — the artifact test only, to discriminate "headless-only artifact"
# from "Chrome reports this regardless of mode"
async def run_headless_reference(artifact_url: str) -> dict:
    profile = profile_dir("fp-headless-ref")
    browser, tab, _, _ = await launch_chrome(profile, headless=True, extra_flags=[], backgrounded=False)
    data = {"label": "headless reference (no patches)"}
    try:
        await tab.go_to(artifact_url, timeout=15.0)
        data["colors"] = await read_system_colors(tab)
        data["props"] = await read_screen_window_props(tab)
    finally:
        await stop_chrome(browser, profile)
    return data


# Extract every table row's label/result on bot.sannysoft.com, flagging "failed"-classed results
async def extract_sannysoft(tab) -> dict:
    raw = await tab.execute_script(
        "return JSON.stringify(Array.from(document.querySelectorAll('tr')).map(function(tr) {"
        "var tds = tr.querySelectorAll('td');"
        "if (tds.length < 2) return null;"
        "return {label: tds[0].textContent.trim().slice(0,60), "
        "result: tds[1].textContent.trim().slice(0,80), "
        "failed: /failed/i.test(tds[1].className)};"
        "}).filter(function(r) { return r; }))"
    )
    value = extract_value(raw)
    rows = json.loads(value) if value else []
    failed_rows = [r for r in rows if r["failed"]]
    return {"total_rows": len(rows), "failed_rows": failed_rows, "rows": rows}


# Extract CreepJS's actual inconsistency-scoring surface in this build: the "Headless" section's
# three percentages plus "confidence: <level>" notes — NOT a "trust score"/"lies" summary, which
# this live build does not render (verified by direct inspection, not assumed)
async def extract_creepjs(tab) -> dict:
    raw = await tab.execute_script("return document.body.textContent")
    full = extract_value(raw) or ""
    headless_signals = re.findall(r"(\d+)% (like headless|headless|stealth)", full)
    confidence_signals = re.findall(r"confidence: (\w+)", full)
    literal_lie_or_trust = bool(re.search(r"\blie(s|d)?\b|trust score", full, re.IGNORECASE))
    return {
        "body_text_len": len(full),
        "headless_signals": headless_signals,
        "confidence_signals": confidence_signals,
        "literal_lie_or_trust_wording_found": literal_lie_or_trust,
        "raw_excerpt": full[:1500],
    }


# Grep for any leftover Chrome process pinned to any probe profile dir
def check_orphans() -> list[str]:
    result = subprocess.run(["pgrep", "-fl", "browser-posture-probe"], capture_output=True, text=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


# Write markdown report and return its path
def write_report(results: dict, orphans: list[str]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"03_fingerprint_patch_probe_{ts}.md"

    none = results["none"]
    href = results["headless_reference"]
    red_headed_nopatch = none["colors"].get("activeText") == "rgb(255, 0, 0)"
    red_headless_nopatch = href["colors"].get("activeText") == "rgb(255, 0, 0)"

    lines = [
        f"# Fingerprint-Patch Consistency Probe — {ts}",
        "",
        "Dev-only probe (macOS, headed-backgrounded only): does `src/search/browser.py`'s "
        "`JS_FINGERPRINT_PATCHES` (written for headless) still make sense under headed? 4 variants "
        "+ 1 headless reference (artifact test only). Targets: local artifact page (system colors + "
        "screen/window props), bot.sannysoft.com, CreepJS.",
        "",
        "## getComputedStyle artifact: does the rgb(255,0,0) ActiveText artifact occur under headed?",
        "",
        "Tested on `color: ActiveText` directly (not a resting `<a>`, which computes to the ordinary "
        "link color in every mode and never touches what the patch targets).",
        "",
        "| Variant | plainLink | activeText | linkText | visitedText |",
        "|---|---|---|---|---|",
    ]
    for v in VARIANTS:
        c = results[v["slug"]]["colors"]
        lines.append(f"| {v['label']} | {c.get('plainLink')} | {c.get('activeText')} | {c.get('linkText')} | {c.get('visitedText')} |")
    lines.append(f"| {href['label']} | {href['colors'].get('plainLink')} | {href['colors'].get('activeText')} | {href['colors'].get('linkText')} | {href['colors'].get('visitedText')} |")

    lines += [
        "",
        f"**ActiveText under headed, no patches: `{none['colors'].get('activeText')}`** "
        f"({'IS' if red_headed_nopatch else 'is NOT'} `rgb(255, 0, 0)`).",
        f"**ActiveText under headless, no patches: `{href['colors'].get('activeText')}`** "
        f"({'IS' if red_headless_nopatch else 'is NOT'} `rgb(255, 0, 0)`).",
        "",
    ]
    if red_headless_nopatch and not red_headed_nopatch:
        verdict_b_reading = "**Red is headless-only.**"
        verdict_b_plain = (
            "red is headless-only — the patch's own premise holds: headless reports rgb(255, 0, 0) "
            "for ActiveText, headed does not"
        )
    elif red_headless_nopatch and red_headed_nopatch:
        verdict_b_reading = "**Red occurs in BOTH modes.**"
        verdict_b_plain = (
            "red occurs in BOTH modes — ActiveText resolves to rgb(255, 0, 0) under headed too, which "
            "is what real Chrome reports, not a headless artifact; the patch's premise does not hold"
        )
    elif not red_headless_nopatch and not red_headed_nopatch:
        verdict_b_reading = "**Red occurs in NEITHER mode observed here.**"
        verdict_b_plain = (
            "red occurs in neither mode observed here — the patch corrects a condition not observed "
            "in this Chrome version on this machine, headed or headless"
        )
    else:
        verdict_b_reading = "**Red occurs under headed but NOT headless.**"
        verdict_b_plain = "red occurs under headed but not headless — the inverse of the patch's premise"
    lines.append(
        f"{verdict_b_reading} The patch's own comment claims headless-only "
        f"(`rgb(255, 0, 0)` for ActiveText); the data above shows {verdict_b_plain}."
    )

    lines += [
        "",
        "## Real vs. hardcoded screen/window properties (all 4 variants + headless reference)",
        "",
        "| Variant | screenW | screenH | availW | availH | colorDepth | pixelDepth | dPR | innerW | innerH | outerW | outerH |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for v in VARIANTS:
        p = results[v["slug"]]["props"]
        lines.append(
            f"| {v['label']} | {p.get('screenWidth')} | {p.get('screenHeight')} | {p.get('availWidth')} | "
            f"{p.get('availHeight')} | {p.get('colorDepth')} | {p.get('pixelDepth')} | {p.get('devicePixelRatio')} | "
            f"{p.get('innerWidth')} | {p.get('innerHeight')} | {p.get('outerWidth')} | {p.get('outerHeight')} |"
        )
    p_href = href["props"]
    lines.append(
        f"| {href['label']} | {p_href.get('screenWidth')} | {p_href.get('screenHeight')} | {p_href.get('availWidth')} | "
        f"{p_href.get('availHeight')} | {p_href.get('colorDepth')} | {p_href.get('pixelDepth')} | {p_href.get('devicePixelRatio')} | "
        f"{p_href.get('innerWidth')} | {p_href.get('innerHeight')} | {p_href.get('outerWidth')} | {p_href.get('outerHeight')} |"
    )
    lines += [
        "",
        f"**Hardcoded by the patch:** screenW/H=1920x1080, availW/H=1920x1057, colorDepth/pixelDepth=30, "
        f"devicePixelRatio=2, outerW=innerW, outerH=innerH+85.",
        f"**Real values under headed, no patches** (variant 4 above): screenW/H="
        f"{results['none']['props'].get('screenWidth')}x{results['none']['props'].get('screenHeight')}, "
        f"availW/H={results['none']['props'].get('availWidth')}x{results['none']['props'].get('availHeight')}, "
        f"colorDepth/pixelDepth={results['none']['props'].get('colorDepth')}/{results['none']['props'].get('pixelDepth')}, "
        f"devicePixelRatio={results['none']['props'].get('devicePixelRatio')} — "
        "this machine has a real 3456x2234 Retina display; the window geometry is whatever "
        "`--window-size`/position the launch used, not the hardcoded external-monitor values.",
        "",
        "## bot.sannysoft.com",
        "",
        "| Variant | total rows | failed rows |",
        "|---|---|---|",
    ]
    for v in VARIANTS:
        s = results[v["slug"]]["sannysoft"]
        lines.append(f"| {v['label']} | {s['total_rows']} | {len(s['failed_rows'])} |")
    if all(len(results[v["slug"]]["sannysoft"]["failed_rows"]) == 0 for v in VARIANTS):
        lines.append(
            "\nAll 4 variants: 0 failed rows. sannysoft does not discriminate between any of these "
            "patch combinations — neither block's presence or absence is visible to this particular check."
        )
    for v in VARIANTS:
        s = results[v["slug"]]["sannysoft"]
        if s["failed_rows"]:
            lines.append(f"\n**{v['label']} — failed rows:**")
            for r in s["failed_rows"]:
                lines.append(f"- {r['label']}: {r['result']}")

    lines += [
        "",
        "## CreepJS",
        "",
        "No literal \"Trust Score\"/\"N lies\" summary exists in this live build (checked directly — "
        "every \"trust\"/\"lie\" substring hit in the full page HTML is a false positive, e.g. "
        "\"CLIENT\" containing \"lie\", or \"TrustedTypePolicy\"). The actual inconsistency-scoring "
        "surface here is the \"Headless\" section's three percentages plus scattered "
        "\"confidence: &lt;level&gt;\" notes.",
        "",
        "| Variant | settled | headless signals (%, label) | confidence notes | literal lie/trust wording? |",
        "|---|---|---|---|---|",
    ]
    for v in VARIANTS:
        c = results[v["slug"]]["creepjs"]
        lines.append(
            f"| {v['label']} | {c['settled']} | {c['headless_signals']} | {c['confidence_signals']} | "
            f"{c['literal_lie_or_trust_wording_found']} |"
        )
    signal_sets = {tuple(results[v["slug"]]["creepjs"]["headless_signals"]) for v in VARIANTS}
    if len(signal_sets) == 1:
        lines.append(
            "\nAll 4 variants produced the IDENTICAL headless-signal reading. CreepJS's headless-"
            "detection module does not discriminate between any of these patch combinations either."
        )

    lines += ["", "## Per-Block Verdict", ""]
    if red_headless_nopatch and not red_headed_nopatch:
        block_b_verdict = (
            "**Block B (getComputedStyle Proxy): KEEP.** Evidence: the ActiveText artifact table above "
            "— `rgb(255, 0, 0)` occurs under headless-no-patches and does NOT occur under headed-no-"
            "patches. The patch's own premise is correct; dropping it under headed would leave headless "
            "runs (if any remain, e.g. via `WEBSEARCH_HEADED` unset) uncorrected, but under headed itself "
            "the Proxy is presently a no-op (nothing to rewrite) rather than a harmful wrapper, since the "
            "trigger condition never fires."
        )
    else:
        block_b_verdict = (
            "**Block B (getComputedStyle Proxy): DROP under headed.** Evidence: the ActiveText artifact "
            "table above shows the rgb(255,0,0) condition does not discriminate headless-only as the "
            f"patch's comment assumes — {verdict_b_plain}. Keeping an always-on Proxy wrapper around "
            "`window.getComputedStyle` under headed adds a detectable deviation (a native function "
            "replaced by a Proxy) for a condition that, per the data above, is not what it was written "
            "to fix in this mode."
        )
    lines.append(block_b_verdict)
    lines.append("")

    real_props = results["none"]["props"]
    diverging = [k for k, v in HARDCODED_PROPS.items() if real_props.get(k) != v]
    matching = [k for k, v in HARDCODED_PROPS.items() if real_props.get(k) == v]
    real_outer_h = real_props.get("outerHeight")
    real_inner_h = real_props.get("innerHeight")
    outer_h_offset = (real_outer_h - real_inner_h) if isinstance(real_outer_h, int) and isinstance(real_inner_h, int) else None

    if diverging:
        lines.append(
            f"**Block A (screen/window overrides): DROP under headed.** Evidence, precisely: "
            f"`{', '.join(diverging)}` diverge from their hardcoded values on this machine's real headed "
            f"window (real vs. hardcoded — see property table above); "
            + (f"`{', '.join(matching)}` happen to coincide with the hardcoded values on this specific "
               f"machine (this Mac is itself 30-bit-color, devicePixelRatio 2) " if matching else "")
            + f"— that coincidence does not generalize to a different machine. The outerHeight formula "
            f"(innerHeight+85) is also off by itself: real outerHeight-innerHeight = {outer_h_offset} here, "
            f"not 85. Under headless there was no real display to contradict; under headed there is a real "
            "window with real, observable dimensions, and reporting values that don't match what a "
            "fingerprinter can cross-check against other signals (the actual rendered viewport, "
            "devicePixelRatio-dependent canvas/font rendering) is exactly the kind of contradiction "
            "detectors score. If a headed default ever needs a DIFFERENT consistent screen profile (not "
            "this machine's real one), values must be internally consistent with each other and with what "
            "the renderer actually does — Milestone 3's concern."
        )
    else:
        lines.append(
            "**Block A (screen/window overrides): the real and hardcoded values happen to match this "
            "run — re-check before relying on this on a different display/window configuration.**"
        )

    lines += [
        "",
        "## Teardown",
        "",
        f"Orphan Chrome processes pinned to any `browser-posture-probe` profile after the run: {len(orphans)}",
    ]
    if orphans:
        lines.append("")
        lines.extend(f"    {o}" for o in orphans)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    asyncio.run(run_probe())
