# INFRASTRUCTURE
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from mcp.types import TextContent

# From scrape_url.py: Shared scraping utilities
from src.scraper.scrape_url import is_garbage_content, COOKIE_CONSENT_SELECTOR, MIN_CONTENT_THRESHOLD, get_plugin_hint

logger = logging.getLogger(__name__)

CLOUDFLARE_SENTINEL = "__cloudflare__"


# ORCHESTRATOR
async def scrape_url_raw_workflow(url: str, output_dir: str) -> list[TextContent]:
    logger.info("Scraping raw: %s", url)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    markdown_generator = DefaultMarkdownGenerator()

    normal_config = BrowserConfig(headless=True, verbose=False)
    content = await try_scrape_raw(normal_config, None, markdown_generator, url, "networkidle")

    if content == CLOUDFLARE_SENTINEL:
        return [TextContent(type="text", text=f"Error scraping {url}: Cloudflare-protected page. Find an alternative source.")]

    if not content:
        content = await try_scrape_raw(normal_config, None, markdown_generator, url, "domcontentloaded")

    if content == CLOUDFLARE_SENTINEL:
        return [TextContent(type="text", text=f"Error scraping {url}: Cloudflare-protected page. Find an alternative source.")]

    if not content:
        stealth_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
        adapter = UndetectedAdapter()
        stealth_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=stealth_config,
            browser_adapter=adapter
        )
        content = await try_scrape_raw(stealth_config, stealth_strategy, markdown_generator, url, "networkidle")

    if content == CLOUDFLARE_SENTINEL:
        return [TextContent(type="text", text=f"Error scraping {url}: Cloudflare-protected page. Find an alternative source.")]

    if not content:
        hint = get_plugin_hint(url)
        msg = f"Error scraping {url}: No content extracted"
        if hint:
            msg += f"\n\nHint: {hint}"
        return [TextContent(type="text", text=msg)]

    parsed = urlparse(url)
    path = parsed.netloc + parsed.path
    safe_name = re.sub(r'[^\w\-.]', '_', path).strip('_')[:120] + ".md"

    filepath = output_path / safe_name
    filepath.write_text(f"<!-- source: {url} -->\n\n{content}")

    logger.info("Scrape complete: %s → %s (%d chars)", url, filepath, len(content))
    return [TextContent(type="text", text=f"Saved: {filepath} ({len(content):,} chars)")]


# FUNCTIONS

# Detect Cloudflare / JS challenge interstitial pages
def is_cloudflare_content(content: str) -> bool:
    lower = content.lower()
    if len(content) < 500:
        if "checking your browser" in lower or "enable javascript and cookies" in lower:
            return True
    if "just a moment" in lower and "cloudflare" in lower:
        return True
    return False


# Attempt raw scrape (no content filter), return content, CLOUDFLARE_SENTINEL, or empty string
async def try_scrape_raw(browser_config, crawler_strategy, markdown_generator, url: str, wait_until: str) -> str:
    logger.debug("Trying %s wait strategy", wait_until)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=wait_until,
        excluded_selector=COOKIE_CONSENT_SELECTOR,
        markdown_generator=markdown_generator,
    )
    try:
        kwargs = {"config": browser_config}
        if crawler_strategy:
            kwargs["crawler_strategy"] = crawler_strategy
        async with AsyncWebCrawler(**kwargs) as crawler:
            result = await crawler.arun(url=url, config=run_config)
        if not result.markdown:
            return ""
        content = result.markdown.raw_markdown
        if not content:
            return ""
        if is_cloudflare_content(content):
            return CLOUDFLARE_SENTINEL
        if len(content) < MIN_CONTENT_THRESHOLD:
            return ""
        if is_garbage_content(content):
            logger.warning("Garbage content detected for %s", url)
            return ""
        return content
    except Exception as e:
        logger.warning("Failed to scrape %s: %s", url, e)
        return ""
