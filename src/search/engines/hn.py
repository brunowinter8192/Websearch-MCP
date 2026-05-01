# INFRASTRUCTURE
import logging

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import get_limiter
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://hn.algolia.com/api/v1/search"


# ORCHESTRATOR

# Search HN Algolia and return ranked results
class HNEngine(BaseEngine):
    name = "hn"

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

# Fetch raw hit items from HN Algolia API
async def _fetch_results(query: str, max_results: int) -> list[dict] | None:
    params = {"query": query, "tags": "story", "hitsPerPage": max_results, "page": 0}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(API_URL, params=params)
    if response.status_code in (429, 403):
        logger.warning("HN Algolia rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("hits", [])


# Parse API response hits into SearchResult list
def _parse_results(hits: list[dict]) -> list[SearchResult]:
    results = []
    for i, hit in enumerate(hits):
        title = hit.get("title") or ""
        if not title:
            continue
        object_id = hit.get("objectID", "")
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        points = hit.get("points") or 0
        num_comments = hit.get("num_comments") or 0
        author = hit.get("author") or ""
        snippet = f"{points} points · {num_comments} comments · by {author}"
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            engine="hn",
            position=i + 1,
        ))
    return results
