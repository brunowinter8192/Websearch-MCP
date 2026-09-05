# INFRASTRUCTURE
import asyncio
import json
import logging
import time
from urllib.parse import quote_plus

from src.search.browser import new_tab, kill_tab
from src.search.document_status import attach_document_status, start_document_status_capture
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.mojeek.com/search?q={}&safe=1"
WAIT_INTERVAL = 0.2

# Total wall-clock budget for search_with_reason's own work (navigation through the results
# poll), anchored at the function's very first line. Mojeek serves an ALTCHA proof-of-work
# challenge on most runs (challenge.js computes a PoW client-side, POSTs it to /captcha/verify,
# then reloads the page once verified — only after that reload does ul.results-standard exist);
# how long that PoW actually takes on this machine is unmeasured, which is exactly what this
# budget exists to let the log answer. Deliberately ONE deadline covering navigation AND the
# results poll together, not a fixed post-navigation wait stacked on top of tab.go_to's own 3.0s
# cap — stacking would risk exceeding the shared 6.0s per-engine watchdog
# (search_web.ENGINE_WATCHDOG_TIMEOUT, NOT raised or overridden here) on a slow navigation;
# anchoring at the top means a slow go_to shrinks the poll's own share automatically instead of
# adding to it. 4.5s leaves ~1.0-1.5s of margin for the diagnose call and kill_tab teardown that
# still run after the deadline is spent (historical mojeek search_ms under the old 0.6s-wait
# scheme ran 800-1020ms, i.e. ~200-400ms of non-wait overhead).
MOJEEK_BUDGET_S = 4.5

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
        t_start = time.monotonic()
        tab = await new_tab()
        search_url = _build_url(query)
        try:
            status_chain = await start_document_status_capture(tab)
            await tab.go_to(search_url, timeout=3.0)
            deadline = t_start + MOJEEK_BUDGET_S
            if not await _wait_for_results(tab, deadline):
                diag = await _diagnose(tab)
                diag["containers_found"] = False
                logger.debug("Mojeek empty for: %s", query)
                return [], None, attach_document_status(diag, status_chain)
            results = await _parse_results(tab, max_results)
            if results:
                return results, None, attach_document_status({}, status_chain)
            diag = await _diagnose(tab)
            diag["containers_found"] = True
            return results, None, attach_document_status(diag, status_chain)
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


# Poll for result containers until `deadline` (monotonic time), return True when found — a single
# wall-clock deadline (not a fixed cycle count) so navigation-time variance shrinks the poll's own
# share of the budget instead of stacking on top of it and risking the shared watchdog
async def _wait_for_results(tab, deadline: float) -> bool:
    while time.monotonic() < deadline:
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


# Match a title against the known block-keyword list, case-insensitive; returns the matched keyword or None
def _match_marker(title: str) -> str | None:
    lowered = title.lower()
    for marker in _BLOCK_MARKERS:
        if marker in lowered:
            return marker
    return None


# Snapshot the page facts behind an empty result — an OBSERVATION, never a verdict
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
