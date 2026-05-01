# INFRASTRUCTURE
import asyncio
import logging
from mcp.types import TextContent

from src.search.browser import close_browser
from src.search.engines.google import GoogleEngine
from src.search.engines.bing import BingEngine
from src.search.engines.scholar import ScholarEngine
from src.search.engines.crossref import CrossRefEngine
from src.search.engines.hn import HNEngine

logger = logging.getLogger(__name__)

SNIPPET_LENGTH = 5000

ENGINES = {
    "google": GoogleEngine(),
    "bing": BingEngine(),
    "google scholar": ScholarEngine(),
    "crossref": CrossRefEngine(),
    "hn": HNEngine(),
}


# ORCHESTRATOR

# Search all enabled engines concurrently, deduplicate results, format as TextContent
async def search_web_workflow(
    query: str,
    category: str,
    language: str = "en",
    time_range: str | None = None,
    engines: str | None = None,
    pages: int = 3
) -> list[TextContent]:
    logger.info("Searching: %s (category=%s, pages=%d)", query, category, pages)
    max_results = pages * 10
    selected = _select_engines(engines)
    raw_results = await _query_engines_concurrent(query, language, max_results, selected)
    deduped = _deduplicate(raw_results)
    formatted_text = _format_results(query, deduped)
    return [TextContent(type="text", text=formatted_text)]


# Run N queries sequentially in shared Chrome, close browser in finally
async def search_batch_workflow(
    queries: list[str],
    category: str,
    language: str = "en",
    time_range: str | None = None,
    engines: str | None = None,
    pages: int = 3,
) -> list[list[TextContent]]:
    results = []
    try:
        for q in queries:
            results.append(await search_web_workflow(q, category, language, time_range, engines, pages))
    finally:
        await close_browser()
    return results


# Synchronous wrapper for dev scripts — runs event loop internally
def fetch_search_results(
    query: str,
    category: str,
    language: str,
    time_range: str | None,
    engines: str | None,
    pageno: int
) -> list:
    selected = _select_engines(engines)
    results = asyncio.run(_query_engines_concurrent(query, language, 10, selected))
    return [
        {
            "url": r.url,
            "title": r.title,
            "content": r.snippet,
            "engines": [r.engine],
        }
        for r in results
    ]


# FUNCTIONS

# Filter engine registry by comma-separated names param or return all
def _select_engines(engines: str | None) -> dict:
    if not engines:
        return ENGINES
    names = [e.strip().lower() for e in engines.split(",")]
    return {k: v for k, v in ENGINES.items() if k in names}


# Query selected engines concurrently, collect all SearchResult objects
async def _query_engines_concurrent(query: str, language: str, max_results: int, selected: dict) -> list:
    tasks = [engine.search(query, language, max_results) for engine in selected.values()]
    results_per_engine = await asyncio.gather(*tasks, return_exceptions=True)
    combined = []
    for r in results_per_engine:
        if isinstance(r, Exception):
            logger.warning("Engine error: %s", r)
        else:
            combined.extend(r)
    return combined


# Deduplicate by URL, preserving first occurrence order
def _deduplicate(results: list) -> list:
    seen: set[str] = set()
    deduped = []
    for r in results:
        if r.url not in seen:
            seen.add(r.url)
            deduped.append(r)
    return deduped


# Format SearchResult list as plain text numbered list
def _format_results(query: str, results: list) -> str:
    if not results:
        return f'No results found for "{query}"'
    lines = [f'Found {len(results)} results for "{query}"\n']
    for idx, r in enumerate(results, 1):
        lines.append(f"{idx}. {r.title}")
        lines.append(f"   URL: {r.url}")
        if r.snippet:
            lines.append(f"   Snippet: {r.snippet[:SNIPPET_LENGTH]}")
        lines.append("")
    return "\n".join(lines)
