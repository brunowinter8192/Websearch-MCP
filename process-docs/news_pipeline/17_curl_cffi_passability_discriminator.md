# 17 — curl_cffi-chrome Passability Discriminator: theblock.co

**Date:** 2026-06-11
**State:** Discriminator complete. Verdict (a): signature was the blocker. curl_cffi-chrome passes CF; 80/425 (18.8%) free DC proxies return 200+XML from a real /post/ sub-sitemap. Free curl_cffi fetch loop is viable for the ~43-sub discovery gap.

---

## Context

The prior monosans pool-evidence session left the 0/17202 result AMBIGUOUS: either (a) rustls TLS signature blocked by CF, or (b) all DC proxy IPs CF-reputation-blocked. This probe discriminates by re-testing with curl_cffi impersonate=chrome — the correct browser TLS/JA3 that monosans' rustls lacked.

**Decision logic recap:**
- Pass count > 0 → (a): signature was the issue; curl_cffi works; free loop viable
- Pass count = 0, failures dominated by 403/429 → (b): IP reputation; curl_cffi can't fix; residential required
- Pass count = 0, failures dominated by connection errors → (c): stale pool; inconclusive

---

## Setup

**Pool:** fresh monosans neutral run (2026-06-11T00:11Z), `check_url = https://ipv4.icanhazip.com`, concurrency 512. Yielded **425 proxies** (http 104, socks4 103, socks5 218), 131s wall-clock. Pool composition: overwhelmingly datacenter ASNs (Global Connectivity Solutions Llp, DigitalOcean, Oracle, Timeweb, Contabo, IONOS, etc.) — this was documented as a prior for (b) in the prior monosans pool-evidence entry. Proxies had been alive for ~1h when discriminator was run.

**Target URL issue (observed, resolved):** Prompt specified "a real /post/ sub-sitemap." First attempt used `sitemap_tbco_post_0.xml` (inferred from `_reconstruct_sub_urls_from_cache()` naming convention). Run 1 returned 87/425 HTTP 404 errors, inconsistent with a CF block (CF returns 403/429, not 404). 404 via SOCKS5 proxy is end-to-end encrypted — theblock.co origin returned 404, meaning URL doesn't exist. Correct URL recovered by bootstrapping: used one of the pool proxies to fetch `sitemap_tbco_index.xml`, parsed `<loc>` entries. Actual post sub URL format: **`sitemap_tbco_post_type_post_N.xml`** (not `sitemap_tbco_post_N.xml`). 64 sub-sitemaps confirmed in index. Bootstrap proxy: `http://217.154.155.115:8080` (IONOS SE, DE) → 200+XML from index on first successful attempt.

**Primary target (discriminator run):** `https://www.theblock.co/sitemap_tbco_post_type_post_0.xml` — oldest /post/ sub, archive back to ~2018, same CF edge that returned 403/429 in the original discovery session.
**Secondary target:** `https://www.theblock.co/sitemap_tbco_index.xml` — tested on passing proxies only for cross-check.

**curl_cffi pattern used:**
```python
s = cffi_requests.Session(impersonate="chrome")  # Chrome JA3/TLS fingerprint; version 0.15.0
r = s.get(target, proxies={"http": purl, "https": purl}, timeout=15)
```
Pass criterion: `status_code == 200` AND content contains `b"<?xml"`, `b"<sitemapindex"`, `b"<urlset"`, or `b"<sitemap>"` within first 500 bytes.

**Concurrency:** `ThreadPoolExecutor(max_workers=20)`, one `Session` per thread. Proxy string: `<protocol>://<host>:<port>`.

---

## Run 1 — Wrong URL (`sitemap_tbco_post_0.xml`)

| result | count | % |
|----|----|----|
| fail_connection | 133 | 31.3% |
| fail_timeout | 104 | 24.5% |
| fail_http_404 | 87 | 20.5% |
| fail_403 | 59 | 13.9% |
| fail_ssl | 42 | 9.9% |

**0 passing.** 87 HTTP 404 responses via SOCKS proxies confirm those proxies reached the CF edge and got a real server 404 — URL doesn't exist. This was the diagnostic for the URL error. 59 HTTP 403s confirm CF IP-reputation filtering is active. Wall-clock: 129s.

---

## Run 2 — Correct URL (`sitemap_tbco_post_type_post_0.xml`)

Pool: 425 proxies. Wall-clock: **126s**.

| result | count | % |
|----|----|----|
| fail_connection | 148 | 34.8% |
| fail_timeout | 100 | 23.5% |
| **pass** | **80** | **18.8%** |
| fail_403 | 66 | 15.5% |
| fail_ssl | 31 | 7.3% |

**PASSING (200 + XML): 80 / 425 (18.8%)**

**Failure mode summary:**
| category | count | interpretation |
|---|---|---|
| CF-block (403) | 66 | CF IP-reputation blocked these DC IPs |
| connection errors (refused/reset/SSL) | 179 | dead proxies |
| timeout | 100 | dead/slow proxies |
| other HTTP | 0 | — |

**Secondary (index, 80 passing proxies):** 53/80 passed (200+XML), 11 timeout, 10 CF-403, 6 connection. Wall-clock: 26s.
The 10 that passed post_0 but got 403 on the index suggest some proxies hit a per-IP rate limit after already having made one successful request. Observed/inferred: these 10 proxies' CF quota was consumed by the post_0 request; the index request seconds later tripped mechanism-2 for that IP.

---

## Verdict: **(a) — Signature was the blocker**

**Observed:** 80/425 proxies returned HTTP 200 + valid XML from a real /post/ sub-sitemap using curl_cffi impersonate=chrome. These are predominantly datacenter ASN proxies (Global Connectivity Solutions, Aeza Group LLC, DigitalOcean, Microsoft, Oracle, Timeweb) — the same DC IP class that monosans' rustls returned 0/17202 on.

**Conclusion (inferred, not speculative):** the shift from 0/17202 (monosans rustls) to 80/425 (curl_cffi-chrome) on the same DC-IP pool class isolates the variable. The only difference is the TLS client fingerprint. curl_cffi-chrome's JA3 passes CF's mechanism-1 signature check; rustls did not.

**Secondary confirmation:** 66/425 (15.5%) got CF-blocked (403) despite using the correct chrome JA3. This shows CF's mechanism-2 IP-reputation filtering IS active — it rejects some DC IPs regardless of TLS fingerprint. The two mechanisms are orthogonal and both real; (a) and partial-(b) co-exist. What (a) means is that the signature check is the NECESSARY precondition: fix the signature, and the subset of DC IPs with acceptable reputation then passes.

**Pool composition note:** the passing proxies span DC providers (Global Connectivity Solutions, Aeza Group LLC, DigitalOcean, Microsoft Azure, Oracle Cloud, Timeweb, IONOS) AND telecom/ISP proxies (Telefonica DE ES, TIM IT, SK Broadband KR, PT Telekomunikasi Indonesia, Iran Telecom, etc.). The telecom IPs represent quasi-residential addresses less likely to be CF-reputation-blocked. Passing ≠ residential-only; a meaningful subset of DC IPs also pass. The prior "all DC → blocked" assumption from the earlier monosans pool-evidence entry is falsified.

---

## Recommendation: Build the curl_cffi Fetch Loop

**Free proxy approach is viable for the discovery gap (~43 missing subs).**

- 80 CF-passing proxies available per fresh pool run (~130s to generate).
- 43 sub-sitemaps needed; each fetch uses one proxy. 80 >> 43 — headroom for failures.
- Per-proxy retry on 403/connection-error: rotate to next proxy, not time-bounded.
- The pool is ephemeral (free proxies turn over within hours), so monosans neutral re-run is the correct refresh strategy before each discovery attempt.

**Next step (not built here):** the production fetch loop:
1. `monosans neutral` run → fresh pool (~130s, neutral check_url, Docker)
2. `curl_cffi impersonate=chrome` + proxy rotation over the ~43 missing subs
3. Per-fetch: retry on 403/429 with next proxy; validate 200+XML per response
4. Resume-safe: existing cache (from probe_discovery.py) means only the missing subs are fetched

**Discovery-stage scope boundary (repeat from the prior entry):** this evidence solves the ~43-sub discovery gap (64 small XML files, ~11MB total, one-off run). The BACKFILL (~27k article pages, GB-scale, ~1300 IP rotations) and the RECURRING 48h pipe are separate problems with different scale constraints. The free pool approach is validated ONLY for the discovery use case.

---

## Probe Artifacts

| File | Role |
|---|---|
| `dev/news_pipeline/theblock/probe_curl_cffi_discriminator.py` | discriminator probe script |
| `dev/news_pipeline/theblock/probe_curl_cffi_discriminator_reports/` | per-run report MDs (gitignored) |
