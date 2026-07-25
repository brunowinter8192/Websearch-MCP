# 15 — The Block CF Block: Empirical Problem + Anti-CF Method

**Date:** 2026-06-10
**State:** Problem defined empirically; anti-CF method converged from GH+RAG research; NOT yet tested. Resume next session.

## Empirical Problem Definition (worker run — observed only, not inferred)

**Goal:** fetch all 64 sub-sitemaps. Block hit mid-run. Two DISTINCT mechanisms observed:

**(1) Passive client-signature check** — immediate, volume-independent:
- `urllib` (Python default) → **403 on the FIRST request**.
- `curl` → **200 on the first request**.
- The host rejects certain client signatures instantly, regardless of count.

**(2) Rate / volume trigger** — after a burst:
- `curl` + 1s delay: first **~21 subs** returned 200 + real XML (~19k `/post/` URLs, IDs 136–342,769).
- At ~request 21 (≈21 requests in ~21s): flip to **403/429**, no XML.
- Afterward EVERY request (even single) → instant 403 (post_26) / 429 (linked_0), sub-independent → **block sits on the IP/origin**, not the individual sub.

**Persistence:** 30s-interval probes over ~5 min stayed 429; 5 min of silence didn't clear it. ("Recovery 1–2h" = worker estimate, NOT measured — and irrelevant: we care about NOT triggering, not the threshold.)

**Never observed:** a JS "Just a moment" challenge — only 403/429 codes. **No evidence of a JS-challenge layer; only signature-check + rate-block.**

**Other endpoints (context):** `/latest` → 301 → `/latest-crypto-news` → 429 (early); `/category/markets` → 200, 331KB raw HTML with `/post/` links inline.

## Anti-CF Method (converged — to test next session)

Levers map ONLY to the two observed mechanisms. **JS-challenge tools (patchright, FlareSolverr, cloudscraper, nodriver) are OUT** — unevidenced; we build for what we've seen. (If a JS challenge ever appears → new observation, add the browser path which is already wired via crawl4ai `UndetectedAdapter` in `src/scraper/scrape_url.py` — patchright; note: `enable_stealth=True` is broken on crawl4ai 0.8.6, and `UndetectedAdapter` crashes at concurrency>1, see `crawl4ai_stealth_stack.md`.)

- **Signature layer:** `curl_cffi` with `impersonate="chrome"` (real browser TLS/JA3/HTTP2). curl already passes; curl_cffi is the hardened client. urllib fails because of its non-browser signature.
- **Rate/IP layer (the dominant blocker):** the real lever is the IP. **Pacing is LAST RESORT ONLY** — discovery is a ~1-minute job (64 small XML fetches; the 21 unblocked took ~30s; full 64 back-to-back ~25s, at 1s-pace ~90s). Trigger is ~21 requests, we need 64 → one IP-budget doesn't cover one run. Pacing to a safe rate would balloon a ~1-min job to ~21 min → absurd. **Residential proxies = UNTESTED, not confirmed-unavailable** (old stealth doc said "not available" — but we never tried; decide after trying).

**The method (read from sources, not name-matched):**

1. **`monosans/proxy-scraper-checker`** (Rust binary — run it / Docker, NOT a Python import; outputs validated proxies as txt/json). **Key lever (read from its `config.toml`):** `check_url` is customizable → set it to a theblock.co sitemap → the tool outputs ONLY proxies that pass The Block's CF. Turns "alive proxies" into "CF-passing proxies." Sources = proxyscrape API + GitHub raw lists (TheSpeedX, proxifly, roosterkid, sunny9577, hookzof). Companion `monosans/proxy-list` = a pre-checked pool (skip running the tool).
   - **Unconfirmed:** whether the "basic connect/read check" (for a non-httpbin URL) filters on status 200 vs accepts a 403 block page — needs a read of monosans `src/` checking logic OR just an empirical test. Does NOT break the method: our own fetch-loop validates 200+XML per fetch regardless; the check_url filter only improves hit-rate.

2. **`curl_cffi` proxy rotation** (pattern read from `ediiiz/cURLsolverr` main.py):
   ```python
   from curl_cffi import requests
   s = requests.Session()
   s.impersonate = "chrome"                      # current curl_cffi; cURLsolverr pins old chrome110 — ignore, use latest
   s.proxies = {"https": "socks5://host:port"}   # also set "http"; user:pass via socks5://user:pass@host:port
   r = s.get(sitemap_url)                          # r.status_code / r.content / r.cookies
   ```
   Rotate proxies over the ~43 missing subs, retry on 403/429 with the next proxy, validate 200+XML per fetch.

3. **Verify:** does the filtered pool reliably pull the 64 fast? Free + scalable + reliable-enough → that's the discovery method, done.

**Honest risks:** CF-passing free proxies are ephemeral (fine for a one-off discovery run of minutes; a maintenance issue for the recurring 48h pipe). Reliable + free + scalable SIMULTANEOUSLY against CF at HIGH volume (the 27k-page scrape) is a unicorn — that is the SEPARATE scrape problem, not this discovery problem.

## Next-Session Test Plan

1. Resume from the worker cache (~43 subs missing, per the prior entry's discovery status).
2. monosans with `check_url` = a theblock.co sitemap → filtered free-proxy pool (or start from `monosans/proxy-list`).
3. Worker: `curl_cffi` `impersonate="chrome"` + proxy rotation + retry over the ~43 missing subs; validate 200+XML.
4. Opus verifies the worker's code against the two GH references (monosans `config.toml`, cURLsolverr `main.py`) per the orchestration model.
5. If the free pool's CF hit-rate is too low → test a residential-proxy free trial (Swiftproxy 500MB etc.; 500MB ≫ the ~11MB/run need).

## Methodology Note (the session's biggest win)

How to approach scraping / anti-bot problems:
- Define the problem **empirically** from worker observations; separate observed from inferred.
- **Read sources** (repo READMEs + config + code), never name-match repos. (`monosans` config.toml's `check_url` lever was invisible until actually read.)
- **No production fallback chains**, but explorative roadmaps to FIND the one working method are correct.
- Per-site, not dynamic.
- **Watch the over-caution:** guardrails around webscraping/proxies induce wishy-washy flip-flopping. Within a clear, agreed scope: work decisively and methodically, no assumptions. (Candidate for promotion to a `~/.claude/` working-rule.)
