# INFRASTRUCTURE
import asyncio
import nest_asyncio
from typing import Literal
from fastmcp import FastMCP
from mcp.types import TextContent

nest_asyncio.apply()

from src.searxng.search_web import search_web_workflow
from src.scraper.scrape_url import scrape_url_workflow, scrape_url_raw_workflow
from src.scraper.explore_site import explore_site_workflow

mcp = FastMCP("SearXNG")


# TOOLS

@mcp.tool
def search_web(
    query: str,
    category: Literal["general", "news", "it", "science"] = "general",
    language: str = "en",
    time_range: Literal["day", "month", "year"] | None = None,
    engines: str | None = None,
    pageno: int = 1
) -> list[TextContent]:
    """Search the web."""
    return search_web_workflow(query, category, language, time_range, engines, pageno)


@mcp.tool
def scrape_url(url: str, max_content_length: int = 15000) -> list[TextContent]:
    """Scrape URL."""
    return asyncio.run(scrape_url_workflow(url, max_content_length))


@mcp.tool
def scrape_url_raw(url: str, output_dir: str) -> list[TextContent]:
    """Scrape URL to markdown file."""
    return asyncio.run(scrape_url_raw_workflow(url, output_dir))


@mcp.tool
def explore_site(
    url: str,
    max_pages: int = 200,
    url_pattern: str | None = None
) -> list[TextContent]:
    """Explore website structure."""
    return asyncio.run(explore_site_workflow(url, max_pages, url_pattern))


if __name__ == "__main__":
    mcp.run()
