# Iteration 20 — Liveness Check + Concurrency Sweep

## Design

**Script:** `dev/news_pipeline/theblock/probe_liveness.py`  
**Check target:** `http://ipv4.icanhazip.com` (HTTP, simple IP-return, no TLS failure modes)  
**Client:** `curl_cffi.AsyncSession` — native libcurl error codes, enables full reason classification  
**Proxy strings:** `http://`, `socks4://`, `socks5h://` (remote DNS for SOCKS5 — avoids local DNS load)  
**Concurrency:** `asyncio.Semaphore(N)`, one shared `AsyncSession`  
**Timeout:** `(connect_s, read_s)` tuple → `CONNECTTIMEOUT_MS` + `TIMEOUT_MS = (connect+read)*1000` (from curl_cffi `utils.py:set_curl_options`) **+ `asyncio.wait_for(timeout=connect_s+read_s+2)` hard Python deadline around `session.get()`** (fix added after hang bug — see below)

## Bug Found + Fixed During This Iteration

**Symptom:** run hung at 16000/20000 indefinitely. `asyncio.gather` never completed.

**Root cause:** curl_cffi's `timeout=(connect_s, read_s)` is not a hard Python-level deadline. Some proxies accept the TCP connection (connect_timeout doesn't fire) then stall data transfer indefinitely — the read timeout does not reliably cancel the underlying libcurl handle in the async event loop. A handful of such coroutines lock `asyncio.gather` forever.

**Fix (commit `2193b10`):** `asyncio.wait_for(session.get(...), timeout=connect_s+read_s+2.0)` **inside** `check_proxy`, **after** `async with sem`. Applied inside the semaphore so wait_for bounds only the network operation, not the semaphore queue-wait (otherwise semaphore latency at high concurrency would produce spurious `hard_timeout` results). New bucket `hard_timeout` added to `DEAD_BUCKETS` — it is diagnostically significant (see results).

## System Limits

FD soft: 1,048,576 / hard: unlimited. Ephemeral ports: 49152–65535 (16,384). 14 cores (I/O-bound — irrelevant). Real ceiling: home-router NAT/conntrack (external, unmeasurable) — the sweep finds it empirically. **Sweep confirmed: router floor is around concurrency=512** (see results below).

## Frozen Pool

Re-frozen 2026-06-11 (same day as predecessor). Fetched from the same 68 sources as the prior source-expansion entry. Written to `frozen_pool/` (gitignored, regenerated on demand):

| Bucket | Unique entries |
|---|---|
| http | 113,223 |
| socks4 | 94,458 |
| socks5 | 112,653 |
| **total** | **320,334** |

Fixed sample: `random.Random(42).sample(all_entries, 20_000)` — deterministic across all sweep runs.

## Dead Reason Classification

| Bucket | Exception / Code | Discriminator |
|---|---|---|
| `connect_timeout` | `Timeout` | elapsed ≤ connect_s + 0.5 → elapsed-primary; fallback: "Connection timed out" in msg |
| `read_timeout` | `Timeout` | elapsed ≥ total_s - 0.5 → elapsed-primary; fallback: "Operation timed out" in msg |
| `hard_timeout` | `asyncio.TimeoutError` | Python-level `wait_for` fired — curl did NOT timeout; proxy held connection open past deadline |
| `connect_timeout`/`read_timeout` → `unknown` | `Timeout` | neither elapsed nor text matched (libcurl version drift signal) |
| `resolve_error` | `CurlECode.COULDNT_RESOLVE_PROXY/HOST` (5, 6) | proxy hostname unresolvable |
| `proxy_handshake_error` | `ProxyError` / `GOT_NOTHING` (52) / `WEIRD_SERVER_REPLY` (8) | SOCKS/CONNECT negotiation failure; protocol-mislabelled proxies land here |
| `connection_refused` | `CurlConnectionError` (code 7) | TCP to proxy refused / unreachable |
| `tls_error` | `SSLError` (codes 35, 58–60, 80–83, …) | TLS handshake failure |
| `http_non200` | HTTP resp ≠ 200 | proxy returned error page |
| `bad_body` | HTTP 200, body not IPv4 | proxy returned garbage or modified response |
| `unknown` | anything else | logged to `probe_liveness_logs/unknown_errors_<UTC>.log` |

## Sweep Results

20k fixed sample, timeout=5s/5s, seed=42. All 4 levels completed 2026-06-11.

| Concurrency | Wall-clock | Throughput | Alive | Alive% | hard_timeout% | Notes |
|---|---|---|---|---|---|---|
| 512 | 456.9s | 44/s | 781 | 3.9% | 84.3% | Best alive rate |
| 1000 | 240.1s | 83/s | 303 | 1.5% | 93.7% | Alive drops 61% vs 512 |
| 2000 | 120.1s | 166/s | 125 | 0.6% | 97.4% | Alive drops 85% vs 512 |
| 3000 | 84.1s | 238/s | 60 | 0.3% | 98.3% | Alive drops 92% vs 512 |

### Dead Reason Histograms

**concurrency=512** (n=20,000 | elapsed=456.9s | throughput=44/s | alive=781/3.9%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 357 | 1.9% |
| read_timeout | 16 | 0.1% |
| hard_timeout | 16,198 | 84.3% |
| connection_refused | 812 | 4.2% |
| proxy_handshake_error | 1,761 | 9.2% |
| http_non200 | 69 | 0.4% |
| bad_body | 2 | 0.0% |
| unknown | 4 | 0.0% |

**concurrency=1000** (n=20,000 | elapsed=240.1s | throughput=83/s | alive=303/1.5%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 174 | 0.9% |
| read_timeout | 23 | 0.1% |
| hard_timeout | 18,451 | 93.7% |
| connection_refused | 344 | 1.7% |
| proxy_handshake_error | 674 | 3.4% |
| http_non200 | 29 | 0.1% |
| unknown | 2 | 0.0% |

**concurrency=2000** (n=20,000 | elapsed=120.1s | throughput=166/s | alive=125/0.6%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 86 | 0.4% |
| read_timeout | 18 | 0.1% |
| hard_timeout | 19,349 | 97.4% |
| connection_refused | 153 | 0.8% |
| proxy_handshake_error | 261 | 1.3% |
| http_non200 | 7 | 0.0% |
| unknown | 1 | 0.0% |

**concurrency=3000** (n=20,000 | elapsed=84.1s | throughput=238/s | alive=60/0.3%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 56 | 0.3% |
| read_timeout | 17 | 0.1% |
| hard_timeout | 19,601 | 98.3% |
| connection_refused | 94 | 0.5% |
| proxy_handshake_error | 158 | 0.8% |
| http_non200 | 12 | 0.1% |
| bad_body | 1 | 0.0% |
| unknown | 1 | 0.0% |

## Analysis

**Throughput scales cleanly** (~linear with concurrency: 44→83→166→238/s). The router does not drop throughput. Wall-clock scales inversely as expected: dominated by hard_timeout count × 12s / concurrency (at 512: ~16k×12/512≈380s, actual 457s; at 3000: ~19.6k×12/3000≈78s, actual 84s — model fits within 20%).

**Alive rate collapses monotonically** with concurrency: 3.9% → 1.5% → 0.6% → 0.3%. This is not a calibration artifact — it is home-router NAT/conntrack saturation misclassifying live proxies as `hard_timeout`. At high concurrency, proxies that would respond within 12s at 512 slots simply do not get answered because the router's conntrack table (or its NAT throughput) is the bottleneck. Each additional live proxy connection competes with thousands of half-open timeout-waiting connections; many live ones time out at the Python level before the router forwards their response.

**hard_timeout balloon is the signal:** 84.3%→93.7%→97.4%→98.3%. At 3000, virtually every dead proxy hits the Python `wait_for` rather than curl's own timeouts. This means curl's `connect_timeout` and `read_timeout` become nearly irrelevant at high concurrency — the router never completes the TCP handshake for most connections, so they all pile into the 12s bucket.

**connect_timeout and connection_refused also decline** at higher concurrency (357→174→86→56 and 812→344→153→94 respectively). These fast-failing proxies should always fail quickly regardless of concurrency. The decline is explained by the router dropping connection_refused packets or absorbing them into conntrack noise — even fast failures get delayed by NAT pressure.

**Proxy dead-mix shift** is unambiguous: the dominant class at all concurrencies is `hard_timeout`. At 512, `proxy_handshake_error` is still visible (9.2%) — SOCKS proxies that connect but fail at the protocol level. At 3000, even these collapse (0.8%) as the router swamps them into `hard_timeout`. The true failure taxonomy is `hard_timeout >> proxy_handshake_error > connection_refused > connect_timeout >> everything else`.

**No resolve_error or tls_error** at any level — expected: `icanhazip.com` is HTTP-only (no TLS), and proxy hostnames are IPs (no DNS resolution required).

**Wall-clock for full 320k run at 512:** ~84% hard_timeout × 320,334 = ~269k hits × 12s / 512 ≈ 6,300s ≈ 1.75 hours. Budget accordingly.

## Concurrency Recommendation (Upward Sweep Only — superseded below)

~~**512 for the full 118k/320k run.**~~

This recommendation was based only on the upward sweep (512–3000). The downward sweep below shows 512 is still in the router-saturated zone. See revised recommendation at end.

---

## Downward Sweep (2026-06-11, same session)

Sample=3000, seed=42, timeout=5s/5s. Two bookend runs at concurrency=512 bracket the sweep to measure pool churn over the ~30 min window.

### Results

| Concurrency | Wall-clock | Throughput | Alive | Alive% | hard_timeout% |
|---|---|---|---|---|---|
| 512 (start) | 72.0s | 42/s | 51 | 1.7% | 92.6% |
| 256 | 137.1s | 22/s | 120 | 4.0% | 77.5% |
| 128 | 265.3s | 11/s | 236 | 7.9% | 60.0% |
| 64 | 493.7s | 6/s | 280 | 9.3% | 51.4% |
| 512 (end) | 72.0s | 42/s | 51 | 1.7% | 92.3% |

### Dead Reason Histograms (downward sweep)

**concurrency=512 start-bookend** (n=3,000 | elapsed=72.0s | alive=51/1.7%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 37 | 1.3% |
| read_timeout | 18 | 0.6% |
| hard_timeout | 2,731 | 92.6% |
| connection_refused | 39 | 1.3% |
| proxy_handshake_error | 111 | 3.8% |
| http_non200 | 12 | 0.4% |
| unknown | 1 | 0.0% |

**concurrency=256** (n=3,000 | elapsed=137.1s | alive=120/4.0%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 85 | 3.0% |
| read_timeout | 23 | 0.8% |
| hard_timeout | 2,233 | 77.5% |
| connection_refused | 166 | 5.8% |
| proxy_handshake_error | 349 | 12.1% |
| http_non200 | 22 | 0.8% |
| bad_body | 1 | 0.0% |
| unknown | 1 | 0.0% |

**concurrency=128** (n=3,000 | elapsed=265.3s | alive=236/7.9%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 75 | 2.7% |
| read_timeout | 49 | 1.8% |
| hard_timeout | 1,658 | 60.0% |
| connection_refused | 327 | 11.8% |
| proxy_handshake_error | 610 | 22.1% |
| http_non200 | 40 | 1.4% |
| bad_body | 2 | 0.1% |
| unknown | 3 | 0.1% |

**concurrency=64** (n=3,000 | elapsed=493.7s | alive=280/9.3%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 38 | 1.4% |
| read_timeout | 162 | 6.0% |
| hard_timeout | 1,399 | 51.4% |
| connection_refused | 367 | 13.5% |
| proxy_handshake_error | 693 | 25.5% |
| http_non200 | 54 | 2.0% |
| bad_body | 3 | 0.1% |
| unknown | 4 | 0.1% |

**concurrency=512 end-bookend** (n=3,000 | elapsed=72.0s | alive=51/1.7%)

| Reason | Count | % of dead |
|---|---|---|
| connect_timeout | 43 | 1.5% |
| read_timeout | 13 | 0.4% |
| hard_timeout | 2,721 | 92.3% |
| connection_refused | 44 | 1.5% |
| proxy_handshake_error | 116 | 3.9% |
| http_non200 | 12 | 0.4% |

### Churn Assessment

Start-bookend: 51 alive. End-bookend: 51 alive. Count identical; elapsed ~30 min between them. **Pool churn over the measurement window is effectively zero.** The proxy pool is stable at the minute-to-hour timescale, so sweep results are directly comparable and a single full run will not be invalidated by pool decay during the run.

### Analysis

**Alive rate climbs monotonically as concurrency drops:** 1.7% → 4.0% → 7.9% → 9.3%. Improvement ratios per halving: 2.4× (512→256), 2.0× (256→128), 1.2× (128→64). The gain is clearly bending at 128→64 — the curve is entering plateau territory.

**512 was deep in the saturated zone.** The upward sweep (previous section) showed 3.9% at 512 on the 20k sample. The downward sweep shows 1.7% at 512 on the 3k sample. These are different seeds' subsets of the same pool, so the absolute numbers aren't directly comparable — but both confirm 512 is well above the router's NAT ceiling. The 512 upward-sweep alive rate of 3.9% was itself suppressed; it was not a clean measurement.

**hard_timeout% as NAT-saturation signal:** 92.6% at 512 → 77.5% at 256 → 60.0% at 128 → 51.4% at 64. At 64, over half of dead proxies still hit the Python `wait_for` (not curl's own timeouts). True plateau — where hard_timeout% stabilises and `connection_refused`/`proxy_handshake_error` dominate — is likely below 64, probably around 32–48.

**Taxonomy shift confirms real failures emerging:** At 512, `proxy_handshake_error` is suppressed to 3.8% (the router drops most connections before SOCKS negotiation even starts). At 64, `proxy_handshake_error` rises to 25.5% and `connection_refused` to 13.5% — these are genuine proxy-quality failures, not router artifacts. The dead-reason mix at 64 is substantially more truthful than at 512.

**read_timeout at 64 jumps to 6.0%** (vs <1% at all higher concurrencies). At 64, curl's own 5s read timeout fires for some proxies that connect and start responding but are slow — a class completely masked by the 12s `hard_timeout` at higher concurrency. This further confirms 64 is closer to the "real" failure taxonomy.

**Wall-clock projection for full 320,334-proxy run** (scaling from 3k sample):

| Concurrency | 3k wall-clock | 320k estimate | Expected alive (×320k) |
|---|---|---|---|
| 128 | 265s | ~28,300s (~7.9 h) | ~25,300 |
| 64 | 494s | ~52,700s (~14.6 h) | ~29,800 |

The marginal gain from 128→64 is +4,500 alive proxies (~18% more) at the cost of +6.7 extra hours (+85% wall-clock). Whether that trade is worth it depends on how many alive proxies the pipeline needs downstream.

### Revised Concurrency Recommendation

**128** for the full run, as the practical operating point. The curve bends sharply between 128 and 64 (1.2× gain vs. 2.0× gain per previous step), and 128's taxonomy already shows healthy `proxy_handshake_error` and `connection_refused` fractions — the router is no longer the dominant bottleneck. Expected yield: ~7.9% × 320k ≈ 25,300 alive proxies in ~8 hours.

**64** is the maximum-fidelity alternative — gets closest to the true plateau (~9.3%, ~29,800 alive from 320k) but at ~15 hours. Viable for a one-time pool build if completeness matters more than time.

**Do NOT use 512** for the full run. It is demonstrably in the saturated zone: only 1.7% alive on the 3k sample vs. 9.3% at 64 — the router false-negatives swamp the true signal by ~5.5×.

## Raw Data Locations

- `dev/news_pipeline/theblock/probe_liveness_logs/sweep_log.md` — all 9 structured entries (4 upward + 5 downward)
- `/tmp/sweep_512.txt`, `/tmp/sweep_1000.txt`, `/tmp/sweep_2000.txt`, `/tmp/sweep_3000.txt` — upward sweep stdout (local)
- `/tmp/sweep_dn_512a.txt`, `/tmp/sweep_dn_256.txt`, `/tmp/sweep_dn_128.txt`, `/tmp/sweep_dn_64.txt`, `/tmp/sweep_dn_512b.txt` — downward sweep stdout (local)
