"""Tests for src/search/engines/yandex.py pure result-parsing / self-link-filter logic.

No network, no browser — covers the seams factored out of the DOM-driven engine:
- _is_self_referential: yandex.com/*.yandex.* domain detection (self-links, video-carousel cards)
- _is_block_url: showcaptcha/checkcaptcha/captcha redirect detection — kept: it is also the early
  short-circuit optimization inside search_with_reason, independent of the removed verdict
- _build_results: JSON items -> SearchResult list, dropping self-referential URLs

_classify_diagnosis was removed (the guessed-verdict-removal milestone): its output was one of the
EMPTY_* sub-statuses that no longer exist — the marker/url/ready_state facts it classified are
still available directly in the diagnosis snapshot.
"""
from src.search.engines.yandex import _build_results, _is_block_url, _is_self_referential


# ---------------------------------------------------------------------------
# _is_self_referential
# ---------------------------------------------------------------------------

def test_is_self_referential_matches_yandex_domain():
    assert _is_self_referential("https://yandex.com/video/preview/123?text=q") is True


def test_is_self_referential_matches_yandex_subdomain():
    assert _is_self_referential("https://translate.yandex.com/translate?url=x") is True


def test_is_self_referential_does_not_match_lookalike_domain():
    assert _is_self_referential("https://notyandex.com/page") is False


def test_is_self_referential_does_not_match_real_external_domain():
    assert _is_self_referential("https://realpython.com/async-io-python/") is False


# ---------------------------------------------------------------------------
# _is_block_url
# ---------------------------------------------------------------------------

def test_is_block_url_detects_showcaptcha_redirect():
    assert _is_block_url("https://yandex.com/showcaptcha?cc=1&mt=abc") is True


def test_is_block_url_false_for_normal_search_url():
    assert _is_block_url("https://yandex.com/search/?text=python") is False


# ---------------------------------------------------------------------------
# _build_results
# ---------------------------------------------------------------------------

def test_build_results_maps_fields_and_position():
    items = [
        {"url": "https://realpython.com/async-io-python/", "title": "Asyncio Walkthrough", "snippet": "Explore how..."},
        {"url": "https://docs.python.org/3/library/asyncio.html", "title": "asyncio docs", "snippet": "Reference."},
    ]
    results = _build_results(items, max_results=10)
    assert len(results) == 2
    assert results[0].url == "https://realpython.com/async-io-python/"
    assert results[0].engine == "yandex"
    assert results[0].position == 1
    assert results[1].position == 2


def test_build_results_drops_yandex_self_referential_urls():
    items = [
        {"url": "https://realpython.com/async-io-python/", "title": "real result", "snippet": ""},
        {"url": "https://yandex.com/video/preview/123?text=q", "title": "video carousel card", "snippet": ""},
        {"url": "https://docs.python.org/3/library/asyncio.html", "title": "another real result", "snippet": ""},
    ]
    results = _build_results(items, max_results=10)
    urls = [r.url for r in results]
    assert "https://yandex.com/video/preview/123?text=q" not in urls
    assert len(results) == 2
    assert [r.position for r in results] == [1, 2]


def test_build_results_skips_items_without_url():
    items = [{"url": "", "title": "no url", "snippet": ""}, {"url": "https://example.com", "title": "ok", "snippet": ""}]
    results = _build_results(items, max_results=10)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_build_results_respects_max_results_cap():
    items = [{"url": f"https://example.com/{i}", "title": str(i), "snippet": ""} for i in range(20)]
    results = _build_results(items, max_results=5)
    assert len(results) == 5
    assert [r.position for r in results] == [1, 2, 3, 4, 5]
