# INFRASTRUCTURE
import logging

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import get_limiter
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,url,abstract"


# ORCHESTRATOR

# Search Semantic Scholar and return ranked results
class SemanticScholarEngine(BaseEngine):
    name = "semantic_scholar"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        limiter = get_limiter(self.name)
        await limiter.acquire()
        results = await _fetch_results(query, max_results)
        if results is None:
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return _parse_results(results)


# FUNCTIONS

# Fetch raw paper search results from Semantic Scholar API
async def _fetch_results(query: str, limit: int) -> list[dict] | None:
    params = {"query": query, "limit": limit, "fields": FIELDS}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(API_URL, params=params)
    if response.status_code in (429, 403):
        logger.warning("Semantic Scholar rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("data", [])


# Parse API response items into SearchResult list
def _parse_results(items: list[dict]) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items):
        url = item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"
        results.append(SearchResult(
            url=url,
            title=item.get("title") or "",
            snippet=item.get("abstract") or "",
            engine="semantic_scholar",
            position=i + 1,
        ))
    return results
