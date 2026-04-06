# INFRASTRUCTURE
import asyncio
import json
import logging
from urllib.parse import quote_plus

from src.search.browser import get_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, get_limiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://scholar.google.com/scholar?q={}&hl={}&num={}"
CONSENT_DOMAIN = "consent.google.com"
CAPTCHA_PATH = "/sorry/"
MAX_WAIT_CYCLES = 15
WAIT_INTERVAL = 1.0

_JS_WAIT = "return document.querySelectorAll('div.gs_r.gs_or.gs_scl').length"

_JS_PARSE = """
return JSON.stringify((function() {
    var nodes = document.querySelectorAll('div.gs_r.gs_or.gs_scl');
    var out = [];
    for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        var a = el.querySelector('h3.gs_rt a');
        var snip = el.querySelector('div.gs_rs');
        if (!a) continue;
        out.push({
            url: a.href,
            title: a.textContent.trim(),
            snippet: snip ? snip.textContent.trim() : ''
        });
    }
    return out;
})());
"""

_JS_CONSENT = """
var btn = document.querySelector('button[jsname="b3VHJd"]') ||
           document.querySelector('.lssxud') ||
           document.querySelector('form[action*="consent"] button[type="submit"]') ||
           document.querySelector('button[aria-label*="Accept"]');
if (btn) { btn.click(); return true; }
return false;
"""

# Pre-register with strict config (3 req/60s) — Scholar is stricter than web Google
_limiters["google_scholar"] = RateLimiter(max_requests=3, window_seconds=60)


# ORCHESTRATOR

# Google Scholar search via pydoll stealth browser
class ScholarEngine(BaseEngine):
    name = "google_scholar"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        logger.info("Scholar search: %s", query)
        limiter = get_limiter(self.name)
        await limiter.acquire()
        tab = await get_tab()
        search_url = _build_url(query, language, max_results)
        try:
            await tab.go_to(search_url, timeout=20)
            current = await tab.current_url
            if CONSENT_DOMAIN in current:
                await _handle_consent(tab)
                await tab.go_to(search_url, timeout=20)
                current = await tab.current_url
            if CAPTCHA_PATH in current:
                logger.warning("Scholar CAPTCHA detected for: %s", query)
                limiter.backoff()
                return []
            if not await _wait_for_results(tab):
                logger.warning("No Scholar results loaded for: %s", query)
                limiter.backoff()
                return []
            results = await _parse_results(tab, max_results)
        except Exception as e:
            logger.error("Scholar search failed: %s", e)
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return results


# FUNCTIONS

# Extract primitive value from CDP execute_script result dict
def _extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Build Scholar search URL with encoded query
def _build_url(query: str, language: str, max_results: int) -> str:
    return SEARCH_URL.format(quote_plus(query), language, max_results)


# Click consent accept button on consent.google.com
async def _handle_consent(tab) -> None:
    logger.info("Scholar consent page detected — clicking accept")
    await tab.execute_script(_JS_CONSENT)
    await asyncio.sleep(2.0)


# Poll for result containers up to MAX_WAIT_CYCLES seconds, return True when found
async def _wait_for_results(tab) -> bool:
    for _ in range(MAX_WAIT_CYCLES):
        raw = await tab.execute_script(_JS_WAIT)
        count = _extract_value(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(WAIT_INTERVAL)
    return False


# Query DOM for Scholar result containers and return SearchResult list
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
            engine="google_scholar",
            position=i + 1,
        ))
    return results
