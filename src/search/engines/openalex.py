# INFRASTRUCTURE
import logging
import os

import httpx

from src.search.engines.base import BaseEngine
from src.search.rate_limiter import RateLimiter, _limiters, get_limiter
from src.search.result import SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://api.openalex.org/works"

# Uniform 4 req/min across all engines (Google-Baseline, normalized 2026-05-04)
_limiters["openalex"] = RateLimiter(max_requests=4, window_seconds=60)


# ORCHESTRATOR

# Search OpenAlex academic graph and return structured results
class OpenAlexEngine(BaseEngine):
    name = "openalex"

    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        logger.info("OpenAlex search: %s", query)
        limiter = get_limiter(self.name)
        await limiter.acquire()
        works = await _fetch_results(query, max_results)
        if works is None:
            limiter.backoff()
            return []
        limiter.reset_backoff()
        return _parse_results(works)


# FUNCTIONS

# Fetch raw work items from OpenAlex search API
async def _fetch_results(query: str, max_results: int) -> list[dict] | None:
    params: dict = {"search": query, "per_page": max_results}
    mailto = os.environ.get("OPENALEX_MAILTO", "")
    if mailto:
        params["mailto"] = mailto
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(API_URL, params=params)
    if response.status_code in (429, 403):
        logger.warning("OpenAlex rate limited: %d", response.status_code)
        return None
    response.raise_for_status()
    return response.json().get("results", [])


# Parse OpenAlex work items into SearchResult list
def _parse_results(works: list[dict]) -> list[SearchResult]:
    results = []
    for i, work in enumerate(works):
        title = work.get("title") or ""
        if not title:
            continue
        url = _pick_url(work)
        if not url:
            continue
        snippet = _reconstruct_abstract(work.get("abstract_inverted_index"))
        cited = work.get("cited_by_count", 0)
        if cited > 50:
            snippet = f"{snippet} (Cited {cited}×)"
        results.append(SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            engine="openalex",
            position=i + 1,
        ))
    return results


# Reconstruct abstract text from OpenAlex inverted index (word -> [positions])
def _reconstruct_abstract(aii: dict | None) -> str:
    if not aii:
        return ""
    pos_word: dict[int, str] = {}
    for word, positions in aii.items():
        for pos in positions:
            pos_word[pos] = word
    return " ".join(pos_word[p] for p in sorted(pos_word))


# Select canonical URL: arXiv > DOI > openalex.org
def _pick_url(work: dict) -> str:
    ids = work.get("ids") or {}
    arxiv = ids.get("arxiv")
    if arxiv:
        return arxiv
    doi = work.get("doi")
    if doi:
        return doi
    return work.get("id", "")
