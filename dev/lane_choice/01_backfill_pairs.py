#!/usr/bin/env python3
"""Backfill paired chromium+camoufox scrapes for every distinct URL in the production scrape log —
the calibration basis for a coming lane-choice metrics feature. Historical records are config/
site-drift stale, so BOTH lanes are re-fired fresh for every URL, never just the missing one.

Orchestration only: the production `websearch` CLI (PATH wrapper -> main-repo cli.py) does the real
scraping and writes scrape_log.jsonl + sidecars itself. This script never writes content — only its
own resume-state JSONL and the md/ report.
"""
# INFRASTRUCTURE
import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).parent
STATE_PATH = SCRIPT_DIR / "jsonl" / "backfill_pairs_state.jsonl"
REPORT_DIR = SCRIPT_DIR / "md"

# The MAIN repo's canonical production log — never a worktree copy (worktrees have their own,
# separate, gitignored src/logs/ tree).
PROD_SCRAPE_LOG_PATH = Path(
    "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/src/logs/scrape_log.jsonl"
)

WEBSEARCH_CMD = "websearch"
ENGINES = [("scrape_url_chromium", "chromium"), ("scrape_url_camoufox", "camoufox")]

# Both lanes' own internal acquisition budgets top out at ~245-246s (TOTAL_SCRAPE_BUDGET_S /
# TOTAL_CAMOUFOX_BUDGET_S) — this wrapper timeout sits above both with margin so the CLI's own
# graceful budget_exhausted path always gets first chance to fire and log a real outcome; only a
# genuinely hung subprocess (no internal budget firing at all) ever hits this.
SUBPROCESS_TIMEOUT_S = 260.0
# Small pause between every CLI invocation (own lane switch or next URL alike) — the sites being
# scraped are real, external, mostly-unrelated third parties; both lanes already spend several
# seconds per call, this just adds a courteous floor rather than back-to-back launches.
POLITENESS_DELAY_S = 2.0


# ORCHESTRATOR

# Collect distinct URLs, fire both lanes fresh per URL (skipping resume-complete pairs), report
def backfill_pairs_workflow(limit: int | None) -> None:
    check_websearch_on_path()
    t_start = time.perf_counter()

    all_urls = collect_distinct_urls()
    fireable_urls, skipped_pdf = filter_pdf_urls(all_urls)
    target_urls = fireable_urls[:limit] if limit is not None else fireable_urls

    completed_pairs = load_completed_pairs()
    fired_counts = {"chromium": 0, "camoufox": 0}
    skipped_resume_count = 0

    for i, url in enumerate(target_urls, 1):
        print(f"[{i}/{len(target_urls)}] {url[:100]}", file=sys.stderr)
        for subcommand, engine in ENGINES:
            if (url, engine) in completed_pairs:
                skipped_resume_count += 1
                print(f"    {engine}: already done this backfill session, skipping", file=sys.stderr)
                continue
            entry = fire_one_pair(url, subcommand, engine)
            append_state(entry)
            fired_counts[engine] += 1
            print(f"    {engine}: {entry['outcome']} ({entry['wall_ms']}ms)", file=sys.stderr)
            time.sleep(POLITENESS_DELAY_S)

    wall_s = time.perf_counter() - t_start
    funnel = {
        "distinct_urls": len(all_urls),
        "skipped_pdf": skipped_pdf,
        "target_urls_this_invocation": len(target_urls),
        "skipped_resume": skipped_resume_count,
        "fired_counts": fired_counts,
        "wall_s": wall_s,
    }
    report_path = write_report(funnel)
    print(f"\nReport: {report_path}", file=sys.stderr)
    print(f"Wall time: {wall_s:.1f}s", file=sys.stderr)


# FUNCTIONS

# Fail fast on a missing PATH entry — a setup defect, not a per-URL data point
def check_websearch_on_path() -> None:
    if shutil.which(WEBSEARCH_CMD) is None:
        raise RuntimeError(f"`{WEBSEARCH_CMD}` not found on PATH — cannot fire the production CLI")


# Distinct URLs from the production log, first-seen order, deduped
def collect_distinct_urls() -> list[str]:
    urls = []
    with open(PROD_SCRAPE_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            urls.append(record["url"])
    return list(dict.fromkeys(urls))


# Split URLs into (fireable, skipped_pdf_count) — mirrors cli.py's own scrape-subcommand .pdf reject
def filter_pdf_urls(urls: list[str]) -> tuple[list[str], int]:
    fireable = [u for u in urls if not urlparse(u).path.lower().endswith(".pdf")]
    return fireable, len(urls) - len(fireable)


# (url, engine) pairs already recorded in this backfill's own resume-state file
def load_completed_pairs() -> set[tuple[str, str]]:
    if not STATE_PATH.exists():
        return set()
    pairs = set()
    with open(STATE_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            pairs.add((entry["url"], entry["engine"]))
    return pairs


# Fire one url+engine pair via the production CLI, then read back its own fresh log record
def fire_one_pair(url: str, subcommand: str, engine: str) -> dict:
    call_start = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    try:
        result = subprocess.run(
            [WEBSEARCH_CMD, subcommand, url],
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_S,
        )
        returncode = result.returncode
        harness_status = "ok" if returncode == 0 else f"cli_exit_{returncode}"
    except subprocess.TimeoutExpired:
        returncode = None
        harness_status = "harness_timeout"
    wall_ms = round((time.perf_counter() - t0) * 1000)

    log_record = find_fresh_log_record(url, engine, call_start)
    outcome = _derive_outcome(log_record) if log_record else f"no_log_record ({harness_status})"

    return {
        "url": url, "engine": engine, "outcome": outcome,
        "harness_status": harness_status, "cli_returncode": returncode,
        "wall_ms": wall_ms, "ts": call_start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }


# This script's own local "did the pair fetch content" label — the production log no longer
# computes an outcome verdict (see src/scraper/DOCS.md's Gotchas: acquisition_error is now logged
# as its own fact instead), so this backfill tool derives the same three-way label it always
# reported, off the two facts that already replace it: a named acquisition_error, or "ok"/"empty"
# from whether any bytes actually came back.
def _derive_outcome(log_record: dict) -> str:
    if log_record.get("acquisition_error"):
        return log_record["acquisition_error"]
    return "ok" if log_record.get("bytes_returned") else "empty"


# The freshest production-log record for url+engine with ts >= since — the CLI's own just-written
# record, read back rather than parsed off stdout (the canonical source, not a re-derived guess)
def find_fresh_log_record(url: str, engine: str, since: datetime) -> dict | None:
    latest = None
    latest_ts = None
    with open(PROD_SCRAPE_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record["url"] != url or record.get("engine") != engine:
                continue
            ts = _parse_ts(record["ts"])
            if ts < since:
                continue
            if latest_ts is None or ts > latest_ts:
                latest, latest_ts = record, ts
    return latest


# Parse the project's standard "%Y-%m-%dT%H:%M:%S.%fZ" timestamp into an aware UTC datetime
def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


# Append one completed-pair record — written immediately so an interrupted run stays resumable
def append_state(entry: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# Write the funnel + per-URL+engine report off the FULL cumulative state file (all invocations so far)
def write_report(funnel: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    all_entries = _read_state_entries()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"01_backfill_pairs_report_{ts}.md"

    sections = [
        format_funnel_section(funnel, all_entries),
        format_outcome_breakdown(all_entries),
        format_per_pair_lines(all_entries),
    ]
    report_path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    return report_path


# All entries ever recorded in the resume-state file, oldest first
def _read_state_entries() -> list[dict]:
    if not STATE_PATH.exists():
        return []
    with open(STATE_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# Funnel section: this invocation's counts plus cumulative state-file totals
def format_funnel_section(funnel: dict, all_entries: list[dict]) -> str:
    fired = funnel["fired_counts"]
    lines = [
        "## Funnel (this invocation)",
        f"- Distinct URLs in production log: {funnel['distinct_urls']}",
        f"- Skipped (.pdf, CLI rejects anyway): {funnel['skipped_pdf']}",
        f"- Target URLs this invocation: {funnel['target_urls_this_invocation']}",
        f"- Pairs already done this backfill session (resumed, skipped): {funnel['skipped_resume']}",
        f"- Fired this invocation: chromium={fired['chromium']}, camoufox={fired['camoufox']}",
        f"- Wall time this invocation: {funnel['wall_s']:.1f}s",
        "",
        "## Cumulative (all invocations, from resume-state)",
        f"- Total pairs recorded: {len(all_entries)}",
        f"- Distinct URLs with BOTH lanes recorded: {_urls_with_both_lanes(all_entries)}",
    ]
    return "\n".join(lines)


def _urls_with_both_lanes(entries: list[dict]) -> int:
    by_url: dict[str, set] = {}
    for e in entries:
        by_url.setdefault(e["url"], set()).add(e["engine"])
    return sum(1 for engines in by_url.values() if len(engines) >= 2)


# Outcome counts per engine, cumulative
def format_outcome_breakdown(all_entries: list[dict]) -> str:
    lines = ["## Outcome counts per engine (cumulative)"]
    for engine in ("chromium", "camoufox"):
        counts: dict[str, int] = {}
        for e in all_entries:
            if e["engine"] != engine:
                continue
            counts[e["outcome"]] = counts.get(e["outcome"], 0) + 1
        lines.append(f"\n**{engine}** ({sum(counts.values())} total):")
        for outcome, count in sorted(counts.items(), key=lambda x: -x[1]):
            lines.append(f"- `{outcome}`: {count}")
    return "\n".join(lines)


# One line per URL+engine with outcome, cumulative, in recorded order
def format_per_pair_lines(all_entries: list[dict]) -> str:
    lines = ["## Per-URL+engine outcomes (cumulative)", ""]
    for e in all_entries:
        lines.append(f"- `{e['engine']:9s}` {e['outcome']:20s} {e['wall_ms']:6d}ms  {e['url']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Backfill paired chromium+camoufox scrapes for every distinct URL in the production scrape log."
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only fire the first N target URLs this invocation (for smoke-testing before a full run)"
    )
    args = parser.parse_args()
    backfill_pairs_workflow(args.limit)


if __name__ == "__main__":
    main()
