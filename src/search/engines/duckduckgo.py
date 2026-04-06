# INFRASTRUCTURE
import logging
from urllib.parse import urlparse, parse_qs, unquote

import httpx
from bs4 import BeautifulSoup

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import get_limiter
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

DDG_URL = "https://html.duckduckgo.com/html/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}


# ORCHESTRATOR

# Search DuckDuckGo HTML-lite via httpx and return ranked results
class DuckDuckGoEngine(BaseEngine):
    name = "duckduckgo"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        limiter = get_limiter(self.name)
        await limiter.acquire()
        html = await _fetch_html(query)
        if html is None:
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return _parse_results(html, max_results)


# FUNCTIONS

# Fetch DDG HTML-lite page via httpx GET request
async def _fetch_html(query: str) -> str | None:
    params = {"q": query}
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
            response = await client.get(DDG_URL, params=params)
        if response.status_code in (429, 403):
            logger.warning("DuckDuckGo rate limited: %d", response.status_code)
            return None
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning("DuckDuckGo fetch failed: %s", e)
        return None


# Resolve DDG redirect URL to final destination URL
def _resolve_url(href: str) -> str:
    if not href:
        return ""
    # DDG HTML-lite wraps URLs in redirect: //duckduckgo.com/l/?uddg=<encoded_url>&...
    if "duckduckgo.com/l/" in href:
        try:
            parsed = urlparse(href if href.startswith("http") else "https:" + href)
            uddg = parse_qs(parsed.query).get("uddg", [""])
            return unquote(uddg[0]) if uddg[0] else href
        except Exception:
            return href
    return href


# Parse HTML into SearchResult list, capped at max_results
def _parse_results(html: str, max_results: int) -> list[SearchResult]:
    soup = BeautifulSoup(html, "lxml")
    results = []
    position = 1
    for el in soup.select("div.result"):
        if position > max_results:
            break
        a = el.select_one("a.result__a")
        snip_el = el.select_one("a.result__snippet")
        if not a:
            continue
        url = _resolve_url(a.get("href", ""))
        if not url:
            continue
        results.append(SearchResult(
            url=url,
            title=a.get_text(strip=True),
            snippet=snip_el.get_text(strip=True) if snip_el else "",
            engine="duckduckgo",
            position=position,
        ))
        position += 1
    return results
