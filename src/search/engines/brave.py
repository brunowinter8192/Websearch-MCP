# INFRASTRUCTURE
import asyncio
import json
import logging
from urllib.parse import quote_plus

from src.search.browser import get_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import get_limiter
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://search.brave.com/search?q={query}&source=web"
WAIT_SECONDS = 3.0

_EXTRACT_JS = """
JSON.stringify(
  Array.from(document.querySelectorAll('div.snippet')).map(function(el) {
    var a = el.querySelector('a.result-header');
    var snip = el.querySelector('p.snippet-description');
    return {
      title: a ? a.innerText.trim() : '',
      url: a ? a.href : '',
      snippet: snip ? snip.innerText.trim() : ''
    };
  }).filter(function(r) { return r.url; })
)
"""


# ORCHESTRATOR

# Search Brave via pydoll stealth browser and return ranked results
class BraveEngine(BaseEngine):
    name = "brave"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        limiter = get_limiter(self.name)
        await limiter.acquire()
        items = await _fetch_results(query)
        if items is None:
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return _parse_results(items, max_results)


# FUNCTIONS

# Navigate to Brave search URL and extract result items via JS evaluation
async def _fetch_results(query: str) -> list[dict] | None:
    url = SEARCH_URL.format(query=quote_plus(query))
    tab = await get_tab()
    try:
        await tab.go_to(url, timeout=30)
        await asyncio.sleep(WAIT_SECONDS)
        response = await tab.execute_script(_EXTRACT_JS, return_by_value=True)
        raw = _extract_value(response)
        items = json.loads(raw)
        if not items:
            logger.warning("Brave: no results extracted from %s", url)
        return items
    except Exception as e:
        logger.warning("Brave fetch failed: %s", e)
        return None


# Extract the JS return value from pydoll execute_script response (handles nested structure)
def _extract_value(response: dict) -> str:
    if isinstance(response, dict):
        direct = response.get("value")
        if direct is not None:
            return direct
        level1 = response.get("result", {})
        if isinstance(level1, dict):
            v = level1.get("value")
            if v is not None:
                return v
            level2 = level1.get("result", {})
            if isinstance(level2, dict):
                v = level2.get("value")
                if v is not None:
                    return v
    return "[]"


# Parse extracted item dicts into SearchResult list, capped at max_results
def _parse_results(items: list[dict], max_results: int) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items):
        if i >= max_results:
            break
        if not item.get("url"):
            continue
        results.append(SearchResult(
            url=item["url"],
            title=item.get("title", ""),
            snippet=item.get("snippet", ""),
            engine="brave",
            position=i + 1,
        ))
    return results
