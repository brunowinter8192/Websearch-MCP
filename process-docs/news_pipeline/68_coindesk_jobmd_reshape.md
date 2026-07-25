# 68 — CoinDesk job.md reshape: trim + eligible-pool-over-time

**Branch:** `riding-report-trim`.
A prior round dropped two plots and `remaining_urls.txt`. This round trims five more noisy sections
and adds the first exhaustion-relevant time-series metric.

## Part A — Trim

Five sections removed from `_write_md` (`reporter.py`):

| Section | Rationale |
|---|---|
| `## HTML size distribution (ok URLs)` | Percentile table of raw HTML char-count — diagnostic during engine bring-up, noise in steady-state backfill |
| `## Markdown length distribution (ok URLs)` | Same — body-level signal useful for regwall debugging, not for daily backfill ops |
| `## Failed URLs` | 20-row URL/error table — already captured in logs; adds length without backfill-ops signal |
| `## Regwall URLs (distinct)` | 50-row URL list — same |
| `| Backfill projection (61k) |` row in `## Throughput` | Derived from `urls_per_min`; reader can compute; the `61k proxy estimate` row in `## Proxy riding` is kept (different metric, kept) |

**Dead `_compute_stats` fields pruned:**

- `html_pct` — `ok_html_sizes` collect + `_percentiles()` call removed.
- `md_pct` — `ok_md_lens` collect + `_percentiles()` call removed.
- `backfill_h` — `_BACKFILL_TOTAL / urls_per_min / 60` computation removed. `_BACKFILL_TOTAL` constant
  kept: still consumed by `proxies_for_backfill` (`round(n_proxies_burned / max(n_ok,1) * _BACKFILL_TOTAL)`).
- `_percentiles()` helper function — only called to produce the two dead fields; removed entirely.

Sections reading `state.job_records` directly (`## Failed URLs`, `## Regwall URLs (distinct)`) left no
dead stats fields — they bypassed `_compute_stats`.

All kept sections unchanged: `## Counts`, `## Throughput` (minus backfill row), `## Proxy riding`,
`### Ride length`, `## Regwall` (counts table), `## Plots`, `cumulative.png`.

## Part B — Eligible proxy pool over time

### Problem

The rider loads its pool once (~26k browser-eligible proxies) and burns proxies into a 60-min cooldown
with no refresh. Exhaustion risk — especially for the full 61k backfill — is invisible in the existing
report. TheBlock's `proxy_pool` engine refreshes its pool every 60 min; the janitor writes `## Proxy
usage per 60-min window` bucketing attempt events. The rider has no pool-size signal at all.

### Instrumentation (`rider.py`)

`RiderState` gains `pool_samples: list = field(default_factory=list)` — each entry a
`(elapsed_s: float, n_eligible: int, n_cooldown: int)` tuple.

`_watchdog` gains `t0_mono = time.monotonic()` captured at function entry (before `while True`).
After each `await asyncio.sleep(interval)`, before the `all_resolved` check:

```python
elapsed_s  = time.monotonic() - t0_mono
n_eligible = len(state.cooldown_mgr.eligible_candidates(state.proxy_pool))
n_cooldown = state.cooldown_mgr.cooldown_count()
state.pool_samples.append((elapsed_s, n_eligible, n_cooldown))
```

Sampling before `all_resolved` ensures a final-state sample even when the run completes on the first
poll. Elapsed base: monotonic clock consistent with `last_progress_mono`. Does not use `state.t_job_start`
(UTC datetime) — avoids timezone arithmetic, matches the stall-detection clock.

Sampling cost: `eligible_candidates()` iterates ~26k `(proto, hp)` tuples with one dict lookup + one
datetime subtraction each — ~1–5 ms. `cooldown_count()` iterates only burned proxies (much smaller).
Poll interval is `min(30, stall_timeout_s / 4)` = 30 s in production. Negligible.

### Windowing + render (`reporter.py`)

`_compute_stats` buckets `state.pool_samples` into 10-min windows (`_WIN_S = 600`). Window index:
`int(elapsed_s / _WIN_S)`. Per window: `min_eligible` (worst-case availability), `avg_eligible`
(rounded int), `peak_cooldown` (worst-case in-cooldown count). Also exposes static `pool_total =
len(state.proxy_pool)` (loaded count, never changes during the run).

`_write_md` renders `## Eligible proxy pool over time` between `### Ride length` and `## Regwall`:

```
Browser-eligible pool (loaded): N

| t (min) | min eligible | avg eligible | peak in-cooldown |
|---|---|---|---|
| 0–10    | …            | …            | …                |
| 10–20   | …            | …            | …                |
```

If `pool_samples` is empty (run completes before first watchdog poll): single line
`"No samples — run completed before first poll."` — no table rendered.

### Edge cases

| Case | Handling |
|---|---|
| Empty `pool_samples` | No table; single fallback line |
| Run < 10 min | All samples in window 0; one-row table (0–10 min) |
| Fast run, `all_resolved` on first poll | One sample before `all_resolved` check; one-row table |
| Stall abort | `pool_samples` covers all polls up to abort; table shows exhaustion trend |

### Contrast with TheBlock janitor

TheBlock: pool refreshes every 60 min → 60-min windows tracking `pool_size` (from refresh event) +
attempt-based metrics (proxies tried, URLs handled). Rider: pool loaded once, burns down → 10-min
windows tracking `n_eligible` (live count from `eligible_candidates`) + `n_cooldown`. Both use the
same per-window bucketing pattern (`int(elapsed / window_s) == k`), same table style.
