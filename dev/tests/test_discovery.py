"""Tests for src/crawler/discovery.py — the feeders-into-traversal discovery entry point.

Two layers. Pure-logic, no network: seed assembly/merge-priority/failed-feeder recording
(synthetic FeederResults), resume_state building/validation, stop-reason determination (a plain
captured-state dict or None, plus max_pages — no strategy object, no private attribute), the
exact-host scope filter, and the version-duplicate recognition chain (`_extract_version_keys`,
`_resolve_canonical_alias`, and `_merge_results`'s own `version_keys` handling — including the
version-less-site proof: `version_keys=None` produces a byte-identical result to omitting the
argument entirely). Fixture-backed, real crawl4ai-driven traversal but only ever against the
local `dev/url_discovery/_fixture_site.py` server, never a live host (see process-docs/
url_discovery/2026-08-28_validation_against_live_sites_was_the_wrong_unit.md for why): ONE real
`discover_urls_workflow` run for the whole file (module-scoped `discovery_result` fixture below,
not re-run per assertion), checked field by field against the fixture's own `ground_truth()` —
replacing the one-off docs.github.com/books.toscrape.com/ui.shadcn.com runs recorded in
process-docs/url_discovery/2026-08-28_frontier_wiring.md and 2026-08-28_fetch_success_and_
frontier_visibility.md, none of which could be repeated or trusted a second time.
"""
import asyncio

import pytest

from src.crawler.seed_feeders_scope import FeederResult
from src.crawler.discovery import (
    DiscoveredURL, DiscoveryResult, _ExactHostFilter, _assemble_seeds, _default_max_pages,
    _build_resume_state, _validate_resume_state, _determine_stop_reason, _merge_results,
    _extract_version_keys, _resolve_canonical_alias, discover_urls_workflow,
    MIN_MAX_PAGES, MAX_PAGES_PER_SEED,
)
from dev.url_discovery._fixture_site import (
    start_fixture_server, stop_fixture_server, ground_truth, seed_url, DEFAULT_HOST,
    ORPHAN_CHAIN, REVISIT_TEST_TARGET, VERSION_DUP_TARGET, VERSION_DUP_CANONICAL,
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
# _determine_stop_reason — takes the SAME captured state dict discovery.py's own on_state_change
# callback already produces (a plain dict, or None for zero successful fetches), plus max_pages;
# no strategy object and no private attribute read anywhere in this module anymore.
# ---------------------------------------------------------------------------

def test_determine_stop_reason_frontier_exhausted_when_under_budget():
    assert _determine_stop_reason({"pages_crawled": 42}, max_pages=500) == "frontier_exhausted"


def test_determine_stop_reason_max_pages_reached_at_exact_budget():
    assert _determine_stop_reason({"pages_crawled": 500}, max_pages=500) == "max_pages_reached"


def test_determine_stop_reason_max_pages_reached_when_overshot():
    # Real, observed behavior (books.toscrape.com: 586 actual vs. 500 requested) — max_pages is
    # enforced at BFS-level granularity, not per-page, so pages_crawled can exceed max_pages.
    assert _determine_stop_reason({"pages_crawled": 586}, max_pages=500) == "max_pages_reached"


def test_determine_stop_reason_frontier_exhausted_when_state_is_none():
    # state is None when no URL was ever successfully processed — the on_state_change callback
    # never fires in that case (crawl4ai only calls it after a successful result), so pages_crawled
    # must default to 0 rather than raise.
    assert _determine_stop_reason(None, max_pages=500) == "frontier_exhausted"


# ---------------------------------------------------------------------------
# _merge_results — fetched vs. failed vs. never-attempted, all visible, none silently dropped
# ---------------------------------------------------------------------------

def test_merge_results_seed_marked_fetched_when_its_own_attempt_succeeded():
    seeds = {"https://x.test/a": "seed", "https://x.test/b": "sitemap"}
    urls = _merge_results(seeds, fetched=["https://x.test/a", "https://x.test/b"], frontier_leftover=[])
    assert DiscoveredURL(url="https://x.test/a", source="seed", fetched=True) in urls
    assert DiscoveredURL(url="https://x.test/b", source="sitemap", fetched=True) in urls


def test_merge_results_seed_marked_not_fetched_when_its_own_attempt_failed():
    # A seed whose OWN traversal fetch failed (anti-bot block, 429, ...) must still appear in the
    # result (a feeder already confirmed it), but visibly marked fetched=False, not silently
    # treated the same as a confirmed page (the review's core complaint).
    seeds = {"https://x.test/a": "seed", "https://x.test/b": "navtree_tree"}
    urls = _merge_results(seeds, fetched=["https://x.test/a"], frontier_leftover=[])
    by_url = {u.url: u for u in urls}
    assert by_url["https://x.test/a"].fetched is True
    assert by_url["https://x.test/b"].fetched is False
    assert by_url["https://x.test/b"].source == "navtree_tree"  # attribution unchanged by the failure


def test_merge_results_genuinely_new_fetched_url_tagged_traversal():
    seeds = {"https://x.test/a": "seed"}
    urls = _merge_results(seeds, fetched=["https://x.test/a", "https://x.test/new"], frontier_leftover=[])
    by_url = {u.url: u for u in urls}
    assert by_url["https://x.test/new"] == DiscoveredURL(url="https://x.test/new", source="traversal", fetched=True)


def test_merge_results_frontier_leftover_included_and_marked_unfetched():
    # The review's point 2: a URL the frontier held when the page budget ran out must not be
    # silently discarded — it appears, tagged "traversal", fetched=False.
    seeds = {"https://x.test/a": "seed"}
    urls = _merge_results(seeds, fetched=["https://x.test/a"], frontier_leftover=["https://x.test/never-fetched"])
    by_url = {u.url: u for u in urls}
    assert by_url["https://x.test/never-fetched"] == DiscoveredURL(
        url="https://x.test/never-fetched", source="traversal", fetched=False)


def test_merge_results_no_duplicate_across_the_three_groups():
    # A URL cannot be BOTH a seed AND a fresh traversal find AND a frontier leftover at once in
    # real data, but first-write-wins must hold if it somehow overlaps.
    seeds = {"https://x.test/a": "seed"}
    urls = _merge_results(seeds, fetched=["https://x.test/a"], frontier_leftover=["https://x.test/a"])
    assert len([u for u in urls if u.url == "https://x.test/a"]) == 1


# ---------------------------------------------------------------------------
# _extract_version_keys — the navtree feeder's own version-key list, never derived or guessed
# ---------------------------------------------------------------------------

def test_extract_version_keys_returns_navtree_feeders_own_list():
    feeder_results = {
        "robots": FeederResult(urls=[], ok=True, source="robots"),
        "sitemap": FeederResult(urls=[], ok=True, source="sitemap"),
        "navtree": FeederResult(urls=[], ok=True, source="navtree_tree", version_keys=["v1", "v2"]),
    }
    assert _extract_version_keys(feeder_results) == ["v1", "v2"]


def test_extract_version_keys_none_when_navtree_has_no_versions():
    # The common case: a version-less site. version_keys defaults to None on FeederResult itself.
    feeder_results = {
        "navtree": FeederResult(urls=[], ok=True, source="navtree_tree"),
    }
    assert _extract_version_keys(feeder_results) is None


def test_extract_version_keys_none_when_navtree_feeder_failed():
    feeder_results = {
        "navtree": FeederResult(urls=[], ok=False, error="could not fetch seed_url"),
    }
    assert _extract_version_keys(feeder_results) is None


def test_extract_version_keys_none_when_navtree_missing_entirely():
    assert _extract_version_keys({}) is None


# ---------------------------------------------------------------------------
# _resolve_canonical_alias — an explicit-version duplicate of an already-known SEED, never of
# another traversal find (narrowly the navtree feeder's own rule, not general URL-equivalence)
# ---------------------------------------------------------------------------

def test_resolve_canonical_alias_matches_a_known_seed():
    seeds = {"https://x.test/docs/guide/intro": "navtree_tree"}
    assert _resolve_canonical_alias(
        "https://x.test/docs/v1/guide/intro", seeds, version_keys=["v1", "v2"]
    ) == "https://x.test/docs/guide/intro"


def test_resolve_canonical_alias_none_when_version_keys_is_none():
    # A version-less site: version_keys is None, canonicalization is skipped entirely — no
    # exception, no false match, zero extra work.
    seeds = {"https://x.test/docs/guide/intro": "navtree_tree"}
    assert _resolve_canonical_alias("https://x.test/docs/v1/guide/intro", seeds, version_keys=None) is None


def test_resolve_canonical_alias_none_when_canonicalized_form_is_not_a_known_seed():
    # Canonicalizes cleanly but doesn't match anything this run already knows — not a duplicate of
    # a KNOWN seed, so no alias is recorded (the narrow, deliberately-scoped rule).
    seeds = {"https://x.test/docs/guide/intro": "navtree_tree"}
    assert _resolve_canonical_alias("https://x.test/docs/v1/guide/other-page", seeds, version_keys=["v1"]) is None


def test_resolve_canonical_alias_none_for_a_genuinely_new_url_with_no_version_segment():
    # canonicalize_version_url is a no-op here (no matching segment) — must not spuriously match.
    seeds = {"https://x.test/docs/guide/intro": "navtree_tree"}
    assert _resolve_canonical_alias("https://x.test/blog/post-1", seeds, version_keys=["v1", "v2"]) is None


# ---------------------------------------------------------------------------
# _merge_results + version_keys — the version-duplicate case, and proof a version-less site is
# entirely unaffected
# ---------------------------------------------------------------------------

def test_merge_results_version_duplicate_gets_canonical_url_set_after_a_real_fetch():
    seeds = {"https://x.test/docs/guide/intro": "navtree_tree"}
    urls = _merge_results(
        seeds,
        fetched=["https://x.test/docs/guide/intro", "https://x.test/docs/v1/guide/intro"],
        frontier_leftover=[], version_keys=["v1", "v2"],
    )
    by_url = {u.url: u for u in urls}
    duplicate = by_url["https://x.test/docs/v1/guide/intro"]
    canonical = by_url["https://x.test/docs/guide/intro"]
    assert duplicate.source == "traversal"
    assert duplicate.fetched is True  # a real fetch still happened — annotation, not prevention
    assert duplicate.canonical_url == "https://x.test/docs/guide/intro"
    assert canonical.source == "navtree_tree"
    assert canonical.canonical_url is None  # the canonical entry itself is never touched


def test_merge_results_version_keys_none_is_byte_identical_to_omitting_the_argument():
    # A version-less site: version_keys defaults to None, canonicalization is skipped entirely —
    # must produce the exact same result as calling _merge_results with no version_keys at all.
    seeds = {"https://x.test/a": "seed"}
    urls_omitted = _merge_results(seeds, fetched=["https://x.test/a", "https://x.test/new"], frontier_leftover=[])
    urls_explicit_none = _merge_results(
        seeds, fetched=["https://x.test/a", "https://x.test/new"], frontier_leftover=[], version_keys=None)
    assert urls_omitted == urls_explicit_none
    assert {u.url: u for u in urls_explicit_none}["https://x.test/new"].canonical_url is None


def test_merge_results_non_matching_traversal_url_unaffected_by_active_version_keys():
    # A genuinely new page with no version segment must not be spuriously marked, even on a
    # versioned site where version_keys IS active for other URLs.
    seeds = {"https://x.test/a": "seed"}
    urls = _merge_results(seeds, fetched=["https://x.test/a", "https://x.test/genuinely-new"],
                          frontier_leftover=[], version_keys=["v1"])
    assert {u.url: u for u in urls}["https://x.test/genuinely-new"].canonical_url is None


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


# ---------------------------------------------------------------------------
# Fixture-backed checks (dev/url_discovery/_fixture_site.py) — the full crawl4ai-driven traversal,
# run for real but only ever against the local fixture server. ONE real discover_urls_workflow run
# for the whole file (discovery_result below is module-scoped), checked from several angles rather
# than re-run per assertion — the wall-time cost this file adds is exactly one real traversal, not
# one per test.
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


def _fixture_url(port: int, path: str) -> str:
    return f"http://{DEFAULT_HOST}:{port}{path}"


def test_discover_urls_workflow_total_and_stop_reason_match_fixture_ground_truth(discovery_result, gt):
    assert discovery_result.ok is True
    assert discovery_result.stop_reason == gt["expected_stop_reason"]
    assert discovery_result.failed_feeders == {}
    assert len(discovery_result.urls) == gt["total_urls"]


def test_discover_urls_workflow_source_breakdown_matches_fixture_ground_truth(discovery_result, gt):
    by_source = {}
    for u in discovery_result.urls:
        by_source[u.source] = by_source.get(u.source, 0) + 1
    assert by_source == gt["by_source"]


def test_discover_urls_workflow_pages_fetched_and_failed_match_fixture_ground_truth(discovery_result, gt):
    assert discovery_result.pages_fetched == gt["pages_fetched_expected"]
    assert discovery_result.pages_failed == gt["pages_failed_expected"]


def test_discover_urls_workflow_unfetchable_robots_seed_is_the_only_fetched_false_entry(
        discovery_result, gt, fixture_server):
    # process-docs/url_discovery/2026-08-28_fetch_success_and_frontier_visibility.md's own
    # fetched=False visibility fix, checked against a real, named failure instead of an
    # anti-bot/429 artifact that could not be reproduced on demand.
    unfetched = [u for u in discovery_result.urls if not u.fetched]
    expected_urls = {_fixture_url(fixture_server, p) for p in gt["robots"]["unfetchable_paths"]}
    assert {u.url for u in unfetched} == expected_urls
    assert len(unfetched) == gt["pages_failed_expected"]
    assert all(u.source == "robots" for u in unfetched)


def test_discover_urls_workflow_orphan_chain_reached_via_traversal(discovery_result, fixture_server):
    # The one thing link-graph traversal exists for — a page reachable by link alone, absent from
    # every feeder, 2 hops deep (proves BFS reaches beyond depth 1, not just depth 1 itself).
    by_url = {u.url: u for u in discovery_result.urls}
    for path in ORPHAN_CHAIN:
        entry = by_url[_fixture_url(fixture_server, path)]
        assert entry.source == "traversal"
        assert entry.fetched is True


def test_discover_urls_workflow_revisit_target_stays_attributed_to_its_own_feeder(
        discovery_result, fixture_server):
    # _build_resume_state's "visited" pre-population (already fixed, already shipped — see this
    # file's own test_build_resume_state_pre_populates_visited_with_every_seed and DOCS.md's
    # Gotchas): a link back to a URL a feeder already delivered must stay attributed to that
    # feeder, not be re-tagged "traversal" or fetched a second time.
    by_url = {u.url: u for u in discovery_result.urls}
    target = by_url[_fixture_url(fixture_server, REVISIT_TEST_TARGET)]
    assert target.source == "sitemap"
    assert target.fetched is True


def test_discover_urls_workflow_version_duplicate_recognized_as_known_alias_of_canonical(
        discovery_result, fixture_server):
    # The gap closed this milestone (previously the open item recorded in process-docs/
    # url_discovery/2026-08-28_fetch_success_and_frontier_visibility.md and src/crawler/DOCS.md's
    # own Gotchas): an explicit-version duplicate of an already-known canonical navtree page is
    # now recognized as an alias of that page, via seed_feeders_navtree.canonicalize_version_url
    # and the version keys FeederResult.version_keys now exposes. This is annotation, not
    # prevention — a real fetch still happens (fetched=True, its own real observed status), and
    # the canonical entry's own attribution is never touched. The duplicate stays visible (a real,
    # working URL a caller whose goal is a complete URL list should still see), now carrying
    # canonical_url pointing at the page it duplicates.
    by_url = {u.url: u for u in discovery_result.urls}
    duplicate = by_url[_fixture_url(fixture_server, VERSION_DUP_TARGET)]
    canonical = by_url[_fixture_url(fixture_server, VERSION_DUP_CANONICAL)]
    assert duplicate.source == "traversal"
    assert duplicate.fetched is True
    assert duplicate.canonical_url == canonical.url
    assert canonical.source == "navtree_tree"
    assert canonical.canonical_url is None  # the canonical entry itself is never touched
    assert duplicate.url != canonical.url


def test_discover_urls_workflow_small_max_pages_overshoots_by_one_bfs_level(fixture_server, gt):
    # The claim on record (src/crawler/DOCS.md's Gotchas, live books.toscrape.com measurement:
    # 586 actual vs. a requested 500): max_pages is enforced at BFS-LEVEL granularity, not
    # per-page — an entire in-flight level's batch completes before the next check can catch it,
    # so the real ceiling can exceed the requested number. max_pages is a normal caller-supplied
    # override (the parameter exists for exactly this), not an internal-only knob, so a caller
    # whose goal is maximum coverage is relying on this being a soft, not exact, ceiling — checked
    # here for real, not just via _determine_stop_reason's own arithmetic stub above.
    #
    # A separate real run (not the shared discovery_result — a deliberately different max_pages),
    # against the same already-running fixture_server. The PROPERTY, not a coincidence: every
    # pre-traversal seed is injected at depth 0 (_build_resume_state), so they are all fetched as
    # ONE BFS level — with max_pages set below that level's size, the real ceiling is the
    # pre-traversal seed count itself, from ground_truth() (never re-derived or hand-typed here,
    # so a fixture change that adds/removes a seed cannot silently point this failure at the wrong
    # cause). Measured directly before writing this assertion, twice, identical both times: with
    # max_pages=1, actual attempts landed at gt["pre_traversal_seed_count"] (15 today).
    result = asyncio.run(discover_urls_workflow(seed_url(fixture_server), max_pages=1))
    assert result.ok is True
    assert result.stop_reason == "max_pages_reached"
    actual_pages = result.pages_fetched + result.pages_failed
    assert actual_pages > 1  # the overshoot property itself
    assert actual_pages == gt["pre_traversal_seed_count"]  # the real ceiling: one whole BFS level
