# INFRASTRUCTURE
import asyncio
import time
from dataclasses import dataclass, field

# From src/crawler/seed_feeders.py: the three seed feeders sharing the FeederResult contract
from src.crawler.seed_feeders import robots_feeder_workflow, sitemap_feeder_workflow, navtree_feeder_workflow
# From src/crawler/seed_feeders_scope.py: normalize_url (so seed_url dedups against an equivalent
# feeder-found URL the same way feeder output already dedups against itself) and require_host
# (seed_url validation, the same precondition every feeder already uses).
from src.crawler.seed_feeders_scope import normalize_url, require_host

_FEEDER_WORKFLOWS = (
    ("robots", robots_feeder_workflow),
    ("sitemap", sitemap_feeder_workflow),
    ("navtree", navtree_feeder_workflow),
)


# One discovered URL and what produced it. source is "seed" (the literal seed_url) or a feeder's
# own FeederResult.source ("robots"/"sitemap"/"navtree_tree"/"navtree_flat"). No fetch is ever
# attempted by this module — a page is only ever fetched once, by the scrape step that follows
# discovery (see discover_urls_workflow's own docstring) — so there is nothing here for a
# fetched/failed flag to distinguish.
@dataclass
class DiscoveredURL:
    url: str
    source: str


# Result of one discovery run. ok=True even when one or two feeders failed (see
# discover_urls_workflow's own docstring) — failed_feeders makes that visible rather than letting
# the run proceed as if a failed feeder had simply found nothing. ok=False only when seed_url
# itself could not be used at all.
@dataclass
class DiscoveryResult:
    urls: list = field(default_factory=list)
    ok: bool = True
    wall_s: float = 0.0
    failed_feeders: dict = field(default_factory=dict)
    error: str | None = None


# ORCHESTRATOR

# Discover a site's URL set: run robots.txt/sitemap/navtree over plain HTTP and merge their output
# with the literal seed_url. No page is ever fetched in a browser here — a prior version of this
# module additionally opened a headless browser and re-fetched every one of these URLs purely to
# read the links on each page, looking for pages no feeder had listed. That traversal was removed:
# link-following belongs to the scrape step, which already loads each page for its content anyway,
# so a separate link-only pass was a duplicate fetch of every page in the run (measured on a real
# site: the feeders returned 3571 URLs in ~2s; the traversal over those same 3571 URLs was still
# running after 12 minutes, projected well over an hour — see process-docs/url_discovery/ for the
# full history of the traversal this replaces).
#
# A feeder returning ok=False contributes nothing SILENTLY — its name and error land in
# `failed_feeders`, always visible on the result, and the run still proceeds on whatever seeds the
# other feeders (plus the literal seed_url, which is injected unconditionally) did produce. The run
# itself is only ok=False when seed_url cannot be used at all (unparseable/hostless) — the same
# precondition class every feeder already uses; a degraded-but-nonzero seed set is a successful, if
# partial, run, not a failed one.
async def discover_urls_workflow(seed_url: str) -> DiscoveryResult:
    t0 = time.time()
    try:
        require_host(seed_url)
    except Exception as exc:
        return DiscoveryResult(ok=False, error=str(exc), wall_s=time.time() - t0)

    feeder_results = await _run_feeders(seed_url)
    seeds, failed_feeders = _assemble_seeds(seed_url, feeder_results)
    urls = [DiscoveredURL(url=url, source=source) for url, source in seeds.items()]
    return DiscoveryResult(urls=urls, ok=True, wall_s=time.time() - t0, failed_feeders=failed_feeders)


# FUNCTIONS

# Run all three feeders concurrently; returns {feeder_name: FeederResult}.
async def _run_feeders(seed_url: str) -> dict:
    results = await asyncio.gather(*[workflow(seed_url) for _, workflow in _FEEDER_WORKFLOWS])
    return {name: result for (name, _), result in zip(_FEEDER_WORKFLOWS, results)}


# Merge feeder output into one {url: source} seed set, first-write-wins (seed_url itself first,
# then robots/sitemap/navtree in that order), plus {feeder_name: error} for every ok=False feeder.
# seed_url is normalized the same way feeder output already is, so an equivalent URL from a
# feeder dedups against it instead of appearing as a spurious second entry.
def _assemble_seeds(seed_url: str, feeder_results: dict) -> tuple:
    seeds = {normalize_url(seed_url): "seed"}
    failed_feeders = {}
    for name, result in feeder_results.items():
        if not result.ok:
            failed_feeders[name] = result.error
            continue
        for url in result.urls:
            if url not in seeds:
                seeds[url] = result.source
    return seeds, failed_feeders
