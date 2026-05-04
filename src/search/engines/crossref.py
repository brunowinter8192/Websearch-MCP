# INFRASTRUCTURE
import logging
import re

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters, get_limiter
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://api.crossref.org/works"

# Uniform 4 req/min across all engines (Google-Baseline, normalized 2026-05-04)
_limiters["crossref"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Search CrossRef and return ranked results
class CrossRefEngine(BaseEngine):
    name = "crossref"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        limiter = get_limiter(self.name)
        await limiter.acquire()
        items = await _fetch_results(query, max_results)
        if items is None:
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return _parse_results(items)


# FUNCTIONS

# Fetch raw work items from CrossRef API
async def _fetch_results(query: str, rows: int) -> list[dict] | None:
    params = {"query": query, "rows": rows}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(API_URL, params=params)
    if response.status_code in (429, 403):
        logger.warning("CrossRef rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("message", {}).get("items", [])


# Parse API response items into SearchResult list; JATS-strip abstract or synthesize from metadata
def _parse_results(items: list[dict]) -> list[SearchResult]:
    results = []
    for i, item in enumerate(items):
        doi = item.get("DOI", "")
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        title_list = item.get("title") or []
        title = title_list[0] if title_list else ""
        abstract = item.get("abstract") or ""
        snippet = _build_snippet(abstract, item)
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            engine="crossref",
            position=i + 1,
        ))
    return results


# Return JATS-stripped abstract if present, else synthesize author+year+container string
def _build_snippet(abstract: str, item: dict) -> str:
    if abstract and abstract.strip():
        stripped = re.sub(r'<[^>]+>', '', abstract)
        stripped = re.sub(r'&[a-z]+;|&#\d+;', '', stripped)  # remove HTML entities
        return ' '.join(stripped.split())
    return _synthesize(item)


# Synthesize a metadata string: "Family, I. et al. (year), Container"
def _synthesize(item: dict) -> str:
    author_list = item.get("author", [])
    if author_list:
        first = author_list[0]
        family = first.get("family", "")
        given = first.get("given", "")
        initial = (given[0] + ".") if given else ""
        author_str = f"{family}, {initial}" if initial else family
        if len(author_list) > 1:
            author_str += " et al."
    else:
        author_str = ""

    year = ""
    for field_name in ("published-print", "issued", "published-online"):
        date_field = item.get(field_name) or {}
        parts = date_field.get("date-parts", [])
        if parts and parts[0] and parts[0][0] is not None:
            year = str(parts[0][0])
            break

    container = (item.get("container-title") or [""])[0]

    if author_str and year and container:
        return f"{author_str} ({year}), {container}"
    elif author_str and year:
        return f"{author_str} ({year})"
    elif year and container:
        return f"({year}), {container}"
    elif year:
        return f"({year})"
    return ""
