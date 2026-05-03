# INFRASTRUCTURE
import asyncio
import json
import logging
from urllib.parse import quote_plus

from src.search.browser import new_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, get_limiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://lobste.rs/search?q={}&what=stories&order=relevance"
MAX_WAIT_CYCLES = 3
WAIT_INTERVAL = 0.2

_JS_WAIT = "return document.querySelectorAll('li.story').length"

_JS_PARSE = """
var _cs = document.querySelectorAll('li.story');
var _out = [];
for (var _i = 0; _i < _cs.length; _i++) {
    var _li = _cs[_i];
    var _a = _li.querySelector('a.u-url');
    var _dom = _li.querySelector('a.domain');
    if (!_a || !_a.href) continue;
    _out.push({url: _a.href, title: _a.textContent.trim(), snippet: _dom ? _dom.textContent.trim() : ''});
}
return JSON.stringify(_out);
"""

# Pre-register with uniform 4 req/min policy (Google-Baseline)
_limiters["lobsters"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Lobsters web search via pydoll stealth browser (lobste.rs/search endpoint, direct hrefs, no captcha check)
class LobstersEngine(BaseEngine):
    name = "lobsters"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        logger.info("Lobsters search: %s", query)
        limiter = get_limiter(self.name)
        await limiter.acquire()
        tab = await new_tab()
        search_url = _build_url(query)
        try:
            await tab.go_to(search_url, timeout=20)
            if not await _wait_for_results(tab):
                logger.warning("No Lobsters results loaded for: %s", query)
                limiter.backoff()
                return []
            results = await _parse_results(tab, max_results)
        except Exception as e:
            logger.error("Lobsters search failed: %s", e)
            limiter.backoff()
            return []
        finally:
            await tab.close()
        limiter.reset_backoff()
        return results


# FUNCTIONS

# Extract primitive value from CDP execute_script result dict
def _extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Build Lobsters search URL with encoded query
def _build_url(query: str) -> str:
    return SEARCH_URL.format(quote_plus(query))


# Poll for result containers up to MAX_WAIT_CYCLES × WAIT_INTERVAL seconds, return True when found
async def _wait_for_results(tab) -> bool:
    for _ in range(MAX_WAIT_CYCLES):
        raw = await tab.execute_script(_JS_WAIT)
        count = _extract_value(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(WAIT_INTERVAL)
    return False


# Query DOM for search result containers and return SearchResult list
async def _parse_results(tab, max_results: int) -> list[SearchResult]:
    raw = await tab.execute_script(_JS_PARSE)
    value = _extract_value(raw)
    if not value:
        return []
    try:
        items = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
    results = []
    for i, item in enumerate(items[:max_results]):
        url = item.get("url", "")
        if not url:
            continue
        results.append(SearchResult(
            url=url,
            title=item.get("title", ""),
            snippet=item.get("snippet", ""),
            engine="lobsters",
            position=i + 1,
        ))
    return results
