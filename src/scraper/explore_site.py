# INFRASTRUCTURE
import asyncio
import logging
from collections import defaultdict
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, AsyncUrlSeeder, SeedingConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter, ContentTypeFilter, URLPatternFilter
from mcp.types import TextContent

logger = logging.getLogger(__name__)

MAX_DEPTH = 10
DEFAULT_MAX_PAGES = 50
CRAWL_TIMEOUT = 120


# ORCHESTRATOR
async def explore_site_workflow(url: str, max_pages: int = DEFAULT_MAX_PAGES, url_pattern: str | None = None) -> list[TextContent]:
    logger.info("Exploring: %s (max_pages=%d)", url, max_pages)
    domain = urlparse(url).netloc

    sitemap_urls = await check_sitemap(domain)
    logger.debug("Sitemap: %d URLs", len(sitemap_urls))
    timed_out, results = await crawl_for_discovery(url, domain, max_pages, url_pattern)
    site_map = build_site_map(url, domain, results, timed_out, sitemap_urls)

    if sitemap_urls:
        site_map["recommended_strategy"] = f"sitemap ({len(sitemap_urls)} URLs in sitemap)"
    elif site_map["total_pages"] > 1:
        site_map["recommended_strategy"] = "prefetch"
    else:
        site_map["recommended_strategy"] = "bfs (JS-heavy, prefetch found only 1 page)"

    logger.info("Discovery complete: %d pages", site_map["total_pages"])
    return [TextContent(type="text", text=format_site_map(site_map))]


# FUNCTIONS

# Check if site has a sitemap and return discovered URLs
async def check_sitemap(domain: str) -> list[str]:
    try:
        async with AsyncUrlSeeder() as seeder:
            config = SeedingConfig(source="sitemap")
            urls = await seeder.urls(domain, config)
            if not urls:
                return []
            return [u if isinstance(u, str) else u.get("url", str(u)) for u in urls]
    except Exception as e:
        logger.warning("Failed to check sitemap for %s: %s", domain, e)
        return []


# BFS crawl to discover site structure with timeout
async def crawl_for_discovery(url: str, domain: str, max_pages: int, url_pattern: str | None = None) -> tuple[bool, list]:
    filters = [
        DomainFilter(allowed_domains=[domain]),
        ContentTypeFilter(allowed_types=["text/html"]),
    ]
    if url_pattern:
        filters.append(URLPatternFilter(patterns=[url_pattern]))
    filter_chain = FilterChain(filters)

    strategy = BFSDeepCrawlStrategy(
        max_depth=MAX_DEPTH,
        include_external=False,
        filter_chain=filter_chain,
        max_pages=max_pages,
    )

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded",
        prefetch=True,
    )

    collected = []
    timed_out = False

    async def run_crawl():
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun(url=url, config=run_config)
            if not isinstance(results, list):
                results = [results]
            collected.extend(results)

    try:
        await asyncio.wait_for(run_crawl(), timeout=CRAWL_TIMEOUT)
    except asyncio.TimeoutError:
        timed_out = True

    return timed_out, collected


# Aggregate crawl results into site map with depth distribution and URL samples
def build_site_map(seed_url: str, domain: str, results: list, timed_out: bool = False, sitemap_urls: list[str] | None = None) -> dict:
    seen = set()
    urls = []
    depth_stats = defaultdict(lambda: {"count": 0, "chars": 0})
    depth_urls = defaultdict(list)

    for r in results:
        url = r.url.rstrip('/') if hasattr(r, 'url') and r.url else None
        if not url or url in seen:
            continue
        seen.add(url)

        chars = len(r.html) if r.html else 0
        depth = r.metadata.get("depth", -1) if r.metadata else -1

        urls.append({"url": url, "depth": depth, "chars": chars})
        depth_stats[depth]["count"] += 1
        depth_stats[depth]["chars"] += chars
        depth_urls[depth].append(url)

    for raw_url in (sitemap_urls or []):
        url = (raw_url if isinstance(raw_url, str) else raw_url.get("url", str(raw_url))).rstrip('/')
        if not url or url in seen:
            continue
        seen.add(url)

        path = urlparse(url).path.strip('/')
        depth = len(path.split('/')) if path else 0

        urls.append({"url": url, "depth": depth, "chars": 0})
        depth_stats[depth]["count"] += 1
        depth_urls[depth].append(url)

    total_chars = sum(u["chars"] for u in urls)
    depth_distribution = {str(k): v for k, v in sorted(depth_stats.items())}
    url_samples = pick_url_samples(depth_urls)

    return {
        "seed_url": seed_url,
        "domain": domain,
        "total_pages": len(urls),
        "total_chars": total_chars,
        "depth_distribution": depth_distribution,
        "url_samples": url_samples,
        "timed_out": timed_out,
    }


# Pick diverse URL samples per depth for noise pattern identification
def pick_url_samples(depth_urls: dict, samples_per_depth: int = 5) -> dict:
    samples = {}
    for depth in sorted(depth_urls.keys()):
        urls = depth_urls[depth]
        if len(urls) <= samples_per_depth:
            samples[str(depth)] = urls
            continue

        step = len(urls) // samples_per_depth
        samples[str(depth)] = [urls[i * step] for i in range(samples_per_depth)]

    return samples


# Format site map as readable Markdown
def format_site_map(site_map: dict) -> str:
    lines = [
        f"# Site Map: {site_map['domain']}",
        f"Seed: {site_map['seed_url']}",
        f"Pages: {site_map['total_pages']} | Chars: {site_map['total_chars']:,}",
        f"Recommended Strategy: {site_map.get('recommended_strategy', 'unknown')}",
    ]

    if site_map.get("timed_out"):
        lines.append(f"\n**PARTIAL RESULTS** — Crawl timed out after {CRAWL_TIMEOUT}s. Consider narrowing url_pattern or reducing max_pages.")

    lines.extend(["", "## Depth Distribution"])

    for depth, stats in site_map["depth_distribution"].items():
        lines.append(f"- Depth {depth}: {stats['count']} pages, {stats['chars']:,} chars")

    if site_map.get("url_samples"):
        lines.extend(["", "## URL Samples"])
        for depth, urls in site_map["url_samples"].items():
            lines.append(f"\n### Depth {depth}")
            for url in urls:
                lines.append(f"- {url}")

    return "\n".join(lines)
