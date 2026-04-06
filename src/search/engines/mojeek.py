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

# arc=none avoids Mojeek 403 bot detection (arc=us triggers it)
SEARCH_URL = "https://www.mojeek.com/search?q={query}&arc=none"
WAIT_SECONDS = 3.0

# Selectors verified from SearXNG Mojeek engine patch (mojeek.py)
# ul.results-standard li → a.ob (URL), h2 a (title), p.s (snippet)
_EXTRACT_JS = """
JSON.stringify(
  Array.from(document.querySelectorAll('ul.results-standard li')).map(function(li) {
    var urlEl = li.querySelector('a.ob');
    var titleEl = li.querySelector('h2 a');
    var snippetEl = li.querySelector('p.s');
    return {
      title: titleEl ? titleEl.innerText.trim() : '',
      url: urlEl ? urlEl.href : '',
      snippet: snippetEl ? snippetEl.innerText.trim() : ''
    };
  }).filter(function(r) { return r.url; })
)
"""


# ORCHESTRATOR

# Search Mojeek via pydoll stealth browser and return ranked results
class MojeekEngine(BaseEngine):
    name = "mojeek"

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

# Navigate to Mojeek search URL and extract result items via JS evaluation
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
            logger.warning("Mojeek: no results extracted from %s", url)
        return items
    except Exception as e:
        logger.warning("Mojeek fetch failed: %s", e)
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
            engine="mojeek",
            position=i + 1,
        ))
    return results
