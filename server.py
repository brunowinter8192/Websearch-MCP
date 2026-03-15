# INFRASTRUCTURE
import asyncio
import nest_asyncio
from typing import Annotated, Literal
from fastmcp import FastMCP
from mcp.types import TextContent
from pydantic import Field

nest_asyncio.apply()

from src.searxng.search_web import search_web_workflow
from src.scraper.scrape_url import scrape_url_workflow, scrape_url_raw_workflow
from src.scraper.explore_site import explore_site_workflow

mcp = FastMCP("SearXNG")


# TOOLS

@mcp.tool
def search_web(
    query: Annotated[str, Field(description="Search query string (e.g., 'python async web scraping')")],
    category: Annotated[
        Literal["general", "news", "it", "science"],
        Field(description="Search category: general (web), news (recent articles), it (tech/packages), science (academic)")
    ] = "general",
    language: Annotated[
        str,
        Field(description="Language code (e.g., 'en', 'de', 'fr'). Default: 'en'")
    ] = "en",
    time_range: Annotated[
        Literal["day", "month", "year"] | None,
        Field(description="Filter by time: day (last 24h), month (last 30d), year (last 365d)")
    ] = None,
    engines: Annotated[
        str | None,
        Field(description="Comma-separated engine list (e.g., 'google,brave'). Default: all engines in category")
    ] = None,
    pageno: Annotated[
        int,
        Field(description="Page number for pagination. Default: 1")
    ] = 1
) -> list[TextContent]:
    """Use when user needs web search results. Searches via SearXNG meta-search engine.
    Good for finding documentation, articles, code examples, news."""
    return search_web_workflow(query, category, language, time_range, engines, pageno)


@mcp.tool
def scrape_url(
    url: str,
    max_content_length: int = 15000
) -> list[TextContent]:
    """Scrape URL."""
    return asyncio.run(scrape_url_workflow(url, max_content_length))


@mcp.tool
def scrape_url_raw(
    url: Annotated[str, Field(description="URL to scrape and save as markdown file")],
    output_dir: Annotated[str, Field(description="Directory to save the markdown file (created if not exists)")]
) -> list[TextContent]:
    """Scrape URL with full-fidelity raw markdown (no content filter) and save as .md file.
    Use for RAG indexing: scrape → save → /rag:web-md-index. Preserves code blocks, tables, all formatting."""
    return asyncio.run(scrape_url_raw_workflow(url, output_dir))


@mcp.tool
def explore_site(
    url: Annotated[str, Field(description="Seed URL to start exploration (e.g., 'https://docs.example.com')")],
    max_pages: Annotated[int, Field(description="Maximum number of pages to discover (default: 200)")] = 200,
    url_pattern: Annotated[
        str | None,
        Field(description="Wildcard URL filter to limit exploration scope (e.g., '*mps*', '*/api/*'). Only URLs matching this pattern are followed.")
    ] = None
) -> list[TextContent]:
    """Use when user wants to understand a website's structure before crawling.
    Shows URL tree with depth levels, page counts, and estimated total size.
    Good for deciding crawl scope (depth, filters, max_pages) before running crawl_site."""
    return asyncio.run(explore_site_workflow(url, max_pages, url_pattern))


if __name__ == "__main__":
    mcp.run()
