# 69 — CoinDesk watchdog: all_resolved hang regression + fix

**Branch:** `riding-report-trim`.
An earlier tail-race change introduced this regression; a prior session designed the original
watchdog + `_abort_stall`.

## Regression

The tail-race PR redefined `RiderState.all_resolved` from:

```python
url_queue.empty() and in_flight == 0   # OLD
```

to:

```python
len(self.done_urls) >= len(self.target_urls)   # NEW (tail-race)
```

This is correct for the slot loops — they need `all_resolved` to go True once every distinct URL is
written, even if in-flight races are still pending. But `_watchdog` consumed `all_resolved` via:

```python
if state.all_resolved:
    return   # ← watchdog exits
```

Under the NEW definition: the moment the last URL's raw file is written (`done_urls.add(url)`), even
if another slot is still suspended in `await _fetch_one_url` on a dup-race of that URL (`in_flight = 1`),
`all_resolved` becomes True. At the next poll (up to 30 s later) the watchdog hits `return` and exits.
`run_riding_pool` is now `await asyncio.gather(*slot_tasks)` with no watchdog. The wedged slot never
returns from Playwright I/O. The process hangs indefinitely.

Under the OLD definition: a wedged in-flight slot kept `in_flight > 0`, so `all_resolved = False`, so
the watchdog stayed alive and eventually fired `_abort_stall` (exit code 1, `termination = "stall"`).

**Symptom observed:** production run hung 10+ minutes at the tail after `[slot N] dup-race discarded`
+ `[slot N] exit` for the slots that drained cleanly; watchdog was silent; no termination.

## Fix

`_watchdog` now splits the `all_resolved` check on `in_flight`:

```python
if state.all_resolved:
    if state.in_flight == 0:
        return   # clean drain — all slots exited before this poll
    _abort_done(state)   # wedged slot(s) on already-done URLs — does not return
```

`_abort_done(state)` (new function, analogous to `_abort_stall`):
- `state.termination = "all-done"` — work is genuinely complete, not a failure.
- Writes `job.md` via `write_riding_report` (late import, same pattern as `_abort_stall`).
- `os._exit(0)` — exit code 0 signals success; all raw files are already on disk.

`_abort_stall` is unchanged — it continues to handle the genuine no-progress stall case
(`all_resolved` still False, `last_progress_mono` stagnant for `stall_timeout_s`).

The grace period IS the watchdog's `sleep(interval)` before the check: in production
(`interval = min(30, stall_timeout_s / 4) = 30 s`), the wedged slot has already been hanging for up to
30 s when `_abort_done` fires. No additional grace needed — the work is done.

Leaves room for Stage 2 (pool refresh): the per-poll body grows as `sample → all_resolved-check →
refresh-if-interval → stall-check`. The `all_resolved` handling block remains self-contained.

## Test

`test_6_watchdog_wedge_after_all_resolved` added to
`dev/news_pipeline/coindesk_proxy_riding/test_tail_race.py` (alongside the earlier tail-race cases, same
src/ import pattern):

- `RiderState` with `target_urls = frozenset(["url_a"])`, `done_urls = {"url_a"}` → `all_resolved = True`.
- `in_flight = 1` — simulates wedged dup-race slot.
- `os._exit` patched to `fake_exit` (appends code, raises `SystemExit`).
- `write_riding_report` patched (avoids matplotlib I/O in test).
- `_watchdog` run with `poll_interval=0.1 s`.
- Assertions: `exit_calls == [0]`; `state.termination == "all-done"`.
- Result: PASS (6/6 total, was 5/5 before).
