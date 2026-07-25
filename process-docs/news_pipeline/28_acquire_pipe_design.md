# 28 — theblock acquire-pipe design (forward path post-jhao104)

**Date:** 2026-06-13
**State:** Design LOCKED (chat synthesis). Build is a fresh dev/ pipe; the dev-run can start on the existing curated pool, the backfill pool is pending the survey from the prior jhao104-adoption entry. Forward path after jhao104 was dropped there.

## Why a fresh pipe
The existing `dev/news_pipeline/theblock/` scripts (`pipe_theblock.py`, the `probe_*`) carry investigation-era stages — neutral-alive pre-filter, separate CF-check — that this design DISCARDS. To avoid mixing, the production-candidate pipe is built clean in `dev/news_pipeline/theblock/acquire_pipe/`.

## Architecture — single TARGET-DRIVEN fetch-with-rotation loop
**KEY decision: NO separate proxy-check stage. Every proxy request is a PRODUCTIVE theblock fetch.** A separate check would waste 1 per-IP-budget unit; with B as low as 1-4 (measured 4-20 in the pipe/cycle-economics entry) that is wasteful-to-catastrophic (B=1 → proxy dead before any useful fetch). A proxy earns use by successfully fetching real content.

- **Input:** a TARGET (a defined set of URLs to fetch) + a candidate proxy pool (from ranked sources).
- **Loop until target complete (or candidates exhausted → report the gap):**
  - take next unfetched target URL → fetch via `curl_cffi impersonate="chrome"` through a proxy.
  - **200 + content** → URL done (data obtained) AND proxy works → ride it for subsequent URLs until it burns (403/429 = hit budget B).
  - **fail (403 / dead)** → URL returns to the queue for the next candidate; proxy → 60min cooldown.
- **Uniform lifecycle (no special-casing of "passers"):** candidate → working/drained → dead/burned → **60min cooldown** → eligible again after 60min. Whether a proxy dies on its first fetch (dud) or after B productive fetches (good), it ends in the same 60min cooldown.
- **60min cooldown = the CF-block duration AND the dedup/staleness state** — don't retry a dead/burned proxy for 60min (its CF block lasts ~that long; CF mitigation_timeout 600-3600s per the recheck-interval entry).

The old two-stage (build-passer-pool via checks, then fetch) model is SUPERSEDED — the "passer pool" exists only as the transient working-set of currently-succeeding proxies.

## Two chained targets
- **Dev-run target = the 64 theblock sub-sitemaps** (fetch sitemap index → parse → 64 sub URLs `sitemap_tbco_post_type_post_N.xml` etc.). Output = ~27k article `/post/` URLs. SMALL — validates the whole pipe end-to-end (rotation, cooldown, B-economics, logging). The curated pool (3477, ~52 CF-passers × budget ~9 ≈ ~468 possible fetches) covers 64 easily → **does NOT need the survey**.
- **Backfill target = the ~27k article pages.** Needs the survey-expanded candidate pool (enough fresh candidates to feed the loop while 60min cooldowns hold burned proxies out).

Same pipe, two targets, chained: target 1's output is target 2's input.

## Parameters
| Param | Value |
|---|---|
| Fetch client | `curl_cffi impersonate="chrome"`, per-protocol scheme (http/socks4/socks5) |
| Pool weighting | socks4-favoured (best CF cohort, 3.57% vs http 0.94%, per the jhao104-adoption entry) |
| Timeout | 15s |
| Concurrency | 50 (conservative for heavy theblock GETs; revisit) |
| Cooldown | 60min, uniform for dead/burned |
| Candidate pool | dev = curated (3477); backfill = survey-ranked top-down to "enough not to starve during cooldowns" (~20-25k, pending survey) |
| Termination | target complete OR candidates exhausted (report gap) |

## Logging
1. **Fetch progress** — URLs done / total (the goal) + successful fetches per time.
2. **Observed B per proxy** — requests-before-burn; the economics number. Distribution over all ridden proxies.
3. **Working-set size over time** — how many proxies currently riding successfully.
4. **Failed-attempts per successful fetch** — candidate-pool richness / whether the sources suffice.
5. **Per-proxy event log** — proxy_key, timestamp, URL, result, running success-count = simultaneously the cooldown/dedup state.

**NO per-repo runtime attribution** — overlapping lists make per-source credit meaningless (per the curated-source-set entry). The survey is a one-time selection snapshot only.

## dev/ first, then src/
Built + validated in `dev/news_pipeline/theblock/acquire_pipe/`. Ported to `src/news/platforms/theblock/` via the Platform contract only after the dev-run validates the machine AND the backfill is proven.

## Build status + decisions [2026-06-13]
Built fresh in `dev/news_pipeline/theblock/acquire_pipe/` (worker repo-survey; stages 1-4 committed + merged to dev). Modules: `p1_fetch.py` (curl_cffi-chrome fetch primitive + XML/HTML validators), `p2_cooldown.py` (in-process per-run 60min cooldown, socks4-first ordering, `proxy_key` reused from proxy_status_log — NOT cumulative/file-based), `p3_target.py` (`build_sitemap_target`: index → 64 sub-sitemap URLs, with proxy-fallback if the direct-from-home index GET 403s), `p4_loop.py` (the concurrent working-set rotation loop), `p5_logger.py` (the 5 logging surfaces). `acquire_pipe.py` orchestrator = Stage 5, stub only (pending). DOCS.md in the folder.

**Concurrency = 128 (decided, not 50).** Candidate search runs at concurrency 128 (CLI param). Reasoning: ~128 is the grounded router-clean-zone (per the concurrency-sweep entry) AND the pool-sizing was computed at 128. The 50 used for the SURVEY/probe was justified ONLY there (single-shot rate measurement, no retry → a router-false-timeout would bias the rate down). In the PIPE the retry logic absorbs false-timeouts (a false-timed-out URL just retries with the next proxy → nothing lost), so conservatism is pointless. 128 vs the heavy-theblock-GET clean zone is unmeasured → the test run logs the timeout-fraction to confirm; if 128 saturates (effective yield drops, like 512 did on light checks) tune DOWN data-driven.

**Loop = CONCURRENT working-set, not sequential single-rider** (course-corrected mid-build). Sequential one-at-a-time with 15s timeouts at ~1.5% pass = ~hours to find workers. Fix: fire ~128 (URL, proxy) attempts in parallel — successes join the working set + their URL is done, failures → cooldown; ride the working set across the queue, refill via concurrent batches. Finding ~7 workers (enough for 64 sitemaps at B≈9) ≈ 2-3min vs ~2h sequential. Still every-request-productive (each parallel attempt targets a real URL).

**Backfill candidate pool = top 13 survey repos (~22k unique)** (per the jhao104-adoption entry). socks4-favoured. NOT only-socks4 (would lose the http stars themiralay/monosans); socks5 is the weakest if we ever trim. First run: blast all protocols, log per-protocol, refine later.

## Pending — next session
- **Stage 4 test run** at concurrency 128 on the COLD curated pool: the 64-sitemap dev-run — measure real wall-time + observed B + timeout-fraction (128 saturation check).
- **Stage 5** — `acquire_pipe.py` orchestrator + CLI: load pool → `build_sitemap_target` → loop → extract article URLs → **persist the ~27k article URL list to a file** (the input for the backfill target).
- Then the **27k backfill run** (target = persisted article URLs, pool = top 13 repos).
