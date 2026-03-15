#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import hashlib
import time
import requests
import yaml
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SEARXNG_URL = "http://localhost:8080/search"
TOP_K = 30
MAX_PAGES = 3
SETTINGS_PATH = Path(__file__).parent.parent.parent / "src" / "searxng" / "settings.yml"
PROFILES_PATH = Path(__file__).parent / "profiles.yml"
REPORTS_DIR = Path(__file__).parent / "01_reports"
DELAY_BETWEEN_REQUESTS = 2


# ORCHESTRATOR
def run_search_suite(compare: bool = False):
    queries = load_queries()
    profiles = load_profiles()
    settings_hash = compute_settings_hash()
    all_results = {}

    for entry in queries:
        query = entry["query"]
        profile_name = entry["profile"]
        profile = profiles.get(profile_name, profiles["general"])

        results = run_query(query, profile)
        key = (query, profile_name)
        all_results[key] = results
        time.sleep(DELAY_BETWEEN_REQUESTS)

        if compare and profile_name != "general":
            general_profile = profiles["general"]
            general_results = run_query(query, general_profile)
            key_general = (query, "general")
            all_results[key_general] = general_results
            time.sleep(DELAY_BETWEEN_REQUESTS)

    report = build_report(all_results, settings_hash, compare)
    save_report(report)


# FUNCTIONS

# Load queries with @profile directives
def load_queries() -> list[dict]:
    queries_file = Path(__file__).parent / "queries.txt"
    queries = []
    current_profile = "general"
    with open(queries_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('@profile:'):
                current_profile = line.split(':', 1)[1].strip()
                continue
            queries.append({"query": line, "profile": current_profile})
    return queries


# Load profile definitions from profiles.yml
def load_profiles() -> dict:
    with open(PROFILES_PATH, 'r') as f:
        return yaml.safe_load(f)


# Compute short hash of settings.yml for report identification
def compute_settings_hash() -> str:
    with open(SETTINGS_PATH, 'r') as f:
        content = f.read()
    return hashlib.md5(content.encode()).hexdigest()[:8]


# Execute single query against SearXNG API with profile parameters and pagination
def run_query(query: str, profile: dict) -> list[dict]:
    all_results = []
    seen_urls = set()

    for page in range(1, MAX_PAGES + 1):
        params = {
            "q": query,
            "format": "json",
            "categories": profile.get("category", "general"),
            "language": profile.get("language", "en"),
            "pageno": page,
        }
        if profile.get("time_range"):
            params["time_range"] = profile["time_range"]
        if profile.get("engines"):
            params["engines"] = profile["engines"]

        response = requests.get(SEARXNG_URL, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        if not results:
            break

        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

        time.sleep(DELAY_BETWEEN_REQUESTS)

    return all_results[:TOP_K]


# Extract domain from URL
def extract_domain(url: str) -> str:
    return urlparse(url).netloc


# Build full markdown report from all query results
def build_report(all_results: dict, settings_hash: str, compare: bool) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    all_items = [item for results in all_results.values() for item in results]
    total_queries = len(set(q for q, _ in all_results.keys()))
    total_results = sum(len(r) for r in all_results.values())
    avg_results = total_results / len(all_results) if all_results else 0
    multi_engine = sum(1 for item in all_items if len(item.get("engines", [])) > 1)
    multi_engine_pct = (multi_engine / len(all_items) * 100) if all_items else 0
    avg_score = sum(item.get("score", 0) for item in all_items) / len(all_items) if all_items else 0

    domain_counts = Counter(extract_domain(item.get("url", "")) for item in all_items)
    top_domains = domain_counts.most_common(10)

    lines = []
    lines.append("# Search Quality Report")
    lines.append(f"Date: {timestamp}")
    lines.append(f"Config hash: {settings_hash}")
    lines.append(f"Compare mode: {'yes' if compare else 'no'}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Unique queries: {total_queries}")
    lines.append(f"- Total runs: {len(all_results)} (queries x profiles)")
    lines.append(f"- Total results: {total_results}")
    lines.append(f"- Avg results per run: {avg_results:.1f}")
    lines.append(f"- Multi-engine results: {multi_engine_pct:.0f}% ({multi_engine}/{len(all_items)})")
    lines.append(f"- Avg score: {avg_score:.1f}")
    lines.append("")
    lines.append("### Top Domains")
    lines.append("")
    lines.append("| Domain | Count |")
    lines.append("|--------|-------|")
    for domain, count in top_domains:
        lines.append(f"| {domain} | {count} |")
    lines.append("")

    # Group results by query for comparison view
    queries_seen = {}
    for (query, profile), results in all_results.items():
        if query not in queries_seen:
            queries_seen[query] = []
        queries_seen[query].append((profile, results))

    for query, profile_results in queries_seen.items():
        for profile_name, results in profile_results:
            lines.append(f'## Query: "{query}"')
            lines.append(f"Profile: {profile_name} | Results: {len(results)}")
            lines.append("")

            if not results:
                lines.append("*No results*")
                lines.append("")
                continue

            lines.append("| # | Score | Engines | Domain | Title | URL | Snippet |")
            lines.append("|---|-------|---------|--------|-------|-----|---------|")

            for idx, item in enumerate(results, 1):
                score = item.get("score", 0)
                engines = ", ".join(item.get("engines", []))
                domain = extract_domain(item.get("url", ""))
                title = item.get("title", "")[:80]
                url = item.get("url", "")
                snippet = item.get("content", "").replace("\n", " ").replace("|", "/")
                lines.append(f"| {idx} | {score:.1f} | {engines} | {domain} | {title} | {url} | {snippet} |")

            lines.append("")

        # Comparison summary when multiple profiles for same query
        if compare and len(profile_results) > 1:
            lines.append(f'### Comparison: "{query}"')
            lines.append("")
            lines.append("| Metric | " + " | ".join(p for p, _ in profile_results) + " |")
            lines.append("|--------|" + "|".join("-----" for _ in profile_results) + "|")

            # Result count
            counts = [str(len(r)) for _, r in profile_results]
            lines.append("| Results | " + " | ".join(counts) + " |")

            # Avg score
            avgs = [f"{sum(i.get('score', 0) for i in r) / len(r):.1f}" if r else "0" for _, r in profile_results]
            lines.append("| Avg Score | " + " | ".join(avgs) + " |")

            # URL overlap
            url_sets = [set(extract_domain(i.get("url", "")) for i in r) for _, r in profile_results]
            if len(url_sets) == 2:
                overlap = len(url_sets[0] & url_sets[1])
                total = len(url_sets[0] | url_sets[1])
                lines.append(f"| Domain Overlap | {overlap}/{total} domains shared | |")

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
    parser = argparse.ArgumentParser(description="Run SearXNG search quality suite")
    parser.add_argument("--compare", action="store_true",
                        help="A/B mode: run each query with its profile AND general, compare results")
    args = parser.parse_args()
    run_search_suite(compare=args.compare)
