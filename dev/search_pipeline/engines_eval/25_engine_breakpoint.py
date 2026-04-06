#!/usr/bin/env python3

# INFRASTRUCTURE
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

REPORTS_DIR = Path(__file__).parent / "25_reports"
SEARXNG_URL = "http://localhost:8080/search"
DELAY_BETWEEN_QUERIES = 3

TEST_QUERIES = [
    # Tech/Code (EN)
    "python asyncio best practices",
    "rust ownership borrow checker explained",
    "fastapi websocket reconnect handler",
    "docker compose health check restart policy",
    "git rebase vs merge workflow",
    "PostgreSQL query optimization composite index",
    "react server components vs client components",
    "nginx reverse proxy websocket configuration",
    # Science (EN)
    "transformer attention mechanism explained",
    "RLHF reinforcement learning human feedback",
    "vector database approximate nearest neighbor",
    "RAG retrieval augmented generation benchmark",
    "climate change carbon capture technology 2025",
    "epidemiology cohort study design methodology",
    # German
    "Bewerbung Lebenslauf Format Deutschland",
    "Mietvertrag Kündigungsfrist gesetzliche Regelung",
    "GmbH Gründung Kosten Schritte",
    "Krankenversicherung Vergleich gesetzlich privat",
    "Python Programmierung Anfänger Tutorial deutsch",
    "Datenschutz DSGVO Website Impressum",
    # Niche/Specific
    "crawl4ai stealth browser detection bypass",
    "SearXNG engine weight configuration",
    "tmux session management scripting",
    "trafilatura vs readability content extraction",
    "SPLADE sparse retrieval model implementation",
    # Broad/General
    "best programming language 2025",
    "how does DNS work",
    "quantum computing error correction",
    "kubernetes vs docker swarm comparison",
    "open source alternative to notion",
]


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
        print(f"    HTTP={row['status_code']} results={row['result_count']} time={row['response_time']}s {flag}", file=sys.stderr)
        rows.append(row)
        if qi < len(TEST_QUERIES):
            time.sleep(DELAY_BETWEEN_QUERIES)
    return rows


# Execute one SearXNG request for a single engine, return raw metrics
def single_query(engine: str, query: str, qi: int) -> dict:
    start = time.time()
    try:
        params = {
            "q": query,
            "format": "json",
            "language": "en",
            "pageno": 1,
            "engines": engine,
        }
        response = requests.get(SEARXNG_URL, params=params, timeout=20)
        elapsed = round(time.time() - start, 2)
        status_code = response.status_code

        if status_code != 200:
            return {
                "qi": qi, "query": query, "status_code": status_code,
                "result_count": 0, "response_time": elapsed,
                "unresponsive": [], "flag": f"HTTP_{status_code}",
                "raw_preview": response.text[:100],
            }

        raw_text = response.text
        data = response.json()
        results = data.get("results", [])
        unresponsive = data.get("unresponsive_engines", [])

        engine_in_unresponsive = any(
            (isinstance(e, list) and e[0] == engine) or
            (isinstance(e, dict) and e.get("name") == engine) or
            (isinstance(e, str) and e == engine)
            for e in unresponsive
        )

        flag = ""
        if engine_in_unresponsive:
            flag = "ENGINE_SUSPENDED"
        elif len(results) == 0:
            flag = "ZERO_RESULTS"

        raw_preview = raw_text[:100] if len(results) == 0 else ""

        return {
            "qi": qi, "query": query, "status_code": status_code,
            "result_count": len(results), "response_time": elapsed,
            "unresponsive": [str(e) for e in unresponsive],
            "flag": flag, "raw_preview": raw_preview,
        }
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        return {
            "qi": qi, "query": query, "status_code": 0,
            "result_count": 0, "response_time": elapsed,
            "unresponsive": [], "flag": f"EXCEPTION: {str(e)[:80]}",
            "raw_preview": "",
        }


# Analyse rows to find first failure, suspension, and recovery points
def find_breakpoints(rows: list) -> dict:
    first_zero = next((r["qi"] for r in rows if r["result_count"] == 0), None)
    first_suspended = next((r["qi"] for r in rows if r["flag"] == "ENGINE_SUSPENDED"), None)

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
        "first_suspended": first_suspended,
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

    if bp["first_suspended"]:
        lines.append(f"- **First ENGINE_SUSPENDED:** Query #{bp['first_suspended']} — \"{rows[bp['first_suspended'] - 1]['query']}\"")
    else:
        lines.append("- **First ENGINE_SUSPENDED:** Not detected")

    if bp["recovery_after_zero"]:
        lines.append(f"- **Recovery after first zero:** Query #{bp['recovery_after_zero']} — \"{rows[bp['recovery_after_zero'] - 1]['query']}\"")
    elif bp["first_zero"]:
        lines.append("- **Recovery after first zero:** No recovery observed")

    lines += [
        "",
        "## Detail",
        "",
        "| # | Query | HTTP | Results | Time(s) | Error/Flag |",
        "|---|-------|------|---------|---------|------------|",
    ]

    for r in rows:
        query_short = r["query"][:55].replace("|", "\\|")
        flag_cell = r["flag"] or "—"
        if r["unresponsive"]:
            unresponsive_str = str(r["unresponsive"])[:80]
            flag_cell += f" unresponsive={unresponsive_str}"
        if r["raw_preview"]:
            flag_cell += f" raw={r['raw_preview'][:60]!r}"
        lines.append(f"| {r['qi']} | {query_short} | {r['status_code']} | {r['result_count']} | {r['response_time']} | {flag_cell} |")

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
