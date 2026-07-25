# 27 — jhao104 Adoption Decided + Recently-Evicted Dedup Patch

**Date:** 2026-06-13
**State:** Architectural fork from the prior tool-pivot entry resolved (chat decision, setup/benchmark pending → worker). Direction: ADOPT jhao104/proxy_pool as the self-maintaining pool; do NOT revert to monosans + own orchestration. Add exactly ONE mechanism on top — a recently-evicted dedup at the scrape-insert step.

## Fork resolution
The prior tool-pivot entry left two paths: (A) lean tool we orchestrate (monosans + our recheck/cap/feed logic) vs (B) full pool-server that subsumes our machinery (jhao104). Resolved to **B with one patch**.

Opus initially leaned A (drop jhao104), on the grounds that jhao104's continuous daemon fights synchronized passes + has a re-scrape churn gap + doesn't match our operating-model control. User overruled with a better synthesis: keep jhao104's three strengths and patch only the churn. Accepted — the patch resolves the churn objection more cleanly than swapping the whole tool.

**Kept from jhao104 (unchanged):**
- Scrape (`fetcher/sources/` auto-loaded scraper classes)
- Direct CF-evaluation — check target = theblock URL, so the single validation step IS the CF-pass test (no separate neutral-alive stage; a dead proxy fails the theblock GET, a CF-blocked proxy fails too — both filtered in one step)
- Dynamic replenish (auto re-scrape when pool < `POOL_SIZE_MIN`)

## The one addition — recently-evicted dedup (60min cooldown)
**Problem it closes (the churn):** jhao104's fetchers do not remember what they evicted. On a high dead/CF-block ratio (the normal case — most scraped proxies fail theblock CF), the auto-replenish re-scrapes the same just-evicted proxies, which get re-validated and re-evicted → endless churn on the same garbage.

**Mechanism:** this is our recheck-interval-entry staleness-filter (the 1h `--recheck-window`) ported onto jhao104's scrape-insert step. When a scraped proxy is one that hit `MAX_FAIL_COUNT` (= got evicted) within the last 60min → skip it, take the next. Redis-native: write an eviction-record key per proxy with `EXPIRE 3600` at eviction time; at scrape-insert do an `EXISTS` check; the key auto-expires after 60min so the proxy is eligible again (in case it recovered).

**Scope — narrower than our `partition_fresh`, deliberately:** we block ONLY the recently-evicted, NOT all recently-checked. jhao104 keeps alive proxies in the pool and re-validates them on its own schedule — they are never re-scraped, so they need no dedup. The only thing a re-scrape would wrongly re-introduce is the freshly-evicted dead. That is exactly the set the cooldown gates.

**Implementation reality:** a real (small, contained) code patch to jhao104's proxy-add path + one Redis structure — not a config line. The config-only parts are separate (see below).

## Config + extension decisions (carried from the prior tool-pivot entry)
- **Check target:** `setting.py` `HTTPS_URL` → a theblock sitemap URL.
- **Custom validator:** add a theblock validator (GET + 200 + XML-body) via the `@ProxyValidator.addHttpValidator` decorator, instead of relying on the default HEAD-status-only check (which would falsely pass a rare CF 200-challenge page). Matches our existing rigorous check.
- **Fail tolerance:** `MAX_FAIL_COUNT > 0` (or `MAX_FAIL_RATE`) — required because of the home-router NAT false-death finding (per the batch-operating-model entry): a single failed check is frequently a transient router-saturation false-death, not a genuine death. `MAX_FAIL_COUNT = 0` would evict good CF-passing proxies on a blip.
- **Concurrency:** the measured ~128 clean zone (per the concurrency-sweep and batch-operating-model entries) was against a LIGHT neutral endpoint and an ASYNC checker. jhao104 hardcodes **20 sync threads** (`range(20)` in `helper/check.py`) — not configurable, must be patched to tune. The theblock check is heavier / longer-lived per connection → optimal concurrency against theblock must be re-measured, do not assume 128. See code-read section below.

## jhao104 code-read — actual mechanics + insertion points [2026-06-13, full source read]
Local clone: `dev/news_pipeline/theblock/jhao104/upstream/` (588K, ~50 py files). Corrects/sharpens the prior tool-pivot entry's summary.

**Scheduler cadence** (`helper/scheduler.py`): two apscheduler interval jobs — `__runProxyFetch` every **5 min** (scrape → "raw" check → passing proxies `put` into pool), `__runProxyCheck` every **2 min** (if pool < `POOL_SIZE_MIN` trigger a fetch, then re-validate the WHOLE pool = "use" check → keep/evict). One fetch runs immediately on startup.

**Concurrency hardcoded at 20 sync threads** — NOT configurable, NOT in `setting.py`. `Checker()` (`helper/check.py` ~line 150) spawns `for index in range(20)` `_ThreadChecker` threads using blocking `requests.head`; scheduler executor also `max_workers=20`. DIVERGENCE: our measured ~128 clean-zone was async + a LIGHT endpoint; jhao104 is 20 sync threads. For theblock (heavy GET + CF) 20 may even be high — must be measured. To tune: patch `range(20)` → a `setting.py` value.

**HTTP-list vs HTTPS-list gating** (`helper/check.py` `DoValidator.validator`, lines 42-47): the eviction-driving `last_status` = `http_r` (the HTTP-validator list result) ONLY; the HTTPS-validator result merely sets the `proxy.https` flag. CONSEQUENCE: our theblock validator MUST register in the **HTTP** list (`@ProxyValidator.addHttpValidator`) so it drives keep/evict — even though theblock is an https URL (the validator does the https GET internally). AND the two existing http-list defaults must be disabled: `httpTimeOutValidator` (HEAD to httpbin) + `customValidatorExample` (returns True) — else they co-gate. The prior tool-pivot entry named the right decorator but missed the disable-defaults + gating-list subtlety.

**Validators use plain `requests` → will NOT pass CF.** `validator.py` validators call `requests.head(...)`. Our theblock validator MUST use `curl_cffi` `impersonate="chrome"` (the anti-CF method established in the earlier CF-block and discriminator entries) + GET + status 200 + XML-body check. This is the integration crux — a plain-`requests` theblock check fails CF signature-gating regardless of proxy quality.

**Recently-evicted dedup — exact two hooks:**
- WRITE (mark on evict): `helper/check.py` `_ThreadChecker.__ifUse`, eviction branch (`if proxy.fail_count > maxFailCount: ... delete`, lines ~130-134) — also write Redis `SETEX evicted:<proxy> 3600 1`.
- SKIP (on scrape): `helper/fetch.py` `Fetcher.run()` yield loop (lines ~150-152) — before yielding a scraped proxy, skip if `EXISTS evicted:<proxy>`. Keeps evicted proxies out of the raw-check queue for 60min.
- redis surface: `db/redisClient.py` exposes only hash ops (hset/hdel/hexists) — add `mark_evicted` (setex) + `is_recently_evicted` (exists) helpers. Eviction keys live in the same redis DB as the `use_proxy` hash. `Fetcher` currently has no db handle — needs a `ProxyHandler`/redis reference for the skip-check.

**Pool storage:** Redis HASH `use_proxy` (key=ip:port, value=JSON Proxy). `POOL_SIZE_MIN = 20` is a fetch-trigger floor, NOT a target. The earlier "15k pool" was the NEUTRAL-alive pool (monosans); the theblock-CF-passing pool will be far smaller (CF-pass is a fraction of the 15.6% alive). Benchmark reveals the actual sustainable CF-pool size — do not assume 15k for CF-passing.

## Logging
Per validation cycle: alive count vs dead count (the pool-health signal; the trend over cycles tells us if the operating model holds). In jhao104's continuous model "per run" = "per validation cycle". This minimal log is sufficient on this design precisely because the recently-evicted dedup kills the churn structurally — "dead" in a cycle is freshly evaluated, not re-counted leftovers.

## Next session — setup + benchmark (worker, dev/ probe)
Probe location: `dev/news_pipeline/theblock/jhao104/` (next to the monosans machinery for a 1:1 benchmark). Docker present; OrbStack CLI = `orb`.

1. Clone jhao104, bring the daemon loop up clean against a NEUTRAL target first (verify scrape → store → re-validate → API at all).
2. Point check at theblock + custom theblock validator (GET+200+XML) + `MAX_FAIL_COUNT > 0`.
3. Add the recently-evicted dedup (Redis key + `EXPIRE 3600` at scrape-insert) + alive/dead-per-cycle logging.
4. Benchmark vs monosans (`check_url = theblock`): **CF-passing proxies per cycle + cycle time**. This run also produces the long-open CF-pass-rate gate for the current network path (per the pipe/cycle-economics entry).

## Stage 1 results — neutral baseline [2026-06-13, worker jhao104-probe]
Probe brought up from source (**Python 3.12** — 3.14 breaks the `lxml`/`APScheduler`/`gunicorn` pins), Redis via Docker, run against the DEFAULT neutral targets (httpbin HTTP / qq.com HTTPS). Reproducible via `dev/news_pipeline/theblock/jhao104/setup.sh`; full detail in `dev/news_pipeline/theblock/jhao104/NOTES.md`.

- **End-to-end works on this machine — no egress blocker.** Validators' explicit `proxies=` override the env `HTTPS_PROXY` (mitmproxy), so checks go local → proxy-under-test → target; fetchers run with proxy env stripped. Direct outbound to arbitrary proxy IPs/ports IS allowed (the feared firewall case did not occur). Verified empirically via `Session.merge_environment_settings()`.
- **One fetch+check cycle:** 540 scraped (14 sources, mostly scdn/daili66/geonode/proxifly; ihuan+zdaye timed out) → 527 format-valid → **117 passed the HTTP neutral check = 22.2% alive**. API serves them (`/count`=117, `/get` returns proxies).
- **0 HTTPS (qq.com) — watch-point for theblock.** None of the 117 http-alive proxies tunneled HTTPS to qq.com. Free proxies rarely support HTTPS tunneling; qq.com may also geo-block non-CN IPs. NOT a theblock prediction (the Stage-2 validator does a `curl_cffi` https GET, unlike jhao104's plain qq.com HEAD) — but flags HTTPS-tunnel capability as the constraint to measure.
- Confirms (for Stage 2/3 tuning): `MAX_FAIL_COUNT=0` evicts on first fail (too aggressive → set >0); `PROXY_REGION=True` fires a ~2s geo-lookup per new proxy (latency → consider disabling).
- jhao104 operates on small fresh per-cycle batches (~540), NOT a large frozen pool like our monosans path — a different operating profile to weigh in the benchmark.

Comparison context: our curated monosans+proxifly neutral-alive = 15.6% (per the curated-source-set entry) but on a 320k frozen pool. jhao104's 22.2% is on its own 540-proxy fresh batch from a different (Chinese-heavy) source set — not directly comparable. The apples-to-apples number is the theblock-CF pass rate (Stage 4 benchmark).

## Stage 2 results — theblock CF-pass rate [2026-06-13, worker jhao104-probe]
Implemented the theblock gating check via a curl_cffi overlay validator (tracked `dev/news_pipeline/theblock/jhao104/patches/helper/validator.py`, copied into `upstream/` by setup.sh). Sole http-list gate = `theblockValidator` (curl_cffi `impersonate="chrome"` GET `https://www.theblock.co/sitemap_tbco_index.xml`; pass = 200 + XML marker in first 500B). The 3 stock validators disabled (decorator omitted). `MAX_FAIL_COUNT=2` via env override (ConfigHandler reads `os.getenv` first — no setting.py patch). Validator verified correct by Opus (diff review) — it found a real passer, so the result is genuine, not a bug.

- **theblock CF-pass rate: 1/526 (0.19%) cycle 1; 0/651 cycle 2; combined 1/1177 = 0.085%.** Pool = **1** proxy (`103.24.214.190:8082`, geonode, ID). All 13 other sources: 0 CF passes. Raw-check 526 proxies @ 20 threads / 15s timeout = 3m17s.
- **Verdict: jhao104's OWN sources yield essentially zero theblock-CF proxies — unusable for a backfill as-configured.**

**Confounds before concluding jhao104 is unviable (the Stage 4 benchmark must control these):**
1. **http-only scheme.** The validator (and jhao104's whole model) addresses proxies as http-CONNECT (`http://host:port`). The 18.8% discriminator (from the passability-discriminator entry) ran on a MIXED http/socks pool with per-protocol schemes. If CF-passing free proxies are predominantly socks, jhao104 structurally misses them (it stores bare ip:port, validates as http → socks wasted).
2. **Source-set.** jhao104's fetchers are China-heavy (scdn, daili66, geonode, kuaidaili...); the monosans path uses TheSpeedX/proxifly/roosterkid/sunny9577/hookzof. Different IP-reputation.
3. **Temporal/IP-reputation drift.** CF-pass measured 18.8% (earlier discriminator entry), 0.8% (later live pipe, per the pipe/cycle-economics entry), now 0.085% — extremely volatile.

## Benchmark result — curated list DIRECT theblock-CF + home-IP [2026-06-13, worker jhao104-probe]
Ran `dev/news_pipeline/theblock/probe_curated_theblock_cf.py` (committed): the monosans+proxifly curated list straight against the curl_cffi theblock check, NO alive pre-filter, CORRECT per-protocol scheme (http/socks4/socks5) — identical gate to jhao104 Stage 2 except the scheme. Concurrency 50 (conservative for heavy theblock GETs vs the ~128 light-check clean zone). Probe code reviewed by Opus — sound.

- **Curated CF-pass: 52/3477 = 1.496% — 17.6× jhao104's 0.085%.** Per-protocol:
  | Protocol | Passed | In list | Rate |
  |---|---|---|---|
  | socks4 | 28 | 785 | **3.567% (best)** |
  | http | 20 | 2119 | 0.944% |
  | socks5 | 4 | 573 | 0.698% |
- **Both jhao104 confounds CONFIRMED:** (1) source-set — curated (international) is 17.6× jhao104 (China-heavy); (2) http-only — socks4 is the BEST cohort (3.8× http), exactly what jhao104's http-CONNECT-only model structurally discarded. jhao104's 0.085% was bad-sources AND missed-socks combined.
- **Home-IP gating check: 200 + sitemap XML, DIRECT (no proxy), curl_cffi-chrome.** Our home IP is currently CF-reputation-CLEAR — the persistent mechanism-2 flag from the earlier monosans pool-evidence entry has decayed. The home-IP + pacing approach is on the table (the gating request works). Open: theblock's safe req/min rate; asymmetric risk (home IP is our only IP, cannot rotate; an overrun → persistent block).

## Survey results — per-repo theblock-CF [2026-06-13, worker repo-survey]
Ran `dev/news_pipeline/theblock/probe_repo_cf_survey.py`: all 22 candidate repos (the 68-source set grouped by repo) sampled ~1250 each against the curl_cffi theblock check (concurrency 50), per-protocol, with cross-repo cumulative dedup. Resolves the prior tool-pivot entry's "which sources" question with data.

**Ranked by CF-rate (full 22):** themiralay 15.21% (217, http-only), roosterkid 10.83% (240, socks4 15.33%), monosans 10.20% (98, http), databay-labs 6.00% (1630, socks4 9.97%), r00tee 2.56% (14487), iplocate 2.32% (2384), sunny9577 2.24% (1894), ALIILAPRO 2.08% (3558), dpangestuw 2.08% (11570), Zaeem20 1.76% (1292), zloi-user 1.60% (1556, socks4 10.29%), hookzof 1.50% (732, socks5), TheSpeedX 1.36% (9791), proxyscrape 1.36% (8842), proxifly 1.28% (3735), mmpx12 1.20% (1377), ShiftyTR 0.92% (983), ErcinDedeoglu 0.56% (45436), mzyui 0.56% (24535), jetkai 0.32% (4643), **MuRongPIG 0.08% (291993 — the junk flood)**, clarketm 0.00% (400).

**Cumulative unique (top-down by CF-rate):** top 10 (≥1.76%) = 20,148; **top 13 (≥1.36%) = 22,080**; top 15 (≥1.28%) = 27,221.

**Conclusions:**
- Pattern: small pre-checked/curated lists = high rate (themiralay/roosterkid/monosans/databay 6-15%); big raw aggregators = junk (MuRongPIG 0.08%, mzyui/ErcinDedeoglu 0.56%).
- **socks4 is consistently the best protocol cohort** across repos (roosterkid 15.33%, zloi 10.29%, databay 9.97%).
- The 20-25k pool target is reachable with QUALITY: **top ~13 repos (≥1.36%) → ~22k unique, no junk needed.** Several repos (sunny9577, ALIILAPRO, mmpx12, ShiftyTR) add ZERO new unique (full overlap); volume comes from r00tee + dpangestuw.

**Home-IP RE-BLOCKED (updates the benchmark home-IP finding above):** during the acquire-pipe Stage-2 sign-off, the direct-from-home index GET returned 403 — our home IP went from CF-clear to CF-BLOCKED within this same session (from the direct touches). Confirms the home-IP + pacing path is FRAGILE (single IP flags easily, can't rotate) → the proxy-pool path is the robust one, and the pipe's index-fetch proxy-fallback is necessary (proven: it caught the 403 and fetched the index via a proxy).

## Verdict + Status
**jhao104 DROPPED** (bad sources + http-only handicap; Stage 3 dedup permanently off). Probe artifacts stay under `dev/news_pipeline/theblock/jhao104/`.

Direction chosen: the **proxy-pool path** (home-IP-pacing is fragile, see above). The forward pipe is being built — see the following acquire-pipe design entry. Backfill candidate pool = the **top 13 survey repos (~22k unique)**. Stages 1-4 built; Stage 5 (orchestrator) + the 64-sitemap test run pending next session.
