# INFRASTRUCTURE
import html
import logging
import os
import re

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://api.crossref.org/works"

_limiters["crossref"] = RateLimiter(max_requests=4, window_seconds=60)

DATE_KEY_PRIORITY = ("issued", "published-online", "published-print")


# ORCHESTRATOR

# Search CrossRef and return ranked results — HTTP API, no DOM-drift/CAPTCHA patterns, no search_with_reason override needed
class CrossRefEngine(BaseEngine):
    name = "crossref"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        items = await _fetch_results(query, max_results)
        if items is None:
            return []
        return _parse_results(items)


# FUNCTIONS

# Iteratively unescape HTML entities until idempotent — handles double-encoded entities
def _deep_unescape(s: str) -> str:
    while True:
        new = html.unescape(s)
        if new == s:
            return new
        s = new


# Fetch raw work items from CrossRef API; polite-pool mailto appended if WEBSEARCH_CROSSREF_MAILTO is set
async def _fetch_results(query: str, rows: int) -> list[dict] | None:
    params: dict = {"query": query, "rows": rows}
    mailto = os.getenv("WEBSEARCH_CROSSREF_MAILTO")
    if mailto:
        params["mailto"] = mailto
    async with httpx.AsyncClient(timeout=6.0) as client:
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
        title = _deep_unescape(title_list[0]) if title_list else ""
        abstract = item.get("abstract") or ""
        snippet = _build_snippet(abstract, item)
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            engine="crossref",
            position=i + 1,
            date=_extract_date(item),
        ))
    return results


# Publication date at native precision from date-parts ([year], [year,month], or [year,month,day]).
def _extract_date(item: dict) -> str | None:
    for field_name in DATE_KEY_PRIORITY:
        date_field = item.get(field_name) or {}
        parts_list = date_field.get("date-parts", [])
        if not parts_list or not parts_list[0] or parts_list[0][0] is None:
            continue
        return _format_date_parts(parts_list[0])
    return None


# Truncate at the first missing/null slot — a gap never shifts a later value into the wrong position
def _format_date_parts(parts: list) -> str:
    year = parts[0]
    if len(parts) < 2 or parts[1] is None:
        return f"{year:04d}"
    month = parts[1]
    if len(parts) < 3 or parts[2] is None:
        return f"{year:04d}-{month:02d}"
    day = parts[2]
    return f"{year:04d}-{month:02d}-{day:02d}"


# Return JATS-stripped abstract if present, else synthesize author+year+container string
def _build_snippet(abstract: str, item: dict) -> str:
    if abstract and abstract.strip():
        stripped = re.sub(r'<[^>]+>', '', abstract)
        stripped = re.sub(r'&[a-z]+;|&#\d+;', '', stripped)
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
    for field_name in DATE_KEY_PRIORITY:
        date_field = item.get(field_name) or {}
        parts = date_field.get("date-parts", [])
        if parts and parts[0] and parts[0][0] is not None:
            year = str(parts[0][0])
            break

    container = _deep_unescape((item.get("container-title") or [""])[0])

    if author_str and year and container:
        return f"{author_str} ({year}), {container}"
    elif author_str and year:
        return f"{author_str} ({year})"
    elif year and container:
        return f"({year}), {container}"
    elif year:
        return f"({year})"
    return ""
