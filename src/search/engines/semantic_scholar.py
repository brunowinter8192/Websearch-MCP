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

SEARCH_URL = "https://www.semanticscholar.org/search?q={}"
ERROR_TEST_ID = "error-message-block"
MAX_WAIT_CYCLES = 5
WAIT_INTERVAL = 0.5

_JS_WAIT = "return document.querySelectorAll('div.cl-paper-row').length"

_JS_ERROR = "return document.querySelectorAll('[data-test-id=\"error-message-block\"]').length"

_JS_PARSE = """var _n = document.querySelectorAll('div.cl-paper-row');
var _o = [];
for (var _i = 0; _i < _n.length; _i++) {
    var _el = _n[_i];
    var _a = _el.querySelector('[data-test-id="title-link"]');
    if (!_a) continue;
    var _s = _el.querySelector('.tldr-abstract-replacement');
    _o.push({url: _a.href, title: _a.textContent.trim(), snippet: _s ? _s.textContent.trim() : ''});
}
return JSON.stringify(_o)"""

_JS_CONSENT = """
var _btn = Array.from(document.querySelectorAll('button')).find(function(b) {
    return b.innerText.indexOf('akzeptieren') !== -1 || b.innerText.indexOf('Accept all') !== -1;
});
if (_btn) { _btn.click(); return true; }
return false;
"""

_limiters["semantic_scholar"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Semantic Scholar academic search via pydoll stealth browser
class SemanticScholarEngine(BaseEngine):
    name = "semantic_scholar"

    # Full search logic with empty-reason diagnosis; exceptions propagate to _engine_with_timing
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None]:
        logger.info("Semantic Scholar search: %s", query)
        tab = await new_tab()
        search_url = _build_url(query)
        try:
            await tab.go_to(search_url, timeout=3.0)
            await _handle_consent(tab)
            if await _has_error_page(tab):
                logger.warning("Semantic Scholar error page for: %s", query)
                return [], S.EMPTY_BLOCK
            if not await _wait_for_results(tab):
                reason = await _diagnose_empty(tab)
                logger.debug("Semantic Scholar empty (%s) for: %s", reason, query)
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
            logger.error("Semantic Scholar search failed: %s", e)
            return []


# FUNCTIONS

# Extract primitive value from CDP execute_script result dict
def _extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Build Semantic Scholar search URL — no sort param (any sort value causes HTTP 400)
def _build_url(query: str) -> str:
    return SEARCH_URL.format(quote_plus(query))


# Detect SS backend error page (HTTP 400/405 rate-limit response — error-message-block test-id present)
async def _has_error_page(tab) -> bool:
    raw = await tab.execute_script(_JS_ERROR)
    val = _extract_value(raw)
    return bool(val and int(val) > 0)


# Click cookie consent accept button if banner is visible (one-time; session persists in profile dir)
async def _handle_consent(tab) -> None:
    raw = await tab.execute_script(_JS_CONSENT)
    val = _extract_value(raw)
    if val:
        logger.info("Semantic Scholar consent banner accepted")


# Poll for result containers up to MAX_WAIT_CYCLES seconds, return True when found
async def _wait_for_results(tab) -> bool:
    for _ in range(MAX_WAIT_CYCLES):
        raw = await tab.execute_script(_JS_WAIT)
        count = _extract_value(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(WAIT_INTERVAL)
    return False


# Query DOM for paper cards and return SearchResult list
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
            engine="semantic_scholar",
            position=i + 1,
        ))
    return results


# Diagnose why SS returned empty after _wait_for_results failed (priority: BLOCK -> CONSENT -> CONCURRENT_RACE -> NO_CONTAINER)
async def _diagnose_empty(tab) -> str:
    if await _has_error_page(tab):
        return S.EMPTY_BLOCK
    consent_raw = await tab.execute_script(_JS_CONSENT)
    if _extract_value(consent_raw):
        return S.EMPTY_CONSENT
    state = _extract_value(await tab.execute_script("return document.readyState")) or ""
    if state != "complete":
        return S.EMPTY_CONCURRENT_RACE
    return S.EMPTY_NO_CONTAINER
