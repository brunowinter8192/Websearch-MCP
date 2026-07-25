# 18 — Free-Proxy Method Optimization + Forward Plan (toward determinism)

**Date:** 2026-06-11
**State:** Discovery method validated (per the prior two entries: monosans pool evidence + curl_cffi discriminator). This note captures the method-optimization landscape, the determinism framing, the throughput/lever analysis, external (Reddit) research, and the exact forward plan for the next session. No code written here — synthesis + plan only.

---

## Decision Frame (this session, user-set)

- **Paid proxies (residential) are OUT.** Free sources only.
- **"We have time" is necessary but NOT sufficient.** The criterion is **DETERMINISM**, derived from maxed-out methods — not from patience. A non-deterministic grind that "eventually" finishes is not acceptable.
- **Sequence:** max out the free-proxy methods FIRST, then derive the determinism math from measured numbers. No determinism claim before the methods are maxed.

---

## State (after this session)

- **Discovery method validated.** monosans neutral pool (free datacenter proxies) + `curl_cffi impersonate="chrome"` → **80/425 (18.8%)** pass a real `/post/` sub-sitemap (`sitemap_tbco_post_type_post_0.xml`). Verdict **(a)**: the rustls TLS signature was the blocker behind monosans' 0/17202; chrome JA3 fixes it. (Full evidence: the monosans pool-evidence entry established the rustls 0-result; the curl_cffi passability-discriminator entry established the 18.8% pass rate.)
- **Both CF mechanisms confirmed real and orthogonal:** signature-gate (mechanism 1, fixed by curl_cffi) + IP-reputation-gate (mechanism 2 — 66/425 still got 403 WITH correct JA3). Signature is the **necessary precondition**; among signature-correct requests, the acceptable-reputation subset of IPs passes. The earlier prior "all DC IPs → blocked" is **falsified** for theblock.co.
- **Our own home IP still mechanism-2-blocked across sessions (>hours).** Observed: urllib→403 AND curl→403 this session (curl gave 200 on a fresh IP last session). The block is long-lived / cumulative, NOT a short rate-window. Implication: single-IP pacing cannot beat it.
- **`/post/` sub-sitemap URL format (corrected, verified):** `sitemap_tbco_post_type_post_N.xml` (NOT `sitemap_tbco_post_N.xml`). 64 subs in `sitemap_tbco_index.xml`.

---

## Determinism Framing

Determinism = **(a) convergence guarantee + (b) bounded, predictable cycle count.**

- **(a) is already structural:** the fetch loop is **resume-safe** — cache every fetched page, only fetch the still-missing ones. → guaranteed eventual completion, never loses progress. This alone makes the process *converge*.
- **(b) = total_pages / (working_proxies_per_cycle × requests_per_IP_budget).** Two unknowns to MEASURE:
  - `working_proxies_per_cycle` — lever: expand sources (see below).
  - `requests_per_IP_budget` — requests one DC proxy IP tolerates before mechanism-2 trips. Observed hint (from the curl_cffi discriminator run): of 80 passing proxies, 10 got 403 on a 2nd request seconds later; 53 tolerated ≥2. Real budget unknown — must be measured.
  - Plus **yield STABILITY** across cycles (variance matters as much as the mean for determinism).

After A+B measured → discovery determinism is trivial (80 >> 43 subs); backfill determinism is projectable (27k / (yield × budget)).

---

## Lever Map

### monosans (pool generation)
- **Sources — BIGGEST lever.** Currently ~7 default lists. 12+ more public list-repos addable as config URLs (see Source Expansion). More sources → more scraped → more alive → more theblock-passing.
- `max_concurrent_checks` (512) — check throughput.
- `timeout` / `connect_timeout` (10s / 5s) — **dead-proxy timeout dominates avg check-time**; lowering it speeds throughput by discarding junk faster.
- `max_proxies_per_source` (100k, non-limiting). `check_url` (neutral icanhazip — keep; theblock as check_url is dead per the prior monosans pool-evidence entry).

### Our curl_cffi fetch loop (separate from monosans)
- **Concurrency:** discriminator used `ThreadPoolExecutor(max_workers=20)` → SLOW (~3.4 proxies/s). Blocking OS threads, only 20 in-flight.
- **Fix:** more threads (100–300) OR `curl_cffi.AsyncSession` (500+ cheap, like monosans' async). Plus a politeness cap so we don't flood theblock's origin (each request is a different proxy IP, but aggregate matters).

---

## Throughput Analysis (why the two tempi differ)

- **Proxy-checking is I/O-bound, NOT CPU-bound.** The CPU is idle waiting on the network. Rechenleistung is not the wall.
- monosans **130/s @ 512**: async (tokio) — 512 suspended futures, ~KB each.
- our loop **3.4/s @ 20**: blocking OS threads — ~MB each, don't scale to thousands (memory). This is the whole difference: async vs blocking threads, not "Rust is faster."
- **Real ceilings when pushing concurrency toward "all at once" (in order):** file descriptors (`ulimit -n`, often 256/1024 on macOS) → ephemeral ports (~28k usable) → home-router conntrack table → thread-stack memory (threaded model only). **CPU is last, not first.**
- Practical sweet spot: a few hundred to ~1000 concurrent async — far above 20, below the FD/port/router walls. monosans' 512 sits there.
- **Second throughput lever:** lower the per-dead-proxy timeout (most scraped proxies are dead and eat the full timeout).

---

## Source Expansion (the "more proxies" lever)

**Mechanism:** GitHub repos host auto-updated `.txt` proxy lists; raw URL = `raw.githubusercontent.com/<owner>/<repo>/<branch>/<file>.txt`; paste into monosans config under the matching protocol. (monosans' 7 defaults already use this exact pattern.) Minority are HTTP APIs (proxyscrape, geonode).

**Verified this session (structure inspected via gh-cli):**
| Repo | Files | Notes |
|---|---|---|
| `mmpx12/proxy-list` (master) | `http.txt`, `socks4.txt`, `socks5.txt` | clean split, hourly |
| `MuRongPIG/Proxy-Master` | `http.txt` (27.9k), `socks4.txt`, `socks5.txt` | ~83k raw, ~5× current scrape; `http_checked.txt` = small pre-validated variant; branch to confirm |
| `clarketm/proxy-list` (master) | `proxy-list-raw.txt` | mixed protocol → treat as http; daily |

**Candidates NOT yet structure-verified (next session, before dispatch):** `jetkai/proxy-list`, `zloi-user/hideip.me`, `Zaeem20/FREE_PROXIES_LIST`, `ErcinDedeoglu/proxies`, `databay-labs/free-proxy-list`, `monosans/proxy-list` (own pre-checked pool).

**Scale impact:** ~17k → 100k+ scraped → working-proxies/cycle from ~80 toward several hundred. **Trade-off:** 100k @ ~130/s ≈ 13 min check (vs 130s). Mitigate via pre-checked short-lists or lower timeout.

---

## Tool Landscape (other repos / methods)

monosans/proxy-scraper-checker is the strongest scraper/checker (1273★, Rust async, the unique `check_url` lever). Alternatives are weaker: `iw4p/proxy-scraper` (594★), many 5–100★ tools. **Decision: keep monosans, max its sources.** `monosans/proxy-list` = ready pre-checked pool, complementary input.

---

## External Research (Reddit — r/webscraping, r/CloudFlare; indexed to reddit-cli-posts this session)

- CF blocks on **ML IP-reputation**, not pure rate. Datacenter IPs (AWS/Azure) often 403'd immediately. Even SHARED/cheap residential gets caught (CF ML-flags shared IPs) — reported by a user with *paid rotating residential* still hitting the bot page.
- What works at scale: **real residential/mobile + rotation + <3 threads per IP** (one report: 30k Walmart pages, 0.4% drop). BUT paid → out of scope per the decision frame.
- **Key reconciliation:** theblock.co does NOT aggressively reputation-block all DC IPs (our 18.8% pass proves it) — its CF is primarily **signature-gated**. The community's general "DC always blocked" prior is FALSIFIED for our specific target. The empirical test beat the prior — the reason we test rather than trust the community default.

---

## Forward Plan (next session)

### Have
- Validated discovery method: free monosans pool + `curl_cffi impersonate="chrome"`, ~80 working proxies/cycle (~130s/pool).
- Probes (on dev): `probe_discovery.py` (existing discovery), `probe_monosans.sh` (monosans Docker invocation), `probe_curl_cffi_discriminator.py` (passability test).
- Cache: `bulk_sitemap_run3.json` (~19k `/post/` URLs, IDs 136–342,769); ~43 subs missing, of which only the `/post/` ones matter.
- monosans acquisition: Docker (`ghcr.io/monosans/proxy-scraper-checker:f44fdb22...`); binary needs a TTY, fails headless.

### Next worker steps
1. **Opus pre-work:** verify + assemble the FULL additional source raw-URL set (the 3 verified + the 6 candidates), pass exact URLs in the worker prompt (worker does not gh-cli).
2. **Expand monosans sources** → maxed neutral config.
3. **MEASURE A — maxed pool yield + stability:** run the expanded config 2–3 cycles; count theblock-passing proxies/cycle (vs ~80) + variance.
4. **MEASURE B — per-IP request budget:** hammer individual working proxies sequentially against theblock subs until 403/429; count successes before block; distribution over several proxies. (= the backfill determinism number.)
5. **BUILD the discovery fetch loop** (separate, after A/B): fresh pool → curl_cffi-chrome rotation (raised concurrency / AsyncSession) over the ~43 missing subs → per-fetch 200+XML validate, retry-next-proxy on 403/429 → resume from cache. Completes discovery.

### Open for later (NOT this plan)
- **Backfill representativeness:** A/B were measured against SITEMAPS. Article HTML pages may have different/stronger CF protection — re-measure against a real article page before any backfill go/no-go.
- Recurring 48h pipe (smaller volume, same IP-quality question).

### Determinism gate
After A+B: discovery is trivially deterministic (80 >> 43). For backfill, project `27k / (yield × per-IP-budget)` and decide free-go vs reconsider The Block — strictly WITHOUT paid options.

---

## Open Questions

- Per-IP request budget for DC proxies (the single most important number — gates the whole backfill economics).
- Yield stability across cycles (mean ~80 measured once; variance unknown).
- Does the home IP's mechanism-2 block ever clear, and on what timescale? (Affects whether direct-from-our-IP fetch of the few missing subs is ever viable as a fallback.)
