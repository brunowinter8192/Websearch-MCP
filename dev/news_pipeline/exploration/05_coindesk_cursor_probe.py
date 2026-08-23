#!/usr/bin/env python3
# INFRASTRUCTURE
import asyncio
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx
from pydoll.browser import Chrome

TARGET_URL = "https://www.coindesk.com/latest-crypto-news"
TIMELINE_API_PATH = "/api/v1/articles/timeline"
TIMELINE_BASE = "https://www.coindesk.com/api/v1/articles/timeline"
OUTPUT_DIR = Path(__file__).parent / "05_data"

TARGET_ID = "cc8f264d-ebd5-4749-ba09-63d771ba1df4"
CLICKS_TO_TRIGGER = 8
CALL_DELAY = 0.3

SKIP_HEADERS = frozenset({
    ":authority", ":method", ":path", ":scheme",
    "host", "content-length", "content-encoding", "transfer-encoding",
})

REAL_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.7680.154 Safari/537.36"
)

_JS_DISMISS_COOKIE = """
(function() {
    var btn = document.querySelector('#onetrust-accept-btn-handler');
    if (btn) { btn.click(); return 'clicked-accept'; }
    var sdk = document.getElementById('onetrust-consent-sdk');
    if (sdk) { sdk.remove(); return 'removed-sdk'; }
    return 'not-found';
})();
"""

_JS_CLICK_BTN = """
(function() {
    var candidates = Array.from(document.querySelectorAll('button, a[role="button"], [role="button"]'));
    for (var i = 0; i < candidates.length; i++) {
        var t = candidates[i].textContent.trim();
        if (/more\\s+stories|load\\s+more|show\\s+more/i.test(t)) {
            candidates[i].scrollIntoView({block: 'center', behavior: 'smooth'});
            candidates[i].click();
            return true;
        }
    }
    return false;
})();
"""


# ORCHESTRATOR

# Walk: paginate N calls logging ALL article storyTypes + identify TARGET_ID.
# Fixed: paginate N calls using fixed cursor (skip invalid storyType anchors).
async def cursor_probe_workflow(
    mode: str,
    n: int,
    invalid_types: frozenset,
    delay: float,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    port = get_free_port()
    session_dir = tempfile.mkdtemp(prefix="coindesk_cursor_")
    chrome = None
    tab = None

    try:
        print(f"[{mode}] Launching Chrome on port {port} …", file=sys.stderr)
        launch_background_chrome(port, session_dir)
        ws_url = wait_for_ws_url(port)
        chrome = Chrome()
        tab = await chrome.connect(ws_url)

        print(f"[{mode}] Navigating to {TARGET_URL} …", file=sys.stderr)
        await tab.go_to(TARGET_URL, timeout=60)
        await asyncio.sleep(3.0)

        raw = await tab.execute_script(_JS_DISMISS_COOKIE)
        print(f"[{mode}] Cookie consent: {_extract_value(raw)}", file=sys.stderr)
        await asyncio.sleep(0.5)

        print(f"[{mode}] Capturing timeline request ({CLICKS_TO_TRIGGER} clicks) …", file=sys.stderr)
        timeline_entry = await capture_timeline_request(tab, CLICKS_TO_TRIGGER)

        if timeline_entry is None:
            print("ERROR: Timeline API not found in HAR.", file=sys.stderr)
            return

        api_url = timeline_entry["request"]["url"]
        raw_hdrs = {h["name"]: h["value"] for h in timeline_entry["request"]["headers"]}
        headers = filter_headers(raw_hdrs)
        print(f"[{mode}] Captured URL: {api_url}", file=sys.stderr)

        first = httpx.get(api_url, headers=headers, follow_redirects=True, timeout=30)
        if first.status_code != 200:
            print(f"ERROR: First replay → {first.status_code}", file=sys.stderr)
            return

        print(f"[{mode}] First replay → 200 ({len(first.content)} bytes)", file=sys.stderr)

        if mode == "walk":
            results = storytype_walk(api_url, headers, first.content, n=n, delay=delay)
            rpath = OUTPUT_DIR / f"walk_{ts}.md"
            jpath = OUTPUT_DIR / f"walk_{ts}_articles.json"
            write_walk_report(rpath, jpath, ts, api_url, n, results)
            print(f"Walk report    → {rpath}")
            print(f"Articles JSON  → {jpath}")
        else:
            results = fixed_cursor_loop(
                api_url, headers, first.content,
                n=n, delay=delay, invalid_types=invalid_types,
            )
            rpath = OUTPUT_DIR / f"fixed_{ts}.md"
            write_fixed_report(rpath, ts, api_url, n, invalid_types, results)
            print(f"Fixed report   → {rpath}")

    finally:
        if tab:
            try:
                await tab.close()
            except Exception as e:
                print(f"tab.close (non-fatal): {e}", file=sys.stderr)
        if chrome:
            try:
                await chrome.close()
            except Exception as e:
                print(f"chrome.close (non-fatal): {e}", file=sys.stderr)
        kill_chrome_on_port(port)
        shutil.rmtree(session_dir, ignore_errors=True)
        print(f"[{mode}] Cleanup done.", file=sys.stderr)


# FUNCTIONS

# Bind port 0 to get a free OS-assigned port
def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# Launch Chrome in background via open -gna (new instance, no foreground)
def launch_background_chrome(port: int, session_dir: str) -> None:
    subprocess.run(
        [
            "open", "-gna", "Google Chrome", "--args",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={session_dir}",
            f"--user-agent={REAL_UA}",
            "--window-size=1920,1080",
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        check=True,
    )


# Poll /json/version until Chrome responds; return webSocketDebuggerUrl
def wait_for_ws_url(port: int, timeout: float = 30.0) -> str:
    url = f"http://localhost:{port}/json/version"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return json.loads(r.read())["webSocketDebuggerUrl"]
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"Chrome not ready on port {port}")


# Kill the Chrome process bound to this debug port
def kill_chrome_on_port(port: int) -> None:
    subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"], check=False)


# Unpack CDP execute_script result dict
def _extract_value(raw):
    try:
        return raw["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Click More-stories n times under HAR record; return first HAR entry matching TIMELINE_API_PATH
async def capture_timeline_request(tab, n_clicks: int) -> dict | None:
    async with tab.request.record() as capture:
        for i in range(n_clicks):
            raw = await tab.execute_script(_JS_CLICK_BTN)
            clicked = bool(_extract_value(raw))
            print(f"  click {i + 1}/{n_clicks}: {'OK' if clicked else 'miss'}", file=sys.stderr)
            await asyncio.sleep(2.5)
    for entry in capture.entries:
        if TIMELINE_API_PATH in entry["request"]["url"]:
            return entry
    return None


# Strip HTTP/2 pseudo-headers and client-managed headers
def filter_headers(raw: dict) -> dict:
    return {k: v for k, v in raw.items() if k.lower() not in SKIP_HEADERS}


# Parse all articles from response body; return list of metadata dicts
def parse_articles(body: bytes) -> list:
    try:
        data = json.loads(body)
    except Exception:
        return []
    articles = data if isinstance(data, list) else None
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                articles = v
                break
    if not articles:
        return []
    result = []
    for a in articles:
        ad = a.get("articleDates") or {}
        result.append({
            "_id": a.get("_id") or a.get("id"),
            "storyType": a.get("storyType"),
            "pathname": a.get("pathname"),
            "title": (a.get("title") or a.get("headline") or "")[:80],
            "displayDate": (
                ad.get("displayDate") or ad.get("publishedAt")
                or a.get("displayDate") or a.get("publishedAt") or a.get("date")
            ),
        })
    return result


# Standard cursor: last article's _id + displayDate
def extract_cursor_std(articles: list) -> tuple:
    if not articles:
        return None, None
    last = articles[-1]
    return last.get("_id"), last.get("displayDate")


# Fixed cursor: scan backward to find last article NOT in invalid_types
def extract_cursor_fixed(articles: list, invalid_types: frozenset) -> tuple:
    for a in reversed(articles):
        st = a.get("storyType") or ""
        if st not in invalid_types:
            aid = a.get("_id")
            adate = a.get("displayDate")
            if aid and adate:
                return aid, adate
    return extract_cursor_std(articles)


# Build cursor URL from lastId + lastDisplayDate
def build_cursor_url(last_id: str, last_date: str) -> str:
    return f"{TIMELINE_BASE}?size=16&lastId={last_id}&lastDisplayDate={last_date}&lang=en"


# Paginate n calls logging ALL article metadata per call; detect TARGET_ID; report storyType distribution
def storytype_walk(first_url: str, headers: dict, first_body: bytes, n: int, delay: float) -> dict:
    all_articles: list = []
    call_log: list = []
    body = first_body
    url = first_url
    target_article = None

    for call_num in range(n + 1):
        articles = parse_articles(body)
        if not articles:
            call_log.append({"call": call_num, "error": "no articles parsed from body"})
            break

        for a in articles:
            if a.get("_id") == TARGET_ID:
                target_article = a

        call_log.append({
            "call": call_num,
            "status": 200,
            "count": len(articles),
            "newest": (articles[0].get("displayDate") or "")[:19],
            "oldest": (articles[-1].get("displayDate") or "")[:19],
            "target_in_call": any(a.get("_id") == TARGET_ID for a in articles),
        })
        all_articles.extend(articles)

        if call_num >= n:
            break

        last_id, last_date = extract_cursor_std(articles)
        if not last_id or not last_date:
            call_log.append({"call": call_num + 1, "error": "cursor extraction failed"})
            break

        next_url = build_cursor_url(last_id, last_date)
        time.sleep(delay)

        t0 = time.monotonic()
        resp = httpx.get(next_url, headers=headers, follow_redirects=True, timeout=30)
        elapsed = round(time.monotonic() - t0, 2)

        print(
            f"  call {call_num + 1}: {resp.status_code} ({elapsed}s)"
            f" pivot={last_date[:10]} storyType={articles[-1].get('storyType')}",
            file=sys.stderr,
        )

        if resp.status_code != 200:
            last_art = articles[-1]
            call_log.append({
                "call": call_num + 1,
                "status": resp.status_code,
                "url": next_url,
                "elapsed": elapsed,
                "cursor_source": {
                    "_id": last_art.get("_id"),
                    "storyType": last_art.get("storyType"),
                    "displayDate": last_art.get("displayDate"),
                    "title": last_art.get("title"),
                    "pathname": last_art.get("pathname"),
                },
                "body_snippet": resp.content[:400].decode("utf-8", errors="replace"),
            })
            break

        body = resp.content
        url = next_url

    type_dist = dict(Counter(
        a.get("storyType") or "NULL" for a in all_articles
    ).most_common())

    return {
        "call_log": call_log,
        "all_articles": all_articles,
        "type_distribution": type_dist,
        "total_articles": len(all_articles),
        "target_article": target_article,
    }


# Paginate n calls using fixed cursor that skips invalid storyType anchors
def fixed_cursor_loop(
    first_url: str,
    headers: dict,
    first_body: bytes,
    n: int,
    delay: float,
    invalid_types: frozenset,
) -> list:
    results: list = []
    body = first_body
    total_articles = 0
    oldest_date: str | None = None

    for i in range(n):
        articles = parse_articles(body)
        if not articles:
            results.append({"call": i + 1, "error": "no articles in body"})
            break

        last_id, last_date = extract_cursor_fixed(articles, invalid_types)
        std_id, _ = extract_cursor_std(articles)
        cursor_overridden = (last_id != std_id)

        if not last_id or not last_date:
            results.append({"call": i + 1, "error": "no valid cursor found after filtering"})
            break

        next_url = build_cursor_url(last_id, last_date)

        if i > 0:
            time.sleep(delay)

        t0 = time.monotonic()
        resp = httpx.get(next_url, headers=headers, follow_redirects=True, timeout=30)
        elapsed = round(time.monotonic() - t0, 2)

        anchor_art = next((a for a in reversed(articles) if a.get("_id") == last_id), articles[-1])
        anchor_type = anchor_art.get("storyType")
        skipped_type = articles[-1].get("storyType") if cursor_overridden else None

        next_articles = parse_articles(resp.content) if resp.status_code == 200 else []
        n_arts = len(next_articles)
        total_articles += n_arts

        if last_date and (oldest_date is None or last_date < oldest_date):
            oldest_date = last_date

        print(
            f"  fixed call {i + 1}: {resp.status_code} ({elapsed}s)"
            f" anchor_type={anchor_type}"
            + (f" [FIXED skipped={skipped_type}]" if cursor_overridden else "")
            + f" oldest={last_date[:10]}",
            file=sys.stderr,
        )

        row = {
            "call": i + 1,
            "status": resp.status_code,
            "elapsed": elapsed,
            "articles": n_arts,
            "anchor_id": last_id,
            "anchor_storyType": anchor_type,
            "cursor_fixed": cursor_overridden,
            "skipped_storyType": skipped_type,
            "oldest_so_far": last_date[:10],
        }

        if resp.status_code != 200:
            row["body_snippet"] = resp.content[:400].decode("utf-8", errors="replace")
            results.append(row)
            break

        results.append(row)
        body = resp.content

    ok_rows = [r for r in results if r.get("status") == 200]
    elapsed_vals = [r["elapsed"] for r in ok_rows if "elapsed" in r]
    results.append({
        "call": "SUMMARY",
        "total_calls": len(ok_rows),
        "total_articles": total_articles,
        "oldest_date": oldest_date[:10] if oldest_date else None,
        "avg_elapsed": round(sum(elapsed_vals) / len(elapsed_vals), 3) if elapsed_vals else None,
        "cursor_fixed_count": sum(1 for r in results if r.get("cursor_fixed")),
        "non_200": sum(
            1 for r in results if isinstance(r.get("call"), int) and r.get("status") != 200
        ),
    })

    return results


# Write walk report (MD) and per-article JSON dump
def write_walk_report(report_path: Path, articles_path: Path, ts: str, api_url: str, n: int, results: dict) -> None:
    lines = ["# CoinDesk StoryType Walk Report"]
    lines.append(f"\n**Run:** {ts} | **Max calls:** {n}\n")
    lines.append(f"**Start URL:** `{api_url}`\n")
    lines.append(f"**Total articles logged:** {results['total_articles']}\n")

    lines.append("## StoryType Distribution\n")
    lines.append("| storyType | Count | % |")
    lines.append("|-----------|-------|---|")
    total = results["total_articles"]
    for st, cnt in results["type_distribution"].items():
        pct = round(cnt / total * 100, 1) if total else 0
        lines.append(f"| `{st}` | {cnt} | {pct}% |")

    lines.append("\n## Target Article (cc8f264d)\n")
    target = results.get("target_article")
    if target:
        lines.append("✅ **FOUND**\n")
        lines.append("```json")
        lines.append(json.dumps(target, indent=2, ensure_ascii=False))
        lines.append("```\n")
    else:
        lines.append("⚠️ TARGET NOT ENCOUNTERED in walk responses.\n")

    lines.append("## Call Log\n")
    lines.append("| Call | Status | Count | Newest | Oldest | Target? | Elapsed |")
    lines.append("|------|--------|-------|--------|--------|---------|---------|")
    for r in results["call_log"]:
        if "error" in r and "status" not in r:
            lines.append(f"| {r['call']} | ERROR | — | — | — | {r['error']} | — |")
            continue
        if r.get("status", 200) != 200:
            flag = "✅ **TARGET**" if r.get("target_in_call") else "—"
            lines.append(
                f"| {r['call']} | **{r['status']}** | — | — |"
                f" {r.get('oldest','')[:10]} | {flag} | {r.get('elapsed','?')}s |"
            )
            cs = r.get("cursor_source", {})
            if cs:
                lines.append(f"\n**403 cursor source:**")
                lines.append(f"- `_id`: `{cs.get('_id')}`")
                lines.append(f"- `storyType`: `{cs.get('storyType')}`")
                lines.append(f"- `displayDate`: {cs.get('displayDate')}")
                lines.append(f"- `pathname`: {cs.get('pathname')}")
                lines.append(f"- `title`: {cs.get('title')}")
            snip = r.get("body_snippet", "")
            if snip:
                lines.append(f"\n**403 body snippet:**\n```\n{snip}\n```\n")
        else:
            flag = "✅ **TARGET**" if r.get("target_in_call") else "—"
            lines.append(
                f"| {r['call']} | 200 | {r.get('count','—')} |"
                f" {r.get('newest','')[:10]} | {r.get('oldest','')[:10]} |"
                f" {flag} | {r.get('elapsed','?')}s |"
            )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    articles_path.write_text(
        json.dumps(results["all_articles"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# Write fixed-cursor loop report (MD)
def write_fixed_report(
    report_path: Path,
    ts: str,
    api_url: str,
    n: int,
    invalid_types: frozenset,
    results: list,
) -> None:
    lines = ["# CoinDesk Fixed Cursor Loop Report"]
    lines.append(f"\n**Run:** {ts} | **Max calls:** {n}\n")
    lines.append(f"**Start URL:** `{api_url}`\n")
    lines.append(f"**Invalid anchor types (skipped):** `{sorted(invalid_types) or '(none)'}`\n")

    summary = next((r for r in results if r.get("call") == "SUMMARY"), None)
    if summary:
        lines.append("## Summary\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Successful calls | {summary['total_calls']} |")
        lines.append(f"| Total articles | {summary['total_articles']} |")
        lines.append(f"| Oldest date reached | {summary['oldest_date']} |")
        lines.append(f"| Avg elapsed / call | {summary['avg_elapsed']}s |")
        lines.append(f"| Cursor-fix overrides | {summary['cursor_fixed_count']} |")
        lines.append(f"| Non-200 responses | {summary['non_200']} |\n")

    lines.append("## Per-Call Log\n")
    lines.append("| Call | Status | Articles | Anchor type | Fixed? | Skipped type | Oldest | Elapsed |")
    lines.append("|------|--------|----------|-------------|--------|--------------|--------|---------|")
    for r in results:
        if r.get("call") == "SUMMARY":
            continue
        fix_flag = "✅" if r.get("cursor_fixed") else "—"
        skipped = r.get("skipped_storyType") or "—"
        if r.get("status") != 200:
            lines.append(
                f"| {r['call']} | **{r['status']}** | — |"
                f" {r.get('anchor_storyType','?')} | {fix_flag} | {skipped} |"
                f" {r.get('oldest_so_far','?')} | {r.get('elapsed','?')}s |"
            )
            snip = r.get("body_snippet", "")
            if snip:
                lines.append(f"\n**Error body:**\n```\n{snip}\n```\n")
        else:
            lines.append(
                f"| {r['call']} | 200 | {r.get('articles','—')} |"
                f" {r.get('anchor_storyType','?')} | {fix_flag} | {skipped} |"
                f" {r.get('oldest_so_far','?')} | {r.get('elapsed','?')}s |"
            )

    report_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CoinDesk cursor storyType probe")
    parser.add_argument(
        "--mode", choices=["walk", "fixed"], default="walk",
        help="walk: log all storyTypes; fixed: use fixed cursor skipping invalid types",
    )
    parser.add_argument(
        "--n", type=int, default=25,
        help="number of paginated calls (default: 25 for walk, increase for fixed/deep)",
    )
    parser.add_argument(
        "--invalid-types", type=str, default="",
        metavar="T1,T2,...",
        help="comma-separated storyTypes to skip as cursor anchor (fixed mode only)",
    )
    parser.add_argument(
        "--delay", type=float, default=CALL_DELAY,
        help=f"seconds between cursor calls (default: {CALL_DELAY})",
    )
    args = parser.parse_args()

    invalid = frozenset(t.strip() for t in args.invalid_types.split(",") if t.strip())
    asyncio.run(cursor_probe_workflow(mode=args.mode, n=args.n, invalid_types=invalid, delay=args.delay))
