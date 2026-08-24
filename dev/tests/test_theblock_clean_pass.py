"""Tests for the proxy_pool clean-pass helper: _run_clean_pass.

Synthetic raw HTML fixtures — no corpus, no network.
Covers: good fixture → clean file written with correct name; body-less → bodyless_urls.txt;
        raw retention (A1); stats correctness.
"""
import hashlib
import logging
from pathlib import Path

import pytest

from src.news.clean_pass import _run_clean_pass
from src.news.platforms.theblock import TheBlockPlatform


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GOOD_URL = "https://www.theblock.co/post/12345/good-article"
BODYLESS_URL = "https://www.theblock.co/post/99999/bodyless-article"


def _hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:12]


GOOD_HASH = _hash(GOOD_URL)
BODYLESS_HASH = _hash(BODYLESS_URL)

# Minimal HTML with NewsArticle JSON-LD: non-empty articleBody + datePublished
GOOD_HTML = """\
<html><head>
<script type="application/ld+json">
{"@type": "NewsArticle", "articleBody": "<p>The Block reports on crypto markets.</p>", "datePublished": "2024-03-15T10:00:00Z"}
</script>
</head><body></body></html>
"""

# Minimal HTML with NewsArticle JSON-LD: empty articleBody → body-less
BODYLESS_HTML = """\
<html><head>
<script type="application/ld+json">
{"@type": "NewsArticle", "articleBody": "", "datePublished": "2024-04-01T12:00:00Z"}
</script>
</head><body></body></html>
"""


@pytest.fixture()
def dirs(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    collection_dir = tmp_path / "collection"
    (raw_dir / f"{GOOD_HASH}.md").write_text(GOOD_HTML, encoding="utf-8")
    (raw_dir / f"{BODYLESS_HASH}.md").write_text(BODYLESS_HTML, encoding="utf-8")
    return raw_dir, collection_dir


def _entries():
    return [
        {"url": GOOD_URL, "hash": GOOD_HASH, "publication_date": ""},
        {"url": BODYLESS_URL, "hash": BODYLESS_HASH, "publication_date": ""},
    ]


_PLATFORM = TheBlockPlatform()
_LOG = logging.getLogger("test_clean_pass")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_good_article_clean_file_written(dirs):
    raw_dir, collection_dir = dirs
    stats = _run_clean_pass(_PLATFORM, _entries(), raw_dir, collection_dir, _LOG)
    expected = collection_dir / f"theblock__2024-03-15__{GOOD_HASH}.md"
    assert expected.exists(), f"expected clean file not found: {expected}"
    assert expected.read_text(encoding="utf-8").strip(), "clean file must not be empty"


def test_bodyless_no_clean_file_url_recorded(dirs):
    raw_dir, collection_dir = dirs
    _run_clean_pass(_PLATFORM, _entries(), raw_dir, collection_dir, _LOG)
    # No clean file for the body-less article
    bodyless_clean = list(collection_dir.glob(f"*{BODYLESS_HASH}*")) if collection_dir.exists() else []
    assert not bodyless_clean, f"body-less article must not produce a clean file: {bodyless_clean}"
    # URL recorded in clean/bodyless_urls.txt
    bodyless_path = raw_dir.parent / "clean" / "bodyless_urls.txt"
    assert bodyless_path.exists(), "bodyless_urls.txt must be created"
    assert BODYLESS_URL in bodyless_path.read_text(encoding="utf-8")


def test_raw_files_unchanged_after_pass(dirs):
    """A1: raw/ files are read-only — content must be identical before and after."""
    raw_dir, collection_dir = dirs
    good_before = (raw_dir / f"{GOOD_HASH}.md").read_text(encoding="utf-8")
    bodyless_before = (raw_dir / f"{BODYLESS_HASH}.md").read_text(encoding="utf-8")
    _run_clean_pass(_PLATFORM, _entries(), raw_dir, collection_dir, _LOG)
    assert (raw_dir / f"{GOOD_HASH}.md").read_text(encoding="utf-8") == good_before
    assert (raw_dir / f"{BODYLESS_HASH}.md").read_text(encoding="utf-8") == bodyless_before


def test_stats_correct(dirs):
    raw_dir, collection_dir = dirs
    stats = _run_clean_pass(_PLATFORM, _entries(), raw_dir, collection_dir, _LOG)
    assert stats == {"n_cleaned": 1, "n_bodyless": 1, "total": 2}


def test_empty_entries_returns_zero_stats(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    collection_dir = tmp_path / "collection"
    stats = _run_clean_pass(_PLATFORM, [], raw_dir, collection_dir, _LOG)
    assert stats == {"n_cleaned": 0, "n_bodyless": 0, "total": 0}
    assert not collection_dir.exists(), "collection_dir must not be created for empty entries"


def test_bodyless_urls_union_merged(dirs):
    """Second run adds new body-less URL — file must be sorted union, not overwritten."""
    raw_dir, collection_dir = dirs
    # First run: BODYLESS_URL lands in the file
    _run_clean_pass(_PLATFORM, _entries(), raw_dir, collection_dir, _LOG)

    # Second run with a new body-less entry
    extra_url = "https://www.theblock.co/post/11111/another-bodyless"
    extra_hash = _hash(extra_url)
    (raw_dir / f"{extra_hash}.md").write_text(BODYLESS_HTML, encoding="utf-8")
    extra_entries = [{"url": extra_url, "hash": extra_hash, "publication_date": ""}]
    _run_clean_pass(_PLATFORM, extra_entries, raw_dir, collection_dir, _LOG)

    bodyless_path = raw_dir.parent / "clean" / "bodyless_urls.txt"
    lines = [l for l in bodyless_path.read_text(encoding="utf-8").splitlines() if l]
    assert BODYLESS_URL in lines
    assert extra_url in lines
    assert lines == sorted(lines), "bodyless_urls.txt must be sorted"
