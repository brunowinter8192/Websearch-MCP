#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import asyncio
import dataclasses
import json
import sys
from datetime import datetime
from pathlib import Path

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import PageCommands
from pydoll.commands.network_commands import NetworkCommands
from pydoll.protocol.network.types import CookieSameSite

from stealth_config import DEFAULT_CONFIG, StealthConfig, build_chrome_args, build_js_patches
from engine_selectors import ENGINE_SELECTORS, HTTPX_ENGINES

REPORTS_DIR = Path(__file__).parent / "27_reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
REPORTS_SUBDIR = REPORTS_DIR / "reports"
SESSION_DIR = str(Path.home() / ".searxng-mcp" / "stealth-test-session")
MAX_WAIT_CYCLES = 15
WAIT_INTERVAL = 1.0
SLEEP_WAIT = 3.0


# ORCHESTRATOR

# Run stealth test for one engine/query with given config, save report, optional screenshot
async def run_stealth_test(engine: str, query: str, config: StealthConfig, screenshot: bool) -> None:
    print(f"Engine: {engine} | Query: {query!r}", file=sys.stderr)
    print(f"Mode: {'headed' if not config.headless else 'headless'}", file=sys.stderr)

    cfg = ENGINE_SELECTORS[engine]
    browser, tab = await _start_browser(config, cfg)
    screenshot_path = None
    detection = {"consent": False, "captcha": False, "zero_results": False, "error": None}
    results = []

    try:
        results, detection = await _run_engine(tab, query, cfg, detection)
        if screenshot:
            screenshot_path = await _save_screenshot(tab, engine)
    except Exception as e:
        detection["error"] = str(e)
        print(f"ERROR: {e}", file=sys.stderr)
    finally:
        await browser.stop()

    _print_summary(engine, query, results, detection)
    report = _build_report(engine, query, config, detection, results, screenshot_path, screenshot)
    report_path = _save_report(engine, report)
    print(f"Report: {report_path}")


# FUNCTIONS

# Build ChromiumOptions from config and start browser, return (browser, tab)
async def _start_browser(config: StealthConfig, engine_cfg: dict):
    options = ChromiumOptions()
    options.headless = config.headless
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    options.block_popups = True
    options.block_notifications = True
    options.webrtc_leak_protection = config.webrtc_leak_protection
    options.browser_preferences = config.browser_preferences

    for arg in build_chrome_args(config):
        options.add_argument(arg)

    browser = Chrome(options)
    tab = await browser.start()
    await _apply_js_patches(tab, config)
    await _inject_consent_cookie(tab, engine_cfg)
    return browser, tab


# Inject consent cookie from engine config via CDP if present
async def _inject_consent_cookie(tab, engine_cfg: dict) -> None:
    cookie = engine_cfg.get("consent_cookie")
    if not cookie:
        return
    await tab._execute_command(NetworkCommands.set_cookie(
        name=cookie["name"],
        value=cookie["value"],
        domain=cookie["domain"],
        path=cookie["path"],
        secure=cookie["secure"],
        same_site=CookieSameSite.LAX,
    ))


# Inject fingerprint patch script via Page.addScriptToEvaluateOnNewDocument
async def _apply_js_patches(tab, config: StealthConfig) -> None:
    js = build_js_patches(config)
    await tab._execute_command(
        PageCommands.add_script_to_evaluate_on_new_document(
            source=js,
            run_immediately=True,
        )
    )


# Navigate engine, handle consent, wait for results, parse
async def _run_engine(tab, query: str, cfg: dict, detection: dict) -> tuple[list, dict]:
    url = cfg["url_fn"](query)

    await tab.go_to(url, timeout=30)
    current = await tab.current_url

    # Consent page detection (Google/Scholar) — cookie injection should have prevented this
    if cfg.get("consent_domain") and cfg["consent_domain"] in current:
        detection["consent"] = True
        print(f"CONSENT PAGE detected — cookie injection may have failed", file=sys.stderr)

    # CAPTCHA detection
    if cfg.get("captcha_path") and cfg["captcha_path"] in current:
        detection["captcha"] = True
        print(f"CAPTCHA detected", file=sys.stderr)
        return [], detection

    # Wait for results
    found = await _wait_for_results(tab, cfg)
    if not found:
        print(f"Timeout — no results loaded", file=sys.stderr)

    # Parse results
    results = await _parse_results(tab, cfg)
    if not results:
        detection["zero_results"] = True

    return results, detection


# Wait for results using engine's strategy (JS poll or fixed sleep)
async def _wait_for_results(tab, cfg: dict) -> bool:
    if cfg["wait"] == "sleep":
        await asyncio.sleep(SLEEP_WAIT)
        return True

    for _ in range(MAX_WAIT_CYCLES):
        raw = await tab.execute_script(cfg["wait_js"])
        count = _extract_nested(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(WAIT_INTERVAL)
    return False


# Run parse JS and return list of result dicts
async def _parse_results(tab, cfg: dict) -> list[dict]:
    raw = await tab.execute_script(cfg["parse_js"])
    value = _extract_nested(raw)
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


# Take screenshot and save to screenshots subdir, return path string
async def _save_screenshot(tab, engine: str) -> str:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_engine = engine.replace(" ", "_")
    path = SCREENSHOTS_DIR / f"{safe_engine}_{timestamp}.png"
    await tab.take_screenshot(path=str(path))
    print(f"Screenshot: {path}", file=sys.stderr)
    return str(path)


# Extract value from nested CDP result structure
def _extract_nested(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Print compact summary to stdout
def _print_summary(engine: str, query: str, results: list, detection: dict) -> None:
    print(f"\n=== {engine} | {query!r} ===")
    print(f"Results: {len(results)}")
    for k, v in detection.items():
        if v:
            print(f"  {k}: {v}")
    for i, r in enumerate(results[:3], 1):
        print(f"  {i}. {r.get('title', '')[:60]}")
        print(f"     {r.get('url', '')}")


# Build full markdown report
def _build_report(
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
def _save_report(engine: str, report: str) -> str:
    REPORTS_SUBDIR.mkdir(parents=True, exist_ok=True)
    safe_engine = engine.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_SUBDIR / f"{safe_engine}_{timestamp}.md"
    path.write_text(report, encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stealth config test — one engine, one query")
    parser.add_argument("engine", help="Engine name: google, bing, 'google scholar' (active); brave requires un-commenting in engine_selectors.py")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--screenshot", action="store_true", help="Save screenshot to 27_reports/screenshots/")
    args = parser.parse_args()

    engine = args.engine.lower()

    if engine in HTTPX_ENGINES:
        print(f"'{engine}' uses httpx — no browser involved, cannot stealth-test.", file=sys.stderr)
        stealth_engines = [k for k, v in ENGINE_SELECTORS.items() if v.get("type") != "httpx"]
        print(f"Stealth-testable engines: {', '.join(stealth_engines)}", file=sys.stderr)
        sys.exit(1)

    if engine not in ENGINE_SELECTORS or ENGINE_SELECTORS[engine].get("type") == "httpx":
        print(f"Unknown engine: {engine!r}", file=sys.stderr)
        available = [k for k, v in ENGINE_SELECTORS.items() if v.get("type") != "httpx"]
        print(f"Available: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    config = dataclasses.replace(DEFAULT_CONFIG, headless=not args.headed)
    asyncio.run(run_stealth_test(engine, args.query, config, args.screenshot))
