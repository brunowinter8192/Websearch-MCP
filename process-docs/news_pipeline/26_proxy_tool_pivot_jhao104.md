# 26 — Proxy Source Strategy Pivot: from list-pulling to a self-maintaining tool

**Date:** 2026-06-12
**State:** Strategy decision. After standalone-evaluating six GitHub proxy LISTS (all low-yield for our network), the direction pivots from "pull more lists" to adopting a self-maintaining scraper-checker TOOL. jhao104/proxy_pool is the lead candidate; setup + CF-targeted run deferred to a dedicated next session.

## Why the pivot — list expansion is futile for quality
The standalone evals (from the curated-source-set entry) measured every realistic list candidate against our own neutral check @128:

| Source | alive% |
|---|---|
| monosans + proxifly (curated, pre-validated) | 15.6% |
| databay-labs (5min, "zero MITM") | 6.4% |
| TheSpeedX (raw) | 5.7% |
| roosterkid (checked, ping) | 4.6% |
| jetkai ("online at the time of testing") | 1.9% |

Two hard lessons: (1) **validation claims do not predict our alive%** — jetkai has the strongest claim and the WORST result; (2) **only monosans + proxifly are high-yield for our network path** — every other list sits at 2-6%. There is no clean list-expansion. Adding raw lists is a pure volume-at-low-quality play, and each measurement is a momentary snapshot of a constantly-churning list. → Stop pulling lists; adopt a TOOL that scrapes + checks + maintains a pool itself, validated against our actual target (theblock CF).

## Tool landscape [GitHub survey 2026-06-12]
| Tool | ⭐ | Type | Fit |
|---|---|---|---|
| jhao104/proxy_pool | 23406 | full pool-server (Python): scrape + check + recheck-scheduler + score + API | **LEAD** — subsumes our system; configurable check target |
| SpiderClub/haipproxy | 5538 | targeted-site pool (Python/scrapy + splash, JS render) | reserve — best CF-targeting, heaviest infra (redis + splash + compose) |
| constverum/ProxyBroker | 4151 | finder + checker (Python) | OUT — README 404, original unmaintained |
| mubeng/mubeng | 2114 | checker + IP-rotator (Go) | OUT for our goal — does NOT scrape (needs external lists) |
| monosans/proxy-scraper-checker | 1275 | lean one-shot scraper + checker (Rust), custom check_url | **BENCHMARK** — known, we orchestrate it ourselves |
| iw4p/proxy-scraper | 594 | scraper (Python) | weaker than monosans (per the methods-optimization entry) |

The architectural fork: a **lean tool we orchestrate** (monosans — outputs a list, we keep our recheck/cap/feed logic) vs a **full pool-server that subsumes our machinery** (jhao104/haipproxy bring scheduler + scoring + API).

## jhao104/proxy_pool — how it works (the clou)
A self-maintaining pool. A daemon runs a 4-step loop:
1. **Scrape** — `fetcher/sources/` auto-loads every `enabled=True` fetcher class (one per source site); pluggable, blacklist via `PROXY_FETCHER_EXCLUDE`.
2. **Store** — Redis (`DB_CONN`, table `use_proxy`).
3. **Re-validate + evict** — periodically re-checks every stored proxy against a target URL; fail-count based (`fail_count` ++ on fail, -- on pass), evict at `MAX_FAIL_COUNT`.
4. **Auto-replenish** — re-scrapes when pool < `POOL_SIZE_MIN`.

Output via Flask **HTTP API** (`/get`, `/get_all`, `/count`, `/pop`). Run: `proxyPool.py schedule` (daemon) + `proxyPool.py server` (API); Docker-compose bundles redis. Structure: `fetcher/` (scrapers), `db/` (redis client), `handler/` (proxy + config + log), `helper/` (check, fetch, scheduler, validator), `api/` (Flask), `setting.py` (config).

**The clou for us:** the check target is a config line in `setting.py`:
```
HTTP_URL  = "http://httpbin.org"
HTTPS_URL = "https://www.qq.com"   # ← set to a theblock URL
```
Point it at theblock → the pool self-maintains a CF-passing proxy set.

**It subsumes our hand-built system:** their re-validate + evict = our staleness filter (per the recheck-interval entry); their scheduler = our cap-cadence (per the batch-operating-model entry); their fail-count eviction = our scoring; their API = our feed-to-CF.

## jhao104 validator — code-checked [helper/validator.py, helper/check.py]
- `httpTimeOutValidator` / `httpsTimeOutValidator`: `r = head(conf.httpsUrl, ...); return True if r.status_code == 200 else False`. **Pass criterion is `status_code == 200`** → a CF 403/503/challenge ≠ 200 → fails. So out-of-the-box, pointing the check at theblock correctly rejects CF-blocked proxies. ✓
- Caveats: it is a **HEAD request, status-only** (no body check) — weaker than our GET + 200 + XML-body; a (rare) CF 200-challenge-page would falsely pass.
- **Explicitly extensible**: `@ProxyValidator.addHttpValidator` decorator + a `customValidatorExample` stub. The clean path is to ADD a theblock validator (GET + 200 + XML), matching our current rigorous check. The framework is designed for this.
- `DoValidator.validator` (check.py): fail_count ++/--; with `MAX_FAIL_COUNT = 0` a single fail evicts. **Given our home-router false-death finding (per the batch-operating-model entry), set `MAX_FAIL_COUNT > 0` or `MAX_FAIL_RATE`** so transient NAT-saturation false-deaths do not evict good proxies. Our own measurement tells us how to tune the tool.

## Next session — the comparison
1. Set up jhao104 via OrbStack (Docker). The TTY/headless issue is solved: macOS Tahoe `open -g` opens the window in the background.
2. Add a custom theblock validator (GET + 200 + XML); set the check target to a theblock sitemap; tune `MAX_FAIL_COUNT` for fail-tolerance.
3. Run; measure **CF-passing proxies per cycle + cycle time**, against monosans (`check_url = theblock`) as the benchmark.
4. Key verification: does the validator reject CF block pages in practice (true CF-pass), and is the yield enough to feed a backfill.

Decision after the comparison: adopt jhao104 (drop most of our `dev/news_pipeline/theblock/` proxy machinery) vs keep monosans + our own orchestration.

## Status
Pivot decided; tool setup + run is the next-session task.
