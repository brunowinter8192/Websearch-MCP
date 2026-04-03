#!/usr/bin/env python3

# INFRASTRUCTURE
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.searxng.search_web import fetch_search_results

REPORTS_DIR = Path(__file__).parent / "10_reports"
DELAY_BETWEEN_QUERIES = 2
TOP_CONSENSUS_N = 20

TEST_QUERIES = [
    "python asyncio best practices",
    "machine learning evaluation metrics NDCG",
    "Bewerbung Lebenslauf Format Deutschland",
    "climate change carbon capture technology",
    "rust ownership borrow checker explained",
    "docker kubernetes container orchestration",
    "transformer architecture attention mechanism",
    "PostgreSQL query optimization index",
    "Bundesliga Transfermarkt aktuell",
    "quantum computing error correction",
    "react hooks state management",
    "epidemiology study design cohort",
    "fastapi async database connection pool",
]


# ORCHESTRATOR
def run_consensus_eval():
    engine_stats: dict = defaultdict(lambda: {
        "total": 0, "consensus": 0, "unique": 0,
        "positions": [], "top20_coverage": 0
    })
    evaluated = 0

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] {query}", file=sys.stderr)
        try:
            results = fetch_search_results(query, "general", "en", None, None, 1)
        except Exception as e:
            print(f"  SKIP: {e}", file=sys.stderr)
            continue

        if results:
            accumulate_engine_stats(results, engine_stats)
            evaluated += 1

        time.sleep(DELAY_BETWEEN_QUERIES)

    report = build_report(engine_stats, evaluated)
    save_report(report)


# FUNCTIONS

# Accumulate per-engine consensus metrics from one query's result set
def accumulate_engine_stats(results: list, engine_stats: dict) -> None:
    url_engines: dict = defaultdict(list)
    engine_urls: dict = defaultdict(list)

    for pos, result in enumerate(results, 1):
        url = result.get("url", "")
        if not url:
            continue
        for engine in result.get("engines", []):
            url_engines[url].append(engine)
            engine_urls[engine].append((url, pos))

    consensus_urls = {url for url, engs in url_engines.items() if len(engs) >= 2}

    top20_consensus: list = []
    seen: set = set()
    for result in results:
        url = result.get("url", "")
        if url in consensus_urls and url not in seen:
            top20_consensus.append(url)
            seen.add(url)
        if len(top20_consensus) >= TOP_CONSENSUS_N:
            break
    top20_set = set(top20_consensus)

    all_engine_url_sets: dict = {
        eng: {url for url, _ in urls} for eng, urls in engine_urls.items()
    }

    for engine, url_pos_list in engine_urls.items():
        url_set = {url for url, _ in url_pos_list}
        positions = [pos for _, pos in url_pos_list]

        other_urls: set = set()
        for other_eng, other_set in all_engine_url_sets.items():
            if other_eng != engine:
                other_urls |= other_set

        engine_stats[engine]["total"] += len(url_set)
        engine_stats[engine]["consensus"] += sum(1 for url in url_set if url in consensus_urls)
        engine_stats[engine]["unique"] += len(url_set - other_urls)
        engine_stats[engine]["positions"].extend(positions)
        engine_stats[engine]["top20_coverage"] += len(url_set & top20_set)


# Build markdown report from aggregated engine stats
def build_report(engine_stats: dict, query_count: int) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    sorted_engines = sorted(
        engine_stats.items(),
        key=lambda x: x[1]["consensus"] / x[1]["total"] if x[1]["total"] > 0 else 0,
        reverse=True,
    )

    lines = [
        "# Engine Consensus Report",
        f"Date: {timestamp}",
        f"Queries evaluated: {query_count}",
        "",
        "## Per-Engine Metrics",
        "",
        "| Engine | Total URLs | Consensus Rate | Unique URLs | Avg Position | Top-20 Coverage |",
        "|--------|-----------|----------------|-------------|--------------|-----------------|",
    ]

    for engine, stats in sorted_engines:
        total = stats["total"]
        consensus = stats["consensus"]
        unique = stats["unique"]
        positions = stats["positions"]
        top20 = stats["top20_coverage"]

        consensus_rate = f"{consensus / total * 100:.0f}%" if total > 0 else "—"
        avg_pos = f"{sum(positions) / len(positions):.1f}" if positions else "—"

        lines.append(f"| {engine} | {total} | {consensus_rate} | {unique} | {avg_pos} | {top20} |")

    lines += [
        "",
        "## Metric Definitions",
        "",
        "- **Total URLs**: Unique URLs returned across all queries",
        "- **Consensus Rate**: % of engine's URLs that also appeared in ≥1 other engine's results",
        "- **Unique URLs**: URLs returned exclusively by this engine (no other engine found them)",
        "- **Avg Position**: Mean position in combined ranking across all results",
        "- **Top-20 Coverage**: URLs contributed to the top-20 consensus results across all queries",
    ]

    return "\n".join(lines)


# Save report to 10_reports directory
def save_report(report: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"consensus_report_{timestamp}.md"
    report_path.write_text(report)
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    run_consensus_eval()
