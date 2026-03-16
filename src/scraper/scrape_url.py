# INFRASTRUCTURE
import re

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from mcp.types import TextContent

_LINK_LINE_RE = re.compile(r'^\[.+\]\(.+\)$')

DEFAULT_MAX_CONTENT_LENGTH = 15000
MIN_CONTENT_THRESHOLD = 200

PLUGIN_HINTS = {
    "reddit.com": "Use the Reddit MCP plugin (reddit search_posts/get_post_comments) for Reddit content.",
    "arxiv.org": "Use the RAG MCP plugin to search indexed papers, or fetch the PDF directly.",
}

COOKIE_CONSENT_SELECTOR = ", ".join([
    "[class*='cookie-banner']", "[id*='cookie-banner']",
    "[class*='cookie-consent']", "[id*='cookie-consent']",
    "[class*='cookie-notice']", "[id*='cookie-notice']",
    "[class*='cookie-law']", "[id*='cookie-law']",
    "[class*='cky-consent']", "[class*='cky-banner']", "[class*='cky-modal']",
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

    # Phase 1: Normal browser (works for most sites, avoids UndetectedAdapter issues)
    normal_config = BrowserConfig(headless=True, verbose=False)
    content = await try_scrape(normal_config, None, markdown_generator, url, "networkidle")

    if not content:
        content = await try_scrape(normal_config, None, markdown_generator, url, "domcontentloaded")

    # Phase 2: Stealth browser (for anti-bot protected sites)
    if not content:
        stealth_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
        adapter = UndetectedAdapter()
        stealth_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=stealth_config,
            browser_adapter=adapter
        )
        content = await try_scrape(stealth_config, stealth_strategy, markdown_generator, url, "networkidle")

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
        content = result.markdown.fit_markdown
        if len(content) < MIN_CONTENT_THRESHOLD and result.markdown.raw_markdown:
            content = result.markdown.raw_markdown
        if is_garbage_content(content):
            return ""
        return content
    except Exception:
        return ""


# Detect garbage content: error pages, cookie walls, login walls, navigation dumps
def is_garbage_content(content: str) -> bool:
    lower = content.lower()

    # Crawl4AI error messages returned as content
    crawl4ai_errors = ["crawl4ai error:", "document is empty", "page is not fully supported"]
    if any(p in lower for p in crawl4ai_errors):
        return True

    # HTTP error pages (404, 403, etc.) — short content with error keywords
    if len(content) < 1000:
        error_keywords = ["not_found", "404", "403", "forbidden", "access denied", "page not found"]
        if any(k in lower for k in error_keywords):
            return True

    # Navigation dumps — high ratio of standalone link lines (e.g., AWS nav pages)
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if len(lines) >= 20:
        link_lines = sum(1 for l in lines if _LINK_LINE_RE.match(l))
        if link_lines / len(lines) > 0.6:
            return True

    # Cookie consent walls — high density of cookie-related terms
    sample = lower[:5000]
    cookie_signals = sample.count("cookie") + sample.count("consent") + sample.count("duration")
    cookie_wall_signals = ("consent preferences" in sample or "cookieyes" in sample or "cookie preferences" in sample)
    if cookie_signals > 15 and cookie_wall_signals:
        return True

    return False


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


# Scrape URL with raw markdown (no content filter) and save to file
async def scrape_url_raw_workflow(url: str, output_dir: str) -> list[TextContent]:
    import re
    from pathlib import Path
    from urllib.parse import urlparse

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    markdown_generator = DefaultMarkdownGenerator()

    normal_config = BrowserConfig(headless=True, verbose=False)
    content = await try_scrape_raw(normal_config, None, markdown_generator, url, "networkidle")

    if not content:
        content = await try_scrape_raw(normal_config, None, markdown_generator, url, "domcontentloaded")

    if not content:
        stealth_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
        adapter = UndetectedAdapter()
        stealth_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=stealth_config,
            browser_adapter=adapter
        )
        content = await try_scrape_raw(stealth_config, stealth_strategy, markdown_generator, url, "networkidle")

    if not content:
        hint = get_plugin_hint(url)
        msg = f"Error scraping {url}: No content extracted"
        if hint:
            msg += f"\n\nHint: {hint}"
        return [TextContent(type="text", text=msg)]

    # Generate filename from URL
    parsed = urlparse(url)
    path = parsed.netloc + parsed.path
    safe_name = re.sub(r'[^\w\-.]', '_', path).strip('_')[:120] + ".md"

    # Save with source comment header
    filepath = output_path / safe_name
    filepath.write_text(f"<!-- source: {url} -->\n\n{content}")

    return [TextContent(type="text", text=f"Saved: {filepath} ({len(content):,} chars)")]


# Attempt raw scrape (no content filter), return content or empty string
async def try_scrape_raw(browser_config, crawler_strategy, markdown_generator, url: str, wait_until: str) -> str:
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
        if not content or len(content) < MIN_CONTENT_THRESHOLD:
            return ""
        if is_garbage_content(content):
            return ""
        return content
    except Exception:
        return ""
