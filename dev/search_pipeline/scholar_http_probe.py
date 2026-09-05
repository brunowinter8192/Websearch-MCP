#!/usr/bin/env python3
"""
HTTP Scholar probe — architectural alternative to src/search/engines/scholar.py.

Status: PROBE (not in production). Tests whether HTTP-based Scholar can survive
concurrent multi-engine burst patterns when Google browser is absent.

Lives in dev/ per documentation rule "dev/ vs src/ for Exploratory Rewrites" —
production stays browser-based until empirical evidence converges on a known-good
fix that addresses the actual production problem.

Source: cherry-picked from commit 82bc88f (discarded pydoll-stealth-probe branch),
modeled on SearXNG's `searx/engines/google_scholar.py`.

Usage: imported by `dev/search_pipeline/no_google_burst_smoke.py`. Not invoked by
production cli.py or ENGINES dict in search_web.py.
"""

# INFRASTRUCTURE
import logging
from urllib.parse import quote_plus

import httpx
from lxml import html as lhtml

from src.search.rate_limiter import RateLimiter
from src.search.result import SearchResult
logger = logging.getLogger(__name__)

SEARCH_URL = "https://scholar.google.com/scholar?q={}&hl={}&num={}&as_sdt=2007&as_vis=0"

# Probe-local sub-status sentinels — deliberately NOT src.search.status's EMPTY_BLOCK/
# EMPTY_NO_RESULTS, which were removed along with the query log's guessed-verdict sub-statuses.
# This probe's own backoff experiment (self._limiter.backoff() on a detected block) is internal to
# this file and never reaches the production query log, so it keeps its own local vocabulary.
_BLOCK = "BLOCK"
_NO_RESULTS = "NO_RESULTS"

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

# CONSENT=YES+ bypasses Google's cookie-consent gate without browser interaction
_COOKIES = {"CONSENT": "YES+"}

# 6.0s — Scholar HTTP latency 1-5s range; matches crossref/open_library override in production
_TIMEOUT = 6.0


# ORCHESTRATOR

# HTTP Scholar probe — distinct name to separate from production browser Scholar in smoke output
class ScholarHTTPProbe:
    name = "scholar_http"

    def __init__(self) -> None:
        # Probe-local rate limiter — does NOT touch production _limiters dict
        self._limiter = RateLimiter(max_requests=20, window_seconds=60)

    # Full HTTP search logic; returns (results, sub_status); exceptions propagate to smoke wrapper
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None]:
        logger.info("ScholarHTTPProbe search: %s", query)
        url = _build_url(query, language, max_results)
        try:
            r = await _fetch(url)
        except httpx.TimeoutException as e:
            logger.warning("ScholarHTTPProbe timeout: %s", e)
            raise
        except httpx.HTTPError as e:
            logger.warning("ScholarHTTPProbe http error: %s", e)
            raise

        # 30x redirect → /sorry/ is the concurrent-CAPTCHA signal
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("Location", "")
            logger.warning("ScholarHTTPProbe redirect → %s", location)
            self._limiter.backoff()
            return [], _BLOCK

        r.raise_for_status()

        results, reason = _parse_response(r.text, max_results)
        if reason == _BLOCK:
            self._limiter.backoff()
        else:
            self._limiter.reset_backoff()
        return results, reason


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


# Parse Scholar HTML; return (results, reason) — reason None on success, _BLOCK on captcha form
def _parse_response(body: str, max_results: int) -> tuple[list[SearchResult], str | None]:
    dom = lhtml.fromstring(body)
    if dom.xpath("//form[@id='gs_captcha_f']"):
        logger.warning("ScholarHTTPProbe inline captcha form detected")
        return [], _BLOCK
    results = _extract_results(dom, max_results)
    if not results:
        return [], _NO_RESULTS
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
            engine="scholar_http",
            position=i + 1,
        ))
    return results
