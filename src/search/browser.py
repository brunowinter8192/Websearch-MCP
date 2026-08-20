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

BACKGROUNDING_FLAGS = [
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]

_FALSY_ENV_VALUES = {"", "0", "false", "no", "off"}

_browser = None
_tab = None
_init_lock = asyncio.Lock()


# FUNCTIONS

# Launch Chrome headed-but-backgrounded via macOS `open -g` — never steals focus
def _open_background_process_creator(command: list[str]) -> subprocess.Popen:
    args = command[1:]
    open_cmd = ["open", "-g", "-n", "-a", "Google Chrome", "--args", *args]
    return subprocess.Popen(open_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Build Chrome options with session persistence and anti-detection
def build_options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.headless = os.environ.get("WEBSEARCH_HEADLESS", "").strip().lower() not in _FALSY_ENV_VALUES
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    options.block_popups = True
    options.block_notifications = True

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.webrtc_leak_protection = True

    for flag in BACKGROUNDING_FLAGS:
        options.add_argument(flag)

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
