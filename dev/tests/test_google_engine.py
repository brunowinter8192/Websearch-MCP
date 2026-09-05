"""Tests for src/search/engines/google.py's pure diagnosis-classification logic.

No network, no browser — Google's block/consent signal is a URL path, never a text marker
(unlike bing/brave/yandex/startpage/mojeek), so there is no _match_marker seam here.
"""
from src.search import status as S
from src.search.engines.google import _classify_diagnosis


def test_classify_diagnosis_sorry_path_is_block():
    assert _classify_diagnosis("https://www.google.com/sorry/index?continue=x", "complete") == S.EMPTY_BLOCK


def test_classify_diagnosis_consent_domain_is_consent():
    assert _classify_diagnosis("https://consent.google.com/ml?continue=x", "complete") == S.EMPTY_CONSENT


def test_classify_diagnosis_sorry_wins_over_consent_domain():
    assert _classify_diagnosis("https://consent.google.com/sorry/index", "complete") == S.EMPTY_BLOCK


def test_classify_diagnosis_page_still_loading_is_concurrent_race():
    assert _classify_diagnosis("https://www.google.com/search?q=x", "loading") == S.EMPTY_CONCURRENT_RACE


def test_classify_diagnosis_clean_page_no_results_is_no_container():
    assert _classify_diagnosis("https://www.google.com/search?q=x", "complete") == S.EMPTY_NO_CONTAINER
