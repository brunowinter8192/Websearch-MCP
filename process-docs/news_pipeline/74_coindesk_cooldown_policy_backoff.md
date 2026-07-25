# 74 — CoinDesk riding: cooldown policy rethink (fixed 60-min → selectable exp-backoff)

Scope: the riding engine's dead/burned-proxy handling. Reconsiders the fixed 60-min cooldown against
external practice, converges on a **selectable** policy (`--cooldown-policy fixed|exp`, default `fixed` =
byte-identical) for an A/B experiment. Implementation in progress (worker on `dev`).

## State before this change (the fixed cooldown)

- `PersistentCooldownManager` (`src/news/engine/proxy_pool/cooldown.py`, **SHARED** with theblock's
  proxy_pool engine): in-memory per-job (fresh `_burned_utc` dict each process — NOT persistent across
  runs despite the name), `COOLDOWN_S = 3600`. `mark_burned` stamps now; `is_eligible` = never-burned OR
  `now − burned_at ≥ 3600`; `eligible_candidates(pool)` filters the current pool.
- Ride loop (`rider.py`): a proxy rides URLs while succeeding; `connect_fail` → immediate burn (1 attempt);
  `regwall` → burn after `burn_threshold = 2`; `failed/empty` → burn after `FAIL_THRESHOLD = 2`. Ride-end →
  `mark_burned` → 60-min cooldown.
- Selection (`_next_proxy`): cursor over `eligible_candidates(current_pool)`. The 30-min pool refresh (from a
  prior session) atomically swaps the list; cooldown NOT reset on refresh; a cooled proxy that fell off the
  new list is naturally excluded (it is not in `pool`, so never a candidate — eligibility is a filter on the
  current list, not a queue).

## Question driving this

Is the 60-min/2-strike construct evidence-based or gut feeling? And: do pre-checks (alive-feeders) pay off?
(The alive-feeder was already dropped in a prior session; this re-validates that against external practice.)

## External evidence (GitHub, read this session via gh-cli-search)

Two shipped schools:

- **scrapy-rotating-proxies** (TeamHG-Memex / Hyperion Gray) — the use-and-detect school, matches our
  engine. `rotating_proxies/expire.py`: **NO pre-check** — proxies start `unchecked` and are used directly
  ("for crawling only 'good' and 'unchecked' proxies are used"). Dead handling = **exponential backoff with
  full jitter**: `next_check = now + uniform(0, min(cap, base·2**failed_attempts))`, `base = 300s` (5 min),
  `cap = 3600s` (60 min). `failed_attempts` resets to 0 on success (`mark_good`), increments on failure
  (`mark_dead`). First failure → re-check in 0-5 min; repeated failures grow toward the 60-min cap. Ban
  (≈ our regwall) and dead (≈ our connect_fail/timeout) share the SAME backoff path — the ban/dead split
  only routes the request *retry*, not the proxy backoff.
- **jhao104/proxy_pool** — the validate-then-serve school (a pool SERVICE, not a scraper). Continuous
  background validation against generic judges (httpbin.org, qq.com), `VERIFY_TIMEOUT = 10`,
  `MAX_FAIL_COUNT = 0` (evict on one recent failure), serve only verified via API. NOT applicable to us:
  validating against httpbin does not predict CoinDesk-regwall success (target-specific IP-rate metering),
  and we run no shared pool service.

Conclusion on pre-checks: the scraper-side practice confirms the earlier decision — for a target-specific
regwall the real fetch IS the check; pre-validation only exists in the service model, and there against
generic judges that would not predict our target. Pre-checks rejected (again).

## Design convergence

- Keep riding (good proxies ride while they succeed) — the core, unchanged.
- Replace the fixed 60-min cooldown with **exp-backoff + full jitter** (base 5 min, cap 60 min), per scrapy.
- `failed_attempts` per proxy, persisting across rides within the run. **Reset on productive ride**
  (`ride_ok ≥ 1`), increment on burn. A proxy that delivered this ride returns in ~5 min (`backoff(0)`);
  a 0-OK proxy backs off progressively (5 → 10 → 20 → 40 → 60 min cap).
- **All failure types treated the same** (regwall, connect_fail, failed/empty). The discriminator is ride
  productivity (`ride_ok ≥ 1`), NOT failure type.

### Rejected alternatives

- **User's initial: remove cooldown, flat 30-min-reset, each proxy max once.** Rejected. "Fresh pool every
  30 min" overstates novelty — `load_backfill_pool()` re-fetches the same 13 repos, ~90% stable over 30 min,
  so a flat reset re-tries the ~93%-dead set every cycle. "Max once" was separately a non-issue: ride-length
  data (job `20260620T010358Z`: mean 1.1, median 1.0) shows riding barely happens already, so abandoning it
  loses ~nothing — but a flat reset is blunter than exp-backoff.
- **Opus's asymmetric backoff (regwall short, connect_fail long).** Rejected by user: rests on an unverified
  assumption about how long an IP-rate block lasts. No evidence on IP-block duration → treat all failures the
  same (scrapy model). The "good proxy returns fast" goal is still met via reset-on-productive-ride, which
  keys on observed productivity (a fact) rather than failure type (a guess), and is self-correcting (a
  re-harvested proxy that then fails with 0 OK grows its backoff again).

### Supporting data

- job `20260620T010358Z` (500-URL, fixed cooldown): ride length mean 1.1 / median 1.0 / max 22;
  8,594 `connect_fail` of ~8,663 non-ok (93%); eligible 19,576 → ~11,799 over 30 min (no exhaustion in
  that window).
- 20k-run throughput (raw-mtime reconstruction, `dev/news_pipeline/coindesk_proxy_riding/analyze_write_times.py`,
  `--since 2026-06-20 03:45`): two-phase depletion — ~25-40/min fresh for ~3h, then ~5-15/min for ~10h;
  9,644 files over 12h51m; longest gap 4m21s (no stall). The eligible/cooldown time-series for the 20k run
  was lost to the manual Ctrl-C (now fixed by SIGINT/SIGTERM report-on-abort, added in a prior session) —
  the A/B runs will capture it.

## A/B approach (implemented; runs pending)

Selectable `--cooldown-policy fixed|exp` (default `fixed` = byte-identical control), implemented in a
DEDICATED `src/news/engine/proxy_riding/cooldown.py` (`RidingCooldownManager`) — the shared
`proxy_pool/cooldown.py` (theblock) is untouched, verified byte-identical (not in the change diff; theblock
callers `buffer.py`/`loop.py`/`scrape.py` unchanged). The active policy is rendered in each run's `job.md`
Counts table (`| Cooldown policy | fixed|exp |`) so the two A/B reports self-identify.

Run guidance: `--limit N` is applied BEFORE the in-raw dedup (`load_discover_filtered(limit)` → then
`filter_new_entries`), so re-running an already-scraped date-range yields 0 new ("all already in raw"). Run
each A/B variant on a FRESH, untouched year (e.g. fixed→2023, exp→2025; hash-verified 0 prior coverage) so
each gets a full N fresh URLs. Metric is proxy-pool dynamics (throughput + eligible-curve + ride-length),
range-independent; winner becomes default.

## Open

- Isolation mechanism resolved → dedicated `proxy_riding/cooldown.py` (theblock byte-identical, verified).
- A/B runs not yet executed (fixed→2023, exp→2025). Pending: compare throughput + eligible-curve + ride-length.
- Whether base = 5 min / cap = 60 min fit our connect_fail-dominated pool, or need tuning — the A/B informs.
