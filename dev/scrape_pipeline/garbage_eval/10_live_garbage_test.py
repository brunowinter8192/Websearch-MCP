#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
if not os.environ.get("SEARXNG_PROJECT_ROOT"):
    os.environ["SEARXNG_PROJECT_ROOT"] = str(PROJECT_ROOT)

sys.path.insert(0, str(PROJECT_ROOT))

from crawl4ai import BrowserConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from src.searxng.search_web import fetch_search_results
from src.scraper.scrape_url import is_garbage_content, log_scrape_failure, try_scrape

REPORTS_DIR = Path(__file__).parent / "10_reports"
FAILURES_JSONL = PROJECT_ROOT / "dev" / "scrape_pipeline" / "failures.jsonl"
SEARCH_TOP_K = 10
SCRAPE_DELAY = 3

EDGE_CASES = {
    "consent_prefix": [
        "https://www.azubiyo.de/bewerbung/layout/",
        "https://www.stepstone.de/magazin/bewerbung/",
    ],
    "padded_404": [
        "https://medium.com/nonexistent-article-xyz-12345",
        "https://dev.to/nonexistent-user-xyz/nonexistent-post-12345",
    ],
    "baseline_good": [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://docs.python.org/3/tutorial/",
    ],
}


# ORCHESTRATOR
async def run_live_garbage_test(mode: str, search_query: str | None) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    failures_before = count_failures(FAILURES_JSONL)

    if mode == "search" and search_query:
        urls = fetch_search_urls(search_query)
        test_pairs = [("search_result", url) for url in urls]
        title = f'Search: "{search_query}"'
    else:
        test_pairs = [(cat, url) for cat, urls in EDGE_CASES.items() for url in urls]
        title = "Edge Cases"

    results = await scrape_test_pairs(test_pairs)
    failures_after = count_failures(FAILURES_JSONL)

    report = build_report(title, results, failures_before, failures_after)
    report_path = REPORTS_DIR / f"live_garbage_test_{timestamp}.md"
    report_path.write_text(report)
    print(f"Report saved: {report_path}")


# FUNCTIONS

# Fetch top URLs from SearXNG search
def fetch_search_urls(query: str) -> list[str]:
    results = fetch_search_results(query, "general", "en", None, None, 1)
    return [r.get("url", "") for r in results[:SEARCH_TOP_K] if r.get("url")]


# Count lines in failures.jsonl
def count_failures(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open())


# Scrape all test pairs: normal networkidle, fallback domcontentloaded
async def scrape_test_pairs(test_pairs: list[tuple[str, str]]) -> list[dict]:
    markdown_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48)
    )
    browser_config = BrowserConfig(headless=True, verbose=False)
    results = []

    for i, (category, url) in enumerate(test_pairs):
        print(f"[{i + 1}/{len(test_pairs)}] {category}: {url[:80]}", file=sys.stderr)

        content, garbage_type, status_code = await try_scrape(
            browser_config, None, markdown_generator, url, "networkidle"
        )
        fallback_used = False
        if not content:
            content, garbage_type2, status_code2 = await try_scrape(
                browser_config, None, markdown_generator, url, "domcontentloaded"
            )
            if garbage_type2:
                garbage_type = garbage_type2
            if status_code2:
                status_code = status_code2
            fallback_used = True

        logged = not content
        if logged:
            log_scrape_failure(url, garbage_type, status_code)

        results.append({
            "category": category,
            "url": url,
            "content_len": len(content),
            "garbage_type": garbage_type,
            "status_code": status_code,
            "fallback_used": fallback_used,
            "logged": logged,
        })

        if i < len(test_pairs) - 1:
            await asyncio.sleep(SCRAPE_DELAY)

    return results


# Build markdown report from scrape results and failure log delta
def build_report(title: str, results: list[dict], failures_before: int, failures_after: int) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_failures = failures_after - failures_before
    successful = sum(1 for r in results if r["content_len"] > 0)
    garbage_hits = sum(1 for r in results if r["garbage_type"])

    lines = [
        f"# Live Garbage Test — {title}",
        f"Date: {timestamp}",
        "",
        "## Summary",
        f"- URLs tested: {len(results)}",
        f"- Successful scrapes: {successful}",
        f"- Garbage detected: {garbage_hits}",
        f"- New failures.jsonl entries: {new_failures}",
        "",
        "## Results",
        "",
        "| # | Category | URL | Content | Garbage | Status | Fallback | Logged |",
        "|---|----------|-----|---------|---------|--------|----------|--------|",
    ]

    for i, r in enumerate(results, 1):
        url_short = r["url"][:70]
        content = f"{r['content_len']} chars" if r["content_len"] > 0 else "—"
        garbage = r["garbage_type"] or "—"
        status = str(r["status_code"]) if r["status_code"] else "—"
        fallback = "yes" if r["fallback_used"] else "no"
        logged = "yes" if r["logged"] else "no"
        lines.append(f"| {i} | {r['category']} | {url_short} | {content} | {garbage} | {status} | {fallback} | {logged} |")

    lines += [
        "",
        "## Failure Log",
        f"- failures.jsonl before: {failures_before}",
        f"- failures.jsonl after:  {failures_after}",
        f"- New entries:           {new_failures}",
        "",
        "## Notes",
        "- `strip_consent_prefix` not yet in `src/scraper/scrape_url.py` — prototype only in `09_garbage_fix_prototype.py`",
        "- Two scrape attempts per URL: networkidle → domcontentloaded fallback (no stealth)",
        "- `log_scrape_failure` called on all final failures; requires `SEARXNG_PROJECT_ROOT` env var",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live search→scrape→garbage pipeline test")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", metavar="QUERY", help="Search for URLs then scrape them")
    group.add_argument("--edge-cases", action="store_true", help="Test known edge case URLs from EDGE_CASES dict")
    args = parser.parse_args()

    if args.search:
        asyncio.run(run_live_garbage_test("search", args.search))
    else:
        asyncio.run(run_live_garbage_test("edge-cases", None))
