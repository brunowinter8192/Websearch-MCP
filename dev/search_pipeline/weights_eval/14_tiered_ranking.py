#!/usr/bin/env python3

# INFRASTRUCTURE
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.searxng.search_web import fetch_search_results

REPORTS_DIR = Path(__file__).parent / "14_reports"
DELAY_BETWEEN_ENGINES = 3
TOP_N_PER_ENGINE = 10
TIER1_SIZE = 20

ENGINES = [
    "google", "bing", "mojeek", "brave", "startpage",
    "duckduckgo", "google scholar", "semantic scholar", "crossref",
]


# ORCHESTRATOR
def run_tiered_ranking(query: str) -> None:
    url_data = collect_results(query)
    tier1, tier2, tier3 = split_tiers(url_data)
    report = build_report(query, tier1, tier2, tier3)
    save_report(query, report)


# FUNCTIONS

# Fetch results from all engines, aggregate URL metadata
def collect_results(query: str) -> dict[str, dict]:
    url_data: dict[str, dict] = {}
    for i, engine in enumerate(ENGINES):
        print(f"[{i + 1}/{len(ENGINES)}] {engine}", file=sys.stderr)
        try:
            results = fetch_search_results(query, "", "en", None, engine, 1)
        except Exception as e:
            print(f"  SKIP: {e}", file=sys.stderr)
            results = []
        for result in results[:TOP_N_PER_ENGINE]:
            url = result.get("url", "")
            if not url:
                continue
            if url not in url_data:
                url_data[url] = {"engines": [], "title": "", "snippet": ""}
            url_data[url]["engines"].append(engine)
            candidate_snippet = result.get("content", "") or ""
            if len(candidate_snippet) > len(url_data[url]["snippet"]):
                url_data[url]["snippet"] = candidate_snippet
                url_data[url]["title"] = result.get("title", "") or ""
        if i < len(ENGINES) - 1:
            time.sleep(DELAY_BETWEEN_ENGINES)
    return url_data


# Split URL data into 3 tiers by engine count
def split_tiers(url_data: dict) -> tuple[list, list, list]:
    consensus = sorted(
        [(url, d) for url, d in url_data.items() if len(d["engines"]) >= 2],
        key=lambda x: len(x[1]["engines"]),
        reverse=True,
    )
    unique = [
        (url, d) for url, d in url_data.items() if len(d["engines"]) == 1
    ]

    tier1 = consensus[:TIER1_SIZE]
    tier2 = consensus[TIER1_SIZE:]
    tier3 = unique
    return tier1, tier2, tier3


# Build markdown report with 3 tier tables
def build_report(query: str, tier1: list, tier2: list, tier3: list) -> str:
    lines = [
        f'# Tiered Search: "{query}"',
        "",
        f"**Tier 1:** {len(tier1)} results | "
        f"**Tier 2:** {len(tier2)} more (≥2 engines) | "
        f"**Tier 3:** {len(tier3)} unique (1 engine)",
        "",
        "## Tier 1 — Top Results",
        "",
        "| # | URL | Engines | Engine Count | Title |",
        "|---|-----|---------|-------------|-------|",
    ]
    for rank, (url, d) in enumerate(tier1, 1):
        engines_str = ", ".join(d["engines"])
        title = d["title"].replace("|", "\\|")[:80]
        lines.append(f"| {rank} | {url} | {engines_str} | {len(d['engines'])} | {title} |")

    lines += [
        "",
        f"## Tier 2 — Extended Consensus (≥2 engines)",
        "",
        "| # | URL | Engines | Engine Count | Title |",
        "|---|-----|---------|-------------|-------|",
    ]
    for rank, (url, d) in enumerate(tier2, 1):
        engines_str = ", ".join(d["engines"])
        title = d["title"].replace("|", "\\|")[:80]
        lines.append(f"| {rank} | {url} | {engines_str} | {len(d['engines'])} | {title} |")

    lines += [
        "",
        "## Tier 3 — Unique (1 engine only)",
        "",
        "| # | URL | Engine | Title |",
        "|---|-----|--------|-------|",
    ]
    for rank, (url, d) in enumerate(tier3, 1):
        engine = d["engines"][0]
        title = d["title"].replace("|", "\\|")[:80]
        lines.append(f"| {rank} | {url} | {engine} | {title} |")

    return "\n".join(lines)


# Save report to 14_reports/<sanitized_query>.md
def save_report(query: str, report: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", query)[:80].strip("_")
    path = REPORTS_DIR / f"{safe_name}.md"
    path.write_text(report, encoding="utf-8")
    print(f"Report saved: {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: 14_tiered_ranking.py <query>", file=sys.stderr)
        sys.exit(1)
    run_tiered_ranking(sys.argv[1])
