# INFRASTRUCTURE
import asyncio
import nest_asyncio
from typing import Annotated, Literal
from fastmcp import FastMCP
from pydantic import Field

nest_asyncio.apply()

from src.scraper.search_web import search_web_workflow
from src.scraper.scrape_urls import scrape_urls_workflow

mcp = FastMCP("SearXNG")


# TOOLS

@mcp.tool
def search_web(
    query: Annotated[str, Field(description="Search query (e.g., 'fastapi async tutorial', 'python memory profiling')")],
    category: Annotated[
        Literal["general", "news", "it", "science"],
        Field(description="Search category: general (web/books), news (articles), it (code/packages/Q&A), science (publications)")
    ] = "general"
) -> dict:
    """Use when user needs to search the web for information. Good for finding documentation, tutorials, code examples, news articles, or scientific papers."""
    return search_web_workflow(query, category)


@mcp.tool
def scrape_urls(
    urls: Annotated[list[str], Field(description="List of URLs to scrape (e.g., ['https://example.com', 'https://docs.python.org'])")],
    concurrency: Annotated[int, Field(description="Number of parallel requests (default: 5, max recommended: 10)")] = 5
) -> list[dict]:
    """Use when user needs to fetch full page content from URLs. Handles JavaScript-rendered pages. Good for extracting documentation, articles, or any web content after getting URLs from search_web."""
    return asyncio.run(scrape_urls_workflow(urls, concurrency))


if __name__ == "__main__":
    mcp.run()
