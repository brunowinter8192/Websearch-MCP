#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import time
import yaml
from pathlib import Path

from src.search.search_web import fetch_search_results
from _engines_report import build_report, save_report

TOP_K = 30
MAX_PAGES = 3
PROFILES_PATH = Path(__file__).parent.parent / "profiles.yml"
DELAY_BETWEEN_REQUESTS = 2


# ORCHESTRATOR
def run_search_suite(compare: bool = False):
    queries = load_queries()
    profiles = load_profiles()
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

    report = build_report(all_results, compare)
    save_report(report)


# FUNCTIONS

# Load queries with @profile directives
def load_queries() -> list[dict]:
    queries_file = Path(__file__).parent.parent / "queries.txt"
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


# Execute single query against search API with profile parameters and pagination
def run_query(query: str, profile: dict) -> list[dict]:
    all_results = []
    seen_urls = set()

    for page in range(1, MAX_PAGES + 1):
        results = fetch_search_results(
            query,
            profile.get("category", "general"),
            profile.get("language", "en"),
            profile.get("time_range"),
            profile.get("engines"),
            page,
        )

        if not results:
            break

        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

        time.sleep(DELAY_BETWEEN_REQUESTS)

    return all_results[:TOP_K]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run search quality suite")
    parser.add_argument("--compare", action="store_true",
                        help="A/B mode: run each query with its profile AND general, compare results")
    args = parser.parse_args()
    run_search_suite(compare=args.compare)
