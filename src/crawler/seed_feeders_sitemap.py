# INFRASTRUCTURE
import asyncio
import gzip
from xml.etree import ElementTree

import httpx

# From src/crawler/seed_feeders_constants.py: shared HTTP timeout, User-Agent, fetch concurrency
from src.crawler.seed_feeders_constants import HTTP_TIMEOUT_S, USER_AGENT, SITEMAP_FETCH_CONCURRENCY


# FUNCTIONS

# GET a sitemap URL, gunzip if named *.gz; None on any non-200/network/decompress error — a
# 404'd or malformed sitemap is a normal outcome for this feeder, not an error.
async def fetch_sitemap(client: httpx.AsyncClient, url: str) -> bytes:
    try:
        response = await client.get(url, timeout=HTTP_TIMEOUT_S,
                                    headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    content = response.content
    if url.endswith(".gz"):
        try:
            content = gzip.decompress(content)
        except OSError:
            return None
    return content


# Local (namespace-stripped) tag name, e.g. "{http://www.sitemaps.org/...}urlset" -> "urlset"
def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


# Stripped text of the first direct child matching local_name, or None
def _child_text(parent, local_name: str) -> str:
    for child in parent:
        if _local_name(child.tag) == local_name:
            return (child.text or "").strip()
    return None


# Parse sitemap XML (namespace-agnostic): ("index", [sub-sitemap urls]) for a <sitemapindex>,
# ("urlset", [loc urls]) for a <urlset>, or ("unknown", []) for anything else/unparseable content.
def parse_sitemap_xml(content: bytes) -> tuple:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError:
        return ("unknown", [])
    root_tag = _local_name(root.tag)
    if root_tag == "sitemapindex":
        locs = [_child_text(entry, "loc") for entry in root]
        return ("index", [loc for loc in locs if loc])
    if root_tag == "urlset":
        locs = [_child_text(entry, "loc") for entry in root]
        return ("urlset", [loc for loc in locs if loc])
    return ("unknown", [])


# Recursively resolve sitemap index/urlset documents starting from sitemap_urls, following
# <sitemapindex> nesting to arbitrary depth (bounded concurrency via a shared semaphore,
# cycle-guarded via a shared visited set). Returns the flat, NOT-yet-deduped list of every
# <loc> URL found in every reachable <urlset>; a sitemap that fails to fetch/parse contributes
# nothing and does not stop the rest of the tree from resolving.
async def resolve_sitemap_urls(client: httpx.AsyncClient, sitemap_urls: list, seen: set = None) -> list:
    seen = seen if seen is not None else set()
    semaphore = asyncio.Semaphore(SITEMAP_FETCH_CONCURRENCY)
    loc_urls = []

    async def _resolve_one(url: str) -> None:
        if url in seen:
            return
        seen.add(url)
        async with semaphore:
            content = await fetch_sitemap(client, url)
        if content is None:
            return
        kind, entries = parse_sitemap_xml(content)
        if kind == "urlset":
            loc_urls.extend(entries)
        elif kind == "index":
            await asyncio.gather(*[_resolve_one(sub) for sub in entries])

    await asyncio.gather(*[_resolve_one(u) for u in sitemap_urls])
    return loc_urls
