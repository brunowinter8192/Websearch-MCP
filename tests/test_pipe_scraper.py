"""Tests for pipe_scraper's per-URL JSONL log (pipe_scrape_logger.py) and the config stamp
it carries.

Runs without a browser: _scrape_all's AsyncWebCrawler is patched with a fake crawler returning
synthetic results, isolating the logging path from the real network/browser call.
"""
import json
from datetime import datetime, timezone

import pytest

from src.crawler import pipe_scraper
from src.crawler.pipe_scrape_logger import log_pipe_scrape


# log_janitor prunes any record whose "ts" falls outside the 14-day retention window (or is
# unparseable) on every write — records here must carry a real, current, ISO-parseable ts.
def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------------------
# _extract_pipe_config_stamp reads real objects, not re-declared literals
# ---------------------------------------------------------------------------

def test_extract_pipe_config_stamp_reads_real_objects():
    """The config stamp reflects the actual constructed BrowserConfig/CrawlerRunConfig values,
    not hardcoded copies — changing an object's value changes the stamp."""
    browser_cfg = pipe_scraper.BrowserConfig(headless=True, verbose=False, enable_stealth=True)
    run_cfg = pipe_scraper.CrawlerRunConfig(
        cache_mode=pipe_scraper.CacheMode.BYPASS,
        wait_until="networkidle",
        delay_before_return_html=1.25,
        page_timeout=9999,
    )
    stamp = pipe_scraper._extract_pipe_config_stamp(browser_cfg, run_cfg, download_delay=2.0,
                                                       concurrency_per_domain=3)
    assert stamp["enable_stealth"] is True
    assert stamp["wait_until"] == "networkidle"
    assert stamp["page_timeout_ms"] == 9999
    assert stamp["delay_before_return_html_s"] == 1.25
    assert stamp["cache_mode"] == "bypass"
    assert stamp["download_delay_s"] == 2.0
    assert stamp["concurrency_per_domain"] == 3
    assert stamp["empty_threshold_bytes"] == pipe_scraper.EMPTY_THRESHOLD_BYTES


def test_extract_pipe_config_stamp_reads_anti_bot_fields_off_real_objects():
    """simulate_user/override_navigator/magic/remove_consent_popups are read off the real
    CrawlerRunConfig, not re-declared — changing the object changes the stamp."""
    browser_cfg = pipe_scraper.BrowserConfig(headless=True, verbose=False)
    run_cfg = pipe_scraper.CrawlerRunConfig(
        simulate_user=True, override_navigator=True, magic=False, remove_consent_popups=True,
    )
    stamp = pipe_scraper._extract_pipe_config_stamp(browser_cfg, run_cfg, download_delay=1.0,
                                                       concurrency_per_domain=8)
    assert stamp["simulate_user"] is True
    assert stamp["override_navigator"] is True
    assert stamp["magic"] is False
    assert stamp["remove_consent_popups"] is True


# ---------------------------------------------------------------------------
# _build_configs: the fixed anti-bot posture this milestone sets
# ---------------------------------------------------------------------------

def test_build_configs_sets_fixed_anti_bot_posture():
    """_build_configs's real BrowserConfig/CrawlerRunConfig carry the milestone's exact
    calibration: stealth + simulate_user + override_navigator on, magic explicitly off,
    consent popups dismissed, pacing/timeout values untouched."""
    browser_cfg, run_cfg = pipe_scraper._build_configs()
    assert browser_cfg.enable_stealth is True
    assert run_cfg.simulate_user is True
    assert run_cfg.override_navigator is True
    assert run_cfg.magic is False
    assert run_cfg.remove_consent_popups is True
    # Unchanged pacing/timeout values — no extraction-side settings added
    assert run_cfg.page_timeout == pipe_scraper.PAGE_TIMEOUT_MS
    assert run_cfg.delay_before_return_html == pipe_scraper.DELAY_BEFORE_RETURN_HTML
    assert run_cfg.markdown_generator.content_filter is None


@pytest.mark.asyncio
async def test_build_configs_produces_live_stealth_adapter():
    """Wiring test, not a dict comparison: constructs the REAL crawl4ai
    AsyncPlaywrightCrawlerStrategy from _build_configs's real BrowserConfig and asserts against
    crawl4ai's own BrowserManager/StealthAdapter state. No network — __init__ only builds state,
    never launches a browser. This is what a flag-only check (`browser_cfg.enable_stealth is
    True`) would NOT catch: StealthAdapter._check_stealth_availability swallows an ImportError
    and silently degrades `apply_stealth` to a no-op with no error raised anywhere (exactly what
    happened on crawl4ai 0.8.6 + playwright-stealth 2.0.2, see
    process-docs/scrape_pipeline/crawl4ai_stealth_stack_2026-05-31.md) — a dict check would still
    pass in that broken state, this test would not."""
    from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
    from playwright_stealth import Stealth

    browser_cfg, _ = pipe_scraper._build_configs()
    strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_cfg)

    # use_undetected resolves False (default PlaywrightAdapter, pipe_scraper passes no adapter) —
    # the precondition browser_manager.py requires to build the stealth adapter at all
    assert strategy.browser_manager.use_undetected is False
    assert strategy.browser_manager._stealth_adapter is not None
    assert strategy.browser_manager._stealth_adapter._stealth_available is True
    assert isinstance(strategy.browser_manager._stealth_adapter._stealth, Stealth)


def test_extract_pipe_config_stamp_carries_empty_threshold_off_the_constant():
    """empty_threshold_bytes is read off the module constant, not a re-declared literal."""
    browser_cfg = pipe_scraper.BrowserConfig(headless=True, verbose=False)
    run_cfg = pipe_scraper.CrawlerRunConfig()
    stamp = pipe_scraper._extract_pipe_config_stamp(browser_cfg, run_cfg, download_delay=1.0,
                                                       concurrency_per_domain=8)
    assert stamp["empty_threshold_bytes"] == pipe_scraper.EMPTY_THRESHOLD_BYTES


# ---------------------------------------------------------------------------
# log_pipe_scrape: fail-soft + real write
# ---------------------------------------------------------------------------

def test_log_pipe_scrape_writes_jsonl_record(tmp_path, monkeypatch):
    """A record appended via log_pipe_scrape is a valid JSONL line with the expected keys."""
    log_file = tmp_path / "pipe_scrape_log.jsonl"
    monkeypatch.setenv("WEBSEARCH_PIPE_SCRAPE_LOG_PATH", str(log_file))

    log_pipe_scrape({"ts": _now_ts(), "run_id": "abc123", "url": "https://x.test",
                      "domain": "x.test", "outcome": "ok", "http_status": 200, "bytes": 500,
                      "wall_ms": 100, "config_hash": "deadbeef00", "config": {"headless": True}})

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["run_id"] == "abc123"
    assert record["outcome"] == "ok"


def test_log_pipe_scrape_appends(tmp_path, monkeypatch):
    """Successive calls append, not overwrite."""
    log_file = tmp_path / "pipe_scrape_log.jsonl"
    monkeypatch.setenv("WEBSEARCH_PIPE_SCRAPE_LOG_PATH", str(log_file))

    for i in range(3):
        log_pipe_scrape({"ts": _now_ts(), "run_id": "r", "url": f"https://x.test/{i}", "domain": "x.test",
                          "outcome": "ok", "http_status": 200, "bytes": 1, "wall_ms": 1,
                          "config_hash": "h", "config": {}})

    assert len(log_file.read_text(encoding="utf-8").splitlines()) == 3


def test_log_pipe_scrape_fail_soft(monkeypatch, caplog):
    """A write failure (unwritable path) is swallowed, not raised — logging must never break a scrape."""
    monkeypatch.setenv("WEBSEARCH_PIPE_SCRAPE_LOG_PATH", "/nonexistent-root-dir/x/pipe_scrape_log.jsonl")

    with caplog.at_level("WARNING", logger="src.crawler.pipe_scrape_logger"):
        log_pipe_scrape({"ts": _now_ts(), "run_id": "r", "url": "https://x.test", "domain": "x.test",
                          "outcome": "ok", "http_status": 200, "bytes": 1, "wall_ms": 1,
                          "config_hash": "h", "config": {}})
    # No exception raised (call above completing is the primary assertion) + a warning was logged
    assert any("pipe_scrape_log write failed" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# _scrape_all: one run_id shared across all URLs, success + exception paths both logged
# ---------------------------------------------------------------------------

class _FakeMarkdown:
    def __init__(self, raw_markdown):
        self.raw_markdown = raw_markdown


class _FakeResult:
    def __init__(self, raw_markdown, status_code=200, success=True, error_message=None):
        self.markdown = _FakeMarkdown(raw_markdown)
        self.status_code = status_code
        self.success = success
        self.error_message = error_message
        self.crawl_stats = {"attempts": 1, "resolved_by": "direct", "fallback_fetch_used": False}


class _FakeCrawler:
    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def arun(self, url, config=None):
        if "fail" in url:
            raise Exception("simulated network failure")
        return _FakeResult(raw_markdown="x" * 500)


@pytest.mark.asyncio
async def test_scrape_all_logs_shared_run_id_across_urls(tmp_path, monkeypatch):
    """Every record from one _scrape_all invocation carries the same run_id."""
    log_file = tmp_path / "pipe_scrape_log.jsonl"
    monkeypatch.setenv("WEBSEARCH_PIPE_SCRAPE_LOG_PATH", str(log_file))
    monkeypatch.setattr(pipe_scraper, "AsyncWebCrawler", _FakeCrawler)

    urls = ["https://x.test/a", "https://x.test/b", "https://x.test/fail"]
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    await pipe_scraper._scrape_all(urls, output_dir, download_delay=0.01, concurrency_per_domain=8)

    records = [json.loads(l) for l in log_file.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 3
    run_ids = {r["run_id"] for r in records}
    assert len(run_ids) == 1

    by_url = {r["url"]: r for r in records}
    assert by_url["https://x.test/a"]["outcome"] == "ok"
    assert by_url["https://x.test/fail"]["outcome"] == "error"
    assert by_url["https://x.test/fail"]["crawl4ai_success"] is None
    assert by_url["https://x.test/a"]["crawl4ai_success"] is True


@pytest.mark.asyncio
async def test_scrape_one_ts_reflects_request_start_not_queue_time(tmp_path, monkeypatch):
    """Regression guard: ts must be stamped AFTER the per-domain gate, not when asyncio.gather
    queues the coroutine. concurrency_per_domain=1 fully serializes 6 same-domain URLs through
    the gate at download_delay=0.05s (jitter 0.025-0.075s/hop) — real elapsed request-start times
    must spread across the run. A ts taken before the gate collapses to one identical value for
    all 6 records regardless of this pacing (the bug this guards against)."""
    log_file = tmp_path / "pipe_scrape_log.jsonl"
    monkeypatch.setenv("WEBSEARCH_PIPE_SCRAPE_LOG_PATH", str(log_file))
    monkeypatch.setattr(pipe_scraper, "AsyncWebCrawler", _FakeCrawler)

    urls = [f"https://x.test/{i}" for i in range(6)]
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    await pipe_scraper._scrape_all(urls, output_dir, download_delay=0.05, concurrency_per_domain=1)

    records = [json.loads(l) for l in log_file.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 6
    timestamps = [datetime.fromisoformat(r["ts"].replace("Z", "+00:00")) for r in records]
    distinct = {t for t in timestamps}
    assert len(distinct) > 1, "all records share one ts — ts is being stamped at queue time, not request start"
    spread_s = (max(timestamps) - min(timestamps)).total_seconds()
    # 5 gate hops at >=0.025s jitter each (serialized, concurrency_per_domain=1) — real lower bound ~0.125s
    assert spread_s > 0.1, f"ts spread too small ({spread_s}s) for a gated 6-URL/concurrency=1 run"


@pytest.mark.asyncio
async def test_scrape_all_records_carry_config_hash_and_config(tmp_path, monkeypatch):
    """Every record carries the same config_hash + config dict for one run (same config in effect)."""
    log_file = tmp_path / "pipe_scrape_log.jsonl"
    monkeypatch.setenv("WEBSEARCH_PIPE_SCRAPE_LOG_PATH", str(log_file))
    monkeypatch.setattr(pipe_scraper, "AsyncWebCrawler", _FakeCrawler)

    urls = ["https://x.test/a", "https://x.test/b"]
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    await pipe_scraper._scrape_all(urls, output_dir, download_delay=0.01, concurrency_per_domain=8)

    records = [json.loads(l) for l in log_file.read_text(encoding="utf-8").splitlines()]
    hashes = {r["config_hash"] for r in records}
    assert len(hashes) == 1
    assert records[0]["config"]["download_delay_s"] == 0.01
    assert records[0]["config"]["concurrency_per_domain"] == 8
    # Fixed anti-bot posture flows through into the logged stamp, not just the in-memory config
    assert records[0]["config"]["enable_stealth"] is True
    assert records[0]["config"]["simulate_user"] is True
    assert records[0]["config"]["override_navigator"] is True
    assert records[0]["config"]["magic"] is False
    assert records[0]["config"]["remove_consent_popups"] is True
