# INFRASTRUCTURE
from urllib.parse import urljoin, urlparse

import httpx

# From src/crawler/seed_feeders_constants.py: shared conventional sitemap fallback paths
from src.crawler.seed_feeders_constants import CONVENTIONAL_SITEMAP_PATHS
# From src/crawler/seed_feeders_scope.py: FeederResult + shared scope/normalize/dedup
from src.crawler.seed_feeders_scope import FeederResult, scope_and_dedup
# From src/crawler/seed_feeders_robots.py: robots.txt fetch + directive parsing
from src.crawler.seed_feeders_robots import fetch_robots_txt, parse_robots_directives
# From src/crawler/seed_feeders_sitemap.py: sitemap fetch + recursive index resolution
from src.crawler.seed_feeders_sitemap import resolve_sitemap_urls
# From src/crawler/seed_feeders_navtree.py: framework nav-tree detection + version union
from src.crawler.seed_feeders_navtree import resolve_navigation_tree


# ORCHESTRATOR

# Fetch seed_url's robots.txt and return its Allow/Disallow path values as scoped, deduped seeds.
async def robots_feeder_workflow(seed_url: str) -> FeederResult:
    try:
        seed_host = _require_host(seed_url)
        base_url = _base_url(seed_url)
        async with httpx.AsyncClient() as client:
            text = await fetch_robots_txt(client, base_url)
        paths = parse_robots_directives(text, base_url)["paths"] if text else []
        return FeederResult(urls=scope_and_dedup(paths, seed_host), ok=True, source="robots")
    except Exception as exc:
        return FeederResult(urls=[], ok=False, error=str(exc))


# Resolve seed_url's sitemap(s) to a flat, scoped, deduped seed list. robots.txt-declared
# Sitemap: locations are preferred; the conventional fallback paths are only tried when
# robots.txt declares none (including when robots.txt itself is missing).
async def sitemap_feeder_workflow(seed_url: str) -> FeederResult:
    try:
        seed_host = _require_host(seed_url)
        base_url = _base_url(seed_url)
        async with httpx.AsyncClient() as client:
            text = await fetch_robots_txt(client, base_url)
            declared_sitemaps = parse_robots_directives(text, base_url)["sitemaps"] if text else []
            sitemap_urls = declared_sitemaps or [urljoin(base_url, p) for p in CONVENTIONAL_SITEMAP_PATHS]
            loc_urls = await resolve_sitemap_urls(client, sitemap_urls)
        return FeederResult(urls=scope_and_dedup(loc_urls, seed_host), ok=True, source="sitemap")
    except Exception as exc:
        return FeederResult(urls=[], ok=False, error=str(exc))


# Resolve seed_url's navigation tree (its frontend framework's own embedded page inventory) to a
# flat, scoped, deduped seed list, unioned across every version the site exposes in the same
# payload. `source` distinguishes a real recursive tree found by structural shape ("navtree_tree")
# from a flat href scan with no tree evidence behind it ("navtree_flat") — see FeederResult. A
# seed_url that cannot be fetched at all (unlike a version root, or robots.txt/a sitemap) is
# ok=False, not an empty "navtree_flat" result — resolve_navigation_tree raises for that case,
# caught by the same except below as an invalid seed_url.
async def navtree_feeder_workflow(seed_url: str) -> FeederResult:
    try:
        seed_host = _require_host(seed_url)
        async with httpx.AsyncClient() as client:
            raw_urls, tier = await resolve_navigation_tree(client, seed_url)
        return FeederResult(urls=scope_and_dedup(raw_urls, seed_host), ok=True, source=f"navtree_{tier}")
    except Exception as exc:
        return FeederResult(urls=[], ok=False, error=str(exc))


# FUNCTIONS

# Validate seed_url and return its bare host; raises ValueError on unparseable/hostless input
def _require_host(seed_url: str) -> str:
    host = urlparse(seed_url).hostname
    if not host:
        raise ValueError(f"seed_url has no host: {seed_url!r}")
    return host


# scheme://host/ root, used as the base for robots.txt and conventional-sitemap-path resolution
def _base_url(seed_url: str) -> str:
    parsed = urlparse(seed_url)
    return f"{parsed.scheme}://{parsed.netloc}/"
