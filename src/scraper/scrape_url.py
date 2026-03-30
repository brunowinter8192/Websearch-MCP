# INFRASTRUCTURE
import logging
import re

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from mcp.types import TextContent

logger = logging.getLogger(__name__)

_LINK_LINE_RE = re.compile(r'^\[.+\]\(.+\)$')

DEFAULT_MAX_CONTENT_LENGTH = 15000
MIN_CONTENT_THRESHOLD = 200

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

_GARBAGE_MESSAGES = {
    "cookie_wall": "Cookie/consent wall detected — page returns only GDPR consent text, not actual content",
    "login_wall": "Login/paywall detected — page requires authentication",
    "cloudflare": "Cloudflare protection — page requires browser verification",
    "http_error": "HTTP error page (404/403)",
    "nav_dump": "Navigation dump — page returned only links, no content",
    "crawl4ai_error": "Crawl4AI extraction error",
}


# ORCHESTRATOR
async def scrape_url_workflow(url: str, max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH) -> list[TextContent]:
    logger.info("Scraping: %s", url)
    markdown_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48)
    )

    normal_config = BrowserConfig(headless=True, verbose=False)
    content, last_garbage = await try_scrape(normal_config, None, markdown_generator, url, "networkidle")

    if not content:
        c2, g2 = await try_scrape(normal_config, None, markdown_generator, url, "domcontentloaded")
        if g2:
            last_garbage = g2
        content = c2

    if not content:
        stealth_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
        adapter = UndetectedAdapter()
        stealth_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=stealth_config,
            browser_adapter=adapter
        )
        c3, g3 = await try_scrape(stealth_config, stealth_strategy, markdown_generator, url, "networkidle")
        if g3:
            last_garbage = g3
        content = c3

    if not content:
        hint = get_plugin_hint(url)
        reason = _GARBAGE_MESSAGES[last_garbage] if last_garbage else "No content extracted"
        msg = f"Error scraping {url}: {reason}"
        if hint:
            msg += f"\n\nHint: {hint}"
        return [TextContent(type="text", text=msg)]

    logger.info("Scrape complete: %s (%d chars)", url, len(content))
    truncated = truncate_content(content, max_content_length)
    return [TextContent(type="text", text=f"# Content from: {url}\n\n{truncated}")]


# FUNCTIONS

# Attempt scrape with given wait strategy, return (content, garbage_type) tuple
async def try_scrape(browser_config, crawler_strategy, markdown_generator, url: str, wait_until: str) -> tuple[str, str | None]:
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
            return "", None
        content = result.markdown.fit_markdown
        if len(content) < MIN_CONTENT_THRESHOLD and result.markdown.raw_markdown:
            content = result.markdown.raw_markdown
        garbage_type = is_garbage_content(content)
        if garbage_type:
            logger.warning("Garbage detected [%s]: %s", garbage_type, url)
            return "", garbage_type
        return content, None
    except Exception as e:
        logger.warning("Failed to scrape %s: %s", url, e)
        return "", None


# Detect garbage content: error pages, cookie walls, login walls, navigation dumps
def is_garbage_content(content: str) -> str | None:
    lower = content.lower()

    crawl4ai_errors = ["crawl4ai error:", "document is empty", "page is not fully supported"]
    if any(p in lower for p in crawl4ai_errors):
        return "crawl4ai_error"

    if len(content) < 1000:
        error_keywords = ["not_found", "404", "403", "forbidden", "access denied", "page not found"]
        if any(k in lower for k in error_keywords):
            return "http_error"

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if len(lines) >= 20:
        link_lines = sum(1 for l in lines if _LINK_LINE_RE.match(l))
        if link_lines / len(lines) > 0.6:
            return "nav_dump"

    sample = lower[:5000]
    cookie_signals = sample.count("cookie") + sample.count("consent") + sample.count("duration")
    cookie_wall_signals = ("consent preferences" in sample or "cookieyes" in sample or "cookie preferences" in sample)
    if cookie_signals > 15 and cookie_wall_signals:
        return "cookie_wall"

    if len(content) < 2000:
        login_patterns = [
            "sign in", "log in", "login", "subscribe to continue", "create account",
            "create an account", "premium content", "paywall", "members only", "subscriber only",
        ]
        if any(p in lower for p in login_patterns):
            return "login_wall"

    if len(content) < 500:
        if "checking your browser" in lower or "enable javascript and cookies" in lower:
            return "cloudflare"

    if "just a moment" in lower and "cloudflare" in lower:
        return "cloudflare"

    return None


# Truncate content at paragraph boundary if too long
def truncate_content(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n\n')
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[Content truncated...]"


# Return generic plugin routing hint for failed scrapes
def get_plugin_hint(url: str) -> str:
    return "This domain may have a dedicated MCP plugin."
