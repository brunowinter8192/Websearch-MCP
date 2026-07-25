# 73 — CoinDesk proxy_riding: report on SIGINT/SIGTERM (manual abort checkpoint)

## Problem

The proxy_riding backfill runs for many hours. The per-run report (`job.md` + `cumulative.png`,
written to `data/news/coindesk/scrape_jobs/{job_id}/`) is the ONLY serialisation of the in-memory
`RiderState` — including the `pool_samples` time-series `(elapsed_s, n_eligible, n_cooldown)` the
watchdog accumulates each poll. A manual abort (Ctrl-C or `kill <pid>`) lost the report entirely.

## State Before Fix — Two Distinct Failure Modes

**SIGINT (Ctrl-C):**
Python installs a default SIGINT handler that raises `KeyboardInterrupt` in the running thread.
Inside `asyncio.run(...)`, the event loop converts this to task cancellation (`CancelledError`),
which unwinds cleanly through `finally` blocks. The `finally` in `run_riding_pool` runs (watchdog
cancel, browser close), then control propagates up through `scrape_entries_riding` → `pipeline.py`
→ `asyncio.run()` exits. Clean unwind — but `state` goes out of scope, `write_riding_report` is
never called, report is silently lost.

**SIGTERM (`kill <pid>`):**
Python installs NO default SIGTERM handler. The OS default disposition terminates the process
immediately — no Python exception, no `CancelledError`, no `finally` blocks, no browser cleanup.
Harder kill than SIGINT: report lost AND Chrome processes left orphaned.

## Why `try/finally` in `pipeline.py` Cannot Fix This

`state` is constructed inside `run_riding_pool` (rider.py) and only returned to `pipeline.py` on
normal completion (line 108: `manifest, state = await scrape_entries_riding(...)`). On any abort
that interrupts the `await`, that line never completes — `pipeline.py` has no `state` reference
and cannot call `write_riding_report`. The fix must live where `state` is in scope: inside the
engine, at the same level as the watchdog.

## Solution

`loop.add_signal_handler` chosen over `signal.signal` for two reasons:
1. Runs in the event loop thread — safe to call synchronous I/O (reporter, matplotlib) directly.
2. Properly replaces asyncio's SIGINT-to-KeyboardInterrupt path; `signal.signal` competes with
   asyncio's internal SIGINT handling and loses.

**In `run_riding_pool` (rider.py), after `state` is constructed, before `crawlers` start:**
```python
loop = asyncio.get_running_loop()
loop.add_signal_handler(signal.SIGINT,  _abort_interrupted, state, signal.SIGINT)
loop.add_signal_handler(signal.SIGTERM, _abort_interrupted, state, signal.SIGTERM)
```

**In the `finally` block, before `watchdog.cancel()`:**
```python
try:
    loop.remove_signal_handler(signal.SIGINT)
    loop.remove_signal_handler(signal.SIGTERM)
except Exception as exc:
    print(f"[rider] remove_signal_handler warn: {exc}", file=sys.stderr)
```
Removal prevents the handler from firing during the normal-completion `write_riding_report` call
in `pipeline.py` (which awaits I/O and could receive a stray signal).

**New function `_abort_interrupted(state, signum)`** (after `_abort_done` in FUNCTIONS section):
- Sets `state.termination = "interrupted"`
- Calls `write_riding_report(state, state.job_dir, state.t_job_start)` via the same late-import
  pattern as `_abort_stall` / `_abort_done` (avoids circular import)
- Fallback to minimal stub `job.md` on reporter error
- `os._exit(130)` for SIGINT (128 + 2), `os._exit(143)` for SIGTERM (128 + 15) — Unix conventions
  for signal-killed processes; distinct from stall (`1`) and done (`0`)

`reporter.py` requires no changes: `stats["termination"]` is rendered verbatim in a markdown table
cell — `"interrupted"` is self-documenting and renders correctly.

## Double-Write Prevention

| Path | Outcome |
|---|---|
| Normal completion | Handlers removed in `finally` → `pipeline.py:125` calls `write_riding_report` once |
| Watchdog abort (`_abort_stall`/`_abort_done`) | `os._exit()` kills process before `pipeline.py` resumes — handlers never fire |
| Manual abort (`_abort_interrupted`) | `os._exit()` kills process — `pipeline.py` never resumes |

No double-write on any path.

## Test Approach + Results

`dev/news_pipeline/coindesk_proxy_riding/test_sigint_report.py` — new file, lazy `src/` imports
inside function bodies (same pattern as `test_tail_race.py`; satisfies dev/ top-level import
constraint).

Two tests, both calling `_abort_interrupted` directly with a monkeypatched `os._exit → SystemExit`:
- `test_abort_interrupted_sigint`: assert `os._exit(130)`, `job.md` + `cumulative.png` written,
  `state.termination == "interrupted"`, `"interrupted"` present in `job.md`.
- `test_abort_interrupted_sigterm`: same but `os._exit(143)`.

Results: **2/2 new tests passed**. `test_tail_race.py` (7 existing src-engine tests): **7/7 passed**.

Commit: `891bd82`
