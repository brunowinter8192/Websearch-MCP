"""Markdown report building and saving for 28_stress_test.py."""

# INFRASTRUCTURE
from datetime import datetime
from pathlib import Path

from _stress_types import QueryResult

REPORTS_DIR = Path(__file__).parent / "28_reports"


# Build full markdown report with summary, timing, failure timeline, full matrix
def build_report(
    results: list[QueryResult],
    total_queries: int,
    timings: dict[str, float],
    total_wall: float,
    engine_order: list[str],
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    engines = [e for e in engine_order if e in timings]

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
def save_report(report: str) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"stress_{timestamp}.md"
    path.write_text(report, encoding="utf-8")
    return str(path)
