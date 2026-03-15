#!/usr/bin/env python3

# INFRASTRUCTURE
import asyncio
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.scraper.scrape_url import scrape_url_workflow

TOP_N_PER_QUERY = 5
EXCERPT_LENGTH = 50000
MIN_USEFUL_CONTENT = 200
REPORTS_DIR = Path(__file__).parent / "02_reports"
SEARCH_REPORTS_DIR = Path(__file__).parent / "01_reports"
DELAY_BETWEEN_REQUESTS = 2


# ORCHESTRATOR
def evaluate_content():
    report_path = resolve_report_path()
    queries_with_urls = parse_search_report(report_path)
    scraped = asyncio.run(scrape_all_urls(queries_with_urls))
    content_dir = save_content_files(scraped, report_path.stem)
    report = build_report(scraped, report_path.name, content_dir.name)
    save_report(report)


# FUNCTIONS

# Resolve which search report to evaluate
def resolve_report_path() -> Path:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.exists():
            return path
        raise FileNotFoundError(f"Report not found: {path}")

    reports = sorted(SEARCH_REPORTS_DIR.glob("search_report_*.md"))
    if not reports:
        raise FileNotFoundError(f"No search reports found in {SEARCH_REPORTS_DIR}")
    return reports[-1]


# Parse search report markdown into queries with their top URLs and snippets
def parse_search_report(report_path: Path) -> list[dict]:
    content = report_path.read_text()
    queries = []
    query_blocks = re.split(r'^## Query: "(.+?)"', content, flags=re.MULTILINE)

    for i in range(1, len(query_blocks), 2):
        query_text = query_blocks[i]
        block = query_blocks[i + 1] if i + 1 < len(query_blocks) else ""

        urls = []
        for line in block.strip().split("\n"):
            if not line.startswith("|") or line.startswith("|--") or line.startswith("| #"):
                continue
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c]
            if len(cells) >= 6:
                try:
                    score = float(cells[1])
                except ValueError:
                    continue
                domain = cells[3]
                title = cells[4]
                url = cells[5]
                snippet = cells[6] if len(cells) >= 7 else ""
                if url.startswith("http"):
                    urls.append({"url": url, "score": score, "domain": domain, "title": title, "snippet": snippet})

        queries.append({"query": query_text, "urls": urls[:TOP_N_PER_QUERY]})

    return queries


# Scrape all URLs across all queries with fallback to snippet
async def scrape_all_urls(queries_with_urls: list[dict]) -> list[dict]:
    results = []
    for query_data in queries_with_urls:
        scraped_urls = []
        for url_data in query_data["urls"]:
            content, source = await scrape_with_fallback(url_data)
            scraped_urls.append({**url_data, "content": content, "source": source})
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

        results.append({"query": query_data["query"], "results": scraped_urls})

    return results


# Scrape URL with fallback chain: scrape → snippet → error
async def scrape_with_fallback(url_data: dict) -> tuple[str, str]:
    try:
        result = await scrape_url_workflow(url_data["url"], max_content_length=EXCERPT_LENGTH)
        content = result[0].text if result else ""

        if content.startswith("Error scraping"):
            if url_data.get("snippet"):
                return url_data["snippet"], "snippet (scrape returned empty)"
            return "[No content available]", "failed"

        content = content.split("\n\n", 1)[1] if "\n\n" in content else content

        if len(content) >= MIN_USEFUL_CONTENT:
            return truncate_content(content, EXCERPT_LENGTH), "scraped"

        if content and is_garbage_content(content):
            if url_data.get("snippet"):
                return url_data["snippet"], "snippet (scraped content was garbage)"
            return content, "scraped (low quality)"

        if content:
            return content, "scraped (short)"

        if url_data.get("snippet"):
            return url_data["snippet"], "snippet (scrape returned empty)"

        return "[No content available]", "failed"

    except Exception as e:
        if url_data.get("snippet"):
            return url_data["snippet"], f"snippet (scrape error: {type(e).__name__})"
        return f"[Scrape error: {type(e).__name__}]", "failed"


# Detect garbage content (cookie banners, cloudflare, login walls)
def is_garbage_content(content: str) -> bool:
    garbage_patterns = [
        "cookie", "cloudflare", "captcha", "enable javascript",
        "access denied", "please verify", "checking your browser",
        "consent preferences", "privacy policy"
    ]
    lower = content.lower()
    matches = sum(1 for p in garbage_patterns if p in lower)
    return matches >= 3


# Truncate content at paragraph boundary
def truncate_content(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n\n')
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[Content truncated...]"


# Generate safe filename from URL
def url_to_filename(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.netloc + parsed.path
    safe = re.sub(r'[^\w\-.]', '_', path).strip('_')
    return safe[:120] + ".md"


# Save individual content files per URL
def save_content_files(scraped_data: list[dict], report_stem: str) -> Path:
    content_dir = REPORTS_DIR / f"02_content_{report_stem}"
    content_dir.mkdir(parents=True, exist_ok=True)

    for query_data in scraped_data:
        for idx, result in enumerate(query_data["results"], 1):
            filename = url_to_filename(result["url"])
            filepath = content_dir / filename

            lines = []
            lines.append(f"# {result['title']}")
            lines.append(f"**URL:** {result['url']}")
            lines.append(f"**Domain:** {result['domain']}")
            lines.append(f"**Score:** {result['score']:.1f}")
            lines.append(f"**Source:** {result['source']}")
            lines.append(f"**Query:** {query_data['query']}")
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append(result["content"])

            filepath.write_text("\n".join(lines))

    return content_dir


# Build summary report referencing content files
def build_report(scraped_data: list[dict], source_report: str, content_dir_name: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_urls = sum(len(q["results"]) for q in scraped_data)

    source_counts = {}
    for q in scraped_data:
        for r in q["results"]:
            key = r["source"].split(" (")[0]
            source_counts[key] = source_counts.get(key, 0) + 1

    lines = []
    lines.append("# Content Evaluation Report")
    lines.append(f"Source: {source_report}")
    lines.append(f"Date: {timestamp}")
    lines.append(f"Content files: {content_dir_name}/")
    lines.append("")
    lines.append("## Scrape Summary")
    lines.append(f"Total URLs: {total_urls}")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {source}: {count}")
    lines.append("")

    for query_data in scraped_data:
        lines.append(f'## Query: "{query_data["query"]}"')
        lines.append("")

        for idx, result in enumerate(query_data["results"], 1):
            filename = url_to_filename(result["url"])
            source_label = result["source"]
            lines.append(f'### {idx}. {result["domain"]} (Score: {result["score"]:.1f}) [{source_label}]')
            lines.append(f'**Title:** {result["title"]}')
            lines.append(f'**URL:** {result["url"]}')
            lines.append(f'**File:** {content_dir_name}/{filename}')
            lines.append("")
            lines.append(result["content"])
            lines.append("")

    return "\n".join(lines)


# Save report to 02_reports directory
def save_report(report: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"content_eval_{timestamp}.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    evaluate_content()
