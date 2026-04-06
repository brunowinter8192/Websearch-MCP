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

SEARCH_URL = "https://www.bing.com/search?q={query}&setlang={language}&count={max_results}"
WAIT_SECONDS = 3.0

_EXTRACT_JS = """
JSON.stringify(
  Array.from(document.querySelectorAll('li.b_algo')).map(function(el) {
    var a = el.querySelector('h2 a');
    var snip = el.querySelector('p.b_lineclamp2') || el.querySelector('.b_caption p');
    return {
      title: a ? a.innerText.trim() : '',
      url: a ? a.href : '',
      snippet: snip ? snip.innerText.trim() : ''
    };
  }).filter(function(r) { return r.url; })
)
"""


# ORCHESTRATOR

# Search Bing via pydoll stealth browser and return ranked results
class BingEngine(BaseEngine):
    name = "bing"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        limiter = get_limiter(self.name)
        await limiter.acquire()
        items = await _fetch_results(query, language, max_results)
        if items is None:
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return _parse_results(items)


# FUNCTIONS

# Navigate to Bing search URL and extract result items via JS evaluation
async def _fetch_results(query: str, language: str, max_results: int) -> list[dict] | None:
    url = SEARCH_URL.format(
        query=quote_plus(query),
        language=language,
        max_results=max_results,
    )
    tab = await get_tab()
    try:
        await tab.go_to(url, timeout=30)
        await asyncio.sleep(WAIT_SECONDS)
        response = await tab.execute_script(_EXTRACT_JS, return_by_value=True)
        raw = _extract_value(response)
        items = json.loads(raw)
        if not items:
            logger.warning("Bing: no results extracted from %s", url)
        return items
    except Exception as e:
        logger.warning("Bing fetch failed: %s", e)
        return None


# Extract the JS return value from pydoll execute_script response (handles nested structure)
def _extract_value(response: dict) -> str:
    if isinstance(response, dict):
        # Try direct access (execute_script may flatten the CDP envelope)
        direct = response.get("value")
        if direct is not None:
            return direct
        # Try 1-level nesting: response['result']['value']
        level1 = response.get("result", {})
        if isinstance(level1, dict):
            v = level1.get("value")
            if v is not None:
                return v
            # Try 2-level nesting: response['result']['result']['value']
            level2 = level1.get("result", {})
            if isinstance(level2, dict):
                v = level2.get("value")
                if v is not None:
                    return v
    return "[]"


# Parse extracted item dicts into SearchResult list
def _parse_results(items: list[dict]) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items):
        if not item.get("url"):
            continue
        results.append(SearchResult(
            url=item["url"],
            title=item.get("title", ""),
            snippet=item.get("snippet", ""),
            engine="bing",
            position=i + 1,
        ))
    return results
