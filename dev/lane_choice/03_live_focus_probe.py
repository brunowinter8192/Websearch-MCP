#!/usr/bin/env python3
"""Live HUMAN focus-steal probe — launches a REAL scrape lane via THIS worktree's own `cli.py`
(never the `websearch` PATH wrapper, which is pinned to the main repo — see DOCS.md Gotchas) against
a real URL, after a visible countdown that gives the human time to switch to another application and
start typing. While the human watches/types, both macOS focus instruments this project already uses
(`02_focus_poll_smoke.py`'s frontmost-app poll and AXMain key-window poll) run concurrently on
background threads, independent of the human's own judgment. Afterwards prints a compact per-
instrument verdict (sample count, deviation count, longest continuous deviation, deviation offsets)
to the terminal the human is looking at, and writes the full sample series to md/ so the numbers
survive the terminal.

Measurement only — no fix, no mitigation change. Reuses 02's instrument primitives via
importlib.util.spec_from_file_location (same numbered-script-reuse pattern as
dev/search_pipeline/00_single_query.py importing 01_google_smoke.py).
"""
# INFRASTRUCTURE
import argparse
import asyncio
import importlib.util
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from patchright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent
WORKTREE_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = WORKTREE_ROOT / "cli.py"
PYTHON = WORKTREE_ROOT / "venv" / "bin" / "python"
REPORT_DIR = SCRIPT_DIR / "md"

# Reuse 02_focus_poll_smoke.py's instrument primitives directly rather than re-declaring them —
# filename starts with a digit, so a normal `import` statement can't name it; this is this project's
# own precedent for wiring one numbered dev script off another (dev/search_pipeline/00_single_query.py
# importing 01_google_smoke.py the same way). Module-level code in 02 is only constants/def's plus an
# `if __name__ == "__main__"` guard, so exec_module here has no side effects.
_spec = importlib.util.spec_from_file_location("focus_poll_smoke", SCRIPT_DIR / "02_focus_poll_smoke.py")
_focus_poll_smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_focus_poll_smoke)
get_frontmost_app = _focus_poll_smoke.get_frontmost_app
get_key_window_owner = _focus_poll_smoke.get_key_window_owner
resolve_camoufox_app_name = _focus_poll_smoke.resolve_camoufox_app_name

POLL_INTERVAL_S = 0.25
# Long enough for a human to read the on-screen instruction, alt-tab/click to a different
# application, and actually start typing there before the browser launches — a 2-3s countdown was
# judged too tight for the read-then-act sequence, 10s gives clear margin.
COUNTDOWN_S = 10
DEFAULT_URL = "https://example.com"


# ORCHESTRATOR

# Countdown -> launch the real lane via THIS worktree's cli.py -> poll both instruments concurrently
# -> print verdict -> write full-series report
def live_focus_probe_workflow(url: str, use_chromium: bool) -> None:
    lane = "chromium" if use_chromium else "camoufox"
    subcommand = "scrape_url_chromium" if use_chromium else "scrape_url_camoufox"
    target_app_name = resolve_target_app_name(use_chromium)

    print_countdown(lane, target_app_name)
    baseline_app = get_frontmost_app()
    print(f"Baseline frontmost app (post-countdown, expected throughout): {baseline_app}")
    print(f"Instrument 2 target app (AXMain/key-window): {target_app_name}\n")

    frontmost_samples: list[tuple[float, str]] = []
    key_window_samples: list[tuple[float, bool]] = []
    stop_event = threading.Event()
    t0 = time.perf_counter()
    frontmost_thread = threading.Thread(
        target=poll_frontmost_loop, args=(t0, frontmost_samples, stop_event)
    )
    key_window_thread = threading.Thread(
        target=poll_key_window_loop, args=(target_app_name, t0, key_window_samples, stop_event)
    )
    frontmost_thread.start()
    key_window_thread.start()

    cmd = [str(PYTHON), str(CLI_PATH), subcommand, url]
    print(f"LAUNCHING NOW: {' '.join(cmd)}  (cwd={WORKTREE_ROOT})")
    result = subprocess.run(cmd, cwd=WORKTREE_ROOT, capture_output=True, text=True)
    wall_s = time.perf_counter() - t0

    stop_event.set()
    frontmost_thread.join()
    key_window_thread.join()

    print(f"\nSubprocess exit code: {result.returncode}  (wall: {wall_s:.1f}s)")
    if result.returncode != 0:
        print("stderr (last 20 lines):")
        print("\n".join(result.stderr.splitlines()[-20:]))

    verdict = compute_verdict(baseline_app, frontmost_samples, key_window_samples)
    print_verdict(verdict)

    report_path = write_report(
        lane, url, cmd, baseline_app, target_app_name,
        frontmost_samples, key_window_samples, verdict, result.returncode, wall_s,
    )
    print(f"\nFull sample series report: {report_path}")


# FUNCTIONS

# Instrument-2 target app name, resolved for whichever lane is actually being launched (never
# hardcoded). Chromium is a regular, non-accessory app already caught by instrument 1 (frontmost) —
# only an LSUIElement accessory process (Camoufox) is structurally invisible to it — so targeting the
# lane-under-test's own app, rather than always "Camoufox", is what makes --chromium runs produce a
# same-shape (if expectedly redundant-with-instrument-1) report row instead of an always-False no-op.
def resolve_target_app_name(use_chromium: bool) -> str:
    if use_chromium:
        return asyncio.run(_resolve_chromium_app_name())
    return resolve_camoufox_app_name()


# Chromium's OWN currently-installed patchright bundle name, resolved dynamically — same resolution
# shape as chromium_scrape.py's _resolve_chromium_bundle_path/_find_app_bundle, duplicated here per
# this project's own precedent of not sharing small lane-specific mechanisms across independent probes
async def _resolve_chromium_app_name() -> str:
    pw = await async_playwright().start()
    try:
        executable_path = pw.chromium.executable_path
    finally:
        await pw.stop()
    for parent in Path(executable_path).parents:
        if parent.suffix == ".app":
            return parent.stem
    return "Chromium"


# Clearly visible pre-launch instruction + second-by-second countdown, printed to the terminal the
# human is sitting at — the whole reason this probe exists (a human must have time to act on it)
def print_countdown(lane: str, target_app_name: str) -> None:
    print("=" * 64)
    print(f"LIVE FOCUS-STEAL PROBE — {lane} lane")
    print("=" * 64)
    print(f"Instrument 2 will watch: {target_app_name}")
    print()
    print(">>> SWITCH TO ANOTHER APPLICATION NOW AND START TYPING. <<<")
    print(f"The browser launches in {COUNTDOWN_S} seconds.\n")
    for remaining in range(COUNTDOWN_S, 0, -1):
        print(f"  launching in {remaining}s...", flush=True)
        time.sleep(1)
    print("  LAUNCHING NOW.\n", flush=True)


# Background-thread loop: append (elapsed_s_since_launch, frontmost_app) samples until stop_event fires
def poll_frontmost_loop(t0: float, samples: list[tuple[float, str]], stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        app = get_frontmost_app()
        samples.append((round(time.perf_counter() - t0, 2), app))
        time.sleep(POLL_INTERVAL_S)


# Background-thread loop: append (elapsed_s_since_launch, is_key_window) samples for app_name until stop_event fires
def poll_key_window_loop(
    app_name: str, t0: float, samples: list[tuple[float, bool]], stop_event: threading.Event
) -> None:
    while not stop_event.is_set():
        is_key = get_key_window_owner(app_name)
        samples.append((round(time.perf_counter() - t0, 2), is_key))
        time.sleep(POLL_INTERVAL_S)


# Longest continuous run of deviating samples, in seconds — walks the (timestamp, value) series once,
# closing a run on the first non-deviating sample (or end of series); +poll_interval accounts for the
# last deviating sample's own dwell time rather than undercounting by one interval
def longest_continuous_run(samples: list[tuple[float, object]], is_deviation, poll_interval_s: float) -> float:
    longest = 0.0
    run_start = None
    prev_t = None
    for t, v in samples:
        if is_deviation(v):
            if run_start is None:
                run_start = t
            prev_t = t
        else:
            if run_start is not None:
                longest = max(longest, prev_t - run_start + poll_interval_s)
                run_start = None
    if run_start is not None:
        longest = max(longest, prev_t - run_start + poll_interval_s)
    return round(longest, 2)


# Per-instrument tallies + longest continuous deviation + deviation offsets — the compact verdict shape
def compute_verdict(
    baseline_app: str,
    frontmost_samples: list[tuple[float, str]],
    key_window_samples: list[tuple[float, bool]],
) -> dict:
    fm_deviations = [(t, app) for t, app in frontmost_samples if app != baseline_app]
    kw_deviations = [(t, is_key) for t, is_key in key_window_samples if is_key]
    return {
        "fm_total": len(frontmost_samples),
        "fm_dev_count": len(fm_deviations),
        "fm_longest_s": longest_continuous_run(frontmost_samples, lambda app: app != baseline_app, POLL_INTERVAL_S),
        "fm_dev_offsets": [t for t, _ in fm_deviations],
        "kw_total": len(key_window_samples),
        "kw_dev_count": len(kw_deviations),
        "kw_longest_s": longest_continuous_run(key_window_samples, lambda is_key: is_key, POLL_INTERVAL_S),
        "kw_dev_offsets": [t for t, _ in kw_deviations],
    }


# Compact verdict, printed to the terminal the human is looking at
def print_verdict(verdict: dict) -> None:
    print("\n" + "=" * 64)
    print("VERDICT")
    print("=" * 64)
    print(
        f"Instrument 1 (frontmost app): {verdict['fm_total']} samples, "
        f"{verdict['fm_dev_count']} deviations, longest continuous deviation "
        f"{verdict['fm_longest_s']}s"
    )
    if verdict["fm_dev_offsets"]:
        print(f"  offsets (s since launch): {verdict['fm_dev_offsets']}")
    print(
        f"Instrument 2 (AXMain key-window): {verdict['kw_total']} samples, "
        f"{verdict['kw_dev_count']} deviations, longest continuous deviation "
        f"{verdict['kw_longest_s']}s"
    )
    if verdict["kw_dev_offsets"]:
        print(f"  offsets (s since launch): {verdict['kw_dev_offsets']}")


# Write the full sample series + verdict to md/ so the numbers survive the terminal
def write_report(
    lane: str, url: str, cmd: list[str], baseline_app: str, target_app_name: str,
    frontmost_samples: list[tuple[float, str]], key_window_samples: list[tuple[float, bool]],
    verdict: dict, returncode: int, wall_s: float,
) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"03_live_focus_probe_report_{ts}.md"

    lines = [
        f"## Live focus-steal probe ({ts})",
        f"- Lane: {lane}",
        f"- URL: {url}",
        f"- Command: {' '.join(cmd)}",
        f"- Worktree root: {WORKTREE_ROOT}",
        f"- Countdown given before launch: {COUNTDOWN_S}s",
        f"- Baseline (expected) frontmost app: `{baseline_app}`",
        f"- Instrument 2 target app (AXMain/key-window): `{target_app_name}`",
        f"- Poll interval: {POLL_INTERVAL_S}s",
        f"- Subprocess exit code: {returncode}",
        f"- Wall time (browser launch to subprocess exit): {wall_s:.1f}s",
        "",
        "## Verdict",
        f"- Instrument 1 (frontmost app): {verdict['fm_total']} samples, "
        f"{verdict['fm_dev_count']} deviations, longest continuous deviation {verdict['fm_longest_s']}s",
        f"- Instrument 2 (AXMain key-window): {verdict['kw_total']} samples, "
        f"{verdict['kw_dev_count']} deviations, longest continuous deviation {verdict['kw_longest_s']}s",
        "",
        f"## Instrument 1 — deviation offsets ({verdict['fm_dev_count']} of {verdict['fm_total']})",
    ]
    lines.append("NONE" if not verdict["fm_dev_offsets"] else ", ".join(f"t={t}s" for t in verdict["fm_dev_offsets"]))
    lines += ["", f"## Instrument 2 — deviation offsets ({verdict['kw_dev_count']} of {verdict['kw_total']})"]
    lines.append("NONE" if not verdict["kw_dev_offsets"] else ", ".join(f"t={t}s" for t in verdict["kw_dev_offsets"]))

    lines += ["", "## Instrument 1 — full sample series"]
    lines += [f"- t={t}s: {app}" for t, app in frontmost_samples]
    lines += ["", "## Instrument 2 — full sample series"]
    lines += [f"- t={t}s: {is_key}" for t, is_key in key_window_samples]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Live HUMAN focus-steal probe: launches a real scrape lane via THIS worktree's own "
            "cli.py (never the `websearch` PATH wrapper), after a countdown, while polling two "
            "macOS focus instruments concurrently. Watch your own focus/typing during the run, "
            "then read the printed verdict."
        )
    )
    parser.add_argument("--url", default=DEFAULT_URL, help=f"URL to scrape (default: {DEFAULT_URL})")
    parser.add_argument(
        "--chromium", action="store_true",
        help="Run the chromium lane instead of camoufox (default: camoufox)",
    )
    args = parser.parse_args()
    live_focus_probe_workflow(args.url, args.chromium)


if __name__ == "__main__":
    main()
