# INFRASTRUCTURE
import asyncio
import logging
import os
import subprocess
from pathlib import Path

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.managers import BrowserProcessManager
from pydoll.commands import TargetCommands

logger = logging.getLogger(__name__)

SESSION_DIR = str(Path.home() / ".websearch" / "browser-session")

# Playwright's own Chromium launch defaults, set on every Chromium it starts (microsoft/playwright
# issues #33515, #37199, #29399, #34031, #36360, macOS/Linux/Windows alike). The Chromium switch
# reference describes them as disabling exactly the backgrounding behavior a backgrounded window
# would otherwise be subject to. In on external evidence, not on our own measurement:
# dev/browser_posture/01_launch_latency_probe.py's timer-drift test could NOT confirm their effect —
# the occlusion condition never materialized on that test machine (concurrent real login sessions
# defeated the window-stacking setup). Applied unconditionally (headed or forced-headless), matching
# Playwright's own always-on behavior.
BACKGROUNDING_FLAGS = [
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]

_browser = None
_tab = None
_init_lock = asyncio.Lock()


# FUNCTIONS

# Launch Chrome headed-but-backgrounded via macOS `open -g` — never steals focus. Proven mechanism
# (dev/search_pipeline/27_brave_headed_lane_probe.py, dev/browser_posture/_lib.py, exercised against
# this exact SESSION_DIR in dev/browser_posture/02_parallel_chrome_probe.py). Drops the resolved
# binary_location (unused; `open -a` targets the app bundle directly). `open -g` returns immediately,
# so the Popen handed back is the short-lived `open` wrapper, not Chrome — kill_stale_chrome() below
# is the real teardown, not pydoll's own stop_process().
def _open_background_process_creator(command: list[str]) -> subprocess.Popen:
    args = command[1:]
    open_cmd = ["open", "-g", "-n", "-a", "Google Chrome", "--args", *args]
    return subprocess.Popen(open_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Build Chrome options with session persistence and anti-detection
def build_options() -> ChromiumOptions:
    options = ChromiumOptions()
    # WEBSEARCH_HEADLESS forces headless (debugging, or a machine with no display) — headed,
    # backgrounded is the default (see get_tab()).
    options.headless = bool(os.environ.get("WEBSEARCH_HEADLESS"))
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    options.block_popups = True
    options.block_notifications = True

    # Anti-detection flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.webrtc_leak_protection = True

    for flag in BACKGROUNDING_FLAGS:
        options.add_argument(flag)

    # No explicit --window-size: measured on this machine (real screen 1728x1117 CSS px, availHeight
    # 998), an explicit 1920x1080 gets silently clamped by Chrome to 1728x998 — the requested size is
    # already a lie about what happens, the same reported-vs-observable contradiction Milestone 2
    # removed from the JS patches. Chrome's own default (measured here: ~1200x954 outer) is
    # internally consistent by construction and machine/session-dependent by design, unlike the
    # removed hardcoded values. Not verified against any engine's viewport-dependent behavior — the
    # dev probes ran at 900x700, production has never run at a checked, fixed size either way.

    # Browser preferences — make profile look like a real user
    options.browser_preferences = {
        "profile": {
            "exit_type": "Normal",
            "exited_cleanly": True,
        },
        "safebrowsing": {"enabled": True},
        "autofill": {"enabled": True},
        "search": {"suggest_enabled": True},
        "enable_do_not_track": False,
        "credentials_enable_service": True,
        "credentials_enable_autosignin": True,
    }

    return options


# Kill stale Chrome processes using our session dir
def kill_stale_chrome():
    logger.info("Stale Chrome cleanup")
    subprocess.run(
        ["pkill", "-f", f"user-data-dir={SESSION_DIR}"],
        capture_output=True,
    )


# Get or create the shared browser and tab
async def get_tab():
    global _browser, _tab
    async with _init_lock:
        if _browser is None:
            logger.info("Starting Chrome session")
            kill_stale_chrome()
            options = build_options()
            _browser = Chrome(options)
            if not options.headless:
                _browser._browser_process_manager = BrowserProcessManager(
                    process_creator=_open_background_process_creator
                )
            _tab = await _browser.start()
    return _tab


# Create a new isolated tab in the shared browser
async def new_tab():
    await get_tab()
    tab = await _browser.new_tab()
    return tab


# Kill tab via browser-level Target.closeTarget — works even when the tab's own connection is hung
# 5s cap on close_target guards against wedged browser channel (Chrome process unresponsive);
# kill_stale_chrome() remains the nuclear OS-level fallback for that extreme case
async def kill_tab(tab) -> None:
    global _browser
    target_id = getattr(tab, '_target_id', None)
    if _browser is None or target_id is None:
        return
    try:
        await asyncio.wait_for(
            _browser._execute_command(TargetCommands.close_target(target_id)),
            timeout=5.0,
        )
    except Exception as e:
        logger.warning("kill_tab close_target failed (target_id=%s): %s", target_id, e)
    finally:
        if _browser is not None:
            _browser._tabs_opened.pop(target_id, None)


# Cleanup browser on shutdown
async def close_browser():
    global _browser, _tab
    if _browser is not None:
        await _browser.stop()
        _browser = None
        _tab = None
