# 76 — CoinDesk riding: acceleration levers + success-load-time instrumentation

Process record of the throughput analysis on the `proxy_riding` backfill engine and the instrumentation built to drive timeout/concurrency tuning. Backfill state at analysis time: 12,564 / 61,628 raw HTMLs (~20%); per-year remaining computed via `url_hash(url)=sha256[:12]` vs `data/news/coindesk/raw/*.html` (2025 + 2026 fully untouched).

## Diagnostic finding — the engine is I/O-bound

From job `20260620T163141Z` (442 OK, 5 browsers × 16 ctx = 80 slots, fixed cooldown):

| Signal | Value | Reading |
|---|---|---|
| OK | 442 | productive fetches |
| Connect-fail fetches | 9728 | ~96% of fetches hit dead proxies |
| Ride length | mean 1.1 | each proxy does ~1 attempt then burns |
| Mean s/fetch (OK+rw+failed) | 8.31s | dominated by `page_timeout=8000ms` |
| Wall | 1442s | |

Estimate: 9728 dead-proxy attempts × ~8s ≈ 78k slot-seconds vs 80×1442 ≈ 115k available → **~2/3 of slot-time spent waiting on dead proxies**. Slots block on `await crawler.arun` (network wait), not compute. This is why CPU sat ~43% and GPU idle during runs — idle compute is a *symptom* of I/O-bound, not spare acceleration headroom.

## Levers evaluated

| Lever | Verdict | Reason |
|---|---|---|
| Pre-flight proxy liveness check | **REJECTED** | The fetch at the target is the only valid liveness test. A separate pre-check is either as expensive as scraping or inaccurate (weaker test → discards good / keeps dead). No public scraper does this. |
| Lower `page_timeout` | **valid, data-gated** | Dominant cost per dead proxy. But where to set it = needs the SUCCESS load-time distribution (set just above p95/p99 so live-but-slow proxies aren't cut). Built instrumentation (below) before tuning. |
| More slots / browsers | **biggest immediate lever** | I/O-bound with idle compute → can pack many more concurrent waits before CPU saturates. Ceiling = RAM (Chromium ctx ~50–100MB each) + Playwright stability, NOT CPU. Scale 80 → 128 → measure. |
| GPU offload | **won't help** | No compute bottleneck to move. Rendering is the small fraction (~442 real page loads); time goes to network wait (~10k proxy attempts). Idle GPU = I/O-bound symptom. |
| Better/more proxy sources | **at free-proxy limit** | ~4% live is the free reality (~32.7k pool, 18 sources, 0 fail). Step-change = paid residential/datacenter proxies (~95% live, collapses the 9728 connect-fails) — a cost decision, not a code lever. |

## Instrumentation built (this session)

Goal: measure the SUCCESS load-time distribution — serves BOTH the timeout floor AND the concurrency-scaling test (does the distribution shift right at higher slot counts = local contention).

- `rider.py`: `JobRecord.load_s` — populated OK-only as `max(0, elapsed_s − DELAY_BEFORE_HTML)` (0.5s). crawl4ai's `CrawlResult` (models.py) exposes **no** navigation/domcontentloaded timing at the direct `arun()` return (timing submodels are dispatcher-layer; `dispatch_result` unreliable without the dispatcher) → fallback approximation. Residual ≈ constant context-setup overhead → curve shifts right by a near-constant → timeout reading slightly conservative (safe direction).
- `reporter.py`: job.md section "Success load-time distribution" — percentiles p50/p90/p95/p99/max (n) + `success_load_hist.png` histogram, x-axis fixed `[0, page_timeout_s]` for cross-run comparability, 0.25s bins. Guard: <2 OK samples → note, no plot, no crash (reporter also runs on stall/abort).
- **`statistics.quantiles` method = `inclusive`** (not the default `exclusive`): exclusive extrapolates beyond the sample (`k/(n+1)`) → on small n, p99 > observed max, misleading for "set timeout above observed tail". inclusive interpolates within `[min,max]`. On large n the two converge; the divergence only bites on small/stall runs.

## Experiment design (pending data)

Run the 10k backfill once at `--slots 80` and once at `--slots 120` (`--from 2025-01-01 --to 2026-12-31 --limit 10000`, both years untouched so limit-before-dedup yields 10k new). Compare the two `success_load_hist.png` + percentile tables:
- distribution unchanged → not locally bound → scale slots up freely.
- distribution shifts right → local contention ceiling found → throughput optimum below that.
Caveat: live-proxy set varies between runs; thousands of OK per run averages it out.

## Empirical: first instrumented run (120 slots, 8 browsers, job 20260624T204129Z)

868 target, 777 OK, **24,238 connect-fails**, fixed cooldown, SIGINT-interrupted. Findings:

- **Concurrency is NOT the throughput lever.** 120 slots → 16.6 OK/min vs the earlier 80-slot ~18.4 OK/min — 120 is *slightly worse*. The live-proxy set is a fixed scarce subset of the pool; more contexts pull+burn it faster, they do not create more live proxies. Raising contexts just front-loads then starves. Supply-via-concurrency refuted.
- **Pool exhaustion is the cooldown ceiling, not a bug.** "Eligible pool over time": min-eligible 17.6k → 0 over 50 min, in-cooldown → 24k. At 120 slots with ~1-attempt rides + 60-min `fixed` cooldown, burn-rate drains the eligible pool faster than cooldowns expire → slots exit ("pool exhausted"). 120 is unsustainable under fixed-60min. → `exp` cooldown (re-admits productive proxies) is the supply-side lever, same as the cooldown-policy rethink from an earlier session.
- **Pool loaded = 20,831 is browser-eligible only.** `_pool_provider` filters to `BROWSER_ELIGIBLE_PROTOS = {http, socks5}`; the ~32.7k full pool includes ~12k socks4 that Chromium/Playwright cannot use. Not a bug — the riding engine runs on ~64% of the pool. (socks4 usable only by curl_cffi / TheBlock.)
- **CPU at limit at 120** (user-observed) — consistent with CPU-bound post-nav processing (markdown gen), see below. Going down from 120, not up.

## Instrumentation evolution (this session)

Built incrementally on the riding reporter (`src/news/engine/proxy_riding/reporter.py` + `rider.py`):
1. **Success load-time distribution** — `load_s = max(0, elapsed − DELAY_BEFORE_HTML)`, OK-only; inclusive-quantile percentiles + histogram. **Caveat discovered:** `load_s` is NOT navigation time — it lumps nav (#4, the only phase `page_timeout` bounds) with markdown generation (#7, CPU-bound) + context setup. p50=8.7s / p99=14.6s on the 120 run while `page_timeout`=8s proves a large non-nav component. So `load_s` cannot cleanly tune `page_timeout`.
2. **Histogram auto-range fix** — x-axis was hard-clipped to `[0, page_timeout_s]`, hiding the >8s bulk; now auto-ranges to data with a `page_timeout` reference line.
3. **Connect-fail breakdown** — `connect_fail`s previously discarded their timing (`break` before `job_records.append`). Now collected as `(elapsed_s, subtype)` in `state.connect_fail_records`; reporter emits elapsed-percentiles + histogram + subtype counts. Classifier `_classify_connect_fail`: `"ms exceeded"` → `page_timeout` (Playwright nav cap; crawl4ai wraps as RuntimeError), `"net::err_timed_out"` → `net_timed_out` (TCP), `err_proxy|err_tunnel|socks` → `proxy_connect`, else `other`. Discriminator note: `"timeout"` alone is ambiguous (both nav-cap and TCP contain it) — `"ms exceeded"` is the unique Playwright-nav-cap signature.

**Why connect-fail breakdown matters for the timeout question:** live proxies that get cut at the 8s cap are currently INVISIBLE — a nav-timeout errors with "Timeout 8000ms exceeded" → classified `connect_fail`. The `page_timeout` subtype is the addressable population for "lives cut at 8s" (a mix of dead-no-response + live-slow; the error string can't separate them — a timeout A/B disambiguates). The connect-fail elapsed histogram shows whether dead proxies hang to ~8s (→ lowering frees slots) or fail fast (→ lowering doesn't help cycling).

## crawl4ai arun phase structure + the connect-fail tail (corrected)

`page_timeout` bounds ONLY `page.goto` (`async_crawler_strategy.py:762-763`, `timeout=config.page_timeout`). Later arun phases are NOT bounded by it — notably a hardcoded `wait_for_selector("body", state="attached", timeout=30000)` at `:812`.

**Retraction:** I initially attributed the connect-fail tail (12-18s) to that 30s body-wait. That is wrong for our config — with `wait_until="domcontentloaded"` the `<body>` attaches at parse, so the body-wait passes ~instantly for a normal page. And with our config there is little post-goto proxy work (0.5s local delay + local markdown), so "fail after a successful goto" is rare — a successful goto already holds the initial document.

**Revised tail hypothesis (UNVERIFIED):** the 12-18s connect-fails are the SAME goto-timeouts, wall-clock STRETCHED by event-loop contention. `DefaultMarkdownGenerator` is sync CPU work that blocks the single asyncio loop; while one coroutine grinds markdown, others (incl. one whose 8s goto-timeout just fired) cannot resume to snapshot `elapsed` → an 8s goto is *measured* as 12-18s. So cap-cluster + tail are largely ONE population (goto-timeouts), smeared right by contention → lowering `page_timeout` shrinks BOTH (better than the earlier "tail won't move" claim). Confirm via per-phase timing (goto vs rest) — a dev probe. Minor edge: malformed HTML where `<body>` never attaches → the 30s body-wait fires.

**Discriminator refinement:** read the timeout A/B off the **histogram cap-cluster peak** (it isolates goto-timeouts at the cap), not the raw `page_timeout` subtype count.

## Open

- **`page_timeout` raise-vs-lower** — pending an instrumented 1000-on-80 run: read the connect-fail breakdown (page_timeout subtype share + whether cf-elapsed piles at 8s) + success distribution. Big page_timeout bucket → lives may be cut → A/B a higher timeout; near-zero + dead proxies hanging to 8s → lower.
- **Cooldown policy** — `fixed` exhausts the pool at high concurrency; `exp` is the supply-side lever (separate from timeout). Pending its own run.
- **Navigation vs markdown split** — `load_s` conflates them; a clean `page_timeout` tune would need nav (#4) isolated from markdown (#7), which crawl4ai does not expose at the `arun` return (would require a two-phase dev probe).

## Empirical: instrumented 1000-on-80 run (job 20260624T223839Z) — timeout question RESOLVED: leans LOWER

1000 target / **1000 OK (all-done)**, 80 slots / 5 browsers, fixed cooldown, 19.4 OK/min, 19,155 connect-fails, pool 21,731.

**Connect-fail breakdown** — p50 8.65s, p90 11.1s, p99 13.3s, max 18.4s. Subtypes: **page_timeout 10,847 (56.6%)**, proxy_connect 6,001 (31.3%), other 2,307 (12.0%). Bimodal: a fast cluster (proxy_connect+other ≈43%, <2-3s) and a slow cluster (page_timeout 56.6%, ~8.5s = 8s cap + overhead).

**Success load-time** — p50 7.08s, p95 11.07s, max 16.07s (load_s, markdown-polluted).

**Plot shapes (the visual proof of LOWER):**
- connect_fail_hist: bimodal, sharp gap AT the 8s line. Left = fast fails (0.5–6s, peak ~1.5–2.5s, declining to ~0 by 6s); near-empty 6–8s dead zone; right = a massive cap-spike at ~8.5–9s (tallest bar ~2850) tailing to 14s (= 8s cap + overhead). The cap bites the FAILURES hard; ~half of 19k fails are this cap-cluster.
- success_load_hist: a smooth right-skewed bell (centre ~5–7s, span 2–16s) that flows THROUGH the 8s line with NO cliff/pile-up — successes are not censored at the cap; the >8s mass is markdown on a sub-8s nav. Lives navigate comfortably under 8s.
- ∴ lowering to **~6s** (first A/B point, not 5s) converts the whole cap-cluster (8.5→~6.5s) while leaving the natural fast-fails (done by 6s) and most successes untouched.

**Interpretation → LOWER, not raise:**
- The 56.6% page_timeouts hanging to ~8.5s are the dominant time sink (~10.8k × 8.5s ≈ 92k slot-seconds). 
- They are NOT lost content: all 1000 URLs eventually succeeded on other proxies (1000/1000 all-done; ~19 failed attempts per URL). So page_timeouts = dead/slow PROXIES hanging to the cap, per-proxy not per-URL. The "raise (lives cut at 8s)" scenario is refuted.
- Successes' high `load_s` (7.08 median) is NOT a near-8s-nav signal: a full success (nav + markdown) totals ~7.6s elapsed while a failing proxy burns 8.5s on nav ALONE → successful navigation is fast (markdown eats a big chunk of the 7.6s). Successes are not bumping the 8s nav cap.
- ∴ lowering `page_timeout` fails dead/slow proxies faster (saves ~3s on 56.6% of attempts) with little success loss (nav is fast) and zero content loss (URLs succeed elsewhere).

**Caveats / interactions:**
- Exact safe floor needs the nav-vs-markdown split (load_s can't isolate). The ~7.6s success-total vs ~8.5s fail-nav hints nav ≈ 4-5s → ~5s timeout likely safe — but set it via A/B, not inference.
- Lower timeout → more attempts/min → faster proxy burn → faster pool drain. At 80@8s the pool drained 16.8k→4k over 60 min but did not exhaust; lowering pushes toward exhaustion → pairs with `exp` cooldown (see the cooldown-policy process doc) for re-supply. Timeout-down + cooldown-exp are complementary.
- `page_timeout` is NOT exposed in the prod CLI (`python -m src.news` has only --browsers/--slots/--cooldown-policy) — a `--page-timeout` flag is needed to A/B it.

## Open (updated)

- **Timeout A/B** — add `--page-timeout` flag; run 1000@5s vs 8s baseline on fresh untouched years; compare OK count (successes kept?), OK/min (faster?), connect-fail breakdown (page_timeout cluster shrinks to ~5s?).
- **Cooldown `exp`** — complementary supply lever; run its own A/B (pairs with lower timeout to offset faster burn).
- 80 slots remains the throughput sweet spot so far (19.4 OK/min > 120's 16.6); concurrency is not the lever (supply-bound).
