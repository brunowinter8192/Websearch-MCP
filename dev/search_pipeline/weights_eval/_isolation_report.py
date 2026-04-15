"""Report building and saving for 11_engine_isolation.py."""

# INFRASTRUCTURE
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "11_reports"


# Build overlap_matrix.md: per-engine summary + unique ranking + Jaccard matrix
def build_overlap_report(summary: dict, jaccard: dict, engines: list, test_queries: list, top_n: int) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    sorted_by_unique = sorted(engines, key=lambda e: summary[e]["unique_urls"], reverse=True)
    sorted_by_consensus = sorted(engines, key=lambda e: summary[e]["consensus_rate"], reverse=True)

    lines = [
        "# Engine Isolation — Overlap Matrix",
        f"Date: {timestamp}",
        f"Queries evaluated: {len(test_queries)}",
        f"Engines tested: {len(engines)}",
        f"Max URLs per engine per query: {top_n}",
        "",
        "## Per-Engine Summary",
        "",
        "| Engine | Avg URLs/Query | Total Unique URLs | Consensus Rate | Avg Position |",
        "|--------|---------------|-------------------|----------------|--------------|",
    ]

    for engine in sorted_by_consensus:
        s = summary[engine]
        avg_u = f"{s['avg_urls_per_query']:.1f}"
        unique = s["unique_urls"]
        cr = f"{s['consensus_rate'] * 100:.0f}%"
        avg_p = f"{s['avg_position']:.1f}" if s["avg_position"] > 0 else "—"
        lines.append(f"| {engine} | {avg_u} | {unique} | {cr} | {avg_p} |")

    lines += [
        "",
        "## Top Unique-Value Engines",
        "",
        "Engines ranked by URLs found exclusively by them (no other engine returned the same URL for the same query).",
        "",
        "| Rank | Engine | Unique URLs |",
        "|------|--------|-------------|",
    ]

    for rank, engine in enumerate(sorted_by_unique, 1):
        lines.append(f"| {rank} | {engine} | {summary[engine]['unique_urls']} |")

    lines += [
        "",
        "## Pairwise Jaccard Similarity Matrix",
        "",
        "Jaccard = |A ∩ B| / |A ∪ B| using global URL sets across all queries. Higher = more overlap.",
        "",
    ]

    short_names = {e: e[:10] for e in engines}
    header_cells = ["Engine"] + [short_names[e] for e in engines]
    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("|" + "---------|" * len(header_cells))

    for a in engines:
        row = [short_names[a]]
        for b in engines:
            val = jaccard[a][b]
            row.append("—" if a == b else f"{val:.2f}")
        lines.append("| " + " | ".join(row) + " |")

    lines += [
        "",
        "## Metric Definitions",
        "",
        "- **Avg URLs/Query**: Mean number of URLs returned by this engine per query",
        "- **Total Unique URLs**: URLs found only by this engine (no other engine returned them for the same query)",
        "- **Consensus Rate**: % of engine's URLs also returned by ≥1 other engine for the same query",
        "- **Avg Position**: Mean position in the engine's result list across all queries",
    ]

    return "\n".join(lines)


# Build engine_<name>.md: all queries with top-N URLs and positions for one engine
def build_engine_report(engine: str, engine_results: dict, test_queries: list, top_n: int) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Engine: {engine}",
        f"Date: {timestamp}",
        f"Queries: {len(test_queries)} | Max URLs per query: {top_n}",
        "",
    ]

    for qi, query in enumerate(test_queries):
        urls = engine_results[engine].get(qi, [])
        lines.append(f"## Query {qi + 1}: {query}")
        lines.append("")
        if not urls:
            lines.append("_No results returned._")
        else:
            lines.append("| Pos | URL |")
            lines.append("|-----|-----|")
            for pos, url in enumerate(urls, 1):
                lines.append(f"| {pos} | {url} |")
        lines.append("")

    return "\n".join(lines)


# Save overlap_matrix.md and one engine_<name>.md per engine
def save_reports(engine_results: dict, summary: dict, jaccard: dict, engines: list, test_queries: list, top_n: int) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    overlap_report = build_overlap_report(summary, jaccard, engines, test_queries, top_n)
    overlap_path = REPORTS_DIR / "overlap_matrix.md"
    overlap_path.write_text(overlap_report)
    print(f"Report saved: {overlap_path}")

    for engine in engines:
        engine_report = build_engine_report(engine, engine_results, test_queries, top_n)
        filename = "engine_" + engine.replace(" ", "_") + ".md"
        engine_path = REPORTS_DIR / filename
        engine_path.write_text(engine_report)
        print(f"Report saved: {engine_path}")
