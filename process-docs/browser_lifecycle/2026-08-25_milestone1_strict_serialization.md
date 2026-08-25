# Milestone 1: strictly-serialized search_web runs with PID-scoped teardown (2026-08-25)

New area. Driving question: how do multiple `search_web` CLI invocations coexist safely on one
shared Chrome profile (`~/.websearch/browser-session`), given production observed two overlapping
runs killing each other's LIVE Chrome mid-search (2026-08-25 incident: mass `ERROR_BROWSER`/
`WebSocketConnectionClosed` across all DOM engines, traced to `kill_stale_chrome`'s unconditional
profile-pattern `pkill` firing at another run's start/exit). Milestone 1 scope: one run kills only
its own Chrome, a second run blocks on a cross-process lock until the first has torn its browser
down, and a lock older than the sweep's hard time budget is presumed stuck and taken over. Explicit
non-scope: no reaper daemon (later milestone), no scrape-lane changes.

## Design

**Cross-process lock — `src/search/browser_lock.py` (new, generic).** `fcntl.flock`-based,
domain-agnostic (no Chrome/SESSION_DIR knowledge — takes an `on_stale` callback), blocking via a
poll loop (`LOCK_NB` + `time.sleep(0.25)`) rather than a plain blocking `flock()` call, since a
plain blocking call has no way to check sidecar age for the staleness override. A JSON sidecar
(`{pid, started_at}`) written on each acquire; a sidecar older than `hard_budget_s` triggers
`on_stale()` then a force-break (unlink the lock file + open a fresh inode at the same path — flock
is inode-bound, so this bypasses the old holder's still-technically-held lock on the now-orphaned
file) and retry. Modeled loosely on `src/news/engine/proxy_pool/box_lock.py`'s sidecar pattern, but
that module is non-blocking (raises `LockBusyError`); this one needed to block-with-timeout, which
box_lock's `LOCK_NB`-then-raise shape doesn't support, so a separate module was written rather than
extending box_lock's contract.

**Own-PID tracking, not profile-pattern kill.** `browser.py::get_tab()` pgreps
`user-data-dir={SESSION_DIR}` immediately after `_browser.start()` and records the result as
`_owned_pids` — trustworthy as "this run's own" ONLY because the cross-process lock (held since
before this point) plus a pre-launch reap (below) guarantee no foreign Chrome can be using the
profile at that moment. `kill_own_chrome()` (replacing `kill_stale_chrome` as the primary teardown)
kills only those PIDs, via `close_browser()`'s existing CDP `Browser.close` command first (found,
via reading `pydoll.browser.Chrome.stop()`'s source, to already be a real working close mechanism —
not the previously-assumed-broken `BrowserProcessManager.stop_process()`, which only ever kills the
short-lived `open -g` wrapper, never real Chrome), then a psutil terminate/wait/kill safety net for
anything CDP-close leaves behind. `close_browser()` itself was left untouched — 40+
`dev/search_pipeline/*.py` probe scripts call it directly, bypassing `search_web.py` entirely, and
none of them were touched by this milestone.

**Crash-vs-hang distinction drives the reap split.** A crashed CLI process releases its flock for
free (kernel-level, on any fd close including `kill -9`) — but its `open -g`-launched Chrome is NOT
a child process and survives the crash, orphaned on the shared profile. This means the stale-lock
takeover path (age > `LOCK_HARD_BUDGET_S`) only ever fires for a genuinely HUNG-but-alive holder,
never a crashed one (crash already leaves the lock free, uncontended, non-stale). The orphaned-
Chrome case therefore needed a SEPARATE reap: `get_tab()` calls `_reap_session_profile()`
unconditionally right after acquiring the lock, before its own launch — legitimate specifically
because holding the lock proves any survivor is orphaned (either a crashed prior run's leftover, or
a stale-takeover victim already handled by `on_stale`).

**`LOCK_HARD_BUDGET_S` = 81s** (`RATE_WAIT_TIMEOUT` 60s + slowest `ENGINE_WATCHDOG_OVERRIDE` 6.0s +
15s margin), defined independently in `browser.py` rather than imported from `search_web.py`'s
constants — importing would create a `browser_lock -> browser -> engines -> search_web` cycle,
since `engines/*.py` already import `browser.py`. A real two-parallel-run measurement (below) put
one full sweep at ~7.25s end to end, so the 15s margin already covers roughly 2x that observed
duration.

## Bug found via live testing: per-engine watchdog cancels the lock wait

First implementation put the lock-acquire call lazily inside `get_tab()`, triggered by whichever
DOM engine's `new_tab()` ran first — but that call executes inside
`asyncio.wait_for(engine.search_with_reason(...), timeout=3.6-6.0s)`. A live two-parallel-CLI-run
test caught the consequence immediately: `duckduckgo`'s (or whichever engine won the race)
`get_tab()` call blocked on `asyncio.to_thread(browser_lock.acquire, ...)`, its own 3.6s watchdog
fired first, `asyncio.wait_for` cancelled the coroutine — releasing `get_tab`'s asyncio-level
`_init_lock` (context-manager exit still runs under cancellation) but NOT the underlying OS thread
running `browser_lock.acquire` (uncancellable, kept polling in the background, orphaned) — the next
queued engine then re-entered `get_tab()` and spawned ANOTHER competing thread. Log evidence from
the reproducing run: 5 separate "Acquiring cross-process browser-session lock" lines within what
should have been 2 total (one per process), and the second process finished in ~10.6s having never
once logged "Own Chrome pids" — every one of its DOM engines failed via the cancel-retry cycle
without ever getting a browser.

Fix: `search_web.py::_prewarm_browser()` — a bare, unwatchdogged `await get_tab()` — called once
from `search_web_workflow`, before the engine fanout, whenever the selected engines intersect a new
`_BROWSER_ENGINES` constant (the 9 pydoll-driven engines). By the time the fanout's own
per-engine-watchdogged tasks run, `_browser` is already set and their own `new_tab()` calls return
near-instantly. A real launch failure inside the prewarm is swallowed (logged) rather than crashing
the whole workflow — it resurfaces identically per-engine when their own `new_tab()` retries it,
matching pre-milestone failure semantics for that case.

Also hardened while fixing this: `get_tab()`'s launch body (lock-acquire through
`_record_own_pids`) wrapped in try/except that resets `_browser`/`_tab` to `None` and releases
`_lock_handle` before re-raising — without it, a real Chrome-launch failure (missing binary etc.)
would leave the cross-process lock held forever, since a half-initialized `Chrome` object makes
`close_browser()`'s own `_browser.stop()` raise `BrowserNotRunning`, so `kill_own_chrome`'s
`finally` alone couldn't be trusted to clean it up.

## Second gap found on review: `close_browser()` raising skips teardown

Flagged in review (not caught by the live tests above, which never exercised a Chrome that dies
mid-sweep): `kill_own_chrome()`'s original `await close_browser()` call was unguarded. Chrome dying
mid-sweep (crash, manual close) makes `_browser.stop()` raise on the dead websocket BEFORE
`close_browser`'s own `_browser = None` reset line runs — a bare call would then skip the PID-scoped
psutil safety net and the lock release that follow it, leaking the cross-process lock until the 81s
stale-takeover. Fixed with a try/except around the `close_browser()` call specifically (logs a
warning, manually resets `_browser`/`_tab`), leaving `close_browser()` itself untouched for its 40+
other direct callers. Regression-guarded
(`test_kill_own_chrome_runs_safety_net_and_release_when_close_browser_raises`).

## Live verification

**Single run, repeated 4x:** `pgrep -f user-data-dir=...` = 0 before and after every run.

**Two parallel runs (post-fix):** started 0.3s apart. Log evidence: process A acquired the lock
uncontended and launched immediately; process B logged "Acquiring cross-process browser-session
lock" exactly once (no retry storm), then blocked for a measured **7.10s**
(16:14:24,992 -> 16:14:32,091) until A's `kill_own_chrome` released the lock, then launched its own
Chrome and completed. Both runs returned real, non-empty results. Zero leftover processes after
both finished. B's wait (~7.1s) closely tracked A's own full sweep duration (~7.25s), confirming
serialization added no wasted overhead beyond the legitimate wait.

**Real crash simulation (E2E):** started a real `cli.py search_web` run, `kill -9`'d the CLI process
2s into the sweep. Confirmed via `pgrep` immediately after: the CLI process was gone but its 17
Chrome-related PIDs on the session profile SURVIVED (not child processes of the killed Python
process). A second real run's log then showed: lock acquired immediately (16:22:41,817 — the
crashed process's flock was already free, kernel-released on process death), "Starting Chrome
session" 1ms later, then "Reaping orphaned Chrome on session profile:
pids=[94571, 94626, 94627, 94628, 94634, 94636, 94637, 94717, 94720, 94721, 94722, 94723, 94725,
94727, 94728, 94729, 94752, 96004]" at 16:22:41,841 — matching the exact 17 surviving PIDs from the
crash (plus one, 96004, that appeared in the gap before the second run started) — followed by a
clean launch with a fully disjoint new PID set (`Own Chrome pids: [96205, 96223, 96224, 96232,
96239, 96243, 96244, 96259]`). The second run completed with real results (crossref=10, mojeek=10,
bing=10, etc.), zero leftover processes afterward, no unexpected errors in the log window.

## Environmental note, unrelated to this milestone

Live verification runs on this machine (load average ~4.5-5.25 during testing) showed the SAME
mass `ERROR_BROWSER`/`TIMEOUT_WATCHDOG` pattern for individual DOM engines with BOTH the pre- and
post-milestone code (confirmed via a direct `git stash`/re-run A-B comparison) — i.e. Chrome cold-
start under this exact machine load was already slow/flaky before this milestone touched anything,
consistent with the pre-existing per-engine variance already on record in
`process-docs/browser_posture/`. Not a regression from this work; noted so a future session reading
the verification logs doesn't mistake individual engine failure rates for a lifecycle-management
symptom — the lifecycle guarantees (zero leftover processes, correct serialization, correct crash
recovery) held regardless of how many individual engines succeeded on a given run.
