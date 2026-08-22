#!/usr/bin/env python3
"""cdp_url route probe for a headed-backgrounded chromium ad-hoc lane — Milestone 1b.

Follow-up to probe 04, which killed the `LSUIElement` lever (crashes the chromium-1228 bundle's
launch). This probe measures the documented field workaround (playwright#35836): launch Chrome
ourselves via macOS `open -g -n -a` (the mechanism proven in `src/search/browser.py` / probe 02,
never steals focus) with our own `--remote-debugging-port` + throwaway `--user-data-dir`, then have
crawl4ai/patchright CONNECT over `cdp_url` rather than launch. Measures, end to end, through the
real crawl4ai `AsyncWebCrawler`:

1. Self-launch success + CDP endpoint coming up.
2. Focus behavior across the WHOLE sequence (self-launch, CDP connect, page creation, navigation,
   teardown) — page creation is the flagged risk per playwright#42343.
3. cmdline delta vs. a freshly-captured patchright-driven headed reference launch (probe 04 Run B
   shape) — the anti-detection surface this route would make us own, not fixed here, only measured.
4. Clean teardown: no crash is expected on this route (no plist edit anywhere), so no launchd
   supervision job should appear either — verified as a regression check against probe 04's finding.

Local throwaway page only. No src/ import, no `_lib.py`/pydoll dependency beyond the three generic
(pydoll-free) helpers reused below — same self-contained convention as probe 04.
"""

# INFRASTRUCTURE
import asyncio
import importlib.metadata
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import psutil

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

sys.path.insert(0, str(Path(__file__).parent))
from _lib import start_probe_server, stop_probe_server, get_frontmost_app  # noqa: E402

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"

CHROMIUM_REVISION_TAG = "chromium-1228"  # the ONLY revision this probe is allowed to touch
LOCAL_DWELL_S = 3.0
FOCUS_POLL_INTERVAL_S = 0.25
CDP_PORT_WAIT_TIMEOUT_S = 10.0
CDP_HTTP_READY_TIMEOUT_S = 5.0

# Stage taxonomy for the focus poll — ROUTE_STAGES is the actual cdp_url route under test;
# REFERENCE_STAGE is an internal tooling step (the patchright DIRECT-launch baseline captured only
# for the cmdline diff) that deliberately has NO backgrounding mitigation and is expected to steal
# focus — must be reported separately, never folded into the route's own headline focus number.
ROUTE_STAGES = ["self_launch", "cdp_port_wait", "cdp_connect_page_navigate", "teardown"]
REFERENCE_STAGE = "reference_launch"

# Deliberately minimal — the point of the args-delta step is to reveal what patchright's driver
# adds "for free" that this route would need to backfill, not to pre-empt the diff by mirroring it.
# --no-startup-window: no pre-existing blank tab at connect time, forcing crawl4ai's get_page() to
# call context.new_page() — the exact page-creation-over-CDP event playwright#42343 flags as risky
# (confirmed by reading crawl4ai's own get_page(): it REUSES an existing page if one is already
# open, so a default startup window would silently dodge the very risk this probe exists to measure).
SELF_LAUNCH_ARGS = ["--no-startup-window", "--no-first-run", "--no-default-browser-check"]


# ORCHESTRATOR

async def run_probe() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path = resolve_chromium_1228_bundle()

    focus_samples: list[tuple[str, str]] = []  # (stage, app) — stage attribution is the point
    stage = {"name": "reference_launch"}
    stop_event = asyncio.Event()
    poll_task = asyncio.create_task(focus_poll_loop(focus_samples, stage, stop_event))

    print("Reference: patchright-driven headed launch (probe 04 Run B shape)", file=sys.stderr)
    reference = await capture_reference_cmdline()
    await asyncio.to_thread(kill_survivors)

    user_data_dir = tempfile.mkdtemp(prefix="browser-posture-cdp-probe-")
    self_launch_result = {"launched": False, "error": None}
    cdp_http_check = {"ready": False, "detail": None}
    scrape_result = {"success": False, "error": None, "content_len": 0}
    self_cmdline = None
    self_pid = None

    try:
        stage["name"] = "self_launch"
        print("Self-launch: open -g -n -a <chromium-1228 bundle>", file=sys.stderr)
        await asyncio.to_thread(self_launch_chrome, bundle_path, user_data_dir)
        self_launch_result["launched"] = True

        stage["name"] = "cdp_port_wait"
        print("Waiting for DevToolsActivePort...", file=sys.stderr)
        port = await asyncio.to_thread(wait_for_devtools_port, user_data_dir, CDP_PORT_WAIT_TIMEOUT_S)
        cdp_http_check = await asyncio.to_thread(check_cdp_http_ready, port)

        self_pid = await asyncio.to_thread(find_pid_by_profile, user_data_dir)
        if self_pid is not None:
            try:
                self_cmdline = psutil.Process(self_pid).cmdline()
            except psutil.Error:
                self_cmdline = None

        print(f"Connecting crawl4ai over cdp_url (port {port})...", file=sys.stderr)
        scrape_result = await scrape_over_cdp(port, stage)
    except Exception as e:
        self_launch_result["error"] = f"{type(e).__name__}: {e}"
        print(f"Self-launch/connect failed: {self_launch_result['error']}", file=sys.stderr)
    finally:
        stage["name"] = "teardown"
        await asyncio.to_thread(kill_by_profile, user_data_dir)
        await asyncio.to_thread(kill_survivors)
        shutil.rmtree(user_data_dir, ignore_errors=True)
        stop_event.set()
        await poll_task

    orphans = check_orphans(user_data_dir)
    cmdline_diff = diff_cmdlines(self_cmdline, reference["cmdline"])
    report_path = write_report(
        bundle_path, reference, self_launch_result, cdp_http_check, scrape_result,
        self_cmdline, cmdline_diff, focus_samples, orphans,
    )
    print(f"\nReport: {report_path}", file=sys.stderr)
    print(f"Orphans after run: {len(orphans)}", file=sys.stderr)


# FUNCTIONS

# Locate the chromium-1228 Google Chrome for Testing.app bundle and hard-verify the revision tag —
# same guard as probe 04, refuses to proceed against any other resolved path (e.g. chromium-1223)
def resolve_chromium_1228_bundle() -> Path:
    matches = list(Path.home().glob(
        "Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/*.app"
    ))
    if not matches:
        raise RuntimeError("No chromium-1228 .app bundle found under ~/Library/Caches/ms-playwright/")
    bundle = matches[0]
    if CHROMIUM_REVISION_TAG not in str(bundle):
        raise RuntimeError(f"Resolved bundle {bundle} is NOT {CHROMIUM_REVISION_TAG}")
    return bundle


# Continuous frontmost-app sample, whole-sequence duration (probe 04's method, reused via _lib) —
# each sample carries the CURRENT stage label (mutated by the orchestrator via the shared `stage`
# dict) so a frontmost hit can be attributed to WHICH step caused it, not just that one occurred
# somewhere in the run
async def focus_poll_loop(samples: list[tuple[str, str]], stage: dict, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        app = await asyncio.to_thread(get_frontmost_app)
        samples.append((stage["name"], app))
        await asyncio.sleep(FOCUS_POLL_INTERVAL_S)


# First descendant of this process whose resolved executable lives under ms-playwright's cache —
# valid for the reference launch (patchright launches it as our own child); NOT valid for the
# self-launch (open forks — see find_pid_by_profile for that case, same lesson as probe 04)
def find_chrome_descendant() -> psutil.Process | None:
    try:
        children = psutil.Process().children(recursive=True)
    except psutil.Error:
        return None
    for proc in children:
        try:
            exe = proc.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        if "ms-playwright" in exe:
            return proc
    return None


# One real patchright-driven headed launch (probe 04's Run B shape, no plist involved) against a
# local throwaway page — captures a FRESH real cmdline as the diff baseline, rather than relying on
# probe 04's saved report text
async def capture_reference_cmdline() -> dict:
    server, thread, port = start_probe_server()
    url = f"http://127.0.0.1:{port}/"
    info = {"pid": None, "exe": None, "cmdline": None}
    stop_event = asyncio.Event()

    async def poll_loop():
        while not stop_event.is_set():
            if info["pid"] is None:
                proc = await asyncio.to_thread(find_chrome_descendant)
                if proc is not None:
                    try:
                        info["pid"] = proc.pid
                        info["exe"] = proc.exe()
                        info["cmdline"] = proc.cmdline()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            await asyncio.sleep(0.2)

    poll_task = asyncio.create_task(poll_loop())
    browser_config = BrowserConfig(headless=False, verbose=False, enable_stealth=True)
    adapter = UndetectedAdapter()
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config, browser_adapter=adapter)
    run_config = CrawlerRunConfig(
        wait_until="load", page_timeout=15000, delay_before_return_html=LOCAL_DWELL_S,
        cache_mode=CacheMode.BYPASS, verbose=False,
    )
    error = None
    try:
        async with AsyncWebCrawler(config=browser_config, crawler_strategy=crawler_strategy) as crawler:
            await crawler.arun(url=url, config=run_config)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    finally:
        stop_event.set()
        await poll_task
        stop_probe_server(server, thread)

    return {"pid": info["pid"], "exe": info["exe"], "cmdline": info["cmdline"], "error": error}


# Launch the chromium-1228 bundle headed-but-backgrounded via macOS `open -g -n -a`, targeting the
# resolved .app PATH directly (not a bare name) — deterministic, no Launch Services ambiguity
def self_launch_chrome(bundle_path: Path, user_data_dir: str) -> None:
    open_cmd = [
        "open", "-g", "-n", "-a", str(bundle_path), "--args",
        "--remote-debugging-port=0", f"--user-data-dir={user_data_dir}",
        *SELF_LAUNCH_ARGS,
    ]
    subprocess.Popen(open_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Poll for Chromium's own DevToolsActivePort file (standard mechanism when --remote-debugging-port=0
# is used) and return the real assigned port — avoids a pre-probed-free-port TOCTOU race
def wait_for_devtools_port(user_data_dir: str, timeout_s: float) -> int:
    port_file = Path(user_data_dir) / "DevToolsActivePort"
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if port_file.exists():
            lines = port_file.read_text().splitlines()
            if lines and lines[0].strip().isdigit():
                return int(lines[0].strip())
        time.sleep(0.1)
    raise TimeoutError(f"DevToolsActivePort did not appear under {user_data_dir} within {timeout_s}s")


# Independent confirmation the CDP HTTP endpoint is actually reachable, separate from crawl4ai's
# own internal _verify_cdp_ready retries — a direct GET on /json/version, parsed for the real
# reported browser string
def check_cdp_http_ready(port: int) -> dict:
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.monotonic() + CDP_HTTP_READY_TIMEOUT_S
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                data = json.loads(resp.read())
                return {"ready": True, "detail": data.get("Browser"), "webSocketDebuggerUrl": data.get("webSocketDebuggerUrl")}
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            last_error = str(e)
            time.sleep(0.2)
    return {"ready": False, "detail": last_error}


# Real crawl4ai connect-over-cdp_url scrape against the local throwaway page — the actual config
# shape this route requires, built off reading browser_manager.py's cdp branch directly. Stage
# label set to "cdp_connect_page_navigate" for the whole arun() call — connect/get_page (the
# page-creation-over-CDP moment)/goto are bundled in one high-level call; splitting them further
# would require hooking crawl4ai internals, out of scope for this probe. Still isolates this whole
# bundle from self_launch/cdp_port_wait/teardown, the primary attribution this milestone needs.
async def scrape_over_cdp(port: int, stage: dict) -> dict:
    server, thread, http_port = start_probe_server()
    url = f"http://127.0.0.1:{http_port}/"
    browser_config = BrowserConfig(
        cdp_url=f"http://127.0.0.1:{port}",
        browser_mode="custom",
        enable_stealth=True,
        cdp_cleanup_on_close=True,
        verbose=False,
    )
    adapter = UndetectedAdapter()
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config, browser_adapter=adapter)
    run_config = CrawlerRunConfig(
        wait_until="load", page_timeout=15000, delay_before_return_html=1.0,
        cache_mode=CacheMode.BYPASS, verbose=False,
    )
    try:
        stage["name"] = "cdp_connect_page_navigate"
        async with AsyncWebCrawler(config=browser_config, crawler_strategy=crawler_strategy) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            success = bool(getattr(result, "success", False)) or bool(getattr(result, "html", None))
            content_len = len(getattr(result, "html", "") or "")
            return {"success": success, "error": getattr(result, "error_message", None), "content_len": content_len}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {e}", "content_len": 0}
    finally:
        stop_probe_server(server, thread)


# Real PID of the self-launched Chrome, found by --user-data-dir substring (NOT children-of-self:
# `open` forks and the actual Chrome process is not our descendant — same lesson as probe 04's
# launchd-driven-respawn finding; the only reliable handle is the profile-dir substring, matching
# src/search/browser.py's own kill_stale_chrome/kill_by_profile pattern)
def find_pid_by_profile(user_data_dir: str) -> int | None:
    result = subprocess.run(["pgrep", "-f", f"user-data-dir={user_data_dir}"], capture_output=True, text=True)
    pids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return int(pids[0]) if pids else None


# Kill the self-launched Chrome by profile dir — the mandatory teardown path since `open -g`'s own
# Popen is a short-lived wrapper, not Chrome itself (same pattern as _lib.py's kill_by_profile /
# src/search/browser.py's kill_stale_chrome)
def kill_by_profile(user_data_dir: str) -> None:
    subprocess.run(["pkill", "-f", f"user-data-dir={user_data_dir}"], capture_output=True)


# Defensive sweep for any leftover ms-playwright/chromium process + launchd supervision job —
# duplicated from probe 04 (self-contained convention); no crash is expected on this route so this
# should always be a no-op, kept as a safety net and a live regression check on that expectation
def kill_survivors() -> None:
    launchd_result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    for line in launchd_result.stdout.splitlines():
        if "chrome.for.testing" in line.lower():
            label = line.split()[-1]
            subprocess.run(["launchctl", "remove", label], capture_output=True)
    victims = []
    for proc in psutil.process_iter(["pid"]):
        try:
            if "ms-playwright/chromium" in proc.exe():
                proc.terminate()
                victims.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    if victims:
        gone, alive = psutil.wait_procs(victims, timeout=3)
        for proc in alive:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass


# Set-difference between the self-launched cmdline and the patchright reference cmdline — the
# anti-detection surface this route would make us own, measured not fixed
def diff_cmdlines(self_cmdline: list[str] | None, reference_cmdline: list[str] | None) -> dict:
    if not self_cmdline or not reference_cmdline:
        return {"comparable": False}

    def flag_set(cmdline):
        return {a.split("=")[0] if a.startswith("--") else a for a in cmdline[1:]}

    self_flags = flag_set(self_cmdline)
    ref_flags = flag_set(reference_cmdline)
    return {
        "comparable": True,
        "only_in_reference": sorted(ref_flags - self_flags),
        "only_in_self": sorted(self_flags - ref_flags),
        "common_count": len(self_flags & ref_flags),
    }


# pgrep for any leftover process pinned to this run's throwaway profile + any residual launchd job
def check_orphans(user_data_dir: str) -> list[str]:
    result = subprocess.run(["pgrep", "-fl", f"user-data-dir={user_data_dir}"], capture_output=True, text=True)
    orphans = [line for line in result.stdout.splitlines() if line.strip()]
    launchd_result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    orphans += [
        f"launchd job: {line}" for line in launchd_result.stdout.splitlines()
        if "chrome.for.testing" in line.lower()
    ]
    return orphans


# Write the markdown report and return its path
def write_report(
    bundle_path: Path, reference: dict, self_launch_result: dict, cdp_http_check: dict,
    scrape_result: dict, self_cmdline: list[str] | None, cmdline_diff: dict,
    focus_samples: list[tuple[str, str]], orphans: list[str],
) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"05_cdp_headed_probe_{ts}.md"
    crawl4ai_version = importlib.metadata.version("crawl4ai")
    patchright_version = importlib.metadata.version("patchright")
    stage_breakdown = stage_focus_breakdown(focus_samples)
    route_apps = [app for stage_name, app in focus_samples if stage_name in ROUTE_STAGES]
    route_total = len(route_apps)
    route_chrome = sum(1 for app in route_apps if "chrome" in app.lower())

    lines = [
        f"# CDP Headed Probe (Milestone 1b) — {ts}",
        "",
        f"Dev-only probe (macOS). `crawl4ai=={crawl4ai_version}`, `patchright=={patchright_version}`. "
        f"Bundle: `{bundle_path}`.",
        "",
        "## 1. Self-launch + CDP endpoint",
        "",
        f"- `open -g -n -a` launch issued: {self_launch_result['launched']}",
        f"- Error (if any): {self_launch_result['error'] or 'none'}",
        f"- CDP HTTP `/json/version` reachable: {cdp_http_check['ready']}",
        f"- Detail: {cdp_http_check['detail']}",
        "",
        "## 2. crawl4ai connect + scrape over cdp_url",
        "",
        "Config shape used: `BrowserConfig(cdp_url=f\"http://127.0.0.1:{port}\", "
        "browser_mode=\"custom\", enable_stealth=True, cdp_cleanup_on_close=True)` + "
        "`UndetectedAdapter()` + `AsyncPlaywrightCrawlerStrategy`. `headless` field is DEAD on this "
        "path (never read inside `browser_manager.py`'s `cdp_url` branch — confirmed by reading the "
        "source, not just inferred) — headed-ness comes entirely from how we spawned the process.",
        "",
        f"- Scrape success: {scrape_result['success']}",
        f"- Content length: {scrape_result['content_len']}",
        f"- Error (if any): {scrape_result['error'] or 'none'}",
        "",
        "## 3. Focus poll (whole sequence: self-launch -> connect -> page creation -> navigation -> teardown)",
        "",
        "**Headline figure is the ROUTE UNDER TEST ONLY** (`self_launch` + `cdp_port_wait` + "
        "`cdp_connect_page_navigate` + `teardown`) — EXCLUDES `reference_launch`, which is this "
        "script's own internal tooling step (a direct, un-backgrounded patchright launch captured "
        "only for the cmdline diff in section 4, not part of the cdp_url route and not expected to "
        "avoid focus steal — folding it into the headline would misrepresent the route being tested):",
        "",
        f"- Route samples: {route_total}",
        f"- Route Chrome-frontmost count: {route_chrome} ({pct(route_chrome, route_total)})",
        f"- Distinct apps seen (whole run, all stages): {sorted({app for _, app in focus_samples})}",
        "",
        "**Per-stage breakdown** (attributes any Chrome-frontmost hit to WHICH step caused it — "
        "`cdp_connect_page_navigate` bundles connect/`get_page()`/goto, the page-creation-over-CDP "
        "moment playwright#42343 flags; finer sub-staging inside it would require hooking crawl4ai "
        "internals, out of scope here). A stage showing 0 samples means it completed faster than "
        "the 0.25s poll interval — NOT that it was confirmed focus-clean, just unsampled. Table "
        "order is thematic (route stages grouped first), NOT chronological — `reference_launch` "
        "actually runs FIRST in real execution, before any route stage:",
        "",
        "| Stage | in route? | samples | chrome frontmost | % |",
        "|-------|-----------|---------|-------------------|---|",
    ]
    for stage_name, total, chrome_count in stage_breakdown:
        in_route = "yes" if stage_name in ROUTE_STAGES else "NO (reference/tooling)"
        lines.append(f"| {stage_name} | {in_route} | {total} | {chrome_count} | {pct(chrome_count, total)} |")
    lines += [
        "",
        "## 4. cmdline delta vs. patchright reference (headed, probe 04 Run B shape)",
        "",
        f"- Reference launch error: {reference['error'] or 'none'}",
        f"- Reference PID/exe: {reference['pid']} / `{reference['exe']}`",
        f"- Self-launch cmdline captured: {self_cmdline is not None}",
    ]
    if cmdline_diff.get("comparable"):
        lines += [
            f"- Flags common to both: {cmdline_diff['common_count']}",
            f"- **Only in reference (patchright-owned surface we would NOT get on this route):** "
            f"{cmdline_diff['only_in_reference']}",
            f"- Only in self-launch (ours, not patchright's): {cmdline_diff['only_in_self']}",
        ]
    else:
        lines.append("- Not comparable — one of the two cmdlines was not captured.")

    lines += [
        "",
        "## Teardown",
        "",
        f"Orphan processes/launchd jobs after the full probe: {len(orphans)}",
    ]
    if orphans:
        lines.append("")
        lines.extend(f"    {o}" for o in orphans)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# (stage, total_samples, chrome_frontmost_count) per stage, canonical order (ROUTE_STAGES then
# REFERENCE_STAGE) — includes stages with 0 samples explicitly, so a fast stage that the 0.25s poll
# never caught is visibly "0 samples" rather than silently absent from the table
def stage_focus_breakdown(focus_samples: list[tuple[str, str]]) -> list[tuple[str, int, int]]:
    totals: dict[str, int] = {s: 0 for s in [*ROUTE_STAGES, REFERENCE_STAGE]}
    chrome_counts: dict[str, int] = {s: 0 for s in [*ROUTE_STAGES, REFERENCE_STAGE]}
    for stage_name, app in focus_samples:
        totals.setdefault(stage_name, 0)
        chrome_counts.setdefault(stage_name, 0)
        totals[stage_name] += 1
        if "chrome" in app.lower():
            chrome_counts[stage_name] += 1
    order = [*ROUTE_STAGES, REFERENCE_STAGE]
    order += [s for s in totals if s not in order]
    return [(s, totals[s], chrome_counts[s]) for s in order]


# Percent helper, "n/a" on an empty denominator
def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{round(100 * count / total)}%"


if __name__ == "__main__":
    asyncio.run(run_probe())
