#!/usr/bin/env python3
"""Runs `01_backfill_pairs.py` as a subprocess under a live macOS frontmost-app poll — the
focus-steal verification gate for the lane-choice backfill: any sample where a browser engine is
the frontmost REGULAR app instead of the app that was frontmost when this script started is a
steal (chromium's steal class — proven-effective for a regular, non-accessory app).

REMOVED 2026-08-27: a second, LSUIElement/accessory-process-scoped window-activation instrument,
added because Camoufox never registers as "frontmost" in this poll's sense. Live human-judged runs
(both on `example.com` and, decisively, against 5 real URLs sequentially under sustained load — the
original complaint's own workload shape) found that signal fires constantly with ZERO perceived
focus loss, with or without a reclaim mechanism reacting to it — a phantom signal, not a real steal.
See `process-docs/camoufox_lane/` for the exact mechanism name and the live-verification writeup.
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

# Launch the backfill subprocess, poll the focus-steal instrument concurrently until it exits, report
def focus_poll_smoke_workflow(limit: int | None) -> None:
    baseline_app = get_frontmost_app()
    print(f"Baseline frontmost app (expected throughout): {baseline_app}", file=sys.stderr)

    frontmost_samples: list[tuple[float, str]] = []
    stop_event = threading.Event()
    frontmost_thread = threading.Thread(target=poll_frontmost_loop, args=(frontmost_samples, stop_event))
    frontmost_thread.start()

    t_start = time.perf_counter()
    cmd = [PYTHON, str(BACKFILL_SCRIPT)]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    result = subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    wall_s = time.perf_counter() - t_start

    stop_event.set()
    frontmost_thread.join()

    report_path = write_report(baseline_app, frontmost_samples, result.returncode, wall_s)
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


# Background-thread loop: append (elapsed_s, app_name) samples until stop_event fires
def poll_frontmost_loop(samples: list[tuple[float, str]], stop_event: threading.Event) -> None:
    t0 = time.perf_counter()
    while not stop_event.is_set():
        app = get_frontmost_app()
        samples.append((round(time.perf_counter() - t0, 2), app))
        time.sleep(FOCUS_POLL_INTERVAL_S)


# Write the funnel + the instrument's tally + any-violation-sample report
def write_report(
    baseline_app: str, frontmost_samples: list[tuple[float, str]], returncode: int, wall_s: float,
) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"02_focus_poll_smoke_report_{ts}.md"

    counts: dict[str, int] = {}
    for _, app in frontmost_samples:
        counts[app] = counts.get(app, 0) + 1
    deviations = [(t, app) for t, app in frontmost_samples if app != baseline_app]

    lines = [
        f"## Focus-poll smoke ({ts})",
        f"- Backfill subprocess exit code: {returncode}",
        f"- Wall time: {wall_s:.1f}s",
        f"- Baseline (expected) frontmost app: `{baseline_app}`",
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
