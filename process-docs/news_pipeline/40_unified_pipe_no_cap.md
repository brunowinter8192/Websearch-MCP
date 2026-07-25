# 40 — Unified pipe model: no caps, full pool, decoupled cadence, dead-URL handling

Crystallizes the proxy-pipe into one coherent model. Origin: the user observed the pipe was "splintered"
(pool selection an opt-in flag, a time cap, socks4 heuristics nobody asked for) and set a clear premise —
**a pipe runs to completion; we never cap time.** This session reworked the dev acquire-pipe
(`dev/news_pipeline/theblock/acquire_pipe/`) to that model. Builds on the tail-race work and the
over-scope retrospective.

## Principle

The pipe's ONLY termination condition is "every target URL resolved" — either fetched with valid content
(`done`) or confirmed permanently gone (`dead`). Time, attempt-count, and pool-exhaustion NEVER abort the
run; they only cause waiting and retrying. No `max_wall_s`, no `--max_hours`, no gap-on-timeout.

## The model (final state)

### Pool (acquisition + health)
- **One pool, full union** — `load_backfill_pool()` (the 13 GH-repo sources merged + deduped, ~22k). No
  curated/backfill choice, no `--pool` flag. Full pool is the baseline, not an opt-in.
- **Health = cooldown, not death** — a proxy that fails 2× consecutively is burned → 60-min cooldown
  (wall-clock UTC, persisted in `proxy_status_log.json`, keyed by proxy identity, survives restarts). After
  60 min it is eligible again. No proxy is permanently discarded.
- **No protocol ordering** — `eligible_candidates()` returns eligible proxies in plain pool order (the
  socks4-first heuristic was removed; it only reordered draw-priority, was not load-bearing).

### Two independent 60-minute clocks (the key mechanic)
- **Pool-refresh clock** — `_last_refresh`: a fresh full pool is fetched on a FIXED 60-min cadence from the
  initial fetch. The exhaustion path does NOT fetch and does NOT reset this clock (decoupled — see "Change
  2"). Only the scheduled tick at the loop top resets it.
- **Per-proxy cooldown clock** — 60 min from the moment THAT proxy was burned, independent of the pool
  fetch. A burned proxy reappearing in a fresh pool fetch (overlap is normal) stays ineligible until ITS
  own clock expires — `build_active_buffer` filters every (re)build through `cm.is_eligible`. The re-fetch
  never revives a cooled-down proxy.
- Worked example: t=0 fetch pool. t=20 proxy X burns → X eligible again at t=80. t=60 scheduled refetch
  (X is in it, but filtered out — cooldown until t=80). t=80 X's cooldown expires → X drawn + used again.

### Fetch engine (`run_loop`)
- `concurrency = 128` (fire 128 (proxy,URL) pairs per round, always), `buffer_size = 1280` (10× concurrency
  eligible buffer, topped up).
- Working-set reuse: proven-good proxies are tried first each round and reused until they 2-strike out
  (a success resets the consecutive-fail counter). This is load-bearing — dropping it caused a prior
  regression.
- Tail-race: when pending URLs < free slots, surplus proxies race the same leftover URLs,
  first-success-wins.
- Exhaustion (all eligible burned + buffer empty): sleep via `_compute_sleep` until the earlier of
  (next per-proxy cooldown expiry, next scheduled pool refresh), rebuild buffer from the EXISTING pool
  (newly-eligible cooled proxies get picked up), continue. No abort.

### Phases (same engine, different target + content_handler)
- Discovery: target = sub-sitemap URLs; handler parses `<loc>`/`<lastmod>` → article URLs.
- Backfill/content: target = article URLs; handler parses JSON-LD `articleBody` → cleaned article.
- 48h-delta: thin discovery variant (highest post sub-sitemap, lastmod ≥ now−48h).

### Observability (unchanged)
box_lock (one job at a time), streaming JSONL per-attempt, `job.md` + `cumulative_hits.png`.

## The five changes implemented this session

1. **No time cap** — removed `max_wall_s` / `DEFAULT_MAX_WALL_S` (`p4_loop.py`) and the `--max_hours` flag
   (`acquire_pipe.py`). The loop's only exit is empty queue.
2. **Decoupled pool-fetch cadence** — the exhaustion block in `run_loop` no longer calls `pool_provider()`
   or resets `_last_refresh`; it only sleeps + rebuilds the buffer from the existing pool. Pool fetch is the
   fixed 60-min tick alone. This separates the two 60-min clocks above.
3. **Removed socks4-first ordering** — `p2_cooldown.eligible_candidates()` returns plain pool order;
   `_PROTO_ORDER` deleted; `p6_buffer` docstrings updated.
4. **Full pool as only mode** — `acquire_pipe.py` drops the `--pool` flag and always calls
   `load_backfill_pool()`. `load_curated_proxies` stays defined in `curated_sources.py` but is unwired.
5. **Dead-URL handling** — `p1_fetch.fetch_url` now returns a 3-way `(status, content)` with
   `"ok"`/`"dead"`/`"fail"`. Classification: **HTTP 404/410 → `"dead"`** (origin reached, URL gone);
   200 + valid markers → `"ok"`; everything else (other status, connection/timeout/CF, invalid content) →
   `"fail"`. In `run_loop`: a `"dead"` URL is removed permanently (added to a new `dead` list, NOT
   re-queued, NOT in `done`) and the proxy is treated as working (joins wset, consec-fail reset, NOT burned
   — it reached the origin). `run_loop` returns `(done, dead, gap)`. All `fetch_url` callers updated to the
   new contract: `p3_target._fetch_index_via_proxy` (burns only on `"fail"`, skips on `"dead"`) and the
   dead-reference `p4_race.run_race` (consistency).

## Decided

- Dead signal = **HTTP 404/410 via a working proxy** only. Connection/timeout/CF/403/5xx = proxy fault →
  retry the URL via another proxy. This is correct dead-URL handling, not a cap.
- `p4_race.py` stays on disk as the retired tail-race reference (its idea is folded into `run_loop`); it is
  not wired in, but its `fetch_url` caller was updated for contract consistency.

## Open

- Live verification: the real 64er run on the full pool (no cap, full ~22k pool) has NOT been run yet — the
  user runs it. Expected: 64/64 sub-sitemaps, 0 dead (the sub-sitemaps exist), shorter wall time than the
  ~18.6 min curated baseline (bigger pool + tail-race).
- ok/dead collision on the same URL in one tail-race batch (one racer 404, another 200) is resolved by
  first-arrival via `batch_done` — near-impossible for real sitemaps, accepted.
