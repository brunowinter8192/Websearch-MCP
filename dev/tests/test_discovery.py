"""Tests for src/crawler/discovery.py — the feeders-into-traversal discovery entry point.

Pure-logic coverage only: seed assembly/merge-priority/failed-feeder recording (synthetic
FeederResults, no network), resume_state building/validation, stop-reason determination (a tiny
stub standing in for BFSDeepCrawlStrategy — only ._pages_crawled/.max_pages are read), and the
exact-host scope filter (real host-string logic, no network). The full crawl4ai-driven traversal
itself is verified by real runs (see process-docs/url_discovery/), not mocked here — matching
this project's own M0 precedent: meaningfully mocking crawl4ai's internal batch loop isn't
practical or high-value compared to just running it for real.
"""
import pytest

from src.crawler.seed_feeders_scope import FeederResult
from src.crawler.discovery import (
    DiscoveryResult, _ExactHostFilter, _assemble_seeds, _default_max_pages, _build_resume_state,
    _validate_resume_state, _determine_stop_reason, discover_urls_workflow,
    MIN_MAX_PAGES, MAX_PAGES_PER_SEED,
)


# ---------------------------------------------------------------------------
# _assemble_seeds — merge priority, failed-feeder visibility, seed_url normalization
# ---------------------------------------------------------------------------

def test_assemble_seeds_includes_literal_seed_url_unconditionally():
    feeder_results = {
        "robots": FeederResult(urls=[], ok=True, source="robots"),
        "sitemap": FeederResult(urls=[], ok=True, source="sitemap"),
        "navtree": FeederResult(urls=[], ok=True, source="navtree_tree"),
    }
    seeds, failed = _assemble_seeds("https://docs.example.com/guide", feeder_results)
    assert seeds == {"https://docs.example.com/guide": "seed"}
    assert failed == {}


def test_assemble_seeds_merges_all_three_feeders_first_write_wins():
    feeder_results = {
        "robots": FeederResult(urls=["https://docs.example.com/a"], ok=True, source="robots"),
        "sitemap": FeederResult(urls=["https://docs.example.com/a", "https://docs.example.com/b"],
                                ok=True, source="sitemap"),
        "navtree": FeederResult(urls=["https://docs.example.com/c"], ok=True, source="navtree_tree"),
    }
    seeds, failed = _assemble_seeds("https://docs.example.com/", feeder_results)
    assert seeds["https://docs.example.com/a"] == "robots"  # robots ran first, kept its own attribution
    assert seeds["https://docs.example.com/b"] == "sitemap"
    assert seeds["https://docs.example.com/c"] == "navtree_tree"
    assert seeds["https://docs.example.com/"] == "seed"
    assert failed == {}


def test_assemble_seeds_seed_url_normalized_dedups_against_feeder_equivalent():
    # Trailing-slash-free seed_url vs. a feeder returning the normalized (same) form
    feeder_results = {
        "robots": FeederResult(urls=[], ok=True, source="robots"),
        "sitemap": FeederResult(urls=["https://docs.example.com/"], ok=True, source="sitemap"),
        "navtree": FeederResult(urls=[], ok=True, source="navtree_tree"),
    }
    seeds, failed = _assemble_seeds("https://DOCS.example.com", feeder_results)
    assert len(seeds) == 1  # one entry, not two — normalize_url makes both forms identical
    assert seeds["https://docs.example.com/"] == "seed"  # seed_url added first, kept its tag


def test_assemble_seeds_failed_feeder_recorded_not_silently_empty():
    feeder_results = {
        "robots": FeederResult(urls=[], ok=False, error="robots.txt fetch timed out"),
        "sitemap": FeederResult(urls=["https://docs.example.com/a"], ok=True, source="sitemap"),
        "navtree": FeederResult(urls=[], ok=False, error="could not fetch seed_url: ..."),
    }
    seeds, failed = _assemble_seeds("https://docs.example.com/", feeder_results)
    assert failed == {
        "robots": "robots.txt fetch timed out",
        "navtree": "could not fetch seed_url: ...",
    }
    assert seeds["https://docs.example.com/a"] == "sitemap"
    assert "robots" not in seeds.values()  # the failed feeder's (empty) urls contributed nothing


# ---------------------------------------------------------------------------
# _default_max_pages — the re-derived floor + per-seed term
# ---------------------------------------------------------------------------

def test_default_max_pages_single_seed_uses_the_floor():
    assert _default_max_pages(1) == MIN_MAX_PAGES


def test_default_max_pages_many_seeds_scales_linearly_once_it_exceeds_the_floor():
    num_seeds = 400
    assert _default_max_pages(num_seeds) == num_seeds * MAX_PAGES_PER_SEED
    assert _default_max_pages(num_seeds) > MIN_MAX_PAGES


# ---------------------------------------------------------------------------
# _build_resume_state / _validate_resume_state
# ---------------------------------------------------------------------------

def test_build_resume_state_stamps_every_seed_depth_zero_explicitly():
    seeds = {"https://x.test/a": "seed", "https://x.test/b": "robots"}
    resume_state = _build_resume_state(seeds)
    assert resume_state["depths"] == {"https://x.test/a": 0, "https://x.test/b": 0}
    assert resume_state["pending"] == [
        {"url": "https://x.test/a", "parent_url": None},
        {"url": "https://x.test/b", "parent_url": None},
    ]


def test_build_resume_state_pre_populates_visited_with_every_seed():
    # Without this, link_discovery's own dedup (checks ONLY "visited", never the pending list)
    # would "rediscover" an already-known seed linked FROM another page as if it were new,
    # wasting page budget and undercounting genuine traversal-only contribution (real finding).
    seeds = {"https://x.test/a": "seed", "https://x.test/b": "robots"}
    resume_state = _build_resume_state(seeds)
    assert set(resume_state["visited"]) == {"https://x.test/a", "https://x.test/b"}


def test_validate_resume_state_accepts_well_formed():
    resume_state = _build_resume_state({"https://x.test/a": "seed"})
    _validate_resume_state(resume_state)  # must not raise


def test_validate_resume_state_rejects_empty_dict():
    with pytest.raises(ValueError, match="pending"):
        _validate_resume_state({})


def test_validate_resume_state_rejects_wrong_key():
    with pytest.raises(ValueError, match="pending"):
        _validate_resume_state({"seed_urls": ["https://x.test/a"]})


def test_validate_resume_state_rejects_empty_pending_list():
    with pytest.raises(ValueError, match="non-empty list"):
        _validate_resume_state({"pending": [], "depths": {}})


def test_validate_resume_state_rejects_malformed_entry():
    with pytest.raises(ValueError, match="malformed pending entry"):
        _validate_resume_state({"pending": [{"url": "https://x.test/a"}], "depths": {}})  # no parent_url


def test_validate_resume_state_rejects_missing_depths_entry():
    resume_state = {
        "pending": [{"url": "https://x.test/a", "parent_url": None}],
        "depths": {},  # missing the entry for the one pending URL
    }
    with pytest.raises(ValueError, match="missing an explicit depths entry"):
        _validate_resume_state(resume_state)


# ---------------------------------------------------------------------------
# _determine_stop_reason — a tiny stub standing in for BFSDeepCrawlStrategy
# ---------------------------------------------------------------------------

class _StrategyStub:
    def __init__(self, pages_crawled: int, max_pages: int):
        self._pages_crawled = pages_crawled
        self.max_pages = max_pages


def test_determine_stop_reason_frontier_exhausted_when_under_budget():
    assert _determine_stop_reason(_StrategyStub(pages_crawled=42, max_pages=500)) == "frontier_exhausted"


def test_determine_stop_reason_max_pages_reached_at_exact_budget():
    assert _determine_stop_reason(_StrategyStub(pages_crawled=500, max_pages=500)) == "max_pages_reached"


def test_determine_stop_reason_max_pages_reached_when_overshot():
    # Real, observed behavior (books.toscrape.com: 586 actual vs. 500 requested) — max_pages is
    # enforced at BFS-level granularity, not per-page, so pages_crawled can exceed max_pages.
    assert _determine_stop_reason(_StrategyStub(pages_crawled=586, max_pages=500)) == "max_pages_reached"


# ---------------------------------------------------------------------------
# _ExactHostFilter — exact host match, www./apex collapsed, no subdomain leniency
# ---------------------------------------------------------------------------

def test_exact_host_filter_accepts_same_host():
    f = _ExactHostFilter("docs.example.com")
    assert f.apply("https://docs.example.com/a") is True


def test_exact_host_filter_collapses_www_and_apex():
    f = _ExactHostFilter("www.docs.example.com")
    assert f.apply("https://docs.example.com/a") is True
    f2 = _ExactHostFilter("docs.example.com")
    assert f2.apply("https://www.docs.example.com/a") is True


def test_exact_host_filter_rejects_sibling_subdomain():
    f = _ExactHostFilter("docs.example.com")
    assert f.apply("https://api.example.com/a") is False


def test_exact_host_filter_rejects_child_subdomain_too():
    # The scope decision is "the seed host and only the seed host: not path prefixed, not
    # subdomains" — a CHILD subdomain of the seed host is still not the seed host itself.
    f = _ExactHostFilter("docs.example.com")
    assert f.apply("https://something.docs.example.com/a") is False


def test_exact_host_filter_rejects_parent_domain():
    f = _ExactHostFilter("docs.example.com")
    assert f.apply("https://example.com/a") is False


def test_exact_host_filter_rejects_malformed_url_without_raising():
    # .hostname (not .port) is what apply() reads — a malformed IPv6 literal is what actually
    # raises ValueError on access; a bad port alone does not (only .port itself would raise for
    # that, and apply() never reads .port at all).
    f = _ExactHostFilter("docs.example.com")
    assert f.apply("https://[:::1]/a") is False


# ---------------------------------------------------------------------------
# discover_urls_workflow — the one path testable without a real crawl4ai run
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discover_urls_workflow_invalid_seed_url_is_failed_not_empty():
    result = await discover_urls_workflow("not-a-url-at-all")
    assert isinstance(result, DiscoveryResult)
    assert result.ok is False
    assert result.urls == []
    assert result.stop_reason is None
    assert result.error is not None
