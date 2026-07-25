# 45 — Proxy job.md: per-60-min-window attempted/successful counts, unified discover + scrape

Evolves the lean "exactly 5 fields" job.md spec — adds proxy-usage visibility the engine
already had the data for but never surfaced. The module shape as of this stage lives in `src/news/engine/proxy_pool/`.

## Motivation

The job.md (`janitor.py`) carried 5 fields, none about proxy usage — even though `logger.record_attempt`
already streams `{proxy_key, ts, url, result}` per fetch. Concrete pain from a prior race regression:
a run with 20478 attempts → 2 successes (0.01%) could NOT be dissected afterward, because no proxy
aggregates were in the report AND `janitor.end_job` unlinks the JSONL. The user wanted: how many proxies
were tried, how many succeeded — per 60-min window, and over BOTH discovery and scrape.

## Decisions

- **Two counts, distinct by `proxy_key`:** **attempted** = distinct proxies attempted; **successful** =
  distinct proxies with a `200 + valid content` fetch. A proxy reused (2-strikes) for N URLs = 1.
- **200 = pass; everything else = failed.** 403 (Cloudflare bot-block), 404/410 (page gone), connection
  errors/timeouts all count as NOT successful. Rationale (user): a 403 means CF recognized the proxy as a
  bot — it did not get the content, so it is not a pass. This maps EXACTLY to the existing logger
  `result` ("ok" only for 200+valid, "fail" for all else) → **no `fetch.py` change needed**. (An earlier
  alternative — count "got through incl. 403" as success, i.e. connectivity vs content — was considered
  and rejected: only content-success counts.)
- **Per 60-min window.** `run_loop` already refreshes the pool every `refresh_interval_s = 3600` (existing
  flow, logs `pool_refresh` events). The report buckets attempts into 60-min windows from `t0` (first
  event) and stacks one row per window. **Distinct is PER WINDOW** — a proxy used in window 0 AND window 1
  counts in both (each window re-fetches the pool = a fresh population); within a window, reuse = 1.
- **Unification — one job spans discover + scrape.** Previously the job/lock/janitor/logger lifecycle lived
  inside `scrape_entries_proxy` (scrape only); theblock's discovery sitemap proxy-fetches (`_fetch_xml`)
  were unlogged. Now the lifecycle is in `pipeline.py:run_pipeline` (proxy_pool branch): one `AcquireLogger`
  is created at job start and passed to BOTH `platform.discover(logger=)` and `scrape_entries_proxy(..., logger)`.
  theblock's `_fetch_xml` calls `record_attempt` per proxy attempt (direct httpx path stays unlogged — not
  a proxy). Browser platforms (CoinDesk) are untouched: `discover()` keeps its no-logger signature, the
  browser branch is byte-for-byte unchanged.
- **"total" is a non-issue.** No predeclared total needed — the report tallies what actually ran
  (1 sitemap-index + N sub-sitemaps + M articles, counted as fetched). `AcquireLogger._total` was dead
  code anyway; passed as 0 at pipeline-level creation.

## Implementation (merged on dev)

Staged: (1) janitor `_compute_window_stats` + stacked table + the pool_size boundary fix (window-index
bucketing with carry-forward, so the on-the-hour refresh serves its own window); (2) lifecycle → pipeline.py
with `try/finally` (empty runs still write a job.md + release the lock; `start_job` before `AcquireLogger`);
(3) thread logger into theblock `_fetch_xml`; (4) DOCS. Verified per stage with synthetic JSONL + import/
signature checks. Live integration test = a real `theblock --timeframe delta` run.

## Open

- Live-verify the per-window table on a real `delta` run (subs 26+25 + their articles) — the first job.md
  that spans discovery + scrape proxy usage.
- The 200=pass definition makes "successful" the CONTENT-success count. For The Block (CF-heavy) most
  proxies will show as not-successful (403) — that is intended; it is the content-success rate, the same
  signal from the earlier race regression. A separate "connected (any HTTP response)" connectivity count was explicitly NOT added.
