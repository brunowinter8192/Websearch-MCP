# INFRASTRUCTURE
import asyncio
import hashlib
import json
import logging
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.browser_manager import ManagedBrowser
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import psutil
from patchright.async_api import async_playwright

from mcp.types import TextContent
# From scrape_logger.py: per-URL JSONL log + sidecar content file
from src.scraper.scrape_logger import log_scrape, write_sidecar
# From death_pipe.py: net-2 crash backstop (per-call watchdog) — net-3 orphan reap reuses its
# terminate/kill primitive
from src import death_pipe

logger = logging.getLogger(__name__)

# Our own bounded DevToolsActivePort wait (R6: self-owned, deterministic — a real deadline-checked
# loop, not an unbounded event wait). Value proven in dev/browser_posture/05_cdp_headed_probe.py.
CDP_PORT_WAIT_TIMEOUT_S = 10.0
# Focus-steal watchdog poll interval — tight enough that any steal (self-launched Chrome is a
# regular, non-accessory app; LSUIElement crashes this bundle per dev/browser_posture/DOCS.md, so
# Camoufox's own accessory-app lever is unavailable here) is a sub-second flicker rather than a
# sustained foreground grab. Same 0.25s granularity this project's own focus-poll probes already use
# (dev/browser_posture/_lib.py's get_frontmost_app).
FOCUS_STEAL_POLL_INTERVAL_S = 0.25

# Outer wall-clock guard for the single cdp-headed acquisition path: 1.0 (bundle-path resolution via
# patchright's own BrowserType.executable_path property — measured ~0.15-0.25s x3 this session,
# margin added, not independently wait_for'd, same treatment as the project's original cold-start
# summand) + 10.0 (DevToolsActivePort wait, CDP_PORT_WAIT_TIMEOUT_S) + 15.5 (crawl4ai's own
# _verify_cdp_ready: 5x2s aiohttp.ClientTimeout + backoff sum
# 0.5*(1.4**0+1.4**1+1.4**2+1.4**3+1.4**4)=5.4728, source: crawl4ai/browser_manager.py) + 180.0
# (connect_over_cdp's own DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS fallback — the SAME
# mechanism/constant that governed the old launch()-based path's cold start, still applies here:
# crawl4ai passes no explicit timeout to connect_over_cdp either, confirmed via patchright's
# _impl/_browser_type.py: "connectOverCDP", TimeoutSettings.launch_timeout, params) + 30.0 (nav,
# page_timeout) + 5.0 (render wait, delay_before_return_html) + 1.3 (consent handling) = 242.8. The
# DevToolsActivePort wait does NOT replace the 180s cold-start ceiling as first assumed — it's an
# addition in front of it, not a substitute. (Lowered from 245.8: the former +3.0 htmldate-extraction
# summand, HTMLDATE_TIMEOUT_S, was removed along with htmldate itself — see this module's own
# Gotchas/DOCS.md — since the declared-date fact now comes from crawl4ai's own already-parsed
# result.metadata, at zero extra acquisition time.)
TOTAL_SCRAPE_BUDGET_S = 242.8
# The single-value posture stamp for extract_config_stamp's "launch_mode" field — kept as a
# constant (not a param) since the escape hatch removal (process-docs/browser_posture/) leaves only
# one acquisition path; still recorded in the log as a truthful discriminator for browser_config.
# headless, which is dead on the cdp path (never read inside crawl4ai's cdp_url branch).
LAUNCH_MODE = "cdp_headed_backgrounded"

_LINK_LINE_RE = re.compile(r'^\[.+\]\(.+\)$')

_ACQUISITION_ERROR_MESSAGES = {
    "browser_missing": "browser binary missing — run `./venv/bin/python -m patchright install chromium` to install it",
}

_BROWSER_LAUNCH_SIGNATURES = (
    "executable doesn't exist",
    "playwright install",
    "browsertype.launch",
    "devtoolsactiveport did not appear",  # this module's own self-launch bounded-wait timeout (cdp path)
)


# ORCHESTRATOR

# Scrape one URL end to end: acquire, log, render — returns content as-is plus acquisition facts
async def scrape_url_chromium_workflow(url: str) -> list[TextContent]:
    t_total = time.perf_counter()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    domain = (urlparse(url).hostname or "").removeprefix("www.")
    logger.info("Scraping: %s", url)

    content, meta = await try_scrape(url)
    total_wall = round((time.perf_counter() - t_total) * 1000)
    config = meta.get("config") or {"config_incomplete": True}
    config_hash = hash_config(config)
    og_published_time = meta.get("og_published_time")

    content_path = write_sidecar(url, ts, content, "filtered", "chromium")
    log_scrape({
        "ts": ts, "url": url, "domain": domain, "mode": "filtered",
        "engine": "chromium",
        "acquisition_error": meta.get("acquisition_error"),
        "timings_ms": {"total_wall": total_wall},
        "http_status": meta.get("status_code"), "content_type": meta.get("content_type"),
        "bytes_returned": len(content.encode("utf-8")) if content else 0,
        "bytes_raw_markdown": meta.get("raw_markdown_bytes", 0),
        "content_path": content_path,
        "og_published_time": og_published_time,
        "landed_url": meta.get("landed_url"),
        "crawl4ai_success": meta.get("crawl4ai_success"),
        "crawl4ai_error_message": meta.get("crawl4ai_error_message"),
        "crawl4ai_attempts": meta.get("crawl4ai_attempts"),
        "crawl4ai_resolved_by": meta.get("crawl4ai_resolved_by"),
        "crawl4ai_fallback_fetch_used": meta.get("crawl4ai_fallback_fetch_used"),
        "document_status_chain": meta.get("document_status_chain"),
        "config_hash": config_hash, "config": config,
    })
    logger.info("Scrape complete: %s (%d chars, acquisition_error=%s)",
                url, len(content), meta.get("acquisition_error"))
    return [TextContent(type="text", text=_format_scrape_output(url, content, meta, og_published_time))]


# FUNCTIONS

# Run one browser acquisition + date extraction + content selection, the guarded span inside try_scrape's budget
async def _acquire_scrape(
    url: str, browser_config: BrowserConfig, crawler_strategy: AsyncPlaywrightCrawlerStrategy,
    run_config: CrawlerRunConfig, empty_meta: dict, document_status_chain: list,
) -> tuple[str, dict]:
    async with AsyncWebCrawler(config=browser_config, crawler_strategy=crawler_strategy) as crawler:
        result = await crawler.arun(url=url, config=run_config)
    status_code = result.status_code if hasattr(result, "status_code") else None
    # The LAST main-frame document response (document_status_chain, collected by the before_goto
    # hook set below) is the response of the page whose content was actually captured — overrides
    # crawl4ai's own status_code, which keeps only the EARLIEST goto-redirect-chain hop and is
    # never updated by a same-document JS navigation happening later (e.g. a Cloudflare challenge
    # resolving during delay_before_return_html). Empty chain (e.g. raw: input, no navigation at
    # all) falls back to crawl4ai's value unchanged — never invents a status.
    if document_status_chain:
        status_code = document_status_chain[-1]
    ct = None
    if hasattr(result, "headers") and result.headers:
        ct = result.headers.get("content-type") or result.headers.get("Content-Type")
    landed_url = getattr(result, "redirected_url", None)
    meta: dict = {**empty_meta, "status_code": status_code, "content_type": ct,
                  "landed_url": landed_url, "document_status_chain": list(document_status_chain)}
    meta.update(extract_crawl4ai_diagnosis(result))
    if not result.markdown:
        return "", meta
    meta["raw_markdown_bytes"] = len((result.markdown.raw_markdown or "").encode("utf-8"))
    meta["og_published_time"] = (getattr(result, "metadata", None) or {}).get("og:published_time")
    content = result.markdown.fit_markdown or ""
    return content, meta


# The run-governing config (unchanged by this milestone)
def _build_run_config() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        magic=True,
        wait_until="load",
        page_timeout=30000,
        delay_before_return_html=5.0,
        max_retries=0,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, preserve_tags=["pre", "code"])
        ),
        remove_consent_popups=True,
        verbose=False,
    )


# Single-call crawl4ai scrape with native anti-bot baseline; returns (content, meta) unconditionally,
# no content judgment. Acquisition is always the cdp-headed-backgrounded route (self-launched
# chromium, connected over cdp_url).
async def try_scrape(url: str) -> tuple[str, dict]:
    await asyncio.to_thread(_reap_orphaned_scrapes)
    run_config = _build_run_config()
    budget_s = TOTAL_SCRAPE_BUDGET_S
    _empty_meta: dict = {
        "acquisition_error": None, "status_code": None, "content_type": None,
        "raw_markdown_bytes": 0, "og_published_time": None,
        "crawl4ai_success": None, "crawl4ai_error_message": None,
        "crawl4ai_attempts": None, "crawl4ai_resolved_by": None,
        "crawl4ai_fallback_fetch_used": None, "landed_url": None,
        "document_status_chain": [],
        "config": {"config_incomplete": True, "launch_mode": LAUNCH_MODE, "total_budget_s": budget_s},
    }
    try:
        return await asyncio.wait_for(
            _acquire_cdp_headed(url, run_config, _empty_meta, budget_s), timeout=budget_s
        )
    except asyncio.TimeoutError:
        logger.warning("Scrape budget exhausted (%.1fs, launch_mode=%s): %s", budget_s, LAUNCH_MODE, url)
        return "", {**_empty_meta, "acquisition_error": "budget_exhausted"}
    except Exception as e:
        if is_browser_launch_error(e):
            logger.error("Browser binary missing/failed to launch for %s: %s", url, e)
            return "", {**_empty_meta, "acquisition_error": "browser_missing"}
        logger.warning("Failed to scrape %s: %s", url, e)
        return "", {**_empty_meta, "acquisition_error": "exception"}


# The default route (probe 05's proven shape): self-launch chromium-1228 headed-but-backgrounded via
# macOS `open -g -n -a`, wait for its DevToolsActivePort, connect crawl4ai over cdp_url. Teardown
# (kill by profile-dir substring + remove the throwaway dir) runs in `finally` so it fires on every
# exit path, including the outer budget's cancellation and any exception raised above (net 1). A
# death_pipe watchdog is ALSO spawned once the port resolves (net 2) — the crash backstop for when
# this whole CLI process dies before the `finally` below ever gets a chance to run at all.
async def _acquire_cdp_headed(
    url: str, run_config: CrawlerRunConfig, empty_meta: dict, budget_s: float,
) -> tuple[str, dict]:
    flags = _build_self_launch_flags(BrowserConfig(enable_stealth=True))
    bundle_path = await _resolve_chromium_bundle_path()
    user_data_dir = tempfile.mkdtemp(prefix="scrape-url-cdp-")
    watchdog_task = asyncio.create_task(_focus_steal_watchdog(bundle_path.stem))
    try:
        _self_launch_chrome(bundle_path, user_data_dir, flags)
        port = await asyncio.to_thread(_wait_for_devtools_port, user_data_dir, CDP_PORT_WAIT_TIMEOUT_S)
        pids = await asyncio.to_thread(_pids_on_profile, user_data_dir)
        death_pipe.spawn_watchdog(pids, cleanup_dir=user_data_dir)
        browser_config = BrowserConfig(
            cdp_url=f"http://127.0.0.1:{port}",
            browser_mode="custom",
            enable_stealth=True,
            cdp_cleanup_on_close=True,
            verbose=False,
        )
        adapter = UndetectedAdapter()
        crawler_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config, browser_adapter=adapter)
        crawler_strategy.set_hook("on_page_context_created", _reject_popup_pages)
        # before_goto is unused by crawl4ai itself and fires before EVERY navigation attempt
        # (including page.goto's own response) — the one place that arms the response listener
        # early enough without touching the on_page_context_created slot _reject_popup_pages owns.
        document_status_chain: list = []
        crawler_strategy.set_hook("before_goto", _make_document_status_listener(document_status_chain))
        config_stamp = extract_config_stamp(browser_config, adapter, crawler_strategy, run_config, budget_s)
        empty_meta = {**empty_meta, "config": config_stamp}
        return await _acquire_scrape(
            url, browser_config, crawler_strategy, run_config, empty_meta, document_status_chain
        )
    finally:
        watchdog_task.cancel()
        try:
            await watchdog_task
        except asyncio.CancelledError:
            pass
        await asyncio.to_thread(_kill_by_profile, user_data_dir)
        shutil.rmtree(user_data_dir, ignore_errors=True)


# Walk up from a bundle-internal executable path to the .app root — same shape as
# camoufox_scrape.py's _find_app_bundle, duplicated per this project's own precedent of not sharing
# small acquisition-lane-specific mechanisms across independent, parallel lanes
def _find_app_bundle(executable_path: str) -> Path | None:
    for parent in Path(executable_path).parents:
        if parent.suffix == ".app":
            return parent
    return None


# Resolve patchright's OWN currently-installed chromium bundle path dynamically — NOT hardcoded to
# a revision number (e.g. "chromium-1228"), which would silently go stale on a patchright upgrade.
# crawl4ai's own get_chromium_path() is NOT usable here: it unconditionally resolves via plain
# playwright, not patchright (confirmed by reading crawl4ai/utils.py) — that would return
# Playwright's OWN separate chromium revision, the wrong bundle entirely (probe 04's finding).
async def _resolve_chromium_bundle_path() -> Path:
    pw = await async_playwright().start()
    try:
        executable_path = pw.chromium.executable_path
    finally:
        await pw.stop()
    bundle = _find_app_bundle(executable_path)
    if bundle is None:
        raise RuntimeError(f"No .app bundle found above patchright's resolved executable: {executable_path}")
    return bundle


# Self-launch flag surface: crawl4ai's OWN flag-construction for an externally-managed/CDP-connected
# browser (ManagedBrowser.build_browser_flags — a live call to the installed package, never pinned,
# so it can never drift out of sync with whatever crawl4ai version is running), plus --window-size
# to match ManagedBrowser's own assembly (_get_browser_args adds it separately, same source).
#
# Deliberately does NOT reach "full" parity with patchright's own RPC-launched headed cmdline
# (probe 05's 34-flag delta): those flags are constructed by patchright's internal Node driver
# specifically for a browserType.launch()/connectOverCDP RPC call — confirmed by reading
# ManagedBrowser.start() itself, which launches via a raw subprocess.Popen, the exact same class of
# mechanism our own `open -g` self-launch uses. No raw-subprocess launcher (crawl4ai's own
# ManagedBrowser included) can ever produce those flags; "full parity" with the RPC cmdline is not
# achievable by construction, not a maintenance gap to guard against.
#
# One deliberate 3-flag deviation from that same delta: build_browser_flags() gates
# --disable-gpu/--disable-gpu-compositing/--disable-software-rasterizer behind `if not
# config.enable_stealth` (its own comment: "Keep WebGL working via SwiftShader when stealth mode is
# active"); the OLDER direct-launch path's sibling function includes them unconditionally, ignoring
# enable_stealth (an existing inconsistency in installed crawl4ai 0.9.2). Kept as build_browser_flags
# produces it, i.e. GPU/WebGL stays ON — more consistent with enable_stealth=True's own intent than
# literal cmdline parity would be.
def _build_self_launch_flags(browser_config: BrowserConfig) -> list[str]:
    flags = list(ManagedBrowser.build_browser_flags(browser_config))
    if browser_config.viewport_width and browser_config.viewport_height:
        flags.append(f"--window-size={browser_config.viewport_width},{browser_config.viewport_height}")
    return flags


# Frontmost macOS application (process) name — same primitive as dev/browser_posture/_lib.py's
# get_frontmost_app, duplicated per this project's own precedent (chromium_scrape.py's own
# _find_app_bundle comment) of not sharing small lane-specific mechanisms across independent lanes
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


# Background task for the whole acquisition span: the self-launched scrape Chrome is a regular,
# non-accessory app (LSUIElement crashes this bundle, dev/browser_posture/DOCS.md), so any window it
# creates can auto-activate it (playwright#42343, process-docs/browser_posture/) regardless of
# `open -g`, which only covers the initial launch moment. Whenever THIS app_name specifically (never
# the user's own separate "Google Chrome", never any other app) is frontmost, immediately re-activates
# whichever app was frontmost the moment before — tracked dynamically as the loop runs, never
# hardcoded — bounding any steal to one FOCUS_STEAL_POLL_INTERVAL_S flicker. Cancelled in
# _acquire_cdp_headed's `finally` (net 1); an in-process asyncio task dies with its own process, so
# unlike a separate watchdog subprocess it cannot outlive a crashed CLI and leave a poll loop behind.
async def _focus_steal_watchdog(app_name: str) -> None:
    last_other_app = await asyncio.to_thread(_get_frontmost_app)
    while True:
        current = await asyncio.to_thread(_get_frontmost_app)
        if current == app_name:
            if last_other_app and last_other_app != app_name:
                await asyncio.to_thread(_activate_app, last_other_app)
        else:
            last_other_app = current
        await asyncio.sleep(FOCUS_STEAL_POLL_INTERVAL_S)


# Launch the resolved chromium bundle headed-but-backgrounded via macOS `open -g -n -a` — the
# proven no-focus-steal mechanism (src/search/browser.py, dev/browser_posture/05_cdp_headed_probe.py)
# — targeting the .app PATH directly, never a bare name (deterministic, no Launch Services ambiguity)
def _self_launch_chrome(bundle_path: Path, user_data_dir: str, flags: list[str]) -> None:
    open_cmd = [
        "open", "-g", "-n", "-a", str(bundle_path), "--args",
        "--remote-debugging-port=0", f"--user-data-dir={user_data_dir}",
        "--no-startup-window", "--no-first-run", "--no-default-browser-check",
        *flags,
    ]
    subprocess.Popen(open_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Poll for Chromium's own DevToolsActivePort file (standard mechanism when --remote-debugging-port=0
# is used) and return the real assigned port — avoids a pre-probed-free-port TOCTOU race. Bounded by
# CDP_PORT_WAIT_TIMEOUT_S; the raised message matches a _BROWSER_LAUNCH_SIGNATURES entry so a
# missing/never-launching bundle is classified as browser_missing, same actionable fix as before.
def _wait_for_devtools_port(user_data_dir: str, timeout_s: float) -> int:
    port_file = Path(user_data_dir) / "DevToolsActivePort"
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if port_file.exists():
            lines = port_file.read_text().splitlines()
            if lines and lines[0].strip().isdigit():
                return int(lines[0].strip())
        time.sleep(0.1)
    raise TimeoutError(f"DevToolsActivePort did not appear under {user_data_dir} within {timeout_s}s")


# PIDs of processes whose cmdline names this exact profile dir — the shared identification
# primitive behind _kill_by_profile, the death_pipe watchdog spawn, and _reap_orphaned_scrapes
def _pids_on_profile(user_data_dir: str) -> list[int]:
    result = subprocess.run(
        ["pgrep", "-f", f"user-data-dir={user_data_dir}"], capture_output=True, text=True
    )
    return [int(p) for p in result.stdout.split() if p.strip().isdigit()]


# Kill the self-launched Chrome by profile-dir substring — the mandatory teardown path since
# `open -g`'s own Popen is a short-lived wrapper, never Chrome itself (src/search/browser.py's
# original kill_stale_chrome pattern; death_pipe._terminate_then_kill WAITS for actual process
# death via psutil rather than a fire-and-forget pkill: a plain pkill returns as soon as the signal
# is sent, not once Chrome actually exits, which raced against the caller's immediately-following
# shutil.rmtree and left a real, non-empty profile directory behind — confirmed live via a real
# cli.py scrape_url_chromium run.
def _kill_by_profile(user_data_dir: str) -> None:
    pids = _pids_on_profile(user_data_dir)
    if pids:
        death_pipe._terminate_then_kill(pids, timeout_s=3.0)


# Net 3 — pre-launch reap for the scrape lane, called at the start of every try_scrape. Parallel
# scrapes are legitimate (every call gets its own unique throwaway profile dir), so a live process
# is NEVER killed just for existing — only once its age exceeds TOTAL_SCRAPE_BUDGET_S, the SAME
# bound any legitimate scrape is itself bounded by (asyncio.wait_for in try_scrape); a still-running
# process past that age cannot be a legitimate in-flight scrape, only an orphan (net 1 and net 2 both
# failed for it — e.g. a pre-death_pipe-milestone leak). Directories are swept on a separate,
# stricter criterion: any scrape-url-cdp-* dir with NO live process at all, any age, is unambiguously
# orphaned regardless of the process-age threshold above.
def _reap_orphaned_scrapes() -> None:
    candidate_pids = _pids_matching_scrape_profiles()
    now = time.time()
    orphaned_pids = []
    for pid in candidate_pids:
        try:
            age_s = now - psutil.Process(pid).create_time()
        except psutil.NoSuchProcess:
            continue
        if age_s > TOTAL_SCRAPE_BUDGET_S:
            orphaned_pids.append(pid)
    if orphaned_pids:
        logger.warning(
            "Reaping orphaned scrape-cdp Chrome (age > %.1fs): pids=%s", TOTAL_SCRAPE_BUDGET_S, orphaned_pids
        )
        death_pipe._terminate_then_kill(orphaned_pids)

    live_dirs = _live_scrape_profile_dirs()
    for entry in Path(tempfile.gettempdir()).glob("scrape-url-cdp-*"):
        if str(entry) not in live_dirs:
            shutil.rmtree(entry, ignore_errors=True)


# All PIDs currently on ANY scrape-url-cdp-* profile (broad prefix match, not one literal dir)
def _pids_matching_scrape_profiles() -> list[int]:
    result = subprocess.run(
        ["pgrep", "-f", "user-data-dir=.*scrape-url-cdp-"], capture_output=True, text=True
    )
    return [int(p) for p in result.stdout.split() if p.strip().isdigit()]


# The set of scrape-url-cdp-* profile dir paths that currently have at least one live process —
# read fresh (after any kill above) so a just-orphaned dir is correctly seen as sweepable this pass
def _live_scrape_profile_dirs() -> set[str]:
    dirs = set()
    for pid in _pids_matching_scrape_profiles():
        try:
            cmdline = psutil.Process(pid).cmdline()
        except psutil.NoSuchProcess:
            continue
        for arg in cmdline:
            if arg.startswith("--user-data-dir=") and "scrape-url-cdp-" in arg:
                dirs.add(arg.removeprefix("--user-data-dir="))
    return dirs


# crawl4ai's on_page_context_created hook target: closes any page the context creates BEYOND the
# one main_page crawl4ai itself asked for (ad/consent-flow popups, window.open) — each such extra
# page is an independent window-creation event that can trigger the same playwright#42343 activation
# the focus-steal watchdog above guards against; closing it fast shrinks that window further
def _reject_popup_pages(main_page, context=None, config=None) -> None:
    def _on_new_page(new_page) -> None:
        if new_page is main_page:
            return
        asyncio.create_task(_close_popup_page(new_page))
    context.on("page", _on_new_page)


# crawl4ai's before_goto hook target: arms a page.on("response") listener before navigation
# begins (so it also catches page.goto's own response), collecting the ORDERED chain of main-frame
# document response statuses — a same-document JS navigation after goto returns (e.g. a Cloudflare
# challenge resolving during delay_before_return_html) fires its own response event here even
# though crawl4ai's own status_code never sees it. A FACT, not a verdict — nothing here decides
# "challenge solved"/"blocked". request.frame can raise for a navigation request issued before its
# frame exists (iframes/popups) — guarded, not filtered on is_navigation_request() alone (which is
# also true for iframe navigations; comparing the frame to page.main_frame is the real filter).
def _make_document_status_listener(status_chain: list) -> Callable:
    def _on_before_goto(page, context=None, url=None, config=None) -> None:
        def _on_response(response) -> None:
            request = response.request
            if request.resource_type != "document":
                return
            try:
                frame = request.frame
            except Exception:
                return
            if frame is not page.main_frame:
                return
            status_chain.append(response.status)
        page.on("response", _on_response)
    return _on_before_goto


# Best-effort popup close — the page may already be gone/closing; logged, not raised, since a stray
# popup failing to close must degrade gracefully, never fail the main scrape it has nothing to do with
async def _close_popup_page(page) -> None:
    try:
        await page.close()
    except Exception as e:
        logger.debug("Popup page close failed (non-fatal): %s", e)


# Read the scrape-governing config back off the actual constructed objects, never re-declared.
# launch_mode is the truthful posture discriminator (browser_config.headless is DEAD on the cdp
# path — never read inside crawl4ai's cdp_url branch, confirmed by source — so it is not stamped at
# all; LAUNCH_MODE is a fixed module constant now that only one acquisition path exists).
def extract_config_stamp(
    browser_config, adapter, crawler_strategy, run_config, total_budget_s: float,
) -> dict:
    content_filter = run_config.markdown_generator.content_filter
    return {
        "launch_mode": LAUNCH_MODE,
        "enable_stealth": browser_config.enable_stealth,
        "adapter": type(adapter).__name__,
        "crawler_strategy": type(crawler_strategy).__name__,
        "magic": run_config.magic,
        "wait_until": run_config.wait_until,
        "page_timeout_ms": run_config.page_timeout,
        "delay_before_return_html_s": run_config.delay_before_return_html,
        "max_retries": run_config.max_retries,
        "cache_mode": run_config.cache_mode.value,
        "content_filter": type(content_filter).__name__,
        "content_filter_threshold": content_filter.threshold,
        "content_filter_preserve_tags": sorted(content_filter.preserve_tags),
        "remove_consent_popups": run_config.remove_consent_popups,
        "total_budget_s": total_budget_s,
    }


# Stable short hash over the config record — cheap "same config" grouping key
def hash_config(config: dict) -> str:
    blob = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


# Read crawl4ai's own anti-bot diagnosis off the result object, verbatim — an OBSERVATION, not a verdict
def extract_crawl4ai_diagnosis(result) -> dict:
    stats = getattr(result, "crawl_stats", None) or {}
    return {
        "crawl4ai_success": getattr(result, "success", None),
        "crawl4ai_error_message": getattr(result, "error_message", None) or None,
        "crawl4ai_attempts": stats.get("attempts"),
        "crawl4ai_resolved_by": stats.get("resolved_by"),
        "crawl4ai_fallback_fetch_used": stats.get("fallback_fetch_used"),
    }


# Detect browser-launch/executable-missing failure (environment defect) vs. an ordinary per-URL error
def is_browser_launch_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(sig in msg for sig in _BROWSER_LAUNCH_SIGNATURES)


# Detect garbage content (error/cookie/login/nav-dump pages) — used only by crawl_site.py's batch filter
def is_garbage_content(content: str) -> str | None:
    if not content or len(content.strip()) < 50:
        return "minimal_content"
    lower = content.lower()

    crawl4ai_errors = ["crawl4ai error:", "document is empty", "page is not fully supported"]
    if any(p in lower for p in crawl4ai_errors):
        return "crawl4ai_error"

    if len(content) < 1000:
        error_keywords = ["not_found", "404", "403", "forbidden", "access denied", "page not found"]
        if any(k in lower for k in error_keywords):
            return "http_error"

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if len(lines) >= 20:
        link_lines = sum(1 for l in lines if _LINK_LINE_RE.match(l))
        if link_lines / len(lines) > 0.6:
            return "nav_dump"

    sample = lower[:5000]
    cookie_signals = sample.count("cookie") + sample.count("consent") + sample.count("duration")
    cookie_wall_signals = ("consent preferences" in sample or "cookieyes" in sample or "cookie preferences" in sample)
    if cookie_signals > 15 and cookie_wall_signals:
        return "cookie_wall"

    if len(content) < 2000:
        login_patterns = [
            "sign in", "log in", "login", "subscribe to continue", "create account",
            "create an account", "premium content", "paywall", "members only", "subscriber only",
        ]
        if any(p in lower for p in login_patterns):
            return "login_wall"

    if len(content) < 500:
        if "checking your browser" in lower or "enable javascript and cookies" in lower:
            return "cloudflare"

    if "just a moment" in lower and "cloudflare" in lower:
        return "cloudflare"

    return None


# Render acquisition facts + full content into one fixed-shape text block
def _format_scrape_output(url: str, content: str, meta: dict, og_published_time: str | None) -> str:
    lines = [f"# Content from: {url}", ""]
    lines += [
        "## Acquisition facts",
        f"- HTTP status: {meta.get('status_code')}",
        f"- Document status chain (ordered main-frame document response statuses observed before "
        f"capture; a fact, not a verdict — never read as challenge-solved/blocked): "
        f"{meta.get('document_status_chain')}",
        f"- Landed URL (the URL the browser actually returned content from): {meta.get('landed_url')}",
        f"- og:published_time (the page's OWN declared value, verbatim from its <head> meta tag — "
        f"null when the page declares none; never a third-party guess): {og_published_time}",
        f"- Bytes (raw markdown from crawl4ai): {meta.get('raw_markdown_bytes', 0)}",
        f"- Bytes (content below, after PruningContentFilter): "
        f"{len(content.encode('utf-8')) if content else 0}",
        "- crawl4ai diagnosis (an OBSERVATION off crawl4ai's own anti-bot detector, NOT a "
        "verdict — it has documented false positives and is not acted on by this scraper): "
        f"success={meta.get('crawl4ai_success')}, resolved_by={meta.get('crawl4ai_resolved_by')}, "
        f"attempts={meta.get('crawl4ai_attempts')}, "
        f"error_message={meta.get('crawl4ai_error_message') or 'none'}",
    ]
    if meta.get("acquisition_error"):
        reason = _acquisition_error_message(meta["acquisition_error"], meta.get("config") or {})
        lines.append(f"- Acquisition error: {reason}")
    lines += ["", "## Content", "", content if content else "(no content returned)"]
    return "\n".join(lines)


# The rendered acquisition-error description — budget_exhausted reads the REAL budget that was in
# effect for this call (config.total_budget_s) rather than a re-declared literal
def _acquisition_error_message(acquisition_error: str, config: dict) -> str:
    if acquisition_error == "budget_exhausted":
        budget = config.get("total_budget_s", "?")
        return f"scrape exceeded the total time budget ({budget}s)"
    return _ACQUISITION_ERROR_MESSAGES.get(acquisition_error, acquisition_error)
