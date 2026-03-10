#!/usr/bin/env python3

# INFRASTRUCTURE
import hashlib
import requests
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SEARXNG_URL = "http://localhost:8080/search"
TOP_K = 10
SETTINGS_PATH = Path(__file__).parent.parent.parent / "src" / "searxng" / "settings.yml"
REPORTS_DIR = Path(__file__).parent / "01_reports"


# ORCHESTRATOR
def run_search_suite():
    queries = load_queries()
    settings_hash = compute_settings_hash()
    all_results = {}

    for query in queries:
        results = run_query(query)
        all_results[query] = results

    report = build_report(all_results, settings_hash)
    save_report(report)


# FUNCTIONS

# Load queries from queries.txt, skip comments and empty lines
def load_queries() -> list[str]:
    queries_file = Path(__file__).parent / "queries.txt"
    queries = []
    with open(queries_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                queries.append(line)
    return queries


# Compute short hash of settings.yml for report identification
def compute_settings_hash() -> str:
    with open(SETTINGS_PATH, 'r') as f:
        content = f.read()
    return hashlib.md5(content.encode()).hexdigest()[:8]


# Execute single query against SearXNG API
def run_query(query: str, category: str = "general", language: str = "en") -> list[dict]:
    params = {
        "q": query,
        "format": "json",
        "categories": category,
        "language": language
    }
    response = requests.get(SEARXNG_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])[:TOP_K]


# Extract domain from URL
def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc


# Build full markdown report from all query results
def build_report(all_results: dict, settings_hash: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_queries = len(all_results)
    total_results = sum(len(r) for r in all_results.values())
    avg_results = total_results / total_queries if total_queries else 0

    all_items = [item for results in all_results.values() for item in results]
    multi_engine = sum(1 for item in all_items if len(item.get("engines", [])) > 1)
    multi_engine_pct = (multi_engine / len(all_items) * 100) if all_items else 0
    high_priority = sum(1 for item in all_items if item.get("priority") == "high")
    high_priority_pct = (high_priority / len(all_items) * 100) if all_items else 0
    avg_score = sum(item.get("score", 0) for item in all_items) / len(all_items) if all_items else 0

    domain_counts = Counter(extract_domain(item.get("url", "")) for item in all_items)
    top_domains = domain_counts.most_common(10)

    lines = []
    lines.append(f"# Search Quality Report")
    lines.append(f"Date: {timestamp}")
    lines.append(f"Config hash: {settings_hash}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total queries: {total_queries}")
    lines.append(f"- Total results: {total_results}")
    lines.append(f"- Avg results per query: {avg_results:.1f}")
    lines.append(f"- Multi-engine results (>1 engine): {multi_engine_pct:.0f}% ({multi_engine}/{len(all_items)})")
    lines.append(f"- High-priority results: {high_priority_pct:.0f}% ({high_priority}/{len(all_items)})")
    lines.append(f"- Avg score: {avg_score:.1f}")
    lines.append("")
    lines.append("### Top Domains")
    lines.append("")
    lines.append("| Domain | Count |")
    lines.append("|--------|-------|")
    for domain, count in top_domains:
        lines.append(f"| {domain} | {count} |")
    lines.append("")

    for query, results in all_results.items():
        lines.append(f'## Query: "{query}"')
        lines.append(f"Category: general | Results: {len(results)}")
        lines.append("")

        if not results:
            lines.append("*No results*")
            lines.append("")
            continue

        lines.append("| # | Score | Pri | Engines | Domain | Title |")
        lines.append("|---|-------|-----|---------|--------|-------|")

        for idx, item in enumerate(results, 1):
            score = item.get("score", 0)
            priority = item.get("priority", "")
            engines = ", ".join(item.get("engines", []))
            domain = extract_domain(item.get("url", ""))
            title = item.get("title", "")[:80]
            pri_display = priority if priority else ""
            lines.append(f"| {idx} | {score:.1f} | {pri_display} | {engines} | {domain} | {title} |")

        lines.append("")

    return "\n".join(lines)


# Save report to 01_reports directory
def save_report(report: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"search_report_{timestamp}.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    run_search_suite()
