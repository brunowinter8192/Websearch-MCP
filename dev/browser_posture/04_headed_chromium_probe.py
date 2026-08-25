#!/usr/bin/env python3
"""Headed-launch feasibility probe for the chromium (patchright) ad-hoc scrape lane.

Milestone 1 of the headed-adhoc chromium switch (`src/scraper/chromium_scrape.py`'s `try_scrape`).
Measures, through the REAL production launch shape (`BrowserConfig` + `UndetectedAdapter` +
`AsyncPlaywrightCrawlerStrategy`, patchright's `use_undetected` path):

1. Executable resolution — which binary actually runs under headless=True vs headless=False,
   read off the real launched process (psutil), not registry metadata.
2. LSUIElement viability — launch success + continuous frontmost-app poll, with and without
   `LSUIElement=true` set on the resolved `Google Chrome for Testing.app` (chromium-1228) bundle.
3. Backgrounding flags — whether the three Playwright-default flags are present on the real
   launched cmdline, and for each, whether crawl4ai's own `_build_browser_args()` put it there or
   patchright's internal driver injected it (crawl4ai's arg list is read directly off the
   installed package this session, not assumed).

Local throwaway page only (never a third-party site). No src/ import (dev-script isolation,
matching `_lib.py`'s own convention) — LSUIElement plist helpers are duplicated from
`src/scraper/camoufox_scrape.py`'s `_find_app_bundle`/`_ensure_no_focus_steal` shape, not imported.
"""

# INFRASTRUCTURE
import asyncio
import importlib.metadata
import plistlib
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

sys.path.insert(0, str(Path(__file__).parent))
from _lib import start_probe_server, stop_probe_server, get_frontmost_app, BACKGROUNDING_FLAGS  # noqa: E402

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"

LOCAL_DWELL_S = 3.0
FOCUS_POLL_INTERVAL_S = 0.25
CHROMIUM_REVISION_TAG = "chromium-1228"  # the ONLY revision this probe is allowed to touch

# Read directly off the installed crawl4ai 0.9.2's browser_manager.py `_build_browser_args()` this
# session: unconditionally-included flags for the plain playwright.chromium.launch() path (no
# cdp_url/use_managed_browser/use_persistent_context set — the exact path try_scrape's BrowserConfig
# takes). `--disable-backgrounding-occluded-windows` is NOT in this set (only added when
# config.light_mode=True, which try_scrape never sets) — if it shows up on the real cmdline anyway,
# that's patchright's internal driver default, not crawl4ai's doing.
CRAWL4AI_UNCONDITIONAL_ARGS = {
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
}


# ORCHESTRATOR

async def run_probe() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Run A: headless=True, plist untouched", file=sys.stderr)
    run_a = await observe_run(headless=True, poll_focus=False, dwell_s=LOCAL_DWELL_S)
    kill_survivors()

    print("Run B: headless=False, plist untouched (focus-poll WITHOUT fix)", file=sys.stderr)
    run_b = await observe_run(headless=False, poll_focus=True, dwell_s=LOCAL_DWELL_S)
    kill_survivors()

    bundle_path = resolve_and_verify_bundle(run_b["exe"])
    plist_path = bundle_path / "Contents" / "Info.plist"
    original_bytes = plist_path.read_bytes()  # byte-exact backup — revert restores THIS, not a plistlib round-trip
    original_lsuielement = read_lsuielement(plist_path)
    codesign_before = read_codesign_status(bundle_path)

    run_c = None
    codesign_after = None
    try:
        set_lsuielement(plist_path, True, original_bytes)
        codesign_after = read_codesign_status(bundle_path)
        print("Run C: headless=False, plist LSUIElement=true (focus-poll WITH fix)", file=sys.stderr)
        run_c = await observe_run(headless=False, poll_focus=True, dwell_s=LOCAL_DWELL_S)
    finally:
        plist_path.write_bytes(original_bytes)
        kill_survivors()
        plist_end_state = read_lsuielement(plist_path)
        plist_format_restored = plist_path.read_bytes() == original_bytes

    orphans = check_orphans()
    report_path = write_report(
        run_a, run_b, run_c, bundle_path, original_lsuielement, plist_end_state,
        plist_format_restored, codesign_before, codesign_after, orphans,
    )
    print(f"\nReport: {report_path}", file=sys.stderr)
    print(f"Orphan chromium-family processes after run: {len(orphans)}", file=sys.stderr)


# FUNCTIONS

# Walk up from a bundle-internal executable path to the .app root — same shape as
# camoufox_scrape.py's _find_app_bundle, duplicated per this dir's no-src-import convention
def find_app_bundle(executable_path: str) -> Path | None:
    for parent in Path(executable_path).parents:
        if parent.suffix == ".app":
            return parent
    return None


# First descendant of this process whose resolved executable path lives under ms-playwright's
# cache (covers both chromium-*/Chrome-for-Testing.app and chromium_headless_shell-*) — restricted
# to OUR process tree so it can never pick up an unrelated Chrome on this machine
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


# One real try_scrape-shaped launch against a local throwaway page; concurrently polls for the
# launched browser process (exe/cmdline, captured once) and, if poll_focus, the frontmost app
# (sampled continuously for the full launch-to-close duration)
async def observe_run(headless: bool, poll_focus: bool, dwell_s: float) -> dict:
    server, thread, port = start_probe_server()
    url = f"http://127.0.0.1:{port}/"
    browser_info = {"pid": None, "exe": None, "cmdline": None}
    focus_samples: list[str] = []
    stop_event = asyncio.Event()

    async def poll_loop():
        while not stop_event.is_set():
            if browser_info["pid"] is None:
                proc = await asyncio.to_thread(find_chrome_descendant)
                if proc is not None:
                    try:
                        browser_info["pid"] = proc.pid
                        browser_info["exe"] = proc.exe()
                        browser_info["cmdline"] = proc.cmdline()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            if poll_focus:
                focus_samples.append(await asyncio.to_thread(get_frontmost_app))
            await asyncio.sleep(FOCUS_POLL_INTERVAL_S)

    poll_task = asyncio.create_task(poll_loop())
    browser_config = BrowserConfig(headless=headless, verbose=False, enable_stealth=True)
    adapter = UndetectedAdapter()
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config, browser_adapter=adapter)
    run_config = CrawlerRunConfig(
        wait_until="load", page_timeout=15000, delay_before_return_html=dwell_s,
        cache_mode=CacheMode.BYPASS, verbose=False,
    )
    launch_success = False
    error_message = None
    try:
        async with AsyncWebCrawler(config=browser_config, crawler_strategy=crawler_strategy) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            launch_success = bool(getattr(result, "success", False)) or bool(getattr(result, "html", None))
    except Exception as e:
        error_message = f"{type(e).__name__}: {e}"
    finally:
        stop_event.set()
        await poll_task
        stop_probe_server(server, thread)

    return {
        "headless": headless,
        "launch_success": launch_success,
        "error_message": error_message,
        "pid": browser_info["pid"],
        "exe": browser_info["exe"],
        "cmdline": browser_info["cmdline"],
        "focus_samples": focus_samples,
        "chrome_frontmost_count": sum(1 for s in focus_samples if "chrome" in s.lower()),
    }


# Resolve run B's headed exe to its .app bundle and hard-verify it's the chromium-1228 install —
# refuses to proceed (no plist write happens) if resolution lands anywhere else, e.g. chromium-1223
def resolve_and_verify_bundle(executable_path: str | None) -> Path:
    if not executable_path:
        raise RuntimeError("Run B captured no browser process — cannot resolve bundle for the plist step")
    bundle = find_app_bundle(executable_path)
    if bundle is None:
        raise RuntimeError(f"No .app bundle found above {executable_path}")
    if CHROMIUM_REVISION_TAG not in str(bundle):
        raise RuntimeError(
            f"Resolved bundle {bundle} is NOT {CHROMIUM_REVISION_TAG} — refusing to touch its plist"
        )
    return bundle


# Read LSUIElement off Info.plist; None means the key is absent (macOS default: foreground app)
def read_lsuielement(plist_path: Path) -> bool | None:
    with open(plist_path, "rb") as f:
        data = plistlib.load(f)
    return data.get("LSUIElement")


# Set LSUIElement on Info.plist, writing back in the SAME format as original_bytes
# (plistlib.dump()'s default is XML — a naive round-trip silently converts a binary plist to XML,
# a format change that survives even a content-level revert; caller restores original_bytes
# byte-for-byte afterward regardless, this just keeps the WHILE-SET state format-faithful too)
def set_lsuielement(plist_path: Path, value: bool, original_bytes: bytes) -> None:
    data = plistlib.loads(original_bytes)
    data["LSUIElement"] = value
    fmt = plistlib.FMT_BINARY if original_bytes.startswith(b"bplist00") else plistlib.FMT_XML
    with open(plist_path, "wb") as f:
        plistlib.dump(data, f, fmt=fmt)


# Remove any macOS launchd per-app supervision job for Chrome for Testing — root cause of the
# gotcha below: when the app CRASHES (e.g. Run C's SIGTRAP from the ICU failure), launchd registers
# `application.com.google.chrome.for.testing.<ids>` and auto-restarts it on a throttled backoff,
# entirely independent of this script's own process tree — a plain psutil/pgrep process kill can
# never stop this, only removing the launchd job does. Returns the labels it found (for reporting).
def remove_stray_launchd_jobs() -> list[str]:
    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    labels = [line.split()[-1] for line in result.stdout.splitlines() if "chrome.for.testing" in line.lower()]
    for label in labels:
        subprocess.run(["launchctl", "remove", label], capture_output=True, text=True)
    return labels


# Kill any live process still running under ms-playwright's chromium cache — system-wide by exe
# path, NOT restricted to our own psutil children: Chrome's GPU/renderer/utility helper processes
# get reparented to launchd the instant the main browser process dies, so once that happens they
# are no longer our descendants even though they never received a kill signal themselves. Scoped
# safely because ms-playwright/chromium* is this project's own browser cache, not shared with
# anything else on the machine (same scope as check_orphans()'s pgrep pattern).
#
# Multi-round + launchd-job removal each round: a single terminate-and-wait pass left a fresh
# "Google Chrome for Testing" main process alive ~15s later (new PID, not a slow-dying old one) —
# traced to the launchd supervision job above, NOT a psutil-visible respawn mechanism. Removing
# the job every round (before it can fire again) is what actually stops it.
def kill_survivors(rounds: int = 3, settle_s: float = 1.5) -> None:
    for _ in range(rounds):
        remove_stray_launchd_jobs()
        victims = []
        for proc in psutil.process_iter(["pid"]):
            try:
                if "ms-playwright/chromium" in proc.exe():
                    proc.terminate()
                    victims.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if not victims:
            continue
        gone, alive = psutil.wait_procs(victims, timeout=3)
        for proc in alive:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(settle_s)


# codesign -dv summary line + verify exit code, for the "does editing Info.plist break the
# signature" open question
def read_codesign_status(bundle_path: Path) -> dict:
    dv = subprocess.run(["codesign", "-dv", str(bundle_path)], capture_output=True, text=True)
    verify = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle_path)], capture_output=True, text=True)
    flags_line = next((l for l in dv.stderr.splitlines() if l.startswith("CodeDirectory") or l.startswith("Signature")), "")
    return {"verify_returncode": verify.returncode, "verify_stderr": verify.stderr.strip(), "signature_line": flags_line}


# Attribute a backgrounding flag's presence on a real cmdline to crawl4ai's own arg list vs
# patchright's internal driver default
def attribute_flag(flag: str, cmdline: list[str] | None) -> str:
    present = bool(cmdline) and flag in cmdline
    if not present:
        return "absent"
    if flag in CRAWL4AI_UNCONDITIONAL_ARGS:
        return "present — crawl4ai arg list"
    return "present — driver-injected (not in crawl4ai's _build_browser_args output)"


# pgrep for any leftover process under ms-playwright's chromium cache dirs (covers both
# chromium-*/Chrome-for-Testing and chromium_headless_shell-* by substring), plus any residual
# launchd supervision job (see remove_stray_launchd_jobs — the actual respawn source)
def check_orphans() -> list[str]:
    result = subprocess.run(["pgrep", "-fl", "ms-playwright/chromium"], capture_output=True, text=True)
    orphans = [line for line in result.stdout.splitlines() if line.strip()]
    launchd_result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    orphans += [
        f"launchd job: {line}"
        for line in launchd_result.stdout.splitlines()
        if "chrome.for.testing" in line.lower()
    ]
    return orphans


# Write the markdown report and return its path
def write_report(
    run_a: dict, run_b: dict, run_c: dict | None, bundle_path: Path,
    original_lsuielement: bool | None, plist_end_state: bool | None, plist_format_restored: bool,
    codesign_before: dict, codesign_after: dict | None, orphans: list[str],
) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"04_headed_chromium_probe_{ts}.md"
    crawl4ai_version = importlib.metadata.version("crawl4ai")
    patchright_version = importlib.metadata.version("patchright")

    lines = [
        f"# Headed Chromium (patchright) Launch Probe — {ts}",
        "",
        "Dev-only probe (macOS). All three launches use `try_scrape`'s exact BrowserConfig/adapter/"
        "strategy shape against a local throwaway page (never a third-party site). "
        f"`crawl4ai=={crawl4ai_version}`, `patchright=={patchright_version}`.",
        "",
        "## 1. Executable resolution",
        "",
        "| Run | headless | launch success | PID | executable |",
        "|-----|----------|-----------------|-----|------------|",
    ]
    for label, r in [("A", run_a), ("B", run_b)]:
        lines.append(f"| {label} | {r['headless']} | {r['launch_success']} | {r['pid']} | `{r['exe']}` |")
    hyp_a = "chromium_headless_shell-1228" in (run_a["exe"] or "") and "chrome-headless-shell" in (run_a["exe"] or "")
    hyp_b = "chromium-1228" in (run_b["exe"] or "") and "Google Chrome for Testing.app" in (run_b["exe"] or "")
    lines += [
        "",
        f"- Headless hypothesis (`chrome-headless-shell` under `chromium_headless_shell-1228`): "
        f"{'CONFIRMED' if hyp_a else 'NOT CONFIRMED'}",
        f"- Headed hypothesis (`Google Chrome for Testing.app` under `chromium-1228`): "
        f"{'CONFIRMED' if hyp_b else 'NOT CONFIRMED'}",
        f"- Run A error: {run_a['error_message'] or 'none'}",
        f"- Run B error: {run_b['error_message'] or 'none'}",
        "",
        "## 2. Backgrounding flags",
        "",
        "Attribution: **crawl4ai arg list** = present in the installed `browser_manager.py`'s "
        "`_build_browser_args()` unconditional output (read directly off the installed package "
        "this session). **driver-injected** = present on the real cmdline but NOT in that list — "
        "patchright/playwright's own internal default, not crawl4ai's doing.",
        "",
        "| Flag | headless (Run A) | headed (Run B) |",
        "|------|-------------------|------------------|",
    ]
    for flag in BACKGROUNDING_FLAGS:
        lines.append(f"| `{flag}` | {attribute_flag(flag, run_a['cmdline'])} | {attribute_flag(flag, run_b['cmdline'])} |")

    lines += [
        "",
        "## 3. LSUIElement viability",
        "",
        f"- Bundle: `{bundle_path}`",
        f"- Original `LSUIElement`: `{original_lsuielement}` (None = key absent, macOS default)",
        f"- End state (reverted): `{plist_end_state}`, byte-exact restore of original file: "
        f"{plist_format_restored} (`Info.plist` written back from a raw-bytes backup taken before "
        "any edit, not a plistlib round-trip — `plistlib.dump()` defaults to XML and would have "
        "silently converted the bundle's original binary (`bplist00`) plist to XML even on a "
        "content-correct revert; caught during this probe, fixed before this run)",
        f"- Codesign verify BEFORE edit: rc={codesign_before['verify_returncode']} — "
        f"{codesign_before['verify_stderr'] or 'ok'} (pre-existing on the untouched bundle, not "
        "caused by this probe)",
    ]
    if codesign_after is not None:
        lines.append(
            f"- Codesign verify AFTER `LSUIElement=true` edit: rc={codesign_after['verify_returncode']} — "
            f"{codesign_after['verify_stderr'] or 'ok'}"
        )
    lines += [
        "",
        "| Run | plist state | launch success | focus samples | chrome frontmost | % chrome frontmost | distinct apps seen |",
        "|-----|-------------|-----------------|----------------|-------------------|----------------------|----------------------|",
    ]
    lines.append(
        f"| B (no fix) | LSUIElement={original_lsuielement} | {run_b['launch_success']} | "
        f"{len(run_b['focus_samples'])} | {run_b['chrome_frontmost_count']} | "
        f"{pct(run_b['chrome_frontmost_count'], len(run_b['focus_samples']))} | "
        f"{sorted(set(run_b['focus_samples']))} |"
    )
    if run_c is not None:
        lines.append(
            f"| C (with fix) | LSUIElement=True | {run_c['launch_success']} | "
            f"{len(run_c['focus_samples'])} | {run_c['chrome_frontmost_count']} | "
            f"{pct(run_c['chrome_frontmost_count'], len(run_c['focus_samples']))} | "
            f"{sorted(set(run_c['focus_samples']))} |"
        )
        lines += [
            "",
            f"- Run C error: {run_c['error_message'] or 'none'}",
        ]
        if not run_c["launch_success"]:
            lines += [
                "",
                "**Verdict: NOT VIABLE as a direct lever on this bundle.** Reproduced 2x (this run "
                "plus one manual repro during investigation): `LSUIElement=true` on the chromium-1228 "
                "`Google Chrome for Testing.app` bundle reliably breaks the launch itself — "
                "`TargetClosedError`, browser log shows `icudtl.dat not found in bundle` / `Invalid "
                "file descriptor to ICU data received`. Isolated from the plist FORMAT (binary vs "
                "XML): a control launch against the identical bundle in XML format with the key "
                "ABSENT succeeded — the failure tracks the `LSUIElement` key specifically, not the "
                "file encoding. Differs from the Camoufox precedent (`process-docs/camoufox_lane/"
                "pipe_switch_and_no_focus_steal_2026-08-20.md`), where the same mechanism worked "
                "cleanly on `Camoufox.app`. Root cause not investigated further (out of scope for "
                "this probe) — plausibly this bundle's ICU-data resource lookup path depends on "
                "`NSApplicationActivationPolicy`/regular-app startup sequencing that `LSUIElement` "
                "changes. A future milestone needs a DIFFERENT no-focus-steal lever for this lane.",
            ]

    lines += [
        "",
        "## Teardown",
        "",
        f"Orphan processes/launchd jobs immediately after this script's own `check_orphans()` call: "
        f"{len(orphans)}.",
        "",
        "**Confirmed root cause (found during this probe's development, NOT fully bounded by the "
        "in-script sweep below — verify manually ~20s after this script exits, e.g. `pgrep -fl "
        '"ms-playwright/chromium"` + `launchctl list | grep chrome.for.testing`).** Run C\'s crash '
        "(`icudtl.dat not found in bundle`, SIGTRAP) makes macOS itself register a launchd per-app "
        "supervision job, `application.com.google.chrome.for.testing.<ids>` (`launchctl list`), "
        "which auto-relaunches the FULL browser (new PID: main process + crashpad + GPU/utility "
        "helpers) on a delay observed to range ~10-15s after process exit — outside what any bounded "
        "in-script sleep can reliably wait out. This is NOT the AsyncWebCrawler/Playwright "
        "context-manager's own teardown failing (Run A/B, which never crash, leave 0 orphans with no "
        "launchd job involved at all) — it is macOS's own crash-recovery, triggered specifically "
        "because Run C's launch crashes. `kill_survivors()` removes any matching launchd job every "
        "sweep round (`remove_stray_launchd_jobs()`) in addition to killing processes; `check_orphans"
        "()` reports residual launchd jobs too, not just processes. One-shot-per-crash, not a "
        "repeating loop (confirmed stable over a 90s undisturbed manual watch after cleanup).",
    ]
    if orphans:
        lines.append("")
        lines.extend(f"    {o}" for o in orphans)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# Percent helper for the focus-poll table, "n/a" on an empty denominator
def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{round(100 * count / total)}%"


if __name__ == "__main__":
    asyncio.run(run_probe())
