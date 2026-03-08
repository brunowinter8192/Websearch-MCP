# INFRASTRUCTURE
import argparse
import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter, URLPatternFilter, ContentTypeFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

PERMALINK_PATTERN = re.compile(r'\[¶\]\([^)]+\)')
TRAILING_SLASH = re.compile(r'/$')


# ORCHESTRATOR
async def crawl_site_workflow(url: str, output_dir: str, depth: int, max_pages: int,
                              exclude_patterns: str = None, include_patterns: str = None):
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    domain = urlparse(url).netloc
    results = await crawl_website(url, domain, depth, max_pages, exclude_patterns, include_patterns)
    unique = deduplicate(results)
    saved = save_markdown(unique, url, target)

    print(f"\nDone: {saved} files saved to {target}")


# FUNCTIONS

# Crawl website using BFS strategy
async def crawl_website(url: str, domain: str, depth: int, max_pages: int,
                        exclude_patterns: str = None, include_patterns: str = None) -> list:
    filters = [
        DomainFilter(allowed_domains=[domain]),
        ContentTypeFilter(allowed_types=["text/html"]),
    ]
    if exclude_patterns:
        filters.append(URLPatternFilter(patterns=exclude_patterns.split(","), reverse=True))
    if include_patterns:
        filters.append(URLPatternFilter(patterns=include_patterns.split(","), reverse=False))
    filter_chain = FilterChain(filters)

    strategy = BFSDeepCrawlStrategy(
        max_depth=depth,
        include_external=False,
        filter_chain=filter_chain,
        max_pages=max_pages
    )

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        wait_until="networkidle",
        markdown_generator=DefaultMarkdownGenerator(),
    )

    print(f"Crawling {url} (depth={depth}, max_pages={max_pages}, domain={domain})")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(url=url, config=run_config)

    if not isinstance(results, list):
        results = [results]

    print(f"Crawled {len(results)} pages")
    return results


# Remove duplicate URLs (trailing slash normalization)
def deduplicate(results: list) -> list:
    seen = set()
    unique = []
    for r in results:
        normalized = TRAILING_SLASH.sub('', r.url) if hasattr(r, 'url') else None
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(r)
    print(f"Unique after dedup: {len(unique)}")
    return unique


# Save crawled pages as markdown files
def save_markdown(results: list, seed_url: str, output_dir: Path) -> int:
    saved = 0
    for r in results:
        url = TRAILING_SLASH.sub('', r.url) if hasattr(r, 'url') else None
        raw_md = r.markdown.raw_markdown if r.markdown else ""
        if not url or not raw_md:
            continue

        clean_md = PERMALINK_PATTERN.sub('', raw_md)
        clean_md = re.sub(r'\n{3,}', '\n\n', clean_md).strip()

        filename = url_to_filename(url, seed_url)
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"<!-- source: {url} -->\n\n{clean_md}")

        saved += 1
        print(f"  [{saved}] {filename} ({len(clean_md)} chars)")

    return saved


# Convert URL to safe filename
def url_to_filename(url: str, seed_url: str) -> str:
    path = url.replace(seed_url.rstrip('/'), '').strip('/')
    if not path:
        return "index.md"
    return path.replace('/', '_').replace('.html', '') + '.md'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl a website and save as Markdown")
    parser.add_argument("--url", required=True, help="Seed URL to crawl")
    parser.add_argument("--output-dir", required=True, help="Directory to save markdown files")
    parser.add_argument("--depth", type=int, default=3, help="Max crawl depth")
    parser.add_argument("--max-pages", type=int, default=100, help="Max pages to crawl")
    parser.add_argument("--exclude-patterns", type=str, default=None,
                        help="Comma-separated URL patterns to exclude (e.g. '/genindex*,/search*')")
    parser.add_argument("--include-patterns", type=str, default=None,
                        help="Comma-separated URL patterns to include (e.g. '/docs/*,/api/*')")
    args = parser.parse_args()

    asyncio.run(crawl_site_workflow(args.url, args.output_dir, args.depth, args.max_pages,
                                    args.exclude_patterns, args.include_patterns))
