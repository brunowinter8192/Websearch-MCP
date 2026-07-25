# 23 — Re-Check Interval: The Question + Where to Source It

**Date:** 2026-06-12
**State:** Alive-recheck mechanism IMPLEMENTED + merged to dev (2026-06-12). The alive-check now skips proxies checked within a window X; baseline **X = 1 h** via `--recheck-window`. First snapshot taken (109 proxies, 21.1% alive). Next: survival-curve tuning of X from the log. Source since expanded to `--source curated` (monosans + proxifly) — combined-run snapshot + source details in the following entry; the recheck mechanism here is unchanged and source-agnostic. Strand B (CF docs) captured to `searxng-cli-reference` as background evidence; CF-cooldown + the per-IP burn budget are deferred; ML IP-reputation is out of scope.

## The question

After a `probe_liveness --source monosans` batch, the whole monosans pool (~103) is grazed in one go (concurrency 128 > pool size). Re-running immediately re-checks the same proxies for nothing. The cycle only becomes meaningful again once enough time has passed that a proxy's status might have CHANGED. So the governing parameter is:

> **Given a proxy that is currently unavailable, after how long is it worth re-checking?**

This is the crux of the whole batching/trying approach — it sets the cycle cadence.

## Two cases — same handling, DIFFERENT recovery clocks

The user framed dead and burned as "the same case". Operationally yes (don't use, re-check later), but the recovery MECHANISM — and therefore the interval AND the source — differ:

| Case | What it is | Recovery governed by |
|---|---|---|
| **Dead** | host offline / unreachable (timeout, refused) | free-proxy churn / host lifetime |
| **CF-burned** | host ALIVE (passes neutral check) but Cloudflare 403/429'd the IP | CF rate-limit / IP-reputation cooldown |

A CF-burned proxy is NOT dead — it still answers the neutral check. Conflating them means applying one re-check threshold to two different clocks.

## Role of the log (already built)

`logs/proxy_status_log.json` records `last_seen` + `last_status` per proxy. That IS the empirical instrument for the re-check interval: once it has runs across hours, we can ask "which proxies last failed > N ago" and tune N against observed recovery. External defaults SEED the threshold; the log TUNES it. The pain is that measuring from scratch is slow — hence: borrow community defaults first.

NOTE: the current log only knows neutral alive/dead (from `probe_liveness`). CF-burn is a later stage not yet logged. When CF-stage logging is added, "CF-blocked" should be a THIRD outcome distinct from alive/dead — precisely because its re-check clock differs. (This does not contradict the "don't store the liveness failure reason" rule — that concerned the dead-host buckets, which genuinely don't matter.)

## Where to source it (research targets for next session)

### Strand A — "dead proxy, when to re-check" (free-proxy churn)
- **Mature proxy-pool projects on GitHub** — e.g. `jhao104/proxy_pool` and peers implement scoring + recheck schedulers. Their defaults (recheck interval, fail-count-to-drop) are community-tested values to borrow. Read the scheduler code. → `gh-cli`.
- **monosans/proxy-scraper-checker itself** — rechecks HOURLY, publishes only currently-alive. The hourly cadence is a scale-tested default in its own right.
- **Academic free-proxy measurement studies** — proxy uptime/churn distributions. → arxiv.

### Strand B — "CF-burned proxy, when usable again" (CF cooldown)
- **Cloudflare rate-limiting docs** — documented block/counting windows + durations.
- **Web-scraping vendor engineering blogs** (ScrapeOps, ZenRows, Scrapfly) — empirical CF-ban-duration findings from scale.
- **r/webscraping** — practitioner reports on real CF cooldowns. → reddit-cli.
- **Our own earlier CF-block entry** — `probe_discovery` observed 429 persisting >5 min; the "1–2h recovery" there was an unmeasured guess.

## Captured evidence — Strand B, Cloudflare's own docs [searxng-cli-reference, indexed 2026-06-12]

Source: `developers.cloudflare.com` WAF rate-limiting-rules + challenge clearance docs, 12 pages captured to `searxng-cli-reference` (seed `https://developers.cloudflare.com/waf/rate-limiting-rules/`, culled). Answers the CONFIGURABLE-rule side of the CF block clock:

- **Block duration = the rule's "Duration" / `mitigation_timeout`** — "once the rate is reached, the rule applies the action to further requests for [this many] seconds." Discrete site-owner-configurable set: `0` (=throttle, no fixed block), `10`, `60` (1 min), `120`, `300` (5 min), `600` (10 min), `3600` (1 h), `86400` (1 day). CF's own best-practice examples use 10 min (forms), 1 h, and "Block for 1 day" (severe credential-stuffing).
- **Counting window = `period`** — 10 s up to 1 h (10/60/120/300/600/3600; footnote up to 65535 s). The window over which requests are tallied before the rule trips.
- **Challenge path:** if the action is a challenge (not a hard block), solving it sets a `cf_clearance` cookie — **default lifetime 30 min** (CF recommends 15–45). A challenge-gated proxy that solves once is clear ~30 min; one that cannot solve is re-challenged every request.

**Grounds the old guesses:** the earlier CF-block entry's "1–2h recovery" guess and its observed "429 persisting >5 min" are consistent with standard `mitigation_timeout` values (600 s / 3600 s). → defensible **CF-burned recheck SEED ≈ 1 h** (covers the common 600–3600 s configs), 10 min as an aggressive floor.

**Gap NOT closed by CF docs:** the IP-reputation / Bot-Management (ML) cooldown — CF deliberately does not document its decay; the `/bots/` docs likely won't carry a number either. theblock.co's specific config is unknown (empirical only). These need a vendor-blog empirical figure (ZenRows / Bright Data) or direct measurement in our CF stage — NOT more CF docs.

## Mechanism + baseline X — alive-recheck filter implemented (2026-06-12)

### Refined state model (user framing)
Three proxy states, two checks:
- **States:** (1) dead — fails the alive-check; (2) alive but CF-blocked from the first request; (3) alive, passes CF initially, then **burned** after 1–2 requests (per-IP budget exhausted).
- **Checks:** alive-check (neutral, `icanhazip`) and CF-passability check. Every proxy is either dropped at the alive-check or carried forward to CF. `proxy_status_log.json` already records alive/dead per proxy at the alive-check.

Focus decision: the FIRST anchor is the **alive-check re-run interval**. CF-cooldown and the per-IP burn budget are deferred; the ML IP-reputation angle is out of scope entirely (not relevant to us).

### The mechanism — X is a staleness TTL on a proxy's alive-result
An alive run is NOT a re-check of every proxy ever seen — it polls the CURRENT monosans list and diffs against the log:
- key absent from log OR last-check age ≥ X → **CHECK**
- key present AND age < X → **SKIP** (reuse the logged result)

X = how long an alive-result stays trusted. Too large → stale (use a since-died proxy / miss a revived one); too small → redundant rechecks + more load per run. A genuinely new proxy has no log entry → always checked, never wrongly skipped. A "dead < X" entry necessarily belongs to a proxy we already tested that monosans kept on its list — skipping it = trusting our own recent measurement (our neutral check is authoritative for us, regardless of monosans' vantage point). No hidden conflict (verified in discussion).

### Baseline X = 1 h
Anchored to the monosans source-refresh cadence (~hourly) — a known bound, not a guessed small number. The staleness risk is absorbed downstream: the CF check + the fetch loop validate every proxy per request (200+XML), so a stale "alive" just fails downstream and rotates out — bounded waste, not corruption. Above the refresh interval X is moot (the list turns over hourly). Tunable via `--recheck-window` without a code edit.

### Implementation [merged to dev, commit 664126f]
`partition_fresh(entries, window_s)` in `proxy_status_log.py` (reuses `_proxy_key` for auth-strip matching; parses `last_seen` timezone-aware via `.replace(tzinfo=timezone.utc)`). Wired on the `--source monosans` path in `probe_liveness_workflow`, between load and `run_checks` — only `to_check` goes to checking + `record_run`; skipped proxies keep their old `last_seen`. CLI flag `--recheck-window` (default 3600). Frozen/sample path untouched.

### First snapshot [2026-06-12T19:58Z]
Filter inert as predicted — all 81 prior log entries were ~18 h old → **0 skipped**, whole current list checked. Current monosans list = **109 proxies, 23 alive (21.1%)**, 86 dead (hard_timeout 63 dominant, then connect_timeout 8, http_non200 6, read_timeout 4, connection_refused 4, proxy_handshake_error 1). Log accounting verified: 81 → 162 unique; 109 got the run timestamp + incremented `checks` + `last_status`; 53 entries that dropped off the current list left untouched (`last_seen` preserved).

### Next — survival-curve tuning
Re-run alive checks over several hours; from the log compute P(still alive at T+Δ | alive at T) — the Δ at which a meaningful fraction has flipped IS the empirical X. Open: whether alive and dead results need different TTLs (the data decides; not a separate research task).

## Open questions
- Dead-proxy re-check interval (Strand A) — borrow a default, then tune via the log.
- CF-burn cooldown (Strand B) — borrow a default, then measure directly (we burn proxies anyway in the CF stage).
- Should the log distinguish neutral-dead vs CF-blocked once the CF stage is wired? (Leaning yes — different recovery clocks.)
