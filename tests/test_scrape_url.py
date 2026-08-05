"""Tests for scrape_url's acquisition-facts contract: browser-launch/timeout classification, the
outer time-budget guard, the removed status-code/content-verdict gate, and the new return shape
that surfaces facts (HTTP status, byte counts, crawl4ai's own diagnosis) alongside full content
instead of judging it.

Runs without a browser: try_scrape's AsyncWebCrawler is patched to raise a synthetic exception,
simulating a missing patchright/chromium executable, to hang past a (monkeypatched, shortened)
TOTAL_SCRAPE_BUDGET_S, or to return a synthetic result carrying an HTTP error status + real content.
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
# try_scrape routes acquisition-level failures to meta["acquisition_error"]
# (renamed from garbage_type — these three states mean "acquisition produced no result at all",
# never a content-judgment verdict; that layer is removed)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_maps_launch_failure_to_browser_missing(monkeypatch, caplog):
    """A browser-launch exception from AsyncWebCrawler yields acquisition_error=browser_missing at ERROR level."""

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
    assert meta["acquisition_error"] == "browser_missing"
    assert any("Browser binary missing" in m or "launch" in m.lower() for m in caplog.messages)


@pytest.mark.asyncio
async def test_try_scrape_names_the_generic_exception_state(monkeypatch):
    """A non-launch exception (e.g. timeout) is classified as acquisition_error="exception" —
    named rather than silently collapsed into the same state as a real empty page."""

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
    assert meta["acquisition_error"] == "exception"


# ---------------------------------------------------------------------------
# The removed status-code gate: a real evidence case — an HTTP error status with real content
# must now come back AS content, not be discarded
# ---------------------------------------------------------------------------

class _FakeMarkdown:
    def __init__(self, raw_markdown, fit_markdown=None):
        self.raw_markdown = raw_markdown
        self.fit_markdown = fit_markdown if fit_markdown is not None else raw_markdown


class _FakeResult:
    def __init__(self, raw_markdown, status_code=200, success=True, error_message=None, html=""):
        self.markdown = _FakeMarkdown(raw_markdown)
        self.status_code = status_code
        self.success = success
        self.error_message = error_message
        self.html = html
        self.headers = {}
        self.crawl_stats = {"attempts": 1, "resolved_by": "direct", "fallback_fetch_used": False}


@pytest.mark.asyncio
async def test_try_scrape_returns_content_on_http_403(monkeypatch):
    """trustpilot-shaped case: HTTP 403 with real content must be returned, not discarded — the
    old status>=400 early return is gone."""

    class _FakeCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url, config=None):
            return _FakeResult(raw_markdown="# Real review content, well past the "
                                             "200-char MIN_CONTENT_THRESHOLD so fit_markdown "
                                             "itself is used without a raw fallback kicking in.",
                                status_code=403,
                                error_message="Blocked by anti-bot protection: Cloudflare JS challenge")

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _FakeCrawler)

    content, meta = await scrape_url.try_scrape("https://de.trustpilot.com/review/entega.de")

    assert content.startswith("# Real review content")
    assert meta["status_code"] == 403
    assert meta["acquisition_error"] is None
    # crawl4ai's diagnosis is recorded, not acted on — content came through despite it
    assert meta["crawl4ai_error_message"] == "Blocked by anti-bot protection: Cloudflare JS challenge"


# ---------------------------------------------------------------------------
# try_scrape enforces TOTAL_SCRAPE_BUDGET_S as an outer guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_times_out_at_budget(monkeypatch, caplog):
    """A hang inside the acquisition (browser call never returns) is cut off at
    TOTAL_SCRAPE_BUDGET_S, yielding acquisition_error=budget_exhausted — not a hang, not a
    traceback. Budget shortened to keep this a fast regression guard; real-budget timing is
    verified separately against a real hanging server (see completion checklist)."""
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
    assert meta["acquisition_error"] == "budget_exhausted"
    assert any("budget exhausted" in m.lower() for m in caplog.messages)


def test_acquisition_error_messages_has_actionable_browser_missing_fix():
    """The acquisition-error description for browser_missing names the concrete install command."""
    msg = scrape_url._ACQUISITION_ERROR_MESSAGES["browser_missing"]
    assert "patchright install chromium" in msg


def test_acquisition_error_messages_has_budget_exhausted_entry():
    """budget_exhausted has a distinct, non-empty description."""
    msg = scrape_url._ACQUISITION_ERROR_MESSAGES["budget_exhausted"]
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


def test_extract_config_stamp_no_longer_carries_max_content_length():
    """max_content_length is gone (the parameter it described no longer exists); the stamp reads
    min_content_threshold directly off the module constant instead (folded in, build_config_record
    removed — its only other job was merging the now-gone max_content_length)."""
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
    assert "max_content_length" not in stamp
    assert stamp["min_content_threshold"] == scrape_url.MIN_CONTENT_THRESHOLD
    assert not hasattr(scrape_url, "build_config_record")


# ---------------------------------------------------------------------------
# is_garbage_content stays importable/functioning — src/crawler/crawl_site.py depends on it for
# its own (different, unattended) batch-crawl filter; this module just stops CALLING it as a gate
# ---------------------------------------------------------------------------

def test_is_garbage_content_still_importable_and_functioning():
    """Guard against accidentally deleting the function itself — only its use as a gate inside
    this module's own try_scrape/scrape_url_workflow was removed."""
    assert scrape_url.is_garbage_content("short") == "minimal_content"
    assert scrape_url.is_garbage_content("A" * 5000 + " ordinary long real content " * 20) is None


def test_try_scrape_does_not_call_is_garbage_content(monkeypatch):
    """The content classifier is never invoked from try_scrape anymore — a page shaped exactly
    like a historical garbage category (short 403-flavored text) must come back as content."""
    called = []
    monkeypatch.setattr(scrape_url, "is_garbage_content",
                         lambda content: called.append(content) or "http_error")

    class _FakeCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url, config=None):
            return _FakeResult(raw_markdown="403 forbidden — but this project no longer discards "
                                             "on that basis, the agent judges now" + "x" * 200,
                                status_code=403)

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _FakeCrawler)

    asyncio.run(scrape_url.try_scrape("https://example.com"))
    assert called == []


# ---------------------------------------------------------------------------
# _format_scrape_output: facts always precede content, crawl4ai's diagnosis reads as an
# observation not a verdict, zero content is explicit and never a substituted message
# ---------------------------------------------------------------------------

def _meta(**overrides):
    base = {
        "acquisition_error": None, "status_code": 200, "content_type": "text/html",
        "fallback_to_raw": False, "raw_markdown_bytes": 100, "date": None,
        "crawl4ai_success": True, "crawl4ai_error_message": None,
        "crawl4ai_attempts": 1, "crawl4ai_resolved_by": "direct",
        "crawl4ai_fallback_fetch_used": False, "config": {},
    }
    base.update(overrides)
    return base


def test_format_scrape_output_facts_precede_content():
    text = scrape_url._format_scrape_output("https://x.test", "the real page content here",
                                              _meta(), None)
    facts_idx = text.index("## Acquisition facts")
    content_idx = text.index("## Content")
    body_idx = text.index("the real page content here")
    assert facts_idx < content_idx < body_idx


def test_format_scrape_output_never_replaces_content_with_a_message():
    """Content appears verbatim in the output — not summarized, not replaced."""
    real_content = "SPECIFIC_MARKER_TEXT_12345 that must appear byte-for-byte in the output"
    text = scrape_url._format_scrape_output("https://x.test", real_content, _meta(), None)
    assert real_content in text


def test_format_scrape_output_zero_content_is_explicit_not_suppressed():
    """Zero content renders as an explicit fact, not a discard message standing in for the page."""
    text = scrape_url._format_scrape_output(
        "https://x.test", "", _meta(status_code=None, raw_markdown_bytes=0,
                                     acquisition_error="budget_exhausted"), None)
    assert "(no content returned)" in text
    assert "Acquisition error: scrape exceeded the total time budget" in text
    assert "Error scraping" not in text  # the old discard-message phrasing must not reappear


def test_format_scrape_output_crawl4ai_diagnosis_labeled_as_observation_not_verdict():
    """The diagnosis line itself carries the observation-not-verdict caveat — a caller reading
    only the output text (not the source) must see this, not just a code comment."""
    text = scrape_url._format_scrape_output(
        "https://x.test", "full product page content here, well past any thin-page threshold",
        _meta(status_code=403,
              crawl4ai_error_message="Blocked by anti-bot protection: Cloudflare JS challenge"),
        None)
    assert "OBSERVATION" in text
    assert "NOT a verdict" in text
    assert "Cloudflare JS challenge" in text
    # And the content is still there despite the diagnosis claiming a block
    assert "full product page content here" in text
