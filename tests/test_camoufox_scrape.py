"""Tests for camoufox_scrape's calibrated core acquisition module — the second, parallel
acquisition lane (Camoufox/Playwright-Firefox) beside crawl4ai's chromium path. No CLI/logging
wiring exists yet (later milestones); this only tests the module boundary itself.

Runs without a real Camoufox browser: camoufox_scrape.AsyncCamoufox and camoufox_scrape.launch_options
are patched with fakes, isolating the module from the real binary/network. camoufox_scrape.AsyncWebCrawler
(the separate throwaway crawler used for raw:// markdown conversion) is patched the same way
test_pipe_scraper.py fakes crawl4ai's own AsyncWebCrawler.
"""
import asyncio
import logging

import pytest
from camoufox.exceptions import CamoufoxNotInstalled

from src.scraper import camoufox_scrape


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

def _fake_launch_options(**kwargs):
    return {"executable_path": "/fake/camoufox/firefox-bin", **kwargs}


class _FakeResponse:
    def __init__(self, status):
        self.status = status


class _FakePage:
    def __init__(self, landed_url, status, html):
        self._landed_url = landed_url
        self._status = status
        self._html = html
        self.url = "about:blank"

    async def goto(self, url, timeout=None):
        self.url = self._landed_url
        return _FakeResponse(self._status)

    async def content(self):
        return self._html


class _FakeBrowser:
    def __init__(self, page):
        self._page = page

    async def new_page(self):
        return self._page


def _make_fake_camoufox(landed_url="https://x.test/a", status=200, html="<html><body>real page content</body></html>"):
    """Factory: returns a fake AsyncCamoufox class bound to one fake page's fixed shape."""
    page = _FakePage(landed_url, status, html)
    browser = _FakeBrowser(page)

    class _FakeAsyncCamoufox:
        def __init__(self, **kwargs):
            self.launch_kwargs = kwargs

        async def __aenter__(self):
            return browser

        async def __aexit__(self, *a):
            return False

    return _FakeAsyncCamoufox


class _RaisingAsyncCamoufox:
    def __init__(self, exc):
        self._exc = exc

    def __call__(self, **kwargs):
        return self

    async def __aenter__(self):
        raise self._exc

    async def __aexit__(self, *a):
        return False


class _HangingAsyncCamoufox:
    def __call__(self, **kwargs):
        return self

    async def __aenter__(self):
        await asyncio.sleep(10)

    async def __aexit__(self, *a):
        return False


class _FakeMarkdown:
    def __init__(self, raw_markdown):
        self.raw_markdown = raw_markdown


class _FakeCrawlResult:
    def __init__(self, raw_markdown):
        self.markdown = _FakeMarkdown(raw_markdown)


_FAKE_MARKDOWN_TEXT = "# Fake Markdown\n\nDeterministic content for assertions."


class _FakeAsyncWebCrawler:
    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def arun(self, url, config=None):
        assert url.startswith("raw://")
        return _FakeCrawlResult(_FAKE_MARKDOWN_TEXT)


# ---------------------------------------------------------------------------
# Normal fetch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_camoufox_normal_fetch(monkeypatch):
    """A clean fetch: content, status, landed_url, raw_markdown_bytes, config/config_hash all
    populated; acquisition_error stays None."""
    monkeypatch.setattr(camoufox_scrape, "launch_options", _fake_launch_options)
    monkeypatch.setattr(camoufox_scrape, "AsyncCamoufox",
                         _make_fake_camoufox(landed_url="https://x.test/a", status=200))
    monkeypatch.setattr(camoufox_scrape, "AsyncWebCrawler", _FakeAsyncWebCrawler)

    content, meta = await camoufox_scrape.try_scrape_camoufox("https://x.test/a")

    assert content == _FAKE_MARKDOWN_TEXT
    assert meta["acquisition_error"] is None
    assert meta["status_code"] == 200
    assert meta["landed_url"] == "https://x.test/a"
    assert meta["raw_markdown_bytes"] == len(_FAKE_MARKDOWN_TEXT.encode("utf-8"))
    assert meta["config"]["executable_path"] == "/fake/camoufox/firefox-bin"
    assert meta["config_hash"] is not None


@pytest.mark.asyncio
async def test_try_scrape_camoufox_captures_landed_url_raw_on_redirect(monkeypatch):
    """landed_url reflects wherever the browser actually ended up — raw, no comparison, no
    verdict, even when it differs from the requested URL (host-change redirect shape)."""
    monkeypatch.setattr(camoufox_scrape, "launch_options", _fake_launch_options)
    monkeypatch.setattr(
        camoufox_scrape, "AsyncCamoufox",
        _make_fake_camoufox(landed_url="https://platform.claude.com/docs/en/api/overview", status=301),
    )
    monkeypatch.setattr(camoufox_scrape, "AsyncWebCrawler", _FakeAsyncWebCrawler)

    content, meta = await camoufox_scrape.try_scrape_camoufox(
        "https://docs.anthropic.com/en/api/getting-started")

    assert meta["status_code"] == 301
    assert meta["landed_url"] == "https://platform.claude.com/docs/en/api/overview"
    # No verdict field of any kind — this module reports facts only
    assert "same_target" not in meta


# ---------------------------------------------------------------------------
# acquisition_error states
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_camoufox_budget_exhausted(monkeypatch, caplog):
    """A hang inside the acquisition (Camoufox never returns) is cut off at
    TOTAL_CAMOUFOX_BUDGET_S, yielding acquisition_error=budget_exhausted — not a hang."""
    monkeypatch.setattr(camoufox_scrape, "TOTAL_CAMOUFOX_BUDGET_S", 0.05)
    monkeypatch.setattr(camoufox_scrape, "launch_options", _fake_launch_options)
    monkeypatch.setattr(camoufox_scrape, "AsyncCamoufox", _HangingAsyncCamoufox())

    with caplog.at_level(logging.WARNING, logger="src.scraper.camoufox_scrape"):
        content, meta = await camoufox_scrape.try_scrape_camoufox("https://x.test/a")

    assert content == ""
    assert meta["acquisition_error"] == "budget_exhausted"
    assert any("budget exhausted" in m.lower() for m in caplog.messages)


@pytest.mark.asyncio
async def test_try_scrape_camoufox_detects_binary_missing(monkeypatch, caplog):
    """CamoufoxNotInstalled (raised from launch_options -> launch_path when the browser binary
    hasn't been fetched) maps to acquisition_error=browser_missing, with the fix command named in
    the logged message."""
    def _raise(**kwargs):
        raise CamoufoxNotInstalled(
            "official/stable is not installed. Please run `camoufox fetch` to install.")
    monkeypatch.setattr(camoufox_scrape, "launch_options", _raise)

    with caplog.at_level(logging.ERROR, logger="src.scraper.camoufox_scrape"):
        content, meta = await camoufox_scrape.try_scrape_camoufox("https://x.test/a")

    assert content == ""
    assert meta["acquisition_error"] == "browser_missing"
    assert any("camoufox fetch" in m for m in caplog.messages)


@pytest.mark.asyncio
async def test_try_scrape_camoufox_exception_fail_soft(monkeypatch):
    """A non-launch-missing exception (e.g. a real browser-launch crash) degrades to
    acquisition_error=exception — never propagates to the caller."""
    monkeypatch.setattr(camoufox_scrape, "launch_options", _fake_launch_options)
    monkeypatch.setattr(camoufox_scrape, "AsyncCamoufox",
                         _RaisingAsyncCamoufox(RuntimeError("simulated browser crash")))

    content, meta = await camoufox_scrape.try_scrape_camoufox("https://x.test/a")

    assert content == ""
    assert meta["acquisition_error"] == "exception"
    assert meta["landed_url"] is None
    assert meta["status_code"] is None


# ---------------------------------------------------------------------------
# Markdown-conversion failure: acquisition SUCCEEDED (real HTML captured) but crawl4ai's raw://
# pipeline failed — must NOT look like acquisition_error, and the captured HTML must not be
# silently discarded (the exact invisible-failure class this whole project session worked against)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_try_scrape_camoufox_preserves_html_when_markdown_conversion_raises(monkeypatch):
    """Real shape observed against idealo.de: HTML acquisition succeeds, but the markdown-
    conversion step blows up. content must be the raw captured HTML (never silently lost as ""),
    content_is_raw_html=True, markdown_conversion_error set, and acquisition_error MUST stay None
    — acquisition itself produced a real result, this is a downstream conversion failure."""
    monkeypatch.setattr(camoufox_scrape, "launch_options", _fake_launch_options)
    monkeypatch.setattr(
        camoufox_scrape, "AsyncCamoufox",
        _make_fake_camoufox(landed_url="https://x.test/a", status=200,
                             html="<html><body>real captured page</body></html>"),
    )

    async def _raising_html_to_markdown(html):
        raise ValueError("Invalid IPv6 URL")
    monkeypatch.setattr(camoufox_scrape, "_html_to_markdown", _raising_html_to_markdown)

    content, meta = await camoufox_scrape.try_scrape_camoufox("https://x.test/a")

    assert content == "<html><body>real captured page</body></html>"
    assert meta["content_is_raw_html"] is True
    assert meta["markdown_conversion_error"] == "Invalid IPv6 URL"
    assert meta["acquisition_error"] is None
    assert meta["raw_markdown_bytes"] == 0
    assert meta["status_code"] == 200
    assert meta["landed_url"] == "https://x.test/a"


@pytest.mark.asyncio
async def test_try_scrape_camoufox_preserves_html_when_crawl4ai_swallows_conversion_error(monkeypatch):
    """_html_to_markdown's OWN internal fail-soft path (crawl4ai swallows the error internally and
    returns success=False/markdown=None rather than raising — the ACTUAL idealo.de shape): same
    outcome as the raising case, reached without _html_to_markdown itself ever raising."""
    monkeypatch.setattr(camoufox_scrape, "launch_options", _fake_launch_options)
    monkeypatch.setattr(
        camoufox_scrape, "AsyncCamoufox",
        _make_fake_camoufox(landed_url="https://x.test/a", status=200,
                             html="<html><body>real captured page</body></html>"),
    )

    class _FakeFailedResult:
        markdown = None
        error_message = "Unexpected error in _crawl_web: Invalid IPv6 URL"

    class _FakeFailingAsyncWebCrawler:
        def __init__(self, *a, **kw):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return False
        async def arun(self, url, config=None):
            return _FakeFailedResult()

    monkeypatch.setattr(camoufox_scrape, "AsyncWebCrawler", _FakeFailingAsyncWebCrawler)

    content, meta = await camoufox_scrape.try_scrape_camoufox("https://x.test/a")

    assert content == "<html><body>real captured page</body></html>"
    assert meta["content_is_raw_html"] is True
    assert meta["markdown_conversion_error"] == "Unexpected error in _crawl_web: Invalid IPv6 URL"
    assert meta["acquisition_error"] is None


# ---------------------------------------------------------------------------
# Calibration surface: _build_camoufox_kwargs / _extract_camoufox_config_stamp
# ---------------------------------------------------------------------------

def test_build_camoufox_kwargs_reflects_block_images_param():
    """block_images is the one parameterized (per-lane) knob; everything else is fixed."""
    off = camoufox_scrape._build_camoufox_kwargs(block_images=False)
    on = camoufox_scrape._build_camoufox_kwargs(block_images=True)
    assert off["block_images"] is False
    assert on["block_images"] is True


def test_build_camoufox_kwargs_fixed_decisions():
    """headless=False (visible window), os="macos" (matches real host), timeout explicit — and the
    deliberately-left-unset knobs (block_webgl, geoip, humanize, enable_cache, proxy) are truly
    ABSENT from the dict, not just False, so camoufox's own library defaults apply untouched."""
    kwargs = camoufox_scrape._build_camoufox_kwargs(block_images=False)
    assert kwargs["headless"] is False
    assert kwargs["os"] == "macos"
    assert kwargs["timeout"] == camoufox_scrape._PLAYWRIGHT_DEFAULT_TIMEOUT_MS
    for absent_key in ("block_webgl", "geoip", "humanize", "enable_cache", "proxy", "locale"):
        assert absent_key not in kwargs


def test_extract_camoufox_config_stamp_reads_real_executable_path_not_redeclared():
    """The stamp's executable_path comes off the REAL resolved launch_options() output, not a
    re-declared literal — changing what launch_options() resolves changes the stamp."""
    kwargs = camoufox_scrape._build_camoufox_kwargs(block_images=False)
    resolved = {"executable_path": "/some/real/resolved/path", "headless": False}
    stamp = camoufox_scrape._extract_camoufox_config_stamp(kwargs, resolved)
    assert stamp["executable_path"] == "/some/real/resolved/path"
    assert stamp["total_budget_s"] == camoufox_scrape.TOTAL_CAMOUFOX_BUDGET_S


def test_extract_camoufox_config_stamp_excludes_randomized_fingerprint_data():
    """The stamp must NOT include per-launch randomized fingerprint data (fonts/seeds/env) even if
    present in the resolved dict — hashing that would make config_hash unique on every call."""
    kwargs = camoufox_scrape._build_camoufox_kwargs(block_images=False)
    resolved = {
        "executable_path": "/some/path",
        "env": {"CAMOU_CONFIG": '{"canvas:seed": 12345}'},
        "firefox_user_prefs": {"some.random.pref": True},
    }
    stamp = camoufox_scrape._extract_camoufox_config_stamp(kwargs, resolved)
    assert "env" not in stamp
    assert "firefox_user_prefs" not in stamp


@pytest.mark.asyncio
async def test_config_hash_stable_for_identical_kwargs(monkeypatch):
    """Two calls with the same calibration surface produce the same config_hash — a real 'same
    config' grouping key, not per-call noise."""
    monkeypatch.setattr(camoufox_scrape, "launch_options", _fake_launch_options)
    monkeypatch.setattr(camoufox_scrape, "AsyncCamoufox",
                         _make_fake_camoufox(landed_url="https://x.test/a", status=200))
    monkeypatch.setattr(camoufox_scrape, "AsyncWebCrawler", _FakeAsyncWebCrawler)

    _, meta1 = await camoufox_scrape.try_scrape_camoufox("https://x.test/a")
    _, meta2 = await camoufox_scrape.try_scrape_camoufox("https://x.test/b")

    assert meta1["config_hash"] == meta2["config_hash"]


# ---------------------------------------------------------------------------
# scrape_url_camoufox_workflow: milestone 2 — the ad-hoc CLI wiring. Logs into the SAME
# scrape_log.jsonl / log_scrape / write_sidecar as scrape_url.py's chromium lane, discriminated by
# the "engine" field. try_scrape_camoufox is faked at the module boundary; log_scrape/write_sidecar
# are faked to capture the record instead of touching the filesystem.
# ---------------------------------------------------------------------------

def _meta(**overrides):
    base = {
        "acquisition_error": None, "status_code": 200, "landed_url": "https://x.test/a",
        "raw_markdown_bytes": 100, "markdown_conversion_error": None, "content_is_raw_html": False,
        "config": {"headless": False}, "config_hash": "deadbeef00",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_scrape_url_camoufox_workflow_logs_engine_discriminator(monkeypatch):
    """The logged record carries engine="camoufox" — the first-class discriminator this milestone
    adds, distinguishing it from the chromium lane's engine="chromium" records in the same file."""
    captured = {}

    async def _fake_try_scrape_camoufox(url, block_images=False):
        return "real markdown content", _meta()
    monkeypatch.setattr(camoufox_scrape, "try_scrape_camoufox", _fake_try_scrape_camoufox)
    monkeypatch.setattr(camoufox_scrape, "write_sidecar", lambda *a, **kw: None)
    monkeypatch.setattr(camoufox_scrape, "log_scrape", lambda record: captured.update(record))

    await camoufox_scrape.scrape_url_camoufox_workflow("https://x.test/a")

    assert captured["engine"] == "camoufox"
    assert captured["url"] == "https://x.test/a"
    assert captured["outcome"] == "ok"
    assert captured["mode"] == "markdown"


@pytest.mark.asyncio
async def test_scrape_url_camoufox_workflow_does_not_double_hash_config(monkeypatch):
    """config_hash is read straight off meta (computed once, inside try_scrape_camoufox) — the
    workflow must not re-hash it itself."""
    captured = {}

    async def _fake_try_scrape_camoufox(url, block_images=False):
        return "content", _meta(config_hash="already-computed-hash")
    monkeypatch.setattr(camoufox_scrape, "try_scrape_camoufox", _fake_try_scrape_camoufox)
    monkeypatch.setattr(camoufox_scrape, "write_sidecar", lambda *a, **kw: None)
    monkeypatch.setattr(camoufox_scrape, "log_scrape", lambda record: captured.update(record))

    await camoufox_scrape.scrape_url_camoufox_workflow("https://x.test/a")

    assert captured["config_hash"] == "already-computed-hash"


@pytest.mark.asyncio
async def test_scrape_url_camoufox_workflow_mode_reflects_raw_html_fallback(monkeypatch):
    """mode="raw_html" (not "markdown") when content_is_raw_html is set — the sidecar/log record
    must say plainly what kind of content is actually stored."""
    captured = {}

    async def _fake_try_scrape_camoufox(url, block_images=False):
        return "<html>raw</html>", _meta(content_is_raw_html=True,
                                          markdown_conversion_error="Invalid IPv6 URL")
    monkeypatch.setattr(camoufox_scrape, "try_scrape_camoufox", _fake_try_scrape_camoufox)
    monkeypatch.setattr(camoufox_scrape, "write_sidecar", lambda *a, **kw: None)
    monkeypatch.setattr(camoufox_scrape, "log_scrape", lambda record: captured.update(record))

    await camoufox_scrape.scrape_url_camoufox_workflow("https://x.test/a")

    assert captured["mode"] == "raw_html"
    assert captured["content_is_raw_html"] is True
    assert captured["markdown_conversion_error"] == "Invalid IPv6 URL"


# ---------------------------------------------------------------------------
# _format_camoufox_output: same fixed-shape philosophy as _format_scrape_output — facts always,
# landed URL unconditional, content_is_raw_html stated plainly with the conversion error surfaced
# ---------------------------------------------------------------------------

def test_format_camoufox_output_normal_markdown_shape():
    text = camoufox_scrape._format_camoufox_output(
        "https://x.test/a", "the real markdown content here", _meta())
    assert "- Engine: camoufox" in text
    assert "- HTTP status: 200" in text
    assert "- Landed URL (the URL the browser actually returned content from): https://x.test/a" in text
    assert "Content format" not in text  # only rendered when content_is_raw_html
    facts_idx = text.index("## Acquisition facts")
    content_idx = text.index("## Content")
    body_idx = text.index("the real markdown content here")
    assert facts_idx < content_idx < body_idx


def test_format_camoufox_output_landed_url_unconditional_even_when_absent():
    """Same rule as the chromium lane: landed_url renders even when None (absent), literally."""
    text = camoufox_scrape._format_camoufox_output(
        "https://x.test/a", "", _meta(landed_url=None, acquisition_error="browser_missing"))
    assert "- Landed URL (the URL the browser actually returned content from): None" in text


def test_format_camoufox_output_raw_html_shape_states_it_plainly():
    """content_is_raw_html must be stated PLAINLY, with the conversion error surfaced verbatim as
    an observation, not buried or omitted."""
    text = camoufox_scrape._format_camoufox_output(
        "https://www.idealo.de/preisvergleich/OffersOfProduct/203078159_-fritz-box-7510-avm.html",
        "<html><body>real captured page</body></html>",
        _meta(content_is_raw_html=True, markdown_conversion_error="Invalid IPv6 URL",
              landed_url="https://www.idealo.de/preisvergleich/OffersOfProduct/"
                         "203078159_-woman-hybrid-jacket-fix-hood-33z6026-cmp-campagnolo.html"))
    assert "RAW HTML, NOT markdown" in text
    assert "Invalid IPv6 URL" in text
    assert "OBSERVATION" in text
    assert "<html><body>real captured page</body></html>" in text


def test_format_camoufox_output_acquisition_failure_shape():
    text = camoufox_scrape._format_camoufox_output(
        "https://x.test/a", "",
        _meta(status_code=None, landed_url=None, raw_markdown_bytes=0,
              acquisition_error="budget_exhausted"))
    assert "(no content returned)" in text
    assert "Acquisition error: camoufox acquisition exceeded the total time budget" in text


# ---------------------------------------------------------------------------
# No-focus-steal launch (milestone 3, Half A) — _find_app_bundle / _ensure_no_focus_steal.
# Uses a real tmp_path .app-shaped bundle + real plistlib round-trip (no fakes needed: plistlib is
# pure Python, no camoufox/OS dependency), pinning the exact mechanism verified empirically this
# session (real osascript/System Events focus-poll: LSUIElement=true stopped Camoufox from ever
# becoming the frontmost application across a real try_scrape_camoufox call).
# ---------------------------------------------------------------------------

def test_find_app_bundle_locates_dotapp_ancestor(tmp_path):
    app = tmp_path / "Camoufox.app"
    (app / "Contents" / "MacOS").mkdir(parents=True)
    executable = app / "Contents" / "MacOS" / "camoufox"
    executable.write_text("")
    assert camoufox_scrape._find_app_bundle(str(executable)) == app


def test_find_app_bundle_returns_none_when_not_in_a_bundle(tmp_path):
    bare = tmp_path / "some_binary"
    bare.write_text("")
    assert camoufox_scrape._find_app_bundle(str(bare)) is None


def _make_fake_app_bundle(tmp_path, existing_plist: dict | None = None):
    import plistlib
    app = tmp_path / "Camoufox.app"
    (app / "Contents" / "MacOS").mkdir(parents=True)
    executable = app / "Contents" / "MacOS" / "camoufox"
    executable.write_text("")
    plist_path = app / "Contents" / "Info.plist"
    with open(plist_path, "wb") as f:
        plistlib.dump(existing_plist or {"CFBundleName": "Camoufox"}, f)
    return str(executable), plist_path


def test_ensure_no_focus_steal_sets_lsuielement(tmp_path, monkeypatch):
    """Fresh bundle, no LSUIElement key -> set to True."""
    import plistlib
    monkeypatch.setattr(camoufox_scrape.sys, "platform", "darwin")
    executable, plist_path = _make_fake_app_bundle(tmp_path)

    camoufox_scrape._ensure_no_focus_steal(executable)

    with open(plist_path, "rb") as f:
        data = plistlib.load(f)
    assert data["LSUIElement"] is True


def test_ensure_no_focus_steal_idempotent(tmp_path, monkeypatch):
    """Already-True bundle -> no write attempted (no exception, value unchanged either way)."""
    import plistlib
    monkeypatch.setattr(camoufox_scrape.sys, "platform", "darwin")
    executable, plist_path = _make_fake_app_bundle(
        tmp_path, existing_plist={"CFBundleName": "Camoufox", "LSUIElement": True})

    camoufox_scrape._ensure_no_focus_steal(executable)

    with open(plist_path, "rb") as f:
        data = plistlib.load(f)
    assert data["LSUIElement"] is True


def test_ensure_no_focus_steal_noop_on_non_macos(tmp_path, monkeypatch):
    """Non-darwin platform -> no-op, no exception, plist untouched."""
    import plistlib
    monkeypatch.setattr(camoufox_scrape.sys, "platform", "linux")
    executable, plist_path = _make_fake_app_bundle(tmp_path)

    camoufox_scrape._ensure_no_focus_steal(executable)

    with open(plist_path, "rb") as f:
        data = plistlib.load(f)
    assert "LSUIElement" not in data


def test_ensure_no_focus_steal_noop_when_executable_path_missing(monkeypatch):
    monkeypatch.setattr(camoufox_scrape.sys, "platform", "darwin")
    camoufox_scrape._ensure_no_focus_steal(None)  # must not raise
    camoufox_scrape._ensure_no_focus_steal("")     # must not raise
