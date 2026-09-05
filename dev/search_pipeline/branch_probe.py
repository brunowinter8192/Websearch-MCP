#!/usr/bin/env python3
"""Sleep-branch discriminator probe — Phase 3 bee investigation.

Discriminates WHICH of the two asyncio.sleep branches inside RateLimiter.acquire()
fires during zero_cascade queries (all 9 engines RATE_SKIP simultaneously):

  backoff_sleep_attempt  — if now < self._backoff_until:  (rate_limiter.py line 36)
  tokencap_sleep_attempt — if len(self._tokens) >= self._max_requests:  (line 47)

Phase 2 confirmed A-sleep: all 9 engines enter acquire(), get lock, sleep, get cancelled
at ~5001ms. Phase 2 inferred backoff-cascade but did NOT distinguish which branch fired.
Phase 3 adds branch-level events to settle this.

Structural discriminator: 6 engines have .backoff() call in engine source (google,
google_scholar, lobsters, mojeek, duckduckgo, semantic_scholar). 4 do NOT (crossref,
openalex, stack_exchange, open_library). Backoff-immune engines cannot enter the backoff
branch unless an unknown code path calls .backoff() on their limiter.

Usage:
    ./venv/bin/python3 dev/search_pipeline/branch_probe.py [--max-queries N] [--smoke]

    --smoke: 4-query dry-run. Prints per-engine detail to stderr. No report written.
             Run before full probe to verify instrumentation is live.

Output (full run only):
    dev/search_pipeline/md/branch_probe_<ts>.md
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

# Monkey-patch RateLimiter.acquire BEFORE any src.search imports.
# Full replacement (not wrapper) — byte-identical body to rate_limiter.py:acquire()
# with branch-discriminator event-emits before each asyncio.sleep.
_rl_mod = importlib.import_module("src.search.rate_limiter")
RateLimiter = _rl_mod.RateLimiter

# (engine_name, event, ts_monotonic, wait_s_or_None)
_acq_events: list[tuple[str, str, float, float | None]] = []

# per-query pre-call snapshots: list of {qi, engines: {name -> {backoff_remaining_s, len_tokens, ...}}}
_pre_snapshots: list[dict] = []


def _get_name(limiter) -> str:
    """Reverse-lookup engine name from _limiters dict by instance identity."""
    for name, lim in _rl_mod._limiters.items():
        if lim is limiter:
            return name
    return "unknown"


async def _replacement_acquire(self) -> None:
    """Byte-identical to rate_limiter.py:acquire() + branch-discriminator event-emits."""
    name = _get_name(self)
    _acq_events.append((name, "enter", time.monotonic(), None))
    try:
        async with self._lock:
            now = time.monotonic()

            # Respect backoff from 429/403 responses
            if now < self._backoff_until:
                wait = self._backoff_until - now
                _acq_events.append((name, "backoff_sleep_attempt", time.monotonic(), wait))
                await asyncio.sleep(wait)
                now = time.monotonic()

            # Remove tokens older than the window
            self._tokens = [t for t in self._tokens if now - t < self._window_seconds]

            # If at capacity, wait until the oldest token expires
            if len(self._tokens) >= self._max_requests:
                oldest = self._tokens[0]
                wait = self._window_seconds - (now - oldest)
                if wait > 0:
                    _acq_events.append((name, "tokencap_sleep_attempt", time.monotonic(), wait))
                    await asyncio.sleep(wait)
                    now = time.monotonic()
                    self._tokens = [t for t in self._tokens if now - t < self._window_seconds]

            self._tokens.append(time.monotonic())
        _acq_events.append((name, "exit_ok", time.monotonic(), None))
    except BaseException as e:
        _acq_events.append((name, f"exit_err:{type(e).__name__}", time.monotonic(), None))
        raise


RateLimiter.acquire = _replacement_acquire
# End monkey-patch — src.search imports follow

_browser_mod = importlib.import_module("src.search.browser")
_search_mod = importlib.import_module("src.search.search_web")
close_browser = _browser_mod.close_browser
search_web_workflow = _search_mod.search_web_workflow

SCRIPT_DIR = Path(__file__).parent
QUERIES_FILE = SCRIPT_DIR / "queries.txt"
REPORT_DIR = SCRIPT_DIR / "md"
FINDINGS_DIR = SCRIPT_DIR / "md"

# 4 engines have NO .backoff() call in engine source — cannot enter backoff branch legitimately
BACKOFF_IMMUNE = frozenset({"crossref", "openalex", "stack_exchange", "open_library"})

CANARY_INTERVAL_S = 0.1
COLD_START_SKIP_S = 5.0

_canary_samples: list[tuple[float, float]] = []  # (ts_mono, latency_ms)
PROBE_START: float = 0.0


# ORCHESTRATOR

async def run_branch_probe(max_queries: int | None, smoke: bool) -> None:
    global PROBE_START
    PROBE_START = time.monotonic()

    queries = _load_queries(QUERIES_FILE, max_queries)
    print(f"branch probe | queries={len(queries)} smoke={smoke}", file=sys.stderr)

    stop_canary = asyncio.Event()
    canary_task = asyncio.create_task(_canary_monitor(stop_canary))

    query_records: list[dict] = []
    try:
        for qi, query in enumerate(queries, 1):
            n_before = len(_acq_events)
            snap = _snapshot_limiters(qi)
            _pre_snapshots.append(snap)

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
            eng_detail = _build_engine_detail(new_events, all_statuses, snap)
            disc = _query_discriminator(eng_detail)

            record = {
                "qi": qi, "query": query, "t_start": t_start, "t_end": t_end,
                "duration_s": t_end - t_start, "google_status": google_status,
                "all_statuses": all_statuses, "category": category,
                "total_ms": timings.get("total_ms", 0),
                "eng_detail": eng_detail, "disc": disc, "snap": snap,
            }
            query_records.append(record)

            flag = {"empty": "⚡", "zero_cascade": "🚫", "normal": ""}[category]
            print(
                f"[{qi:2}/{len(queries)}] {query[:48]!r:50} "
                f"cat={category:<12} disc={disc:<24} ev={len(new_events)} {flag}",
                file=sys.stderr,
            )
            if smoke:
                _dump_smoke(new_events, eng_detail, snap)

    finally:
        stop_canary.set()
        await canary_task
        await close_browser()

    zero_n = sum(1 for r in query_records if r["category"] == "zero_cascade")
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
            "\n🛑 STOP: cascade did not reproduce "
            f"({zero_n}/{len(query_records)} zero_cascade < min {min_expected}). "
            "Instrumentation may be interfering. Data INVALID — do not proceed.",
            file=sys.stderr,
        )
        # Write minimal note for audit trail
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        stop_path = REPORT_DIR / f"branch_probe_{ts_str}_STOP.md"
        stop_path.write_text(
            f"# Branch Probe STOP — {ts_str}\n\n"
            f"Cascade did not reproduce: {zero_n}/{len(query_records)} zero_cascade "
            f"(min expected {min_expected}). Instrumentation interference suspected.\n",
            encoding="utf-8",
        )
        print(f"STOP note: {stop_path}", file=sys.stderr)
        return

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    rp = _write_report(query_records, cascade_ok, zero_n)
    fp = _write_findings(query_records, rp, cascade_ok, zero_n)
    print(f"\nReport:   {rp}", file=sys.stderr)
    print(f"Findings: {fp}", file=sys.stderr)


# FUNCTIONS

async def _canary_monitor(stop: asyncio.Event) -> None:
    """Pattern B canary — asyncio.sleep(0.1) actual elapsed, measures scheduling latency."""
    while not stop.is_set():
        t0 = time.monotonic()
        await asyncio.sleep(CANARY_INTERVAL_S)
        elapsed = time.monotonic() - t0
        _canary_samples.append((time.monotonic(), max(0.0, (elapsed - CANARY_INTERVAL_S) * 1000)))


def _load_queries(path: Path, n: int | None) -> list[str]:
    qs = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return qs[:n] if n else qs


def _snapshot_limiters(qi: int) -> dict:
    """Layer 1: per-engine limiter state immediately before search_web_workflow call."""
    now = time.monotonic()
    engines = {}
    for name, lim in _rl_mod._limiters.items():
        br = max(0.0, lim._backoff_until - now)
        tok_count = sum(1 for t in lim._tokens if now - t < lim._window_seconds)
        engines[name] = {
            "backoff_remaining_s": round(br, 2),
            "len_tokens": tok_count,
            "max_requests": lim._max_requests,
            "window_seconds": lim._window_seconds,
        }
    return {"qi": qi, "engines": engines}


def _build_engine_detail(
    events: list[tuple[str, str, float, float | None]],
    all_statuses: dict[str, str],
    snap: dict,
) -> dict[str, dict]:
    """Per-engine Layer-2 analysis from acquire() events captured during one query."""
    by_eng: dict[str, list[tuple[str, float, float | None]]] = defaultdict(list)
    for eng, evt, ts, wait in events:
        by_eng[eng].append((evt, ts, wait))

    detail = {}
    for eng in set(all_statuses) | set(by_eng):
        evts = by_eng.get(eng, [])
        enter_ts = next((ts for e, ts, _ in evts if e == "enter"), None)
        exit_item = next(((e, ts) for e, ts, _ in reversed(evts) if e.startswith("exit_")), None)
        exit_class = exit_item[0][len("exit_"):] if exit_item else "none"
        dur_ms = round((exit_item[1] - enter_ts) * 1000) if (enter_ts and exit_item) else None

        backoff_ev = next(((ts, w) for e, ts, w in evts if e == "backoff_sleep_attempt"), None)
        tokencap_ev = next(((ts, w) for e, ts, w in evts if e == "tokencap_sleep_attempt"), None)

        pre = snap["engines"].get(eng, {})
        detail[eng] = {
            "status": all_statuses.get(eng, "—"),
            "pre_backoff_remaining_s": pre.get("backoff_remaining_s", "?"),
            "pre_len_tokens": pre.get("len_tokens", "?"),
            "backoff_attempt": backoff_ev is not None,
            "backoff_wait_s": round(backoff_ev[1], 1) if backoff_ev else None,
            "tokencap_attempt": tokencap_ev is not None,
            "tokencap_wait_s": round(tokencap_ev[1], 1) if tokencap_ev else None,
            "exit_class": exit_class,
            "dur_ms": dur_ms,
        }
    return detail


def _query_discriminator(eng_detail: dict[str, dict]) -> str:
    """Classify query by which branch fired across RATE_SKIP engines."""
    rs = [d for d in eng_detail.values() if d["status"] == "RATE_SKIP"]
    if not rs:
        return "ok"
    n = len(rs)
    n_ba = sum(1 for d in rs if d["backoff_attempt"])
    n_tc = sum(1 for d in rs if d["tokencap_attempt"])
    n_ni = sum(1 for d in rs if not d["backoff_attempt"] and not d["tokencap_attempt"])
    if n_tc == n and n_ba == 0:
        return "tokencap"
    if n_ba == n and n_tc == 0:
        return "backoff"
    if n_ba > 0 and n_tc > 0:
        return f"mixed(ba={n_ba} tc={n_tc} ni={n_ni}/{n})"
    if n_ni == n:
        return "neither"
    return f"partial(ba={n_ba} tc={n_tc} ni={n_ni}/{n})"


def _dump_smoke(
    events: list[tuple[str, str, float, float | None]],
    eng_detail: dict[str, dict],
    snap: dict,
) -> None:
    print(f"  total events: {len(events)}", file=sys.stderr)
    for eng in sorted(eng_detail):
        d = eng_detail[eng]
        pre = snap["engines"].get(eng, {})
        imm = "(I)" if eng in BACKOFF_IMMUNE else "   "
        print(
            f"    {eng:<22}{imm} pre_br={pre.get('backoff_remaining_s', '?'):>6}s "
            f"pre_tok={pre.get('len_tokens', '?')}  "
            f"backoff={d['backoff_attempt']} wait={d['backoff_wait_s']}  "
            f"tokencap={d['tokencap_attempt']} wait={d['tokencap_wait_s']}  "
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
        return {
            "n": len(data),
            "p50": round(_pct(data, 50), 1),
            "p99": round(_pct(data, 99), 1),
            "max": round(max(data), 1),
        }

    return {k: _s(by_cat.get(k, [])) for k in ("normal", "empty", "zero_cascade")}


def _overall_verdict(records: list[dict]) -> str:
    zc = [r["disc"] for r in records if r["category"] == "zero_cascade"]
    if not zc:
        return "no_cascade"
    counts: dict[str, int] = defaultdict(int)
    for d in zc:
        key = "mixed" if (d.startswith("mixed") or d.startswith("partial")) else d
        counts[key] += 1
    return max(counts, key=lambda k: counts[k])


def _write_report(records: list[dict], cascade_ok: bool, zero_n: int) -> Path:
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"branch_probe_{ts_str}.md"
    verdict = _overall_verdict(records)
    cstats = _canary_stats(records)
    empty_n = sum(1 for r in records if r["category"] == "empty")

    lines: list[str] = [
        f"# Branch Probe Report — {ts_str}",
        "",
        f"**Overall verdict:** {verdict}  ",
        f"**Cascade reproduced:** {cascade_ok} ({zero_n}/{len(records)} zero_cascade)  ",
        f"**Empty queries:** {empty_n}  ",
        f"**Total acquire events:** {len(_acq_events)}  ",
        "",
        "---",
        "",
        "## Per-Query Summary",
        "",
        "| # | Query | cat | disc | total_ms |",
        "|---|-------|-----|------|----------|",
    ]
    for r in records:
        q = r["query"][:38].replace("|", "\\|")
        lines.append(f"| {r['qi']} | {q} | {r['category']} | {r['disc']} | {r['total_ms']} |")

    # Central discriminator table
    zc_records = [r for r in records if r["category"] == "zero_cascade"]
    lines += [
        "",
        "## Central Discriminator — Zero-Cascade Queries",
        "",
        "pre_br = backoff_remaining_s at query entry; pre_tok = len(tokens) in window;",
        "ba = backoff_sleep_attempt fired; tc = tokencap_sleep_attempt fired;",
        "wait = planned asyncio.sleep duration (before wait_for cancels at 5s).",
        "*(I) = backoff-immune engine (no .backoff() call in engine source)*",
        "",
    ]
    if not zc_records:
        lines.append("*No zero_cascade queries in this run.*")
    else:
        lines += [
            "| q# | engine | I | pre_br_s | pre_tok | ba | wait_ba_s | tc | wait_tc_s | exit | dur_ms |",
            "|----|--------|---|----------|---------|----|-----------|----|-----------|------|--------|",
        ]
        for r in zc_records:
            for eng in sorted(r["eng_detail"]):
                d = r["eng_detail"][eng]
                if d["status"] != "RATE_SKIP":
                    continue
                imm = "I" if eng in BACKOFF_IMMUNE else ""
                ba = "Y" if d["backoff_attempt"] else "N"
                tc = "Y" if d["tokencap_attempt"] else "N"
                bw = f"{d['backoff_wait_s']:.1f}" if d["backoff_wait_s"] is not None else "—"
                tw = f"{d['tokencap_wait_s']:.1f}" if d["tokencap_wait_s"] is not None else "—"
                lines.append(
                    f"| {r['qi']} | {eng} | {imm} "
                    f"| {d['pre_backoff_remaining_s']} | {d['pre_len_tokens']} "
                    f"| {ba} | {bw} | {tc} | {tw} "
                    f"| {d['exit_class']} | {d['dur_ms'] or '—'} |"
                )

    # Pre-query state for first zero_cascade
    first_zc = next((r for r in records if r["category"] == "zero_cascade"), None)
    lines += ["", "## Pre-Query State — First Zero-Cascade Query", ""]
    if first_zc:
        lines.append(f"Query #{first_zc['qi']}: `{first_zc['query']}`")
        lines += [
            "",
            "| engine | I | backoff_remaining_s | len_tokens | max_requests | predicted_branch |",
            "|--------|---|--------------------:|----------:|:-------------|:-----------------|",
        ]
        for eng, s in sorted(first_zc["snap"]["engines"].items()):
            imm = "I" if eng in BACKOFF_IMMUNE else ""
            if s["backoff_remaining_s"] > 0:
                pred = "backoff(!IMMUNE)" if eng in BACKOFF_IMMUNE else "backoff"
            elif s["len_tokens"] >= s["max_requests"]:
                pred = "tokencap"
            else:
                pred = "neither(?)"
            lines.append(
                f"| {eng} | {imm} | {s['backoff_remaining_s']} | {s['len_tokens']} "
                f"| {s['max_requests']} | {pred} |"
            )
    else:
        lines.append("*No zero_cascade queries — snapshot N/A.*")

    # Branch-fire aggregate by category
    lines += [
        "",
        "## Branch-Fire Aggregate by Category",
        "",
        "Averages = engines-per-query that fired each branch, over all queries in category.",
        "",
        "| category | n_q | avg_backoff_eng | avg_tokencap_eng | avg_neither_eng | canary_p99_ms |",
        "|----------|-----|----------------:|-----------------:|----------------:|---------------|",
    ]
    for cat in ("normal", "empty", "zero_cascade"):
        cat_rec = [r for r in records if r["category"] == cat]
        if not cat_rec:
            lines.append(f"| {cat} | 0 | — | — | — | — |")
            continue
        ba_avgs, tc_avgs, ni_avgs = [], [], []
        for r in cat_rec:
            rs = [d for d in r["eng_detail"].values() if d["status"] == "RATE_SKIP"]
            n = len(rs) or 1
            ba_avgs.append(sum(1 for d in rs if d["backoff_attempt"]) / n)
            tc_avgs.append(sum(1 for d in rs if d["tokencap_attempt"]) / n)
            ni_avgs.append(
                sum(1 for d in rs if not d["backoff_attempt"] and not d["tokencap_attempt"]) / n
            )
        mn = statistics.mean
        cs = cstats[cat]
        lines.append(
            f"| {cat} | {len(cat_rec)} | {round(mn(ba_avgs), 2)} "
            f"| {round(mn(tc_avgs), 2)} | {round(mn(ni_avgs), 2)} | {cs['p99']} |"
        )

    # Canary detail
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
        "## Verdict Key",
        "",
        "| Label | Meaning |",
        "|-------|---------|",
        "| tokencap | All RATE_SKIP engines fired tokencap branch (len(tokens) >= max_requests) |",
        "| backoff | All RATE_SKIP engines fired backoff branch (now < _backoff_until) |",
        "| mixed(ba=X tc=Y) | Both branches fired across engines within a single query |",
        "| neither | RATE_SKIP engines: CancelledError but no sleep branch reached |",
        "| ok | No RATE_SKIP engines |",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_findings(records: list[dict], report_path: Path, cascade_ok: bool, zero_n: int) -> Path:
    path = FINDINGS_DIR / "03_branch_probe.md"
    verdict = _overall_verdict(records)
    cstats = _canary_stats(records)
    report_rel = report_path.relative_to(Path(__file__).parent.parent.parent)
    ts_str = datetime.now().strftime("%Y-%m-%d")

    zc_records = [r for r in records if r["category"] == "zero_cascade"]

    avg_ba = avg_tc = avg_ni = "—"
    immune_ba_any = False
    if zc_records:
        ba_per, tc_per, ni_per = [], [], []
        for r in zc_records:
            rs = [d for d in r["eng_detail"].values() if d["status"] == "RATE_SKIP"]
            n = len(rs) or 1
            ba_per.append(sum(1 for d in rs if d["backoff_attempt"]) / n)
            tc_per.append(sum(1 for d in rs if d["tokencap_attempt"]) / n)
            ni_per.append(
                sum(1 for d in rs if not d["backoff_attempt"] and not d["tokencap_attempt"]) / n
            )
        mn = statistics.mean
        avg_ba = round(mn(ba_per), 2)
        avg_tc = round(mn(tc_per), 2)
        avg_ni = round(mn(ni_per), 2)
        immune_ba_any = any(
            d["backoff_attempt"]
            for r in zc_records
            for eng, d in r["eng_detail"].items()
            if eng in BACKOFF_IMMUNE and d["status"] == "RATE_SKIP"
        )

    s_zc = cstats["zero_cascade"]

    verdict_text = {
        "tokencap": (
            "**tokencap-path wins.** ALL RATE_SKIP engines — including backoff-immune engines "
            "(crossref, openalex, stack_exchange, open_library) — fired the "
            "`len(tokens) >= max_requests` branch. No engine fired the backoff branch. "
            "The uniform 4 req/60s cap saturates within the batch-query window: 4 successful "
            "queries in <60s fills each engine's token bucket; the 5th acquire() sleeps waiting "
            "for the oldest token to age out (planned wait ≈ 60s − age_of_oldest_token, typically "
            "40–55s). asyncio.wait_for cancels at 5s → CancelledError → RATE_SKIP. "
            "Phase 2 multi-engine backoff-cascade narrative is INCORRECT for this scenario."
        ),
        "backoff": (
            "**backoff-path wins.** ALL RATE_SKIP engines fired the `if now < _backoff_until:` "
            f"branch. {'Includes backoff-IMMUNE engines (crossref, openalex, stack_exchange, open_library) → an unknown code path calls .backoff() on these limiters. Grep src/ for .backoff() call sites.' if immune_ba_any else 'Only backoff-capable engines fired — consistent with Phase 2 narrative.'} "
            "Phase 2 multi-engine backoff-cascade narrative CONFIRMED."
        ),
        "mixed": (
            f"**mixed.** Both branches fired across engines within zero_cascade queries. "
            f"avg per query: backoff={avg_ba} engines, tokencap={avg_tc} engines, neither={avg_ni}. "
            f"{'Backoff-immune engines appeared in backoff group → unknown .backoff() call site exists. ' if immune_ba_any else ''}"
            "Multi-cause cascade: some engines genuinely backed off, others at token-cap saturation."
        ),
        "neither": (
            "**neither.** RATE_SKIP engines got CancelledError but no sleep branch was entered. "
            "CancelledError arrives before reaching asyncio.sleep — unexpected given Phase 2 "
            "lock_granted=Y. Investigate lock acquisition timing."
        ),
        "no_cascade": (
            "**no_cascade.** Zero cascade did not reproduce — data INVALID."
        ),
    }.get(verdict, f"**{verdict}** — see per-query detail in report.")

    lines: list[str] = [
        "# Bee CDP Starvation — Phase 3 Branch Probe",
        "",
        f"**Date:** {ts_str}  ",
        f"**Verdict:** {verdict}  ",
        f"**Cascade reproduced:** {cascade_ok} ({zero_n}/{len(records)} zero_cascade)  ",
        f"**Report:** `{report_rel}`  ",
        "",
        "---",
        "",
        "## Hypothesis",
        "",
        "Phase 2 confirmed A-sleep: all 9 engines enter `acquire()`, get lock, sleep, get",
        "cancelled at ~5001ms. Phase 2 inferred backoff-cascade (Google CAPTCHA sets",
        "`backoff_until`, non-Google engines follow suit via their own 429/bot-detect calls).",
        "That inference was NOT probe-verified — Phase 2 instrumentation was a wrapper around",
        "the original `acquire()` and did not distinguish which of the two `asyncio.sleep`",
        "branches fired.",
        "",
        "Two branches in `acquire()` (rate_limiter.py):",
        "- **backoff branch** (line 36): `if now < self._backoff_until:` — fires only if engine",
        "  called `.backoff()`. 6 engines have `.backoff()` in source; 4 do NOT.",
        "- **tokencap branch** (line 47): `if len(self._tokens) >= self._max_requests:` — fires",
        "  when 4 tokens in the 60s window. After 4 successful queries in <60s, ANY engine hits this.",
        "",
        "Structural discriminator: crossref, openalex, stack_exchange, open_library have NO",
        "`.backoff()` call in engine source. If they show `backoff_sleep_attempt=Y`, an unknown",
        "code path calls `.backoff()` on them — that would be a new finding.",
        "",
        "## Instrumentation",
        "",
        "- **Layer 1** — `_snapshot_limiters()`: per-engine `{backoff_remaining_s, len_tokens}`",
        "  captured immediately before each `search_web_workflow` call.",
        "- **Layer 2** — `_replacement_acquire()`: full replacement of `RateLimiter.acquire()`",
        "  (NOT a wrapper around original). Byte-identical body + `backoff_sleep_attempt` /",
        "  `tokencap_sleep_attempt` events emitted before each `await asyncio.sleep`.",
        "  Event tuple: `(engine, event, ts_mono, wait_s)`.",
        "- **Layer 3** — canary task (Pattern B, identical to Phase 1+2): scheduling latency.",
        "",
        "No `_WatchedLock` / `__init__` patch (Phase 2 proved lock_granted=Y; lock events unneeded).",
        "",
        "## Key Numbers",
        "",
        "| Category | n_q | avg_backoff_eng/q | avg_tokencap_eng/q | avg_neither_eng/q | canary_p99_ms |",
        "|----------|-----|------------------:|-------------------:|------------------:|:--------------|",
        f"| zero_cascade | {zero_n} | {avg_ba} | {avg_tc} | {avg_ni} | {s_zc['p99']} |",
        "",
        "## Verdict",
        "",
        verdict_text,
        "",
    ]

    if immune_ba_any and verdict in ("backoff", "mixed"):
        lines += [
            "## Key Side Finding: Backoff-Immune Engine in Backoff Branch",
            "",
            "crossref / openalex / stack_exchange / open_library showed `backoff_sleep_attempt=Y`",
            "despite having no `.backoff()` call in their engine source. Possible causes:",
            "(a) cross-cutting code in `search_web.py` orchestration calls `.backoff()` on all",
            "    limiters on CAPTCHA/error detection, OR",
            "(b) `get_limiter()` returning a shared instance due to aliased key.",
            "Next step: `grep -rn '\\.backoff()' src/` to locate all call sites.",
            "",
        ]

    lines += [
        "## Next Steps",
        "",
        "Pending (bead `searxng-bee`):",
    ]
    if verdict == "tokencap":
        lines += [
            "- Fix: raise per-engine `max_requests` from 4 to align with `MAX_REQUESTS=10` default,",
            "  OR add inter-query minimum delay in `search_batch_workflow` (≥15s keeps bucket from",
            "  filling in a 60s window with typical 5-10s query durations),",
            "  OR detect token saturation pre-acquire and skip engine gracefully (no 5s wait).",
            "- Phase 2 backoff-cascade narrative was based on inference, not measurement. The",
            "  backoff() calls in engine source are real but NOT the dominant cascade mechanism here.",
        ]
    elif verdict == "backoff":
        lines += [
            "- Identify which non-Google engines have `backoff_until` set and what triggered it.",
            "- Instrument `.backoff()` call sites (6 engines) to log which backend returned 429/403.",
            "- Consider reducing BACKOFF_BASE from 30s or adding per-engine tuning.",
        ]
    elif verdict == "mixed":
        lines += [
            "- For tokencap-affected engines: raise max_requests or add inter-query delay.",
            "- For backoff-affected engines: instrument .backoff() call sites.",
            "- Immune engines in backoff group → grep src/ for unexpected .backoff() calls.",
        ]
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sleep-branch discriminator probe — Phase 3 (backoff vs tokencap)."
    )
    parser.add_argument("--max-queries", dest="max_queries", type=int, default=None,
                        help="Limit to first N queries (default: all from queries.txt)")
    parser.add_argument("--smoke", action="store_true",
                        help="4-query dry-run: verify instrumentation, no report written")
    args = parser.parse_args()
    if args.smoke and args.max_queries is None:
        args.max_queries = 4
    asyncio.run(run_branch_probe(args.max_queries, args.smoke))
