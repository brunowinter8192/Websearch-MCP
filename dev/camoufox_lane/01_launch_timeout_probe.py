#!/usr/bin/env python3
"""Camoufox launch-timeout enforcement probe — camoufox_lane budget-grounding area, milestone 1.

Sends an absurdly low launch timeout (1ms) through the SAME chain
src/scraper/camoufox_scrape.py uses in production (kwargs -> camoufox.launch_options ->
AsyncCamoufox(from_options=...)), to determine whether the launch-timeout kwarg the production
code forwards is actually enforced at runtime, or silently ignored. A second run repeats the exact
same chain with the production default (30000ms) as a control, confirming a clean launch through the
same probe path (not a different code path that happens to also launch Camoufox).

Dev scripts may not import from src/ — PROD_KWARGS below is a literal copy of the kwargs
camoufox_scrape.py's _build_camoufox_kwargs() builds (same headless/os/block_images/timeout
values), not a re-derivation; kept in sync by inspection, not by import.
"""

# INFRASTRUCTURE
import asyncio
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from camoufox import launch_options
from camoufox.async_api import AsyncCamoufox

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"

# Mirrors src/scraper/camoufox_scrape.py's _PLAYWRIGHT_DEFAULT_TIMEOUT_MS (the production value
# passed as the "timeout" kwarg through launch_options()/AsyncCamoufox).
PROD_TIMEOUT_MS = 30000
LOW_TIMEOUT_MS = 1

# Mirrors src/scraper/camoufox_scrape.py's _build_camoufox_kwargs(block_images=False) — same
# headless/os/block_images values; "timeout" is overridden per run below.
PROD_KWARGS = {
    "headless": False,
    "os": "macos",
    "block_images": False,
}


# ORCHESTRATOR
async def run_probe() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    low_result = await attempt_launch(LOW_TIMEOUT_MS, "LOW (1ms)")
    control_result = await attempt_launch(PROD_TIMEOUT_MS, "CONTROL (30000ms, production default)")
    report_path = write_report(low_result, control_result)
    print(f"\nReport: {report_path}", file=sys.stderr)


# FUNCTIONS

# Resolve launch_options with the given timeout override, launch AsyncCamoufox through the SAME
# chain camoufox_scrape.py's _acquire() uses, observe the outcome. Returns dict: timeout_ms,
# outcome ("launched"|"exception"), wall_s, exception_type, exception_str, traceback.
async def attempt_launch(timeout_ms: int, label: str) -> dict:
    kwargs = {**PROD_KWARGS, "timeout": timeout_ms}
    print(f"=== {label} ===", file=sys.stderr)
    t0 = time.perf_counter()
    try:
        resolved = await asyncio.get_event_loop().run_in_executor(
            None, lambda: launch_options(**kwargs)
        )
        async with AsyncCamoufox(from_options=resolved) as browser:
            page = await browser.new_page()
            await page.close()
        wall = time.perf_counter() - t0
        print(f"  launched cleanly in {wall:.3f}s", file=sys.stderr)
        return {
            "label": label, "timeout_ms": timeout_ms, "outcome": "launched", "wall_s": round(wall, 3),
            "exception_type": None, "exception_str": None, "traceback": None,
        }
    except Exception as e:
        wall = time.perf_counter() - t0
        tb = traceback.format_exc()
        print(f"  raised {type(e).__name__} after {wall:.3f}s: {e}", file=sys.stderr)
        return {
            "label": label, "timeout_ms": timeout_ms, "outcome": "exception", "wall_s": round(wall, 3),
            "exception_type": type(e).__name__, "exception_str": str(e), "traceback": tb,
        }


# Write the markdown report and return its path
def write_report(low: dict, control: dict) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"01_launch_timeout_probe_{ts}.md"
    lines = [
        f"# Camoufox Launch-Timeout Enforcement Probe — {ts}",
        "",
        "LOW run: timeout=1ms through the production chain (kwargs -> camoufox.launch_options -> "
        "AsyncCamoufox(from_options=...)). CONTROL run: same chain, timeout=30000ms (the production "
        "default, _PLAYWRIGHT_DEFAULT_TIMEOUT_MS in src/scraper/camoufox_scrape.py).",
        "",
        "## Results",
        "",
        "| Run | timeout_ms | outcome | wall time | exception type |",
        "|---|---|---|---|---|",
        f"| {low['label']} | {low['timeout_ms']} | {low['outcome']} | {low['wall_s']}s | {low['exception_type']} |",
        f"| {control['label']} | {control['timeout_ms']} | {control['outcome']} | {control['wall_s']}s | {control['exception_type']} |",
        "",
        "## LOW run — verbatim traceback",
        "",
        "```",
        low["traceback"] or "(no exception raised)",
        "```",
        "",
        "## CONTROL run",
        "",
        f"outcome={control['outcome']}, wall={control['wall_s']}s",
    ]
    if control["traceback"]:
        lines += ["", "```", control["traceback"], "```"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    asyncio.run(run_probe())
