# INFRASTRUCTURE
import asyncio
import json
import logging
import re
from urllib.parse import quote_plus

from src.search.browser import new_tab, kill_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult
from src.search import status as S

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
    var _time = _li.querySelector('time');
    if (!_a || !_a.href) continue;
    _out.push({
        url: _a.href,
        title: _a.textContent.trim(),
        snippet: _dom ? _dom.textContent.trim() : '',
        date_raw: _time ? (_time.getAttribute('datetime') || '') : ''
    });
}
return JSON.stringify(_out);
"""

# Uniform 4 req/min across all engines (Google-Baseline, normalized 2026-05-04)
_limiters["lobsters"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Lobsters web search via pydoll stealth browser (lobste.rs/search endpoint, direct hrefs, no captcha check)
class LobstersEngine(BaseEngine):
    name = "lobsters"

    # Full search logic with empty-reason diagnosis; exceptions propagate to _engine_with_timing
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None]:
        logger.info("Lobsters search: %s", query)
        tab = await new_tab()
        search_url = _build_url(query)
        try:
            await tab.go_to(search_url, timeout=3.0)
            if not await _wait_for_results(tab):
                reason = await _diagnose_empty(tab)
                logger.debug("Lobsters empty (%s) for: %s", reason, query)
                return [], reason
            results = await _parse_results(tab, max_results)
            return results, (None if results else S.EMPTY_NO_RESULTS)
        finally:
            await kill_tab(tab)

    # Legacy thin wrapper — delegates to search_with_reason; swallows exceptions for dev-script compat
    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        try:
            results, _ = await self.search_with_reason(query, language, max_results)
            return results
        except Exception as e:
            logger.error("Lobsters search failed: %s", e)
            return []


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
            date=_extract_date(item.get("date_raw", "")),
        ))
    return results


# Day-precision ISO date from the <time datetime="YYYY-MM-DD HH:MM:SS"> attribute — no time component
def _extract_date(datetime_attr: str) -> str | None:
    text = (datetime_attr or "").strip()
    date_part = text[:10]
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_part):
        return date_part
    return None


# Diagnose why Lobsters returned empty after _wait_for_results failed; tab is still open
# Priority: BLOCK → CONCURRENT_RACE → NO_CONTAINER (Lobsters has no captcha selector)
async def _diagnose_empty(tab) -> str:
    title = _extract_value(await tab.execute_script("return document.title.toLowerCase()")) or ""
    if any(x in title for x in ("captcha", "unusual traffic", "are you a bot", "robot", "access denied")):
        return S.EMPTY_BLOCK
    state = _extract_value(await tab.execute_script("return document.readyState")) or ""
    if state != "complete":
        return S.EMPTY_CONCURRENT_RACE
    return S.EMPTY_NO_CONTAINER
