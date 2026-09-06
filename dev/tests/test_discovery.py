"""Tests for src/crawler/discovery.py — the feeder-merge discovery entry point.

Two layers. Pure-logic, no network: seed assembly/merge-priority/failed-feeder recording
(synthetic FeederResults). Fixture-backed, real network but only ever against the local
`dev/url_discovery/_fixture_site.py` server, never a live host (see process-docs/
url_discovery/2026-08-28_validation_against_live_sites_was_the_wrong_unit.md for why): ONE real
`discover_urls_workflow` run for the whole file (module-scoped `discovery_result` fixture below,
not re-run per assertion), checked field by field against the fixture's own `ground_truth()`.

discover_urls_workflow no longer runs a browser-driven link-graph traversal after the feeders —
that phase was removed as a duplicate fetch of every page in the run (link-following now belongs
to the scrape step, which already loads each page for its content). Every test that exercised the
removed traversal (resume_state building/validation, stop-reason determination, the exact-host
scope filter, `_merge_results`'s fetched/frontier-leftover/canonical_url handling, version-
duplicate alias recognition) is gone with it, not weakened to still pass against the new shape.
"""
import asyncio

import pytest

from src.crawler.seed_feeders_scope import FeederResult
from src.crawler.discovery import DiscoveredURL, DiscoveryResult, _assemble_seeds, discover_urls_workflow
from dev.url_discovery._fixture_site import start_fixture_server, stop_fixture_server, ground_truth, seed_url


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
# discover_urls_workflow — the one path testable without a real feeder run
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discover_urls_workflow_invalid_seed_url_is_failed_not_empty():
    result = await discover_urls_workflow("not-a-url-at-all")
    assert isinstance(result, DiscoveryResult)
    assert result.ok is False
    assert result.urls == []
    assert result.error is not None


# ---------------------------------------------------------------------------
# Fixture-backed checks (dev/url_discovery/_fixture_site.py) — the real feeder-merge run, run for
# real but only ever against the local fixture server. ONE real discover_urls_workflow run for the
# whole file (discovery_result below is module-scoped).
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fixture_server():
    server, thread, port = start_fixture_server()
    yield port
    stop_fixture_server(server, thread)


@pytest.fixture(scope="module")
def gt():
    return ground_truth()


@pytest.fixture(scope="module")
def discovery_result(fixture_server):
    return asyncio.run(discover_urls_workflow(seed_url(fixture_server)))


def test_discover_urls_workflow_total_matches_fixture_ground_truth(discovery_result, gt):
    assert discovery_result.ok is True
    assert discovery_result.failed_feeders == {}
    assert len(discovery_result.urls) == gt["total_urls"]


def test_discover_urls_workflow_source_breakdown_matches_fixture_ground_truth(discovery_result, gt):
    by_source = {}
    for u in discovery_result.urls:
        by_source[u.source] = by_source.get(u.source, 0) + 1
    assert by_source == gt["by_source"]


def test_discover_urls_workflow_no_url_carries_a_fetched_or_canonical_field(discovery_result):
    # DiscoveredURL is url+source only now — no page is ever fetched by discovery itself, so there
    # is nothing left for a fetched/canonical_url flag to distinguish (see discovery.py's Gotchas).
    for u in discovery_result.urls:
        assert isinstance(u, DiscoveredURL)
        assert not hasattr(u, "fetched")
        assert not hasattr(u, "canonical_url")
