"""Tests for browser-launch failure classification and the outer time-budget
guard in scrape_url.

Runs without a browser: try_scrape's AsyncWebCrawler is patched to raise a
synthetic exception, simulating a missing patchright/chromium executable, or
to hang past a (monkeypatched, shortened) TOTAL_SCRAPE_BUDGET_S.
"""
import asyncio
import logging

import pytest

from src.scraper import scrape_url


# ---------------------------------------------------------------------------
# is_browser_launch_error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("msg", [
    "BrowserType.launch: Executable doesn't exist at /root/.cache/ms-playwright/chromium-1208/chrome-linux/chrome",
    "Please run the following command to download new browsers:\n    playwright install",
    "Failed to launch chromium via BrowserType.launch",
])
def test_is_browser_launch_error_detects_signatures(msg):
    """Known launch-failure signatures are classified as browser_missing."""
    assert scrape_url.is_browser_launch_error(Exception(msg)) is True


@pytest.mark.parametrize("msg", [
    "Timeout 60000ms exceeded while waiting for load",
    "net::ERR_NAME_NOT_RESOLVED at https://nonexistent-domain-xyz.test",
    "Page.goto: net::ERR_CONNECTION_REFUSED",
    "",
])
def test_is_browser_launch_error_ignores_ordinary_errors(msg):
    """Ordinary per-URL network/timeout errors are NOT misclassified as browser problems."""
    assert scrape_url.is_browser_launch_error(Exception(msg)) is False


# ---------------------------------------------------------------------------
# try_scrape routes launch failures to garbage_type "browser_missing"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_maps_launch_failure_to_browser_missing(monkeypatch, caplog):
    """A browser-launch exception from AsyncWebCrawler yields garbage_type=browser_missing at ERROR level."""

    class _RaisingCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            raise Exception("BrowserType.launch: Executable doesn't exist at /fake/chrome")

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _RaisingCrawler)

    with caplog.at_level(logging.ERROR, logger="src.scraper.scrape_url"):
        content, meta = await scrape_url.try_scrape("https://example.com")

    assert content == ""
    assert meta["garbage_type"] == "browser_missing"
    assert any("Browser binary missing" in m or "launch" in m.lower() for m in caplog.messages)


@pytest.mark.asyncio
async def test_try_scrape_keeps_generic_outcome_for_ordinary_errors(monkeypatch):
    """A non-launch exception (e.g. timeout) keeps the existing generic empty-meta behavior."""

    class _RaisingCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            raise Exception("Timeout 60000ms exceeded while waiting for load")

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _RaisingCrawler)

    content, meta = await scrape_url.try_scrape("https://example.com")

    assert content == ""
    assert meta["garbage_type"] is None


# ---------------------------------------------------------------------------
# scrape_url_workflow surfaces the actionable message
# ---------------------------------------------------------------------------

def test_garbage_messages_has_actionable_browser_missing_fix():
    """The user-facing message for browser_missing names the concrete install command."""
    msg = scrape_url._GARBAGE_MESSAGES["browser_missing"]
    assert "patchright install chromium" in msg


# ---------------------------------------------------------------------------
# try_scrape enforces TOTAL_SCRAPE_BUDGET_S as an outer guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_times_out_at_budget(monkeypatch, caplog):
    """A hang inside the acquisition (browser call never returns) is cut off at
    TOTAL_SCRAPE_BUDGET_S, yielding garbage_type=budget_exhausted — not a hang, not a traceback.
    Budget shortened to keep this a fast regression guard; real-budget timing is verified
    separately against a real hanging server (see completion checklist)."""
    monkeypatch.setattr(scrape_url, "TOTAL_SCRAPE_BUDGET_S", 0.05)

    class _HangingCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            await asyncio.sleep(10)
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, *a, **kw):
            await asyncio.sleep(10)

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _HangingCrawler)

    with caplog.at_level(logging.WARNING, logger="src.scraper.scrape_url"):
        content, meta = await scrape_url.try_scrape("https://example.com")

    assert content == ""
    assert meta["garbage_type"] == "budget_exhausted"
    assert any("budget exhausted" in m.lower() for m in caplog.messages)


def test_garbage_messages_has_budget_exhausted_entry():
    """budget_exhausted has a distinct, non-empty user-facing message."""
    msg = scrape_url._GARBAGE_MESSAGES["budget_exhausted"]
    assert "budget" in msg.lower()


def test_extract_config_stamp_carries_total_budget_s():
    """The config stamp reads TOTAL_SCRAPE_BUDGET_S off the constant, not a re-declared literal."""
    browser_config = scrape_url.BrowserConfig(headless=True, verbose=False, enable_stealth=True)
    adapter = scrape_url.UndetectedAdapter()
    crawler_strategy = scrape_url.AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config, browser_adapter=adapter
    )
    run_config = scrape_url.CrawlerRunConfig(
        markdown_generator=scrape_url.DefaultMarkdownGenerator(
            content_filter=scrape_url.PruningContentFilter(threshold=0.48, preserve_tags=["pre", "code"])
        ),
        excluded_selector=scrape_url.COOKIE_CONSENT_SELECTOR,
    )
    stamp = scrape_url.extract_config_stamp(browser_config, adapter, crawler_strategy, run_config)
    assert stamp["total_budget_s"] == scrape_url.TOTAL_SCRAPE_BUDGET_S
