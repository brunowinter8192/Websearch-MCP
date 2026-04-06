# INFRASTRUCTURE
import asyncio
import logging
import os
import subprocess
from pathlib import Path

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import PageCommands

logger = logging.getLogger(__name__)

SESSION_DIR = str(Path.home() / ".searxng-mcp" / "browser-session")

# Real Chrome UA for installed version — removes HeadlessChrome signal
REAL_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.7680.154 Safari/537.36"
)

# JS injected before every page — patches screen/window properties
JS_FINGERPRINT_PATCHES = """
(function() {
    // Screen dimensions: 1920x1080 (external Mac monitor)
    Object.defineProperty(screen, 'width', { get: () => 1920 });
    Object.defineProperty(screen, 'height', { get: () => 1080 });
    Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
    Object.defineProperty(screen, 'availHeight', { get: () => 1057 });
    Object.defineProperty(screen, 'colorDepth', { get: () => 30 });
    Object.defineProperty(screen, 'pixelDepth', { get: () => 30 });

    // devicePixelRatio: Retina Mac
    Object.defineProperty(window, 'devicePixelRatio', { get: () => 2 });

    // outerWidth/outerHeight: real browser has toolbar (~85px)
    Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
    Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight + 85 });
})();

(function() {
    // CSS ActiveText: headless renders rgb(255,0,0) — patch getComputedStyle (#39)
    var _origGCS = window.getComputedStyle;
    window.getComputedStyle = function(element, pseudoElt) {
        var style = _origGCS.apply(this, arguments);
        return new Proxy(style, {
            get: function(target, name) {
                var value = target[name];
                if (name === 'color' && value === 'rgb(255, 0, 0)') {
                    return 'rgb(0, 102, 204)';
                }
                return typeof value === 'function' ? value.bind(target) : value;
            }
        });
    };
})();
"""

_browser = None
_tab = None
_init_lock = asyncio.Lock()


# FUNCTIONS

# Build Chrome options with session persistence and anti-detection
def build_options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.headless = not os.environ.get("SEARXNG_HEADED")
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    options.block_popups = True
    options.block_notifications = True

    # Anti-detection flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.webrtc_leak_protection = True

    # Fingerprint patches: UA override + window size
    options.add_argument(f"--user-agent={REAL_USER_AGENT}")
    options.add_argument("--window-size=1920,1080")

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


# Inject JS patches for screen/window fingerprint vectors
async def apply_fingerprint_patches(tab):
    await tab._execute_command(
        PageCommands.add_script_to_evaluate_on_new_document(
            source=JS_FINGERPRINT_PATCHES,
            run_immediately=True,
        )
    )


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
            _browser = Chrome(build_options())
            _tab = await _browser.start()
            await apply_fingerprint_patches(_tab)
    return _tab


# Cleanup browser on shutdown
async def close_browser():
    global _browser, _tab
    if _browser is not None:
        await _browser.stop()
        _browser = None
        _tab = None
