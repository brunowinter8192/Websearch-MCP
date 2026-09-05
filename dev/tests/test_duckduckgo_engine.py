"""Tests for src/search/engines/duckduckgo.py's pure diagnosis-classification logic.

No network, no browser — DDG's block signal is the structural presence of the
form#challenge-form element (an element count), never a text marker, so classification takes
a bool (challenge_form) rather than a marker string.
"""
from src.search import status as S
from src.search.engines.duckduckgo import _classify_diagnosis


def test_classify_diagnosis_challenge_form_present_is_block():
    assert _classify_diagnosis(True, "complete") == S.EMPTY_BLOCK


def test_classify_diagnosis_page_still_loading_is_concurrent_race():
    assert _classify_diagnosis(False, "loading") == S.EMPTY_CONCURRENT_RACE


def test_classify_diagnosis_clean_page_no_results_is_no_container():
    assert _classify_diagnosis(False, "complete") == S.EMPTY_NO_CONTAINER
