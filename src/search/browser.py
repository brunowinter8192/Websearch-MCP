# INFRASTRUCTURE
import asyncio
import logging
import subprocess
from pathlib import Path

import psutil
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.managers import BrowserProcessManager
from pydoll.commands import TargetCommands

from src.search import browser_lock
# From death_pipe.py: net-2 crash backstop — kills our own Chrome if this process dies without
# tearing it down itself
from src import death_pipe

logger = logging.getLogger(__name__)

SESSION_DIR = str(Path.home() / ".websearch" / "browser-session")
LOCK_PATH = Path(SESSION_DIR).parent / "browser-session.lock"

# Hard budget for one search_web sweep, past which a held cross-process lock is presumed stuck
# (not merely slow) and force-broken (browser_lock.acquire's stale-takeover). Derived from
# search_web.py's own worst case: RATE_WAIT_TIMEOUT (60s, a single engine's rate-limiter wait) +
# ENGINE_WATCHDOG_TIMEOUT (6.0s, uniform across all engines as of 2026-08-25 — no per-engine
# override to pick a "slowest" from anymore) + a 15s margin — real two-parallel-CLI-run measurement
# (2026-08-25) put one full sweep (prewarm+launch through kill_own_chrome teardown) at ~7.25s end
# to end, so 15s already covers ~2x that observed duration; not imported from search_web.py's own
# constants to avoid a browser_lock -> browser -> engines -> search_web import cycle — if those
# constants change, re-derive this by hand.
LOCK_HARD_BUDGET_S = 60.0 + 6.0 + 15.0

BACKGROUNDING_FLAGS = [
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]

_browser = None
_tab = None
_init_lock = asyncio.Lock()
_lock_handle: browser_lock.LockHandle | None = None
_owned_pids: list[int] = []


# FUNCTIONS

# Launch Chrome headed-but-backgrounded via macOS `open -g` — never steals focus
def _open_background_process_creator(command: list[str]) -> subprocess.Popen:
    args = command[1:]
    open_cmd = ["open", "-g", "-n", "-a", "Google Chrome", "--args", *args]
    return subprocess.Popen(open_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Build Chrome options with session persistence and anti-detection
def build_options() -> ChromiumOptions:
    options = ChromiumOptions()
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


# Kill any Chrome process on the shared session profile — legitimate ONLY while the cross-process
# lock is held (proves any survivor is orphaned: a crashed prior run's leftover, whose `open -g`
# wrapper died but whose real Chrome did not, since it is not a child process; or a stale-takeover
# victim). Never called without the lock held.
def _reap_session_profile() -> None:
    result = subprocess.run(
        ["pgrep", "-f", f"user-data-dir={SESSION_DIR}"], capture_output=True, text=True
    )
    pids = [int(p) for p in result.stdout.split() if p.strip().isdigit()]
    if not pids:
        return
    logger.info("Reaping orphaned Chrome on session profile: pids=%s", pids)
    _terminate_then_kill(pids)


# Snapshot Chrome PIDs on the session profile right after launch — trustworthy as "ours" only
# because the cross-process lock + the pre-launch reap above guarantee no foreign Chrome can be
# using this profile at this moment.
def _record_own_pids() -> None:
    global _owned_pids
    result = subprocess.run(
        ["pgrep", "-f", f"user-data-dir={SESSION_DIR}"], capture_output=True, text=True
    )
    _owned_pids = [int(p) for p in result.stdout.split() if p.strip().isdigit()]
    logger.info("Own Chrome pids: %s", _owned_pids)


# SIGTERM then, after a grace period, SIGKILL any still-alive PID — shared by the reap and the
# own-Chrome teardown paths
def _terminate_then_kill(pids: list[int], timeout_s: float = 5.0) -> None:
    procs = []
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            procs.append(proc)
        except psutil.NoSuchProcess:
            pass
    gone, alive = psutil.wait_procs(procs, timeout=timeout_s)
    for proc in alive:
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass


# Get or create the shared browser and tab — first call in a run blocks on the cross-process lock
# (held until kill_own_chrome tears the browser down), reaps any orphaned survivor of a crashed
# prior run, then launches and spawns a death_pipe watchdog (net 2 — a crash backstop for when THIS
# run itself dies before kill_own_chrome/net 1 ever runs; no cleanup_dir, the session profile is
# persistent by design, only the processes get reaped). Must be called OUTSIDE any per-engine
# watchdog (search_web.py's _prewarm_browser does this) — a per-engine timeout (3.6-6.0s) is far
# shorter than a legitimate cross-process lock wait, and asyncio.wait_for cancelling this coroutine
# mid-wait would abandon the blocking asyncio.to_thread call as an orphaned background thread,
# never releasing the lock.
async def get_tab():
    global _browser, _tab, _lock_handle
    async with _init_lock:
        if _browser is None:
            logger.info("Acquiring cross-process browser-session lock")
            _lock_handle = await asyncio.to_thread(
                browser_lock.acquire, LOCK_PATH, LOCK_HARD_BUDGET_S, _reap_session_profile
            )
            try:
                logger.info("Starting Chrome session")
                _reap_session_profile()
                options = build_options()
                _browser = Chrome(options)
                _browser._browser_process_manager = BrowserProcessManager(
                    process_creator=_open_background_process_creator
                )
                _tab = await _browser.start()
                _record_own_pids()
                death_pipe.spawn_watchdog(_owned_pids)
            except Exception:
                _browser = None
                _tab = None
                _lock_handle.release()
                _lock_handle = None
                raise
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


# Deterministic own-run teardown: graceful CDP close_browser() first (caught — Chrome dying mid-
# sweep, crash or manual close, makes _browser.stop() raise on the dead websocket before its own
# `_browser = None` reset runs; a bare `await close_browser()` here would then skip the PID safety
# net and the lock release below it, leaking the lock until the 81s stale-takeover), a PID-scoped
# psutil terminate/kill safety net for anything that survives it (never a profile-pattern kill of a
# live foreign browser — that PID list is only ever this run's own, per _record_own_pids'
# guarantee), then release the cross-process lock. Safe to call even if this run never touched the
# browser (pure-HTTP-engine runs) — every step is a no-op in that case. Called once, from
# search_web_workflow's finally around the engine sweep, and as cli.py's atexit backstop.
async def kill_own_chrome() -> None:
    global _browser, _tab, _owned_pids, _lock_handle
    if _browser is not None:
        try:
            await close_browser()
        except Exception as e:
            logger.warning("close_browser failed (Chrome likely already dead): %s", e)
            _browser = None
            _tab = None
    if _owned_pids:
        logger.info("Killing own Chrome (safety net): pids=%s", _owned_pids)
        _terminate_then_kill(_owned_pids, timeout_s=10.0)
        _owned_pids = []
    if _lock_handle is not None:
        _lock_handle.release()
        _lock_handle = None


# Sync wrapper for atexit — atexit callbacks cannot be coroutines; safe because atexit fires only
# after asyncio.run() in main() has already returned, i.e. no loop is running
def kill_own_chrome_atexit() -> None:
    asyncio.run(kill_own_chrome())
