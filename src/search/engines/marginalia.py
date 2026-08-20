# INFRASTRUCTURE
import logging

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://api2.marginalia-search.com/search"
API_KEY = "public"

_limiters["marginalia"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Search Marginalia (independent index, small/old/text-heavy web) and return structured results — HTTP API, no DOM-drift/CAPTCHA patterns
class MarginaliaEngine(BaseEngine):
    name = "marginalia"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        logger.info("Marginalia search: %s", query)
        items = await _fetch_results(query, max_results)
        if items is None:
            return []
        return _parse_results(items)


# FUNCTIONS

# Fetch raw result items from the Marginalia public API; returns None on rate-limit
async def _fetch_results(query: str, max_results: int) -> list[dict] | None:
    params: dict = {"query": query, "count": max_results}
    headers: dict = {"API-Key": API_KEY}
    async with httpx.AsyncClient(timeout=3.6) as client:
        response = await client.get(API_URL, params=params, headers=headers)
    if response.status_code in (429, 403):
        logger.warning("Marginalia rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("results", [])


# Parse Marginalia result items into SearchResult list
def _parse_results(items: list[dict]) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items):
        url = item.get("url", "")
        if not url:
            continue
        results.append(SearchResult(
            url=url,
            title=item.get("title", ""),
            snippet=item.get("description", ""),
            engine="marginalia",
            position=i + 1,
        ))
    return results
