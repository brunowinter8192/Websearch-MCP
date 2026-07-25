# 29 — Stage 5 Build + Sitemap Dev-Run

## What we did

Built `acquire_pipe.py` (Stage 5 orchestrator, 83 LOC) and ran the sitemap dev-run at
concurrency 128 against the curated pool (monosans + proxifly, ~3477 candidates).

**content_handler design (p4_loop.py change):**
Added `content_handler: Callable[[str, bytes], None] | None = None` to `run_loop`.
At the `if ok:` success branch, fires `content_handler(url, content)` before updating
`done`/`wset`. Rotation logic (deque, working-set, CooldownManager, gap detection,
`psuccess`) unchanged. Pattern mirrors `_scrape_one` in `src/crawler/pipe_scraper.py`:
write at the fetch site, return only metadata up the chain.

**Orchestrator flow:**
`load_curated_proxies()` → `build_sitemap_target()` (64 sub-sitemap URLs) →
`run_loop(..., content_handler)` → dedup `<loc>` URLs → write `theblock_article_urls.txt`
→ `logger.finalize()`. CLI: `--concurrency` (default 128).

## What we found

### Solid data

| Metric | Value |
|---|---|
| Sub-sitemaps fetched (target 64) | 59 |
| Gap (pool exhausted before completion) | 5 (`post_type_post` variants: 19, 21, possible others) |
| Unique `<loc>` URLs extracted | 44,041 |
| `/post/` article URLs | 26,003 |
| `/linked/` | 5,456 |
| `/price/` | 7,023 |
| `/article/` | 1,040 |
| `/press-releases/` | 747 |
| other (profiles, tags, data, etc.) | 2,096 |

**Timing (mtime-reconstructed):**
- Bulk phase (files 1–54): **475s = 7.9min**
- Straggler tail (files 55–59, slow-churn retries): +582s
- Total span first→last XML: **1057s = 17.6min**
- Bulk rate: **6.8 sub-sitemaps/min**

All 64 sub-sitemaps entered the first batch simultaneously (concurrency 128 ≥ 64 targets),
so the run was a single drain — not a steady-state multi-batch scenario.

**Output artifact:** `acquire_pipe_output/theblock_article_urls.txt` (44,041 lines, committed).
Raw XMLs gitignored (59 files, 13 MB).

### Where the data is not reliable

**Logger report missing.** Process was killed before `finalize()` — the 5 logging surfaces
(B-per-proxy distribution, fail/success ratio, working-set snapshots, per-proxy event JSONL)
were never written. The proxy economics of this run are unobserved.

**The 5 gap sub-sitemaps** (all `post_type_post`) stalled in the straggler tail for >8 min
with no new files written. Cause unknown without the event log: could be systematic CF-block
on high-volume `/post/` sitemaps, could be coincidental proxy exhaustion after the bulk drain.

## Time extrapolation — NOT a reliable estimate

A naive projection from the bulk rate to the article backfill:

> 26,003 articles / 6.8 fetches/min = ~3,824 min ≈ **64h**

This number is not actionable. Four reasons:

**(a) 6.8/min is cold-start-limited, not steady-state.**
The bulk rate was measured across a single drain of 64 targets with 128 concurrent slots —
all 64 entered the pool simultaneously. The first working proxies were found in 1–3s, but
the remaining targets had to wait for new proxy candidates as early ones burned. With 26k
targets and 128 concurrency, the working set would persist across hundreds of batches; the
per-batch rate after warm-up is meaningfully higher than the cold-start aggregate.

**(b) B-per-proxy and fail/success ratio are unmeasured.**
These are the dominant levers for throughput: B is how many successful fetches one proxy
delivers before burning; fail/success is how many candidates are consumed per success.
Without the logger report, both are unknown for the curated pool on sub-sitemaps, and
completely unknown for article pages.

**(c) The backfill uses a different pool.**
The article backfill design (per the acquire-pipe-design entry) targets the 22k-candidate survey top-13 pool
(not the curated 3477). Pool size, socks4/5 composition, and CF-pass rate are different.

**(d) HTML article pages face heavier CF challenge than XML sitemaps.**
Sitemap XML (`/sitemap_tbco_*.xml`) is a low-sensitivity path — CF likely applies lighter
fingerprinting than to article HTML (`/post/...`). Pass rate per proxy attempt will be
lower, burning the pool faster.

## Decision / next

Run must reach `finalize()` to recover proxy economics. Two options:
1. Let the loop run to natural gap (pool exhausted, no more eligible candidates) — the 5
   gap sitemaps cause the queue to drain via `break` and `finalize()` fires.
2. Add periodic checkpoint to `AcquireLogger` so mid-run data survives a kill.

For the backfill dev-run: use the survey top-13 pool (22k candidates), set concurrency to
128, and let the run complete or gap naturally. The B-per-proxy distribution from that run
is the first reliable throughput signal.
