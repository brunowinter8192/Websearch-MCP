#!/usr/bin/env python3
"""Google smoke test — self-contained, reads config.yml, no src/ imports."""

# INFRASTRUCTURE
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import yaml
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import PageCommands
from pydoll.commands.network_commands import NetworkCommands
from pydoll.protocol.network.types import CookieSameSite

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.yml"


# ORCHESTRATOR

async def run_smoke_test() -> None:
    cfg = load_config(CONFIG_PATH)
    queries = load_queries(SCRIPT_DIR / cfg["run"]["queries_file"])
    report_dir = (SCRIPT_DIR / cfg["report"]["output_dir"]).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    browser = await start_browser(cfg)
    records = []

    try:
        for qi, query in enumerate(queries):
            print(f"[{qi + 1}/{len(queries)}] {query}", file=sys.stderr)
            record = await run_query(browser, query, cfg)
            records.append(record)
            label = record["status"]
            count = record["count"]
            title = record["page_title"][:60]
            print(f"  → {label} | {count} results | title: {title!r}", file=sys.stderr)
            if qi < len(queries) - 1:
                await asyncio.sleep(cfg["run"]["delay_between_queries"])
    finally:
        await stop_browser(browser)

    report_path = write_report(records, report_dir)
    ok_count = sum(1 for r in records if r["status"] == "OK")
    non_ok = [r for r in records if r["status"] != "OK"]
    print(f"\nReport: {report_path}", file=sys.stderr)
    print(f"Result: {ok_count}/30 OK, {len(non_ok)}/30 non-OK ({_summarize_statuses(non_ok)})", file=sys.stderr)
    nav_times = [r["navigation_time_ms"] for r in records if r["navigation_time_ms"] > 0]
    dom_times = [r["dom_wait_time_ms"] for r in records if r["dom_wait_time_ms"] > 0]
    if nav_times:
        print(f"Timing: nav mean/max {int(sum(nav_times)/len(nav_times))}ms/{max(nav_times)}ms, dom mean/max {int(sum(dom_times)/len(dom_times))}ms/{max(dom_times)}ms", file=sys.stderr)


# FUNCTIONS

# Load and return parsed config.yml
def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# Load queries from file, one per line, skip blank lines
def load_queries(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


# Build ChromiumOptions from config
def _build_options(cfg: dict) -> ChromiumOptions:
    bc = cfg["browser"]
    sc = cfg["stealth"]
    prefs = sc["browser_preferences"]

    options = ChromiumOptions()
    options.headless = bc["headless"]
    options.add_argument(f"--user-data-dir={os.path.expanduser(bc['session_dir'])}")
    options.add_argument(f"--user-agent={bc['user_agent']}")
    options.add_argument(f"--window-size={bc['window_width']},{bc['window_height']}")
    options.add_argument(f"--binary-location={bc['binary']}")

    for feat in sc.get("disable_blink_features", []):
        options.add_argument(f"--disable-blink-features={feat}")
    if sc.get("webrtc_leak_protection"):
        options.webrtc_leak_protection = True
    if sc.get("block_popups"):
        options.block_popups = True
    if sc.get("block_notifications"):
        options.block_notifications = True

    options.browser_preferences = {
        "profile": {"exit_type": "Normal", "exited_cleanly": True},
        "safebrowsing": {"enabled": prefs.get("safebrowsing", True)},
        "autofill": {"enabled": prefs.get("autofill", True)},
        "search": {"suggest_enabled": prefs.get("search_suggest", True)},
        "enable_do_not_track": prefs.get("do_not_track", False),
        "credentials_enable_service": prefs.get("credentials", True),
        "credentials_enable_autosignin": prefs.get("credentials", True),
    }
    return options


# Build JS fingerprint patch string from config
def _build_js_patches(cfg: dict) -> str:
    patches = cfg["stealth"].get("js_patches", {})
    parts = []

    if patches.get("screen_dimensions"):
        w = cfg["browser"]["window_width"]
        h = cfg["browser"]["window_height"]
        parts.append(f"""(function() {{
    Object.defineProperty(screen, 'width', {{ get: () => {w} }});
    Object.defineProperty(screen, 'height', {{ get: () => {h} }});
    Object.defineProperty(screen, 'availWidth', {{ get: () => {w} }});
    Object.defineProperty(screen, 'availHeight', {{ get: () => {h - 23} }});
    Object.defineProperty(screen, 'colorDepth', {{ get: () => 30 }});
    Object.defineProperty(screen, 'pixelDepth', {{ get: () => 30 }});
}})();""")

    if patches.get("device_pixel_ratio"):
        parts.append("""(function() {
    Object.defineProperty(window, 'devicePixelRatio', { get: () => 2 });
})();""")

    if patches.get("outer_dimensions"):
        parts.append("""(function() {
    Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
    Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight + 85 });
})();""")

    if patches.get("css_active_text"):
        parts.append("""(function() {
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
})();""")

    return "\n\n".join(parts)


# Kill stale Chrome processes using the smoke session dir
def _kill_stale_chrome(session_dir: str) -> None:
    subprocess.run(
        ["pkill", "-f", f"user-data-dir={session_dir}"],
        capture_output=True,
    )


# Inject SOCS consent cookie via CDP to bypass Google consent page
async def _inject_consent_cookie(tab, cfg: dict) -> None:
    cookie = cfg["google"]["consent_cookie"]
    await tab._execute_command(NetworkCommands.set_cookie(
        name=cookie["name"],
        value=cookie["value"],
        domain=cookie["domain"],
        path=cookie["path"],
        secure=cookie["secure"],
        same_site=CookieSameSite.LAX,
    ))


# Start browser, apply fingerprint patches and consent cookie to initial tab
async def start_browser(cfg: dict) -> Chrome:
    session_dir = os.path.expanduser(cfg["browser"]["session_dir"])
    _kill_stale_chrome(session_dir)
    browser = Chrome(_build_options(cfg))
    tab = await browser.start()
    js = _build_js_patches(cfg)
    if js:
        await tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=js, run_immediately=True
            )
        )
    await _inject_consent_cookie(tab, cfg)
    await tab.close()
    return browser


# Stop browser cleanly
async def stop_browser(browser: Chrome) -> None:
    try:
        await browser.stop()
    except Exception:
        pass


# Run one query: navigate, detect, parse, return record dict
async def run_query(browser: Chrome, query: str, cfg: dict) -> dict:
    gc = cfg["google"]
    rc = cfg["run"]
    js_patches = _build_js_patches(cfg)

    tab = await browser.new_tab()
    if js_patches:
        await tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=js_patches, run_immediately=True
            )
        )
    await _inject_consent_cookie(tab, cfg)

    record = {
        "query": query,
        "count": 0,
        "domains": 0,
        "google_internal": 0,
        "page_title": "",
        "current_url": "",
        "status": "EMPTY",
        "sample_urls": [],
        "sample_titles": [],
        "navigation_time_ms": 0,
        "dom_wait_time_ms": 0,
    }

    try:
        search_url = gc["url_template"].format(
            query=quote_plus(query),
            hl=gc["hl"],
            num=gc["num"],
        )

        _t_nav = time.monotonic()
        await tab.go_to(search_url, timeout=rc["page_load_timeout"])
        record["navigation_time_ms"] = int((time.monotonic() - _t_nav) * 1000)
        current_url = await tab.current_url

        # Handle consent page — two variants:
        # (a) classic redirect to consent.google.com
        # (b) inline consent on the search URL (cookie banner without redirect)
        if gc["consent_domain"] in current_url or await _has_inline_consent(tab):
            await _handle_consent(tab, gc)
            await asyncio.sleep(rc["consent_settle"])
            await tab.go_to(search_url, timeout=rc["page_load_timeout"])
            current_url = await tab.current_url

        record["current_url"] = current_url

        # CAPTCHA check
        if gc["captcha_path"] in current_url:
            record["page_title"] = await _get_title(tab)
            record["status"] = "CAPTCHA"
            return record

        # Remaining consent check (shouldn't happen after handling)
        if gc["consent_domain"] in current_url:
            record["page_title"] = await _get_title(tab)
            record["status"] = "CONSENT"
            return record

        # Wait for results
        _t_dom = time.monotonic()
        found = await _wait_for_results(tab, gc)
        record["dom_wait_time_ms"] = int((time.monotonic() - _t_dom) * 1000)
        record["page_title"] = await _get_title(tab)

        if not found:
            record["status"] = _derive_status(0, 0, record["page_title"], current_url, gc)
            return record

        # Parse results
        results = await _parse_results(tab, gc)
        urls = [r["url"] for r in results]
        domains = {_extract_domain(u) for u in urls if u}
        google_internal = sum(1 for u in urls if _is_google_internal(u))

        record["count"] = len(results)
        record["domains"] = len(domains)
        record["google_internal"] = google_internal
        record["sample_urls"] = urls[:cfg["report"]["include_sample_urls"]]
        record["sample_titles"] = [r["title"] for r in results[:cfg["report"]["include_sample_urls"]]]
        record["status"] = _derive_status(
            len(results), len(domains), record["page_title"], current_url, gc
        )

    except Exception as e:
        print(f"    ERROR: {e}", file=sys.stderr)
        record["status"] = "ERROR"
        record["page_title"] = str(e)[:120]
    finally:
        try:
            await tab.close()
        except Exception:
            pass

    return record


# Detect inline consent banner (Google embeds cookie consent on search URL, no redirect)
async def _has_inline_consent(tab) -> bool:
    js = """
var body = document.body ? document.body.innerText : '';
return body.indexOf('Before you continue') !== -1 || body.indexOf('cookies and data') !== -1;
"""
    raw = await tab.execute_script(js)
    val = _extract_scalar(raw)
    return bool(val)


# Click Google consent accept button using fallback chain
async def _handle_consent(tab, gc: dict) -> None:
    buttons = gc["consent_buttons"]
    selector = ", ".join(buttons)
    js = f"""
var btn = document.querySelector({json.dumps(selector)});
if (btn) {{ btn.click(); return true; }}
return false;
"""
    await tab.execute_script(js)
    await asyncio.sleep(gc["wait_for_results"]["interval_seconds"] * 2)


# Poll for result containers, return True when found
async def _wait_for_results(tab, gc: dict) -> bool:
    js = gc["selectors"]["wait_js"]
    max_cycles = gc["wait_for_results"]["max_cycles"]
    interval = gc["wait_for_results"]["interval_seconds"]
    for _ in range(max_cycles):
        raw = await tab.execute_script(js)
        count = _extract_scalar(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(interval)
    return False


# Extract page title via JS
async def _get_title(tab) -> str:
    raw = await tab.execute_script("return document.title")
    return str(_extract_scalar(raw) or "")


# Parse result containers into list of {url, title, snippet}
async def _parse_results(tab, gc: dict) -> list[dict]:
    js = gc["selectors"]["parse_js"]
    raw = await tab.execute_script(js)
    value = _extract_scalar(raw)
    if not value or not isinstance(value, str):
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


# Derive status label from detection signals
def _derive_status(count: int, domains: int, title: str, url: str, gc: dict) -> str:
    captcha_path = gc["captcha_path"]
    consent_domain = gc["consent_domain"]
    if captcha_path in url:
        return "CAPTCHA"
    if consent_domain in url:
        return "CONSENT"
    if count == 0 and "Google Search" not in title:
        return "BLOCKED"
    if count == 0:
        return "EMPTY"
    if count >= 8 and domains >= 5:
        return "OK"
    return "SUSPECT"


# Extract primitive value from pydoll execute_script result
# pydoll returns Response[EvaluateResult]: {"id":..., "result": {"result": {"type":..., "value":...}}}
# So path is: response["result"]["result"]["value"]
def _extract_scalar(result):
    if result is None:
        return None
    if isinstance(result, (str, int, float, bool)):
        return result
    if isinstance(result, dict):
        # Path 1: response["result"]["result"]["value"]  (standard CDP Response wrapper)
        level1 = result.get("result")
        if isinstance(level1, dict):
            level2 = level1.get("result")
            if isinstance(level2, dict):
                v = level2.get("value")
                if v is not None:
                    return v
            # Path 2: response["result"]["value"]  (already unwrapped one level)
            v = level1.get("value")
            if v is not None:
                return v
        # Path 3: response["value"]  (fully unwrapped)
        v = result.get("value")
        if v is not None:
            return v
    return None


# Extract domain from URL
def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


# Check if URL is a Google-internal link (maps, images, etc.)
def _is_google_internal(url: str) -> bool:
    domain = _extract_domain(url)
    return "google." in domain


# Summarize non-OK status counts as a short string
def _summarize_statuses(records: list[dict]) -> str:
    from collections import Counter
    c = Counter(r["status"] for r in records)
    return ", ".join(f"{count}× {status}" for status, count in c.most_common())


# Write markdown report and return path
def write_report(records: list[dict], report_dir: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = report_dir / f"smoke_{ts}.md"

    lines = [
        f"# Google Smoke Test — {ts}",
        "",
        f"**Queries:** {len(records)}  ",
        f"**OK:** {sum(1 for r in records if r['status'] == 'OK')}  ",
        f"**Non-OK:** {sum(1 for r in records if r['status'] != 'OK')}",
        "",
        "## Overview",
        "",
        "| # | Query | Status | Count | Domains | Google-Internal | Nav ms | DOM ms | Page-Title | Sample-URL |",
        "|---|-------|--------|-------|---------|-----------------|--------|--------|------------|------------|",
    ]

    for i, r in enumerate(records, 1):
        query = r["query"][:50].replace("|", "\\|")
        status = r["status"]
        count = r["count"]
        domains = r["domains"]
        gint = r["google_internal"]
        nav_ms = r["navigation_time_ms"]
        dom_ms = r["dom_wait_time_ms"]
        title = r["page_title"][:50].replace("|", "\\|")
        sample = r["sample_urls"][0] if r["sample_urls"] else ""
        lines.append(f"| {i} | {query} | {status} | {count} | {domains} | {gint} | {nav_ms} | {dom_ms} | {title} | {sample} |")

    _nav = sorted(r["navigation_time_ms"] for r in records if r["navigation_time_ms"] > 0)
    _dom = sorted(r["dom_wait_time_ms"] for r in records if r["dom_wait_time_ms"] > 0)
    def _ms(lst, fn):
        return fn(lst) if lst else 0
    lines += [
        "",
        "## Timing Summary",
        "",
        "| Metric | Navigation (ms) | DOM-Wait (ms) |",
        "|--------|-----------------|---------------|",
        f"| Mean   | {_ms(_nav, lambda v: int(sum(v)/len(v)))} | {_ms(_dom, lambda v: int(sum(v)/len(v)))} |",
        f"| Median | {_ms(_nav, lambda v: v[len(v)//2])} | {_ms(_dom, lambda v: v[len(v)//2])} |",
        f"| Max    | {_ms(_nav, max)} | {_ms(_dom, max)} |",
        f"| p95    | {_ms(_nav, lambda v: v[min(int(len(v)*0.95), len(v)-1)])} | {_ms(_dom, lambda v: v[min(int(len(v)*0.95), len(v)-1)])} |",
    ]

    non_ok = [r for r in records if r["status"] != "OK"]
    if non_ok:
        lines += ["", "## Non-OK Details", ""]
        for r in non_ok:
            lines += [
                f"### [{r['status']}] {r['query']}",
                "",
                f"- **Status:** {r['status']}",
                f"- **Page title:** {r['page_title']}",
                f"- **Current URL:** {r['current_url']}",
                f"- **Result count:** {r['count']}",
                f"- **Unique domains:** {r['domains']}",
            ]
            if r["sample_urls"]:
                lines.append("- **Sample URLs:**")
                for url in r["sample_urls"]:
                    lines.append(f"  - {url}")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
