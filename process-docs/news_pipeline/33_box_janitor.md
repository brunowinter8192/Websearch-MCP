# 33 — Box/Janitor: clean-slate jobs, global lock, persistent job record

## Decision

Three interlocking changes implemented together as Stages A–E:

1. **Cooldown → in-memory** (Stage A): reverts the persistent `cooled_at` store from the prior sustained-loop stage.
2. **Global single-job lock** (Stage B): `box_lock.py`, Mineru flock pattern.
3. **Janitor** (Stage C/D/E): job lifecycle management — wipe transient logs at start, derive persistent MD+plot at end.

---

## Stage A — Cooldown revert: persistent → in-memory

### Supersedes prior persistent-cooldown Stage 1 + Stage 4

Stage 1 of the prior sustained-loop stage added `load_cooled_at()` + `mark_cooled_batch()` to `proxy_status_log.py`
and built `PersistentCooldownManager` on top. Stage 4 wired `cm.flush()` into `run_loop`.

**Rationale for revert:** with the JOB model (one bounded target run = one job), persistence across
process restarts is counterproductive. A new job should start with a fully fresh pool — old burn state
from a previous job is stale information. In-memory cooldown achieves this: each new process = empty
burn dict = clean slate.

### What changed

- `p2_cooldown.py`: `PersistentCooldownManager.__init__` reduced to `self._burned_utc = {}`.
  Removed: `load_cooled_at()` call, `_dirty` set, `flush()` method, `_TS_FMT` constant.
  Public API unchanged: `mark_burned`, `is_eligible`, `eligible_candidates`, `cooldown_count`,
  `earliest_eligible_at`. Removed unused `CooldownManager` alias.
- `p3_target.py`: `CooldownManager` import → `PersistentCooldownManager` (alias was its only consumer).
- `p4_loop.py`: `cm.flush()` call removed.
- `proxy_status_log.py`: `load_cooled_at()`, `mark_cooled_batch()`, `_parse_proxy_key()` removed
  (`_parse_proxy_key` was helper only for `mark_cooled_batch` → orphaned). `record_run`,
  `partition_fresh`, `proxy_key`, `_parse_host_port`, `_load_log`, `_save_log` untouched.
  `proxy_status_log.json` and `probe_liveness.py` remain — probe_liveness uses `record_run` +
  `partition_fresh` and is dev/ history; removing it would destroy investigation provenance.

---

## Stage B — Global single-job lock (box_lock.py, Mineru pattern)

### Design

One acquire-pipe job at a time, system-wide. Fixed file names (not per-job):
- `~/.searxng-cli-locks/acquire_pipe.flock` — kernel flock vessel
- `~/.searxng-cli-locks/acquire_pipe.lock` — JSON sidecar with `{pid, job, target, started_at, status}`

`job`/`target` are sidecar metadata for the busy error message, NOT in filenames. Two concurrent
invocations both try to flock the same `acquire_pipe.flock` → only one succeeds.

### Crash-safety

`fcntl.flock` is released by the kernel on process death (SIGKILL, crash, OOM). The JSON sidecar
is an application-level artifact — it stays on disk after an unclean exit. `cleanup_stale()` handles
this: reads PID from sidecar → `os.kill(pid, 0)` → `ProcessLookupError` = dead → unlink sidecar.
The next `acquire()` call recovers transparently.

SIGTERM kills Python before `finally` runs → sidecar stays, flock released by kernel →
next `acquire()` via `cleanup_stale` removes stale sidecar and acquires successfully.
Verified in smoke test.

### `LockBusyError` message format

`"acquire_pipe already running: pid=N, job='J', target='T', running Xs"`
Read from sidecar at raise time. Sidecar read failure → generic fallback string.

---

## Stage C/D — Janitor + pool-size logging

### Job lifecycle

```
acquire_pipe.py:
  with box_lock.acquire(job_id, target_desc):
      janitor.start_job(job_id)          # wipe transient dirs
      logger = AcquireLogger(...)        # opens streaming JSONL
      run_loop(...)                      # fills JSONL
      logger.close()                     # flush + close JSONL (no per-run MD)
      janitor.end_job(job_id, jsonl_path, target_count, done_count)
        → read JSONL
        → compute stats (ok-event inter-hit deltas, pool_refresh events)
        → write acquire_pipe_jobs/<job_id>/job.md
        → write acquire_pipe_jobs/<job_id>/cumulative_hits.png
        → unlink JSONL
        → wipe acquire_pipe_logs/ + acquire_pipe_reports/
```

### Transient vs persistent

| Artifact | Kind | Lifetime |
|---|---|---|
| `acquire_pipe_logs/acquire_events_<ts>.jsonl` | transient | wiped at start, killed at end |
| `acquire_pipe_reports/acquire_run_<ts>.md` | transient | wiped at start, never written in wired flow |
| `acquire_pipe_jobs/<job_id>/job.md` | persistent | survives forever |
| `acquire_pipe_jobs/<job_id>/cumulative_hits.png` | persistent | survives forever |

`logger.close()` rather than `logger.finalize()` — avoids writing the per-run MD to the transient
`acquire_pipe_reports/` dir. `finalize()` retained for standalone logger use.

### Pool-size logging

`p5_logger.AcquireLogger.record_pool_refresh(size)` writes `{"event":"pool_refresh","size":N,"ts":...}`
to the streaming JSONL. Called from `p4_loop.run_loop` after each of the 3 `pool_provider()` invocations
(initial startup, 60-min scheduled refresh, exhaustion-wakeup refresh). Janitor reads these events to
populate the "Pool size (per refresh)" field in `job.md`.

### job.md — exactly 5 fields

| Field | Derivation |
|---|---|
| URLs | `target_count` / `done_count` arguments |
| Mean inter-hit | mean of consecutive ok-event timestamp deltas (seconds) |
| Median inter-hit | median of the same deltas |
| Total time | `max(ts) - min(ts)` across all events |
| Pool size (per refresh) | sizes from `pool_refresh` events, in order |

t0 = `min(ts)` across all events (consistent with `_throughput_buckets` in `p5_logger`).
Inter-hit mean/median = "—" if <2 ok events (no deltas).

### Plot

`cumulative_hits.png`: x = elapsed seconds since t0, y = cumulative ok fetches.
`ax.step(where="post")` — step happens at the hit timestamp.
matplotlib installed via `./venv/bin/python -m pip install matplotlib`.

---

## Stage E — Wiring

`acquire_pipe.py` changes:
- `job_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")`
- `target_desc = f"theblock-{pool_name}-{len(target_urls)}"`
- Workflow body wrapped in `with box_lock.acquire(job_id, target_desc):`
- `LockBusyError` caught outside `with` → `print(e); sys.exit(1)`
- `REPORT_DIR` constant removed (no longer used)
- Docstring updated: no persistent-cooldown reference

---

## 64er run — 20260614T190143Z

`./venv/bin/python dev/news_pipeline/theblock/acquire_pipe/acquire_pipe.py --pool curated --max_hours 0.5`

Result: 64/64 sub-sitemaps completed (0 gap), 47128 unique article URLs.
Straggler tail: bulk completed at ~10min, final stragglers via exhaustion-wakeup (proxy cooldown
recovery). Total wall time 1114s (~18.6min). Pool: 3396 curated proxies, 1 refresh cycle.

job.md fields: Mean inter-hit 17.7s · Median 10.0s · Total 1114.0s · Pool 3396.

---

## Why probe_liveness / probe_* / proxy_status_log.json stay

These are dev/ investigation artifacts documenting the proxy liveness characterization that informed
the pool strategy. `probe_liveness.py` uses `record_run` + `partition_fresh` from `proxy_status_log.py`
— both still present. Removing them would destroy the investigation trail without any benefit to the
acquire-pipe. They are self-contained; the acquire-pipe never calls them.
