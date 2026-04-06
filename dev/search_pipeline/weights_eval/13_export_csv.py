#!/usr/bin/env python3

# INFRASTRUCTURE
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPORTS_DIR = Path(__file__).parent / "11_reports"
EVAL_DIR = REPORTS_DIR / "eval"

QUERY_HEADER_RE = re.compile(r'^## Query \d+: (.+)$')
TABLE_ROW_RE = re.compile(r'^\|\s*(\d+)\s*\|\s*(https?://[^\s|]+)')


# ORCHESTRATOR
def run_csv_export():
    engine_data = load_engine_data()
    if not engine_data:
        print("ERROR: No engine_*.md files found in 11_reports/ — run 11_engine_isolation.py first.", file=sys.stderr)
        sys.exit(1)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    write_engine_urls(engine_data)
    write_engine_summary(engine_data)
    write_overlap_pairwise(engine_data)
    write_query_coverage(engine_data)
    write_query_unique_urls(engine_data)


# FUNCTIONS

# Parse all engine_*.md files into engine → query → [(pos, url)] mapping
def load_engine_data() -> dict[str, dict[str, list[tuple[int, str]]]]:
    engine_data: dict[str, dict[str, list[tuple[int, str]]]] = {}
    for engine_file in sorted(REPORTS_DIR.glob("engine_*.md")):
        engine_name = engine_file.stem.removeprefix("engine_").replace("_", " ")
        engine_data[engine_name] = {}
        current_query = None
        for line in engine_file.read_text(encoding="utf-8").splitlines():
            qm = QUERY_HEADER_RE.match(line)
            if qm:
                current_query = qm.group(1).strip()
                engine_data[engine_name][current_query] = []
                continue
            if current_query is None:
                continue
            rm = TABLE_ROW_RE.match(line)
            if rm:
                pos = int(rm.group(1))
                url = rm.group(2).strip()
                engine_data[engine_name][current_query].append((pos, url))
    return engine_data


# Collect unique ordered query list from engine data (preserving file order)
def get_all_queries(engine_data: dict) -> list[str]:
    seen: set = set()
    queries: list[str] = []
    for queries_dict in engine_data.values():
        for q in queries_dict:
            if q not in seen:
                seen.add(q)
                queries.append(q)
    return queries


# Extract hostname from URL, stripping www. prefix
def extract_domain(url: str) -> str:
    try:
        hostname = urlparse(url).hostname or ""
        return hostname.removeprefix("www.")
    except Exception:
        return ""


# Write engine_urls.csv: one row per engine × query × URL
def write_engine_urls(engine_data: dict) -> None:
    path = EVAL_DIR / "engine_urls.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["engine", "query", "position", "url", "domain"])
        for engine, queries in sorted(engine_data.items()):
            for query, url_list in queries.items():
                for pos, url in url_list:
                    writer.writerow([engine, query, pos, url, extract_domain(url)])
    print(f"Saved: {path}")


# Write engine_summary.csv: aggregated per-engine metrics
def write_engine_summary(engine_data: dict) -> None:
    engines = list(engine_data.keys())
    queries = get_all_queries(engine_data)
    query_count = len(queries)

    path = EVAL_DIR / "engine_summary.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["engine", "total_urls", "unique_urls", "consensus_urls", "consensus_rate", "avg_urls_per_query"])
        for engine in sorted(engines):
            total_urls = 0
            unique_count = 0
            consensus_count = 0
            for query in queries:
                url_set = {url for _, url in engine_data[engine].get(query, [])}
                total_urls += len(url_set)
                other_urls: set = set()
                for other in engines:
                    if other != engine:
                        other_urls |= {url for _, url in engine_data[other].get(query, [])}
                for url in url_set:
                    if url in other_urls:
                        consensus_count += 1
                    else:
                        unique_count += 1
            consensus_rate = round(consensus_count / total_urls, 4) if total_urls > 0 else 0.0
            avg_urls = round(total_urls / query_count, 2) if query_count > 0 else 0.0
            writer.writerow([engine, total_urls, unique_count, consensus_count, consensus_rate, avg_urls])
    print(f"Saved: {path}")


# Write overlap_pairwise.csv: Jaccard similarity for every unique engine pair
def write_overlap_pairwise(engine_data: dict) -> None:
    engines = sorted(engine_data.keys())
    queries = get_all_queries(engine_data)

    global_sets: dict[str, set] = {
        engine: {url for query in queries for _, url in engine_data[engine].get(query, [])}
        for engine in engines
    }

    path = EVAL_DIR / "overlap_pairwise.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["engine_a", "engine_b", "jaccard", "shared_urls", "union_urls"])
        for i, a in enumerate(engines):
            for b in engines[i + 1:]:
                shared = len(global_sets[a] & global_sets[b])
                union = len(global_sets[a] | global_sets[b])
                jaccard = round(shared / union, 4) if union > 0 else 0.0
                writer.writerow([a, b, jaccard, shared, union])
    print(f"Saved: {path}")


# Write query_coverage.csv: per-engine × per-query breakdown
def write_query_coverage(engine_data: dict) -> None:
    engines = sorted(engine_data.keys())
    queries = get_all_queries(engine_data)

    path = EVAL_DIR / "query_coverage.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["engine", "query", "num_urls", "num_consensus", "num_unique"])
        for engine in engines:
            for query in queries:
                url_set = {url for _, url in engine_data[engine].get(query, [])}
                other_urls: set = set()
                for other in engines:
                    if other != engine:
                        other_urls |= {url for _, url in engine_data[other].get(query, [])}
                num_consensus = sum(1 for url in url_set if url in other_urls)
                num_unique = len(url_set) - num_consensus
                writer.writerow([engine, query, len(url_set), num_consensus, num_unique])
    print(f"Saved: {path}")


# Write query_unique_urls.csv: distinct URL count across all engines per query
def write_query_unique_urls(engine_data: dict) -> None:
    queries = get_all_queries(engine_data)
    path = EVAL_DIR / "query_unique_urls.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query", "total_unique_urls"])
        for query in queries:
            all_urls: set = set()
            for queries_dict in engine_data.values():
                all_urls |= {url for _, url in queries_dict.get(query, [])}
            writer.writerow([query, len(all_urls)])
    print(f"Saved: {path}")


if __name__ == "__main__":
    run_csv_export()
