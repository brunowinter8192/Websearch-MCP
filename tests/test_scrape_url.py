"""Tests for scrape_url's acquisition-facts contract: browser-launch/timeout classification, the
outer time-budget guard, the removed status-code/content-verdict gate, the new return shape that
surfaces facts (HTTP status, byte counts, crawl4ai's own diagnosis) alongside full content instead
of judging it, and (milestone 2 of headed-adhoc) the two-path acquisition architecture — the default
cdp-headed-backgrounded route (self-launch + connect over cdp_url) and the WEBSEARCH_HEADLESS
escape hatch (the old direct headless-shell launch).

Runs without a browser: try_scrape's AsyncWebCrawler is patched to raise a synthetic exception,
simulating a missing patchright/chromium executable, to hang past a (monkeypatched, shortened)
budget constant, or to return a synthetic result carrying an HTTP error status + real content.
Tests that exercise the default cdp path additionally patch the self-launch/port-wait/teardown
mechanics (`_patch_cdp_launch_mechanics`) so no real browser is spawned — those functions get their
own dedicated, unmocked tests further down.
"""
import asyncio
import logging

import pytest

from src.scraper import scrape_url


# ---------------------------------------------------------------------------
# Shared test helper: bypass the real self-launch/port-wait/teardown mechanics so the default cdp
# path can be exercised (AsyncWebCrawler mocked separately, per test) without spawning a real
# browser — mirrors how AsyncWebCrawler itself is already mocked throughout this file.
# ---------------------------------------------------------------------------

def _patch_cdp_launch_mechanics(monkeypatch):
    async def _fake_resolve_bundle():
        return scrape_url.Path("/fake/chromium-1228/Google Chrome for Testing.app")

    monkeypatch.setattr(scrape_url, "_resolve_chromium_bundle_path", _fake_resolve_bundle)
    monkeypatch.setattr(scrape_url, "_self_launch_chrome", lambda *a, **kw: None)
    monkeypatch.setattr(scrape_url, "_wait_for_devtools_port", lambda *a, **kw: 9999)
    monkeypatch.setattr(scrape_url, "_kill_by_profile", lambda *a, **kw: None)


# ---------------------------------------------------------------------------
# is_browser_launch_error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("msg", [
    "BrowserType.launch: Executable doesn't exist at /root/.cache/ms-playwright/chromium-1208/chrome-linux/chrome",
    "Please run the following command to download new browsers:\n    playwright install",
    "Failed to launch chromium via BrowserType.launch",
    "DevToolsActivePort did not appear under /tmp/scrape-url-cdp-abc123 within 10.0s",
])
def test_is_browser_launch_error_detects_signatures(msg):
    """Known launch-failure signatures (both the old direct-launch and the new cdp self-launch's
    own timeout) are classified as browser_missing."""
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
# never a content-judgment verdict; that layer is removed). All exercise the DEFAULT cdp path
# unless noted, via _patch_cdp_launch_mechanics.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_maps_launch_failure_to_browser_missing(monkeypatch, caplog):
    """A browser-launch exception from AsyncWebCrawler yields acquisition_error=browser_missing at ERROR level."""
    _patch_cdp_launch_mechanics(monkeypatch)

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
    _patch_cdp_launch_mechanics(monkeypatch)

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
    def __init__(self, raw_markdown, status_code=200, success=True, error_message=None, html="",
                 redirected_url=None):
        self.markdown = _FakeMarkdown(raw_markdown)
        self.status_code = status_code
        self.success = success
        self.error_message = error_message
        self.html = html
        self.headers = {}
        self.crawl_stats = {"attempts": 1, "resolved_by": "direct", "fallback_fetch_used": False}
        self.redirected_url = redirected_url


@pytest.mark.asyncio
async def test_try_scrape_returns_content_on_http_403(monkeypatch):
    """trustpilot-shaped case: HTTP 403 with real content must be returned, not discarded — the
    old status>=400 early return is gone."""
    _patch_cdp_launch_mechanics(monkeypatch)

    class _FakeCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url, config=None):
            return _FakeResult(raw_markdown="# Real review content, returned as fit_markdown "
                                             "unconditionally — no fit/raw selection exists anymore.",
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
# The fit->raw fallback (MIN_CONTENT_THRESHOLD) is gone as of 2026-08-22 — content is ALWAYS
# fit_markdown, even when short and raw_markdown is longer. An operational-log analysis (69
# production chromium scrapes) found the fallback fired exactly once, on a degenerate page where
# both fit and raw were ~1 byte; the one near-threshold case did not fire and its raw excess was
# category-page link-chrome — exactly what the filter exists to remove.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_returns_short_fit_markdown_unconditionally(monkeypatch):
    """A short fit_markdown (well under the old 200-char threshold) with a much longer raw_markdown
    available is returned AS the short fit_markdown — no fallback to raw fires, because the
    mechanism no longer exists at all."""
    _patch_cdp_launch_mechanics(monkeypatch)
    fake_short_fit = "short fit"

    class _FakeCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url, config=None):
            result = _FakeResult(raw_markdown="x" * 2537)
            result.markdown.fit_markdown = fake_short_fit
            return result

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _FakeCrawler)

    content, meta = await scrape_url.try_scrape("https://example.com")

    assert content == fake_short_fit
    assert meta["raw_markdown_bytes"] == 2537


@pytest.mark.asyncio
async def test_scrape_url_workflow_log_record_has_no_fallback_to_raw_field(monkeypatch):
    """The removed field must not reappear in the JSONL record — fallback_to_raw described a
    mechanism that no longer exists."""
    captured = {}

    async def _fake_try_scrape(url):
        return "real content", _meta()

    monkeypatch.setattr(scrape_url, "try_scrape", _fake_try_scrape)
    monkeypatch.setattr(scrape_url, "write_sidecar", lambda *a, **kw: None)
    monkeypatch.setattr(scrape_url, "log_scrape", lambda record: captured.update(record))

    await scrape_url.scrape_url_workflow("https://example.com")

    assert "fallback_to_raw" not in captured
    assert captured["bytes_raw_markdown"] == 100  # raw_markdown_bytes still reported, as a fact


def test_format_scrape_output_has_no_raw_fallback_note():
    """The " + raw fallback" selection note is gone from the content-bytes line — there is no
    selection to note anymore, content is always the filtered fit_markdown."""
    text = scrape_url._format_scrape_output("https://x.test", "some content", _meta(), None)
    assert "raw fallback" not in text
    assert "Bytes (content below, after PruningContentFilter):" in text


# ---------------------------------------------------------------------------
# try_scrape captures meta["landed_url"] RAW from result.redirected_url
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_captures_landed_url_raw(monkeypatch):
    """meta["landed_url"] is result.redirected_url verbatim — no normalization, no verdict."""
    _patch_cdp_launch_mechanics(monkeypatch)

    class _FakeCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url, config=None):
            return _FakeResult(
                raw_markdown="idealo-shaped: same numeric ID, rewritten slug, real content here.",
                redirected_url="https://www.idealo.de/preisvergleich/OffersOfProduct/"
                               "203078159_-woman-hybrid-jacket-fix-hood-33z6026-cmp-campagnolo.html",
            )

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _FakeCrawler)

    _, meta = await scrape_url.try_scrape(
        "https://www.idealo.de/preisvergleich/OffersOfProduct/203078159_-fritz-box-7510-avm.html")

    assert meta["landed_url"] == (
        "https://www.idealo.de/preisvergleich/OffersOfProduct/"
        "203078159_-woman-hybrid-jacket-fix-hood-33z6026-cmp-campagnolo.html")


@pytest.mark.asyncio
async def test_try_scrape_landed_url_is_none_on_launch_failure(monkeypatch):
    """A path that never obtains a result object (browser_missing) carries landed_url=None, same
    as every other acquisition-error field — no result means no fact to read it off."""
    _patch_cdp_launch_mechanics(monkeypatch)

    class _RaisingCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            raise Exception("BrowserType.launch: Executable doesn't exist at /fake/chrome")

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _RaisingCrawler)

    _, meta = await scrape_url.try_scrape("https://example.com")

    assert meta["acquisition_error"] == "browser_missing"
    assert meta["landed_url"] is None


@pytest.mark.asyncio
async def test_scrape_url_workflow_logs_landed_url(monkeypatch):
    """scrape_url_workflow's log_scrape record carries the raw landed_url off meta — no verdict
    computed or stored alongside it (removed: an agent reading the log has both "url" and
    "landed_url" in the same record and compares them itself)."""
    captured = {}

    async def _fake_try_scrape(url):
        return "real content", _meta(
            landed_url="https://platform.claude.com/en/api/getting-started")

    monkeypatch.setattr(scrape_url, "try_scrape", _fake_try_scrape)
    monkeypatch.setattr(scrape_url, "write_sidecar", lambda *a, **kw: None)
    monkeypatch.setattr(scrape_url, "log_scrape", lambda record: captured.update(record))

    await scrape_url.scrape_url_workflow("https://docs.anthropic.com/en/api/getting-started")

    assert captured["landed_url"] == "https://platform.claude.com/en/api/getting-started"
    assert "same_target" not in captured


# ---------------------------------------------------------------------------
# try_scrape enforces the launch-mode-specific budget constant as an outer guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_times_out_at_budget(monkeypatch, caplog):
    """A hang inside the acquisition (browser call never returns) is cut off at
    TOTAL_SCRAPE_BUDGET_CDP_S (the default path's budget), yielding acquisition_error=
    budget_exhausted — not a hang, not a traceback. Budget shortened to keep this a fast
    regression guard; real-budget timing is verified separately (see completion checklist)."""
    _patch_cdp_launch_mechanics(monkeypatch)
    monkeypatch.setattr(scrape_url, "TOTAL_SCRAPE_BUDGET_CDP_S", 0.05)

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


@pytest.mark.asyncio
async def test_try_scrape_headless_forced_times_out_at_its_own_budget(monkeypatch, caplog):
    """The WEBSEARCH_HEADLESS escape hatch uses TOTAL_SCRAPE_BUDGET_HEADLESS_S, not the cdp
    path's constant — the two are independent, confirmed by shortening only the headless one."""
    monkeypatch.setenv("WEBSEARCH_HEADLESS", "1")
    monkeypatch.setattr(scrape_url, "TOTAL_SCRAPE_BUDGET_HEADLESS_S", 0.05)
    monkeypatch.setattr(scrape_url, "TOTAL_SCRAPE_BUDGET_CDP_S", 999)  # would never fire if wrongly used

    class _HangingCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            await asyncio.sleep(10)
            return self

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _HangingCrawler)

    content, meta = await scrape_url.try_scrape("https://example.com")

    assert content == ""
    assert meta["acquisition_error"] == "budget_exhausted"
    assert meta["config"]["launch_mode"] == "headless_direct_forced"


def test_acquisition_error_messages_has_actionable_browser_missing_fix():
    """The acquisition-error description for browser_missing names the concrete install command."""
    msg = scrape_url._ACQUISITION_ERROR_MESSAGES["browser_missing"]
    assert "patchright install chromium" in msg


def test_acquisition_error_message_budget_exhausted_reads_real_budget():
    """budget_exhausted's message reads the REAL budget that was in effect for that call
    (config.total_budget_s) — not a single hand-typed literal, since the two launch modes have
    different budgets."""
    msg_cdp = scrape_url._acquisition_error_message(
        "budget_exhausted", {"total_budget_s": scrape_url.TOTAL_SCRAPE_BUDGET_CDP_S})
    msg_headless = scrape_url._acquisition_error_message(
        "budget_exhausted", {"total_budget_s": scrape_url.TOTAL_SCRAPE_BUDGET_HEADLESS_S})
    assert "247.8" in msg_cdp
    assert "221.3" in msg_headless
    assert "budget" in msg_cdp.lower()


# ---------------------------------------------------------------------------
# extract_config_stamp — launch_mode discriminator (replaces the dead-on-the-cdp-path
# browser_config.headless field), total_budget_s now an explicit param (two budgets, not one)
# ---------------------------------------------------------------------------

def _real_stamp_args():
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
    return browser_config, adapter, crawler_strategy, run_config


def test_extract_config_stamp_carries_total_budget_s():
    """The config stamp reads total_budget_s off the value passed in, not a re-declared literal."""
    args = _real_stamp_args()
    stamp = scrape_url.extract_config_stamp(*args, "cdp_headed_backgrounded", 247.8)
    assert stamp["total_budget_s"] == 247.8


def test_extract_config_stamp_carries_launch_mode_not_headless():
    """launch_mode is the truthful posture discriminator; the old "headless" boolean field is
    gone entirely (it was dead on the cdp path — never read inside crawl4ai's cdp_url branch)."""
    args = _real_stamp_args()
    stamp = scrape_url.extract_config_stamp(*args, "cdp_headed_backgrounded", 247.8)
    assert stamp["launch_mode"] == "cdp_headed_backgrounded"
    assert "headless" not in stamp


def test_extract_config_stamp_no_longer_carries_max_content_length():
    """max_content_length is gone (the parameter it described no longer exists) — build_config_record
    removed, its only job was merging it in."""
    args = _real_stamp_args()
    stamp = scrape_url.extract_config_stamp(*args, "headless_direct_forced", 221.3)
    assert "max_content_length" not in stamp
    assert not hasattr(scrape_url, "build_config_record")


def test_extract_config_stamp_no_longer_carries_min_content_threshold():
    """The fit->raw fallback mechanism (MIN_CONTENT_THRESHOLD) was removed entirely as of
    2026-08-22 — content is always fit_markdown; the stamp no longer carries a field for a
    selection mechanism that no longer exists."""
    args = _real_stamp_args()
    stamp = scrape_url.extract_config_stamp(*args, "cdp_headed_backgrounded", 247.8)
    assert "min_content_threshold" not in stamp
    assert not hasattr(scrape_url, "MIN_CONTENT_THRESHOLD")


# ---------------------------------------------------------------------------
# is_garbage_content stays importable/functioning — src/crawler/crawl_site.py depends on it for
# its own (different, unattended) batch-crawl filter; this module just stops CALLING it as a gate
# ---------------------------------------------------------------------------

def test_is_garbage_content_still_importable_and_functioning():
    """Guard against accidentally deleting the function itself — only its use as a gate inside
    this module's own try_scrape/scrape_url_workflow was removed."""
    assert scrape_url.is_garbage_content("short") == "minimal_content"
    assert scrape_url.is_garbage_content("A" * 5000 + " ordinary long real content " * 20) is None


@pytest.mark.asyncio
async def test_try_scrape_does_not_call_is_garbage_content(monkeypatch):
    """The content classifier is never invoked from try_scrape anymore — a page shaped exactly
    like a historical garbage category (short 403-flavored text) must come back as content."""
    _patch_cdp_launch_mechanics(monkeypatch)
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

    await scrape_url.try_scrape("https://example.com")
    assert called == []


# ---------------------------------------------------------------------------
# _format_scrape_output: facts always precede content, crawl4ai's diagnosis reads as an
# observation not a verdict, zero content is explicit and never a substituted message
# ---------------------------------------------------------------------------

def _meta(**overrides):
    base = {
        "acquisition_error": None, "status_code": 200, "content_type": "text/html",
        "raw_markdown_bytes": 100, "date": None,
        "crawl4ai_success": True, "crawl4ai_error_message": None,
        "crawl4ai_attempts": 1, "crawl4ai_resolved_by": "direct",
        "crawl4ai_fallback_fetch_used": False, "landed_url": None, "config": {},
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
                                     acquisition_error="budget_exhausted",
                                     config={"total_budget_s": 247.8}), None)
    assert "(no content returned)" in text
    assert "Acquisition error: scrape exceeded the total time budget (247.8s)" in text
    assert "Error scraping" not in text  # the old discard-message phrasing must not reappear


# ---------------------------------------------------------------------------
# _format_scrape_output: the landed-URL line is UNCONDITIONAL — rendered on every scrape, exactly
# like HTTP status, whether the landed URL matches the requested one, differs, or is absent. No
# code-side verdict decides whether the agent gets to see this fact (milestone 5: same_target and
# the conditional render it drove were both removed — see the module's own comment on this line).
# ---------------------------------------------------------------------------

def test_format_scrape_output_renders_landed_url_line_when_it_differs():
    """A landed URL on a genuinely different host renders as an explicit, readable fact — wording
    makes no claim about "redirect" or "different target", since nothing decides that anymore."""
    text = scrape_url._format_scrape_output(
        "https://docs.anthropic.com/en/api/getting-started",
        "the real landed page content",
        _meta(landed_url="https://platform.claude.com/en/api/getting-started"),
        None)
    assert ("Landed URL (the URL the browser actually returned content from): "
            "https://platform.claude.com/en/api/getting-started") in text


def test_format_scrape_output_renders_landed_url_line_when_it_matches():
    """landed_url identical to the requested URL — the overwhelming majority case — still renders
    the line, unconditionally, exactly like HTTP status does."""
    text = scrape_url._format_scrape_output(
        "https://www.rfc-editor.org/info/rfc2616/", "the rfc content",
        _meta(landed_url="https://www.rfc-editor.org/info/rfc2616/"), None)
    assert ("Landed URL (the URL the browser actually returned content from): "
            "https://www.rfc-editor.org/info/rfc2616/") in text


def test_format_scrape_output_renders_landed_url_line_when_absent():
    """No landed_url at all (e.g. acquisition failed before a result existed) still renders the
    line — the absence itself is the fact, rendered literally (None), matching how every other
    absent value in this block reads (e.g. HTTP status on a budget_exhausted record) rather than
    being suppressed into a missing line."""
    text = scrape_url._format_scrape_output(
        "https://x.test/a", "", _meta(landed_url=None, acquisition_error="browser_missing"), None)
    assert "Landed URL (the URL the browser actually returned content from): None" in text


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


# ---------------------------------------------------------------------------
# WEBSEARCH_HEADLESS escape hatch — same falsy-value semantics as src/search/browser.py,
# see process-docs/browser_posture/2026-08-03_headless_escape_hatch_falsy_value_fix.md's area
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected_forced", [
    (None, False),           # unset -> headed (default)
    ("", False),
    ("0", False),
    ("false", False),
    ("FALSE", False),
    ("no", False),
    ("off", False),
    ("  ", False),           # whitespace-only
    ("1", True),
    ("true", True),
    ("yes", True),
    ("anything-else", True),
])
def test_headless_env_forced_falsy_value_matrix(monkeypatch, value, expected_forced):
    if value is None:
        monkeypatch.delenv("WEBSEARCH_HEADLESS", raising=False)
    else:
        monkeypatch.setenv("WEBSEARCH_HEADLESS", value)
    assert scrape_url._headless_env_forced() is expected_forced


@pytest.mark.asyncio
async def test_try_scrape_default_dispatches_to_cdp_headed(monkeypatch):
    """No env var set -> the default cdp-headed path is taken, never the headless-direct one."""
    monkeypatch.delenv("WEBSEARCH_HEADLESS", raising=False)
    _patch_cdp_launch_mechanics(monkeypatch)
    called = {"headless_direct": False, "cdp_headed": False}

    async def _fake_headless_direct(*a, **kw):
        called["headless_direct"] = True
        return "", _meta()

    async def _fake_cdp_headed(*a, **kw):
        called["cdp_headed"] = True
        return "", _meta()

    monkeypatch.setattr(scrape_url, "_acquire_headless_direct", _fake_headless_direct)
    monkeypatch.setattr(scrape_url, "_acquire_cdp_headed", _fake_cdp_headed)

    await scrape_url.try_scrape("https://example.com")

    assert called["cdp_headed"] is True
    assert called["headless_direct"] is False


@pytest.mark.asyncio
async def test_try_scrape_headless_env_dispatches_to_headless_direct(monkeypatch):
    """WEBSEARCH_HEADLESS=1 -> the old direct-launch path is taken, self-launch mechanics never
    called at all (not just no-op'd — genuinely never invoked)."""
    monkeypatch.setenv("WEBSEARCH_HEADLESS", "1")
    called = {"headless_direct": False, "cdp_headed": False}

    async def _fake_headless_direct(*a, **kw):
        called["headless_direct"] = True
        return "", _meta()

    async def _fake_cdp_headed(*a, **kw):
        called["cdp_headed"] = True
        return "", _meta()

    monkeypatch.setattr(scrape_url, "_acquire_headless_direct", _fake_headless_direct)
    monkeypatch.setattr(scrape_url, "_acquire_cdp_headed", _fake_cdp_headed)

    await scrape_url.try_scrape("https://example.com")

    assert called["headless_direct"] is True
    assert called["cdp_headed"] is False


@pytest.mark.asyncio
async def test_launch_mode_truthful_on_cdp_path(monkeypatch):
    _patch_cdp_launch_mechanics(monkeypatch)
    monkeypatch.delenv("WEBSEARCH_HEADLESS", raising=False)

    class _FakeCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url, config=None):
            return _FakeResult(raw_markdown="x" * 300)

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _FakeCrawler)

    _, meta = await scrape_url.try_scrape("https://example.com")
    assert meta["config"]["launch_mode"] == "cdp_headed_backgrounded"
    assert meta["config"]["total_budget_s"] == scrape_url.TOTAL_SCRAPE_BUDGET_CDP_S


@pytest.mark.asyncio
async def test_launch_mode_truthful_on_headless_forced_path(monkeypatch):
    monkeypatch.setenv("WEBSEARCH_HEADLESS", "1")

    class _FakeCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url, config=None):
            return _FakeResult(raw_markdown="x" * 300)

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _FakeCrawler)

    _, meta = await scrape_url.try_scrape("https://example.com")
    assert meta["config"]["launch_mode"] == "headless_direct_forced"
    assert meta["config"]["total_budget_s"] == scrape_url.TOTAL_SCRAPE_BUDGET_HEADLESS_S


# ---------------------------------------------------------------------------
# cdp-headed teardown fires on every exit path — the self-launched Chrome must be killed even
# when acquisition raises or the outer budget times out
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cdp_headed_teardown_fires_on_exception(monkeypatch):
    _patch_cdp_launch_mechanics(monkeypatch)
    kill_calls = []
    monkeypatch.setattr(scrape_url, "_kill_by_profile", lambda d: kill_calls.append(d))

    class _RaisingCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            raise Exception("Timeout 60000ms exceeded while waiting for load")

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _RaisingCrawler)

    await scrape_url.try_scrape("https://example.com")

    assert len(kill_calls) == 1


@pytest.mark.asyncio
async def test_cdp_headed_teardown_fires_on_budget_timeout(monkeypatch):
    _patch_cdp_launch_mechanics(monkeypatch)
    kill_calls = []
    monkeypatch.setattr(scrape_url, "_kill_by_profile", lambda d: kill_calls.append(d))
    monkeypatch.setattr(scrape_url, "TOTAL_SCRAPE_BUDGET_CDP_S", 0.05)

    class _HangingCrawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            await asyncio.sleep(10)
            return self

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(scrape_url, "AsyncWebCrawler", _HangingCrawler)

    _, meta = await scrape_url.try_scrape("https://example.com")

    assert meta["acquisition_error"] == "budget_exhausted"
    assert len(kill_calls) == 1


# ---------------------------------------------------------------------------
# Self-launch mechanics — real functions, no mocking (subprocess/filesystem only)
# ---------------------------------------------------------------------------

def test_wait_for_devtools_port_reads_real_port_file(tmp_path):
    port_file = tmp_path / "DevToolsActivePort"
    port_file.write_text("54321\n/devtools/browser/fake-uuid\n")
    port = scrape_url._wait_for_devtools_port(str(tmp_path), timeout_s=2.0)
    assert port == 54321


def test_wait_for_devtools_port_times_out_when_file_never_appears(tmp_path):
    with pytest.raises(TimeoutError, match="DevToolsActivePort did not appear"):
        scrape_url._wait_for_devtools_port(str(tmp_path), timeout_s=0.3)


def test_find_app_bundle_walks_up_to_app_suffix():
    bundle = scrape_url._find_app_bundle(
        "/Users/x/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/"
        "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
    assert str(bundle).endswith("Google Chrome for Testing.app")


def test_find_app_bundle_returns_none_when_no_app_ancestor():
    assert scrape_url._find_app_bundle("/usr/local/bin/chrome") is None


# ---------------------------------------------------------------------------
# Flag-parity mechanism — build_browser_flags() is called LIVE (never pinned), so its own
# existence/signature is a hard, loud-failure guard: if crawl4ai ever renames/removes/reshapes it,
# this test goes red instead of the self-launch silently losing its flag surface.
# ---------------------------------------------------------------------------

def test_build_browser_flags_symbol_resolves_and_is_callable():
    """Guard against a silent posture change on a crawl4ai upgrade: if ManagedBrowser.
    build_browser_flags disappears, gets renamed, or its signature changes incompatibly, THIS
    test fails loudly — no try/except swallowing the import or the call."""
    from crawl4ai.browser_manager import ManagedBrowser
    import inspect

    assert hasattr(ManagedBrowser, "build_browser_flags")
    sig = inspect.signature(ManagedBrowser.build_browser_flags)
    params = list(sig.parameters)
    assert params, "build_browser_flags must accept at least one parameter (the BrowserConfig)"

    # Real call, real BrowserConfig — not mocked. Raises loudly if the signature is incompatible.
    flags = ManagedBrowser.build_browser_flags(scrape_url.BrowserConfig(enable_stealth=True))
    assert isinstance(flags, list)
    assert all(isinstance(f, str) for f in flags)
    assert len(flags) > 0


def test_build_self_launch_flags_keeps_gpu_on_under_stealth():
    """enable_stealth=True must NOT carry --disable-gpu/--disable-gpu-compositing/
    --disable-software-rasterizer — build_browser_flags() gates these behind `not enable_stealth`
    (its own comment: keep WebGL working under stealth). Deliberate 3-flag deviation from literal
    parity with the old direct-launch path's cmdline, confirmed here so it can't silently regress
    back to disabling GPU."""
    flags = scrape_url._build_self_launch_flags(scrape_url.BrowserConfig(enable_stealth=True))
    assert "--disable-gpu" not in flags
    assert "--disable-gpu-compositing" not in flags
    assert "--disable-software-rasterizer" not in flags
    assert "--disable-blink-features=AutomationControlled" in flags


def test_build_self_launch_flags_includes_window_size_when_viewport_set():
    config = scrape_url.BrowserConfig(enable_stealth=True, viewport_width=1080, viewport_height=600)
    flags = scrape_url._build_self_launch_flags(config)
    assert "--window-size=1080,600" in flags
