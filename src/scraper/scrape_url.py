# INFRASTRUCTURE
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from mcp.types import TextContent

logger = logging.getLogger(__name__)

_LINK_LINE_RE = re.compile(r'^\[.+\]\(.+\)$')

DEFAULT_MAX_CONTENT_LENGTH = 15000
MIN_CONTENT_THRESHOLD = 200

CONSENT_WORDS = ["cookie", "consent", "einwilligung", "tracking", "akzeptieren", "datenschutz", "zweck"]
CONSENT_DENSITY_THRESHOLD = 5
CONSENT_SKIP_OFFSET = 300

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
    content, last_garbage, last_status_code = await try_scrape(normal_config, None, markdown_generator, url, "networkidle")

    if not content:
        c2, g2, s2 = await try_scrape(normal_config, None, markdown_generator, url, "domcontentloaded")
        if g2:
            last_garbage = g2
        if s2:
            last_status_code = s2
        content = c2

    if not content:
        stealth_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
        adapter = UndetectedAdapter()
        stealth_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=stealth_config,
            browser_adapter=adapter
        )
        c3, g3, s3 = await try_scrape(stealth_config, stealth_strategy, markdown_generator, url, "networkidle")
        if g3:
            last_garbage = g3
        if s3:
            last_status_code = s3
        content = c3

    if not content:
        log_scrape_failure(url, last_garbage, last_status_code)
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

# Attempt scrape with given wait strategy, return (content, garbage_type, status_code) tuple
async def try_scrape(browser_config, crawler_strategy, markdown_generator, url: str, wait_until: str) -> tuple[str, str | None, int | None]:
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
        status_code = result.status_code if hasattr(result, 'status_code') else None
        if status_code and status_code >= 400:
            logger.warning("HTTP %d detected: %s", status_code, url)
            return "", "http_error", status_code
        if not result.markdown:
            return "", None, status_code
        content = result.markdown.fit_markdown
        if len(content) < MIN_CONTENT_THRESHOLD and result.markdown.raw_markdown:
            content = result.markdown.raw_markdown
        garbage_type = is_garbage_content(content)
        if garbage_type == "cookie_wall":
            stripped = strip_consent_prefix(content)
            if stripped != content and is_garbage_content(stripped) is None:
                logger.info("Consent prefix stripped: %s (%d chars removed)", url, len(content) - len(stripped))
                return stripped, None, status_code
        if garbage_type:
            logger.warning("Garbage detected [%s]: %s", garbage_type, url)
            return "", garbage_type, status_code
        return content, None, status_code
    except Exception as e:
        logger.warning("Failed to scrape %s: %s", url, e)
        return "", None, None


# Append one JSONL failure record to dev/scrape_pipeline/failures.jsonl
def log_scrape_failure(url: str, garbage_type: str | None, status_code: int | None) -> None:
    project_root = os.environ.get("SEARXNG_PROJECT_ROOT")
    if not project_root:
        return
    try:
        log_path = Path(project_root) / "dev" / "scrape_pipeline" / "failures.jsonl"
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "url": url,
            "garbage_type": garbage_type,
            "status_code": status_code,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning("Failed to log scrape failure: %s", e)


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


# Strip leading consent block: detect by keyword density, cut before first heading after offset
def strip_consent_prefix(content: str) -> str:
    if not content:
        return content
    sample = content[:3000].lower()
    density = sum(sample.count(w) for w in CONSENT_WORDS)
    if density <= CONSENT_DENSITY_THRESHOLD:
        return content
    match = re.search(r'\n(#{1,2} )', content[CONSENT_SKIP_OFFSET:])
    if match:
        pos = CONSENT_SKIP_OFFSET + match.start() + 1
        return content[pos:]
    return content


# Truncate content at paragraph boundary if too long
def truncate_content(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n\n')
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[Content truncated...]"


# Return plugin hint for domains with dedicated MCP plugins, empty string otherwise
def get_plugin_hint(url: str) -> str:
    from urllib.parse import urlparse
    from src.routing import PLUGIN_ROUTED_DOMAINS
    try:
        host = (urlparse(url).hostname or "").removeprefix("www.")
    except Exception:
        return ""
    for domain in PLUGIN_ROUTED_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return f"This domain has a dedicated MCP plugin. Use the appropriate plugin tool instead of scrape_url."
    return ""
