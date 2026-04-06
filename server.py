# INFRASTRUCTURE
import asyncio
import atexit
import nest_asyncio
from typing import Literal
from fastmcp import FastMCP
from mcp.types import TextContent

from src.routing import check_plugin_routed
from src.search.search_web import search_web_workflow
from src.search.browser import close_browser
from src.scraper.scrape_url import scrape_url_workflow
from src.scraper.scrape_url_raw import scrape_url_raw_workflow
from src.scraper.explore_site import explore_site_workflow
from src.scraper.download_pdf import download_pdf_workflow

nest_asyncio.apply()
atexit.register(lambda: asyncio.run(close_browser()))

mcp = FastMCP("SearXNG")


# TOOL REGISTRATION

@mcp.tool
def search_web(
    query: str,
    category: Literal["general", "news", "it", "science"] = "general",
    language: str = "en",
    time_range: Literal["day", "month", "year"] | None = None,
    engines: str | None = None,
    pages: int = 3
) -> list[TextContent]:
    """Search the web. Fetches `pages` result pages and returns combined deduplicated results."""
    return asyncio.run(search_web_workflow(query, category, language, time_range, engines, pages))


@mcp.tool
def scrape_url(url: str, max_content_length: int = 15000) -> list[TextContent]:
    """Scrape URL."""
    if blocked := check_plugin_routed(url):
        return blocked
    return asyncio.run(scrape_url_workflow(url, max_content_length))


@mcp.tool
def scrape_url_raw(url: str, output_dir: str) -> list[TextContent]:
    """Scrape URL to markdown file."""
    if blocked := check_plugin_routed(url):
        return blocked
    return asyncio.run(scrape_url_raw_workflow(url, output_dir))


@mcp.tool
def explore_site(
    url: str,
    max_pages: int = 200,
    url_pattern: str | None = None
) -> list[TextContent]:
    """Explore website structure."""
    return asyncio.run(explore_site_workflow(url, max_pages, url_pattern))


@mcp.tool
def download_pdf(url: str, output_dir: str = "/tmp") -> list[TextContent]:
    """Download PDF file from URL."""
    return download_pdf_workflow(url, output_dir)


if __name__ == "__main__":
    mcp.run()
