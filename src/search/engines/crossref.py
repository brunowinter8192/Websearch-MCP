# INFRASTRUCTURE
import logging

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import get_limiter
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://api.crossref.org/works"


# ORCHESTRATOR

# Search CrossRef and return ranked results
class CrossRefEngine(BaseEngine):
    name = "crossref"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        limiter = get_limiter(self.name)
        await limiter.acquire()
        items = await _fetch_results(query, max_results)
        if items is None:
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return _parse_results(items)


# FUNCTIONS

# Fetch raw work items from CrossRef API
async def _fetch_results(query: str, rows: int) -> list[dict] | None:
    params = {"query": query, "rows": rows}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(API_URL, params=params)
    if response.status_code in (429, 403):
        logger.warning("CrossRef rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("message", {}).get("items", [])


# Parse API response items into SearchResult list
def _parse_results(items: list[dict]) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items):
        doi = item.get("DOI", "")
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        title_list = item.get("title") or []
        title = title_list[0] if title_list else ""
        abstract = item.get("abstract") or ""
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=abstract,
            engine="crossref",
            position=i + 1,
        ))
    return results
