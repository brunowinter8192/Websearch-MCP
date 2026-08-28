"""Tests for src/crawler/seed_feeders*.py — robots.txt + sitemap seed feeders.

Pure-function tests run with no network at all. Fetch-layer tests inject a fake httpx client
directly (fetch_robots_txt/fetch_sitemap take `client` as a parameter — no monkeypatching
needed). Workflow-level tests monkeypatch `seed_feeders.httpx.AsyncClient`, mirroring this
project's own `test_marginalia_engine.py` fake-client pattern.
"""
import pytest

from src.crawler.seed_feeders_scope import FeederResult, normalize_url, scope_and_dedup
from src.crawler.seed_feeders_robots import fetch_robots_txt, parse_robots_directives
from src.crawler.seed_feeders_sitemap import fetch_sitemap, parse_sitemap_xml, resolve_sitemap_urls
from src.crawler import seed_feeders


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
    assert result == FeederResult(urls=[], ok=True)


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
    assert result == FeederResult(urls=[], ok=True)


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
