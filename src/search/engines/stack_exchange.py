# INFRASTRUCTURE
import html
import logging
import os
import re
from datetime import datetime, timezone

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://api.stackexchange.com/2.3/search/advanced"

_limiters["stack_exchange"] = RateLimiter(max_requests=4, window_seconds=60)

_KEY_WARNED = False


# ORCHESTRATOR

# Search Stack Exchange stackoverflow and return structured results — HTTP API, no DOM-drift/CAPTCHA patterns
class StackExchangeEngine(BaseEngine):
    name = "stack_exchange"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        logger.info("Stack Exchange search: %s", query)
        items = await _fetch_results(query, max_results)
        if items is None:
            return []
        return _parse_results(items)


# FUNCTIONS

# Fetch raw question items from Stack Exchange search/advanced API
async def _fetch_results(query: str, max_results: int) -> list[dict] | None:
    global _KEY_WARNED
    params: dict = {
        "q": query,
        "site": "stackoverflow",
        "pagesize": max_results,
        "sort": "relevance",
        "order": "desc",
        "filter": "withbody",
    }
    api_key = os.environ.get("STACK_EXCHANGE_API_KEY", "")
    if api_key:
        params["key"] = api_key
    elif not _KEY_WARNED:
        logger.info("STACK_EXCHANGE_API_KEY not set — anonymous quota (300 req/day)")
        _KEY_WARNED = True
    async with httpx.AsyncClient(timeout=3.6) as client:
        response = await client.get(API_URL, params=params)
    if response.status_code in (429, 403):
        logger.warning("Stack Exchange rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("items", [])


# Parse SE question items into SearchResult list
def _parse_results(items: list[dict]) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items):
        url = item.get("link", "")
        if not url:
            continue
        title = html.unescape(item.get("title", ""))
        body = item.get("body", "")
        if body:
            snippet = _strip_html(body)[:500]
        else:
            score = item.get("score", 0)
            answers = item.get("answer_count", 0)
            tags = ", ".join(item.get("tags", [])[:5])
            snippet = f"Score {score} · {answers} answers · tagged {tags}"
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            engine="stack_exchange",
            position=i + 1,
            date=_extract_date(item),
        ))
    return results


# Strip HTML tags from body text and normalise whitespace
def _strip_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return ' '.join(text.split())


# creation_date is a Unix epoch int (part of the default filter, always present) -> day-precision ISO date
def _extract_date(item: dict) -> str | None:
    ts = item.get("creation_date")
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
