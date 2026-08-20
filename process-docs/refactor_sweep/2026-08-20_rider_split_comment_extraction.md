# rider.py split + comment sweep (2026-08-20)

`src/news/engine/proxy_riding/rider.py` (574 LOC, over the 400-LOC ceiling) split into 4
concern-based modules under `src/news/engine/proxy_riding/`. Pure refactor — zero behavior/
record-shape/constant-value change, verified by dev-suite parity + full pytest baseline parity
(see Verification).

## Module cut

| Module | Owns |
|---|---|
| `rider.py` (entry, unchanged import path) | `run_riding_pool` (orchestrator), `_run_slot`, `_apply_fetch_result`, `_finalize_ride`, `_next_proxy`, `_watchdog`, `_teardown_pool` |
| `state.py` | `RideRecord`, `JobRecord`, `RiderState` dataclasses + constants |
| `fetch.py` | `_fetch_one_url`, `_classify_crawl_result`, `_is_regwall`, `_classify_connect_fail`, `_write_raw`, `_url_hash` |
| `abort.py` | `_abort_done`, `_abort_interrupted`, `_abort_stall` + shared `_abort_write_report_and_exit` |

### Constraint that shaped the cut: dev-test monkeypatch namespace binding

`dev/news_pipeline/coindesk_proxy_riding/{test_tail_race,test_sigint_report,smoke_stage1}.py` do
`unittest.mock.patch.object(rider_mod, "_fetch_one_url", stub)`,
`patch.object(rider_mod, "_next_proxy", stub)`, `patch.object(rider_mod, "POOL_REFRESH_INTERVAL_S", 0.0)`
and then call `rider_mod._run_slot(...)` / `_watchdog(...)` directly. Python resolves a function's
free names through `__globals__` — the module dict of wherever the function is *defined*, not where
it's imported. Patching an attribute on `rider_mod` only affects code whose defining module is
`rider.py`. This means `_run_slot` and `_watchdog` could NOT move to `fetch.py`/a new module without
silently breaking these tests' ability to stub the fetch layer / the refresh-interval constant — the
patches would set an attribute nobody reads. `_fetch_one_url`/`_next_proxy`/`POOL_REFRESH_INTERVAL_S`
themselves CAN move (and did, to `fetch.py`/`state.py`) as long as `rider.py` still does
`from .fetch import _fetch_one_url` etc. (a `from X import Y` creates a NEW binding of the name `Y`
in the importing module's own `__dict__`, which is exactly the binding `patch.object(rider_mod, ...)`
overwrites). `os._exit` patching (`patch.object(rider_mod.os, "_exit", ...)`) is unaffected by any of
this — `os` is a singleton module object, so `rider_mod.os is abort_mod.os`; patching its `_exit`
attribute is global regardless of which module calls `os._exit(...)`. This is why `_abort_done`/
`_abort_interrupted`/`_abort_stall` COULD move to `abort.py` freely, and why the late `reporter.
write_riding_report` import is similarly safe to move (fresh module-attribute lookup each call, not
a name bound at abort.py's own definition time).

No test needed editing to accommodate this — only import lines, since `rider.py` re-exports every
moved dataclass/constant it uses. Two dev-test source-string assertions in `smoke_stage1.py::
test_import_clean` DID need updating: they grepped `Path(rider_mod.__file__).read_text()` for the
late-import string `"src.news.engine.proxy_riding.reporter"`, which now lives in `abort.py`, not
`rider.py` — re-pointed to check `abort_mod.__file__`'s content instead (see Verification).

### `_run_slot`/`_apply_fetch_result` decomposition

`_run_slot` (134→67 code lines) kept its outer proxy-acquisition loop and inner dequeue-or-race +
fetch-call block inline — deliberately NOT extracted into a further helper, because the original
control flow interleaves `continue`/`break` with `all_resolved`/stall re-checks at specific points;
folding the dequeue-or-race logic into a separately-looping helper would change how often those
re-checks happen relative to queue draining, a narrow but real behavior-drift risk under racing
slots. The status-branch logic (ok/regwall/connect_fail/failed dispatch, ~53 code lines) extracted
to `_apply_fetch_result`, returning a tri-state `"continue"|"append"|"break"` that reproduces the
original inline control flow exactly: `connect_fail` and fail-count-at-threshold both `break`
WITHOUT reaching the original's trailing `job_records.append(job)` line; `ok`/`regwall`/
below-threshold `failed`/`empty` fall through to append; dup-race `ok` `continue`s without append.
The `finally`-block `RideRecord` build extracted to `_finalize_ride` (27 lines). Both new helpers
mutate a local `_RideProgress` scratch dataclass instead of five loose mutable locals threaded
through — ephemeral, never persisted, never reaches a report; not placed in `state.py` since it has
no relationship to `RiderState`/reporting, only to `_run_slot`'s internal bookkeeping.

`_fetch_one_url` (55→24 code lines): extracted `_classify_crawl_result` (the success/empty/regwall
branch, 11 lines) — output tuple identical for every branch, verified by construction (each original
`if`/`elif` arm mapped 1:1 to a `return` in the new helper).

`run_riding_pool` (55 lines, under the 100-line ceiling but had one coherent helper available):
extracted `_teardown_pool` (signal-handler removal + watchdog cancel + crawler close, 11 lines) —
mechanical move, same code, no logic change.

### Abort-dedup helper

`_abort_write_report_and_exit(state, log_prefix, exit_code, fallback_title, extra_fields)` replaces
the ~40-line triplicated report-write-with-fallback block in each of `_abort_done`/
`_abort_interrupted`/`_abort_stall`. Each caller sets `state.termination` and prints its own
(differently-worded) log line BEFORE calling the helper; the helper reads `state.termination` back
for the fallback stub's `termination:` line. `extra_fields` is the ONLY per-caller fallback-stub
content difference (`_abort_stall` passes `[f"idle_s: {idle_s:.0f}"]`, inserted at the same position
the original inline `idle_s:` line occupied, between `termination:` and `n_ok:`; the other two pass
`[]`). `os._exit(exit_code)` and the try/except/try/except nesting (reporter call → fallback stub
write → both wrapped, `sys.stderr.flush()` always before exit) reproduced exactly. Consolidating 3
call sites into 1 also collapsed the 3 near-identical "late import — avoids circular" comments into 1.

## Comment triage

Every comment in the original file was checked against `src/news/engine/proxy_riding/DOCS.md` (which
already carried an unusually detailed "Key dataclasses" / `_watchdog` poll-loop / `_classify_connect_fail`
subtype paragraph before this sweep) and the `news_pipeline`/`pooling` process-docs areas before
deleting.

| Original comment | Verdict | Covering surface |
|---|---|---|
| `REGWALL_SIGNALS` header (raw_markdown vs html rationale) | moved | `DOCS.md` Gotchas (new — landmine, not previously stated as an actionable warning) |
| `PAGE_TIMEOUT_MS`/`DELAY_BEFORE_HTML`/`POOL_REFRESH_INTERVAL_S`/`FAIL_THRESHOLD` inline trailing comments | deleted | already verbatim in `DOCS.md` Role / `_watchdog` poll-loop bullets / `JobRecord.load_s` paragraph |
| `STALL_TIMEOUT_S` inline comment (60 min) | moved | `DOCS.md` Gotchas (new — module default 3600 vs production override 300 was NOT documented anywhere; genuine landmine) |
| `_PROXY_ERR` header | deleted | self-evident from the literal tuple at its one usage site (`_classify_crawl_result`) |
| `_watchdog`'s 5-line header (timer-based, immune to wedged slots, poll interval formula) | deleted, condensed to 1-line header | verbatim in `DOCS.md` Role paragraph + `_watchdog` poll-loop bullet list |
| `_classify_connect_fail`'s 4-line subtype doc | deleted, condensed to 1-line header | verbatim duplicated in `DOCS.md`'s `_classify_connect_fail` paragraph |
| `_abort_done`/`_abort_stall` 2-3 line headers (never-returns, no-teardown rationale) | condensed to 1-line header ("Never returns" retained in the header itself) | "no Python teardown, no atexit, no browser.close()" already in `DOCS.md` Gotchas |
| `_abort_interrupted`'s exit-code formula (128+SIGINT=2 / 128+SIGTERM=15) | moved | `DOCS.md` Gotchas (new — Unix signal-exit convention, not documented elsewhere) |
| `_run_slot` inline `# stale queue entry — already won by a racer` | deleted | covered by `DOCS.md` Flow step 4 (dup-race discard) |
| `_run_slot` inline `# skip job_records.append — dup fetch, no stats` | deleted | same — Flow step 4 |
| `_watchdog` call-site inline `# does not return` / `# clean drain` comments | deleted | callee's own condensed header states "Never returns"; "clean drain" verbatim in `DOCS.md` bullet 3 |
| Dataclass field comments (`positions`, `proxy_pool`, `job_dir`, `output_dir`, `target_urls`, `pool_provider`, `pool_samples`, `connect_fail_records`, `termination`) | mostly deleted (verbatim in `DOCS.md`'s dataclass paragraph already); `positions` tuple shape and `termination`'s true 5-value enum (original comment omitted `"interrupted"`) folded into the same paragraph — genuinely missing/stale before this sweep | `DOCS.md` "Key dataclasses" paragraph (now under `state.py`), `DOCS.md` Flow step 5 |

Tally: **12 blocks/comments deleted as covered**, **3 moved to `DOCS.md` Gotchas as new content**
(regwall raw_markdown-vs-html landmine, STALL_TIMEOUT_S module-default-vs-prod-override, exit-code
Unix convention), **1 correction folded into an existing `DOCS.md` paragraph** (`termination`'s
5th value), **0 required genuinely new process-docs substance beyond this sweep record and the
monkeypatch-binding constraint above** (which itself has no other home — it's a refactor-mechanics
finding, not a Gotcha about runtime behavior, and not previously investigated in any area).

## Verification

`dev/news_pipeline/coindesk_proxy_riding/test_tail_race.py`: 7/7 passed (baseline: 7/7, unchanged) —
integration-level, real `_run_slot` + real `RiderState`, mocked `_fetch_one_url`/`_next_proxy`, real
raw-file writes to a tmpdir, asserts `n_ok`/`done_urls`/file-count/no-double-write/no-spurious-requeue/
watchdog-wedge-exit/pool-refresh across 7 deterministic scenarios — proves `_apply_fetch_result`'s
tri-state append/continue/break dispatch matches the original inline control flow bit-for-bit under
racing conditions, not just by code inspection.
`dev/news_pipeline/coindesk_proxy_riding/test_sigint_report.py`: 0/2 (baseline: 0/2, unchanged — both
fail on `ModuleNotFoundError: matplotlib` in this venv, pre-existing environment gap, not a code
issue; the exit-code/termination assertions before the `matplotlib`-dependent report-file check were
not reached in either run).
`dev/news_pipeline/coindesk_proxy_riding/smoke_stage1.py::test_import_clean`: PASS (baseline: PASS,
unchanged) — after re-pointing its source-string check from `rider_mod` to `abort_mod` for the
late-import assertion.
`smoke_stage1.py::test_watchdog_deterministic`: FAIL with identical `TypeError:
RiderState.__init__() missing 2 required positional arguments: 'job_dir' and 'target_urls'` before
and after — pre-existing staleness (this dev test predates `job_dir`/`target_urls` becoming required
fields), unrelated to and unmodified by this refactor.
Full suite (`pytest tests/`): 182 passed, 10 failed (8 `test_query_logger.py` + 2 `test_proxy_pool.py`)
— identical to the standing baseline; `tests/` has zero references to `proxy_riding` so this refactor
could not have touched that failure set regardless.
Repo-wide grep for every moved symbol (`RiderState`, `JobRecord`, `RideRecord`, `RAW_SUBDIR`,
`FAIL_THRESHOLD`, `_abort_stall`, `_abort_interrupted`, `_abort_done`) confirmed zero stale
`rider.py`-sourced imports outside the intentionally-unchanged `rider_mod._fetch_one_url`/
`_next_proxy`/`_watchdog`/`os` patch targets (which correctly stay pointed at `rider.py`) and the
unrelated legacy `dev/news_pipeline/coindesk_proxy_riding/p2_browser_rider.py` prototype (a
standalone dev-local module never imported from `src/`, out of scope).
