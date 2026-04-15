#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import asyncio
import dataclasses
import sys

from stealth_config import DEFAULT_CONFIG, StealthConfig
from _stealth_browser import start_browser, run_engine
from _stealth_report import save_screenshot, print_summary, build_report, save_report
from engine_selectors import ENGINE_SELECTORS, HTTPX_ENGINES


# ORCHESTRATOR

# Run stealth test for one engine/query with given config, save report, optional screenshot
async def run_stealth_test(engine: str, query: str, config: StealthConfig, screenshot: bool) -> None:
    print(f"Engine: {engine} | Query: {query!r}", file=sys.stderr)
    print(f"Mode: {'headed' if not config.headless else 'headless'}", file=sys.stderr)

    cfg = ENGINE_SELECTORS[engine]
    browser, tab = await start_browser(config, cfg)
    screenshot_path = None
    detection = {"consent": False, "captcha": False, "zero_results": False, "error": None}
    results = []

    try:
        results, detection = await run_engine(tab, query, cfg, detection)
        if screenshot:
            screenshot_path = await save_screenshot(tab, engine)
    except Exception as e:
        detection["error"] = str(e)
        print(f"ERROR: {e}", file=sys.stderr)
    finally:
        await browser.stop()

    print_summary(engine, query, results, detection)
    report = build_report(engine, query, config, detection, results, screenshot_path, screenshot)
    report_path = save_report(engine, report)
    print(f"Report: {report_path}")


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
