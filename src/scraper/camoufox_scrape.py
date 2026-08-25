# INFRASTRUCTURE
import asyncio
import logging
import plistlib
import subprocess
import sys
import time
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

from camoufox import launch_options
from camoufox.async_api import AsyncCamoufox
from camoufox.exceptions import CamoufoxNotInstalled

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from mcp.types import TextContent
# From src/scraper/chromium_scrape.py: same config-hash algorithm used across all scrape paths
from src.scraper.chromium_scrape import hash_config
# From src/scraper/scrape_logger.py: per-URL JSONL log + sidecar content file, shared with chromium_scrape.py
from src.scraper.scrape_logger import log_scrape, write_sidecar

logger = logging.getLogger(__name__)

_PLAYWRIGHT_DEFAULT_TIMEOUT_MS = 30000
_GOTO_WAIT_UNTIL = "domcontentloaded"
CAMOUFOX_RENDER_WAIT_S = 5.0
TOTAL_CAMOUFOX_BUDGET_S = 245.0
# Key-window steal-back watchdog poll interval — same 0.25s tightness as chromium_scrape.py's
# FOCUS_STEAL_POLL_INTERVAL_S, bounding any steal to a sub-second flicker.
KEY_WINDOW_POLL_INTERVAL_S = 0.25

_CAMOUFOX_ACQUISITION_ERROR_MESSAGES = {
    "browser_missing": "camoufox browser binary missing — run `./venv/bin/python -m camoufox fetch` to install it",
    "budget_exhausted": f"camoufox acquisition exceeded the total time budget ({TOTAL_CAMOUFOX_BUDGET_S}s)",
}


# ORCHESTRATOR

# Run the Camoufox lane end to end for one URL: acquisition, JSONL logging, sidecar content, rendered facts
async def scrape_url_camoufox_workflow(url: str, block_images: bool = False) -> list[TextContent]:
    t_total = time.perf_counter()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    domain = (urlparse(url).hostname or "").removeprefix("www.")
    logger.info("Scraping via camoufox: %s", url)

    content, meta = await try_scrape_camoufox(url, block_images=block_images)
    total_wall = round((time.perf_counter() - t_total) * 1000)

    outcome = meta.get("acquisition_error") or ("ok" if content else "empty")
    mode = "raw_html" if meta.get("content_is_raw_html") else "markdown"
    content_path = write_sidecar(url, ts, content, outcome, mode, "camoufox")
    log_scrape({
        "ts": ts, "url": url, "domain": domain, "mode": mode, "outcome": outcome,
        "engine": "camoufox",
        "timings_ms": {"total_wall": total_wall},
        "http_status": meta.get("status_code"),
        "bytes_returned": len(content.encode("utf-8")) if content else 0,
        "bytes_raw_markdown": meta.get("raw_markdown_bytes", 0),
        "content_path": content_path,
        "landed_url": meta.get("landed_url"),
        "markdown_conversion_error": meta.get("markdown_conversion_error"),
        "content_is_raw_html": meta.get("content_is_raw_html", False),
        "config_hash": meta.get("config_hash"), "config": meta.get("config"),
    })
    logger.info("Camoufox scrape complete: %s (%d chars, outcome=%s)", url, len(content), outcome)
    return [TextContent(type="text", text=_format_camoufox_output(url, content, meta))]


# FUNCTIONS

# Walk up from a bundle-internal executable path (.../Foo.app/Contents/MacOS/bin) to the .app root
def _find_app_bundle(executable_path: str) -> Path | None:
    for parent in Path(executable_path).parents:
        if parent.suffix == ".app":
            return parent
    return None


# Set LSUIElement=true on the resolved Camoufox .app bundle so its launch does not steal focus
def _ensure_no_focus_steal(executable_path: str | None) -> None:
    if sys.platform != "darwin" or not executable_path:
        return
    app_path = _find_app_bundle(executable_path)
    if app_path is None:
        return
    plist_path = app_path / "Contents" / "Info.plist"
    try:
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
        if data.get("LSUIElement") is True:
            return
        data["LSUIElement"] = True
        with open(plist_path, "wb") as f:
            plistlib.dump(data, f)
    except Exception as e:
        logger.warning("Could not set LSUIElement on %s (no-focus-steal not applied): %s", plist_path, e)


# Frontmost macOS application (process) name — duplicated per this project's own precedent (see
# chromium_scrape.py's own _get_frontmost_app) of not sharing small lane-specific mechanisms
def _get_frontmost_app() -> str:
    result = subprocess.run(
        [
            "osascript", "-e",
            'tell application "System Events" to get name of first application process whose frontmost is true',
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


# Re-activate a named process via System Events — the same process-name namespace _get_frontmost_app reads from
def _activate_app(app_name: str) -> None:
    subprocess.run(
        [
            "osascript", "-e",
            f'tell application "System Events" to set frontmost of process "{app_name}" to true',
        ],
        capture_output=True, text=True,
    )


# True if app_name's OWN front window is the true key/main window (AXMain) — the key-window-level
# signal a plain frontmost-app check is blind to for an LSUIElement/accessory process: Camoufox can
# win true keyboard/mouse input focus without ever registering as "frontmost" in the NSWorkspace/
# System Events sense _get_frontmost_app reads (confirmed live: 9/12 samples True during a real
# scrape while frontmost-app showed 0 deviations the whole time). False on any error, e.g. the
# process isn't running — correct: a non-running process cannot hold key-window focus.
def _is_key_window_owner(app_name: str) -> bool:
    result = subprocess.run(
        [
            "osascript", "-e",
            f'tell application "System Events" to tell process "{app_name}" '
            'to return value of attribute "AXMain" of front window',
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip() == "true"


# Background task for the whole acquisition span: _ensure_no_focus_steal's LSUIElement patch only
# suppresses the OS's default activation-ON-LAUNCH policy, and dropping Firefox's own `-foreground`
# flag (_build_camoufox_kwargs's ignore_default_args) removes the one other known EXPLICIT
# launch-time activation call — but Camoufox can still win true key-window status when it
# creates/shows its browser window (confirmed live: the steal window was t=3.6-6.6s into a real
# scrape, well after launch, not at t=0 — window-creation-time activation, not launch-time, the
# Camoufox analog of chromium_scrape.py's own playwright#42343 gap). Whenever app_name's OWN front
# window holds AXMain, immediately re-activates whichever app was truly frontmost the moment before —
# tracked dynamically, never hardcoded — reclaiming true key-window status for it. Cancelled in
# _acquire_camoufox's `finally`, mirroring chromium_scrape.py's _focus_steal_watchdog exactly.
async def _key_window_steal_watchdog(app_name: str) -> None:
    last_other_app = await asyncio.to_thread(_get_frontmost_app)
    while True:
        if await asyncio.to_thread(_is_key_window_owner, app_name):
            if last_other_app and last_other_app != app_name:
                await asyncio.to_thread(_activate_app, last_other_app)
        else:
            last_other_app = await asyncio.to_thread(_get_frontmost_app)
        await asyncio.sleep(KEY_WINDOW_POLL_INTERVAL_S)


# Build the plain kwargs this module hands to camoufox.launch_options()/AsyncCamoufox — the calibrated core surface
def _build_camoufox_kwargs(block_images: bool) -> dict:
    return {
        "headless": False,
        "os": "macos",
        "block_images": block_images,
        "timeout": _PLAYWRIGHT_DEFAULT_TIMEOUT_MS,
        # Playwright's Firefox launcher unconditionally injects "-foreground" whenever headless=False
        # (confirmed by reading the installed playwright driver bundle) — an explicit macOS Cocoa
        # activation call that overrides _ensure_no_focus_steal's LSUIElement plist patch below (that
        # patch only changes the PASSIVE default activation policy; -foreground is an active override
        # of it). ignore_default_args is Playwright's own public mechanism for dropping a specific
        # default-injected arg by exact string match; camoufox.launch_options() passes it straight
        # through to playwright.firefox.launch(). Leaves -wait-for-browser, -profile, and camoufox's
        # own fingerprint/window-size/position args (appended separately, never part of this filtered
        # set) untouched.
        "ignore_default_args": ["-foreground"],
    }


# Read the config stamp back off the REAL resolved launch_options() output plus this module's own input kwargs
def _extract_camoufox_config_stamp(kwargs: dict, resolved: dict) -> dict:
    return {
        **kwargs,
        "executable_path": resolved.get("executable_path"),
        "total_budget_s": TOTAL_CAMOUFOX_BUDGET_S,
    }


# Run one Camoufox launch + goto + capture + markdown conversion, the guarded span inside try_scrape_camoufox's budget
async def _acquire_camoufox(url: str, kwargs: dict, empty_meta: dict) -> tuple[str, dict]:
    resolved = await asyncio.get_event_loop().run_in_executor(
        None, partial(launch_options, **kwargs)
    )
    await asyncio.get_event_loop().run_in_executor(
        None, _ensure_no_focus_steal, resolved.get("executable_path")
    )
    config_stamp = _extract_camoufox_config_stamp(kwargs, resolved)
    meta: dict = {**empty_meta, "config": config_stamp, "config_hash": hash_config(config_stamp)}

    app_path = _find_app_bundle(resolved.get("executable_path") or "")
    watchdog_task = asyncio.create_task(_key_window_steal_watchdog(app_path.stem)) if app_path else None
    try:
        async with AsyncCamoufox(from_options=resolved) as browser:
            page = await browser.new_page()
            response = await page.goto(
                url, timeout=_PLAYWRIGHT_DEFAULT_TIMEOUT_MS, wait_until=_GOTO_WAIT_UNTIL
            )
            await asyncio.sleep(CAMOUFOX_RENDER_WAIT_S)
            landed_url = page.url
            status_code = response.status if response else None
            html = await page.content()
    finally:
        if watchdog_task:
            watchdog_task.cancel()
            try:
                await watchdog_task
            except asyncio.CancelledError:
                pass

    try:
        raw_markdown, conversion_error = await _html_to_markdown(html)
    except Exception as e:
        raw_markdown, conversion_error = "", str(e)

    if conversion_error:
        logger.warning("Camoufox markdown conversion failed for %s: %s", url, conversion_error)
        content, content_is_raw_html = html, True
    else:
        content, content_is_raw_html = raw_markdown, False

    meta.update({
        "status_code": status_code, "landed_url": landed_url,
        "raw_markdown_bytes": len(raw_markdown.encode("utf-8")),
        "markdown_conversion_error": conversion_error,
        "content_is_raw_html": content_is_raw_html,
    })
    return content, meta


# Single-call Camoufox (Playwright-Firefox) acquisition; returns (content, meta) unconditionally, no content judgment
async def try_scrape_camoufox(url: str, block_images: bool = False) -> tuple[str, dict]:
    kwargs = _build_camoufox_kwargs(block_images)
    _empty_meta: dict = {
        "acquisition_error": None, "status_code": None, "landed_url": None,
        "raw_markdown_bytes": 0, "markdown_conversion_error": None, "content_is_raw_html": False,
        "config": {"config_incomplete": True}, "config_hash": None,
    }

    try:
        return await asyncio.wait_for(
            _acquire_camoufox(url, kwargs, _empty_meta), timeout=TOTAL_CAMOUFOX_BUDGET_S,
        )
    except asyncio.TimeoutError:
        logger.warning("Camoufox acquisition budget exhausted (%.1fs): %s", TOTAL_CAMOUFOX_BUDGET_S, url)
        return "", {**_empty_meta, "acquisition_error": "budget_exhausted"}
    except CamoufoxNotInstalled as e:
        logger.error(
            "Camoufox browser binary missing for %s — run "
            "`./venv/bin/python -m camoufox fetch` to install it: %s", url, e,
        )
        return "", {**_empty_meta, "acquisition_error": "browser_missing"}
    except Exception as e:
        logger.warning("Failed to scrape %s via camoufox: %s", url, e)
        return "", {**_empty_meta, "acquisition_error": "exception"}


# HTML -> markdown via crawl4ai's own raw: pipeline, reused exactly as pipe_scraper's own fallback rescue does
async def _html_to_markdown(html: str) -> tuple[str, str | None]:
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(),
        verbose=False,
    )
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw:{html}", config=run_config)
    except Exception as e:
        return "", str(e)
    if result.markdown and result.markdown.raw_markdown:
        return result.markdown.raw_markdown, None
    return "", (getattr(result, "error_message", None) or "crawl4ai raw: conversion produced no markdown")


# Render acquisition facts + full content into one fixed-shape text block, a sibling to _format_scrape_output
def _format_camoufox_output(url: str, content: str, meta: dict) -> str:
    lines = [
        f"# Content from: {url}", "",
        "## Acquisition facts",
        "- Engine: camoufox",
        f"- HTTP status: {meta.get('status_code')}",
        f"- Landed URL (the URL the browser actually returned content from): {meta.get('landed_url')}",
        f"- Bytes (raw markdown from crawl4ai's raw: conversion): {meta.get('raw_markdown_bytes', 0)}",
        f"- Bytes (content below): {len(content.encode('utf-8')) if content else 0}",
    ]
    if meta.get("content_is_raw_html"):
        lines.append(
            "- Content format: RAW HTML, NOT markdown — the markdown-conversion step failed "
            "(an OBSERVATION off crawl4ai's own raw: pipeline, not a verdict on this page; the "
            f"page already captured is returned as-is rather than discarded): "
            f"{meta.get('markdown_conversion_error')}"
        )
    if meta.get("acquisition_error"):
        reason = _CAMOUFOX_ACQUISITION_ERROR_MESSAGES.get(meta["acquisition_error"], meta["acquisition_error"])
        lines.append(f"- Acquisition error: {reason}")
    lines += ["", "## Content", "", content if content else "(no content returned)"]
    return "\n".join(lines)
