# INFRASTRUCTURE
import asyncio
import base64
import json
import logging
import re
from urllib.parse import urlparse, parse_qs

from src.search.browser import new_tab, kill_tab
from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult
from src.search import status as S

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.bing.com/search?q={}"
MAX_WAIT_CYCLES = 20
WAIT_INTERVAL = 0.3

_JS_WAIT = "return document.querySelectorAll('li.b_algo').length"

_JS_PARSE = """
var _cs = document.querySelectorAll('li.b_algo');
var _out = [];
for (var _i = 0; _i < _cs.length; _i++) {
    var _c = _cs[_i];
    var _h2a = _c.querySelector('h2 a');
    var _cap = _c.querySelector('.b_caption p') || _c.querySelector('.b_caption');
    var _dt = _c.querySelector('span.news_dt');
    if (!_h2a || !_h2a.href) continue;
    _out.push({
        url: _h2a.href,
        title: _h2a.textContent.trim(),
        snippet: _cap ? _cap.textContent.trim() : '',
        date_raw: _dt ? _dt.textContent.trim() : ''
    });
}
return JSON.stringify(_out);
"""

_JS_DIAGNOSE = """
var body = document.body ? document.body.innerText.toLowerCase() : '';
var title = document.title.toLowerCase();
var markers = ['captcha', 'unusual traffic', 'verify you are human', 'are you a robot',
               'access denied', 'automated queries', 'ungewöhnlichen datenverkehr',
               'roboter', 'bestätigen sie, dass sie ein mensch'];
var hit = null;
for (var _i = 0; _i < markers.length; _i++) {
    if (body.indexOf(markers[_i]) !== -1 || title.indexOf(markers[_i]) !== -1) { hit = markers[_i]; break; }
}
return JSON.stringify({marker: hit, url: window.location.href, ready_state: document.readyState});
"""

_limiters["bing"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Bing web search via pydoll stealth browser — direct path to the Bing index, degrades gracefully to empty+reason
class BingEngine(BaseEngine):
    name = "bing"

    # Full search logic with empty-reason diagnosis; exceptions propagate to _engine_with_timing
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None]:
        logger.info("Bing search: %s", query)
        tab = await new_tab()
        try:
            await tab.go_to(SEARCH_URL.format(query.replace(" ", "+")), timeout=10.0)
            if not await _wait_for_results(tab):
                reason = await _diagnose_empty(tab)
                logger.debug("Bing empty (%s) for: %s", reason, query)
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
            logger.error("Bing search failed: %s", e)
            return []


# FUNCTIONS

# Extract primitive value from CDP execute_script result dict
def _extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Unwrap Bing's bing.com/ck/a?...&u=<prefixed-base64>&... tracking redirect to the real destination URL
def _clean_url(href: str) -> str:
    if not href:
        return ""
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    u = qs.get("u", [None])[0]
    if not u:
        return href
    payload = u[2:] if len(u) > 2 else u
    padded = payload + "=" * (-len(payload) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")
    except Exception:
        return href


# Poll for result containers up to MAX_WAIT_CYCLES x WAIT_INTERVAL seconds, return True when found
async def _wait_for_results(tab) -> bool:
    for _ in range(MAX_WAIT_CYCLES):
        raw = await tab.execute_script(_JS_WAIT)
        count = _extract_value(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(WAIT_INTERVAL)
    return False


# Build SearchResult list from parsed li.b_algo items, unwrapping tracking URLs (pure — no browser access)
def _build_results(items: list[dict], max_results: int) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items[:max_results]):
        url = _clean_url(item.get("url", ""))
        if not url:
            continue
        results.append(SearchResult(
            url=url, title=item.get("title", ""), snippet=item.get("snippet", ""),
            engine="bing", position=i + 1,
            date=_extract_date(item.get("date_raw", "")),
        ))
    return results


_DE_MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
_EN_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
_DE_DATE_RE = re.compile(r'^(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s+(\d{4})$')
_EN_DATE_RE = re.compile(r'^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$')


# Parse span.news_dt's localized display string to a day-precision ISO date; unrecognized formats degrade to None
def _extract_date(news_dt_text: str) -> str | None:
    text = (news_dt_text or "").strip()
    if not text:
        return None
    m = _DE_DATE_RE.match(text)
    if m:
        day, month_name, year = m.groups()
        month = _DE_MONTHS.get(month_name.lower())
        return f"{int(year):04d}-{month:02d}-{int(day):02d}" if month else None
    m = _EN_DATE_RE.match(text)
    if m:
        month_name, day, year = m.groups()
        month = _EN_MONTHS.get(month_name.lower())
        return f"{int(year):04d}-{month:02d}-{int(day):02d}" if month else None
    return None


# Query DOM for li.b_algo containers and return SearchResult list
async def _parse_results(tab, max_results: int) -> list[SearchResult]:
    raw = await tab.execute_script(_JS_PARSE)
    value = _extract_value(raw)
    if not value:
        return []
    try:
        items = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
    return _build_results(items, max_results)


# Classify a diagnosis snapshot into an EMPTY sub-status (priority: block marker -> CONCURRENT_RACE -> NO_CONTAINER)
def _classify_diagnosis(marker: str | None, ready_state: str) -> str:
    if marker:
        return S.EMPTY_BLOCK
    if ready_state != "complete":
        return S.EMPTY_CONCURRENT_RACE
    return S.EMPTY_NO_CONTAINER


# Diagnose why Bing returned zero li.b_algo after _wait_for_results failed; tab is still open
async def _diagnose_empty(tab) -> str:
    raw = await tab.execute_script(_JS_DIAGNOSE)
    val = _extract_value(raw)
    diag = {"marker": None, "url": "", "ready_state": ""}
    if val:
        try:
            diag.update(json.loads(val))
        except (json.JSONDecodeError, TypeError):
            pass
    return _classify_diagnosis(diag["marker"], diag["ready_state"])
