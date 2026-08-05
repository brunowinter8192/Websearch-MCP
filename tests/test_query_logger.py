"""Tests for query_logger + per-engine stats capture in search_web_workflow.

Runs without network: mock engines return fixed results immediately.
Uses tmp_path to redirect LOG_PATH so production log is never touched.
"""
import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_engine(name: str, results: list, delay: float = 0.0):
    """Mock engine with .name and async .search()."""
    eng = MagicMock()
    eng.name = name

    async def _search(query, language, max_results):
        if delay:
            await asyncio.sleep(delay)
        return results

    eng.search = _search
    return eng


def _fake_result(url: str = "https://example.com", title: str = "T", snippet: str = "S", engine: str = "mock"):
    from src.search.result import SearchResult
    return SearchResult(url=url, title=title, snippet=snippet, engine=engine, position=1)


# ---------------------------------------------------------------------------
# test_log_query_writes_jsonl
# ---------------------------------------------------------------------------

def test_log_query_writes_jsonl(tmp_path):
    """log_query appends exactly one JSONL line with the provided record."""
    log_file = tmp_path / "query_log.jsonl"

    import src.search.query_logger as ql
    with patch.object(ql, "LOG_PATH", log_file):
        ql.log_query({"ts": "2026-01-01T00:00:00.000Z", "query": "hello", "total_wall_ms": 42})

    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["query"] == "hello"
    assert record["total_wall_ms"] == 42


def test_log_query_appends(tmp_path):
    """Two log_query calls produce two JSONL lines."""
    log_file = tmp_path / "query_log.jsonl"

    import src.search.query_logger as ql
    with patch.object(ql, "LOG_PATH", log_file):
        ql.log_query({"query": "a"})
        ql.log_query({"query": "b"})

    lines = log_file.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["query"] == "a"
    assert json.loads(lines[1])["query"] == "b"


def test_log_query_fail_soft(tmp_path, caplog):
    """log_query does NOT raise when write fails — logs a warning instead."""
    import src.search.query_logger as ql

    # Create a FILE where the parent dir should be, so mkdir fails
    blocker = tmp_path / "blocked"
    blocker.write_text("i am a file")
    bad_path = blocker / "nested" / "query_log.jsonl"

    with patch.object(ql, "LOG_PATH", bad_path):
        with caplog.at_level(logging.WARNING, logger="src.search.query_logger"):
            ql.log_query({"query": "should not crash"})

    assert any("query_log write failed" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# test_engine_with_timing (unit tests, no workflow)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_engine_with_timing_ok():
    """_engine_with_timing returns (results, rate_wait_ms, search_ms, OK, None) on success."""
    from src.search.search_web import _engine_with_timing

    r = _fake_result("https://x.com", engine="fast")
    fast = _make_mock_engine("fast", [r])

    results, rate_wait_ms, search_ms, status, drop_reason = await _engine_with_timing(
        fast, "query", "en", 10, timeout=3.6
    )

    assert len(results) == 1
    assert status == "OK"
    assert drop_reason is None
    assert isinstance(rate_wait_ms, int) and rate_wait_ms >= 0
    assert isinstance(search_ms, int) and search_ms >= 0


@pytest.mark.asyncio
async def test_engine_with_timing_timeout():
    """_engine_with_timing returns TIMEOUT + drop_reason when engine exceeds watchdog."""
    from src.search.search_web import _engine_with_timing

    slow = _make_mock_engine("slow_eng", [], delay=5.0)

    results, rate_wait_ms, search_ms, status, drop_reason = await _engine_with_timing(
        slow, "query", "en", 10, timeout=0.05
    )

    assert results == []
    assert status == "TIMEOUT"
    assert drop_reason is not None and "watchdog" in drop_reason
    assert isinstance(rate_wait_ms, int)
    assert isinstance(search_ms, int)


@pytest.mark.asyncio
async def test_engine_with_timing_empty():
    """_engine_with_timing returns EMPTY status when engine returns []."""
    from src.search.search_web import _engine_with_timing

    empty = _make_mock_engine("empty_eng", [])

    results, _, _, status, drop_reason = await _engine_with_timing(
        empty, "query", "en", 10, timeout=3.6
    )

    assert results == []
    assert status == "EMPTY"
    assert drop_reason is None


# ---------------------------------------------------------------------------
# test_search_web_workflow_writes_log (integration, no network)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_web_workflow_writes_log(tmp_path):
    """search_web_workflow writes exactly one JSONL record with correct fields."""
    import src.search.query_logger as ql
    from src.search import search_web
    log_file = tmp_path / "query_log.jsonl"

    result_a = _fake_result("https://a.com", engine="google")
    result_b = _fake_result("https://b.com", engine="duckduckgo")

    mock_engines = {
        "google": _make_mock_engine("google", [result_a]),
        "duckduckgo": _make_mock_engine("duckduckgo", [result_b]),
    }

    async def _mock_preview(results, top_n=20):
        stats = {"urls_attempted": len(results[:top_n]), "urls_succeeded": 0, "url_timeouts": 0, "total_ms": 1}
        return results[:top_n], stats

    with (
        patch.object(search_web, "ENGINES", mock_engines),
        patch.object(search_web, "fetch_previews", _mock_preview),
        patch.object(search_web, "cache_write"),
        patch.object(search_web, "cache_key", return_value="testkey"),
        patch.object(search_web, "_merge_and_rank", return_value=([result_a, result_b], {"general": 1, "academic": 0, "qa": 1})),
        patch.object(ql, "LOG_PATH", log_file),
    ):
        await search_web.search_web_workflow("test query", language="en")

    lines = log_file.read_text().splitlines()
    assert len(lines) == 1, f"Expected 1 log line, got {len(lines)}: {lines}"

    rec = json.loads(lines[0])
    assert rec["query"] == "test query"
    assert rec["language"] == "en"
    assert "ts" in rec and rec["ts"].endswith("Z")
    assert rec["total_wall_ms"] >= 0
    assert set(rec["engines_requested"]) == {"google", "duckduckgo"}
    assert "google" in rec["engines"]
    assert "duckduckgo" in rec["engines"]

    for eng_name, stats in rec["engines"].items():
        assert "rate_wait_ms" in stats, f"{eng_name} missing rate_wait_ms"
        assert "search_ms" in stats, f"{eng_name} missing search_ms"
        assert stats["status"] in ("OK", "EMPTY", "TIMEOUT", "ERROR"), f"{eng_name} bad status"
        assert "result_count" in stats, f"{eng_name} missing result_count"
        assert "drop_reason" in stats, f"{eng_name} missing drop_reason"

    pv = rec["preview"]
    assert "urls_attempted" in pv
    assert "urls_succeeded" in pv
    assert "url_timeouts" in pv
    assert "total_ms" in pv
    assert rec["bottleneck_engine"] in ("google", "duckduckgo")


# ---------------------------------------------------------------------------
# record_type = "drilldown" — schema + search_key correlation
# ---------------------------------------------------------------------------

def test_log_query_accepts_drilldown_record_shape(tmp_path, monkeypatch):
    """log_query writes a well-shaped drilldown record — the generic writer, exercised with the
    new record_type's fields (mirrors test_log_query_writes_jsonl's pattern for engine_run/
    workflow_summary; uses the real WEBSEARCH_QUERY_LOG_PATH env var, not the ql.LOG_PATH
    attribute the pre-existing broken tests above reference — that attribute does not exist on
    the real module, see this file's process-docs entry for that finding)."""
    import src.search.query_logger as ql
    log_file = tmp_path / "query_log.jsonl"
    monkeypatch.setenv("WEBSEARCH_QUERY_LOG_PATH", str(log_file))

    ql.log_query({
        "record_type": "drilldown", "ts": "2026-08-05T00:00:00.000Z",
        "query": "fritzbox 7510", "language": "en", "mode": None, "engine": "google",
        "search_key": "abc123def456", "cache_status": "hit", "engine_in_pools": True,
        "result_count": 2, "urls": ["https://a.com", "https://b.com"],
    })

    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["record_type"] == "drilldown"
    assert rec["search_key"] == "abc123def456"
    assert rec["urls"] == ["https://a.com", "https://b.com"]


def _make_mock_engine_with_reason(name: str, results: list):
    """Mock engine matching the CURRENT _engine_with_timing interface
    (engine.search_with_reason(query, language, max_results) -> (results, empty_reason)) — NOT
    the shared _make_mock_engine() above, which sets .search (not .search_with_reason) and is
    stale against this interface; see this file's process-docs entry for that finding. Deliberately
    a separate, local, correct helper rather than fixing the shared one (out of scope, pre-existing)."""
    eng = MagicMock()
    eng.name = name

    async def _search_with_reason(query, language, max_results):
        return results, None

    eng.search_with_reason = _search_with_reason
    return eng


@pytest.mark.asyncio
async def test_search_web_workflow_writes_search_key_matching_cache_key(tmp_path, monkeypatch):
    """workflow_summary's search_key equals the real cache.cache_key(...) output for the same
    call — the exact join value a drilldown record must reproduce to correlate back to this
    search. Real engine fanout mocked (no network); cache_write mocked (no real cache-dir write);
    cache_key itself is NOT mocked — it must be the real function for this assertion to mean
    anything."""
    from src.search import search_web
    from src.search.cache import cache_key as real_cache_key
    log_file = tmp_path / "query_log.jsonl"
    monkeypatch.setenv("WEBSEARCH_QUERY_LOG_PATH", str(log_file))

    result_a = _fake_result("https://a.com", engine="google")
    mock_engines = {"google": _make_mock_engine_with_reason("google", [result_a])}

    with (
        patch.object(search_web, "ENGINES", mock_engines),
        patch.object(search_web, "_DEFAULT_ENGINES", {"google"}),
        patch.object(search_web, "cache_write"),
    ):
        await search_web.search_web_workflow("test query", language="en")

    lines = log_file.read_text().splitlines()
    records = [json.loads(l) for l in lines]
    summary_records = [r for r in records if r["record_type"] == "workflow_summary"]
    assert len(summary_records) == 1
    rec = summary_records[0]
    expected_key = real_cache_key("test query", "en", None, None, modifier_id=None)
    assert rec["search_key"] == expected_key


# ---------------------------------------------------------------------------
# cli.py's _log_drilldown — real function, isolated subprocess (importing cli.py in-process
# reconfigures the root logger via logging.basicConfig and registers an atexit chrome-kill hook;
# side effects that must not bleed into the rest of this test suite)
# ---------------------------------------------------------------------------

def test_log_drilldown_all_cache_status_and_pool_combinations(tmp_path):
    """Real cli.py._log_drilldown, exercised for the sub-cases that matter: a hit with the engine
    present (real urls, result_count matches); a hit with the engine absent from pools
    (engine_in_pools=False, urls empty — distinguishing 'excluded upstream' from 'zero results');
    and a cache-miss-then-search-failure (cache_status names the failure explicitly rather than
    looking like an ordinary hit)."""
    import os
    import subprocess
    import sys

    log_file = tmp_path / "query_log.jsonl"
    repo_root = Path(__file__).parent.parent
    script = f"""
import sys
sys.path.insert(0, {str(repo_root)!r})
import cli
cli._log_drilldown("fritzbox 7510", "en", None, "google", "searchkey123", "hit", True,
                    ["https://a.com", "https://b.com"])
cli._log_drilldown("fritzbox 7510", "en", None, "obscure_engine", "searchkey123", "hit", False, [])
cli._log_drilldown("never searched", "en", None, "google", "searchkey999",
                    "miss_then_search_failed", False, [])
"""
    env = {**os.environ, "WEBSEARCH_QUERY_LOG_PATH": str(log_file)}
    result = subprocess.run([sys.executable, "-c", script], cwd=repo_root, env=env,
                             capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"stderr: {result.stderr}"

    lines = log_file.read_text().splitlines()
    assert len(lines) == 3
    recs = [json.loads(l) for l in lines]

    hit_with_urls = recs[0]
    assert hit_with_urls["cache_status"] == "hit"
    assert hit_with_urls["engine_in_pools"] is True
    assert hit_with_urls["result_count"] == 2
    assert hit_with_urls["urls"] == ["https://a.com", "https://b.com"]
    assert hit_with_urls["search_key"] == "searchkey123"

    hit_engine_absent = recs[1]
    assert hit_engine_absent["engine_in_pools"] is False
    assert hit_engine_absent["result_count"] == 0
    assert hit_engine_absent["urls"] == []

    miss_failed = recs[2]
    assert miss_failed["cache_status"] == "miss_then_search_failed"
    assert miss_failed["engine_in_pools"] is False
    assert miss_failed["urls"] == []
