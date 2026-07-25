# 64 — CoinDesk watchdog abort report path fix

**Branch:** `coindesk-watchdog`. This corrects the watchdog in the CoinDesk proxy-riding src/ port.

## Bug

`_abort_stall` (`rider.py`) received `output_dir = platform_dir` (= `data/news/coindesk/`) and wrote
both `remaining_urls.txt` and the job report (`job.md` + three plots) into that platform root.

Root cause: `job_dir = data/news/coindesk/scrape_jobs/{job_id}/` was computed in `pipeline.py` at
line 118 — **after** `scrape_entries_riding` returns. When the watchdog fires, `scrape_entries_riding`
never returns (`os._exit(1)` terminates the process from within the engine). `job_dir` is therefore
never computed; the watchdog's abort path had no access to it and wrote everything to `output_dir`
(platform root) by default.

On normal completion `pipeline.py` computes `job_dir` and calls `write_riding_report(state, job_dir,
t_job_start)` itself — that path was correct. Only the stall-abort path was broken.

During backfill (300 s stall cutoff, large URLs set) the watchdog fires repeatedly, re-cluttering
`data/news/coindesk/` with `remaining_urls.txt`, `job.md`, `cumulative.png`, `ride_lengths.png`,
`regwall_position.png` on every stalled run.

## Fix — threading chain (four sites)

**Invariant preserved throughout:** raw HTML writes (`_write_raw` → `state.output_dir/raw/{hash}.html`)
use `state.output_dir = platform_dir` and are completely untouched.

### 1. `pipeline.py:run_scrape_only`

`job_dir` moved from line 118 (post-scrape) to just before the `scrape_entries_riding` call (~line 101).
Passed as new 4th arg:

```python
job_dir = DATA_ROOT / platform.name / "scrape_jobs" / job_id
manifest, state = await scrape_entries_riding(new_entries, platform_dir, riding_cfg, job_dir)
```

The subsequent `write_riding_report(state, job_dir, t_job_start)` (normal-completion path) is unchanged;
`job_dir` is already in scope.

### 2. `scrape.py:scrape_entries_riding`

New `job_dir: Path` parameter; forwarded to `run_riding_pool`:

```python
async def scrape_entries_riding(
    entries:    list[dict],
    output_dir: Path,
    riding_cfg: RidingScrapeConfig,
    job_dir:    Path,
) -> tuple[list[dict], RiderState]:
    ...
    state = await run_riding_pool(..., output_dir=output_dir, job_dir=job_dir, ...)
```

### 3. `rider.py:RiderState` + `run_riding_pool`

`RiderState` gains a `job_dir: Path` field (alongside the existing `output_dir`):

```
output_dir:  Path   # raw HTML target: output_dir/raw/{hash}.html  ← unchanged
job_dir:     Path   # report target: scrape_jobs/{job_id}/         ← NEW
```

`run_riding_pool` accepts `job_dir: Path` and passes it to the `RiderState` constructor.

### 4. `rider.py:_abort_stall`

`state.job_dir.mkdir(parents=True, exist_ok=True)` added at the top of the abort body (before the
first file write — the directory does not yet exist at stall time). All three write targets change:

| Write | Before | After |
|---|---|---|
| `remaining_urls.txt` | `output_dir / "remaining_urls.txt"` | `state.job_dir / "remaining_urls.txt"` |
| `write_riding_report(…)` | `write_riding_report(state, output_dir, …)` | `write_riding_report(state, state.job_dir, …)` |
| fallback `job.md` stub | `(output_dir / "job.md").write_text(…)` | `(state.job_dir / "job.md").write_text(…)` |

`reporter.py:write_riding_report` is unchanged — it already takes its target dir as a parameter and
`mkdir`s it; the `mkdir` call becomes a safe no-op since `_abort_stall` already created the dir.

## Edge cases

**Directory existence.** `state.job_dir` does not exist when `_abort_stall` fires — it is normally
created by `write_riding_report`, which `_abort_stall` has not yet called. Fix: explicit
`state.job_dir.mkdir(parents=True, exist_ok=True)` before the first write. `write_riding_report`'s
own `mkdir` then fires safely as a no-op.

**`os._exit` in tests.** `_abort_stall` ends with `os._exit(1)`, which terminates the Python process,
killing any test runner. Mitigation: `unittest.mock.patch("src.news.engine.proxy_riding.rider.os._exit")`
neutering the call before invoking `_abort_stall` directly with a synthetic `RiderState`. The patch
target is the module-level binding in `rider.py`, not `os._exit` globally.

## Verification

Script: `/tmp/verify_watchdog_path.py` (one-shot, not committed).

Constructed a minimal `RiderState` with `output_dir = platform_dir` (tmpdir), `job_dir =
platform_dir/scrape_jobs/20260620T120000Z`, two queued URLs, one in-flight URL, and a pre-existing
`platform_dir/raw/abc123.html` to probe the raw-path regression.

Assertions (all pass):

| Check | Result |
|---|---|
| `job_dir/remaining_urls.txt` exists | PASS |
| `job_dir/job.md` exists | PASS |
| `platform_dir/remaining_urls.txt` absent | PASS |
| `platform_dir/job.md` absent | PASS |
| `platform_dir/raw/abc123.html` untouched | PASS |
| `job_dir/raw/` absent (raw never written to job_dir) | PASS |
| queued URL in remaining_urls.txt content | PASS |
| in-flight URL in remaining_urls.txt content | PASS |
| `os._exit(1)` called exactly once | PASS |
