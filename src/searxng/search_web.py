# INFRASTRUCTURE
import logging
import requests
from mcp.types import TextContent

logger = logging.getLogger(__name__)

SEARXNG_URL = "http://localhost:8080/search"
MAX_RESULTS = 80
SNIPPET_LENGTH = 5000


# ORCHESTRATOR
def search_web_workflow(
    query: str,
    category: str,
    language: str = "en",
    time_range: str | None = None,
    engines: str | None = None,
    pages: int = 3
) -> list[TextContent]:
    logger.info("Searching: %s (category=%s, pages=%d)", query, category, pages)
    seen_urls: set[str] = set()
    all_results: list = []
    for pageno in range(1, pages + 1):
        page_results = fetch_search_results(query, category, language, time_range, engines, pageno)
        logger.debug("Page %d: %d results", pageno, len(page_results))
        for r in page_results:
            url = r.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)
    formatted_text = format_results(query, all_results)
    return [TextContent(type="text", text=formatted_text)]


# FUNCTIONS

# Fetch raw search results from SearXNG API
def fetch_search_results(
    query: str,
    category: str,
    language: str,
    time_range: str | None,
    engines: str | None,
    pageno: int
) -> list:
    params = {
        "q": query,
        "format": "json",
        "categories": category,
        "language": language,
        "pageno": pageno
    }
    if time_range:
        params["time_range"] = time_range
    if engines:
        params["engines"] = engines

    response = requests.get(SEARXNG_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])[:MAX_RESULTS]


# Transform raw results into plain text numbered list
def format_results(query: str, raw_results: list) -> str:
    if not raw_results:
        return f'No results found for "{query}"'

    lines = [f'Found {len(raw_results)} results for "{query}"\n']

    for idx, item in enumerate(raw_results, 1):
        title = item.get("title", "No title")
        url = item.get("url", "")
        content = item.get("content", "")[:SNIPPET_LENGTH]

        lines.append(f"{idx}. {title}")
        lines.append(f"   URL: {url}")
        if content:
            lines.append(f"   Snippet: {content}")
        lines.append("")

    return "\n".join(lines)
