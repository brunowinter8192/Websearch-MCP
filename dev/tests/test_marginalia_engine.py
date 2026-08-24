"""Tests for src/search/engines/marginalia.py — pure result-parsing plus the 429 -> empty
classification (network mocked via monkeypatch, no real HTTP call).
"""
import pytest

import src.search.engines.marginalia as marginalia_mod
from src.search.engines.marginalia import MarginaliaEngine, _fetch_results, _parse_results


def test_parse_results_maps_fields_and_position():
    items = [
        {
            "url": "https://www.tedinski.com/2018/05/08/case-study-unix-philosophy.html",
            "title": "Deconstructing the \"Unix philosophy\"",
            "description": "I'm still working on figuring out how to organize my thoughts...",
            "quality": 3.37,
            "format": "html",
        },
        {
            "url": "https://www.ssp.sh/brain/unix-philosophy/",
            "title": "Unix Philosophy",
            "description": "Here are some examples...",
        },
    ]
    results = _parse_results(items)
    assert len(results) == 2
    assert results[0].url == "https://www.tedinski.com/2018/05/08/case-study-unix-philosophy.html"
    assert results[0].title == "Deconstructing the \"Unix philosophy\""
    assert results[0].snippet == "I'm still working on figuring out how to organize my thoughts..."
    assert results[0].engine == "marginalia"
    assert results[0].position == 1
    assert results[1].position == 2


def test_parse_results_skips_items_without_url():
    items = [
        {"url": "", "title": "no url", "description": ""},
        {"url": "https://example.com", "title": "ok", "description": ""},
    ]
    results = _parse_results(items)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_parse_results_defaults_missing_title_and_description_to_empty_string():
    items = [{"url": "https://example.com"}]
    results = _parse_results(items)
    assert len(results) == 1
    assert results[0].title == ""
    assert results[0].snippet == ""


def test_parse_results_empty_list_returns_empty_list():
    assert _parse_results([]) == []


# ---------------------------------------------------------------------------
# 429/403 rate-limit -> graceful empty (network mocked, mirrors crossref/openalex/etc. shape)
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict | None = None):
        self.status_code = status_code
        self._json_body = json_body or {}

    def json(self):
        return self._json_body

    def raise_for_status(self):
        pass


class _FakeAsyncClient:
    def __init__(self, status_code: int):
        self._status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, *a, **kw):
        return _FakeResponse(self._status_code)


@pytest.mark.asyncio
async def test_fetch_results_returns_none_on_429(monkeypatch):
    monkeypatch.setattr(marginalia_mod.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(429))
    result = await _fetch_results("some query", 10)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_results_returns_none_on_403(monkeypatch):
    monkeypatch.setattr(marginalia_mod.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(403))
    result = await _fetch_results("some query", 10)
    assert result is None


@pytest.mark.asyncio
async def test_search_returns_empty_list_on_rate_limit(monkeypatch):
    monkeypatch.setattr(marginalia_mod.httpx, "AsyncClient", lambda *a, **kw: _FakeAsyncClient(429))
    engine = MarginaliaEngine()
    results = await engine.search("some query")
    assert results == []
