"""Per-engine query execution for 28_stress_test.py."""

# INFRASTRUCTURE
import sys
import time

import httpx

from stealth_config import StealthConfig
from _stress_types import QueryResult
from _stress_browser import start_browser, run_one_tab

CROSSREF_MAILTO = "stress-test@searxng-mcp.local"


# Run all queries for one pydoll engine with a dedicated Chrome browser
async def run_pydoll_engine(
    engine: str, queries: list[str], config: StealthConfig
) -> tuple[list[QueryResult], float]:
    results: list[QueryResult] = []
    wall_start = time.monotonic()
    browser = None

    try:
        browser = await start_browser(engine, config)

        for q_idx, query in enumerate(queries, 1):
            print(f"  [{engine}] [{q_idx}/{len(queries)}] {query[:40]!r}", file=sys.stderr)
            try:
                result = await run_one_tab(browser, query, engine, config)
            except Exception as e:
                err_str = str(e)
                print(f"  [{engine}] browser-level error — {err_str[:80]}", file=sys.stderr)
                try:
                    await browser.stop()
                except Exception:
                    pass
                try:
                    browser = await start_browser(engine, config)
                    result = await run_one_tab(browser, query, engine, config)
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


# Run all queries for one httpx engine
async def run_httpx_engine(engine: str, queries: list[str]) -> tuple[list[QueryResult], float]:
    results: list[QueryResult] = []
    wall_start = time.monotonic()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for q_idx, query in enumerate(queries, 1):
            print(f"  [{engine}] [{q_idx}/{len(queries)}] {query[:40]!r}", file=sys.stderr)
            result = await run_one_httpx(client, engine, query)
            results.append(result)
            status = f"  [{engine}] {result.result_count} results ({result.response_time:.1f}s)"
            if result.error:
                status += f" | {result.error[:50]}"
            print(status, file=sys.stderr)

    return results, time.monotonic() - wall_start


# Dispatch httpx query to the right engine implementation
async def run_one_httpx(client: httpx.AsyncClient, engine: str, query: str) -> QueryResult:
    if engine == "crossref":
        return await _query_crossref(client, query)
    return QueryResult(query, engine, 0, 0.0, f"unknown httpx engine: {engine}", "")


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
