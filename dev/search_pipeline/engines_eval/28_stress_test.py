#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import asyncio
import dataclasses
import json
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from duckduckgo_search import DDGS
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import PageCommands
from pydoll.commands.network_commands import NetworkCommands
from pydoll.protocol.network.types import CookieSameSite

from stealth_config import DEFAULT_CONFIG, StealthConfig, build_chrome_args, build_js_patches
from engine_selectors import ENGINE_SELECTORS, HTTPX_ENGINES

QUERIES_FILE = Path(__file__).parent.parent / "queries.txt"
REPORTS_DIR = Path(__file__).parent / "28_reports"
SESSION_BASE = str(Path.home() / ".searxng-mcp" / "stress-test")
PYDOLL_ENGINES = ["google", "bing", "brave", "startpage", "mojeek", "google scholar"]
HTTPX_ENGINE_LIST = sorted(HTTPX_ENGINES)
DOM_SETTLE_SECONDS = 0.0
CROSSREF_MAILTO = "stress-test@searxng-mcp.local"


@dataclass
class QueryResult:
    query: str
    engine: str
    result_count: int
    response_time: float
    error: Optional[str]
    first_title: str


# ORCHESTRATOR

# Run all engines in parallel, collect results, write summary report
async def run_stress_test(
    config: StealthConfig,
    limit: Optional[int],
    engine_filter: Optional[str],
    jitter: float,
) -> None:
    queries = _load_queries(limit)

    pydoll_engines = [e for e in PYDOLL_ENGINES if not engine_filter or e == engine_filter]
    httpx_engines = [e for e in HTTPX_ENGINE_LIST if not engine_filter or e == engine_filter]
    all_engines = pydoll_engines + httpx_engines

    total = len(queries) * len(all_engines)
    print(
        f"Loaded {len(queries)} queries | Engines: {len(all_engines)} | Total: {total}",
        file=sys.stderr,
    )

    wall_start = time.monotonic()

    outputs = await asyncio.gather(
        *[_run_pydoll_engine(e, queries, config, jitter) for e in pydoll_engines],
        *[_run_httpx_engine(e, queries) for e in httpx_engines],
        return_exceptions=True,
    )

    total_wall = time.monotonic() - wall_start

    results: list[QueryResult] = []
    timings: dict[str, float] = {}

    for engine, output in zip(all_engines, outputs):
        if isinstance(output, Exception):
            print(f"  [{engine}] engine-level crash — {output}", file=sys.stderr)
            timings[engine] = 0.0
        else:
            engine_results, engine_wall = output
            results.extend(engine_results)
            timings[engine] = engine_wall

    report = _build_report(results, len(queries), timings, total_wall)
    path = _save_report(report)
    print(f"\nReport: {path}")


# FUNCTIONS

# Parse queries.txt and return only @profile: general queries
def _load_queries(limit: Optional[int]) -> list[str]:
    text = QUERIES_FILE.read_text(encoding="utf-8")
    queries = []
    in_general = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "@profile: general":
            in_general = True
            continue
        if stripped.startswith("@profile:"):
            in_general = False
            continue
        if in_general and stripped and not stripped.startswith("#"):
            queries.append(stripped)

    return queries[:limit] if limit else queries


# Run all queries for one pydoll engine with a dedicated Chrome browser
async def _run_pydoll_engine(
    engine: str, queries: list[str], config: StealthConfig, jitter: float
) -> tuple[list[QueryResult], float]:
    results: list[QueryResult] = []
    wall_start = time.monotonic()
    browser = None

    try:
        browser = await _start_browser(engine, config)

        for q_idx, query in enumerate(queries, 1):
            if jitter > 0 and q_idx > 1:
                await asyncio.sleep(random.uniform(0, jitter))

            print(f"  [{engine}] [{q_idx}/{len(queries)}] {query[:40]!r}", file=sys.stderr)
            try:
                result = await _run_one_tab(browser, query, engine, config)
            except Exception as e:
                err_str = str(e)
                print(f"  [{engine}] browser-level error — {err_str[:80]}", file=sys.stderr)
                try:
                    await browser.stop()
                except Exception:
                    pass
                try:
                    browser = await _start_browser(engine, config)
                    result = await _run_one_tab(browser, query, engine, config)
                except Exception as e2:
                    result = QueryResult(query, engine, 0, 0.0, f"restart_failed: {str(e2)[:80]}", "")

            results.append(result)
            status = f"  [{engine}] {result.result_count} results ({result.response_time:.1f}s)"
            if result.error:
                status += f" | {result.error[:50]}"
            print(status, file=sys.stderr)

    finally:
        if browser:
            try:
                await browser.stop()
            except Exception:
                pass

    return results, time.monotonic() - wall_start


# Run all queries for one httpx engine (DuckDuckGo, Semantic Scholar, CrossRef)
async def _run_httpx_engine(engine: str, queries: list[str]) -> tuple[list[QueryResult], float]:
    results: list[QueryResult] = []
    wall_start = time.monotonic()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for q_idx, query in enumerate(queries, 1):
            print(f"  [{engine}] [{q_idx}/{len(queries)}] {query[:40]!r}", file=sys.stderr)
            result = await _run_one_httpx(client, engine, query)
            results.append(result)
            status = f"  [{engine}] {result.result_count} results ({result.response_time:.1f}s)"
            if result.error:
                status += f" | {result.error[:50]}"
            print(status, file=sys.stderr)

    return results, time.monotonic() - wall_start


# Build browser with engine-specific session dir and inject consent cookies
async def _start_browser(engine: str, config: StealthConfig):
    engine_slug = engine.replace(" ", "_")
    session_dir = f"{SESSION_BASE}/{engine_slug}"

    options = ChromiumOptions()
    options.headless = config.headless
    options.add_argument(f"--user-data-dir={session_dir}")
    options.block_popups = True
    options.block_notifications = True
    options.webrtc_leak_protection = config.webrtc_leak_protection
    options.browser_preferences = config.browser_preferences

    for arg in build_chrome_args(config):
        options.add_argument(arg)

    browser = Chrome(options)
    tab = await browser.start()
    await _inject_consent_cookies(tab)
    return browser


# Set Google/Scholar SOCS consent cookie via CDP
async def _inject_consent_cookies(tab) -> None:
    cookie = ENGINE_SELECTORS["google"]["consent_cookie"]
    await tab._execute_command(NetworkCommands.set_cookie(
        name=cookie["name"],
        value=cookie["value"],
        domain=cookie["domain"],
        path=cookie["path"],
        secure=cookie["secure"],
        same_site=CookieSameSite.LAX,
    ))


# Open tab (or isolated context when use_contexts=True), navigate, parse, close — return QueryResult
async def _run_one_tab(browser, query: str, engine: str, config: StealthConfig) -> QueryResult:
    cfg = ENGINE_SELECTORS[engine]
    start = time.monotonic()
    tab = None
    context_id = None

    try:
        if config.use_contexts:
            context_id = await browser.create_browser_context()
            tab = await browser.new_tab(browser_context_id=context_id)
        else:
            tab = await browser.new_tab()

        js = build_js_patches(config)
        await tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=js,
                run_immediately=True,
            )
        )

        url = cfg["url_fn"](query)
        await tab.go_to(url, timeout=30)
        current = await tab.current_url

        if cfg.get("captcha_path") and cfg["captcha_path"] in current:
            elapsed = time.monotonic() - start
            return QueryResult(query, engine, 0, elapsed, "CAPTCHA", "")

        if cfg.get("consent_domain") and cfg["consent_domain"] in current:
            elapsed = time.monotonic() - start
            return QueryResult(query, engine, 0, elapsed, "consent_redirect", "")

        if cfg.get("captcha_detect_js"):
            raw = await tab.execute_script(cfg["captcha_detect_js"])
            detected = _extract_nested(raw)
            if detected:
                elapsed = time.monotonic() - start
                return QueryResult(query, engine, 0, elapsed, "slider_captcha", "")

        await asyncio.sleep(DOM_SETTLE_SECONDS)
        items = await _parse_results(tab, cfg)
        elapsed = time.monotonic() - start
        first_title = items[0].get("title", "")[:60] if items else ""

        return QueryResult(query, engine, len(items), elapsed, None, first_title)

    except Exception as e:
        elapsed = time.monotonic() - start
        return QueryResult(query, engine, 0, elapsed, str(e)[:120], "")

    finally:
        if config.use_contexts and context_id:
            try:
                await browser.delete_browser_context(context_id)
            except Exception:
                pass
        elif tab:
            try:
                await tab.close()
            except Exception:
                pass


# Dispatch httpx query to the right engine implementation
async def _run_one_httpx(client: httpx.AsyncClient, engine: str, query: str) -> QueryResult:
    if engine == "duckduckgo":
        return await _query_duckduckgo(query)
    if engine == "semantic scholar":
        return await _query_semantic_scholar(client, query)
    if engine == "crossref":
        return await _query_crossref(client, query)
    return QueryResult(query, engine, 0, 0.0, f"unknown httpx engine: {engine}", "")


# Query DuckDuckGo via duckduckgo_search library (sync, wrapped in executor)
async def _query_duckduckgo(query: str) -> QueryResult:
    start = time.monotonic()
    try:
        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(
            None, lambda: list(DDGS().text(query, max_results=10))
        )
        elapsed = time.monotonic() - start
        first_title = items[0].get("title", "")[:60] if items else ""
        return QueryResult(query, "duckduckgo", len(items), elapsed, None, first_title)
    except Exception as e:
        elapsed = time.monotonic() - start
        return QueryResult(query, "duckduckgo", 0, elapsed, str(e)[:120], "")


# Query Semantic Scholar REST API
async def _query_semantic_scholar(client: httpx.AsyncClient, query: str) -> QueryResult:
    start = time.monotonic()
    try:
        resp = await client.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": query, "limit": 10},
        )
        resp.raise_for_status()
        items = resp.json().get("data", [])
        elapsed = time.monotonic() - start
        first_title = items[0].get("title", "")[:60] if items else ""
        return QueryResult(query, "semantic scholar", len(items), elapsed, None, first_title)
    except Exception as e:
        elapsed = time.monotonic() - start
        return QueryResult(query, "semantic scholar", 0, elapsed, str(e)[:120], "")


# Query CrossRef REST API (polite pool via mailto header)
async def _query_crossref(client: httpx.AsyncClient, query: str) -> QueryResult:
    start = time.monotonic()
    try:
        resp = await client.get(
            "https://api.crossref.org/works",
            params={"query": query, "rows": 10},
            headers={"mailto": CROSSREF_MAILTO},
        )
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
        elapsed = time.monotonic() - start
        titles = items[0].get("title", []) if items else []
        first_title = titles[0][:60] if titles else ""
        return QueryResult(query, "crossref", len(items), elapsed, None, first_title)
    except Exception as e:
        elapsed = time.monotonic() - start
        return QueryResult(query, "crossref", 0, elapsed, str(e)[:120], "")


# Execute parse_js and return list of result dicts
async def _parse_results(tab, cfg: dict) -> list[dict]:
    raw = await tab.execute_script(cfg["parse_js"])
    value = _extract_nested(raw)
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


# Extract value from nested CDP result structure
def _extract_nested(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Build full markdown report with summary, timing, failure timeline, full matrix
def _build_report(
    results: list[QueryResult],
    total_queries: int,
    timings: dict[str, float],
    total_wall: float,
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    engines = [e for e in (PYDOLL_ENGINES + HTTPX_ENGINE_LIST) if e in timings]

    by_engine: dict[str, list[QueryResult]] = {e: [] for e in engines}
    for r in results:
        if r.engine in by_engine:
            by_engine[r.engine].append(r)

    queries_ordered: list[str] = []
    seen: set[str] = set()
    for r in results:
        if r.query not in seen:
            seen.add(r.query)
            queries_ordered.append(r.query)

    lines = [
        "# Stress Test Report",
        f"Date: {timestamp}",
        f"Queries: {total_queries} | Engines: {len(engines)} | Total: {total_queries * len(engines)}",
        "",
        "## Summary per Engine",
        "",
        "| Engine | Success | Zero Results | Errors | Avg Time | Total URLs |",
        "|--------|---------|--------------|--------|----------|------------|",
    ]

    for engine in engines:
        ers = by_engine[engine]
        if not ers:
            continue
        success = sum(1 for r in ers if r.result_count > 0)
        zero = sum(1 for r in ers if r.result_count == 0 and not r.error)
        errors = sum(1 for r in ers if r.error)
        avg_time = sum(r.response_time for r in ers) / len(ers)
        total_urls = sum(r.result_count for r in ers)
        lines.append(f"| {engine} | {success} | {zero} | {errors} | {avg_time:.1f}s | {total_urls} |")

    lines += [
        "",
        "## Timing",
        "",
        "| Engine | Wall Clock | Queries | Avg/Query |",
        "|--------|-----------|---------|-----------|",
    ]

    for engine in engines:
        wall = timings.get(engine, 0.0)
        n = len(by_engine[engine])
        avg = wall / n if n else 0.0
        lines.append(f"| {engine} | {wall:.1f}s | {n} | {avg:.1f}s |")

    total_m = int(total_wall // 60)
    total_s = total_wall % 60
    lines.append(f"\nTotal wall clock: {total_m}m {total_s:.1f}s (parallel)")

    lines += [
        "",
        "## Failure Timeline",
        "",
        "| Engine | First Failure Query | Query # | Status |",
        "|--------|---------------------|---------|--------|",
    ]

    for engine in engines:
        ers = by_engine[engine]
        first_fail = None
        for idx, r in enumerate(ers, 1):
            if r.error or r.result_count == 0:
                first_fail = (idx, r)
                break
        if first_fail:
            idx, r = first_fail
            status = r.error if r.error else "zero_results"
            q_short = r.query[:40].replace("|", "\\|")
            lines.append(f"| {engine} | {q_short} | {idx} | {status[:60]} |")
        else:
            lines.append(f"| {engine} | — | — | — |")

    lines += [
        "",
        "## Full Matrix",
        "",
        "| # | Query | " + " | ".join(engines) + " |",
        "|---|-------|" + "|".join(["-------"] * len(engines)) + "|",
    ]

    lookup: dict[tuple, QueryResult] = {(r.query, r.engine): r for r in results}

    for q_idx, query in enumerate(queries_ordered, 1):
        cells = []
        for engine in engines:
            r = lookup.get((query, engine))
            if not r:
                cells.append("—")
            elif r.error:
                short_err = r.error[:20].replace("|", "\\|")
                cells.append(f"❌ {short_err}")
            else:
                cells.append(str(r.result_count))
        short_q = query[:35].replace("|", "\\|")
        lines.append(f"| {q_idx} | {short_q} | " + " | ".join(cells) + " |")

    return "\n".join(lines)


# Save report to 28_reports/stress_<timestamp>.md, return path string
def _save_report(report: str) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"stress_{timestamp}.md"
    path.write_text(report, encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stress test — all queries × 9 engines (parallel)")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--limit", type=int, default=None, help="Only first N queries")
    parser.add_argument("--engine", type=str, default=None, help="Only test this engine")
    parser.add_argument("--use-contexts", action="store_true", help="browser.new_context() per query (Brave tuning)")
    parser.add_argument("--canvas-noise", action="store_true", help="Enable canvas fingerprint noise")
    parser.add_argument("--jitter", type=float, default=0.0, help="Random delay between queries (seconds)")
    args = parser.parse_args()

    config = dataclasses.replace(
        DEFAULT_CONFIG,
        headless=not args.headed,
        use_contexts=args.use_contexts,
        patch_canvas_noise=args.canvas_noise,
    )
    asyncio.run(run_stress_test(config, args.limit, args.engine, args.jitter))
