# INFRASTRUCTURE
"""Shared helpers for the browser-posture latency/flag probes (01, 02).

Self-contained: does NOT import src/ (dev-script isolation) — profile-dir constants and the
`open -g` process_creator mechanism are duplicated from src/search/browser.py's shape and
dev/search_pipeline/27_brave_headed_lane_probe.py's proven launch technique, not shared imports.
"""
import http.server
import json
import logging
import subprocess
import threading
import time
from pathlib import Path

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.managers import BrowserProcessManager

logger = logging.getLogger(__name__)

# Dedicated probe-only profile root — NOT src/search/browser.py's shared SESSION_DIR (that dir is
# addressed explicitly and only by 02_parallel_chrome_probe.py, which tests the real collision case)
PROBE_PROFILE_ROOT = Path.home() / ".websearch" / "browser-posture-probe"

# Playwright's own Chromium launch defaults (microsoft/playwright#33515, #37199, #29399, #34031,
# #36360) — the three flags this milestone measures
BACKGROUNDING_FLAGS = [
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]

# Identical geometry for the automation window and the occluder window so the occluder fully
# covers it (occlusion is a property of screen coverage, not focus)
WINDOW_ARGS = ["--window-position=200,200", "--window-size=900,700"]

# Timer-drift harness page: setInterval every 100ms, 40 ticks (4s nominal). Chromium's documented
# background-page timer throttling clamps to ~1/sec, so throttled vs unthrottled differ by an
# order of magnitude in tick count over the same wall-clock window — unambiguous when present.
PROBE_HTML = """<!doctype html>
<html><head><title>browser-posture-probe</title></head>
<body>
<p id="marker">PROBE_PAGE_READY</p>
<script>
window.__ticks = [];
(function() {
  var n = 0;
  var iv = setInterval(function() {
    window.__ticks.push(Date.now());
    n++;
    if (n >= 40) { clearInterval(iv); }
  }, 100);
})();
</script>
</body></html>
"""


# FUNCTIONS

# Serve PROBE_HTML for any GET request; used as a neutral, deterministic, zero-anti-bot local target
class _ProbeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = PROBE_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


# Start a throwaway localhost HTTP server on an OS-assigned free port; returns (server, thread, port)
def start_probe_server() -> tuple[http.server.ThreadingHTTPServer, threading.Thread, int]:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _ProbeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


# Shut down the probe HTTP server and its thread
def stop_probe_server(server: http.server.ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    thread.join(timeout=5)


# Resolve a named probe profile dir under PROBE_PROFILE_ROOT
def profile_dir(name: str) -> str:
    return str(PROBE_PROFILE_ROOT / name)


# Kill any Chrome process pinned to the given --user-data-dir (probe profile OR the real
# production SESSION_DIR when 02_parallel_chrome_probe.py passes it explicitly)
def kill_by_profile(profile: str) -> None:
    subprocess.run(["pkill", "-f", f"user-data-dir={profile}"], capture_output=True)


# Count live processes pinned to the given --user-data-dir (teardown / collision verification)
def count_processes_for(profile: str) -> int:
    result = subprocess.run(["pgrep", "-f", f"user-data-dir={profile}"], capture_output=True, text=True)
    return len([line for line in result.stdout.splitlines() if line.strip()])


# Build ChromiumOptions for one probe configuration
def build_options(profile: str, headless: bool, extra_flags: list[str], window_args: bool) -> ChromiumOptions:
    options = ChromiumOptions()
    options.headless = headless
    options.add_argument(f"--user-data-dir={profile}")
    options.block_popups = True
    options.block_notifications = True
    for flag in extra_flags:
        options.add_argument(flag)
    if window_args:
        for arg in WINDOW_ARGS:
            options.add_argument(arg)
    return options


# Launch the system Google Chrome headed-but-backgrounded via macOS `open -g` (proven mechanism,
# dev/search_pipeline/27_brave_headed_lane_probe.py) — drops the resolved binary_location (unused;
# `open -a` targets the app bundle directly)
def open_background_process_creator(command: list[str]) -> subprocess.Popen:
    args = command[1:]
    open_cmd = ["open", "-g", "-n", "-a", "Google Chrome", "--args", *args]
    return subprocess.Popen(open_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Start one Chrome instance for a probe config; returns (browser, tab, start_to_tab_s, start_to_drivable_s)
async def launch_chrome(
    profile: str, headless: bool, extra_flags: list[str], backgrounded: bool
) -> tuple[Chrome, object, float, float]:
    kill_by_profile(profile)
    time.sleep(0.3)
    options = build_options(profile, headless, extra_flags, window_args=backgrounded)
    browser = Chrome(options)
    if backgrounded:
        browser._browser_process_manager = BrowserProcessManager(process_creator=open_background_process_creator)
    t0 = time.monotonic()
    tab = await browser.start()
    t_tab = time.monotonic() - t0
    await tab.execute_script("1+1")
    t_drivable = time.monotonic() - t0
    return browser, tab, t_tab, t_drivable


# Stop a probe browser: CDP Browser.close, then unconditional pkill safety net (mirrors
# src/search/browser.py's kill_tab/kill_stale_chrome pattern; mandatory when backgrounded via
# `open -g`, since that Popen is the short-lived `open` wrapper, not Chrome itself)
async def stop_chrome(browser, profile: str) -> None:
    if browser is not None:
        try:
            await browser.stop()
        except Exception as e:
            logger.warning("browser.stop() failed (expected to fall through to pkill): %s", e)
    kill_by_profile(profile)


# Spawn a plain, BACKGROUNDED (`-g`, no focus steal) Chrome window on a throwaway profile — used
# both as the timer-drift occluder (configs 2/3) and as the simulated already-running user Chrome
# (02_parallel_chrome_probe.py). Never forgrounds: this runs on a shared machine with concurrent
# real sessions, and a dev probe has no license to steal focus regardless of what it simulates.
def spawn_plain_chrome(profile: str, window_args: list[str] | None = None) -> None:
    kill_by_profile(profile)
    time.sleep(0.3)
    args = ["open", "-g", "-n", "-a", "Google Chrome", "--args", f"--user-data-dir={profile}"]
    if window_args:
        args += window_args
    subprocess.run(args)


# Extract primitive value from CDP execute_script result dict
def extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Read document.visibilityState/hidden — ground truth for whether Chromium currently considers
# this tab occluded/backgrounded, independent of any assumption about window stacking
async def read_visibility_state(tab) -> dict:
    raw = await tab.execute_script(
        "return JSON.stringify({visibilityState: document.visibilityState, hidden: document.hidden})"
    )
    value = extract_value(raw)
    return json.loads(value) if value else {"visibilityState": None, "hidden": None}


# Read back window.__ticks from the probe page and compute drift stats
async def read_tick_stats(tab) -> dict:
    raw = await tab.execute_script("return JSON.stringify(window.__ticks || [])")
    value = extract_value(raw)
    ticks = json.loads(value) if value else []
    if len(ticks) < 2:
        return {"count": len(ticks), "mean_interval_ms": None, "max_gap_ms": None}
    intervals = [ticks[i + 1] - ticks[i] for i in range(len(ticks) - 1)]
    return {
        "count": len(ticks),
        "mean_interval_ms": round(sum(intervals) / len(intervals), 1),
        "max_gap_ms": max(intervals),
    }


# Compute min/median/max (ms, rounded) over a list of second-valued floats
def stats_ms(values: list[float]) -> dict:
    ms = sorted(round(v * 1000) for v in values)
    n = len(ms)
    if n == 0:
        return {"n": 0, "min": None, "median": None, "max": None}
    median = ms[n // 2] if n % 2 else (ms[n // 2 - 1] + ms[n // 2]) // 2
    return {"n": n, "min": ms[0], "median": median, "max": ms[-1]}


# Frontmost macOS application name (focus-steal check)
def get_frontmost_app() -> str:
    result = subprocess.run(
        [
            "osascript", "-e",
            'tell application "System Events" to get name of first application process whose frontmost is true',
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip()
