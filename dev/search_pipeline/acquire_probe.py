#!/usr/bin/env python3
"""RateLimiter.acquire() instrumentation probe — Phase 2 bee investigation.

Discriminates three hypotheses for zero_cascade queries (all 9+ engines RATE_SKIP):
  B:       enter=N                  — Task never scheduled by asyncio
  A-lock:  enter=Y, lg=N, ~5000ms  — entered acquire() but blocked waiting for the lock
  A-sleep: enter=Y, lg=Y, ~5000ms  — got lock, blocked on asyncio.sleep(backoff_s)
  C:       enter=Y, exit_ok        — acquire() innocent, bug elsewhere

Phase 1 REFUTED CDP starvation (event loop p99=1.4ms, 0 CDP events during cascade).
New hypothesis: Python 3.14 asyncio.Lock non-release under CancelledError causes
stale lock that blocks subsequent queries on same engine.

Usage:
    ./venv/bin/python3 dev/search_pipeline/acquire_probe.py [--max-queries N] [--smoke]

    --smoke: 4-query dry-run, prints per-engine event detail to stderr, no report written.
             Run first to verify instrumentation is live before full 20-query run.

Output (full run only):
    dev/search_pipeline/md/acquire_probe_<ts>.md
"""

# INFRASTRUCTURE
import argparse
import asyncio
import importlib
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# --- Monkey-patches on RateLimiter BEFORE any other src imports ---
# Dynamic import avoids static 'from src.' hook in dev/ scripts (same pattern as cdp_starvation_probe.py)
_rl_mod = importlib.import_module("src.search.rate_limiter")
RateLimiter = _rl_mod.RateLimiter

_acq_events: list[tuple[str, str, float]] = []  # (engine, event, ts_monotonic)


def _get_name(limiter) -> str:
    """Reverse-lookup engine name from _limiters dict by instance identity."""
    for name, lim in _rl_mod._limiters.items():
        if lim is limiter:
            return name
    return "unknown"


class _WatchedLock:
    """Wraps asyncio.Lock to record lock_attempt / lock_granted / lock_released|lock_stuck.

    lock_stuck = lock.locked() is True after __aexit__ completes — Python 3.14 regression signal.
    """

    def __init__(self, real: asyncio.Lock, limiter) -> None:
        self._real = real
        self._limiter = limiter

    def locked(self) -> bool:
        return self._real.locked()

    async def __aenter__(self):
        name = _get_name(self._limiter)
        _acq_events.append((name, "lock_attempt", time.monotonic()))
        await self._real.__aenter__()
        _acq_events.append((name, "lock_granted", time.monotonic()))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        result = await self._real.__aexit__(exc_type, exc_val, exc_tb)
        # Distinguish correct release from stuck lock (Python 3.14 non-release hypothesis)
        evt = "lock_stuck" if self._real.locked() else "lock_released"
        _acq_events.append((_get_name(self._limiter), evt, time.monotonic()))
        return result


_orig_init = RateLimiter.__init__


def _patched_init(self, *args, **kwargs) -> None:
    _orig_init(self, *args, **kwargs)
    self._lock = _WatchedLock(self._lock, self)


_orig_acquire = RateLimiter.acquire


async def _patched_acquire(self) -> None:
    name = _get_name(self)
    _acq_events.append((name, "enter", time.monotonic()))
    try:
        await _orig_acquire(self)
        _acq_events.append((name, "exit_ok", time.monotonic()))
    except BaseException as e:
        _acq_events.append((name, f"exit_err:{type(e).__name__}", time.monotonic()))
        raise


RateLimiter.__init__ = _patched_init
RateLimiter.acquire = _patched_acquire
# --- End monkey-patches ---

_browser_mod = importlib.import_module("src.search.browser")
_search_mod = importlib.import_module("src.search.search_web")
close_browser = _browser_mod.close_browser
search_web_workflow = _search_mod.search_web_workflow

SCRIPT_DIR = Path(__file__).parent
QUERIES_FILE = SCRIPT_DIR / "queries.txt"
REPORT_DIR = SCRIPT_DIR / "md"
FINDINGS_DIR = SCRIPT_DIR / "md"

CANARY_INTERVAL_S = 0.1
COLD_START_SKIP_S = 5.0

_canary_samples: list[tuple[float, float]] = []  # (ts_mono, latency_ms)
PROBE_START: float = 0.0


# ORCHESTRATOR

async def run_acquire_probe(max_queries: int | None, smoke: bool) -> None:
    global PROBE_START
    PROBE_START = time.monotonic()

    queries = _load_queries(QUERIES_FILE, max_queries)
    print(f"acquire probe | queries={len(queries)} smoke={smoke}", file=sys.stderr)

    stop_canary = asyncio.Event()
    canary_task = asyncio.create_task(_canary_monitor(stop_canary))

    query_records: list[dict] = []
    try:
        for qi, query in enumerate(queries, 1):
            n_before = len(_acq_events)
            t_start = time.monotonic()
            _, timings = await search_web_workflow(query, "en", None, None, _with_timings=True)
            t_end = time.monotonic()

            det = timings.get("engine_details", {})
            google_status = det.get("google", {}).get("status", "—")
            all_statuses = {k: v.get("status", "—") for k, v in det.items()}
            all_rate_skip = bool(all_statuses) and all(s == "RATE_SKIP" for s in all_statuses.values())
            # "captcha" (keyed on the removed EMPTY_BLOCK verdict) renamed to "empty" — the
            # guessed-verdict-removal milestone collapsed EMPTY_BLOCK into bare "EMPTY", and
            # engine_details (status+ms only) carries no diagnosis to reconstruct which kind of
            # empty this was; an honest narrower label beats a familiar wrong one.
            category = (
                "empty" if google_status == "EMPTY"
                else "zero_cascade" if all_rate_skip
                else "normal"
            )

            new_events = _acq_events[n_before:]
            eng_summary = _build_engine_summary(new_events, all_statuses)
            disc = _discriminator(eng_summary)

            record = {
                "qi": qi, "query": query, "t_start": t_start, "t_end": t_end,
                "duration_s": t_end - t_start, "google_status": google_status,
                "all_statuses": all_statuses, "category": category,
                "total_ms": timings.get("total_ms", 0),
                "eng_summary": eng_summary, "disc": disc,
            }
            query_records.append(record)

            flag = {"empty": "⚡", "zero_cascade": "🚫", "normal": ""}[category]
            print(
                f"[{qi:2}/{len(queries)}] {query[:48]!r:50} "
                f"cat={category:<12} disc={disc:<8} ev={len(new_events)} {flag}",
                file=sys.stderr,
            )
            if smoke:
                _dump_smoke(new_events, eng_summary)

    finally:
        stop_canary.set()
        await canary_task
        await close_browser()

    zero_n = sum(1 for r in query_records if r["category"] == "zero_cascade")
    # Cascade expected: ≥5/20 based on Phase 1 baseline; for shorter smoke: 0 OK
    min_expected = max(3, len(query_records) // 4) if not smoke else 0
    cascade_ok = zero_n >= min_expected
    print(
        f"\nzero_cascade={zero_n}/{len(query_records)}  cascade_reproduced={cascade_ok}",
        file=sys.stderr,
    )
    if smoke:
        print("Smoke OK — re-run without --smoke for full 20-query run.", file=sys.stderr)
        return
    if not cascade_ok:
        print(
            "WARNING: cascade did not reproduce — instrumentation may be interfering. "
            "Data may be invalid.",
            file=sys.stderr,
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    rp = _write_report(query_records, cascade_ok, zero_n)
    fp = _write_findings(query_records, rp, cascade_ok, zero_n)
    print(f"\nReport:   {rp}", file=sys.stderr)
    print(f"Findings: {fp}", file=sys.stderr)


# FUNCTIONS

async def _canary_monitor(stop: asyncio.Event) -> None:
    """Pattern B: scheduling-latency canary — asyncio.sleep(0.1) actual elapsed."""
    while not stop.is_set():
        t0 = time.monotonic()
        await asyncio.sleep(CANARY_INTERVAL_S)
        elapsed = time.monotonic() - t0
        _canary_samples.append((time.monotonic(), max(0.0, (elapsed - CANARY_INTERVAL_S) * 1000)))


def _load_queries(path: Path, n: int | None) -> list[str]:
    qs = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return qs[:n] if n else qs


def _build_engine_summary(
    events: list[tuple[str, str, float]],
    all_statuses: dict[str, str],
) -> dict[str, dict]:
    """Per-engine analysis from events captured during one query."""
    by_eng: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for eng, evt, ts in events:
        by_eng[eng].append((evt, ts))

    summary = {}
    for eng in set(all_statuses) | set(by_eng):
        evts = by_eng.get(eng, [])
        enter_ts = next((ts for e, ts in evts if e == "enter"), None)
        exit_item = next(((e, ts) for e, ts in reversed(evts) if e.startswith("exit_")), None)
        exit_class = exit_item[0][len("exit_"):] if exit_item else "none"
        dur_ms = round((exit_item[1] - enter_ts) * 1000) if (enter_ts and exit_item) else None
        summary[eng] = {
            "status": all_statuses.get(eng, "—"),
            "entered": enter_ts is not None,
            "lock_granted": any(e == "lock_granted" for e, _ in evts),
            "lock_released": any(e == "lock_released" for e, _ in evts),
            "lock_stuck": any(e == "lock_stuck" for e, _ in evts),
            "exit_class": exit_class,
            "dur_ms": dur_ms,
        }
    return summary


def _discriminator(eng_summary: dict[str, dict]) -> str:
    """Classify query: ok / B / A-lock / A-sleep / C / mixed."""
    rs = [d for d in eng_summary.values() if d["status"] == "RATE_SKIP"]
    if not rs:
        return "ok"
    n = len(rs)
    n_ent = sum(1 for d in rs if d["entered"])
    n_lg = sum(1 for d in rs if d["lock_granted"])
    n_ok = sum(1 for d in rs if d["exit_class"] == "ok")
    n_err = sum(1 for d in rs if d["exit_class"].startswith("err:"))
    if n_ent == 0:
        return "B"
    if n_ok == n:
        return "C"
    if n_lg == 0:
        return "A-lock"
    if n_err > 0:
        return "A-sleep"
    return f"mixed(ent={n_ent} lg={n_lg} ok={n_ok} err={n_err}/{n})"


def _dump_smoke(events: list, eng_summary: dict) -> None:
    print(f"  total events: {len(events)}", file=sys.stderr)
    for eng in sorted(eng_summary):
        d = eng_summary[eng]
        print(
            f"    {eng:<22} entered={d['entered']} lg={d['lock_granted']} "
            f"lr={d['lock_released']} ls={d['lock_stuck']} "
            f"exit={d['exit_class']:<22} dur={d['dur_ms']}ms",
            file=sys.stderr,
        )


def _sample_category(ts: float, records: list[dict]) -> str:
    for r in records:
        if r["t_start"] <= ts < r["t_end"]:
            return r["category"]
    return "between"


def _pct(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (k - lo) * (s[hi] - s[lo])


def _canary_stats(records: list[dict]) -> dict[str, dict]:
    cold_cutoff = PROBE_START + COLD_START_SKIP_S
    by_cat: dict[str, list[float]] = defaultdict(list)
    for ts, lat in _canary_samples:
        if ts < cold_cutoff:
            continue
        cat = _sample_category(ts, records)
        if cat != "between":
            by_cat[cat].append(lat)

    def _s(data: list[float]) -> dict:
        if not data:
            return {"n": 0, "p50": 0.0, "p99": 0.0, "max": 0.0}
        return {"n": len(data), "p50": round(_pct(data, 50), 1),
                "p99": round(_pct(data, 99), 1), "max": round(max(data), 1)}

    return {k: _s(by_cat.get(k, [])) for k in ("normal", "empty", "zero_cascade")}


def _agg_ratios(records: list[dict]) -> tuple:
    """Avg entered/lg/ok/err ratios + p99 dur_ms for RATE_SKIP engines across query set."""
    ratios_ent, ratios_lg, ratios_ok, ratios_err, durs = [], [], [], [], []
    for r in records:
        rs = [d for d in r["eng_summary"].values() if d["status"] == "RATE_SKIP"]
        n_rs = len(rs) or 1
        ratios_ent.append(sum(1 for d in rs if d["entered"]) / n_rs)
        ratios_lg.append(sum(1 for d in rs if d["lock_granted"]) / n_rs)
        ratios_ok.append(sum(1 for d in rs if d["exit_class"] == "ok") / n_rs)
        ratios_err.append(sum(1 for d in rs if d["exit_class"].startswith("err:")) / n_rs)
        durs += [d["dur_ms"] for d in rs if d["dur_ms"] is not None]
    mn = statistics.mean
    dp99: int | str = round(_pct(durs, 99)) if durs else "—"
    return (round(mn(ratios_ent), 2), round(mn(ratios_lg), 2),
            round(mn(ratios_ok), 2), round(mn(ratios_err), 2), dp99)


def _overall_disc(records: list[dict]) -> str:
    zc = [r["disc"] for r in records if r["category"] == "zero_cascade"]
    if not zc:
        return "no_cascade"
    counts: dict[str, int] = defaultdict(int)
    for d in zc:
        counts[d] += 1
    return max(counts, key=lambda k: counts[k])


def _write_report(records: list[dict], cascade_ok: bool, zero_n: int) -> Path:
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"acquire_probe_{ts_str}.md"
    od = _overall_disc(records)
    cstats = _canary_stats(records)
    empty_n = sum(1 for r in records if r["category"] == "empty")

    lines: list[str] = [
        f"# Acquire Probe Report — {ts_str}",
        "",
        f"**Overall discriminator:** {od}  ",
        f"**Cascade reproduced:** {cascade_ok} ({zero_n}/{len(records)} zero_cascade)  ",
        f"**Empty queries:** {empty_n}  ",
        f"**Total acquire events:** {len(_acq_events)}  ",
        "",
        "---",
        "",
        "## Per-Query Summary",
        "",
        "| # | Query | cat | disc | total_ms | ent/rs | lg/rs | ok/rs | err/rs |",
        "|---|-------|-----|------|----------|--------|-------|-------|--------|",
    ]
    for r in records:
        rs = [d for d in r["eng_summary"].values() if d["status"] == "RATE_SKIP"]
        n_rs = len(rs)
        n_ent = sum(1 for d in rs if d["entered"])
        n_lg = sum(1 for d in rs if d["lock_granted"])
        n_ok = sum(1 for d in rs if d["exit_class"] == "ok")
        n_err = sum(1 for d in rs if d["exit_class"].startswith("err:"))
        q = r["query"][:38].replace("|", "\\|")
        lines.append(
            f"| {r['qi']} | {q} | {r['category']} | {r['disc']} "
            f"| {r['total_ms']} | {n_ent}/{n_rs} | {n_lg}/{n_rs} | {n_ok}/{n_rs} | {n_err}/{n_rs} |"
        )

    zc_records = [r for r in records if r["category"] == "zero_cascade"]
    lines += ["", "## Zero-Cascade Per-Engine Detail", ""]
    if not zc_records:
        lines.append("*No zero_cascade queries in this run.*")
    else:
        lines += [
            "| query | engine | status | entered | lock_granted | lock_released | lock_stuck | exit_class | dur_ms |",
            "|-------|--------|--------|---------|--------------|---------------|------------|------------|--------|",
        ]
        for r in zc_records:
            q = r["query"][:28].replace("|", "\\|")
            for eng in sorted(r["eng_summary"]):
                d = r["eng_summary"][eng]
                yn = lambda b: "Y" if b else "N"  # noqa: E731
                lines.append(
                    f"| {q} | {eng} | {d['status']} "
                    f"| {yn(d['entered'])} | {yn(d['lock_granted'])} "
                    f"| {yn(d['lock_released'])} | {yn(d['lock_stuck'])} "
                    f"| {d['exit_class']} | {d['dur_ms'] or '—'} |"
                )

    lines += [
        "",
        "## Aggregate by Category",
        "",
        "Ratios = fraction of RATE_SKIP engines per query, averaged over queries in category.",
        "",
        "| Category | n_q | avg_ent | avg_lg | avg_ok | avg_err | p99_dur_ms |",
        "|----------|-----|---------|--------|--------|---------|------------|",
    ]
    for cat in ("normal", "empty", "zero_cascade"):
        cat_rec = [r for r in records if r["category"] == cat]
        if not cat_rec:
            lines.append(f"| {cat} | 0 | — | — | — | — | — |")
            continue
        ent, lg, ok, err, dp99 = _agg_ratios(cat_rec)
        lines.append(f"| {cat} | {len(cat_rec)} | {ent} | {lg} | {ok} | {err} | {dp99} |")

    lines += [
        "",
        "## Pattern B Canary — Scheduling Latency",
        "",
        "| Category | n | p50 ms | p99 ms | max ms |",
        "|----------|---|--------|--------|--------|",
    ]
    for cat in ("normal", "empty", "zero_cascade"):
        s = cstats[cat]
        lines.append(f"| {cat} | {s['n']} | {s['p50']} | {s['p99']} | {s['max']} |")

    lines += [
        "",
        "## Verdict",
        "",
        f"**{od}**",
        "",
        "| Label | Meaning |",
        "|-------|---------|",
        "| B | acquire() Task never scheduled — asyncio scheduling gap |",
        "| A-lock | Task entered, blocked on lock — Python 3.14 Lock non-release under CancelledError |",
        "| A-sleep | Task got lock, blocked on asyncio.sleep(backoff_s) — expected only for Google |",
        "| C | acquire() returned ok — bug lies downstream |",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_findings(records: list[dict], report_path: Path, cascade_ok: bool, zero_n: int) -> Path:
    path = FINDINGS_DIR / "02_acquire_probe.md"
    od = _overall_disc(records)
    cstats = _canary_stats(records)
    s_zc = cstats["zero_cascade"]
    s_norm = cstats["normal"]
    report_rel = report_path.relative_to(Path(__file__).parent.parent.parent)

    zc_records = [r for r in records if r["category"] == "zero_cascade"]
    if zc_records:
        ent, lg, ok, err, dp99 = _agg_ratios(zc_records)
    else:
        ent = lg = ok = err = dp99 = "—"

    normal_n = sum(1 for r in records if r["category"] == "normal")
    empty_n = sum(1 for r in records if r["category"] == "empty")

    disc_text = {
        "B": (
            "**B wins.** `acquire()` Tasks were never started — `asyncio.wait_for` timeout fired "
            "before the inner Task got a scheduler turn. Event loop IS free (canary confirms), so "
            "the scheduling gap is specific to how `asyncio.wait_for` + `asyncio.gather` interact "
            "in Python 3.14 with a long-sleeping peer Task (Google's backoff sleep)."
        ),
        "A-lock": (
            "**A-lock wins.** `acquire()` Tasks entered (`enter` recorded) but never received the "
            "lock (`lock_granted` absent). Consistent with Python 3.14 `asyncio.Lock.__aexit__` "
            "failing to release the lock under `CancelledError` propagated via `asyncio.wait_for` "
            "timeout. Each cancelled acquire() leaves `self._lock` held. The next query's "
            "`acquire()` blocks on `async with self._lock:` indefinitely — times out again — "
            "perpetuating the cascade across all subsequent queries."
        ),
        "A-sleep": (
            "**A-sleep wins.** `acquire()` Tasks entered AND received the lock (`lock_granted` "
            "present) but timed out inside `asyncio.sleep(backoff_s)`. Expected for Google "
            "(backoff set by CAPTCHA). If non-Google engines also show this, their `backoff_until` "
            "was set unexpectedly — investigate `backoff()` call sites."
        ),
        "C": (
            "**C wins.** All `acquire()` calls completed normally (exit_ok). RATE_SKIP is assigned "
            "outside `acquire()` — investigate `_engine_with_timing` return path."
        ),
        "no_cascade": (
            "**no_cascade.** Zero cascade did not reproduce. Instrumentation may be interfering "
            "with timing. Data INVALID."
        ),
    }.get(od, f"**{od}** — mixed result, see per-query detail table in report.")

    lines = [
        "# Bee CDP Starvation — Phase 2 Acquire Probe",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ",
        f"**Verdict:** {od}  ",
        f"**Cascade reproduced:** {cascade_ok} ({zero_n}/{len(records)} zero_cascade)  ",
        f"**Report:** `{report_rel}`  ",
        "",
        "---",
        "",
        "## Hypothesis",
        "",
        "Phase 1 REFUTED CDP event-loop starvation (scheduling latency p99=1.4ms; 0 CDP events",
        "during zero_cascade). Chrome is silent. Event loop is free. Yet all 9+ engines show",
        "RATE_SKIP with rate_wait_ms≈5000ms (=RATE_WAIT_TIMEOUT). Three candidates:",
        "",
        "- **B:** `asyncio.wait_for` timeout fires before inner `acquire()` Task is scheduled.",
        "- **A-lock:** Task runs, enters `async with self._lock:`, blocks (stale lock from prior",
        "  cancelled acquire() where Python 3.14 `Lock.__aexit__` did not release).",
        "- **A-sleep:** Task runs, gets lock, blocks on `asyncio.sleep(backoff_s)` inside.",
        "  Plausible only for Google (backoff set by CAPTCHA). Non-Google have no backoff.",
        "- **C:** acquire() completes fine — bug is downstream of acquire().",
        "",
        "## Instrumentation",
        "",
        "Two monkey-patches on `RateLimiter` class (applied before search_web import):",
        "",
        "- **`acquire()` wrapper** — records `enter`, `exit_ok`, `exit_err:<class>` per engine.",
        "- **`__init__` wrapper** → `_WatchedLock` replaces `self._lock` — records",
        "  `lock_attempt`, `lock_granted`, `lock_released`/`lock_stuck` via Lock wrappers.",
        "  `lock_stuck` = lock.locked() still True after __aexit__ returns (non-release signal).",
        "",
        "Pattern B canary re-runs for triangulation (same as Phase 1).",
        "",
        "## Key Numbers",
        "",
        "| Category | n_q | avg_ent | avg_lg | avg_ok | avg_err | dur_p99_ms | canary_p99_ms |",
        "|----------|-----|---------|--------|--------|---------|------------|---------------|",
        f"| normal | {normal_n} | — | — | — | — | — | {s_norm['p99']} |",
        f"| empty | {empty_n} | — | — | — | — | — | — |",
        f"| zero_cascade | {zero_n} | {ent} | {lg} | {ok} | {err} | {dp99} | {s_zc['p99']} |",
        "",
        "## Verdict",
        "",
        disc_text,
        "",
        "## Next Steps",
        "",
        "Pending (bead `searxng-bee`):",
    ]
    if od == "A-lock":
        lines += [
            "- Write minimal Python 3.14 repro: `asyncio.wait_for(coro_that_holds_lock, 0.001)` —",
            "  check if `lock.locked()` is True after timeout. If yes: confirmed Python 3.14 regression.",
            "- Fix option 1: remove `asyncio.Lock` from `RateLimiter.acquire()`. Concurrent",
            "  calls per engine are structurally safe (gather fanout calls each engine once per query).",
            "- Fix option 2: in `search_batch_workflow`, on CAPTCHA detection, reset all engine",
            "  limiters' `_lock = asyncio.Lock()` before proceeding to next query.",
        ]
    elif od == "B":
        lines += [
            "- Minimal repro: 9 concurrent `asyncio.wait_for(immediate_coro, 5.0)` with one",
            "  peer Task doing `asyncio.sleep(60)` — confirm inner Tasks complete before timeout.",
            "- Check Python 3.14 `asyncio.wait_for` source for Task scheduling deferral.",
        ]
    elif od == "A-sleep":
        lines += [
            "- Identify which non-Google engines have `backoff_until` set and why.",
            "- Check `backoff()` call sites for unintended cross-engine propagation.",
        ]
    elif od == "C":
        lines += ["- Investigate `_engine_with_timing` post-acquire status assignment."]
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RateLimiter.acquire() instrumentation probe — Phase 2 bee."
    )
    parser.add_argument("--max-queries", dest="max_queries", type=int, default=None,
                        help="Limit to first N queries (default: all from queries.txt)")
    parser.add_argument("--smoke", action="store_true",
                        help="4-query dry-run: verify instrumentation live, no report written")
    args = parser.parse_args()
    if args.smoke and args.max_queries is None:
        args.max_queries = 4
    asyncio.run(run_acquire_probe(args.max_queries, args.smoke))
