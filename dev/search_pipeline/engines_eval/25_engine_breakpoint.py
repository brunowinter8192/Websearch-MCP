#!/usr/bin/env python3

# INFRASTRUCTURE
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from src.search.search_web import fetch_search_results

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent / "25_reports"
QUERIES_FILE = Path(__file__).parent.parent / "queries.txt"
DELAY_BETWEEN_QUERIES = 3


# Load general-profile queries from queries.txt
def load_queries() -> list[str]:
    queries = []
    current_profile = "general"
    with open(QUERIES_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('@profile:'):
                current_profile = line.split(':', 1)[1].strip()
                continue
            if current_profile == "general":
                queries.append(line)
    return queries


TEST_QUERIES = load_queries()


# ORCHESTRATOR
def run_breakpoint_test(engine: str) -> None:
    print(f"Testing engine: {engine} ({len(TEST_QUERIES)} queries)", file=sys.stderr)
    rows = collect_rows(engine)
    report = build_report(engine, rows)
    save_report(engine, report)


# FUNCTIONS

# Fire all test queries against one engine and return per-request result rows
def collect_rows(engine: str) -> list[dict]:
    rows = []
    for qi, query in enumerate(TEST_QUERIES, 1):
        print(f"  [{qi}/{len(TEST_QUERIES)}] {query[:60]}", file=sys.stderr)
        row = single_query(engine, query, qi)
        flag = row.get("flag") or "ok"
        print(f"    results={row['result_count']} time={row['response_time']}s {flag}", file=sys.stderr)
        rows.append(row)
        if qi < len(TEST_QUERIES):
            time.sleep(DELAY_BETWEEN_QUERIES)
    return rows


# Execute one fetch_search_results call for a single engine, return metrics
def single_query(engine: str, query: str, qi: int) -> dict:
    start = time.time()
    try:
        results = fetch_search_results(query, "", "en", None, engine, 1)
        elapsed = round(time.time() - start, 2)
        flag = "ZERO_RESULTS" if not results else ""
        return {
            "qi": qi,
            "query": query,
            "result_count": len(results),
            "response_time": elapsed,
            "flag": flag,
        }
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        logger.error("Engine %s query %d failed: %s", engine, qi, e)
        return {
            "qi": qi,
            "query": query,
            "result_count": 0,
            "response_time": elapsed,
            "flag": f"EXCEPTION: {str(e)[:80]}",
        }


# Analyse rows to find first failure and recovery points
def find_breakpoints(rows: list) -> dict:
    first_zero = next((r["qi"] for r in rows if r["result_count"] == 0), None)

    recovery_after_zero = None
    if first_zero:
        for r in rows:
            if r["qi"] > first_zero and r["result_count"] > 0:
                recovery_after_zero = r["qi"]
                break

    total_zero = sum(1 for r in rows if r["result_count"] == 0)
    total_ok = sum(1 for r in rows if r["result_count"] > 0)

    return {
        "first_zero": first_zero,
        "recovery_after_zero": recovery_after_zero,
        "total_zero": total_zero,
        "total_ok": total_ok,
    }


# Build markdown report with summary and detail table
def build_report(engine: str, rows: list) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    bp = find_breakpoints(rows)

    lines = [
        f"# Engine Breakpoint Test: {engine}",
        f"Date: {timestamp}",
        f"Total queries: {len(rows)} | Delay: {DELAY_BETWEEN_QUERIES}s between requests",
        "",
        "## Summary",
        "",
        f"- **Results OK:** {bp['total_ok']}/{len(rows)}",
        f"- **Zero results:** {bp['total_zero']}/{len(rows)}",
    ]

    if bp["first_zero"]:
        lines.append(f"- **First zero result:** Query #{bp['first_zero']} — \"{rows[bp['first_zero'] - 1]['query']}\"")
    else:
        lines.append("- **First zero result:** None — all queries returned results")

    if bp["recovery_after_zero"]:
        lines.append(f"- **Recovery after first zero:** Query #{bp['recovery_after_zero']} — \"{rows[bp['recovery_after_zero'] - 1]['query']}\"")
    elif bp["first_zero"]:
        lines.append("- **Recovery after first zero:** No recovery observed")

    lines += [
        "",
        "## Detail",
        "",
        "| # | Query | Results | Time(s) | Error/Flag |",
        "|---|-------|---------|---------|------------|",
    ]

    for r in rows:
        query_short = r["query"][:55].replace("|", "\\|")
        flag_cell = r["flag"] or "—"
        lines.append(f"| {r['qi']} | {query_short} | {r['result_count']} | {r['response_time']} | {flag_cell} |")

    return "\n".join(lines)


# Save report to 25_reports/<engine>_<timestamp>.md
def save_report(engine: str, report: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_engine = engine.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{safe_engine}_{timestamp}.md"
    path.write_text(report, encoding="utf-8")
    print(f"Report saved: {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: 25_engine_breakpoint.py <engine>", file=sys.stderr)
        print(f"Engines: google, bing, mojeek, brave, startpage, duckduckgo, google scholar, semantic scholar, crossref", file=sys.stderr)
        sys.exit(1)
    run_breakpoint_test(sys.argv[1])
