# INFRASTRUCTURE
import argparse
import asyncio
import time
from urllib.parse import urlparse

from crawl_site import discover_urls, discover_urls_sitemap

UNLIMITED_PAGES = 100000


# ORCHESTRATOR
async def explore_site_workflow(url: str, strategy: str, max_pages: int, output: str,
                                depth: int, include_patterns: str, exclude_patterns: str):
    domain = urlparse(url).netloc
    effective_max = UNLIMITED_PAGES if max_pages == 0 else max_pages

    if output is None:
        output = f"/tmp/explore_{domain}_urls.txt"

    print(f"Exploring {url} (strategy: {strategy})")

    start = time.time()

    if strategy == "sitemap":
        urls = await discover_urls_sitemap(domain, include_patterns)
        strategy_used = "sitemap"
        duration = time.time() - start
        print(f"Sitemap: {len(urls)} URLs found in {duration:.1f}s")
    elif strategy == "prefetch":
        urls = await discover_urls(url, domain, depth, effective_max, exclude_patterns, include_patterns)
        strategy_used = "prefetch"
        duration = time.time() - start
        print(f"Prefetch: {len(urls)} URLs found in {duration:.1f}s")
    else:
        urls = await discover_urls_sitemap(domain, include_patterns)
        if urls:
            strategy_used = "sitemap"
            duration = time.time() - start
            print(f"Sitemap: {len(urls)} URLs found in {duration:.1f}s")
        else:
            print("No sitemap found. Trying prefetch BFS...")
            urls = await discover_urls(url, domain, depth, effective_max, exclude_patterns, include_patterns)
            strategy_used = "prefetch"
            duration = time.time() - start
            print(f"Prefetch: {len(urls)} URLs found in {duration:.1f}s")

    save_url_list(urls, output)
    print(f"Saved {len(urls)} URLs to {output}")


# FUNCTIONS

# Save URL list to text file (one URL per line)
def save_url_list(urls: list[str], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discover all URLs of a website and save to a file")
    parser.add_argument("--url", required=True, help="Seed URL to explore")
    parser.add_argument("--strategy", choices=["auto", "sitemap", "prefetch"], default="auto",
                        help="Discovery strategy: auto (sitemap→prefetch), sitemap, prefetch")
    parser.add_argument("--max-pages", type=int, default=0,
                        help="Max pages to discover (0 = unlimited)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path (default: /tmp/explore_<domain>_urls.txt)")
    parser.add_argument("--depth", type=int, default=10,
                        help="Max crawl depth for prefetch BFS")
    parser.add_argument("--include-patterns", type=str, default=None,
                        help="Comma-separated URL patterns to include (e.g. '/docs/*,/api/*')")
    parser.add_argument("--exclude-patterns", type=str, default=None,
                        help="Comma-separated URL patterns to exclude (e.g. '/genindex*,/search*')")
    args = parser.parse_args()

    asyncio.run(explore_site_workflow(args.url, args.strategy, args.max_pages, args.output,
                                     args.depth, args.include_patterns, args.exclude_patterns))
