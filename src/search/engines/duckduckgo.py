# INFRASTRUCTURE
import asyncio
import json
import logging
import re
from urllib.parse import quote_plus, urlparse, parse_qs

from src.search.browser import new_tab, kill_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult
from src.search import status as S

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
    var _extras = _c.querySelector('.result__extras__url');
    var _dateSpan = _extras ? _extras.querySelector('span:not(.result__icon)') : null;
    if (!_a) continue;
    _out.push({
        href: _a.href,
        title: _a.textContent.trim(),
        snippet: _snip ? _snip.textContent.trim() : '',
        date_raw: _dateSpan ? _dateSpan.textContent.trim() : ''
    });
}
return JSON.stringify(_out);
"""

# Uniform 4 req/min across all engines (Google-Baseline, normalized 2026-05-04)
_limiters["duckduckgo"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# DuckDuckGo web search via pydoll stealth browser (html.duckduckgo.com/html/ endpoint)
class DuckDuckGoEngine(BaseEngine):
    name = "duckduckgo"

    # Full search logic with empty-reason diagnosis; exceptions propagate to _engine_with_timing
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None]:
        logger.info("DuckDuckGo search: %s", query)
        tab = await new_tab()
        search_url = _build_url(query)
        try:
            await tab.go_to(search_url, timeout=3.0)
            if await _has_captcha(tab):
                logger.warning("DuckDuckGo CAPTCHA detected for: %s", query)
                return [], S.EMPTY_BLOCK
            if not await _wait_for_results(tab):
                reason = await _diagnose_empty(tab)
                logger.debug("DuckDuckGo empty (%s) for: %s", reason, query)
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
            logger.error("DuckDuckGo search failed: %s", e)
            return []


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
            date=_extract_date(item.get("date_raw", "")),
        ))
    return results


# Day-precision ISO date from the bare '.result__extras__url' date span (e.g. '2026-07-29T18:00:00.0000000')
# — truncates to YYYY-MM-DD, no invented/kept time component (consistent with lobsters/bing precision)
def _extract_date(date_raw: str) -> str | None:
    text = (date_raw or "").replace("\xa0", " ").strip()
    date_part = text[:10]
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_part):
        return date_part
    return None


# Diagnose why DDG returned empty after _wait_for_results failed; tab is still open
# Priority: BLOCK → CONCURRENT_RACE → NO_CONTAINER (no consent flow for DDG)
async def _diagnose_empty(tab) -> str:
    captcha_raw = await tab.execute_script(_JS_CAPTCHA)
    if _extract_value(captcha_raw) and int(_extract_value(captcha_raw) or 0) > 0:
        return S.EMPTY_BLOCK
    state = _extract_value(await tab.execute_script("return document.readyState")) or ""
    if state != "complete":
        return S.EMPTY_CONCURRENT_RACE
    return S.EMPTY_NO_CONTAINER
