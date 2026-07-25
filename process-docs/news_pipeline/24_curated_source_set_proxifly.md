# 24 — Curated Source Set: monosans + proxifly (post-clean-slate expansion)

**Date:** 2026-06-12
**State:** proxifly added as the second curated source. The alive-check source is now `--source curated` (monosans + proxifly, merged + deduped). Implemented + merged to dev. First combined run: 549 alive of 3508 checked.

## Expansion frame
The prior clean-slate entry set "monosans-only first, expand later". This is the first expansion. Selection criterion: **by GitHub stars (curation/trust), NOT by list size** — a big list (MuRongPIG ~83k raw, ⭐411) is a dilution flood; a high-star list is curated. Stars and the historical CF-signal from the pipe/cycle-economics entry agree (MuRongPIG dropped on both).

## proxifly/free-proxy-list [⭐5628, inspected via gh-cli 2026-06-12]
- **~3579 proxies**, validated every 5 min ("working proxies", no duplicates) — a pre-checked pool like monosans, NOT a raw dump. HTTP 1175 / HTTPS 966 / SOCKS4 774 / SOCKS5 664 (counts drift per 5-min refresh).
- **Schema (clean for our keys):** `all/data.json` = array of `{protocol, ip, port, proxy: "proto://ip:port", https: bool, anonymity, score, geolocation}`. The `proxy` field IS our canonical key string. No auth (free proxies). Field is `ip` (not `host` as in monosans).
- **"https" is NOT a protocol:** the `https` bucket holds entries with `protocol: "http"` + `https: true` (an http proxy that also supports HTTPS-CONNECT). Verified empirically: the http-bucket and https-bucket are **disjoint by host:port** (1153 vs 975, overlap 0) — different proxies, same http protocol family, split by capability. So `protocol` ∈ {http, socks4, socks5} only; we read the field directly, no https special-casing.

## Architecture — unified curated source (NOT a parallel selectable source)
`curated_sources.py` → `load_curated_proxies()` fetches monosans (`load_monosans_proxies`) + proxifly (`_fetch_proxifly`, reads `all/data.json`), concatenates, dedups via the canonical `proxy_key`. `proxy_key` was promoted from private `_proxy_key` to public in `proxy_status_log.py` specifically so the dedup keyspace is provably identical to the log-match keyspace (one source of truth: `record_run`, `partition_fresh`, `_merge_dedup` all use it). Returns one `[(protocol, host:port)]` list. `probe_liveness.py --source curated` runs it through the existing `partition_fresh` → `run_checks` → `record_run`; the recheck mechanism is unchanged and source-agnostic (see the recheck-interval entry). monosans-origin is NOT tracked through the merge — a per-source scoreboard is pointless when lists overlap (only meaningful for fully independent sources).

## First combined run [2026-06-12T21:02Z, `--source curated --concurrency 128`]
- Curated list (deduped): **3578**. Staleness-filter skipped **70** (monosans proxies checked <60 min before, measured at filter-time = run-start). Checked **3508**.
- **549 alive (15.6%)**, 2959 dead.
- vs monosans-only baseline (the prior recheck-interval entry): 23 alive (21.1%). → **24× more usable proxies**; the lower % is expected (proxifly contributes more but, on our network path, somewhat weaker proxies). Absolute working count is the win.
- Log accounting verified: 162 → 3652 unique; the 3508 checked got the run timestamp + incremented checks/status; 70 fresh-skipped + 74 dropped-off-list entries untouched (`last_seen` preserved).

## Candidate landscape (by stars) — next expansion
Most high-star raw-proxy-list repos are already in the parked 68-source set (`probe_pool_size.py`). Ranked: proxifly ⭐5628 (ADDED), TheSpeedX ⭐5621 (the real next candidate — RAW list ~9k, per-file protocol; standalone alive-eval in flight), **oxylabs/free-proxy-list ⭐3013 — RULED OUT: marketing shell** (README + images only, no list files; a sign-up funnel for their paid service, 5 IPs behind registration), clarketm ⭐2386, databay-labs ⭐1692, monosans ⭐1426 (in use), hookzof ⭐991, roosterkid ⭐855, jetkai ⭐644, sunny9577 ⭐580, ShiftyTR ⭐579, zloi-user ⭐471, mmpx12 ⭐429, **MuRongPIG ⭐411 — keep OUT** (dilution flood, 0 CF historically), Zaeem20 ⭐391, ErcinDedeoglu ⭐372. Pool/aggregator TOOLS (zu1k/proxypool, chill117/proxy-lists, gavin66/proxy_list) are not pasteable lists — excluded.

**Lesson — pure-stars ranking can mislead.** oxylabs (⭐3013) looked like a top candidate by stars but is a vendor marketing repo with no data — structure inspection (`get_repo_tree`) is mandatory before treating a high-star repo as a source. After the two pre-validated sources (monosans, proxifly), the remaining high-star repos are RAW (TheSpeedX, clarketm, …) — lower alive%, higher volume — so each addition is %-gated by marginal/standalone alive% (per the following entry's approach).

## Standalone alive-evals — expansion candidates [2026-06-12]
Each candidate is eval'd standalone (`--source <repo>`, all proxies, no filter/cap, no log write) to measure its raw alive% before deciding inclusion. Decision by alive **%**, not absolute count (per the following entry's approach).

| Repo | ⭐ | Tier | Format | Standalone alive% |
|---|---|---|---|---|
| TheSpeedX | 5621 | RAW | bare host:port, per-file proto | **5.7%** (507/8964) — below bar; shelved in favour of clean repos |
| databay-labs | 1692 | CLEAN (5min, "zero MITM") | bare host:port, per-file http/socks4/socks5 | **6.4%** (181/2808) |
| jetkai | 644 | CLEAN (online-at-testing, hourly) | bare host:port, `online-proxies/txt/proxies-{http,https,socks4,socks5}.txt` | **1.9%** (86/4643) — worst, despite strongest claim |
| roosterkid | 855 | CHECKED (hourly, ping) | DECORATED `<flag> IP:PORT <ms> <CC> [ISP]` + header block — regex-extract IP:PORT, skip header | **4.6%** (11/238) |

**Keying (decided after format inspection):** all loaders produce `(proto, host:port)` with proto ∈ {http, socks4, socks5}; a "https" file is tagged **http** — free "https" lists are http-family proxies (CONNECT-capable), not a distinct scheme, which matches proxifly's own `protocol: http` for its https bucket. → `proxy_key` = `proto://host:port`, consistent with the log + dedup.

**Format landmine (roosterkid):** the checked files carry a donation/website header block and decorate each proxy line with a country-flag emoji, response-time, country code and ISP. A naive bare-line loader would parse the BTC/ETH donation addresses as proxies — hence the per-line `\d{1,3}(?:\.\d{1,3}){3}:\d+` extract + header skip. (The user's "understand the repos before handling them" rule caught this.)

**Conclusion — no clean expansion exists.** Validation claims do not predict our alive%: jetkai (strongest claim, "online at the time of testing") is the WORST at 1.9%; databay's "zero MITM" → 6.4%. None approach monosans+proxifly's 15.6% — those two are uniquely high-yield for our network path. Every candidate is 2-6%, so a strict %-bar adds none. Expansion is therefore a pure volume-at-low-quality play (biggest absolute: TheSpeedX +507 because it is huge, databay +181; roosterkid +11 and jetkai +86 not worth it). The higher-value lever for pool depth is likely the **monosans/proxy-scraper-checker TOOL** (dynamic multi-source scrape + self-check, ~17k historically, with a theblock `check_url` to output CF-passing proxies directly, per the earlier CF-block entry), NOT more raw GitHub lists. Needs Docker + TTY (fails headless).

## Note
Historical source evaluations from the earlier optimization/expansion entries are superseded by the clean slate (the prior entry) — their measured numbers are not current state. This file is the post-clean-slate curated-source record.
