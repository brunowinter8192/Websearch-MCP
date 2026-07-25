# Iteration 19 — 68-Source Pool Expansion

## What We Did

Assembled the maxed public-list source set (68 URLs) and measured the raw proxy pool available before any liveness filter. This was a pure scrape/count probe — no proxy was contacted.

**Dev script:** `dev/news_pipeline/theblock/probe_pool_size.py`  
**Canonical run report:** `dev/news_pipeline/theblock/probe_pool_size_reports/pool_size_20260611T172304Z.md`  
**Run:** 2026-06-11T17:23:04Z | wall-clock: 1.2s | all 68 sources returned HTTP 200

### Parser Fix (run 1 → run 2)

Initial run (17:13Z) used regex `^([a-zA-Z0-9.\-]+):(\d{1,5})$` — strict end-of-line anchor. `zloi-user/hideip.me` uses `host:port:Country` format (e.g. `103.133.27.179:8080:Indonesia`); the trailing `:Country` field caused 0 parsed entries across all 4 zloi files.

Fix: regex changed to `^([a-zA-Z0-9.\-]+):(\d{1,5})(?=[:\s]|$)` — lookahead tolerates trailing `:field` or space-separated extra columns while still rejecting 6-digit fake ports and CF error strings. Full scope-check confirmed: only zloi-user was affected (+1,319 raw delta from the fix itself; remaining delta between runs is live source churn).

Canonical numbers below are from the corrected run 2.

## Source Set (68 URLs)

Three protocol buckets: 29 HTTP/HTTPS sources + 19 SOCKS4 + 20 SOCKS5.

Two mixed-protocol aggregate lists assigned to the HTTP bucket (protocol-unknown entries):
- `themiralay/Proxy-List-World/master/data.txt`
- `clarketm/proxy-list/master/proxy-list-raw.txt`

## Measured Pool Size

| Metric | Count |
|---|---|
| Total raw (all sources, incl. cross-source duplicates) | **428,500** |
| Global unique host:port | **118,701** |
| Sum of per-bucket uniques (http+socks4+socks5) | **319,948** |
| Cross-protocol bucket overlap | **201,247** |

Cross-bucket overlap = 201,247 means the same host:port appears in multiple protocol buckets across ~63% of per-bucket unique entries. Sources like MuRongPIG/Proxy-Master publish identical IPs across HTTP, SOCKS4, and SOCKS5 files.

### Per-Protocol Breakdown

| Bucket | Sources | Raw | Unique |
|---|---|---|---|
| http | 29 | 167,797 | 113,683 |
| socks4 | 19 | 119,083 | 94,342 |
| socks5 | 20 | 141,620 | 111,923 |

### Source Dominance

MuRongPIG/Proxy-Master dominates: 101,620 HTTP + 89,709 SOCKS4 + 100,664 SOCKS5 = **291,993 raw** (68% of total raw). The Proxy-Master list is itself an aggregator — its high count largely drives the cross-bucket overlap.

Low-yield: monosans static GitHub files (http: 76, socks4: 1, socks5: 4 = 81 total). The old baseline of ~17,202 came from the monosans Docker scraper-checker running dynamically, not from these static pre-committed files.

## Baseline Comparison

| | Raw | Unique |
|---|---|---|
| Prior monosans single-source Docker scraper run | ~17,202 | not measured |
| This run (68 sources, corrected parser) | 428,500 | 118,701 |
| Expansion | **24.9×** raw | — |

Global unique (118,701) is **6.9×** the old raw baseline (which was itself un-deduped).

## Dead Sources

None — 68/68 HTTP 200. Notable: `mmpx12` files have a single Cloudflare error string concatenated onto line 1 (`error code: 502<ip>:<port>`); the parser correctly rejects these 3 corrupted lines (1 per file). Not a systematic issue.

## Parse Logic

Line formats handled: bare `host:port`, `proto://host:port`, `proto://user:pass@host:port`, `host:port:Country`. Regex: `^([a-zA-Z0-9.\-]+):(\d{1,5})(?=[:\s]|$)` after stripping protocol and auth prefixes. Port validated 1–65535. Blank lines, comment lines (`#`), HTML/markdown silently skipped.

## Next Step

This unique count (118,701 global) is the input to the liveness filter. The curl_cffi-chrome pass rate was measured at 18.8% of a neutral pool in the prior discriminator entry. Projected CF-passing pool: ~22,000 proxies if the rate holds at this scale.
