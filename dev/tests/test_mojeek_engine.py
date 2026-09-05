"""Tests for src/search/engines/mojeek.py's pure marker-matching logic.

No network, no browser — _match_marker (case-insensitive block-keyword scan against the page
title) is the one seam factored out of the DOM-driven engine. _classify_diagnosis was removed
(the guessed-verdict-removal milestone): its output was one of the EMPTY_* sub-statuses that no
longer exist — the marker fact it derived from is still available in the diagnosis snapshot's
`marker` field, populated by _match_marker directly.
"""
from src.search.engines.mojeek import _match_marker


def test_match_marker_detects_captcha_keyword_case_insensitive():
    assert _match_marker("CAPTCHA Challenge") == "captcha"


def test_match_marker_detects_access_denied():
    assert _match_marker("403 - Access Denied") == "access denied"


def test_match_marker_returns_none_for_clean_title():
    assert _match_marker("python asyncio - Mojeek Search") is None
