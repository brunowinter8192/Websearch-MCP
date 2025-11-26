# INFRASTRUCTURE
from playwright.async_api import async_playwright, Browser
from mcp.types import TextContent

from src.scraper.html_parser import parse_html
from src.scraper.content_filter import filter_content
from src.scraper.markdown_converter import to_markdown

TIMEOUT_MS = 30000
DEFAULT_MAX_CONTENT_LENGTH = 100000


# ORCHESTRATOR
async def scrape_url_workflow(url: str, max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH) -> list[TextContent]:
    browser = await init_browser()
    raw_html = await fetch_url_content(url, browser)
    await cleanup_browser(browser)

    if isinstance(raw_html, Exception):
        error_msg = f"Error scraping {url}: {str(raw_html)}"
        return [TextContent(type="text", text=error_msg)]

    extracted_content = extract_single_content(url, raw_html, max_content_length)
    return [TextContent(type="text", text=extracted_content)]


# Parse and convert single HTML to markdown with header
def extract_single_content(url: str, html: str, max_content_length: int) -> str:
    parsed = parse_html(html)
    filtered = filter_content(parsed)
    markdown = to_markdown(filtered, max_content_length)
    truncated = truncate_content(markdown, max_content_length)
    return f"# Content from: {url}\n\n{truncated}"


# FUNCTIONS

# Initialize headless Chromium browser instance with stealth mode
async def init_browser() -> Browser:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    return browser


# Fetch HTML content from URL using Playwright with stealth context
async def fetch_url_content(url: str, browser: Browser) -> str | Exception:
    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")

        content_selectors = ["main", "article", "[class*='content']", "h1"]
        try:
            await page.wait_for_selector(", ".join(content_selectors), state="visible", timeout=5000)
        except Exception:
            pass

        content = await page.content()
        await context.close()
        return content
    except Exception as e:
        return e


# Release browser resources
async def cleanup_browser(browser: Browser) -> None:
    await browser.close()


# Truncate content if too long
def truncate_content(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n\n')
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[Content truncated...]"
