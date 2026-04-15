"""Report and screenshot functions for 27_stealth_test.py."""

# INFRASTRUCTURE
import dataclasses
import sys
from datetime import datetime
from pathlib import Path

from stealth_config import StealthConfig

REPORTS_DIR = Path(__file__).parent / "27_reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
REPORTS_SUBDIR = REPORTS_DIR / "reports"


# Take screenshot and save to screenshots subdir, return path string
async def save_screenshot(tab, engine: str) -> str:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_engine = engine.replace(" ", "_")
    path = SCREENSHOTS_DIR / f"{safe_engine}_{timestamp}.png"
    await tab.take_screenshot(path=str(path))
    print(f"Screenshot: {path}", file=sys.stderr)
    return str(path)


# Print compact summary to stdout
def print_summary(engine: str, query: str, results: list, detection: dict) -> None:
    print(f"\n=== {engine} | {query!r} ===")
    print(f"Results: {len(results)}")
    for k, v in detection.items():
        if v:
            print(f"  {k}: {v}")
    for i, r in enumerate(results[:3], 1):
        print(f"  {i}. {r.get('title', '')[:60]}")
        print(f"     {r.get('url', '')}")


# Build full markdown report
def build_report(
    engine: str,
    query: str,
    config: StealthConfig,
    detection: dict,
    results: list,
    screenshot_path: str | None,
    screenshot_requested: bool,
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = "headed" if not config.headless else "headless"
    screenshot_label = "yes" if screenshot_path else ("requested but failed" if screenshot_requested else "no")

    lines = [
        "# Stealth Test Report",
        f"Date: {timestamp}",
        f'Engine: {engine} | Query: "{query}"',
        f"Mode: {mode} | Screenshot: {screenshot_label}",
        "",
        "## Config Used",
        "",
        "| Setting | Value |",
        "|---------|-------|",
    ]

    cfg_dict = dataclasses.asdict(config)
    for key, value in cfg_dict.items():
        if isinstance(value, (dict, list)) and len(str(value)) > 80:
            display = str(value)[:80] + "…"
        else:
            display = str(value)
        display = display.replace("|", "\\|")
        lines.append(f"| {key} | {display} |")

    consent_label = "Yes" if detection["consent"] else "No"
    captcha_label = "Yes" if detection["captcha"] else "No"
    zero_label = "Yes" if detection["zero_results"] else "No"
    error_label = detection["error"] or "None"

    lines += [
        "",
        "## Detection",
        "",
        "| Check | Result |",
        "|-------|--------|",
        f"| Consent Page | {consent_label} |",
        f"| CAPTCHA | {captcha_label} |",
        f"| Zero Results | {zero_label} |",
        f"| Error | {error_label} |",
        "",
        f"## Results ({len(results)} URLs)",
        "",
        "| # | Title | URL |",
        "|---|-------|-----|",
    ]

    for idx, r in enumerate(results, 1):
        title = r.get("title", "")[:80].replace("|", "\\|")
        url = r.get("url", "").replace("|", "\\|")
        lines.append(f"| {idx} | {title} | {url} |")

    if not results:
        lines.append("| — | — | — |")

    return "\n".join(lines)


# Save report to 27_reports/reports/<engine>_<timestamp>.md, return path
def save_report(engine: str, report: str) -> str:
    REPORTS_SUBDIR.mkdir(parents=True, exist_ok=True)
    safe_engine = engine.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_SUBDIR / f"{safe_engine}_{timestamp}.md"
    path.write_text(report, encoding="utf-8")
    return str(path)
