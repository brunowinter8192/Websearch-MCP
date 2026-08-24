"""Tests for src/search/engines/bing.py pure result-parsing / URL-unwrap / diagnosis logic.

No network, no browser — covers the three seams factored out of the DOM-driven engine:
- _clean_url: bing.com/ck/a?...&u=<prefixed-base64> tracking redirect -> real destination URL
- _build_results: JSON items (as if already parsed from the page) -> SearchResult list
- _classify_diagnosis: block / race / no-container classification
"""
from src.search import status as S
from src.search.engines.bing import _build_results, _classify_diagnosis, _clean_url


# ---------------------------------------------------------------------------
# _clean_url
# ---------------------------------------------------------------------------

def test_clean_url_unwraps_ck_a_redirect_to_real_destination():
    # Real sample captured live in dev/search_pipeline/28_bing_probe.py exploration —
    # u=a1<base64url(https://docs.python.org/3/library/asyncio.html)>
    wrapped = (
        "https://www.bing.com/ck/a?!&&p=3433f59b1e520073dfadefacf80bd715cd2b9ad5a31edea67e9ae0212fa91585"
        "&ptn=3&ver=2&hsh=4&fclid=2775937b-2388-6e7b-1e71-844822246f08"
        "&u=a1aHR0cHM6Ly9kb2NzLnB5dGhvbi5vcmcvMy9saWJyYXJ5L2FzeW5jaW8uaHRtbA&ntb=1"
    )
    assert _clean_url(wrapped) == "https://docs.python.org/3/library/asyncio.html"


def test_clean_url_passes_through_direct_url_with_no_u_param():
    assert _clean_url("https://example.com/page") == "https://example.com/page"


def test_clean_url_empty_href_returns_empty():
    assert _clean_url("") == ""


def test_clean_url_falls_back_to_raw_href_when_decode_raises(monkeypatch):
    import src.search.engines.bing as bing_mod

    def _raise(*a, **kw):
        raise ValueError("simulated decode failure")

    monkeypatch.setattr(bing_mod.base64, "urlsafe_b64decode", _raise)
    wrapped = "https://www.bing.com/ck/a?u=a1aHR0cHM6Ly9leGFtcGxlLmNvbQ&ntb=1"
    assert _clean_url(wrapped) == wrapped


# ---------------------------------------------------------------------------
# _build_results
# ---------------------------------------------------------------------------

def test_build_results_unwraps_url_and_maps_fields():
    items = [{
        "url": "https://www.bing.com/ck/a?u=a1aHR0cHM6Ly9yZWFscHl0aG9uLmNvbS9hc3luYy1pby1weXRob24v&ntb=1",
        "title": "Python's asyncio: A Hands-On Walkthrough",
        "snippet": "Explore how...",
    }]
    results = _build_results(items, max_results=10)
    assert len(results) == 1
    assert results[0].url == "https://realpython.com/async-io-python/"
    assert results[0].title == "Python's asyncio: A Hands-On Walkthrough"
    assert results[0].engine == "bing"
    assert results[0].position == 1


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


# ---------------------------------------------------------------------------
# _classify_diagnosis
# ---------------------------------------------------------------------------

def test_classify_diagnosis_marker_is_block():
    assert _classify_diagnosis("captcha", "complete") == S.EMPTY_BLOCK


def test_classify_diagnosis_page_still_loading_is_concurrent_race():
    assert _classify_diagnosis(None, "loading") == S.EMPTY_CONCURRENT_RACE


def test_classify_diagnosis_clean_page_no_results_is_no_container():
    assert _classify_diagnosis(None, "complete") == S.EMPTY_NO_CONTAINER
