# INFRASTRUCTURE
import asyncio
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, FilterChain
from crawl4ai.deep_crawling.filters import URLFilter

# From src/crawler/seed_feeders.py: the three seed feeders sharing the FeederResult contract
from src.crawler.seed_feeders import robots_feeder_workflow, sitemap_feeder_workflow, navtree_feeder_workflow
# From src/crawler/seed_feeders_scope.py: shared host validation/collapse, reused for consistency
# with what the feeders already consider in-scope
from src.crawler.seed_feeders_scope import normalize_url, host_key, require_host

# max_depth is deliberately generous, not a safety device — max_pages alone guarantees
# termination (see discover_urls_workflow), so depth only bounds REACH, never WORK. A real
# documentation site's link-diameter is almost always far below this (verified: books.toscrape.com
# reached depth 2 out of 10 available before its run stopped on budget, not depth).
DEFAULT_MAX_DEPTH = 10
# A chosen starting floor, not a measured optimum for any particular site — sized against the
# one number this project has on record (bare link-following measured 248 pages on
# docs.github.com/de/rest), not against seed count. A caller learns whether 500 was ever binding
# from DiscoveryResult.stop_reason, not from this constant being "the right number" — see
# process-docs/url_discovery/ for the full reasoning and the real run that produced 586 vs. this
# floor of 500 on books.toscrape.com.
MIN_MAX_PAGES = 500
# Linear in seed count, not compounding with depth — only matters once seed count is large enough
# to need more budget just to visit every seed once; stays bounded regardless of how generous
# max_depth is, since max_pages is the sole termination lever (see DEFAULT_MAX_DEPTH above).
MAX_PAGES_PER_SEED = 2

_FEEDER_WORKFLOWS = (
    ("robots", robots_feeder_workflow),
    ("sitemap", sitemap_feeder_workflow),
    ("navtree", navtree_feeder_workflow),
)


# One discovered URL and what first produced it — "seed" (the literal seed_url), a feeder's own
# `FeederResult.source` ("robots"/"sitemap"/"navtree_tree"/"navtree_flat"), or "traversal" (a link
# discovered mid-crawl that no feeder and no seed already carried).
@dataclass
class DiscoveredURL:
    url: str
    source: str


# Result of one discovery run. ok=True even when one or two feeders failed (see
# discover_urls_workflow's own docstring) — failed_feeders makes that visible rather than letting
# the run proceed as if a failed feeder had simply found nothing. ok=False only when seed_url
# itself could not be used at all. stop_reason distinguishes an exhausted frontier from an
# exhausted page budget; it is None when ok=False, since no traversal ever ran.
@dataclass
class DiscoveryResult:
    urls: list = field(default_factory=list)
    ok: bool = True
    stop_reason: str | None = None
    wall_s: float = 0.0
    failed_feeders: dict = field(default_factory=dict)
    error: str | None = None


# Exact-hostname scope filter for traversal-discovered links — collapses www./apex via the same
# host_key feeders already use, otherwise EXACT match only (no subdomain leniency). Deliberately
# NOT crawl4ai's own DomainFilter, whose _is_subdomain treats a child subdomain as in-scope by
# design — the wrong semantics for "the seed host and only the seed host" (see DOCS.md Gotchas).
class _ExactHostFilter(URLFilter):
    __slots__ = ("_seed_key",)

    def __init__(self, seed_host: str):
        super().__init__(name="ExactHostFilter")
        self._seed_key = host_key(seed_host)

    def apply(self, url: str) -> bool:
        try:
            host = urlsplit(url).hostname or ""
        except ValueError:
            return False
        return host_key(host) == self._seed_key


# ORCHESTRATOR

# Discover a site's URL set: seed the traversal frontier from all three feeders plus the literal
# seed_url itself, then traverse. `max_depth`/`max_pages` default to DEFAULT_MAX_DEPTH/a
# seed-count-scaled floor of MIN_MAX_PAGES (see those constants) when omitted.
#
# A feeder returning ok=False contributes nothing SILENTLY — its name and error land in
# `failed_feeders`, always visible on the result, and the run still proceeds on whatever seeds
# the other feeders (plus the literal seed_url, which is injected unconditionally) did produce.
# The run itself is only ok=False when seed_url cannot be used at all (unparseable/hostless) —
# the same precondition class every feeder already uses; a degraded-but-nonzero seed set is a
# successful, if partial, run, not a failed one.
async def discover_urls_workflow(seed_url: str, max_depth: int | None = None,
                                 max_pages: int | None = None) -> DiscoveryResult:
    t0 = time.time()
    try:
        seed_host = require_host(seed_url)
    except Exception as exc:
        return DiscoveryResult(ok=False, error=str(exc), wall_s=time.time() - t0)

    feeder_results = await _run_feeders(seed_url)
    seeds, failed_feeders = _assemble_seeds(seed_url, feeder_results)

    resolved_max_depth = max_depth if max_depth is not None else DEFAULT_MAX_DEPTH
    resolved_max_pages = max_pages if max_pages is not None else _default_max_pages(len(seeds))

    resume_state = _build_resume_state(seeds)
    _validate_resume_state(resume_state)

    try:
        discovered, stop_reason = await _traverse(seed_url, seed_host, resume_state,
                                                   resolved_max_depth, resolved_max_pages)
    except Exception as exc:
        return DiscoveryResult(ok=False, error=str(exc), failed_feeders=failed_feeders,
                               wall_s=time.time() - t0)

    for url in discovered:
        if url not in seeds:
            seeds[url] = "traversal"

    urls = [DiscoveredURL(url=u, source=src) for u, src in seeds.items()]
    return DiscoveryResult(urls=urls, ok=True, stop_reason=stop_reason,
                           wall_s=time.time() - t0, failed_feeders=failed_feeders)


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


# seeds + a fixed, seed-count-independent expansion budget — see MIN_MAX_PAGES/MAX_PAGES_PER_SEED.
def _default_max_pages(num_seeds: int) -> int:
    return max(MIN_MAX_PAGES, num_seeds * MAX_PAGES_PER_SEED)


# Build the resume_state BFSDeepCrawlStrategy needs, with EVERY seed's depth stamped explicitly
# at 0 rather than left to the strategy's own default (which does the same thing silently — see
# process-docs/url_discovery/2026-08-28_resume_state_preseed_probe.md Result 3 — this makes that
# choice visible in the data instead of relying on undocumented default behavior). "visited" is
# pre-populated with every known seed too — without it, link_discovery's own dedup (which checks
# ONLY the "visited" set, never the seeds/pending list) does not recognize an already-known seed
# rediscovered as a link FROM another page, spends part of the page budget "discovering" URLs the
# run already had, and undercounts genuine traversal-only contribution (see DOCS.md Gotchas for
# the real run that surfaced this and the caveat on normalization mismatch this fix does not
# fully close).
def _build_resume_state(seeds: dict) -> dict:
    return {
        "pending": [{"url": url, "parent_url": None} for url in seeds],
        "depths": {url: 0 for url in seeds},
        "visited": list(seeds.keys()),
    }


# Fail fast on the two silent-failure shapes M0 found (an empty dict, a wrong/missing "pending"
# key) plus malformed entries — raises ValueError, never silently hands a broken resume_state to
# the strategy, which would otherwise fall back to a plain single-start_url crawl or a silent
# empty one with no exception either way.
def _validate_resume_state(resume_state: dict) -> None:
    if not resume_state or "pending" not in resume_state:
        raise ValueError("resume_state missing a non-empty 'pending' key")
    pending = resume_state["pending"]
    if not isinstance(pending, list) or not pending:
        raise ValueError("resume_state['pending'] must be a non-empty list")
    depths = resume_state.get("depths", {})
    for item in pending:
        if not isinstance(item, dict) or "url" not in item or "parent_url" not in item:
            raise ValueError(f"malformed pending entry: {item!r}")
        if item["url"] not in depths:
            raise ValueError(f"pending URL missing an explicit depths entry: {item['url']!r}")


# Run the traversal itself: exact-host scope filter (include_external=True so crawl4ai's own
# crude same-page-netloc substring check — see DOCS.md Gotchas — never gets a chance to matter;
# this filter is the sole scope authority), lightweight fetch config (no markdown generation,
# this milestone only harvests URLs). Returns (discovered_urls, stop_reason).
async def _traverse(seed_url: str, seed_host: str, resume_state: dict,
                    max_depth: int, max_pages: int) -> tuple:
    strategy = BFSDeepCrawlStrategy(
        max_depth=max_depth,
        max_pages=max_pages,
        filter_chain=FilterChain([_ExactHostFilter(seed_host)]),
        include_external=True,
        resume_state=resume_state,
    )
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, wait_until="domcontentloaded",
        deep_crawl_strategy=strategy, stream=False, verbose=False,
    )
    browser_config = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(url=seed_url, config=config)

    stop_reason = _determine_stop_reason(strategy)
    discovered = [r.url for r in results if r.success]
    return discovered, stop_reason


# "max_pages_reached" if the strategy's own page count met/exceeded its budget, else
# "frontier_exhausted". Reads strategy._pages_crawled, a private crawl4ai attribute — see
# DOCS.md Gotchas for why this is fine to use but worth flagging.
def _determine_stop_reason(strategy: BFSDeepCrawlStrategy) -> str:
    if strategy._pages_crawled >= strategy.max_pages:
        return "max_pages_reached"
    return "frontier_exhausted"
