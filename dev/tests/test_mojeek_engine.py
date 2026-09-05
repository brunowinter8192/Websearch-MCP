"""Tests for src/search/engines/mojeek.py's pure marker-matching / diagnosis-classification logic.

No network, no browser — covers the two seams factored out of the DOM-driven engine:
- _match_marker: case-insensitive block-keyword scan against the page title
- _classify_diagnosis: block / race / no-container classification from a diagnosis snapshot
"""
from src.search import status as S
from src.search.engines.mojeek import _classify_diagnosis, _match_marker


# ---------------------------------------------------------------------------
# _match_marker
# ---------------------------------------------------------------------------

def test_match_marker_detects_captcha_keyword_case_insensitive():
    assert _match_marker("CAPTCHA Challenge") == "captcha"


def test_match_marker_detects_access_denied():
    assert _match_marker("403 - Access Denied") == "access denied"


def test_match_marker_returns_none_for_clean_title():
    assert _match_marker("python asyncio - Mojeek Search") is None


# ---------------------------------------------------------------------------
# _classify_diagnosis
# ---------------------------------------------------------------------------

def test_classify_diagnosis_marker_is_block():
    assert _classify_diagnosis("captcha", "complete") == S.EMPTY_BLOCK


def test_classify_diagnosis_page_still_loading_is_concurrent_race():
    assert _classify_diagnosis(None, "loading") == S.EMPTY_CONCURRENT_RACE


def test_classify_diagnosis_clean_page_no_results_is_no_container():
    assert _classify_diagnosis(None, "complete") == S.EMPTY_NO_CONTAINER
