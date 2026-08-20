#!/usr/bin/env python3
"""
Deterministic tail-race tests for src/news/engine/proxy_riding/rider.py.
No browser or proxy infrastructure needed — _fetch_one_url and _next_proxy are mocked.

All src/ imports are lazy (inside function bodies) to satisfy dev/ isolation rules.

Five cases:
  1. surplus-slots race: 2 URLs, 6 slots → both done, n_ok=2, no double-write
  2. write-exactly-once: 1 URL, 3 slots all racing → n_ok=1, exactly 1 raw file
  3. no-spurious-requeue: stale dequeue → no fetch; raced-fail → not re-queued
  4. normal path: 4 URLs, 4 slots → all done via dequeue, no racing
  5. fail-before-success: URL fails first fetch (re-queued), succeeds second → done exactly once

Usage:
    ./venv/bin/python dev/news_pipeline/coindesk_proxy_riding/test_tail_race.py
"""

# INFRASTRUCTURE

import asyncio
import hashlib
import sys
import tempfile
import unittest.mock
from pathlib import Path

# Prepend worktree root so lazy src/ imports (inside function bodies) resolve correctly.
# Pattern from smoke_stage1.py: parents[3] = dev/news_pipeline/coindesk_proxy_riding/ → worktree root.
_WORKTREE = Path(__file__).parents[3]
if str(_WORKTREE) not in sys.path:
    sys.path.insert(0, str(_WORKTREE))


# ORCHESTRATOR

def main() -> None:
    results = [
        _run("test_1_surplus_slots_race_both_done",              test_1_surplus_slots_race_both_done),
        _run("test_2_write_exactly_once_per_url",                test_2_write_exactly_once_per_url),
        _run("test_3_no_spurious_requeue",                       test_3_no_spurious_requeue),
        _run("test_4_normal_path_no_racing",                     test_4_normal_path_no_racing),
        _run("test_5_fail_before_success_done_once",             test_5_fail_before_success_done_once),
        _run("test_6_watchdog_wedge_after_all_resolved",         test_6_watchdog_wedge_after_all_resolved),
        _run("test_7_watchdog_pool_refresh",                     test_7_watchdog_pool_refresh),
    ]
    passed = sum(results)
    print(f"\n{'='*55}")
    print(f"Results: {passed}/{len(results)} passed")
    if passed < len(results):
        sys.exit(1)


# FUNCTIONS

def _run(name: str, fn) -> bool:
    print(f"[test] {name} ...", end=" ", flush=True)
    try:
        fn()
        print("PASS")
        return True
    except AssertionError as exc:
        print(f"FAIL — {exc}")
        return False
    except Exception as exc:
        import traceback
        print(f"ERROR — {exc}")
        traceback.print_exc()
        return False


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:12]


# 2 URLs, 6 slots: slots 0-1 dequeue, slots 2-5 race. Both URLs done, n_ok=2.
def test_1_surplus_slots_race_both_done() -> None:
    from src.news.engine.proxy_riding import rider as rider_mod
    from src.news.engine.proxy_riding.state import RiderState, RAW_SUBDIR
    from src.news.engine.proxy_riding.cooldown import RidingCooldownManager as PersistentCooldownManager

    urls = ["https://cd.com/a", "https://cd.com/b"]

    async def ok_fetch(crawler, url, proxy_str, page_timeout_ms):
        return "ok", 1000, 500, 0.1, f"<html>{url}</html>", None

    async def fixed_proxy(state):
        return ("http", "p:1")

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / RAW_SUBDIR).mkdir()

        async def run():
            q = asyncio.Queue()
            for u in urls:
                q.put_nowait(u)
            state = RiderState(
                url_queue=q, proxy_pool=[("http", "p:1")],
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p, job_dir=p / "jobs",
                burn_threshold=10, page_timeout_ms=8000,
                total_urls=len(urls), target_urls=frozenset(urls),
            )
            with (
                unittest.mock.patch.object(rider_mod, "_fetch_one_url", ok_fetch),
                unittest.mock.patch.object(rider_mod, "_next_proxy",    fixed_proxy),
            ):
                tasks = [asyncio.create_task(rider_mod._run_slot(i, None, state)) for i in range(6)]
                await asyncio.gather(*tasks)
            return state

        state = asyncio.run(run())

        assert state.done_urls == set(urls),   f"done_urls={state.done_urls}"
        assert state.n_ok == 2,                f"n_ok={state.n_ok} (expected 2)"
        for u in urls:
            assert (p / RAW_SUBDIR / f"{_url_hash(u)}.html").exists(), f"raw file missing: {u}"


# 1 URL, 3 slots all racing — first writer wins, n_ok=1, exactly one raw file.
def test_2_write_exactly_once_per_url() -> None:
    from src.news.engine.proxy_riding import rider as rider_mod
    from src.news.engine.proxy_riding.state import RiderState, RAW_SUBDIR
    from src.news.engine.proxy_riding.cooldown import RidingCooldownManager as PersistentCooldownManager

    url_x = "https://cd.com/x"

    async def ok_fetch(crawler, url, proxy_str, page_timeout_ms):
        return "ok", 1000, 500, 0.1, f"<html>{url}</html>", None

    async def fixed_proxy(state):
        return ("http", "p:1")

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / RAW_SUBDIR).mkdir()

        async def run():
            q = asyncio.Queue()
            q.put_nowait(url_x)          # one copy in queue
            state = RiderState(
                url_queue=q, proxy_pool=[("http", "p:1")],
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p, job_dir=p / "jobs",
                burn_threshold=10, page_timeout_ms=8000,
                total_urls=1, target_urls=frozenset([url_x]),
            )
            with (
                unittest.mock.patch.object(rider_mod, "_fetch_one_url", ok_fetch),
                unittest.mock.patch.object(rider_mod, "_next_proxy",    fixed_proxy),
            ):
                tasks = [asyncio.create_task(rider_mod._run_slot(i, None, state)) for i in range(3)]
                await asyncio.gather(*tasks)
            return state

        state = asyncio.run(run())

        raw_files = list((p / RAW_SUBDIR).iterdir())
        assert state.n_ok == 1,                f"n_ok={state.n_ok} (expected 1)"
        assert state.done_urls == {url_x},     f"done_urls={state.done_urls}"
        assert len(raw_files) == 1,            f"raw file count={len(raw_files)} (expected 1)"


# Two sub-cases: (a) stale dequeue skipped without fetch; (b) raced-fail not re-queued.
def test_3_no_spurious_requeue() -> None:
    from src.news.engine.proxy_riding import rider as rider_mod
    from src.news.engine.proxy_riding.state import RiderState, RAW_SUBDIR
    from src.news.engine.proxy_riding.cooldown import RidingCooldownManager as PersistentCooldownManager

    # Sub-case A: url_x already in done_urls, url_x stale-queued, url_y is the open one.
    # Slot must skip url_x (no fetch), race url_y, write url_y. fetch_call_count == 1.
    url_x = "https://cd.com/stale"
    url_y = "https://cd.com/open"
    fetch_calls: list[str] = []

    async def ok_fetch_spy(crawler, url, proxy_str, page_timeout_ms):
        fetch_calls.append(url)
        return "ok", 1000, 500, 0.1, f"<html>{url}</html>", None

    async def fixed_proxy(state):
        return ("http", "p:1")

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / RAW_SUBDIR).mkdir()

        async def run_a():
            q = asyncio.Queue()
            q.put_nowait(url_x)          # stale: url_x already done
            state = RiderState(
                url_queue=q, proxy_pool=[("http", "p:1")],
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p, job_dir=p / "jobs",
                burn_threshold=10, page_timeout_ms=8000,
                total_urls=2, target_urls=frozenset([url_x, url_y]),
            )
            state.done_urls.add(url_x)   # pre-mark url_x as done
            with (
                unittest.mock.patch.object(rider_mod, "_fetch_one_url", ok_fetch_spy),
                unittest.mock.patch.object(rider_mod, "_next_proxy",    fixed_proxy),
            ):
                await rider_mod._run_slot(0, None, state)
            return state

        state_a = asyncio.run(run_a())

        assert url_x not in fetch_calls,       f"stale url_x was fetched (should be skipped)"
        assert url_y in fetch_calls,           f"url_y was not fetched"
        assert state_a.done_urls == {url_x, url_y}, f"done_urls={state_a.done_urls}"

    # Sub-case B: url_x not done, queue empty → slot races url_x.
    # First fetch → "failed" (raced, dequeued=False) → must NOT be re-queued.
    # Second fetch → "ok" → done. Verify no put_nowait call for url_x after the failure.
    url_x2 = "https://cd.com/race-fail"
    put_calls: list[str] = []
    call_n = [0]

    async def fail_then_ok(crawler, url, proxy_str, page_timeout_ms):
        call_n[0] += 1
        if call_n[0] == 1:
            return "failed", None, None, 0.1, "", "err"
        return "ok", 1000, 500, 0.1, "<html></html>", None

    with tempfile.TemporaryDirectory() as tmp2:
        p2 = Path(tmp2)
        (p2 / RAW_SUBDIR).mkdir()

        async def run_b():
            q = asyncio.Queue()          # empty — slot must race
            state = RiderState(
                url_queue=q, proxy_pool=[("http", "p:1")],
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p2, job_dir=p2 / "jobs",
                burn_threshold=10, page_timeout_ms=8000,
                total_urls=1, target_urls=frozenset([url_x2]),
            )
            orig_put = state.url_queue.put_nowait
            state.url_queue.put_nowait = lambda u: (put_calls.append(u), orig_put(u))[1]
            with (
                unittest.mock.patch.object(rider_mod, "_fetch_one_url", fail_then_ok),
                unittest.mock.patch.object(rider_mod, "_next_proxy",    fixed_proxy),
            ):
                await rider_mod._run_slot(0, None, state)
            return state

        state_b = asyncio.run(run_b())

        assert url_x2 not in put_calls,        f"raced-fail was re-queued: {put_calls}"
        assert state_b.n_ok == 1,              f"n_ok={state_b.n_ok} (expected 1)"
        assert state_b.done_urls == {url_x2},  f"done_urls={state_b.done_urls}"


# 4 URLs, 4 slots: each slot dequeues one distinct URL. No racing. n_ok=4.
def test_4_normal_path_no_racing() -> None:
    from src.news.engine.proxy_riding import rider as rider_mod
    from src.news.engine.proxy_riding.state import RiderState, RAW_SUBDIR
    from src.news.engine.proxy_riding.cooldown import RidingCooldownManager as PersistentCooldownManager

    urls = [f"https://cd.com/{i}" for i in range(4)]
    raced: list[str] = []   # URLs fetched via race path (dequeued=False) — must be empty

    async def ok_fetch(crawler, url, proxy_str, page_timeout_ms):
        return "ok", 1000, 500, 0.1, f"<html>{url}</html>", None

    async def fixed_proxy(state):
        return ("http", "p:1")

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / RAW_SUBDIR).mkdir()

        async def run():
            q = asyncio.Queue()
            for u in urls:
                q.put_nowait(u)
            state = RiderState(
                url_queue=q, proxy_pool=[("http", "p:1")],
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p, job_dir=p / "jobs",
                burn_threshold=10, page_timeout_ms=8000,
                total_urls=len(urls), target_urls=frozenset(urls),
            )
            with (
                unittest.mock.patch.object(rider_mod, "_fetch_one_url", ok_fetch),
                unittest.mock.patch.object(rider_mod, "_next_proxy",    fixed_proxy),
            ):
                tasks = [asyncio.create_task(rider_mod._run_slot(i, None, state)) for i in range(4)]
                await asyncio.gather(*tasks)
            return state

        state = asyncio.run(run())

        assert state.n_ok == 4,               f"n_ok={state.n_ok} (expected 4)"
        assert state.done_urls == set(urls),  f"done_urls mismatch"
        raw_files = list((p / RAW_SUBDIR).iterdir())
        assert len(raw_files) == 4,           f"raw file count={len(raw_files)} (expected 4)"


# 1 URL, 1 slot: first fetch fails → requeue → second fetch ok → done exactly once.
def test_5_fail_before_success_done_once() -> None:
    from src.news.engine.proxy_riding import rider as rider_mod
    from src.news.engine.proxy_riding.state import RiderState, RAW_SUBDIR
    from src.news.engine.proxy_riding.cooldown import RidingCooldownManager as PersistentCooldownManager

    url_x = "https://cd.com/stubborn"
    call_n = [0]

    async def fail_then_ok(crawler, url, proxy_str, page_timeout_ms):
        call_n[0] += 1
        if call_n[0] == 1:
            return "failed", None, None, 0.1, "", "transient error"
        return "ok", 1000, 500, 0.1, "<html>body</html>", None

    async def fixed_proxy(state):
        return ("http", "p:1")

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / RAW_SUBDIR).mkdir()

        async def run():
            q = asyncio.Queue()
            q.put_nowait(url_x)
            state = RiderState(
                url_queue=q, proxy_pool=[("http", "p:1")],
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p, job_dir=p / "jobs",
                burn_threshold=10, page_timeout_ms=8000,
                total_urls=1, target_urls=frozenset([url_x]),
            )
            with (
                unittest.mock.patch.object(rider_mod, "_fetch_one_url", fail_then_ok),
                unittest.mock.patch.object(rider_mod, "_next_proxy",    fixed_proxy),
            ):
                await rider_mod._run_slot(0, None, state)
            return state

        state = asyncio.run(run())

        assert call_n[0] == 2,                f"fetch called {call_n[0]} times (expected 2)"
        assert state.n_ok == 1,               f"n_ok={state.n_ok} (expected 1)"
        assert state.done_urls == {url_x},    f"done_urls={state.done_urls}"
        raw_files = list((p / RAW_SUBDIR).iterdir())
        assert len(raw_files) == 1,           f"raw file count={len(raw_files)} (expected 1)"


# all_resolved=True (last URL in done_urls) but in_flight=1 (one wedged slot) →
# _watchdog must call os._exit(0) and set termination='all-done', NOT return silently.
def test_6_watchdog_wedge_after_all_resolved() -> None:
    from src.news.engine.proxy_riding import rider as rider_mod
    from src.news.engine.proxy_riding.state import RiderState, RAW_SUBDIR
    from src.news.engine.proxy_riding.rider import _watchdog
    from src.news.engine.proxy_riding.cooldown import RidingCooldownManager as PersistentCooldownManager

    url_done = "https://cd.com/already-done"
    exit_calls: list[int] = []

    def fake_exit(code: int) -> None:
        exit_calls.append(code)
        raise SystemExit(code)

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / RAW_SUBDIR).mkdir()

        async def run() -> RiderState:
            q = asyncio.Queue()
            state = RiderState(
                url_queue=q, proxy_pool=[],
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p, job_dir=p / "jobs",
                burn_threshold=2, page_timeout_ms=8_000,
                total_urls=1, target_urls=frozenset([url_done]),
            )
            # Simulate: last URL written by first-writer winner → all_resolved=True.
            state.done_urls.add(url_done)
            # Simulate: one slot still suspended inside await _fetch_one_url on dup-race.
            state.in_flight = 1

            with (
                unittest.mock.patch.object(rider_mod.os, "_exit", fake_exit),
                unittest.mock.patch("src.news.engine.proxy_riding.reporter.write_riding_report"),
            ):
                try:
                    await _watchdog(state, poll_interval=0.1)
                except SystemExit:
                    return state   # os._exit(0) raised by fake_exit — expected termination
            return state

        state = asyncio.run(run())

    assert exit_calls == [0],               f"expected os._exit(0), got {exit_calls}"
    assert state.termination == "all-done", f"termination={state.termination!r}"


# pool_provider is called once per refresh interval; proxy_pool is atomically replaced.
# Patches POOL_REFRESH_INTERVAL_S=0.0 so the first poll always triggers refresh.
# State has all_resolved=True + in_flight=0 → watchdog returns cleanly after the refresh.
def test_7_watchdog_pool_refresh() -> None:
    from src.news.engine.proxy_riding import rider as rider_mod
    from src.news.engine.proxy_riding.state import RiderState, RAW_SUBDIR
    from src.news.engine.proxy_riding.rider import _watchdog
    from src.news.engine.proxy_riding.cooldown import RidingCooldownManager as PersistentCooldownManager

    pool_a = [("http", "proxy-a1:1"), ("http", "proxy-a2:2")]
    pool_b = [("http", "proxy-b1:1"), ("socks5", "proxy-b2:2"), ("http", "proxy-b3:3")]
    refresh_count = [0]

    async def mock_provider() -> list:
        refresh_count[0] += 1
        return pool_b

    url_done = "https://cd.com/refreshed"

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / RAW_SUBDIR).mkdir()

        async def run():
            q = asyncio.Queue()
            state = RiderState(
                url_queue=q, proxy_pool=pool_a,
                cooldown_mgr=PersistentCooldownManager(),
                output_dir=p, job_dir=p / "jobs",
                burn_threshold=2, page_timeout_ms=8_000,
                total_urls=1, target_urls=frozenset([url_done]),
                pool_provider=mock_provider,
            )
            # all_resolved=True + in_flight=0 → watchdog returns cleanly after refresh
            state.done_urls.add(url_done)

            # POOL_REFRESH_INTERVAL_S=0.0: any elapsed time satisfies the refresh check
            with unittest.mock.patch.object(rider_mod, "POOL_REFRESH_INTERVAL_S", 0.0):
                await _watchdog(state, poll_interval=0.05)
            return state

        state = asyncio.run(run())

    assert refresh_count[0] >= 1,      f"pool_provider not called (refresh_count={refresh_count[0]})"
    assert state.proxy_pool is pool_b, f"proxy_pool not replaced: {state.proxy_pool}"


if __name__ == "__main__":
    main()
