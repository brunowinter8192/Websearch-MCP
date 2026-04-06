#!/usr/bin/env python3

# INFRASTRUCTURE
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.searxng.search_web import fetch_search_results

REPORTS_DIR = Path(__file__).parent / "11_reports"
DELAY_BETWEEN_ENGINES = 5
DELAY_BETWEEN_QUERIES = 10
TOP_N = 10

ENGINES = [
    "google",
    "bing",
    "mojeek",
    "brave",
    "startpage",
    "duckduckgo",
    "google scholar",
    "semantic scholar",
    "crossref",
]

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
    # German (Alltag + Tech)
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
def run_isolation_eval():
    engine_results: dict[str, dict[int, list[str]]] = {e: {} for e in ENGINES}

    for qi, query in enumerate(TEST_QUERIES):
        print(f"[Query {qi + 1}/{len(TEST_QUERIES)}] {query}", file=sys.stderr)
        for ei, engine in enumerate(ENGINES):
            print(f"  [{ei + 1}/{len(ENGINES)}] {engine}", file=sys.stderr)
            try:
                results = fetch_search_results(query, "", "en", None, engine, 1)
                for r in results:
                    reported_engines = r.get("engines", [])
                    if reported_engines and engine not in reported_engines:
                        print(f"    WARNING: Result from {reported_engines}, expected {engine}", file=sys.stderr)
                urls = [r.get("url", "") for r in results if r.get("url")][:TOP_N]
            except Exception as e:
                print(f"    SKIP: {e}", file=sys.stderr)
                urls = []
            engine_results[engine][qi] = urls
            if ei < len(ENGINES) - 1:
                time.sleep(DELAY_BETWEEN_ENGINES)
        if qi < len(TEST_QUERIES) - 1:
            time.sleep(DELAY_BETWEEN_QUERIES)

    summary = compute_per_engine_summary(engine_results)
    jaccard = compute_jaccard_matrix(engine_results)
    save_reports(engine_results, summary, jaccard)


# FUNCTIONS

# Compute per-engine metrics: avg URLs/query, total unique, consensus rate, avg position
def compute_per_engine_summary(engine_results: dict) -> dict:
    summary = {}
    query_count = len(TEST_QUERIES)

    for engine in ENGINES:
        total_urls = 0
        consensus_count = 0
        unique_count = 0
        position_sum = 0
        position_total = 0

        for qi in range(query_count):
            urls = engine_results[engine].get(qi, [])
            url_set = set(urls)
            total_urls += len(url_set)

            for pos, url in enumerate(urls, 1):
                position_sum += pos
                position_total += 1

            other_urls: set = set()
            for other_engine in ENGINES:
                if other_engine != engine:
                    other_urls |= set(engine_results[other_engine].get(qi, []))

            for url in url_set:
                if url in other_urls:
                    consensus_count += 1
                else:
                    unique_count += 1

        summary[engine] = {
            "total_urls": total_urls,
            "avg_urls_per_query": total_urls / query_count if query_count > 0 else 0,
            "unique_urls": unique_count,
            "consensus_count": consensus_count,
            "consensus_rate": consensus_count / total_urls if total_urls > 0 else 0,
            "avg_position": position_sum / position_total if position_total > 0 else 0,
        }

    return summary


# Compute pairwise Jaccard similarity using global URL sets across all queries
def compute_jaccard_matrix(engine_results: dict) -> dict:
    global_sets: dict[str, set] = {}
    for engine in ENGINES:
        all_urls: set = set()
        for qi in range(len(TEST_QUERIES)):
            all_urls |= set(engine_results[engine].get(qi, []))
        global_sets[engine] = all_urls

    jaccard: dict[str, dict[str, float]] = {}
    for a in ENGINES:
        jaccard[a] = {}
        for b in ENGINES:
            set_a = global_sets[a]
            set_b = global_sets[b]
            union = set_a | set_b
            if not union:
                jaccard[a][b] = 0.0
            else:
                jaccard[a][b] = len(set_a & set_b) / len(union)

    return jaccard


# Build overlap_matrix.md: per-engine summary + unique ranking + Jaccard matrix
def build_overlap_report(summary: dict, jaccard: dict) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    query_count = len(TEST_QUERIES)

    sorted_by_unique = sorted(
        ENGINES, key=lambda e: summary[e]["unique_urls"], reverse=True
    )
    sorted_by_consensus = sorted(
        ENGINES, key=lambda e: summary[e]["consensus_rate"], reverse=True
    )

    lines = [
        "# Engine Isolation — Overlap Matrix",
        f"Date: {timestamp}",
        f"Queries evaluated: {query_count}",
        f"Engines tested: {len(ENGINES)}",
        f"Max URLs per engine per query: {TOP_N}",
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

    short_names = {e: e[:10] for e in ENGINES}
    header_cells = ["Engine"] + [short_names[e] for e in ENGINES]
    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("|" + "---------|" * len(header_cells))

    for a in ENGINES:
        row = [short_names[a]]
        for b in ENGINES:
            val = jaccard[a][b]
            if a == b:
                row.append("—")
            else:
                row.append(f"{val:.2f}")
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
def build_engine_report(engine: str, engine_results: dict) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Engine: {engine}",
        f"Date: {timestamp}",
        f"Queries: {len(TEST_QUERIES)} | Max URLs per query: {TOP_N}",
        "",
    ]

    for qi, query in enumerate(TEST_QUERIES):
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
def save_reports(engine_results: dict, summary: dict, jaccard: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    overlap_report = build_overlap_report(summary, jaccard)
    overlap_path = REPORTS_DIR / "overlap_matrix.md"
    overlap_path.write_text(overlap_report)
    print(f"Report saved: {overlap_path}")

    for engine in ENGINES:
        engine_report = build_engine_report(engine, engine_results)
        filename = "engine_" + engine.replace(" ", "_") + ".md"
        engine_path = REPORTS_DIR / filename
        engine_path.write_text(engine_report)
        print(f"Report saved: {engine_path}")


if __name__ == "__main__":
    run_isolation_eval()
