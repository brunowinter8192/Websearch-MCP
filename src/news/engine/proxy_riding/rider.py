# INFRASTRUCTURE

import asyncio
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig

# From cooldown.py: proxy cooldown manager (type hint only)
from src.news.engine.proxy_riding.cooldown import RidingCooldownManager
# From state.py: shared riding dataclasses + constants
from src.news.engine.proxy_riding.state import (
    RiderState, RideRecord, JobRecord,
    PAGE_TIMEOUT_MS, DELAY_BEFORE_HTML, STALL_TIMEOUT_S, POOL_REFRESH_INTERVAL_S,
    FAIL_THRESHOLD, RAW_SUBDIR,
)
# From fetch.py: per-URL fetch + classification helpers
from src.news.engine.proxy_riding.fetch import (
    _fetch_one_url, _classify_connect_fail, _write_raw, _url_hash,
)
# From abort.py: report-then-exit handlers for watchdog/signal aborts
from src.news.engine.proxy_riding.abort import _abort_done, _abort_interrupted, _abort_stall


# Ephemeral per-ride bookkeeping for _run_slot — not persisted, never reaches a report.
@dataclass
class _RideProgress:
    burn_count: int  = 0
    fail_count: int  = 0
    ride_ok:    int  = 0
    positions:  list = field(default_factory=list)
    cf_broke:   bool = False


# ORCHESTRATOR

# Launch n_slots concurrent rider tasks across n_browsers browser instances; return shared state when done.
async def run_riding_pool(
    url_queue:       asyncio.Queue,
    proxy_pool:      list,
    cooldown_mgr:    RidingCooldownManager,
    output_dir:      Path,
    job_dir:         Path,
    target_urls:     frozenset,
    burn_threshold:  int,
    n_slots:         int,
    page_timeout_ms: int   = PAGE_TIMEOUT_MS,
    n_browsers:      int   = 1,
    stall_timeout_s: float = STALL_TIMEOUT_S,
    pool_provider:   object = None,
) -> RiderState:
    (output_dir / RAW_SUBDIR).mkdir(parents=True, exist_ok=True)
    state = RiderState(
        url_queue=url_queue,
        proxy_pool=proxy_pool,
        cooldown_mgr=cooldown_mgr,
        output_dir=output_dir,
        job_dir=job_dir,
        burn_threshold=burn_threshold,
        page_timeout_ms=page_timeout_ms,
        total_urls=url_queue.qsize(),
        target_urls=target_urls,
        stall_timeout_s=stall_timeout_s,
        pool_provider=pool_provider,
    )
    state.n_browsers = n_browsers
    state.n_slots    = n_slots

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT,  _abort_interrupted, state, signal.SIGINT)
    loop.add_signal_handler(signal.SIGTERM, _abort_interrupted, state, signal.SIGTERM)

    crawlers = [AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) for _ in range(n_browsers)]
    await asyncio.gather(*[c.start() for c in crawlers])
    watchdog = asyncio.create_task(_watchdog(state))
    try:
        tasks = [asyncio.create_task(_run_slot(i, crawlers[i % n_browsers], state)) for i in range(n_slots)]
        await asyncio.gather(*tasks)
    finally:
        await _teardown_pool(loop, watchdog, crawlers)
    if state.termination == "running":
        state.termination = "all-done"
    return state


# FUNCTIONS

# One rider task: pull proxy → ride URL queue → burn/rotate → repeat.
async def _run_slot(slot_id: int, crawler: AsyncWebCrawler, state: RiderState) -> None:
    print(f"[slot {slot_id}] started", file=sys.stderr)

    while not state.all_resolved:
        if time.monotonic() - state.last_progress_mono > state.stall_timeout_s:
            print(f"[slot {slot_id}] stall — stopping", file=sys.stderr)
            state.termination = "stall"
            break

        entry = await _next_proxy(state)
        if entry is None:
            if state.all_resolved:
                break
            print(f"[slot {slot_id}] pool exhausted", file=sys.stderr)
            state.termination = "pool-exhausted"
            break

        proto, hp = entry
        pstr     = f"{proto}://{hp}"
        t_bind   = time.monotonic()
        progress = _RideProgress()

        try:
            while progress.burn_count < state.burn_threshold:
                if state.all_resolved:
                    break
                if time.monotonic() - state.last_progress_mono > state.stall_timeout_s:
                    state.termination = "stall"
                    break

                dequeued = True
                try:
                    url = state.url_queue.get_nowait()
                    if url in state.done_urls:
                        continue
                except asyncio.QueueEmpty:
                    if state.all_resolved:
                        break
                    open_list = sorted(state.target_urls - state.done_urls)
                    if not open_list:
                        break
                    url = open_list[slot_id % len(open_list)]
                    dequeued = False

                state.in_flight += 1
                state.in_flight_urls.add(url)
                ride_pos  = len(progress.positions) + 1
                t_url_abs = datetime.now(timezone.utc)

                status, char_count, markdown_len, elapsed, html, err = await _fetch_one_url(
                    crawler, url, pstr, state.page_timeout_ms,
                )
                state.in_flight -= 1
                state.in_flight_urls.discard(url)

                progress.positions.append((url, status, round(elapsed, 2)))
                job = JobRecord(
                    url=url, url_hash=_url_hash(url),
                    status=status, char_count=char_count, markdown_len=markdown_len,
                    elapsed_s=round(elapsed, 2), error=err, file=None,
                    t_start=t_url_abs, ride_position=ride_pos, proxy_str=pstr,
                    load_s=round(max(0.0, elapsed - DELAY_BEFORE_HTML), 3) if status == "ok" else None,
                )

                action = _apply_fetch_result(
                    slot_id, state, progress, job, url, html, dequeued, ride_pos, elapsed, err,
                )
                if action == "continue":
                    continue
                if action == "append":
                    state.job_records.append(job)
                if action == "break":
                    break

        finally:
            _finalize_ride(slot_id, state, proto, hp, pstr, t_bind, progress)

    print(f"[slot {slot_id}] exit", file=sys.stderr)


# Dispatch one fetch's status (ok/regwall/connect_fail/failed/empty); return "continue"|"append"|"break".
def _apply_fetch_result(
    slot_id:  int,
    state:    RiderState,
    progress: _RideProgress,
    job:      JobRecord,
    url:      str,
    html:     str,
    dequeued: bool,
    ride_pos: int,
    elapsed:  float,
    err:      str | None,
) -> str:
    status = job.status

    if status == "ok":
        if url not in state.done_urls:
            state.done_urls.add(url)
            out      = _write_raw(_url_hash(url), html, state.output_dir)
            job.file = str(out)
            state.n_ok += 1
            progress.ride_ok += 1
            state.last_progress_mono = time.monotonic()
            print(f"[slot {slot_id}] ok  r={ride_pos} {url[:70]}", file=sys.stderr)
            return "append"
        print(f"[slot {slot_id}] dup-race discarded {url[:70]}", file=sys.stderr)
        return "continue"

    if status == "regwall":
        progress.burn_count += 1
        state.n_regwall     += 1
        if dequeued and url not in state.done_urls:
            state.url_queue.put_nowait(url)
        print(
            f"[slot {slot_id}] RW  burn={progress.burn_count}/{state.burn_threshold}"
            f" r={ride_pos}", file=sys.stderr,
        )
        return "append"

    if status == "connect_fail":
        state.n_connect_fail += 1
        if dequeued and url not in state.done_urls:
            state.url_queue.put_nowait(url)
        progress.cf_broke = True
        state.connect_fail_records.append((round(elapsed, 3), _classify_connect_fail(err)))
        print(f"[slot {slot_id}] CF  rotating", file=sys.stderr)
        return "break"

    progress.fail_count += 1
    if dequeued and url not in state.done_urls:
        state.url_queue.put_nowait(url)
    print(
        f"[slot {slot_id}] {status} fail={progress.fail_count}/{FAIL_THRESHOLD}"
        f" r={ride_pos} → requeue", file=sys.stderr,
    )
    if progress.fail_count >= FAIL_THRESHOLD:
        return "break"
    return "append"


# Build + append RideRecord for a finished proxy ride; mark proxy burned; log summary.
def _finalize_ride(
    slot_id:  int,
    state:    RiderState,
    proto:    str,
    hp:       str,
    pstr:     str,
    t_bind:   float,
    progress: _RideProgress,
) -> None:
    ride = RideRecord(
        proxy_str=pstr, proto=proto, host_port=hp,
        n_ok=progress.ride_ok, n_regwall=progress.burn_count,
        n_connect_fail=1 if progress.cf_broke else 0,
        n_failed=progress.fail_count,
        n_urls_attempted=len(progress.positions),
        burned_threshold=progress.burn_count >= state.burn_threshold,
        burned_connect=progress.cf_broke,
        ride_s=time.monotonic() - t_bind,
        positions=progress.positions,
    )
    state.ride_records.append(ride)
    state.cooldown_mgr.mark_burned(proto, hp, ride_ok=progress.ride_ok)
    print(
        f"[slot {slot_id}] proxy done ok={progress.ride_ok} rw={progress.burn_count}"
        f" cf={int(progress.cf_broke)} n={len(progress.positions)} {pstr}",
        file=sys.stderr,
    )


# Atomically advance pool cursor; return (proto, hp) or None if pool is empty.
async def _next_proxy(state: RiderState) -> tuple[str, str] | None:
    async with state.proxy_lock:
        eligible = state.cooldown_mgr.eligible_candidates(state.proxy_pool)
        if not eligible:
            return None
        idx              = state.proxy_cursor % len(eligible)
        state.proxy_cursor += 1
        return eligible[idx]


# Independent progress watchdog — separate asyncio task, immune to wedged slots (see package DOCS.md Role).
async def _watchdog(
    state:         RiderState,
    poll_interval: float | None = None,
) -> None:
    interval           = poll_interval if poll_interval is not None else min(30.0, state.stall_timeout_s / 4)
    t0_mono            = time.monotonic()
    _last_refresh_mono = time.monotonic()
    while True:
        await asyncio.sleep(interval)
        elapsed_s  = time.monotonic() - t0_mono
        n_eligible = len(state.cooldown_mgr.eligible_candidates(state.proxy_pool))
        n_cooldown = state.cooldown_mgr.cooldown_count()
        state.pool_samples.append((elapsed_s, n_eligible, n_cooldown))
        if state.pool_provider and time.monotonic() - _last_refresh_mono >= POOL_REFRESH_INTERVAL_S:
            new_pool = await state.pool_provider()
            if new_pool:
                old_n = len(state.proxy_pool)
                state.proxy_pool = new_pool
                _last_refresh_mono = time.monotonic()
                print(f"[watchdog] pool refresh: {old_n} → {len(new_pool)} proxies", file=sys.stderr)
            else:
                print("[watchdog] pool refresh returned empty — keeping current pool", file=sys.stderr)
        if state.all_resolved:
            if state.in_flight == 0:
                return
            _abort_done(state)
        idle = time.monotonic() - state.last_progress_mono
        if idle > state.stall_timeout_s:
            _abort_stall(state, idle)


# Remove signal handlers, cancel watchdog, close crawlers — teardown after slot tasks finish.
async def _teardown_pool(loop, watchdog: asyncio.Task, crawlers: list) -> None:
    try:
        loop.remove_signal_handler(signal.SIGINT)
        loop.remove_signal_handler(signal.SIGTERM)
    except Exception as exc:
        print(f"[rider] remove_signal_handler warn: {exc}", file=sys.stderr)
    watchdog.cancel()
    results = await asyncio.gather(*[c.close() for c in crawlers], return_exceptions=True)
    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"[rider] crawler[{idx}].close warn: {r}", file=sys.stderr)
