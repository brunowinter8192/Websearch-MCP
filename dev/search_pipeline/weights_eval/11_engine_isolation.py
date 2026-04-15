#!/usr/bin/env python3

# INFRASTRUCTURE
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.search.search_web import fetch_search_results
from _isolation_report import save_reports

DELAY_BETWEEN_ENGINES = 5
DELAY_BETWEEN_QUERIES = 10
TOP_N = 10

ENGINES = [
    "google",
    "bing",
    "google scholar",
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
    save_reports(engine_results, summary, jaccard, ENGINES, TEST_QUERIES, TOP_N)


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
            jaccard[a][b] = 0.0 if not union else len(set_a & set_b) / len(union)

    return jaccard


if __name__ == "__main__":
    run_isolation_eval()
