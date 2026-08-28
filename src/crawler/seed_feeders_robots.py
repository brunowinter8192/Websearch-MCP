# INFRASTRUCTURE
import re
from urllib.parse import urljoin

import httpx

# From src/crawler/seed_feeders_constants.py: shared HTTP timeout + User-Agent
from src.crawler.seed_feeders_constants import HTTP_TIMEOUT_S, USER_AGENT

_DIRECTIVE_RE = re.compile(r'^\s*(allow|disallow|sitemap)\s*:\s*(.+?)\s*$', re.IGNORECASE)


# FUNCTIONS

# GET <base>/robots.txt; None on any non-200 response or network error — both are normal
# outcomes for this directive, not failures (a missing robots.txt is expected on many hosts).
async def fetch_robots_txt(client: httpx.AsyncClient, base_url: str) -> str | None:
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = await client.get(robots_url, timeout=HTTP_TIMEOUT_S,
                                    headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return response.text


# Extract Allow/Disallow path values (resolved to absolute URLs against base_url, kept
# regardless of what the directive actually permits — they disclose site structure either way)
# and Sitemap: URLs, from robots.txt text. Directive grouping (User-agent blocks) is ignored on
# purpose: every Allow/Disallow/Sitemap line in the file is collected, not just one block's.
def parse_robots_directives(text: str, base_url: str) -> dict:
    paths = []
    sitemaps = []
    for line in text.splitlines():
        line = line.split("#", 1)[0]
        match = _DIRECTIVE_RE.match(line)
        if not match:
            continue
        directive, value = match.group(1).lower(), match.group(2).strip()
        if not value:
            continue
        if directive == "sitemap":
            sitemaps.append(urljoin(base_url, value))
        else:
            paths.append(urljoin(base_url, value))
    return {"paths": paths, "sitemaps": sitemaps}
