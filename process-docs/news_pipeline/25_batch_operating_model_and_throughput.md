# 25 — Batch Operating Model + Throughput Economics

**Date:** 2026-06-12
**State:** Design crystallized in-session (chat brainstorm). The alive-check operating model for prod/backfill: hard-capped batches cycling the pool, run-time held constant. Throughput re-confirmed router-bound. Implementation pending (a `--limit` cap + funnel metrics); TheSpeedX standalone eval in flight.

## Throughput facts (concurrency 128, timeout 5s/5s)
Measured: curated run = 3508 proxies in 255s pure check-time → **~13.8/s**; the prior concurrency-sweep entry @128 ≈ 11/s; the pipe/cycle-economics baseline 11.4/s. Operating figure: **~12-14 proxies/s**.

Linear cost model:

| Pool | Check-time @128 |
|---|---|
| 1.000 | ~75s |
| 3.500 (curated now) | ~4 min |
| 9.000 (+TheSpeedX raw) | ~12 min |
| 20.000 | ~28 min |
| 320.000 (full raw set) | ~7-8 h |

## Concurrency is router-bound, NOT a free speed lever [corrects an in-session error]
A mid-session suggestion to raise concurrency 128→512 for speed was WRONG. The measured downward sweep (from the prior concurrency-sweep entry, bookended, churn≈0) shows alive% COLLAPSES with concurrency: 64=9.3%, 128=7.9%, 256=4.0%, 512=1.7%. Raising to 512 would have cut found-alive ~4.6×.

**Mechanism — home-router NAT/conntrack saturation.** Each check is an outbound connection through a mostly-dead proxy, occupying a conntrack slot on the home router; a dead proxy holds its slot until the 12s timeout fires. At high concurrency, hundreds of slots are tied up by timing-out-dead connections, so a genuinely-alive proxy's response cannot be forwarded in time → it false-times-out (`hard_timeout`) → counted dead. Signal: `hard_timeout%` balloons (93% @512 → 60% @128 → 51% @64); at low concurrency the dead-taxonomy shifts to GENUINE failures (`proxy_handshake_error`, `connection_refused`). The Mac is far from its own limits at 512 (FD ~1M, ephemeral ports ~16k) → the saturating resource is the external NAT = the router.

**How to measure the router's tolerance.** You do NOT read an absolute conntrack number — consumer routers give no shell access, and the number is less useful than the response curve. You run a FIXED proxy sample (`seed=42`) at several concurrency levels with a start/end BOOKEND (same level twice, bracketing the sweep) to rule out pool churn, and read off where alive% plateaus. The plateau is the router's clean zone. That IS the measurement — it measures the operationally relevant quantity (alive-detection accuracy vs load), not an abstract capacity. A more direct alternative: ramp concurrency against a known-good endpoint WITHOUT proxies (every connection must succeed) and find where success/latency degrade — isolates the raw router ceiling, but is less representative than the real proxy workload.

**Timeout × concurrency coupling.** The optimal concurrency is a router property (fixed hardware) ≈ 128, but it is COUPLED to the timeout: a dead proxy holds its conntrack slot for the full timeout (now 12s = connect 5 + read 5 + 2 slack). A SHORTER timeout frees slots faster → the router tolerates HIGHER concurrency before saturating. So the real speed lever is the PAIR (timeout, concurrency), found via a 2D-sweep — not concurrency alone. Deferred until pool size makes it necessary.

## Capped-batch operating model (the prod/backfill design)
Do NOT evaluate the whole pool per run. Cap each alive-run at a hard limit B of proxies. The log-diff (`partition_fresh`) guarantees each batch is FRESH candidates (not checked within X); over successive runs you cycle the pool B-at-a-time, feeding alive proxies to CF as you go. Run-time is then CONSTANT (~75s for B=1000) regardless of total pool size — the throughput "problem" dissolves into "how many batches to cycle once".

**Capacity relationship (rigorous):**

> Pool_max (kept fully fresh) = B × (X / cadence)

With B=1000, X=60 min, cadence=5 min: 1000 × 12 = **12.000**. A 12k pool gets every proxy checked once per hour. Above 12k the cycle falls behind X — but a backfill does NOT need full freshness, it needs a steady alive→CF supply, which the cap delivers at constant cost; the pool just cycles slower through its tail. To raise the 12k ceiling: increase B, shorten cadence, or lengthen X (the formula gives the exact factor).

**Slice ordering:** the B taken from `to_check` should be un-logged (new) proxies first, then oldest `last_seen` first — the most-overdue get priority, fair cycling. NOT a naive head-slice.

## Funnel metrics (per-run logging) + %-gating
Log per run the full funnel: **raw total → after dedup → after log-diff → evaluated → alive-of-evaluated**. Currently `sweep_log` records n (post-filter) + skipped + alive%; the raw-total and dedup-drop are NOT yet logged → gap to close.

**Per-repo include/exclude by marginal alive% — resolves the "no scoreboard" tension.** A persistent per-source scoreboard is pointless because lists overlap (per the curated-source-set entry). But a one-time MARGINAL measurement is clean: add a repo ONE AT A TIME; because the existing pool is fresh-skipped by the log-diff, the run's newly-evaluated set ≈ the new repo's unique contribution, and its alive% ≈ the repo's marginal yield. Low marginal alive% or few unique proxies → drop; high unique-alive → keep. The funnel metrics are the decision instrument. The cap-model and the %-gating are the SAME mechanism (capped batches right after adding a repo are automatically that repo's proxies). Decision is by **alive %, not absolute count**.

## Standalone vs marginal eval
Two ways to measure a new repo, both valid:
- **Standalone** (TheSpeedX, this session): a `--source <repo>` eval branch checks ALL of the repo's proxies, no filter/cap, no `record_run` (no per-proxy log pollution for a maybe-rejected repo). Gives the repo's raw alive% in isolation. Compare to curated 15.6%.
- **Marginal** (in-pool): add the repo to the curated source, run capped batches; the log-diff makes the batch ≈ the repo's unique contribution. Gives marginal yield net of overlap.

## Open / deferred
- 2D timeout×concurrency sweep — deferred until pool > ~20k (intra-sweep decay: sweep exceeds the ~30 min pool-stability window from the prior concurrency-sweep entry's bookend) / ~43k (full sweep > X=1h → the staleness filter can no longer keep the pool fresh; the delta-trick breaks).
- Cap default B=1000 (~75s/batch, ~1.2 min — matches the "grab proxies fast, feed CF, repeat" loop).
