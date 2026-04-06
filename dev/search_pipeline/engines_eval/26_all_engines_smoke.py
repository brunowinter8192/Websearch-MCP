#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from src.search.search_web import fetch_search_results

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

REPORTS_DIR = Path(__file__).parent / "26_reports"
QUERIES_FILE = Path(__file__).parent.parent / "queries.txt"
DELAY_BETWEEN_ENGINES = 3
DELAY_BETWEEN_QUERIES = 5

ENGINES = [
    "google",
    "bing",
    "brave",
    "startpage",
    "mojeek",
    "duckduckgo",
    "google scholar",
    "semantic scholar",
    "crossref",
]


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


# ORCHESTRATOR

# Run all queries against all engines, build and save report
def run_smoke_test(limit: int = 0) -> None:
    queries = load_queries()
    if limit > 0:
        queries = queries[:limit]
    print(f"Smoke test: {len(queries)} queries x {len(ENGINES)} engines", file=sys.stderr)
    results = collect_all_results(queries)
    report = build_report(results, queries)
    save_report(report)


# FUNCTIONS

# Collect results for every (query, engine) combination
def collect_all_results(queries: list[str]) -> dict:
    results = {}
    total = len(queries) * len(ENGINES)
    done = 0

    for qi, query in enumerate(queries, 1):
        results[query] = {}
        for ei, engine in enumerate(ENGINES):
            done += 1
            print(f"  [{done}/{total}] {engine} | {query[:50]}", file=sys.stderr)
            row = query_engine(engine, query)
            results[query][engine] = row
            flag = row["flag"] or "ok"
            print(f"    results={row['result_count']} time={row['response_time']}s {flag}", file=sys.stderr)
            if ei < len(ENGINES) - 1:
                time.sleep(DELAY_BETWEEN_ENGINES)

        if qi < len(queries):
            time.sleep(DELAY_BETWEEN_QUERIES)

    return results


# Run fetch_search_results for one (engine, query) pair and return metrics row
def query_engine(engine: str, query: str) -> dict:
    start = time.time()
    try:
        results = fetch_search_results(query, "", "en", None, engine, 1)
        elapsed = round(time.time() - start, 2)
        sample_url = results[0]["url"] if results else ""
        return {
            "result_count": len(results),
            "response_time": elapsed,
            "sample_url": sample_url,
            "flag": "ZERO_RESULTS" if not results else "",
        }
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        logger.error("Engine %s failed for query %r: %s", engine, query, e)
        return {
            "result_count": 0,
            "response_time": elapsed,
            "sample_url": "",
            "flag": f"EXCEPTION: {str(e)[:80]}",
        }


# Build summary stats per engine across all queries
def build_engine_summary(results: dict, queries: list[str]) -> list[dict]:
    summary = []
    for engine in ENGINES:
        queries_ok = 0
        queries_zero = 0
        total_urls = 0
        for query in queries:
            row = results[query][engine]
            if row["result_count"] > 0:
                queries_ok += 1
                total_urls += row["result_count"]
            else:
                queries_zero += 1
        avg = total_urls / queries_ok if queries_ok > 0 else 0.0
        summary.append({
            "engine": engine,
            "queries_ok": queries_ok,
            "queries_zero": queries_zero,
            "total_urls": total_urls,
            "avg_results": avg,
        })
    return summary


# Build full markdown report
def build_report(results: dict, queries: list[str]) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = build_engine_summary(results, queries)

    lines = [
        "# All-Engines Smoke Test",
        f"Date: {timestamp}",
        f"Queries: {len(queries)} | Engines: {len(ENGINES)}",
        "",
        "## Summary Table",
        "",
        "| Engine | Queries OK | Queries Zero | Total URLs | Avg Results/Query |",
        "|--------|-----------|-------------|------------|-------------------|",
    ]

    for s in summary:
        lines.append(
            f"| {s['engine']} | {s['queries_ok']} | {s['queries_zero']} | {s['total_urls']} | {s['avg_results']:.1f} |"
        )

    lines += ["", "## Per-Query Detail", ""]

    for qi, query in enumerate(queries, 1):
        lines.append(f'### Query {qi}: "{query}"')
        lines.append("")
        lines.append("| Engine | Results | Time(s) | Sample URL |")
        lines.append("|--------|---------|---------|------------|")
        for engine in ENGINES:
            row = results[query][engine]
            sample = row["sample_url"] or "—"
            flag_suffix = f" `{row['flag']}`" if row["flag"] else ""
            lines.append(
                f"| {engine} | {row['result_count']}{flag_suffix} | {row['response_time']} | {sample} |"
            )
        lines.append("")

    return "\n".join(lines)


# Save report to 26_reports/<timestamp>.md
def save_report(report: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"smoke_{timestamp}.md"
    path.write_text(report, encoding="utf-8")
    print(f"Report saved: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all-engines smoke test")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit to first N queries (0 = all)")
    args = parser.parse_args()
    run_smoke_test(limit=args.limit)
