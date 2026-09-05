#!/usr/bin/env python3
"""
Stage 1 — Pool Fetch (value_eval_v3).

Fetches results for 16 (mode, query) pairs (4 modes × 4 queries).
Writes per-pair pool.json + engine_report.md, then engine_report_summary.md.

No URL filter applied — C-methods (BM25, Cross-Encoder) handle topic relevance from
title+snippet. Query modifier (+book / +pdf / +documentation) still biases engine results.

pool.json schema:
  pool      — oracle input + C1/C2'/C3: capped_pool sorted by URL, ALL fields
               (url / title / snippet / engines / min_position / positions)
  pool_full — C2 BM25 vanilla: full_pool (all deduped results) sorted by URL, ALL fields

positions: {engine_name: rank} — per-engine position (additive v3 field; Methods 2-5 RRF).
Invariants: set(engines)==set(positions.keys()), min_position==min(positions.values()).

Oracle workers: read pool[*].{url, title, snippet} only — ignore engines/min_position/positions.

Usage:
  ./venv/bin/python dev/search_pipeline/stage1_pool_fetch.py [--smoke] [--ts-dir PATH]
"""

# INFRASTRUCTURE
import argparse
import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

# From rerank_probe_smoke.py: browser lifecycle + engine fanout (re-exports from src/)
from rerank_probe_smoke import close_browser, _query_engines_concurrent, _select_engines

# From bm25_sweep_smoke.py: pool builder (merge raw results by URL)
from bm25_sweep_smoke import _build_pool

import logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

REPORT_DIR = SCRIPT_DIR / "runs"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MODES = ["general", "pdf", "books", "docs"]

QUERIES = [
    "transformer attention mechanism",
    "postgresql index types btree gin gist performance",
    "python asyncio event loop concurrency",
    "contrastive learning self-supervised representations",
]

SMOKE_MODE  = "general"
SMOKE_QUERY = "transformer attention mechanism"

# NOTE: _STATUS_HINTS duplicated from 11_pipeline_smoke.py, keep in sync manually
# until extracted to shared helper.
# EMPTY_NO_RESULTS/EMPTY_NO_CONTAINER/EMPTY_CONSENT/EMPTY_BLOCK/EMPTY_CONCURRENT_RACE entries
# removed with the guessed-verdict sub-statuses — every empty result now logs bare "EMPTY".
_STATUS_HINTS: dict[str, str] = {
    "TIMEOUT_WATCHDOG":      "watchdog timeout",
    "TIMEOUT_NONCOOP":       "non-cooperative",
    "TIMEOUT_HTTPX":         "httpx timeout",
    "ERROR_BROWSER":         "Chrome error",
    "ERROR_HTTP":            "HTTP error",
    "ERROR_PARSE":           "parse error",
    "ERROR_OTHER":           "unexpected error",
    "RATE_SKIP":             "rate skip",
    "EMPTY":                 "empty",
    "ERROR":                 "error",
}

_MODE_ENGINES = frozenset({"google", "duckduckgo"})


# ORCHESTRATOR

async def run_pool_fetch(smoke: bool, ts_dir_arg: Path | None) -> Path:
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_dir = ts_dir_arg or (REPORT_DIR / f"value_eval_v3_{ts}")
    ts_dir.mkdir(parents=True, exist_ok=True)

    pairs   = [(SMOKE_MODE, SMOKE_QUERY)] if smoke else [(m, q) for m in MODES for q in QUERIES]
    n_pairs = len(pairs)

    selected, _ = _select_engines(None)
    print(f"Engines ({len(selected)}): {', '.join(sorted(selected.keys()))}", file=sys.stderr)
    print(f"Pairs: {n_pairs} | Output: {ts_dir}", file=sys.stderr)
    print(file=sys.stderr)

    summary_rows: list[dict] = []
    try:
        for i, (mode, query) in enumerate(pairs, 1):
            print(f"[{i}/{n_pairs}] mode={mode} | {query}", file=sys.stderr)
            meta = await _run_one_pair(ts_dir, mode, query, selected)
            print(
                f"  raw={meta['raw_count']}  capped={meta['capped_count']}"
                f"  oracle={meta['oracle_count']}"
                f"  fetch={meta['fetch_ms']}ms",
                file=sys.stderr,
            )
            summary_rows.append(meta)
    finally:
        await close_browser()

    _save_engine_summary(ts_dir, summary_rows, ts)
    print(f"\nOutput dir: {ts_dir}", file=sys.stderr)
    return ts_dir


# FUNCTIONS

# Slug for file naming — must match stage3/stage4 _query_slug
def _query_slug(query: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", query.lower())[:30].strip("_")


# Build query_modifier_map for the given mode (None for general)
def _modifier_map(mode: str) -> dict | None:
    if mode == "books": return {e: (lambda q: f"{q} book")          for e in _MODE_ENGINES}
    if mode == "pdf":   return {e: (lambda q: f"{q} pdf")           for e in _MODE_ENGINES}
    if mode == "docs":  return {e: (lambda q: f"{q} documentation") for e in _MODE_ENGINES}
    return None


# Cap raw results to position <= K then dedup into pool dicts
def _build_capped_pool(raw_results: list, K: int) -> list[dict]:
    return _build_pool([r for r in raw_results if r.position <= K])


# Attach positions: {engine: rank} to each pool entry from the matching raw_results slice
def _attach_positions(raw_results: list, pool: list[dict]) -> None:
    pos_map: dict[str, dict[str, int]] = {}
    for r in raw_results:
        if r.url not in pos_map:
            pos_map[r.url] = {}
        eng = pos_map[r.url]
        eng[r.engine] = min(eng.get(r.engine, 999), r.position)
    for m in pool:
        m["positions"] = pos_map.get(m["url"], {})


# Fetch + save pool.json + engine_report.md for one pair; return summary metadata
async def _run_one_pair(ts_dir: Path, mode: str, query: str, selected: dict) -> dict:
    qmm = _modifier_map(mode)

    t0 = time.perf_counter()
    raw_results, engine_stats = await _query_engines_concurrent(
        query, "en", 10, selected, query_modifier_map=qmm
    )
    fetch_ms   = round((time.perf_counter() - t0) * 1000)
    fetched_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    google_count = engine_stats.get("google", {}).get("result_count", 0)
    K            = google_count if google_count > 0 else 10

    full_pool   = _build_pool(raw_results)
    capped_raw  = [r for r in raw_results if r.position <= K]
    capped_pool = _build_pool(capped_raw)
    _attach_positions(raw_results, full_pool)
    _attach_positions(capped_raw, capped_pool)
    oracle_pool = sorted(capped_pool, key=lambda m: m["url"])

    slug = _query_slug(query)
    _save_pool_json(
        ts_dir, mode, slug, query, fetched_ts, google_count,
        oracle_pool, full_pool, len(raw_results), len(capped_pool),
    )
    _save_engine_report(
        ts_dir, mode, slug, query, fetched_ts, engine_stats, oracle_pool,
        len(raw_results), len(capped_pool),
    )

    return {
        "mode":         mode,
        "query":        query,
        "slug":         slug,
        "raw_count":    len(raw_results),
        "capped_count": len(capped_pool),
        "oracle_count": len(oracle_pool),
        "fetch_ms":     fetch_ms,
        "engine_stats": engine_stats,
    }


# Save pool.json — oracle input (pool) + C2 full pool (pool_full)
def _save_pool_json(
    ts_dir: Path, mode: str, slug: str, query: str, fetched_ts: str,
    google_count: int, oracle_pool: list[dict], full_pool: list[dict],
    raw_count: int, capped_count: int,
) -> None:
    def _item(m: dict) -> dict:
        return {
            "url":          m["url"],
            "title":        (m.get("title") or "").strip(),
            "snippet":      (m.get("snippet") or "").strip(),
            "engines":      m.get("engines", []),
            "min_position": m.get("min_position", 999),
            "positions":    m.get("positions", {}),
        }

    data = {
        "mode":         mode,
        "query":        query,
        "fetched_ts":   fetched_ts,
        "google_count": google_count,
        "pool_sizes": {
            "raw":             raw_count,
            "capped":          capped_count,
            "filtered_capped": len(oracle_pool),  # = capped (no URL filter)
        },
        "pool":      [_item(m) for m in oracle_pool],
        "pool_full": [_item(m) for m in sorted(full_pool, key=lambda m: m["url"])],
    }
    (ts_dir / f"{mode}_{slug}_pool.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# Write engine_report.md for one pair
def _save_engine_report(
    ts_dir: Path, mode: str, slug: str, query: str, fetched_ts: str,
    engine_stats: dict, oracle_pool: list[dict],
    raw_count: int, capped_count: int,
) -> None:
    oracle_count = len(oracle_pool)

    # URLs = raw result_count from engine_stats (matches 11_pipeline_smoke.py convention)
    rows: list[tuple] = []
    for eng, info in engine_stats.items():
        status = info.get("status", "")
        ms     = info.get("search_ms", 0)
        n      = info.get("result_count", 0)
        drop   = info.get("drop_reason") or ""
        reason = drop if drop else (_STATUS_HINTS.get(status, "") if status != "OK" else "")
        rows.append((n, eng, status, reason, ms))
    rows.sort(key=lambda x: (-x[0], x[1]))

    lines = [
        f"# Engine Report — {mode} × {query}",
        "",
        f"**Mode:** {mode}",
        f"**Query:** {query}",
        f"**Fetched:** {fetched_ts}",
        "",
        "## Pool Sizes",
        "",
        "| Stage | Count |",
        "|-------|------:|",
        f"| Raw results | {raw_count} |",
        f"| Capped (K=google_count) | {capped_count} |",
        f"| Oracle pool (capped — no URL filter) | {oracle_count} |",
        "",
        "## Engine Breakdown",
        "",
        "| Engine | URLs | Status | Reason | ms |",
        "|--------|-----:|--------|--------|----|",
    ]
    for n, eng, status, reason, ms in rows:
        lines.append(f"| {eng} | {n} | {status} | {reason} | {ms} |")

    lines += [
        "",
        f"## Pool URL Listing (oracle pool — {oracle_count} URLs, sorted by URL)",
        "",
    ]
    for i, m in enumerate(oracle_pool, 1):
        title   = (m.get("title")   or "").strip().replace("\n", " ")[:100]
        snippet = (m.get("snippet") or "").strip().replace("\n", " ")[:200]
        lines += [
            f"{i}. {m['url']}",
            f"   Title: {title}",
            f"   Snippet: {snippet}",
            "",
        ]

    (ts_dir / f"{mode}_{slug}_engine_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


# Write engine_report_summary.md aggregated over all pairs
def _save_engine_summary(ts_dir: Path, rows: list[dict], ts: str) -> None:
    # EMPTY_NO_RESULTS/EMPTY_NO_CONTAINER/EMPTY_CONSENT/EMPTY_CONCURRENT_RACE/EMPTY_BLOCK were
    # removed with the guessed-verdict sub-statuses — every empty result now logs bare "EMPTY", so
    # there is no more BLOCK-vs-EMPTY distinction to bucket separately (BLOCK% column dropped below).
    _EMPTY_STATUSES   = {"EMPTY"}
    _TIMEOUT_STATUSES = {"TIMEOUT_WATCHDOG", "TIMEOUT_NONCOOP", "TIMEOUT_HTTPX"}
    _ERROR_STATUSES   = {"ERROR_BROWSER", "ERROR_HTTP", "ERROR_PARSE", "ERROR_OTHER", "ERROR"}

    engine_data: dict[str, dict] = {}
    for row in rows:
        mode = row["mode"]
        for eng, info in row["engine_stats"].items():
            if eng not in engine_data:
                engine_data[eng] = {
                    "n":             0,
                    "ok":            0,
                    "total_urls":    0,
                    "status_counts": {},
                    "mode_ok":       {m: 0 for m in MODES},
                    "mode_n":        {m: 0 for m in MODES},
                }
            d      = engine_data[eng]
            status = info.get("status", "ERROR_OTHER")
            n_urls = info.get("result_count", 0)
            d["n"]          += 1
            d["total_urls"] += n_urls
            d["status_counts"][status] = d["status_counts"].get(status, 0) + 1
            d["mode_n"][mode] += 1
            if status == "OK":
                d["ok"] += 1
                d["mode_ok"][mode] += 1

    def _pct(count: int, total: int) -> str:
        return str(round(count / total * 100)) if total else "0"

    def _dominant_failure(sc: dict) -> str:
        non_ok = {k: v for k, v in sc.items() if k != "OK"}
        return max(non_ok, key=non_ok.get) if non_ok else "—"

    lines = [
        "# Engine Report Summary — value_eval_v2",
        "",
        f"**Run:** {ts}",
        f"**Pairs:** {len(rows)} (4 modes × 4 queries)",
        "",
        "## Per-Engine Aggregate",
        "",
        "| Engine | n | OK | EMPTY% | TIMEOUT% | ERROR% | Total URLs | Mean URLs/Pool | Dominant Failure |",
        "|--------|---|----|----|----|---|---|---|---|",
    ]
    for eng in sorted(engine_data):
        d   = engine_data[eng]
        n   = d["n"]
        sc  = d["status_counts"]
        tu  = d["total_urls"]
        mu  = f"{tu / n:.1f}" if n else "0"
        emp = sum(sc.get(s, 0) for s in _EMPTY_STATUSES)
        tmo = sum(sc.get(s, 0) for s in _TIMEOUT_STATUSES)
        err = sum(sc.get(s, 0) for s in _ERROR_STATUSES)
        dom = _dominant_failure(sc)
        lines.append(
            f"| {eng} | {n} | {d['ok']} | {_pct(emp, n)}"
            f" | {_pct(tmo, n)} | {_pct(err, n)} | {tu} | {mu} | {dom} |"
        )

    lines += [
        "",
        "## Per-Mode Engine Availability (OK out of 4 pairs per mode)",
        "",
        "| Engine | general | pdf | books | docs |",
        "|--------|---------|-----|-------|------|",
    ]
    for eng in sorted(engine_data):
        d     = engine_data[eng]
        cells = " | ".join(f"{d['mode_ok'][m]}/{d['mode_n'][m]}" for m in MODES)
        lines.append(f"| {eng} | {cells} |")

    lines.append("")
    (ts_dir / "engine_report_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 1 — Pool Fetch (value_eval_v2)")
    parser.add_argument("--smoke",  action="store_true", help="One pair only (general × Q1)")
    parser.add_argument("--ts-dir", default=None,        help="Output directory override")
    args       = parser.parse_args()
    ts_dir_arg = Path(args.ts_dir) if args.ts_dir else None
    ts_dir     = asyncio.run(run_pool_fetch(smoke=args.smoke, ts_dir_arg=ts_dir_arg))
    print(ts_dir)
