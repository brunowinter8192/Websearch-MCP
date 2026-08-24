"""Tests for src/search/engines/startpage.py pure result-parsing / diagnosis logic.

No network, no browser — covers the two seams factored out of the DOM-driven engine:
- _build_results: JSON items (as if already parsed from the page) -> SearchResult list
- _classify_diagnosis: block/race/no-container classification from a diagnosis snapshot
"""
from src.search import status as S
from src.search.engines.startpage import _build_results, _classify_diagnosis


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
    assert results[0].title == "Asyncio Walkthrough"
    assert results[0].snippet == "Explore how..."
    assert results[0].engine == "startpage"
    assert results[0].position == 1
    assert results[1].position == 2


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

def test_classify_diagnosis_block_marker_wins():
    assert _classify_diagnosis("captcha", False, "https://www.startpage.com/sp/search", "complete") == S.EMPTY_BLOCK


def test_classify_diagnosis_iframe_challenge_is_block():
    assert _classify_diagnosis(None, True, "https://www.startpage.com/sp/search", "complete") == S.EMPTY_BLOCK


def test_classify_diagnosis_page_still_loading_is_concurrent_race():
    assert _classify_diagnosis(None, False, "https://www.startpage.com/sp/search", "loading") == S.EMPTY_CONCURRENT_RACE


def test_classify_diagnosis_clean_page_no_results_is_no_container():
    assert _classify_diagnosis(None, False, "https://www.startpage.com/sp/search", "complete") == S.EMPTY_NO_CONTAINER
