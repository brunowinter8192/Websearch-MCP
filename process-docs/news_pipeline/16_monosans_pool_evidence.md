# 16 — monosans/proxy-scraper-checker Pool Evidence for theblock.co

**Date:** 2026-06-11
**State:** Empirical probe complete. Recommendation: neutral check_url only; theblock.co check_url is unusable. Discovery-stage proxy approach requires residential IPs, not addressed here.

---

## 1. Acquisition

**Binary path (nightly.link `aarch64-apple-darwin`) → BLOCKED by TTY requirement.**
Artifact `proxy-scraper-checker-binary-aarch64-apple-darwin.zip` (4.2 MB) downloads and extracts to a working arm64 Mach-O binary. At runtime, `src/main.rs:291` throws `Device not configured (os error 6)` — the TUI build opens `/dev/tty` directly; headless (redirected stdout/stderr) invocation fails immediately. No workaround without a Rust toolchain recompile.

**Docker path (nightly.link `arm64-v8`) → WORKS.**
Artifact `proxy-scraper-checker-docker-arm64-v8.zip` (3.4 KB) contains `compose.yaml` + `Dockerfile` (FROM ghcr.io base + UID/GID usermod). Base image: `ghcr.io/monosans/proxy-scraper-checker:f44fdb22c56e544eedf5784b2c5501fe9b3e466b`. Build via compose fails (Docker Hub auth TLS error on `docker.io/docker/dockerfile:1` parser directive). Direct pull of the ghcr.io base image succeeds. Invocation:

```bash
docker run --rm \
  -v /path/to/config.toml:/app/config.toml:ro \
  -v /path/to/out:/app/out \
  -v proxy_scraper_checker_cache:/home/app/.cache/proxy_scraper_checker \
  ghcr.io/monosans/proxy-scraper-checker:f44fdb22c56e544eedf5784b2c5501fe9b3e466b
```

Docker version logs to stdout (no TUI) — suitable for headless runs.

**Config schema note:** default config.toml ships inside the binary zip. Required sections: `[output]`, `[output.txt]`, `[output.json]`, `[checking]`, `[scraping]`, `[scraping.http]`, `[scraping.socks4]`, `[scraping.socks5]`. No `[settings]` block exists. The parser requires all sections — configs MUST derive from the bundled default, overriding only `check_url`, `max_concurrent_checks`, and `output.path`.

Config files committed: `dev/news_pipeline/theblock/monosans_cfg_neutral.toml`, `monosans_cfg_theblock.toml`. Probe wrapper: `dev/news_pipeline/theblock/probe_monosans.sh`.

---

## 2. Signature Micro-Test

**Goal:** verify the mechanism-1 (client-signature) and mechanism-2 (IP-level block) observations from the prior CF-block investigation still hold from our IP this session.

**Test:** 2 requests to `https://www.theblock.co/sitemap_tbco_news.xml` from our host IP.

| Client | Status |
|---|---|
| `urllib` (Python default) | **403** |
| `curl` 8.7.1 | **403** |

**The prior investigation established:** curl→200 on a fresh IP (mechanism 1 passes curl; mechanism 1 blocks urllib). Current result curl→403 is INCONSISTENT with a fresh-IP baseline — this means our IP is currently in the mechanism-2 blocked state from the previous discovery session. Mechanism-2 block persists across sessions (confirmed >hours, previously unquantified). Mechanism-1 distinction (urllib vs curl) remains the established reference from that prior session; it cannot be re-isolated while mechanism-2 is active.

**Rustls signature micro-test:** no Rust toolchain present → standalone reqwest/rustls probe not buildable. See §4 for inference path.

---

## 3. Pool Yield — Neutral `check_url` (Deliverable 3)

**Config:** `check_url = "https://ipv4.icanhazip.com"`, `max_concurrent_checks = 512`. Sources: default (proxyscrape API + TheSpeedX, proxifly, roosterkid, sunny9577, hookzof GitHub lists; http/socks4/socks5).

**Run:** 2026-06-10T23:28:07Z → 23:30:47Z, wall-clock **160s**.

| Metric | Value |
|---|---|
| Proxies scraped | 17,202 |
| Proxies passing | **494** |
| Pass rate | 2.87% |
| http | 123 |
| socks4 | 95 |
| socks5 | 276 |

Confirms these sources yield a live pool: 494 proxies can connect to the internet and return a plain-IP response within 10s.

---

## 4. Pool Yield — TheBlock `check_url` (Deliverable 4)

**Config:** `check_url = "https://www.theblock.co/sitemap_tbco_news.xml"`, `max_concurrent_checks = 50`. Same sources.

**Run:** 2026-06-10T23:31:27Z → 23:51:38Z, wall-clock **1211s** (~20 min; expected at 10× lower concurrency).

| Metric | Value |
|---|---|
| Proxies scraped | 17,202 |
| Proxies passing | **0** |
| Pass rate | 0% |

`proxies.json` = `[]`. No proxy of any protocol (http/socks4/socks5) from these free sources returns HTTP 2xx from the theblock.co sitemap.

**Signal analysis — the 0 result is AMBIGUOUS. Two candidate causes, cannot be isolated without a rustls probe from a clean IP:**

1. **Rustls TLS fingerprint blocked (mechanism 1 applied to all IPs via proxy):** theblock.co performs a client-signature check. monosans uses rustls with aws_lc_rs, ALPN `http/1.1`, Chrome UA header. For HTTPS via proxy, the TLS is end-to-end (CONNECT tunnel); theblock.co sees the rustls JA3, not a browser JA3. If the check operates on JA3/TLS fingerprint, rustls would fail it even with a clean proxy IP — and every proxy check would return 403, dropping all 17,202. This would produce exactly the observed 0-passing result.

2. **All datacenter/VPS proxy IPs reputation-blocked (mechanism 2 extended to proxy pool):** theblock.co CF may block known datacenter ASN ranges at the IP level, regardless of TLS fingerprint. Free proxy pools (proxyscrape, TheSpeedX et al.) are overwhelmingly datacenter-hosted IPs (Vultr, Linode, DigitalOcean, OVH, Hetzner ASNs). CF's bot-management has extensive IP reputation data. All 17,202 proxies being on blocked ASNs would also produce 0-passing.

3. **Both simultaneously:** the two mechanisms are orthogonal and could both be active.

**What would isolate the causes:** a standalone rustls reqwest probe (matching monosans' exact TLS stack) making a single request to theblock.co FROM OUR OWN IP (when not mechanism-2-blocked) would tell us if mechanism 1 applies to rustls. Currently not runnable — no Rust toolchain, and our IP is mechanism-2-blocked.

**Practical implication for the check_url strategy:** regardless of which cause dominates, the conclusion is the same — `check_url = theblock.co sitemap` yields an empty pool from these free sources. It is not a useful filter.

---

## 5. check_url Strategy Recommendation

**Use neutral `check_url` only (e.g. `https://ipv4.icanhazip.com`); do NOT use theblock.co as `check_url`.**

Rationale: theblock check_url produces 0 passing proxies — either because rustls is blocked, or DC IPs are blocked, or both. Either way, the filter produces no pool. A neutral check_url yields a live pool of 494 proxies. Validation against theblock.co is then the responsibility of the `curl_cffi impersonate="chrome"` fetch loop (the anti-CF method from the prior CF-block investigation), which uses a browser TLS fingerprint and can handle per-proxy retry on 403/429. This separation is cleaner: monosans screens for liveness, curl_cffi screens for CF-passability.

**Check-url-as-proxy-pool-filter is not a viable strategy against this CF configuration** with these free proxy sources — the 0-from-17202 result shows the filter would discard every proxy before the real test. The two-stage approach (alive-filter → curl_cffi validation loop) is the correct architecture.

---

## 6. Scope — This Is the Discovery-Stage Proxy Problem Only

This probe addresses **one specific question**: can free proxies from monosans' default sources get past theblock.co's CF to fetch the ~43 remaining sub-sitemaps (≈64 small XML files, ~25s of requests per run, ~11MB total). That is the open discovery problem from the general-roadmap entry.

**This probe does NOT address:**

- **Backfill:** ~27k article pages, GB-scale, would require ~1300 IP-budget rotations (at 21 requests per IP-block). Free proxies from public lists — even if they can pass mechanism 1 via curl_cffi — are ephemeral, unreliable, and overwhelmingly datacenter-hosted. Reliable + free + scalable + CF-bypassing SIMULTANEOUSLY against GB-scale crawl = unrealistic with public lists. Residential proxies (Swiftproxy, Oxylabs, etc.) are a separate, untested, paid-tier question. The backfill problem is OPEN and unresolved by this evidence.

- **The recurring 48h pipe:** same scalability concern. The 48h window is smaller (41 URLs per news-sitemap cycle), so the budget concern is lower — but the IP quality question remains.

**Implications for next steps:** if the curl_cffi loop with the neutral-filtered pool (494 proxies) can successfully fetch the ~43 missing subs, discovery is complete. If the neutral pool's DC IPs are all CF-reputation-blocked against theblock.co (as the 0-result suggests), then residential proxies are the next lever to test (Swiftproxy 500MB free trial, per the test plan from the prior CF-block entry).
