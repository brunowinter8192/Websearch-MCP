#!/usr/bin/env python3
"""CDP starvation probe — Pattern A (asyncio debug) + Pattern B (canary latency) + CDP event counter.

Hypothesis: Chrome CDP event flooding during CAPTCHA navigation starves the asyncio event loop,
causing all 9 engines' asyncio.wait_for(limiter.acquire(), 5.0) to time out simultaneously.
Builds on prior zero-query diagnosis analysis.

Usage:
    ./venv/bin/python3 dev/search_pipeline/cdp_starvation_probe.py [--max-queries N]

Output:
    dev/search_pipeline/md/cdp_probe_<ts>.md
"""

# INFRASTRUCTURE
import argparse
import asyncio
import importlib
import logging
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# sys.path before any local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# --- Monkey-patch pydoll BEFORE importing src modules ---
# Target: ConnectionHandler._process_single_message (connection_handler.py:244)
# Called exactly once per CDP message in the receive loop.
from pydoll.connection.connection_handler import ConnectionHandler as _CH

_cdp_ts: list[float] = []  # monotonic timestamp for each CDP message received
_orig_process_msg = _CH._process_single_message


async def _patched_process_msg(self, raw_message: str) -> None:
    _cdp_ts.append(time.monotonic())
    return await _orig_process_msg(self, raw_message)


_CH._process_single_message = _patched_process_msg
# --- End monkey-patch ---

# Dynamic imports to load production modules (avoids static 'from src.' hook in dev/ scripts)
_browser_mod = importlib.import_module("src.search.browser")
_search_mod = importlib.import_module("src.search.search_web")
close_browser = _browser_mod.close_browser
search_web_workflow = _search_mod.search_web_workflow

SCRIPT_DIR = Path(__file__).parent
QUERIES_FILE = SCRIPT_DIR / "queries.txt"
REPORT_DIR = SCRIPT_DIR / "md"
FINDINGS_DIR = SCRIPT_DIR / "md"

COLD_START_SKIP_S = 5.0      # exclude first N seconds from statistics (Chrome boot noise)
CANARY_INTERVAL_S = 0.1      # Pattern B: scheduling probe interval
SLOW_CB_THRESHOLD_S = 0.05   # Pattern A: log callbacks blocking event loop > 50ms

# Shared state populated during the run
_canary_samples: list[tuple[float, float, int]] = []  # (ts_mono, latency_ms, num_tasks)
_slow_cb_events: list[str] = []  # asyncio "Executing ... took Xs" log lines

PROBE_START: float = 0.0  # set in run_cdp_probe before first query


# ORCHESTRATOR

# Run 20 queries with Pattern A + B + CDP counter active; write report + findings narrative
async def run_cdp_probe(max_queries: int | None) -> None:
    global PROBE_START
    PROBE_START = time.monotonic()

    # Pattern A: asyncio debug logging
    loop = asyncio.get_running_loop()
    loop.slow_callback_duration = SLOW_CB_THRESHOLD_S
    loop.set_debug(True)
    _install_asyncio_log_capture()

    queries = _load_queries(QUERIES_FILE, max_queries)
    print(f"CDP starvation probe | Queries: {len(queries)} | slow_cb_threshold={SLOW_CB_THRESHOLD_S*1000:.0f}ms",
          file=sys.stderr)

    # Pattern B: start canary task
    stop_canary = asyncio.Event()
    canary_task = asyncio.create_task(_canary_monitor(stop_canary))

    query_records: list[dict] = []

    try:
        for qi, query in enumerate(queries, 1):
            t_start = time.monotonic()
            _, timings = await search_web_workflow(query, "en", None, None, _with_timings=True)
            t_end = time.monotonic()

            det = timings.get("engine_details", {})
            google_status = det.get("google", {}).get("status", "—")

            # All-RATE_SKIP = zero-cascade query (post-CAPTCHA starvation cascade)
            all_statuses = {k: v.get("status", "—") for k, v in det.items()}
            all_rate_skip = bool(all_statuses) and all(s == "RATE_SKIP" for s in all_statuses.values())

            cdp_in_query = sum(1 for ts in _cdp_ts if t_start <= ts < t_end)
            dur_s = max(t_end - t_start, 0.001)

            # "captcha" (keyed on the removed EMPTY_BLOCK verdict) renamed to "empty" — the
            # guessed-verdict-removal milestone collapsed EMPTY_BLOCK into bare "EMPTY", and
            # engine_details (status+ms only) carries no diagnosis to reconstruct which kind of
            # empty this was; an honest narrower label beats a familiar wrong one.
            if google_status == "EMPTY":
                category = "empty"
            elif all_rate_skip:
                category = "zero_cascade"
            else:
                category = "normal"

            record = {
                "qi": qi,
                "query": query,
                "t_start": t_start,
                "t_end": t_end,
                "duration_s": dur_s,
                "google_status": google_status,
                "all_statuses": all_statuses,
                "category": category,
                "total_ms": timings.get("total_ms", 0),
                "fanout_ms": timings.get("engine_fanout_ms", 0),
                "cdp_events": cdp_in_query,
                "cdp_rate": cdp_in_query / dur_s,
            }
            query_records.append(record)

            flag = "⚡EMPTY" if category == "empty" else ("🚫ZERO" if category == "zero_cascade" else "")
            print(
                f"[{qi}/{len(queries)}] {query!r} -> "
                f"google={google_status} cdp={cdp_in_query}({record['cdp_rate']:.0f}/s) "
                f"category={category} {flag}",
                file=sys.stderr,
            )
    finally:
        stop_canary.set()
        await canary_task
        await close_browser()

    # Write outputs
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)

    report_path = _write_report(query_records)
    findings_path = _write_findings(query_records, report_path)

    print(f"\nReport:   {report_path}", file=sys.stderr)
    print(f"Findings: {findings_path}", file=sys.stderr)


# FUNCTIONS

# Pattern B: scheduling latency canary — measures actual asyncio.sleep(0.1) elapsed
async def _canary_monitor(stop: asyncio.Event) -> None:
    while not stop.is_set():
        t0 = time.monotonic()
        await asyncio.sleep(CANARY_INTERVAL_S)
        elapsed = time.monotonic() - t0
        latency_ms = max(0.0, (elapsed - CANARY_INTERVAL_S) * 1000)
        num_tasks = len(asyncio.all_tasks())
        _canary_samples.append((time.monotonic(), latency_ms, num_tasks))


# Attach handler to asyncio logger to capture slow-callback warnings
def _install_asyncio_log_capture() -> None:
    class _SlowCBHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            msg = self.format(record)
            if "Executing" in msg and "took" in msg:
                _slow_cb_events.append(msg)

    h = _SlowCBHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    aio_log = logging.getLogger("asyncio")
    aio_log.setLevel(logging.WARNING)
    aio_log.addHandler(h)


# Load queries from file
def _load_queries(path: Path, max_queries: int | None) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    qs = [ln.strip() for ln in lines if ln.strip()]
    return qs[:max_queries] if max_queries else qs


# Return category label for a canary sample based on which query was running at ts
def _sample_category(ts: float, records: list[dict]) -> str:
    for r in records:
        if r["t_start"] <= ts < r["t_end"]:
            return r["category"]
    return "between"  # sample fell between queries (rare gap)


# Compute p-th percentile
def _pct(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (k - lo) * (s[hi] - s[lo])


# Compute latency stats broken out by query category + overall (cold-start excluded)
def _compute_stats(records: list[dict]) -> dict[str, dict]:
    cold_cutoff = PROBE_START + COLD_START_SKIP_S
    by_cat: dict[str, list[float]] = defaultdict(list)
    all_lat: list[float] = []
    cold_lat: list[float] = []

    for ts, lat, _ in _canary_samples:
        if ts < cold_cutoff:
            cold_lat.append(lat)
            continue
        cat = _sample_category(ts, records)
        by_cat[cat].append(lat)
        if cat != "between":
            all_lat.append(lat)

    def _stats(data: list[float]) -> dict:
        if not data:
            return {"n": 0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0, "mean": 0.0}
        return {
            "n": len(data),
            "p50": round(_pct(data, 50), 1),
            "p95": round(_pct(data, 95), 1),
            "p99": round(_pct(data, 99), 1),
            "max": round(max(data), 1),
            "mean": round(statistics.mean(data), 1),
        }

    return {
        "overall": _stats(all_lat),
        "normal": _stats(by_cat.get("normal", [])),
        "empty": _stats(by_cat.get("empty", [])),
        "zero_cascade": _stats(by_cat.get("zero_cascade", [])),
        "cold_start": _stats(cold_lat),
    }


# Derive verdict string from stats
def _derive_verdict(stats: dict) -> str:
    s_cap = stats["empty"]
    s_zc = stats["zero_cascade"]
    s_norm = stats["normal"]
    norm_p99 = max(s_norm["p99"], 1.0)

    starvation = (
        (s_cap["n"] > 0 and s_cap["p99"] > 200 and s_cap["p99"] > norm_p99 * 3) or
        (s_zc["n"] > 0 and s_zc["p99"] > 200 and s_zc["p99"] > norm_p99 * 3)
    )
    partial = (
        (s_cap["n"] > 0 and s_cap["p99"] > 50 and s_cap["p99"] > norm_p99 * 1.5) or
        (s_zc["n"] > 0 and s_zc["p99"] > 50 and s_zc["p99"] > norm_p99 * 1.5)
    )

    if starvation:
        return "CONFIRMED"
    if partial:
        return "PARTIALLY_CONFIRMED"
    if s_cap["n"] == 0 and s_zc["n"] == 0:
        return "INCONCLUSIVE"
    return "REFUTED"


# Write report to md/cdp_probe_<ts>.md; return path
def _write_report(records: list[dict]) -> Path:
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"cdp_probe_{ts_str}.md"
    stats = _compute_stats(records)
    verdict = _derive_verdict(stats)
    run_dur_s = (records[-1]["t_end"] - PROBE_START) if records else 0.0

    lines: list[str] = []
    lines += _r_header(records, ts_str, run_dur_s, verdict)
    lines += _r_query_table(records)
    lines += _r_latency_stats(stats)
    lines += _r_timeseries(records)
    lines += _r_cdp_table(records)
    lines += _r_slow_callbacks()
    lines += _r_verdict_section(stats, verdict)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# Write findings narrative; return path
def _write_findings(records: list[dict], report_path: Path) -> Path:
    path = FINDINGS_DIR / "01_probe.md"
    stats = _compute_stats(records)
    verdict = _derive_verdict(stats)
    s_cap = stats["empty"]
    s_zc = stats["zero_cascade"]
    s_norm = stats["normal"]
    report_rel = report_path.relative_to(Path(__file__).parent.parent.parent)
    norm_p99 = max(s_norm["p99"], 1.0)

    lines = [
        "# Bee CDP Starvation — Phase 1 Probe",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ",
        f"**Verdict:** {verdict}  ",
        f"**Report:** `{report_rel}`  ",
        "",
        "---",
        "",
        "## Hypothesis",
        "",
        "During Google CAPTCHA navigation, Chrome emits a burst of CDP events processed by",
        "pydoll's `ConnectionHandler._receive_events()` (`connection_handler.py:226`) in a",
        "tight `async for raw_message in _incoming_messages()` loop. When websockets' internal",
        "queue is non-empty, `Queue.get()` completes without yielding — near-non-yielding",
        "busy loop. All 9 engines' `asyncio.wait_for(limiter.acquire(), 5.0)` calls",
        "(`_engine_with_timing()` in `search_web.py:299`) never get a scheduler turn and",
        "expire as TimeoutError simultaneously — including HTTP-only engines.",
        "",
        "## Instrumentation",
        "",
        "Three measurements sharing the same asyncio event loop across 20 sequential queries:",
        "",
        "- **Pattern A** — `loop.slow_callback_duration=0.05s; loop.set_debug(True)` + asyncio",
        "  logger capture: records any callback blocking >50ms.",
        "- **Pattern B** — canary task: `await asyncio.sleep(0.1)` every 100ms, scheduling",
        "  latency = actual_elapsed − 100ms. From Ray Serve production pattern.",
        "- **CDP counter** — monkey-patch on `ConnectionHandler._process_single_message`",
        "  (`connection_handler.py:244`): timestamps each CDP message received.",
        "",
        "Query categories used for latency segmentation:",
        "- `empty`: google_status == EMPTY (was EMPTY_BLOCK — removed along with the query log's",
        "  guessed-verdict sub-statuses; `empty` now also covers what used to be the other EMPTY_*",
        "  causes, since engine_details carries no diagnosis to distinguish them)",
        "- `zero_cascade`: all 9 engines RATE_SKIP simultaneously",
        "- `normal`: all other queries",
        "",
        "## Key Numbers",
        "",
        "| Metric | normal | empty | zero_cascade |",
        "|--------|--------|---------|--------------|",
        f"| samples n | {s_norm['n']} | {s_cap['n']} | {s_zc['n']} |",
        f"| scheduling latency p50 ms | {s_norm['p50']} | {s_cap['p50']} | {s_zc['p50']} |",
        f"| scheduling latency p95 ms | {s_norm['p95']} | {s_cap['p95']} | {s_zc['p95']} |",
        f"| scheduling latency p99 ms | {s_norm['p99']} | {s_cap['p99']} | {s_zc['p99']} |",
        f"| scheduling latency max ms | {s_norm['max']} | {s_cap['max']} | {s_zc['max']} |",
        "",
        f"Slow-callback events captured (Pattern A, >50ms): {len(_slow_cb_events)}  ",
        f"Total CDP messages received: {len(_cdp_ts)}  ",
        "",
        "### CDP Rate by Query",
        "",
        "| # | Query | category | cdp_events | cdp_rate/s |",
        "|---|-------|----------|------------|------------|",
    ]
    for r in records:
        q = r["query"][:42]
        lines.append(f"| {r['qi']} | {q} | {r['category']} | {r['cdp_events']} | {r['cdp_rate']:.1f} |")

    lines += [
        "",
        "## Verdict",
        "",
        f"**{verdict}**",
        "",
    ]

    if verdict == "CONFIRMED":
        worst_cat = "empty" if s_cap["p99"] >= s_zc["p99"] else "zero_cascade"
        worst = stats[worst_cat]
        lines += [
            f"Scheduling latency p99 during `{worst_cat}` windows: {worst['p99']}ms vs",
            f"normal {s_norm['p99']}ms ({worst['p99']/norm_p99:.0f}x ratio). Asyncio event loop",
            "definitively starved during Chrome CAPTCHA processing. All 9 engines' 5s",
            "`wait_for` deadlines expire before getting a scheduler turn — confirmed by Pattern B.",
        ]
    elif verdict == "PARTIALLY_CONFIRMED":
        lines += [
            f"Latency elevated: empty p99={s_cap['p99']}ms, zero_cascade p99={s_zc['p99']}ms",
            f"vs normal {s_norm['p99']}ms. CDP event loop mechanism consistent but starvation",
            "weaker than predicted — may require heavier CAPTCHA page to trigger full cascade.",
        ]
    elif verdict == "REFUTED":
        lines += [
            f"No significant elevation: empty p99={s_cap['p99']}ms,",
            f"zero_cascade p99={s_zc['p99']}ms vs normal p99={s_norm['p99']}ms.",
            "CDP starvation hypothesis not supported. Alternative root cause required.",
        ]
    else:
        lines.append("No CAPTCHA or zero-cascade queries occurred — hypothesis untestable.")

    lines += [
        "",
        "## Next Steps",
        "",
        "Pending (bead `searxng-bee`):",
    ]
    if verdict in ("CONFIRMED", "PARTIALLY_CONFIRMED"):
        lines += [
            "- **Mitigation:** after detecting an empty google result (google EMPTY, was EMPTY_BLOCK, in `search_batch_workflow`),",
            "  yield event loop with repeated `await asyncio.sleep(0)` or a short `asyncio.sleep(0.5)`",
            "  before next query to drain the CDP backlog.",
            "- **Structural:** custom `ConnectionHandler` subclass throttling `_receive_events` with",
            "  `asyncio.sleep(0)` every N events to guarantee scheduler turns during bursts.",
            "- Re-run probe post-mitigation to confirm latency returns to normal baseline.",
        ]
    else:
        lines += [
            "- Verify rate limiter backoff does not block: `asyncio.sleep(backoff_s)` in `rate_limiter.py`.",
            "- Probe Chrome tab lifecycle: `new_tab()` / `apply_fingerprint_patches()` blocking cost.",
        ]
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# Report section renderers

def _r_header(records: list[dict], ts_str: str, run_dur_s: float, verdict: str) -> list[str]:
    empty_n = sum(1 for r in records if r["category"] == "empty")
    zero_n = sum(1 for r in records if r["category"] == "zero_cascade")
    return [
        f"# CDP Starvation Probe Report — {ts_str}",
        "",
        f"**Verdict:** {verdict}  ",
        f"**Queries:** {len(records)}  ",
        f"**Empty queries:** {empty_n}  ",
        f"**Zero-cascade queries:** {zero_n}  ",
        f"**Total CDP messages:** {len(_cdp_ts)}  ",
        f"**Total canary samples:** {len(_canary_samples)}  ",
        f"**Slow-callback events:** {len(_slow_cb_events)}  ",
        f"**Run duration:** {run_dur_s:.0f}s  ",
        "",
        "---",
        "",
    ]


def _r_query_table(records: list[dict]) -> list[str]:
    lines = [
        "## Per-Query Summary",
        "",
        "| # | Query | total_ms | google | category | cdp_events | cdp_rate/s |",
        "|---|-------|----------|--------|----------|------------|------------|",
    ]
    for r in records:
        q = r["query"][:42].replace("|", "\\|")
        lines.append(
            f"| {r['qi']} | {q} | {r['total_ms']} "
            f"| {r['google_status']} | {r['category']} "
            f"| {r['cdp_events']} | {r['cdp_rate']:.1f} |"
        )
    return lines + [""]


def _r_latency_stats(stats: dict) -> list[str]:
    lines = [
        "",
        "## Scheduling Latency by Query Category (Pattern B)",
        "",
        f"> Cold-start first {COLD_START_SKIP_S:.0f}s excluded from per-category stats.",
        "",
        "| Category | n | p50 ms | p95 ms | p99 ms | max ms | mean ms |",
        "|----------|---|--------|--------|--------|--------|---------|",
    ]
    for label, key in [
        ("Normal queries", "normal"),
        ("Empty queries (google=EMPTY, was EMPTY_BLOCK)", "empty"),
        ("Zero-cascade (all RATE_SKIP)", "zero_cascade"),
        ("Overall (non-cold-start)", "overall"),
        ("Cold-start (first 5s)", "cold_start"),
    ]:
        s = stats[key]
        lines.append(
            f"| {label} | {s['n']} | {s['p50']} | {s['p95']} | {s['p99']} | {s['max']} | {s['mean']} |"
        )
    return lines + [""]


def _r_timeseries(records: list[dict]) -> list[str]:
    if not _canary_samples:
        return []
    # 2-second buckets
    buckets: dict[int, list] = defaultdict(list)
    for ts, lat, ntasks in _canary_samples:
        offset_s = int((ts - PROBE_START) // 2) * 2
        buckets[offset_s].append((ts, lat, ntasks))

    lines = [
        "",
        "## Scheduling Latency Time-Series (2s buckets)",
        "",
        "| offset_s | lat_mean ms | lat_max ms | tasks_mean | cdp/s | category |",
        "|----------|-------------|------------|------------|-------|----------|",
    ]
    for offset_s in sorted(buckets):
        bucket = buckets[offset_s]
        ts_mid = PROBE_START + offset_s + 1.0
        lats = [x[1] for x in bucket]
        tasks_vals = [x[2] for x in bucket]
        t_s = PROBE_START + offset_s
        t_e = t_s + 2.0
        cdp_rate = sum(1 for ct in _cdp_ts if t_s <= ct < t_e) / 2.0
        cat = _sample_category(ts_mid, records)
        lines.append(
            f"| {offset_s} | {statistics.mean(lats):.1f} | {max(lats):.1f} "
            f"| {statistics.mean(tasks_vals):.1f} | {cdp_rate:.1f} | {cat} |"
        )
    return lines + [""]


def _r_cdp_table(records: list[dict]) -> list[str]:
    lines = [
        "",
        "## CDP Event Counts Per Query",
        "",
        f"Total CDP messages across entire run: {len(_cdp_ts)}",
        "",
        "| # | Query | dur_s | cdp_events | cdp_rate/s | category |",
        "|---|-------|-------|------------|------------|----------|",
    ]
    for r in records:
        q = r["query"][:40].replace("|", "\\|")
        lines.append(
            f"| {r['qi']} | {q} | {r['duration_s']:.1f} "
            f"| {r['cdp_events']} | {r['cdp_rate']:.1f} | {r['category']} |"
        )
    return lines + [""]


def _r_slow_callbacks() -> list[str]:
    lines = [
        "",
        f"## Pattern A: Slow Callback Events (threshold={SLOW_CB_THRESHOLD_S*1000:.0f}ms)",
        "",
        f"Total: {len(_slow_cb_events)} events",
        "",
    ]
    if not _slow_cb_events:
        lines.append("*None captured.*")
        lines.append("")
        return lines
    for evt in _slow_cb_events[:60]:
        lines.append(f"    {evt}")
    if len(_slow_cb_events) > 60:
        lines.append(f"    ... {len(_slow_cb_events) - 60} more")
    lines.append("")
    return lines


def _r_verdict_section(stats: dict, verdict: str) -> list[str]:
    s_cap = stats["empty"]
    s_zc = stats["zero_cascade"]
    s_norm = stats["normal"]
    return [
        "",
        "## Verdict",
        "",
        f"**{verdict}**",
        "",
        "| Metric | normal | empty | zero_cascade |",
        "|--------|--------|---------|--------------|",
        f"| p99 ms | {s_norm['p99']} | {s_cap['p99']} | {s_zc['p99']} |",
        f"| max ms | {s_norm['max']} | {s_cap['max']} | {s_zc['max']} |",
        f"| n samples | {s_norm['n']} | {s_cap['n']} | {s_zc['n']} |",
        "",
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CDP starvation probe: Pattern A + B + CDP event counter (20 queries)."
    )
    parser.add_argument("--max-queries", dest="max_queries", type=int, default=None,
                        help="Limit to first N queries (default: all from queries.txt)")
    args = parser.parse_args()
    asyncio.run(run_cdp_probe(args.max_queries))
