# INFRASTRUCTURE
import asyncio
import dataclasses
import logging

import httpx
from lxml import html as lxml_html

from src.search.result import SearchResult

logger = logging.getLogger(__name__)

PREVIEW_TOP_N = 20
PREVIEW_CONCURRENCY = 8
PREVIEW_TIMEOUT = 3.0
PREVIEW_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.7727.101 Safari/537.36"
    )
}


# ORCHESTRATOR

# Fetch og:description / meta:description for top-N results, attach preview field, skip rest
async def fetch_previews(results: list[SearchResult], top_n: int = PREVIEW_TOP_N) -> list[SearchResult]:
    targets = results[:top_n]
    rest = results[top_n:]
    sem = asyncio.Semaphore(PREVIEW_CONCURRENCY)
    async with httpx.AsyncClient(
        timeout=PREVIEW_TIMEOUT,
        follow_redirects=True,
        headers=PREVIEW_HEADERS,
    ) as client:
        raw = await asyncio.gather(
            *[_fetch_one(client, sem, r.url) for r in targets],
            return_exceptions=True,
        )
    out = []
    for r, p in zip(targets, raw):
        if isinstance(p, Exception) or p is None:
            out.append(r)
        else:
            out.append(dataclasses.replace(r, preview=p))
    return out + rest


# FUNCTIONS

# Fetch one URL with semaphore guard, extract og:description + meta:description, return dict or None on any failure
async def _fetch_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    url: str,
) -> dict | None:
    async with sem:
        try:
            resp = await client.get(url)
            tree = lxml_html.fromstring(resp.content)
            og = tree.xpath("string(//meta[@property='og:description']/@content)") or None
            meta = tree.xpath("string(//meta[@name='description']/@content)") or None
            if not og and not meta:
                return None
            return {"og": og, "meta": meta}
        except Exception as e:
            logger.debug("Preview fetch skipped %s: %s", url, e)
            return None
