# INFRASTRUCTURE
import asyncio
import json
import logging
from urllib.parse import quote_plus

from src.search.browser import new_tab, kill_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult
from src.search import status as S

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.mojeek.com/search?q={}&safe=1"
MAX_WAIT_CYCLES = 3
WAIT_INTERVAL = 0.2

_JS_WAIT = "return document.querySelectorAll('ul.results-standard > li > a.ob').length"

_JS_PARSE = """
var _cs = document.querySelectorAll('ul.results-standard > li > a.ob');
var _out = [];
for (var _i = 0; _i < _cs.length; _i++) {
    var _a = _cs[_i];
    var _li = _a.closest('li');
    var _h2a = _li ? _li.querySelector('h2 a') : null;
    var _ps = _li ? _li.querySelector('p.s') : null;
    if (!_a.href) continue;
    _out.push({url: _a.href, title: _h2a ? _h2a.textContent.trim() : '', snippet: _ps ? _ps.textContent.trim() : ''});
}
return JSON.stringify(_out);
"""

_JS_DIAGNOSE = """
return JSON.stringify({
    title: document.title,
    url: window.location.href,
    ready_state: document.readyState
});
"""

_BLOCK_MARKERS = ("captcha", "unusual traffic", "are you a bot", "robot", "access denied")

_limiters["mojeek"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Mojeek web search via pydoll stealth browser (mojeek.com/search endpoint, direct hrefs, no captcha check)
class MojeekEngine(BaseEngine):
    name = "mojeek"

    # Full search logic with empty-reason diagnosis; exceptions propagate to _engine_with_timing
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None, dict | None]:
        logger.info("Mojeek search: %s", query)
        tab = await new_tab()
        search_url = _build_url(query)
        try:
            await tab.go_to(search_url, timeout=3.0)
            if not await _wait_for_results(tab):
                diag = await _diagnose(tab)
                reason = _classify_diagnosis(diag["marker"], diag["ready_state"])
                logger.debug("Mojeek empty (%s) for: %s", reason, query)
                return [], reason, diag
            results = await _parse_results(tab, max_results)
            if results:
                return results, None, None
            diag = await _diagnose(tab)
            return results, S.EMPTY_NO_RESULTS, diag
        finally:
            await kill_tab(tab)

    # Legacy thin wrapper — delegates to search_with_reason; swallows exceptions for dev-script compat
    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        try:
            results, _, _ = await self.search_with_reason(query, language, max_results)
            return results
        except Exception as e:
            logger.error("Mojeek search failed: %s", e)
            return []


# FUNCTIONS

# Extract primitive value from CDP execute_script result dict
def _extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Build Mojeek search URL with encoded query
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
            engine="mojeek",
            position=i + 1,
        ))
    return results


# Classify a diagnosis snapshot into an EMPTY sub-status (priority: BLOCK -> CONCURRENT_RACE -> NO_CONTAINER)
def _classify_diagnosis(marker: str | None, ready_state: str) -> str:
    if marker:
        return S.EMPTY_BLOCK
    if ready_state != "complete":
        return S.EMPTY_CONCURRENT_RACE
    return S.EMPTY_NO_CONTAINER


# Match a title against the known block-keyword list, case-insensitive; returns the matched keyword or None
def _match_marker(title: str) -> str | None:
    lowered = title.lower()
    for marker in _BLOCK_MARKERS:
        if marker in lowered:
            return marker
    return None


# Snapshot the page facts behind an empty-reason verdict — an OBSERVATION, not a verdict
async def _diagnose(tab) -> dict:
    raw = await tab.execute_script(_JS_DIAGNOSE)
    val = _extract_value(raw)
    diag = {"title": "", "url": "", "ready_state": ""}
    if val:
        try:
            diag.update(json.loads(val))
        except (json.JSONDecodeError, TypeError):
            pass
    diag["marker"] = _match_marker(diag["title"])
    return diag
