"""Tests for src/crawler/seed_feeders*.py — robots.txt + sitemap seed feeders.

Two layers. Pure-function, no network at all: fetch-layer tests inject a fake httpx client
directly (fetch_robots_txt/fetch_sitemap take `client` as a parameter — no monkeypatching
needed); workflow-level tests monkeypatch `seed_feeders.httpx.AsyncClient`, an established
fake-client pattern in this project's test suite. Fixture-backed, real network but only ever
against the local `dev/url_discovery/_fixture_site.py` server, never a live host (see
process-docs/url_discovery/2026-08-28_validation_against_live_sites_was_the_wrong_unit.md for
why): one shared module-scoped server for the whole file, each of the three feeders checked
against the exact fixture feature built for it — replacing the one-off, unrepeatable
docs.github.com/theblock.co/ui.shadcn.com/nextjs.org runs process-docs/url_discovery/
2026-08-28_robots_sitemap_seed_feeders.md and 2026-08-28_navtree_seed_feeder.md recorded.
"""
import json

import pytest

from src.crawler.seed_feeders_scope import FeederResult, normalize_url, scope_and_dedup
from src.crawler.seed_feeders_robots import fetch_robots_txt, parse_robots_directives
from src.crawler.seed_feeders_sitemap import fetch_sitemap, parse_sitemap_xml, resolve_sitemap_urls
from src.crawler.seed_feeders_navtree import (
    extract_payloads, find_navigation_tree, _build_version_urls, canonicalize_version_url,
    resolve_navigation_tree,
)
from src.crawler import seed_feeders
from dev.url_discovery._fixture_site import (
    start_fixture_server, stop_fixture_server, seed_url, DEFAULT_HOST,
    RSC_DEMO_ROOT, RSC_DEMO_CHILDREN, ROBOTS_DISALLOW_PATHS, ROBOTS_ALLOW_PATHS,
    SITEMAP_BLOG_PAGES, SITEMAP_LEGAL_PAGES, NAVTREE_CANONICAL_PAGES, NAVTREE_V1_ONLY_PAGES,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code: int, content: bytes = b"", text: str = None):
        self.status_code = status_code
        self.content = content
        self.text = text if text is not None else content.decode("utf-8", errors="ignore")


class _FakeAsyncClient:
    """Routes GET requests by exact URL; unmapped URLs come back 404."""

    def __init__(self, routes: dict):
        self._routes = routes

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, **kwargs):
        return self._routes.get(url, _FakeResponse(404))


def _xml(body: str) -> bytes:
    return f'<?xml version="1.0" encoding="UTF-8"?>{body}'.encode()


def _next_data_html(payload: dict) -> str:
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script></html>'


def _rsc_html(rows: list) -> str:
    # One push call carrying every row, JSON-escaped exactly as a real page embeds it
    content = "\n".join(rows)
    return f'<html><script>self.__next_f.push([1,{json.dumps(content)}])</script></html>'


# ---------------------------------------------------------------------------
# normalize_url — merge-vs-keep-distinct boundary (see seed_feeders_scope.py docstring)
# ---------------------------------------------------------------------------

def test_normalize_url_lowercases_scheme_and_host():
    assert normalize_url("HTTP://Example.COM/a") == "http://example.com/a"


def test_normalize_url_strips_default_port():
    assert normalize_url("https://example.com:443/a") == "https://example.com/a"
    assert normalize_url("http://example.com:80/a") == "http://example.com/a"


def test_normalize_url_keeps_non_default_port():
    assert normalize_url("https://example.com:8443/a") == "https://example.com:8443/a"


def test_normalize_url_collapses_empty_path_to_root():
    assert normalize_url("https://example.com") == "https://example.com/"


def test_normalize_url_drops_fragment():
    assert normalize_url("https://example.com/a#section") == "https://example.com/a"


def test_normalize_url_keeps_query_string_verbatim():
    assert normalize_url("https://example.com/a?page=2") == "https://example.com/a?page=2"


def test_normalize_url_keeps_non_root_trailing_slash_distinct():
    assert normalize_url("https://example.com/a/") == "https://example.com/a/"
    assert normalize_url("https://example.com/a/") != normalize_url("https://example.com/a")


def test_normalize_url_preserves_legacy_params_segment():
    # urlparse would split ";jsessionid=ABC" into its own .params field and drop it on rebuild;
    # normalize_url uses urlsplit specifically so this stays part of path (review note #3)
    assert normalize_url("https://example.com/a;jsessionid=ABC") == "https://example.com/a;jsessionid=ABC"


def test_normalize_url_raises_on_bad_port():
    with pytest.raises(ValueError):
        normalize_url("https://example.com:notaport/a")


# ---------------------------------------------------------------------------
# scope_and_dedup — host scope + the same merge boundary applied end-to-end
# ---------------------------------------------------------------------------

def test_scope_and_dedup_drops_foreign_host():
    urls = ["https://docs.example.com/a", "https://evil.example.org/a"]
    assert scope_and_dedup(urls, "docs.example.com") == ["https://docs.example.com/a"]


def test_scope_and_dedup_collapses_www_and_apex_keeping_first_seen():
    urls = ["https://www.example.com/a", "https://example.com/a"]
    result = scope_and_dedup(urls, "example.com")
    assert result == ["https://www.example.com/a"]


def test_scope_and_dedup_scope_check_ignores_www_on_seed_host_too():
    urls = ["https://www.example.com/a"]
    assert scope_and_dedup(urls, "www.example.com") == ["https://www.example.com/a"]


def test_scope_and_dedup_keeps_distinct_query_strings():
    urls = ["https://example.com/a?page=1", "https://example.com/a?page=2"]
    assert scope_and_dedup(urls, "example.com") == urls


def test_scope_and_dedup_keeps_distinct_http_vs_https():
    urls = ["http://example.com/a", "https://example.com/a"]
    assert scope_and_dedup(urls, "example.com") == urls


def test_scope_and_dedup_keeps_distinct_params_segment():
    urls = ["https://example.com/a;p=1", "https://example.com/a;p=2"]
    assert scope_and_dedup(urls, "example.com") == urls


def test_scope_and_dedup_merges_default_port_and_case_duplicates():
    urls = ["https://Example.com:443/a", "https://example.com/a"]
    assert scope_and_dedup(urls, "example.com") == ["https://example.com/a"]


def test_scope_and_dedup_merges_empty_path_and_root_slash():
    urls = ["https://example.com", "https://example.com/"]
    assert scope_and_dedup(urls, "example.com") == ["https://example.com/"]


def test_scope_and_dedup_drops_malformed_url_without_raising():
    urls = ["https://example.com:notaport/a", "https://example.com/b"]
    assert scope_and_dedup(urls, "example.com") == ["https://example.com/b"]


def test_scope_and_dedup_preserves_first_seen_order():
    urls = ["https://example.com/c", "https://example.com/a", "https://example.com/c"]
    assert scope_and_dedup(urls, "example.com") == ["https://example.com/c", "https://example.com/a"]


# ---------------------------------------------------------------------------
# parse_robots_directives — Allow/Disallow paths + Sitemap: lines
# ---------------------------------------------------------------------------

def test_parse_robots_directives_extracts_paths_and_sitemap():
    text = (
        "User-agent: *\n"
        "Disallow: /search\n"
        "Allow: /public/\n"
        "Sitemap: https://example.com/sitemap_index.xml\n"
    )
    result = parse_robots_directives(text, "https://example.com/")
    assert result["paths"] == ["https://example.com/search", "https://example.com/public/"]
    assert result["sitemaps"] == ["https://example.com/sitemap_index.xml"]


def test_parse_robots_directives_case_insensitive_and_comment_stripped():
    text = "DISALLOW: /a  # internal only\nsitemap: /sitemap.xml\n"
    result = parse_robots_directives(text, "https://example.com/")
    assert result["paths"] == ["https://example.com/a"]
    assert result["sitemaps"] == ["https://example.com/sitemap.xml"]


def test_parse_robots_directives_multiple_user_agent_blocks_all_collected():
    text = (
        "User-agent: *\nDisallow: /a\n\n"
        "User-agent: GPTBot\nDisallow: /b\nDisallow: /c\n"
    )
    result = parse_robots_directives(text, "https://example.com/")
    assert result["paths"] == [
        "https://example.com/a", "https://example.com/b", "https://example.com/c",
    ]


def test_parse_robots_directives_ignores_blank_and_unrelated_lines():
    text = "User-agent: *\n\n# comment only\nCrawl-delay: 10\nDisallow: /x\n"
    result = parse_robots_directives(text, "https://example.com/")
    assert result["paths"] == ["https://example.com/x"]


def test_parse_robots_directives_empty_value_dropped():
    text = "User-agent: *\nDisallow:\n"
    result = parse_robots_directives(text, "https://example.com/")
    assert result["paths"] == []


# ---------------------------------------------------------------------------
# fetch_robots_txt — DI'd fake client, no monkeypatching
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_robots_txt_returns_text_on_200():
    client = _FakeAsyncClient({"https://example.com/robots.txt": _FakeResponse(200, text="Disallow: /a\n")})
    text = await fetch_robots_txt(client, "https://example.com/")
    assert text == "Disallow: /a\n"


@pytest.mark.asyncio
async def test_fetch_robots_txt_missing_returns_none_not_error():
    client = _FakeAsyncClient({})  # every URL 404s
    text = await fetch_robots_txt(client, "https://example.com/")
    assert text is None


# ---------------------------------------------------------------------------
# parse_sitemap_xml / fetch_sitemap
# ---------------------------------------------------------------------------

def test_parse_sitemap_xml_urlset():
    content = _xml(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://example.com/a</loc></url>"
        "<url><loc>https://example.com/b</loc></url>"
        "</urlset>"
    )
    kind, urls = parse_sitemap_xml(content)
    assert kind == "urlset"
    assert urls == ["https://example.com/a", "https://example.com/b"]


def test_parse_sitemap_xml_sitemapindex():
    content = _xml(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://example.com/sub1.xml</loc></sitemap>"
        "<sitemap><loc>https://example.com/sub2.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    kind, urls = parse_sitemap_xml(content)
    assert kind == "index"
    assert urls == ["https://example.com/sub1.xml", "https://example.com/sub2.xml"]


def test_parse_sitemap_xml_malformed_returns_unknown():
    kind, urls = parse_sitemap_xml(b"not xml at all <<<")
    assert (kind, urls) == ("unknown", [])


def test_parse_sitemap_xml_unrelated_root_returns_unknown():
    kind, urls = parse_sitemap_xml(_xml("<rss><channel/></rss>"))
    assert (kind, urls) == ("unknown", [])


@pytest.mark.asyncio
async def test_fetch_sitemap_404_returns_none_not_error():
    client = _FakeAsyncClient({})
    content = await fetch_sitemap(client, "https://example.com/sitemap.xml")
    assert content is None


# ---------------------------------------------------------------------------
# resolve_sitemap_urls — the nested-sitemapindex requirement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_sitemap_urls_flattens_two_level_nesting():
    top = _xml(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://example.com/mid.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    mid = _xml(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://example.com/leaf.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    leaf = _xml(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://example.com/page1</loc></url>"
        "<url><loc>https://example.com/page2</loc></url>"
        "</urlset>"
    )
    client = _FakeAsyncClient({
        "https://example.com/top.xml": _FakeResponse(200, content=top),
        "https://example.com/mid.xml": _FakeResponse(200, content=mid),
        "https://example.com/leaf.xml": _FakeResponse(200, content=leaf),
    })
    urls = await resolve_sitemap_urls(client, ["https://example.com/top.xml"])
    assert sorted(urls) == ["https://example.com/page1", "https://example.com/page2"]


@pytest.mark.asyncio
async def test_resolve_sitemap_urls_one_404_sub_is_normal_not_fatal():
    top = _xml(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://example.com/ok.xml</loc></sitemap>"
        "<sitemap><loc>https://example.com/missing.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    ok_leaf = _xml(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://example.com/page1</loc></url>"
        "</urlset>"
    )
    client = _FakeAsyncClient({
        "https://example.com/top.xml": _FakeResponse(200, content=top),
        "https://example.com/ok.xml": _FakeResponse(200, content=ok_leaf),
        # "missing.xml" intentionally absent from routes -> 404
    })
    urls = await resolve_sitemap_urls(client, ["https://example.com/top.xml"])
    assert urls == ["https://example.com/page1"]


@pytest.mark.asyncio
async def test_resolve_sitemap_urls_cycle_guard_does_not_hang():
    a = _xml(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://example.com/b.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    b = _xml(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://example.com/a.xml</loc></sitemap>"  # points back to a.xml
        "</sitemapindex>"
    )
    client = _FakeAsyncClient({
        "https://example.com/a.xml": _FakeResponse(200, content=a),
        "https://example.com/b.xml": _FakeResponse(200, content=b),
    })
    urls = await resolve_sitemap_urls(client, ["https://example.com/a.xml"])
    assert urls == []  # neither doc is a urlset, and the cycle terminates cleanly


# ---------------------------------------------------------------------------
# robots_feeder_workflow / sitemap_feeder_workflow — end-to-end, fake client injected
# via monkeypatching seed_feeders.httpx.AsyncClient (workflows construct it internally)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_robots_feeder_workflow_returns_scoped_paths(monkeypatch):
    robots_text = "User-agent: *\nDisallow: /internal/\nAllow: /public/\n"
    routes = {"https://docs.example.com/robots.txt": _FakeResponse(200, text=robots_text)}
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.robots_feeder_workflow("https://docs.example.com/")
    assert result.ok is True
    assert result.urls == [
        "https://docs.example.com/internal/", "https://docs.example.com/public/",
    ]


@pytest.mark.asyncio
async def test_robots_feeder_workflow_missing_robots_is_ok_empty(monkeypatch):
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient({}))

    result = await seed_feeders.robots_feeder_workflow("https://docs.example.com/")
    assert result == FeederResult(urls=[], ok=True, source="robots")


@pytest.mark.asyncio
async def test_robots_feeder_workflow_invalid_seed_url_is_failed_not_empty():
    result = await seed_feeders.robots_feeder_workflow("not-a-url-at-all")
    assert result.ok is False
    assert result.urls == []
    assert result.error is not None


@pytest.mark.asyncio
async def test_sitemap_feeder_workflow_prefers_robots_declared_sitemap(monkeypatch):
    robots_text = "Sitemap: https://docs.example.com/declared.xml\n"
    urlset = _xml(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://docs.example.com/a</loc></url>"
        "</urlset>"
    )
    routes = {
        "https://docs.example.com/robots.txt": _FakeResponse(200, text=robots_text),
        "https://docs.example.com/declared.xml": _FakeResponse(200, content=urlset),
        # conventional paths deliberately NOT routed — if the feeder fell back to them
        # instead of the robots-declared one, this test would see an empty result
    }
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.sitemap_feeder_workflow("https://docs.example.com/")
    assert result.ok is True
    assert result.urls == ["https://docs.example.com/a"]


@pytest.mark.asyncio
async def test_sitemap_feeder_workflow_falls_back_to_conventional_paths(monkeypatch):
    urlset = _xml(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://docs.example.com/a</loc></url>"
        "</urlset>"
    )
    routes = {
        # no robots.txt at all -> declares no sitemaps -> conventional fallback used
        "https://docs.example.com/sitemap.xml": _FakeResponse(200, content=urlset),
    }
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.sitemap_feeder_workflow("https://docs.example.com/")
    assert result.ok is True
    assert result.urls == ["https://docs.example.com/a"]


@pytest.mark.asyncio
async def test_sitemap_feeder_workflow_all_404_is_ok_empty_docs_github_shape(monkeypatch):
    # Mirrors the docs.github.com reference case: robots.txt exists but declares no
    # Sitemap:, and both conventional fallback paths 404.
    routes = {
        "https://docs.example.com/robots.txt": _FakeResponse(200, text="User-agent: *\nDisallow: /a\n"),
    }
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.sitemap_feeder_workflow("https://docs.example.com/")
    assert result == FeederResult(urls=[], ok=True, source="sitemap")


@pytest.mark.asyncio
async def test_sitemap_feeder_workflow_drops_foreign_host_urls(monkeypatch):
    urlset = _xml(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://docs.example.com/a</loc></url>"
        "<url><loc>https://evil.example.org/b</loc></url>"
        "</urlset>"
    )
    routes = {"https://docs.example.com/sitemap.xml": _FakeResponse(200, content=urlset)}
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.sitemap_feeder_workflow("https://docs.example.com/")
    assert result.urls == ["https://docs.example.com/a"]


# ---------------------------------------------------------------------------
# extract_payloads — payload-shape detection (Pages Router __NEXT_DATA__, App Router RSC stream)
# ---------------------------------------------------------------------------

def test_extract_payloads_detects_next_data_shape():
    html = _next_data_html({"props": {"pageProps": {"a": 1}}})
    payloads = extract_payloads(html)
    assert payloads == [{"props": {"pageProps": {"a": 1}}}]


def test_extract_payloads_detects_rsc_stream_shape():
    html = _rsc_html(['1:{"a":1}', '2:{"b":2}'])
    payloads = extract_payloads(html)
    assert {"a": 1} in payloads
    assert {"b": 2} in payloads


def test_extract_payloads_rsc_skips_non_json_import_rows_without_erroring():
    # "I[...]" is a real row shape (module import reference) that never carries page data
    html = _rsc_html(['1:I[437976,["chunk.js"]]', '2:{"real":"data"}'])
    payloads = extract_payloads(html)
    assert payloads == [{"real": "data"}]


def test_extract_payloads_neither_shape_returns_empty():
    html = "<html><body>plain page, no framework payload</body></html>"
    assert extract_payloads(html) == []


# ---------------------------------------------------------------------------
# find_navigation_tree — tier 1 (structural tree walk) and tier 2 (flat href scan) fallback
# ---------------------------------------------------------------------------

def test_find_navigation_tree_walks_recursive_tree():
    payload = {
        "url": "/docs",
        "children": [
            {"url": "/docs/a"},
            {"url": "/docs/b", "children": [{"url": "/docs/b/c"}]},
        ],
    }
    hrefs, tier, source = find_navigation_tree([payload])
    assert tier == "tree"
    assert source is payload
    assert sorted(hrefs) == ["/docs", "/docs/a", "/docs/b", "/docs/b/c"]


def test_find_navigation_tree_picks_the_largest_candidate():
    payload = {
        "smallWidget": {"href": "/x", "children": [{"href": "/x/a"}]},
        "realNav": {"href": "/docs", "children": [
            {"href": "/docs/a"}, {"href": "/docs/b"}, {"href": "/docs/c"},
        ]},
    }
    hrefs, tier, source = find_navigation_tree([payload])
    assert tier == "tree"
    assert sorted(hrefs) == ["/docs", "/docs/a", "/docs/b", "/docs/c"]


def test_find_navigation_tree_rejects_react_element_children_as_a_tree():
    # Real shape observed on ui.shadcn.com: a rendered <button> element whose "children" prop is
    # a list of OTHER React elements (each itself a 4-item ["$", tag, key, props] list), not a
    # list of plain data dicts — must not be mistaken for a navigation-tree node.
    payload = {
        "href": "/prev-page",
        "children": [["$", "svg", None, {}], ["$", "span", None, {"children": "Previous"}]],
    }
    hrefs, tier, source = find_navigation_tree([payload])
    assert tier == "flat"
    assert source is None
    assert hrefs == ["/prev-page"]  # still recovered, just via the flat tier, not the tree tier


def test_find_navigation_tree_tier2_filters_fragment_and_internal_asset_paths():
    payload = {"links": [
        {"href": "/a"}, {"href": "#anchor-only"}, {"href": "/_next/static/chunk.css"}, {"href": ""},
    ]}
    hrefs, tier, source = find_navigation_tree([payload])
    assert tier == "flat"
    assert hrefs == ["/a"]


def test_find_navigation_tree_no_payloads_returns_empty_flat():
    assert find_navigation_tree([]) == ([], "flat", None)


# ---------------------------------------------------------------------------
# _build_version_urls / canonicalize_version_url — the framework-specific version handling
# ---------------------------------------------------------------------------

def test_build_version_urls_constructs_url_per_other_version():
    all_versions = {"v1": {}, "v2": {}, "v3": {}}
    urls = _build_version_urls("https://x.test/de/guide", all_versions, "v1", "/guide")
    assert urls == {
        "v2": "https://x.test/de/v2/guide",
        "v3": "https://x.test/de/v3/guide",
    }
    assert "v1" not in urls  # current version's tree is already in hand, not rebuilt


def test_build_version_urls_strips_version_prefix_when_seed_is_a_non_default_version():
    # Mirrors the real GHEC-as-seed case: currentPathWithoutLanguage still carries the version
    all_versions = {"v1": {}, "v2": {}}
    urls = _build_version_urls("https://x.test/de/v2/guide", all_versions, "v2", "/v2/guide")
    assert urls == {"v1": "https://x.test/de/v1/guide"}


def test_build_version_urls_empty_when_a_required_field_is_missing():
    assert _build_version_urls("https://x.test/de/guide", None, "v1", "/guide") == {}
    assert _build_version_urls("https://x.test/de/guide", {"v1": {}, "v2": {}}, None, "/guide") == {}
    assert _build_version_urls("https://x.test/de/guide", {"v1": {}, "v2": {}}, "v1", None) == {}


def test_build_version_urls_empty_when_content_path_not_a_suffix_of_seed():
    all_versions = {"v1": {}, "v2": {}}
    urls = _build_version_urls("https://x.test/de/guide", all_versions, "v1", "/unrelated-path")
    assert urls == {}


def test_canonicalize_version_url_strips_matching_segment_anywhere_in_path():
    url = "https://x.test/de/v2/guide/a"
    assert canonicalize_version_url(url, ["v1", "v2"]) == "https://x.test/de/guide/a"


def test_canonicalize_version_url_noop_when_no_marker_present():
    url = "https://x.test/de/guide/a"
    assert canonicalize_version_url(url, ["v1", "v2"]) == url


def test_canonicalize_version_url_preserves_query():
    url = "https://x.test/de/v2/guide?page=2"
    assert canonicalize_version_url(url, ["v2"]) == "https://x.test/de/guide?page=2"


# ---------------------------------------------------------------------------
# resolve_navigation_tree — end-to-end union + canonicalize, DI'd fake client
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_navigation_tree_unions_versions_and_dedups_via_canonicalization():
    default_payload = {"props": {"pageProps": {"mainContext": {
        "sidebarTree": {"href": "/de/guide", "childPages": [
            {"href": "/de/guide/intro", "childPages": []},
            {"href": "/de/guide/setup", "childPages": []},
        ]},
        "allVersions": {"v1": {"version": "v1"}, "v2": {"version": "v2"}},
        "currentVersion": "v1",
        "currentPathWithoutLanguage": "/guide",
    }}}}
    v2_payload = {"props": {"pageProps": {"mainContext": {
        "sidebarTree": {"href": "/de/v2/guide", "childPages": [
            {"href": "/de/v2/guide/intro", "childPages": []},
            {"href": "/de/v2/guide/legacy-page", "childPages": []},  # only exists in v2
        ]},
    }}}}
    routes = {
        "https://docs.example.com/de/guide": _FakeResponse(200, text=_next_data_html(default_payload)),
        "https://docs.example.com/de/v2/guide": _FakeResponse(200, text=_next_data_html(v2_payload)),
    }
    client = _FakeAsyncClient(routes)

    urls, tier, version_keys = await resolve_navigation_tree(client, "https://docs.example.com/de/guide")
    assert tier == "tree"
    assert sorted(set(urls)) == sorted([
        "https://docs.example.com/de/guide",
        "https://docs.example.com/de/guide/intro",
        "https://docs.example.com/de/guide/setup",
        "https://docs.example.com/de/guide/legacy-page",  # recovered only via the v2 union
    ])
    # version_keys is the site's own version-key list — surfaced so discovery.py's traversal can
    # recognize an explicit-version duplicate of an already-known canonical page without
    # reimplementing this feeder's own detection (see FeederResult.version_keys).
    assert sorted(version_keys) == ["v1", "v2"]


@pytest.mark.asyncio
async def test_resolve_navigation_tree_unfetchable_seed_raises_not_empty():
    # The seed is the target of the whole run, unlike a version root or robots.txt/a sitemap —
    # its own fetch failure must not look like "this site has no navigation tree" (review note).
    client = _FakeAsyncClient({})  # every URL 404s
    with pytest.raises(RuntimeError, match="could not fetch seed_url"):
        await resolve_navigation_tree(client, "https://docs.example.com/de/guide")


# ---------------------------------------------------------------------------
# navtree_feeder_workflow — end-to-end FeederResult contract, source tags both tiers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_navtree_feeder_workflow_next_data_shape_end_to_end(monkeypatch):
    payload = {"tree": {"url": "/docs", "children": [{"url": "/docs/a"}, {"url": "/docs/b"}]}}
    routes = {"https://docs.example.com/": _FakeResponse(200, text=_next_data_html(payload))}
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.navtree_feeder_workflow("https://docs.example.com/")
    assert result.ok is True
    assert result.source == "navtree_tree"
    assert sorted(result.urls) == [
        "https://docs.example.com/docs", "https://docs.example.com/docs/a", "https://docs.example.com/docs/b",
    ]


@pytest.mark.asyncio
async def test_navtree_feeder_workflow_rsc_tree_shape_does_not_fall_through(monkeypatch):
    # The App Router shape carrying a genuine structured tree (the ui.shadcn.com/Fumadocs case)
    # — a detector that only knows __NEXT_DATA__ would silently find nothing here at all.
    rows = [
        '1:{"tree":{"type":"root","name":"Docs","children":['
        '{"type":"page","name":"A","url":"/docs/a"},'
        '{"type":"page","name":"B","url":"/docs/b"}]}}'
    ]
    routes = {"https://docs.example.com/": _FakeResponse(200, text=_rsc_html(rows))}
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.navtree_feeder_workflow("https://docs.example.com/")
    assert result.ok is True
    assert result.source == "navtree_tree"
    assert sorted(result.urls) == ["https://docs.example.com/docs/a", "https://docs.example.com/docs/b"]


@pytest.mark.asyncio
async def test_navtree_feeder_workflow_rsc_dom_only_shape_falls_back_to_flat_tier(monkeypatch):
    # The App Router shape with no structured tree at all (the nextjs.org/docs case) — a single
    # rendered <a> element, href present but "children" is text, not a list of tree nodes.
    rows = ['1:["$","a",null,{"href":"/docs/only-link","children":"Link text"}]']
    routes = {"https://docs.example.com/": _FakeResponse(200, text=_rsc_html(rows))}
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.navtree_feeder_workflow("https://docs.example.com/")
    assert result.ok is True
    assert result.source == "navtree_flat"
    assert result.urls == ["https://docs.example.com/docs/only-link"]


@pytest.mark.asyncio
async def test_navtree_feeder_workflow_neither_shape_is_ok_empty(monkeypatch):
    # Reachable, but genuinely carries no framework payload — a normal empty outcome.
    routes = {"https://docs.example.com/": _FakeResponse(200, text="<html>plain page</html>")}
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(routes))

    result = await seed_feeders.navtree_feeder_workflow("https://docs.example.com/")
    assert result == FeederResult(urls=[], ok=True, source="navtree_flat")


@pytest.mark.asyncio
async def test_navtree_feeder_workflow_unreachable_seed_is_failed_not_ok_empty(monkeypatch):
    # Contrast with the test above: here the seed itself never loads at all (every URL 404s) —
    # must be ok=False, not indistinguishable from "reachable, no navigation tree" (review note).
    monkeypatch.setattr(seed_feeders.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient({}))

    result = await seed_feeders.navtree_feeder_workflow("https://docs.example.com/")
    assert result.ok is False
    assert result.urls == []
    assert result.source is None
    assert result.error is not None


@pytest.mark.asyncio
async def test_navtree_feeder_workflow_invalid_seed_url_is_failed_not_empty():
    result = await seed_feeders.navtree_feeder_workflow("not-a-url-at-all")
    assert result.ok is False
    assert result.urls == []
    assert result.error is not None


# ---------------------------------------------------------------------------
# Fixture-backed checks (dev/url_discovery/_fixture_site.py) — real network, but only ever
# against the local fixture server, never a live host. One module-scoped server for the whole
# file (fixture_server below) — every test here shares the same real server, no per-test startup.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fixture_server():
    server, thread, port = start_fixture_server()
    yield port
    stop_fixture_server(server, thread)


def _fixture_url(port: int, path: str) -> str:
    return f"http://{DEFAULT_HOST}:{port}{path}"


@pytest.mark.asyncio
async def test_robots_feeder_against_fixture_collects_allow_and_disallow(fixture_server):
    # The deliberate behavior process-docs/url_discovery/2026-08-28_robots_sitemap_seed_feeders.md
    # documents: Allow AND Disallow paths are both collected as seeds, regardless of what they
    # permit — checked here against a stable local host instead of a one-off live snapshot.
    result = await seed_feeders.robots_feeder_workflow(seed_url(fixture_server))
    assert result.ok is True
    assert result.source == "robots"
    expected = {_fixture_url(fixture_server, p) for p in ROBOTS_DISALLOW_PATHS + ROBOTS_ALLOW_PATHS}
    assert set(result.urls) == expected


@pytest.mark.asyncio
async def test_sitemap_feeder_against_fixture_resolves_two_level_nested_index(fixture_server):
    # The recursive-resolution claim process-docs/url_discovery/2026-08-28_robots_sitemap_seed_
    # feeders.md verified against theblock.co's 63-sub-sitemap index — a live tree that changes
    # every run. This fixture's 2-level nesting (sitemap_index.xml -> sitemap-docs-group.xml,
    # itself an index -> two leaf urlsets) exercises the same recursion, with a result that never
    # drifts between runs.
    result = await seed_feeders.sitemap_feeder_workflow(seed_url(fixture_server))
    assert result.ok is True
    assert result.source == "sitemap"
    expected = {_fixture_url(fixture_server, p) for p in SITEMAP_BLOG_PAGES + SITEMAP_LEGAL_PAGES}
    assert set(result.urls) == expected


@pytest.mark.asyncio
async def test_navtree_feeder_against_fixture_unions_versions_and_recovers_oldest_only_pages(fixture_server):
    # The version-union claim process-docs/url_discovery/2026-08-28_navtree_seed_feeder.md
    # verified against docs.github.com (254 -> 304 URLs, a snapshot that has already drifted once
    # on record). This fixture's 3-version tree makes "2 pages exist only in the oldest version" an
    # exact, named set instead of an unlabeled part of a larger live count.
    result = await seed_feeders.navtree_feeder_workflow(seed_url(fixture_server))
    assert result.ok is True
    assert result.source == "navtree_tree"
    expected = {_fixture_url(fixture_server, p) for p in NAVTREE_CANONICAL_PAGES + NAVTREE_V1_ONLY_PAGES}
    assert set(result.urls) == expected


@pytest.mark.asyncio
async def test_navtree_feeder_against_fixture_detects_rsc_app_router_shape(fixture_server):
    # The OTHER payload shape process-docs/url_discovery/2026-08-28_navtree_seed_feeder.md
    # verified against ui.shadcn.com (substituted for the challenge-gated coindesk.com) — this
    # fixture's isolated /rsc-demo island exercises the same self.__next_f.push extractor
    # directly, deterministically, without depending on any third-party site being reachable.
    result = await seed_feeders.navtree_feeder_workflow(_fixture_url(fixture_server, RSC_DEMO_ROOT))
    assert result.ok is True
    assert result.source == "navtree_tree"
    expected = {_fixture_url(fixture_server, p) for p in RSC_DEMO_CHILDREN}
    assert set(result.urls) == expected
