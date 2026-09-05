# INFRASTRUCTURE
import logging
from urllib.parse import quote_plus

import httpx
from lxml import html as lhtml

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult
from src.search import status as S

logger = logging.getLogger(__name__)

SEARCH_URL = "https://scholar.google.com/scholar?q={}&hl={}&num={}&as_sdt=2007&as_vis=0"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.7680.154 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

_COOKIES = {"CONSENT": "YES+"}

_TIMEOUT = 6.0

# ORCHESTRATOR

# Google Scholar search via httpx (no browser); migrated from pydoll 2026-05-09 (bead searxng-f3i)
class ScholarEngine(BaseEngine):
    name = "google_scholar"

    # Full HTTP search logic; returns (results, reason, diagnosis); exceptions propagate to
    # _engine_with_timing. diagnosis is always None — this engine builds no diagnosis mechanism
    # (HTTP + lxml parse, no browser DOM to inspect)
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None, dict | None]:
        logger.info("Scholar search: %s", query)
        url = _build_url(query, language, max_results)
        r = await _fetch(url)

        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("Location", "")
            logger.warning("Scholar redirect → %s", location)
            return [], S.EMPTY_BLOCK, None

        r.raise_for_status()

        results, reason = _parse_response(r.text, max_results)
        return results, reason, None

    # Legacy thin wrapper — delegates to search_with_reason; swallows exceptions for dev-script compat
    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        try:
            results, _, _ = await self.search_with_reason(query, language, max_results)
            return results
        except Exception as e:
            logger.error("Scholar search failed: %s", e)
            return []


# FUNCTIONS

# Build Scholar search URL with encoded query and standard Scholar params
def _build_url(query: str, language: str, max_results: int) -> str:
    return SEARCH_URL.format(quote_plus(query), language, max_results)


# Execute single httpx GET with browser headers; follow_redirects=False to catch /sorry/ redirect
async def _fetch(url: str) -> httpx.Response:
    async with httpx.AsyncClient(
        headers=_HEADERS,
        cookies=_COOKIES,
        follow_redirects=False,
        timeout=_TIMEOUT,
    ) as client:
        return await client.get(url)


# Parse Scholar HTML; return (results, reason) — reason None on success, EMPTY_BLOCK on captcha form
def _parse_response(body: str, max_results: int) -> tuple[list[SearchResult], str | None]:
    dom = lhtml.fromstring(body)
    if dom.xpath("//form[@id='gs_captcha_f']"):
        logger.warning("Scholar inline captcha form detected")
        return [], S.EMPTY_BLOCK
    results = _extract_results(dom, max_results)
    if not results:
        return [], S.EMPTY_NO_RESULTS
    return results, None


# Extract SearchResult list from parsed Scholar DOM — skips [CITATION] blocks (no anchor)
def _extract_results(dom, max_results: int) -> list[SearchResult]:
    results = []
    for i, block in enumerate(dom.xpath("//div[@data-rp]")):
        if i >= max_results:
            break
        title_nodes = block.xpath(".//h3[1]//a")
        if not title_nodes:
            continue
        title = title_nodes[0].text_content().strip()
        url = title_nodes[0].get("href", "")
        if not url or not title:
            continue
        snippet_nodes = block.xpath(".//div[@class='gs_rs']")
        snippet = snippet_nodes[0].text_content().strip() if snippet_nodes else ""
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            engine="google_scholar",
            position=i + 1,
        ))
    return results
