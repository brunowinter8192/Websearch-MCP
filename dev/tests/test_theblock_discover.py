"""Tests for theblock discover.py range-mode helpers.

Synthetic sub-sitemap URL list — no network calls.
Covers: _subs_in_range, _sub_by_index (regression), and the discover() dispatch
        error paths for sub:A-B.
"""
import pytest

from src.news.platforms.theblock.discover import _subs_in_range, _sub_by_index

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_urls(indices: list[int]) -> list[str]:
    """Return synthetic post_type_post sub-sitemap URLs for the given indices."""
    return [
        f"https://www.theblock.co/sitemap_tbco_post_type_post_{i}.xml"
        for i in indices
    ]


# All 27 subs used in scope (0-26 → indices 0..26; prompt example uses 24-27
# with "27 subs" including 0-26, so we use 0-26 as the full realistic set).
_ALL_URLS = _make_urls(list(range(27)))  # indices 0..26


# ---------------------------------------------------------------------------
# _subs_in_range — happy path
# ---------------------------------------------------------------------------

def test_range_selects_correct_subs():
    result = _subs_in_range(_ALL_URLS, 24, 26)
    # Extract trailing numbers from result
    import re
    nums = [int(re.search(r"_(\d+)\.xml$", u).group(1)) for u in result]
    assert sorted(nums) == [24, 25, 26]


def test_range_includes_both_endpoints():
    result = _subs_in_range(_ALL_URLS, 0, 2)
    import re
    nums = sorted(int(re.search(r"_(\d+)\.xml$", u).group(1)) for u in result)
    assert nums == [0, 1, 2]


def test_range_single_element_via_equal_bounds():
    """sub:5-5 should select exactly one sub."""
    result = _subs_in_range(_ALL_URLS, 5, 5)
    assert len(result) == 1
    assert "_5.xml" in result[0]


def test_range_returns_descending_order():
    """Newest-first — consistent with delta."""
    result = _subs_in_range(_ALL_URLS, 10, 13)
    import re
    nums = [int(re.search(r"_(\d+)\.xml$", u).group(1)) for u in result]
    assert nums == [13, 12, 11, 10]


def test_range_full_set():
    """sub:0-26 should return all 27 subs descending."""
    result = _subs_in_range(_ALL_URLS, 0, 26)
    assert len(result) == 27
    import re
    nums = [int(re.search(r"_(\d+)\.xml$", u).group(1)) for u in result]
    assert nums == list(range(26, -1, -1))


# ---------------------------------------------------------------------------
# _subs_in_range — error paths
# ---------------------------------------------------------------------------

def test_range_no_match_raises():
    """Range outside all existing subs → RuntimeError."""
    with pytest.raises(RuntimeError, match="matched no post_type_post"):
        _subs_in_range(_ALL_URLS, 50, 60)


def test_range_partial_overlap_selects_only_matching():
    """Range extends beyond existing subs — only existing ones returned."""
    result = _subs_in_range(_ALL_URLS, 24, 99)
    import re
    nums = sorted(int(re.search(r"_(\d+)\.xml$", u).group(1)) for u in result)
    # Only 24, 25, 26 exist in _ALL_URLS
    assert nums == [24, 25, 26]


# ---------------------------------------------------------------------------
# _sub_by_index — regression (single sub:N unchanged)
# ---------------------------------------------------------------------------

def test_single_sub_by_index():
    result = _sub_by_index(_ALL_URLS, 26)
    assert "_26.xml" in result


def test_single_sub_by_index_not_found():
    with pytest.raises(RuntimeError, match="sub:99 not found"):
        _sub_by_index(_ALL_URLS, 99)


def test_single_sub_by_index_zero():
    result = _sub_by_index(_ALL_URLS, 0)
    assert "_0.xml" in result


# ---------------------------------------------------------------------------
# discover() dispatch — A>B and non-int validation (via RuntimeError check)
# ---------------------------------------------------------------------------

def test_range_a_greater_than_b_raises():
    """sub:27-24 (A > B) must raise before any URL lookup."""
    import asyncio
    from unittest.mock import patch, AsyncMock

    # Patch network so this never touches the wire
    fake_index = (
        b"<?xml version='1.0'?><sitemapindex>"
        + b"".join(
            b"<sitemap><loc>https://www.theblock.co/sitemap_tbco_post_type_post_"
            + str(i).encode()
            + b".xml</loc></sitemap>"
            for i in range(27)
        )
        + b"</sitemapindex>"
    )

    with patch("src.news.platforms.theblock.discover._fetch_xml", return_value=fake_index):
        with pytest.raises(RuntimeError, match=r"A \(27\) must be ≤ B \(24\)"):
            asyncio.run(__import__("src.news.platforms.theblock.discover", fromlist=["discover"]).discover("sub:27-24"))


def test_range_non_int_raises():
    """sub:x-y (non-integer parts) must raise."""
    import asyncio
    from unittest.mock import patch

    fake_index = (
        b"<?xml version='1.0'?><sitemapindex>"
        b"<sitemap><loc>https://www.theblock.co/sitemap_tbco_post_type_post_1.xml</loc></sitemap>"
        b"</sitemapindex>"
    )

    with patch("src.news.platforms.theblock.discover._fetch_xml", return_value=fake_index):
        with pytest.raises(RuntimeError, match="expected two integers"):
            asyncio.run(__import__("src.news.platforms.theblock.discover", fromlist=["discover"]).discover("sub:x-y"))


def test_range_no_existing_sub_in_range_raises():
    """A valid A-B range but no existing sub falls in it → RuntimeError."""
    import asyncio
    from unittest.mock import patch

    fake_index = (
        b"<?xml version='1.0'?><sitemapindex>"
        + b"".join(
            b"<sitemap><loc>https://www.theblock.co/sitemap_tbco_post_type_post_"
            + str(i).encode()
            + b".xml</loc></sitemap>"
            for i in range(5)  # only subs 0..4 exist
        )
        + b"</sitemapindex>"
    )

    with patch("src.news.platforms.theblock.discover._fetch_xml", return_value=fake_index):
        with pytest.raises(RuntimeError, match="matched no post_type_post"):
            asyncio.run(__import__("src.news.platforms.theblock.discover", fromlist=["discover"]).discover("sub:10-20"))
