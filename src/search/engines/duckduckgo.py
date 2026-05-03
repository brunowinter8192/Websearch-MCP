# INFRASTRUCTURE
import asyncio
import json
import logging
from urllib.parse import quote_plus, urlparse, parse_qs

from src.search.browser import new_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, get_limiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://html.duckduckgo.com/html/?q={}&kl=wt-wt"
CAPTCHA_SELECTOR = "form#challenge-form"
MAX_WAIT_CYCLES = 3
WAIT_INTERVAL = 0.2

_JS_WAIT = "return document.querySelectorAll('#links > div.web-result').length"

_JS_CAPTCHA = f"return document.querySelectorAll('{CAPTCHA_SELECTOR}').length"

_JS_PARSE = """
var _cs = document.querySelectorAll('#links > div.web-result');
var _out = [];
for (var _i = 0; _i < _cs.length; _i++) {
    var _c = _cs[_i];
    var _a = _c.querySelector('h2 a');
    var _snip = _c.querySelector('a.result__snippet');
    if (!_a) continue;
    _out.push({href: _a.href, title: _a.textContent.trim(), snippet: _snip ? _snip.textContent.trim() : ''});
}
return JSON.stringify(_out);
"""

# Pre-register with uniform 4 req/min policy (Google-Baseline)
_limiters["duckduckgo"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# DuckDuckGo web search via pydoll stealth browser (html.duckduckgo.com/html/ endpoint)
class DuckDuckGoEngine(BaseEngine):
    name = "duckduckgo"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        logger.info("DuckDuckGo search: %s", query)
        limiter = get_limiter(self.name)
        await limiter.acquire()
        tab = await new_tab()
        search_url = _build_url(query)
        try:
            await tab.go_to(search_url, timeout=20)
            if await _has_captcha(tab):
                logger.warning("DuckDuckGo CAPTCHA detected for: %s", query)
                limiter.backoff()
                return []
            if not await _wait_for_results(tab):
                logger.warning("No DuckDuckGo results loaded for: %s", query)
                limiter.backoff()
                return []
            results = await _parse_results(tab, max_results)
        except Exception as e:
            logger.error("DuckDuckGo search failed: %s", e)
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


# Build DuckDuckGo search URL with encoded query
def _build_url(query: str) -> str:
    return SEARCH_URL.format(quote_plus(query))


# Check for DDG bot-challenge form in DOM
async def _has_captcha(tab) -> bool:
    raw = await tab.execute_script(_JS_CAPTCHA)
    val = _extract_value(raw)
    return bool(val and int(val) > 0)


# Poll for result containers up to MAX_WAIT_CYCLES × WAIT_INTERVAL seconds, return True when found
async def _wait_for_results(tab) -> bool:
    for _ in range(MAX_WAIT_CYCLES):
        raw = await tab.execute_script(_JS_WAIT)
        count = _extract_value(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(WAIT_INTERVAL)
    return False


# Unwrap DDG redirect URLs (duckduckgo.com/l/?uddg=<encoded> pattern)
def _clean_url(href: str) -> str:
    if not href:
        return ""
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    uddg = qs.get("uddg", [None])[0]
    if uddg:
        return uddg
    return href


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
        url = _clean_url(item.get("href", ""))
        if not url:
            continue
        results.append(SearchResult(
            url=url,
            title=item.get("title", ""),
            snippet=item.get("snippet", ""),
            engine="duckduckgo",
            position=i + 1,
        ))
    return results
