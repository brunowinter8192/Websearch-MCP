"""Tests for src/search/engines/mojeek.py's pure marker-matching logic and _wait_for_results'
deadline behavior.

No real browser/CDP — a stub tab exposing only execute_script (returning the CDP-shaped dict
_extract_value expects) drives _wait_for_results directly. _match_marker (case-insensitive
block-keyword scan against the page title) is the one pure seam factored out of the DOM-driven
engine. _classify_diagnosis was removed (the guessed-verdict-removal milestone): its output was
one of the EMPTY_* sub-statuses that no longer exist — the marker fact it derived from is still
available in the diagnosis snapshot's `marker` field, populated by _match_marker directly.
"""
import time

import pytest

from src.search.engines.mojeek import _match_marker, _wait_for_results


class _StubTab:
    """Fake tab exposing only execute_script — one queued container-count per call, the last
    value repeating once the queue is exhausted. No browser, no network, no CDP."""

    def __init__(self, counts: list[int]):
        self._counts = list(counts)
        self._last = 0

    async def execute_script(self, script: str) -> dict:
        if self._counts:
            self._last = self._counts.pop(0)
        return {"result": {"result": {"value": self._last}}}


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
# _wait_for_results
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wait_for_results_returns_true_as_soon_as_containers_appear():
    """Deadline is generous (5s); containers appear on the third poll — proves the function
    returns the instant they do, not once the deadline is spent (the search_ms honesty guarantee)."""
    tab = _StubTab([0, 0, 3])
    deadline = time.monotonic() + 5.0
    assert await _wait_for_results(tab, deadline) is True


@pytest.mark.asyncio
async def test_wait_for_results_returns_false_once_deadline_passes_without_containers():
    """Containers never appear; a short deadline proves the function gives up exactly when the
    deadline is spent, not before and not by waiting indefinitely."""
    tab = _StubTab([0])
    deadline = time.monotonic() + 0.05
    assert await _wait_for_results(tab, deadline) is False
