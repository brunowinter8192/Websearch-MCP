#!/usr/bin/env python3
"""Classify 11 Lobsters EMPTY queries from smoke_20260504_023641: pydoll browser, 3s wait vs production 600ms."""

# INFRASTRUCTURE
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent))

from src.search.browser import new_tab, close_browser
from src.search.rate_limiter import get_limiter

REPORT_DIR = SCRIPT_DIR / "01_reports"
SCREENSHOT_DIR = REPORT_DIR / "empty_classify_lobsters_screenshots"

SEARCH_URL = "https://lobste.rs/search?q={}&what=stories&order=relevance"
WAIT_SECONDS = 3.0  # vs production 600ms — deliberate generous margin

_JS_COUNT = "return document.querySelectorAll('li.story').length"
_JS_TITLE = "return document.title"
_JS_HTML_SNIPPET = "return document.documentElement.outerHTML.substring(0, 2000)"

# (smoke_row, query) for all 11 Lobsters EMPTY entries from smoke_20260504_023641
LOBSTERS_EMPTY_QUERIES = [
    (3,  "fastapi websocket reconnect handler"),
    (13, "climate change carbon capture technology 2025"),
    (14, "epidemiology cohort study design methodology"),
    (15, "Bewerbung Lebenslauf Format Deutschland"),
    (16, "Mietvertrag Kündigungsfrist gesetzliche Regelung"),
    (17, "GmbH Gründung Kosten Schritte"),
    (18, "Krankenversicherung Vergleich gesetzlich privat"),
    (19, "Python Programmierung Anfänger Tutorial deutsch"),
    (20, "Datenschutz DSGVO Website Impressum"),
    (21, "crawl4ai stealth browser detection bypass"),
    (22, "pydoll chromium CDP automation"),
]


# ORCHESTRATOR

async def run_classify() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    limiter = get_limiter("lobsters")
    records = []

    try:
        for idx, (smoke_row, query) in enumerate(LOBSTERS_EMPTY_QUERIES):
            take_screenshot = idx < 3  # first 3 queries only
            print(f"[{idx + 1}/11] smoke#{smoke_row}: {query}", file=sys.stderr)
            record = await probe_query(limiter, smoke_row, query, take_screenshot, idx)
            records.append(record)
            print(
                f"  story_count={record['story_count']} | title={record['page_title']!r} | {record['classification']}",
                file=sys.stderr,
            )
    finally:
        await close_browser()

    report_path = write_report(records)
    counts = _summary_counts(records)
    print(f"\nReport: {report_path}", file=sys.stderr)
    print(f"Summary: {counts}", file=sys.stderr)


# FUNCTIONS

# Extract primitive value from CDP execute_script result dict
def _extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


# Probe one query: navigate, wait 3s, record count + title + HTML + optional screenshot
async def probe_query(limiter, smoke_row: int, query: str, take_screenshot: bool, idx: int) -> dict:
    record = {
        "smoke_row": smoke_row,
        "query": query,
        "story_count": 0,
        "page_title": "",
        "html_snippet": "",
        "screenshot_path": "",
        "classification": "UNKNOWN",
        "notes": "",
    }

    await limiter.acquire()
    tab = await new_tab()
    url = SEARCH_URL.format(quote_plus(query))

    try:
        await tab.go_to(url, timeout=20)
        await asyncio.sleep(WAIT_SECONDS)

        # Count
        raw = await tab.execute_script(_JS_COUNT)
        count = _extract_value(raw)
        record["story_count"] = int(count) if count is not None else 0

        # Title
        raw = await tab.execute_script(_JS_TITLE)
        record["page_title"] = _extract_value(raw) or ""

        # HTML snippet
        raw = await tab.execute_script(_JS_HTML_SNIPPET)
        html = _extract_value(raw) or ""
        record["html_snippet"] = html[:2000]

        # Screenshot (first 3 only)
        if take_screenshot:
            slug = query[:40].replace(" ", "_").replace("/", "-")
            shot_path = SCREENSHOT_DIR / f"{slug}.png"
            await tab.take_screenshot(path=str(shot_path))
            record["screenshot_path"] = str(shot_path)

    except Exception as e:
        record["notes"] = f"{type(e).__name__}: {str(e)[:120]}"
    finally:
        await tab.close()

    record["classification"] = _classify(record)
    return record


# Classify from story count, page title, and HTML snippet
def _classify(r: dict) -> str:
    count = r["story_count"]
    title = r["page_title"].lower()
    html = r["html_snippet"].lower()
    notes = r["notes"]

    if notes:
        # Exception during probe — check for bot-block signals in whatever we got
        if any(x in html for x in ("cloudflare", "captcha", "access denied", "403")):
            return "BOT_BLOCK"
        return "UNKNOWN"

    if count > 0:
        return "PIPELINE_BUG"

    # Bot / block signals
    if any(x in title for x in ("cloudflare", "captcha", "access denied", "403", "just a moment")):
        return "BOT_BLOCK"
    if any(x in html for x in ("cloudflare", "captcha", "access denied", "cf-browser-verification")):
        return "BOT_BLOCK"

    # Genuine search page with no results
    if "lobste.rs" in title or "lobsters" in title or "search" in title:
        return "ENGINE_EMPTY"

    return "UNKNOWN"


# Tally classification counts
def _summary_counts(records: list[dict]) -> dict:
    counts = {"ENGINE_EMPTY": 0, "PIPELINE_BUG": 0, "BOT_BLOCK": 0, "UNKNOWN": 0}
    for r in records:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    return counts


# Write markdown report and return path
def write_report(records: list[dict]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"empty_classify_lobsters_{ts}.md"
    counts = _summary_counts(records)

    lines = [
        f"# Lobsters EMPTY Classification — {ts}",
        "",
        "Source: `dev/search_pipeline/01_reports/search_smoke_20260504_023641.md`",
        f"Method: pydoll browser, {WAIT_SECONDS}s wait (vs production 600ms), "
        "li.story count + page title + HTML snippet + screenshots for first 3 queries.",
        "",
        "## Summary",
        "",
        f"- ENGINE_EMPTY: {counts['ENGINE_EMPTY']}/11",
        f"- PIPELINE_BUG: {counts['PIPELINE_BUG']}/11",
        f"- BOT_BLOCK: {counts['BOT_BLOCK']}/11",
        f"- UNKNOWN: {counts['UNKNOWN']}/11",
        "",
        "## Per-Query",
        "",
        "| # | Smoke # | Query | story count (3s) | page title | HTML snippet (200 chars) | Classification |",
        "|---|---------|-------|------------------|------------|--------------------------|----------------|",
    ]

    for idx, r in enumerate(records, 1):
        query = r["query"].replace("|", "\\|")
        snippet = r["html_snippet"][:200].replace("\n", " ").replace("|", "\\|")
        title = r["page_title"].replace("|", "\\|")
        lines.append(
            f"| {idx} | {r['smoke_row']} | {query} "
            f"| {r['story_count']} | {title!r} | `{snippet}` | {r['classification']} |"
        )

    # Screenshots section
    shots = [r for r in records if r.get("screenshot_path")]
    if shots:
        lines += ["", "## Screenshots", ""]
        for r in shots:
            lines.append(f"- `{r['screenshot_path']}`")

    # Notes for exceptions
    noted = [r for r in records if r.get("notes")]
    if noted:
        lines += ["", "## Exception Notes", ""]
        for r in noted:
            lines.append(f"- Smoke#{r['smoke_row']} `{r['query']}`: {r['notes']}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    asyncio.run(run_classify())
