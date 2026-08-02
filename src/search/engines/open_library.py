# INFRASTRUCTURE
import logging

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://openlibrary.org/search.json"

# Uniform 4 req/min across all engines (Google-Baseline, normalized 2026-05-04)
_limiters["open_library"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Search Open Library catalog and return structured book results
# Empty-on-success not sub-classified — HTTP API, no DOM-drift/CAPTCHA-page patterns apply
class OpenLibraryEngine(BaseEngine):
    name = "open_library"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        docs = await _fetch_results(query, max_results)
        if docs is None:
            return []
        return _parse_results(docs)


# FUNCTIONS

# Fetch raw doc items from Open Library search API; returns None on rate-limit
async def _fetch_results(query: str, limit: int) -> list[dict] | None:
    params: dict = {"q": query, "limit": limit}
    async with httpx.AsyncClient(timeout=6.0) as client:  # aligned with ENGINE_WATCHDOG_OVERRIDE
        response = await client.get(API_URL, params=params)
    if response.status_code in (429, 403):
        logger.warning("Open Library rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("docs", [])


# Parse Open Library doc items into SearchResult list
def _parse_results(docs: list[dict]) -> list[SearchResult]:
    results = []
    for i, doc in enumerate(docs):
        key = doc.get("key", "")
        if not key:
            continue
        title = doc.get("title", "")
        if not title:
            continue
        url = f"https://openlibrary.org{key}"
        snippet = _build_snippet(doc)
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            engine="open_library",
            position=i + 1,
            date=_extract_date(doc),
        ))
    return results


# Synthesize 4-pillar snippet: author, year, edition count, ebook access
def _build_snippet(doc: dict) -> str:
    authors = doc.get("author_name") or []
    author = authors[0] if authors else ""
    year = doc.get("first_publish_year")
    editions = doc.get("edition_count", 0)
    ebook = doc.get("ebook_access", "unknown")
    if author and year:
        return f"{author} ({year}) — {editions} eds, ebook: {ebook}"
    elif author:
        return f"{author} — {editions} eds, ebook: {ebook}"
    elif year:
        return f"({year}) — {editions} eds, ebook: {ebook}"
    return f"{editions} eds, ebook: {ebook}"


# first_publish_year is year-only precision
def _extract_date(doc: dict) -> str | None:
    year = doc.get("first_publish_year")
    return str(year) if year else None
