# 30 — Streaming Logger + Proxy Economics (curated pool)

## What we did

Rebuilt `p5_logger.AcquireLogger` to stream events to JSONL on every fetch attempt
(vs. accumulating in memory and writing only at `finalize()`). Added Surface 6:
throughput over time, derived entirely from the durable JSONL.

Then ran the 64-sub-sitemap target again (curated pool, concurrency 128) to measure
the proxy economics that were lost in the prior sitemap dev-run entry when the process was killed before
`finalize()`.

## Design

**Streaming JSONL (`p5_logger.py`):**
- `__init__`: creates `acquire_pipe_logs/acquire_events_<ts>.jsonl` immediately and
  opens it with `open(..., "a", encoding="utf-8", buffering=1)`. `buffering=1` =
  line-buffered: every `write()` call ending in `\n` is flushed to the OS buffer
  immediately. No Python-side accumulation.
- `record_attempt()`: builds the event dict (unchanged fields: `proxy_key`, `ts`,
  `url`, `result`, `proxy_success_count`) and writes `json.dumps(event) + "\n"` to
  the open file handle. `self._events: list[dict]` removed entirely.
- `finalize()`: closes the file handle, then calls `_throughput_buckets(jsonl_path)`
  to build Surface 6 from the on-disk JSONL. `_write_event_log()` removed —
  superseded by the streaming write.
- In-memory state retained: `_done`, `_attempts`, `_b_dist`, `_ws_snapshots`,
  `_proxy_successes` — all small (scalars / per-proxy counters, max ~pool-size entries).

**`_throughput_buckets(jsonl_path)` — fully JSONL-derived:**
- Reads the JSONL file, parses all events.
- `t0 = min(ts)` across ALL events (not an in-memory `_t0_wall`) — so the function
  is callable on any partial JSONL from a killed run, with no runtime context needed.
- Buckets `result == "ok"` events by `int((ts - t0).total_seconds() // 60)`.
- Returns `dict[int, int]`: minute-offset → ok-fetch count.

**Thread safety:** `as_completed()` in `run_loop` iterates sequentially in the main
thread — `record_attempt()` is always called single-threaded. No lock needed.

## Validation: kill-safe confirmed

The run was killed at 61/64 (after the straggler tail stalled). `finalize()` never ran.
The complete MD report — including B-per-proxy distribution, fail/success ratio, and
Surface 6 throughput curve — was reconstructed offline from the durable JSONL alone,
using a standalone script calling `_throughput_buckets()` and `_write_summary()`.

This is the direct proof that the streaming design closes the finalize()-data-loss
problem documented in the prior sitemap dev-run entry.

B-distribution reconstruction note: `proxy_success_count` in each event is the
running ok-count for that proxy at the time of the event. For proxies that were burned
(had at least one success then failed), `max(proxy_success_count)` across their events
equals B. This works correctly from the JSONL without needing the in-memory `_b_dist`.

## Proxy economics — curated pool, concurrency 128

Run: 64 sub-sitemap targets, curated pool (~3477 candidates), concurrency 128.
Killed at 61/64 after straggler stall; 797 total events in JSONL.

### B-per-proxy distribution

| B (fetches before burn) | Proxies |
|---|---|
| 1 | 19 |
| 2 | 6 |
| 3 | 3 |
| 4 | 1 |
| 6 | 1 |
| 7 | 1 |

- **Proxies retired: 31**
- **Mean B: 1.84** — **Max B: 7**
- 61% of retired proxies had B=1: one success, then burned. The pool is dominated by
  single-use proxies; multi-use proxies (B≥3) are rare exceptions, not the rule.

### Fail/success ratio

| Metric | Value |
|---|---|
| Successful fetches | 61 |
| Failed attempts | 736 |
| **Ratio (fails/success)** | **12.07** |

~12 proxy attempts are consumed per successful sub-sitemap fetch.

### Surface 6 — throughput over time

| Minute | OK fetches |
|---|---|
| 0 | 26 |
| 1 | 17 |
| 2 | 6 |
| 3 | 0 |
| 4 | 0 |
| 5 | 3 |
| 6 | 1 |
| 7 | 1 |
| 8 | 1 |
| 9 | 2 |
| 10 | 2 |
| 11 | 2 |

**Pattern: bursty, not linear.** First 2 minutes: 49 ok (80% of total). Gap at
minutes 3–4 (all socks4-first good proxies burned, no eligible candidates yet). Trickle
at minutes 5–11: 1–3 ok/min as new candidates cycle in from the cold pool. The
initial burst is front-loaded because `CooldownManager.eligible_candidates()` sorts
socks4-first — the socks4 cohort drains first and fastest, leaving the slower http/socks5
tail and eventually a brief zero-throughput gap before fresh candidates arrive.

## Conclusion: curated pool unsuitable for backfill

**Curated pool ceiling at ~60 successes before collapse.** The proxy economics on the
curated 3477-candidate pool yield ~60 usable fetches before the good-proxy supply
exhausts and throughput falls to trickle. For a 64-item target this is acceptable
(61/64 = 95%); for 26k article URLs it is not.

**Naive extrapolation (unreliable but directional):**
- Rate model: 61 ok / 11.3min = 5.4/min — then collapse. The trickle rate (min 5–11)
  is ~1.6/min.
- If trickle sustained for 26k: 26,000 / 1.6 ≈ 270h (~11 days). Not actionable.
- If pool recharges via 60min cooldown in cycles: each 60min cycle yields ~60 ok.
  26,000 / 60 ok-per-cycle × 60min/cycle ≈ 26,000min ≈ 18 days. Also not actionable.

**Confirms the 22k-survey-pool as the backfill path.** The 22k-candidate top-13 survey
pool (per the acquire-pipe-design entry) has ~6× more candidates and higher CF-passability (selected by
successful theblock survey hits). The B-distribution and fail/success ratio on THAT pool
are the open measurement needed before a backfill wall-time estimate is meaningful.
