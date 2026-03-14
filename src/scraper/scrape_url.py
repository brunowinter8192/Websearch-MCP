# INFRASTRUCTURE
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from mcp.types import TextContent

DEFAULT_MAX_CONTENT_LENGTH = 15000

PLUGIN_HINTS = {
    "reddit.com": "Use the Reddit MCP plugin (reddit search_posts/get_post_comments) for Reddit content.",
    "arxiv.org": "Use the RAG MCP plugin to search indexed papers, or fetch the PDF directly.",
}

COOKIE_CONSENT_SELECTOR = ", ".join([
    "[class*='cookie-banner']", "[id*='cookie-banner']",
    "[class*='cookie-consent']", "[id*='cookie-consent']",
    "[class*='cookie-notice']", "[id*='cookie-notice']",
    "[class*='cookie-law']", "[id*='cookie-law']",
    "[class*='cky-']",
    "[class*='onetrust']", "[id*='onetrust']",
    "[id*='CookiebotDialog']", "[class*='CookiebotWidget']",
    "[class*='cc-banner']", "[class*='cc-window']",
    "[class*='gdpr']", "[id*='gdpr']",
])


# ORCHESTRATOR
async def scrape_url_workflow(url: str, max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH) -> list[TextContent]:
    markdown_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48)
    )
    browser_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
    adapter = UndetectedAdapter()
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=adapter
    )

    content = await try_scrape(browser_config, crawler_strategy, markdown_generator, url, "networkidle")

    if not content:
        content = await try_scrape(browser_config, crawler_strategy, markdown_generator, url, "domcontentloaded")

    if not content:
        hint = get_plugin_hint(url)
        msg = f"Error scraping {url}: No content extracted"
        if hint:
            msg += f"\n\nHint: {hint}"
        return [TextContent(type="text", text=msg)]

    truncated = truncate_content(content, max_content_length)
    return [TextContent(type="text", text=f"# Content from: {url}\n\n{truncated}")]


# FUNCTIONS

# Attempt scrape with given wait strategy, return content or empty string
async def try_scrape(browser_config, crawler_strategy, markdown_generator, url: str, wait_until: str) -> str:
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=wait_until,
        remove_overlay_elements=True,
        excluded_selector=COOKIE_CONSENT_SELECTOR,
        markdown_generator=markdown_generator,
    )
    try:
        async with AsyncWebCrawler(crawler_strategy=crawler_strategy, config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
        return result.markdown.fit_markdown if result.markdown else ""
    except Exception:
        return ""


# Truncate content at paragraph boundary if too long
def truncate_content(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n\n')
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[Content truncated...]"


# Check if URL matches a domain with a dedicated plugin
def get_plugin_hint(url: str) -> str:
    for domain, hint in PLUGIN_HINTS.items():
        if domain in url:
            return hint
    return ""
