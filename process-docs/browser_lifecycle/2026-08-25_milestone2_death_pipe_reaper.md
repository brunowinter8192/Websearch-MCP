# Milestone 2: death-pipe crash reaper across both Chrome lanes (2026-08-25)

Continues the `browser_lifecycle` area. Milestone 1 covered `search_web` runs coexisting safely on
the shared session profile (cross-process lock, PID-scoped kill, stale-takeover). This milestone
closes the remaining process-hygiene requirement: ANY process/window the CLI spawns, across all
three browser families (search-lane Chrome, scrape-lane Chrome for Testing, Camoufox Firefox), gone
promptly regardless of how the CLI process itself ends — including a hard crash mid-run, which
Milestone 1's own teardown (a `finally`-block-shaped mechanism) structurally cannot reach.

## Investigation: the 28h scrape-cdp leak

A `scrape-url-cdp-vjre0993` Chrome-for-Testing instance (13 processes) survived 28+ hours despite
`chromium_scrape.py`'s existing per-call `_kill_by_profile` teardown. Read the teardown path
end to end (`_acquire_cdp_headed`'s `finally`, wrapped by `try_scrape`'s
`asyncio.wait_for(..., timeout=245.8)` with both `except` branches returning normally) before
concluding anything — every internal failure path (budget exhaustion, browser-launch exception,
generic exception) logs a completion record via the caller's own `log_scrape` call, so an internal
skip was ruled OUT, not assumed.

Cross-referenced `cli.log.2026-08-24` (main repo checkout, not the worktree — logs are gitignored,
per-checkout) against the leaked profile's own filesystem timestamps. Found the exact line: `10:56:
44,937 [INFO] src.scraper.scrape_url:87 - Scraping: https://web2.cylex.de/firma-home/express-
aenderungsschneiderei-frankfurt-13490734.html`, immediately preceded by a fresh `asyncio:64 - Using
selector: KqueueSelector` (a new event loop — i.e. a distinct `cli.py scrape_url` subprocess from
the batch of `paket.net` scrapes completing normally moments before it). **No further log line for
that URL ever exists** — no completion log, no `scrape_log.jsonl` record for `cylex`, confirmed via
grep. Since every internal `try_scrape` path returns and lets the caller log, total silence for 28+
hours is only possible if the Python process itself died externally (most plausibly an
orchestrator-side timeout shorter than the 245.8s internal budget) between Chrome launching and the
`finally` block ever running — `open -g`'s detachment means the orphaned Chrome then runs forever.

## Design: three independent, event-driven nets — no time constants, no launchd

An earlier proposal (launchd user agent vs. opportunistic-only reap, both with an implied wall-clock
polling cadence) was explicitly REPLACED by the user with a purely event-driven model requiring no
scheduled/installed component:

- **Net 1** (pre-existing, both lanes) — the normal `finally`/`kill_own_chrome` teardown. Untouched.
- **Net 2** (new, this milestone's core) — `src/death_pipe.py`: `spawn_watchdog(pids,
  cleanup_dir=None)` opens a pipe, spawns a detached helper (the same file, re-invoked as its own
  `__main__`) with the pipe's READ end as its stdin, and never closes the WRITE end itself — that
  open fd's lifetime IN THE CALLING PROCESS is the only "aliveness" signal there is. The helper
  blocks on a single `os.read(0, 1)`; the OS closes every fd a process holds when it ends for ANY
  reason (clean exit, uncaught exception, `SIGKILL`), so the helper wakes on EOF regardless of HOW
  the parent died, no cooperation required. On wake it kills any still-alive PID and removes
  `cleanup_dir` if given, then exits — silently, if net 1 already handled everything (the common
  case), or with one log line to `cli.log` if it actually had to act. Placed at `src/` root
  (alongside `log_janitor.py`) since it's genuinely domain-agnostic — no Chrome/Firefox knowledge at
  all, just "watch a fd, clean up on EOF." Wired into the search lane in `browser.py::get_tab()`
  right after `_record_own_pids()` (no `cleanup_dir` — the session profile is deliberately
  persistent, never deleted, only its processes get reaped) and into the scrape lane in
  `chromium_scrape.py::_acquire_cdp_headed()` once the cdp port resolves (with the call's own
  throwaway profile dir as `cleanup_dir`, since that one genuinely is disposable).
- **Net 3** (new, scrape lane only) — `_reap_orphaned_scrapes()`, called at the start of every
  `try_scrape`. Parallel scrapes are legitimate (each call gets its own unique throwaway profile
  dir), so a live process is never killed just for existing — only once its age exceeds
  `TOTAL_SCRAPE_BUDGET_S` (a derived bound off an existing constant, not a new one: no legitimate
  scrape can still be running past its own outer `asyncio.wait_for` budget). Directories are swept
  on a separate, simpler criterion: any `scrape-url-cdp-*` dir with zero live processes attached,
  any age, is unambiguously orphaned. The search lane already had its own net-3 equivalent
  (`_reap_session_profile`, from Milestone 1) — not touched here.

`_kill_by_profile` was refactored to share `death_pipe._terminate_then_kill` rather than
re-implementing the same psutil terminate/wait/kill loop a third time (browser.py's own copy from
Milestone 1 stayed separate — intra-module reuse via the now-shared `death_pipe` module was judged
in scope, since both lanes already depend on that module for net 2 itself; a third independent copy
would have been pure duplication with no benefit).

## Camoufox (family 3): verified live, no code needed

Two independent trials: real `cli.py scrape_url_camoufox` run, `kill -9`'d ~1.2-1.5s in (well inside
the unconditional `CAMOUFOX_RENDER_WAIT_S=5.0` window, so definitely mid-flight). Both times, zero
surviving `Library/Caches/camoufox/` processes, confirmed via `ps aux` — NOT `pgrep -f`, which
produced misleading transient/shifting-PID noise unrelated to Camoufox during this investigation
(traced to macOS system helpers momentarily matching the search string, nothing to do with the
actual browser; `ps aux | grep` gave a clean, stable read both times). Consistent with
`process-docs/camoufox_lane/pipe_switch_and_no_focus_steal_2026-08-20.md`'s finding that Firefox is
spawned from inside Playwright's own Node.js driver, never a detached `open -g` process — that
driver evidently self-terminates its child when its connection to the (now-dead) Python process
breaks. No `camoufox_scrape.py` code changes made; documented here and in `src/scraper/DOCS.md`'s
Gotchas instead.

## A test bug found along the way, not a death_pipe bug

The first integration-test draft for `death_pipe.py` used `psutil.pid_exists(pid)` to check whether
a killed dummy process was "gone," and consistently failed with the dummy still showing as alive
5+ seconds after a real, working kill. Root cause (isolated via a minimal `os.pipe()`+`subprocess`
repro that worked correctly, then incrementally reintroducing pieces until the failure reappeared):
the dummy is the TEST's own child (`subprocess.Popen` from the test itself), unlike a real
detached Chrome/Firefox — a killed child becomes a zombie (still `pid_exists()==True`) until its
OWN parent explicitly reaps it. `psutil.Process(pid).status()` confirmed `zombie`, and
`dummy.poll()`/`.returncode` confirmed the kill (`-15`, SIGTERM) had genuinely already happened.
Fixed by checking `dummy.poll() is not None` instead (which also reaps as a side effect) — a test
artifact specific to using a self-spawned dummy, not present in production (real Chrome/Firefox
targets are never children of the CLI process).

## Live verification

**Search lane crash sim:** real `search_web` run, `kill -9`'d mid-sweep (7 real Chrome PIDs up).
`cli.log`, same second as the kill: `parent died without tearing down its own browser — killed
pids=[60811, 60814, 60813, 60798, 60804, 60751, 60799], removed_dir=None`. `pgrep` confirmed 0
processes immediately after — the death-pipe fired, not a subsequent run's reap (no second
invocation occurred).

**Scrape lane crash sim:** real `scrape_url_chromium` run, `kill -9`'d mid-scrape (9 real Chrome
PIDs up). Same second: `killed pids=[63875, 63921, 63922, 63925], removed_dir=/var/folders/.../T/
scrape-url-cdp-d9rz1vy2` — both the processes and the throwaway directory gone, confirmed via
`pgrep` and `find`.

**Normal-path clean runs, both lanes:** real CLI invocations, zero leftover processes, zero stray
`death_pipe.py` helper processes remaining afterward, no intervention log line (net 1 handled
everything; the watchdog woke, found nothing to do, exited silently).

**Net 3 live check:** planted a fake `scrape-url-cdp-faketest.*` directory with no process attached
— swept on the very next real `scrape_url_chromium` call.

**Tests:** 246 passed (was 226 going into this milestone) — 8 real-subprocess integration tests for
`death_pipe.py`'s core pipe/EOF/kill mechanism (no mocking of the primitive itself, only the
protected targets are dummy processes), 2 for `browser.py`'s net-2 wiring, 11 for
`chromium_scrape.py`'s net-2/net-3 wiring and age-threshold logic (subprocess/psutil mocked).

Machine confirmed fully clean (zero processes across all three families) at the end of the session.
