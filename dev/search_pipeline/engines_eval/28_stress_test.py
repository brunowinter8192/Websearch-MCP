#!/usr/bin/env python3

# INFRASTRUCTURE
import argparse
import asyncio
import dataclasses
import sys
import time
from pathlib import Path
from typing import Optional

from stealth_config import DEFAULT_CONFIG, StealthConfig
from engine_selectors import HTTPX_ENGINES
from _stress_types import QueryResult
from _stress_engines import run_pydoll_engine, run_httpx_engine
from _stress_report import build_report, save_report

QUERIES_FILE = Path(__file__).parent.parent / "queries.txt"
# PARKED: brave commented out — PoW CAPTCHA incompatible with asyncio.gather architecture
# See DOCS.md "Parked: Brave & Dropped Engines" and decisions/stealth01_detection_layers.md
# To resume: un-comment brave here and un-comment brave entry in engine_selectors.py
PYDOLL_ENGINES = [
    "google",
    "bing",
    # "brave",  # PARKED
    "google scholar",
]
HTTPX_ENGINE_LIST = sorted(HTTPX_ENGINES)


# ORCHESTRATOR

# Run all engines in parallel, collect results, write summary report
async def run_stress_test(
    config: StealthConfig,
    limit: Optional[int],
    engine_filter: Optional[str],
) -> None:
    queries = _load_queries(limit)

    pydoll_engines = [e for e in PYDOLL_ENGINES if not engine_filter or e == engine_filter]
    httpx_engines = [e for e in HTTPX_ENGINE_LIST if not engine_filter or e == engine_filter]
    all_engines = pydoll_engines + httpx_engines

    total = len(queries) * len(all_engines)
    print(
        f"Loaded {len(queries)} queries | Engines: {len(all_engines)} | Total: {total}",
        file=sys.stderr,
    )

    wall_start = time.monotonic()

    outputs = await asyncio.gather(
        *[run_pydoll_engine(e, queries, config) for e in pydoll_engines],
        *[run_httpx_engine(e, queries) for e in httpx_engines],
        return_exceptions=True,
    )

    total_wall = time.monotonic() - wall_start

    results: list[QueryResult] = []
    timings: dict[str, float] = {}

    for engine, output in zip(all_engines, outputs):
        if isinstance(output, Exception):
            print(f"  [{engine}] engine-level crash — {output}", file=sys.stderr)
            timings[engine] = 0.0
        else:
            engine_results, engine_wall = output
            results.extend(engine_results)
            timings[engine] = engine_wall

    report = build_report(results, len(queries), timings, total_wall, all_engines)
    path = save_report(report)
    print(f"\nReport: {path}")


# FUNCTIONS

# Parse queries.txt and return only @profile: general queries
def _load_queries(limit: Optional[int]) -> list[str]:
    text = QUERIES_FILE.read_text(encoding="utf-8")
    queries = []
    in_general = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "@profile: general":
            in_general = True
            continue
        if stripped.startswith("@profile:"):
            in_general = False
            continue
        if in_general and stripped and not stripped.startswith("#"):
            queries.append(stripped)

    return queries[:limit] if limit else queries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stress test — all queries × active engines (google, bing, google scholar, crossref) in parallel")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--limit", type=int, default=None, help="Only first N queries")
    parser.add_argument("--engine", type=str, default=None, help="Only test this engine")
    args = parser.parse_args()

    config = dataclasses.replace(DEFAULT_CONFIG, headless=not args.headed)
    asyncio.run(run_stress_test(config, args.limit, args.engine))
