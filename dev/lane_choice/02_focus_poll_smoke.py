#!/usr/bin/env python3
"""Runs `01_backfill_pairs.py` as a subprocess under TWO concurrent macOS focus-steal instruments —
the focus-steal verification gate for the lane-choice backfill:
1. Frontmost-app poll: any sample where a browser engine is the frontmost REGULAR app instead of
   the app that was frontmost when this script started is a steal (chromium's steal class —
   proven-effective for a regular, non-accessory app).
2. Key-window poll: Camoufox is LSUIElement (accessory) — it can grab true keyboard/mouse input
   focus (AXMain on its own front window) WITHOUT ever registering as "frontmost" in instrument 1's
   sense (confirmed blind spot: Firefox's `-foreground` launch flag forces key-window status via an
   explicit Cocoa activation call that bypasses the passive LSUIElement default instrument 1 relies
   on). Instrument 2 queries Camoufox's OWN process by name, not a system-wide filter (which requires
   Accessibility permission this environment doesn't grant), so it catches this class instrument 1
   cannot.
"""
# INFRASTRUCTURE
import argparse
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BACKFILL_SCRIPT = SCRIPT_DIR / "01_backfill_pairs.py"
REPORT_DIR = SCRIPT_DIR / "md"
PYTHON = sys.executable

FOCUS_POLL_INTERVAL_S = 0.25


# ORCHESTRATOR

# Launch the backfill subprocess, poll both focus-steal instruments concurrently until it exits, report all
def focus_poll_smoke_workflow(limit: int | None) -> None:
    baseline_app = get_frontmost_app()
    camoufox_app_name = resolve_camoufox_app_name()
    print(f"Baseline frontmost app (expected throughout): {baseline_app}", file=sys.stderr)
    print(f"Camoufox process name (key-window instrument target): {camoufox_app_name}", file=sys.stderr)

    frontmost_samples: list[tuple[float, str]] = []
    key_window_samples: list[tuple[float, bool]] = []
    stop_event = threading.Event()
    frontmost_thread = threading.Thread(target=poll_frontmost_loop, args=(frontmost_samples, stop_event))
    key_window_thread = threading.Thread(
        target=poll_key_window_loop, args=(camoufox_app_name, key_window_samples, stop_event)
    )
    frontmost_thread.start()
    key_window_thread.start()

    t_start = time.perf_counter()
    cmd = [PYTHON, str(BACKFILL_SCRIPT)]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    result = subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    wall_s = time.perf_counter() - t_start

    stop_event.set()
    frontmost_thread.join()
    key_window_thread.join()

    report_path = write_report(
        baseline_app, camoufox_app_name, frontmost_samples, key_window_samples, result.returncode, wall_s
    )
    print(f"\nFocus-poll report: {report_path}", file=sys.stderr)


# FUNCTIONS

# Frontmost macOS application name (same primitive as dev/browser_posture/_lib.py's get_frontmost_app)
def get_frontmost_app() -> str:
    result = subprocess.run(
        [
            "osascript", "-e",
            'tell application "System Events" to get name of first application process whose frontmost is true',
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


# Camoufox's .app process name, resolved off the REAL installed bundle (never hardcoded) — same
# resolution pattern as chromium_scrape.py's bundle_path.stem, via camoufox's own launch_options()
def resolve_camoufox_app_name() -> str:
    from camoufox import launch_options as camoufox_launch_options
    resolved = camoufox_launch_options(headless=False, os="macos")
    executable_path = Path(resolved["executable_path"])
    for parent in executable_path.parents:
        if parent.suffix == ".app":
            return parent.stem
    return "Camoufox"


# True if app_name's OWN front window is the true key/main window (AXMain) — the key-window-level
# signal, queried per-named-process (not a system-wide "whose" filter, which throws a hard
# Accessibility permission error on this machine). False (not True) on any error, e.g. the process
# isn't running — correct: a non-running process cannot hold key-window focus.
def get_key_window_owner(app_name: str) -> bool:
    result = subprocess.run(
        [
            "osascript", "-e",
            f'tell application "System Events" to tell process "{app_name}" '
            'to return value of attribute "AXMain" of front window',
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip() == "true"


# Background-thread loop: append (elapsed_s, app_name) samples until stop_event fires
def poll_frontmost_loop(samples: list[tuple[float, str]], stop_event: threading.Event) -> None:
    t0 = time.perf_counter()
    while not stop_event.is_set():
        app = get_frontmost_app()
        samples.append((round(time.perf_counter() - t0, 2), app))
        time.sleep(FOCUS_POLL_INTERVAL_S)


# Background-thread loop: append (elapsed_s, is_key_window) samples for camoufox_app_name until stop_event fires
def poll_key_window_loop(camoufox_app_name: str, samples: list[tuple[float, bool]], stop_event: threading.Event) -> None:
    t0 = time.perf_counter()
    while not stop_event.is_set():
        is_key = get_key_window_owner(camoufox_app_name)
        samples.append((round(time.perf_counter() - t0, 2), is_key))
        time.sleep(FOCUS_POLL_INTERVAL_S)


# Write the funnel + both instruments' tallies + any-violation-sample report
def write_report(
    baseline_app: str, camoufox_app_name: str,
    frontmost_samples: list[tuple[float, str]], key_window_samples: list[tuple[float, bool]],
    returncode: int, wall_s: float,
) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"02_focus_poll_smoke_report_{ts}.md"

    counts: dict[str, int] = {}
    for _, app in frontmost_samples:
        counts[app] = counts.get(app, 0) + 1
    deviations = [(t, app) for t, app in frontmost_samples if app != baseline_app]
    key_window_hits = [(t, is_key) for t, is_key in key_window_samples if is_key]

    lines = [
        f"## Focus-poll smoke ({ts})",
        f"- Backfill subprocess exit code: {returncode}",
        f"- Wall time: {wall_s:.1f}s",
        f"- Baseline (expected) frontmost app: `{baseline_app}`",
        f"- Camoufox process name (key-window instrument target): `{camoufox_app_name}`",
        f"- Poll interval: {FOCUS_POLL_INTERVAL_S}s",
        "",
        f"## Instrument 1 — Frontmost app tally (whole run, {len(frontmost_samples)} samples)",
    ]
    for app, count in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(frontmost_samples) if frontmost_samples else 0
        lines.append(f"- `{app}`: {count} ({pct:.1f}%)")

    lines += ["", f"## Instrument 1 — Deviations from baseline ({len(deviations)} samples)"]
    if not deviations:
        lines.append("NONE — baseline app stayed frontmost for every sample. No frontmost-level steal observed.")
    else:
        for t, app in deviations:
            lines.append(f"- t={t}s: `{app}`")

    lines += [
        "",
        f"## Instrument 2 — Camoufox key-window (AXMain) samples ({len(key_window_samples)} total, "
        f"{len(key_window_hits)} True)",
    ]
    if not key_window_hits:
        lines.append(
            "NONE True — Camoufox's own window never held true key/main-window status. "
            "No key-window-level steal observed."
        )
    else:
        for t, _ in key_window_hits:
            lines.append(f"- t={t}s: Camoufox held key-window status (STEAL)")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Run the lane-choice backfill under a live macOS frontmost-app poll (focus-steal check)."
    )
    parser.add_argument("--limit", type=int, default=None, help="Forwarded to 01_backfill_pairs.py --limit")
    args = parser.parse_args()
    focus_poll_smoke_workflow(args.limit)


if __name__ == "__main__":
    main()
