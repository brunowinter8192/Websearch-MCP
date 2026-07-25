# Stealth

> **Demoted to historical-inventory 2026-05-28 (research-inventory artifact).** As of 2026-05-28, active production-stealth code paths in the codebase were: (a) src/search/browser.py — JS_FINGERPRINT_PATCHES (screen-dimensions, devicePixelRatio, getComputedStyle CSS Color-Patch), REAL_USER_AGENT override, Chrome anti-detection flags (--disable-blink-features=AutomationControlled, webrtc_leak_protection) — applied per tab via apply_fingerprint_patches(); (b) src/scraper/scrape_url.py Phase-2 fallback — BrowserConfig(enable_stealth=True) + UndetectedAdapter. The remainder of this file is cross-layer detection-knowledge inventory and historical engine-status snapshots (pre-engine-cut 2026-04 SearXNG stack, Brave drop-decision). Kept as research reference.

Applies to: `src/search/` (pydoll-based custom engine) + `dev/search_pipeline/` (test suite)

## Detection Layers — Overview

| # | Layer | What is checked | Our knobs | Status |
|---|-------|-------------------|----------------------|--------|
| 1 | **Browser Fingerprint** | webdriver flag, WebGL vendor/renderer, Canvas hash, navigator.plugins, chrome.runtime, screen dimensions, Permissions API, CSS media queries | screen/DPR/outer/css JS patches, `disable_blink_features=AutomationControlled` | 4/4 active patches ON. WebGL, Canvas, chrome.runtime, navigator.plugins not implemented |
| 2 | **Behavioral** | Request timing, missing mouse movement/scrolling, click patterns | `humanize_click`, `humanize_type`, `humanize_scroll` | All OFF |
| 3 | **Session Tracking** | Cookie tracking across queries, cookie walls | SOCS consent cookie via CDP per tab, `use_context` | SOCS ON, use_context OFF |
| 4 | **IP Reputation** | Datacenter IPs, VPN/Tor exit nodes, proxy lists | `proxy` per engine | Direct only. No proxy. |
| 5 | **Rate Limiting** | X requests/window per IP | `delay_between_queries` | 0 — no delay (deliberate) |
| 6 | **TLS/HTTP Fingerprint** | JA3 hash, HTTP/2 frame order, header order | Not controllable — Chrome is Chrome | OK (Chrome TLS is real) |
| 7 | **CAPTCHA** | PoW (Brave), reCAPTCHA, hCaptcha | `captcha_path` URL detection | Detect-only, no solving |

## Knob Inventory

### Global (config.yml + 01_google_smoke.py)

| Knob | Layer | Default (baseline) | Effect |
|---------------|-------|--------------------|--------|
| `disable_blink_features: AutomationControlled` | 1 | ON ✅ | Removes `navigator.webdriver=true` |
| `js_patches.screen_dimensions` | 1 | ON ✅ | Overrides screen.width/height/availWidth/availHeight/colorDepth/pixelDepth |
| `js_patches.device_pixel_ratio` | 1 | ON ✅ | Sets window.devicePixelRatio = 2 |
| `js_patches.outer_dimensions` | 1 | ON ✅ | Overrides window.outerWidth/outerHeight |
| `js_patches.css_active_text` | 1 | ON ✅ | getComputedStyle proxy — masks headless CSS color leak |
| `webrtc_leak_protection` | 1/4 | ON ✅ | Prevents IP leak via WebRTC |
| WebGL vendor override | 1 | OFF ❌ | WebGL vendor/renderer override (Apple M1 Pro) |
| Canvas noise | 1 | OFF ❌ | Subtle canvas fingerprint randomization |
| Permissions override | 1 | OFF ❌ | Permissions.query override for notifications |
| chrome.runtime masking | 1 | NOT IMPLEMENTED | chrome.runtime object spoofing |
| navigator.plugins spoofing | 1 | NOT IMPLEMENTED | Fake plugin list for headless |
| `block_popups` | 2 | ON ✅ | Blocks pop-ups (no behavioral signal) |
| `block_notifications` | 2 | ON ✅ | Blocks notification requests |
| `humanize_click` | 2 | NOT IMPLEMENTED | Human-like click patterns |
| `humanize_type` | 2 | NOT IMPLEMENTED | Human-like typing |
| `humanize_scroll` | 2 | NOT IMPLEMENTED | Scroll with easing/jitter |
| SOCS consent cookie | 3 | ON ✅ | CDP NetworkCommands.set_cookie per tab — bypasses Google cookie wall |
| `use_context` | 3 | OFF ❌ | Fresh browser context per query (cookie isolation) |
| `delay_between_queries` | 5 | 0 ❌ | Pause between queries — 0 = no delay (deliberate) — break at ~90 queries/10min back-to-back → [Layer 5](#layer-5-rate-limiting) Batch 1 |
| `page_load_timeout` | 5 | 20s | Max navigation wait time |

### Per-Engine (in config.yml google section)

| Knob | Layer | Effect |
|---------------|-------|--------|
| `proxy` | 4 | None (direct) — no proxy configured |
| `consent_cookie` | 3 | SOCS cookie + fallback consent_buttons for Google |
| `wait_for_results` | 2/5 | Max 15 cycles × 1s — no aggressive polling |
| `consent_settle` | 2 | 2s settle after consent handling |

## Engine Status

### Stress Test 2026-04-07 (Legacy — 9-Engine SearXNG Stack)

| Engine | Score | Main Problem | Detection Layer | Routing |
|--------|-------|-------------|-----------------|---------|
| Google | 30/30 ✅ | — | — | direct, consent_cookie |
| Bing | 30/30 ✅ | — | — | direct |
| CrossRef | 30/30 ✅ | — | — | httpx API |
| Mojeek | 15/30 ⚠️ | Block from query 16 | Rate-limiting (IP) | direct |
| DuckDuckGo | 6/30 ⚠️ | Bing redirect | Package bug (ddgs) | httpx |
| Brave | 1/30 ❌ | PoW CAPTCHA from query 2 | Fingerprint + rate-limiting | direct (Tor = 0/30) |
| Startpage | 0/30 ❌ | Zero results, no error | Unclear | direct |
| Google Scholar | 0/0 ❌ | Engine crash | Unclear | direct |
| Semantic Scholar | 3/30 ❌ | 429 rate-limit | Rate-limiting (API) | httpx API |

### New Baseline 2026-04-21 (pydoll custom stack, single-engine)

| Engine | Score | Stack | Config |
|--------|-------|-------|--------|
| Google | 30/30 ✅ | headless pydoll Chrome, SOCS cookie, 4 JS patches | `dev/search_pipeline/config.yml` + `01_google_smoke.py` |

This run was the reference baseline at the time. (Report deleted, see git history at 1ad627f.)

## Dropped Engines — Final Verdict

| Engine | Score | Reason |
|--------|-------|-------|
| Brave | 1–10/30 | PoW CAPTCHA, no combination reached 30/30 — see rationale below |
| Startpage | 0/30 | Zero results, root cause unclear |
| DuckDuckGo | 6/30 | Redirect to Bing via ddgs bug |
| Mojeek | 15/30 | IP-based rate-limit (15 req/60s, not bypassable) |
| Semantic Scholar | 3/30 | 429 rate-limit (API) |

**Survivor set (active in `src/search/`):** ~~Google, Bing, Google Scholar, CrossRef~~ — **historical, pre-engine-expansion**.

**As of 2026-05-04:** 8 active engines in a uniform 4 req/min rate-limit pool — Google, DuckDuckGo, Mojeek, Lobsters (browser via pydoll); Google Scholar (browser, JS fix 2026-05-04); CrossRef, OpenAlex, Stack Exchange (HTTP API). Bing: src/search/engines/bing.py deleted 2026-05-04 (DOM-drift, no added value over DDG). HN dropped 2026-05-04 (rate-limit-cascade-hostile).

**Update 2026-05-09:** Google Scholar browser → HTTP migration. Scholar excluded from `_DEFAULT_ENGINES` due to Google co-fire decoupling — dormant in default queries until pooling-rework. Plus Semantic Scholar (browser, added 2026-05-07) and Open Library (HTTP, 2026-05-08). Engine set at that point: 9 engines (Google, DDG, Mojeek, Lobsters, SemScholar via browser; CrossRef, OpenAlex, StackExchange, Open Library via HTTP).

### Brave — Drop Decision & Rationale

**Decision: Brave is dropped.**

Core reason: All CAPTCHA solutions (waiting, click-solving, API) are incompatible with the `asyncio.gather` parallel-engine architecture in `src/search/search_web.py`. Google delivers in ~0.2s. A Brave CAPTCHA generates 10–15s minimum latency per query — makes the entire search response unusable.

Tested and rejected:
- Stealth patch matrix (8 combinations, best: WebGL +7 → 10/30) — table in [Layer 1: Browser Fingerprint](#layer-1-browser-fingerprint)
- Patchright with Chromium binary → slider CAPTCHA instead of PoW, 0/30
- Camoufox (Firefox, headless) → 7/30
- PoW reverse-engineering (Argon2 + Privacy Pass VOPRF) — solvable, but latency problem remains
- Brave Search API (2K/month free) — no CAPTCHA, but latency-architecture problem remains

### How Brave Work Could Be Resumed

Prerequisites for resume:
1. Solve the architecture problem: take Brave out of `asyncio.gather` (own timeout, fallback to remaining 3 engines)
2. Test Patchright with real Chrome binary (`patchright install chrome` + `channel="chrome"` + `headless=True`) — never correctly tested
3. Alternatively: evaluate Brave Search API

## Referenced Files

- `dev/search_pipeline/01_google_smoke.py` — baseline implementation
- `dev/search_pipeline/config.yml` — baseline config
- dev/search_pipeline/01_reports/smoke_20260421_022343.md (deleted, see git 1ad627f) — 30/30 baseline run
- dev/search_pipeline/01_reports/smoke_20260421_182917.md (deleted, see git 1ad627f) — 28/30 re-verify run

---

## Layer 1: Browser Fingerprint

### Status Quo

#### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**ON:**
- `--disable-blink-features=AutomationControlled` — removes the `navigator.webdriver=true` flag
- `screen_dimensions` patch — overrides `screen.width/height/availWidth/availHeight/colorDepth/pixelDepth` (1920×1080, colorDepth=30)
- `device_pixel_ratio` patch — sets `window.devicePixelRatio = 2`
- `outer_dimensions` patch — sets `window.outerWidth = innerWidth`, `window.outerHeight = innerHeight + 85`
- `css_active_text` patch — `getComputedStyle` proxy masks the headless-typical CSS color value (rgb(255,0,0) → rgb(0,102,204))
- User-Agent: Chrome 147 via `--user-agent=` CLI argument
- `webrtc_leak_protection: true` (pydoll attribute)
- All 4 JS patches via `PageCommands.add_script_to_evaluate_on_new_document` — injected both at browser start (initial tab) and per new tab in `run_query()`

**OFF:**
- `patch_webgl` — WebGL vendor/renderer override not configured
- `patch_canvas_noise` — canvas fingerprint randomization not configured
- `patch_permissions` — Permissions.query override not configured

**NOT IMPLEMENTED:**
- chrome.runtime object masking (no `window.chrome.runtime` spoof)
- navigator.plugins spoofing (empty plugin list in headless remains visible)
- navigator.userAgentData brands override (`Chromium` vs `Google Chrome`)

#### Detection Surface

What Layer 1 checks:

| Signal | What is detected | Our control |
|--------|-----------------|---------------|
| `navigator.webdriver` | `true` in headless | ✅ AutomationControlled removes it |
| Screen dimensions | `screen.width/height = 0` in headless | ✅ Patched to 1920×1080 |
| devicePixelRatio | 1.0 in headless (instead of 2.0 on Retina) | ✅ Patched to 2 |
| outerWidth/outerHeight | Missing titlebar offset | ✅ Patched +85px outer height |
| CSS active text color | rgb(255,0,0) headless artifact | ✅ Proxy patch |
| WebGL vendor/renderer | `Google SwiftShader` = strong headless signal | ❌ no patch |
| Canvas hash | Deterministic in headless | ❌ no noise |
| navigator.plugins | Empty in headless | ❌ no spoof |
| chrome.runtime | Missing in headless | ❌ no masking |
| Permissions API | `.query({name:'notifications'})` returns `denied` immediately | ❌ no override |
| Error.stack CDP trap | pydoll: `CDP Runtime.enable` detectable via Error.stack getter | ❌ not fixed |
| navigator.userAgentData | `brands: ["Chromium"]` instead of `["Google Chrome"]` | ❌ no override |

### Evidence

#### Brave Stealth Patch Matrix (2026-04-09)

| Stack / Patch | X/30 | First Failure | Delta vs Baseline |
|---------------|------|---------------|-------------------|
| pydoll baseline (settle=0.0, proxy=None) | 3/30 | Query 3 | — |
| pydoll + patch_webgl=True | 10/30 | Query 11 | +7 |
| pydoll + patch_canvas_noise=True | 6/30 | Query 7 | +3 |
| pydoll + patch_permissions=True | 0/30 | Query 1 | -3 (counterproductive) |
| pydoll + chrome.runtime + navigator.plugins | 0/30 | Query 1 | -3 (counterproductive) |
| pydoll + all patches combined | 0/30 | Query 1 | -3 (bad patches dominate) |
| Patchright (Chromium binary) | 0/30 | Query 1 | -3 (slider CAPTCHA instead of PoW) |
| Camoufox (Firefox, headless) | 7/30 | Query 8 | +4 |

Finding: WebGL fingerprint is the strongest single signal. Permissions and plugin patches are counterproductive for Brave — Brave detects JS overrides of these APIs directly.

#### Brave Detection Signals (2026-04-09, reverse engineering)

- CDP `Runtime.enable` + `Error.stack` getter trap — affects pydoll, Patchright fixes it
- `navigator.userAgentData.brands`: `"Chromium"` instead of `"Google Chrome"` (affects Patchright with Chromium binary)
- `__playwright_evaluation_script__` in `Function.prototype.toString`
- `navigator.webdriver = true`
- WebGL SwiftShader renderer (strong signal — WebGL patch gives +7)
- `navigator.brave.isBrave` missing (soft signal)

#### puppeteer-extra-plugin-stealth Comparison (2026-04-07)

Missing patches vs. puppeteer-extra:
- chrome.runtime masking — implemented subsequently, counterproductive for Brave (0/30)
- navigator.plugins spoofing — implemented subsequently, counterproductive for Brave (0/30)

Finding: patches that beat Brave with Puppeteer are ineffective or harmful with pydoll — presumably because pydoll has additional CDP-leak signals.

### Recommendation

Pending — to be determined by stress-test iterations. Current baseline reaches 30/30 (Google, Run 1, no load). Recommendation to be refined after the first break.

Candidates for the next iteration (after stress break):
- WebGL patch (gives +7 with Brave — to be tested whether neutral or positive with Google)
- Canvas noise (gives +3 with Brave — test alongside)
- **NOT** permissions/plugins/chrome.runtime (counterproductive with Brave, unclear with Google)

### Open Questions

- Brave: are JS overrides of Permissions/plugins detected directly via CDP or via behavioral deviation?
- Brave: Patchright with real Chrome binary (not Chromium) — never correctly tested (`patchright install chrome` + `channel="chrome"`)
- Google: does the WebGL patch behave neutrally or positively on 30/30 runs? (Brave evidence shows +7, Google might react differently)
- navigator.userAgentData override: pydoll capability unclear — CDP `Emulation.setUserAgentOverride` with `userAgentMetadata` would be the path

---

## Layer 2: Behavioral

### Status Quo

#### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**ON:**
- `block_popups: true` — blocks pop-up windows (reduces unexpected interactions)
- `block_notifications: true` — blocks notification-permission dialogs

**OFF / NOT IMPLEMENTED:**
- No mouse movement between queries
- No scroll simulation
- No humanized click pattern
- No typing (no form interaction — navigation directly via URL)
- `delay_between_queries: 0` — no delay (timing signal present, see Layer 5)
- `consent_settle: 2.0` — only wait, only during consent handling

The baseline stack navigates exclusively via `tab.go_to(url)` — no DOM interaction except during the consent fallback (`btn.click()`). There are no humanized behavioral signals.

#### Detection Surface

What Layer 2 checks:

| Signal | What is detected | Our control |
|--------|-----------------|---------------|
| Request timing | Too fast, too regular — bot-typical | ❌ 0 delay between queries |
| Mouse movement | Completely missing | ❌ not implemented |
| Scroll behavior | Missing | ❌ not implemented |
| Click pattern | Too precise / instant (no human jitter) | ❌ on consent-button click |
| Tab activity | New tabs open/close without idle | ⚠️ new tab per query, navigates immediately |

### Evidence

No quantitative behavioral tests conducted. Baseline 30/30 with everything OFF confirms that Google does not actively block on Layer 2 at moderate traffic.

### Recommendation

Pending — to be determined by stress-test iterations. Only once a stress break occurs and Layer 5 (rate-limiting) is ruled out is behavioral the next candidate.

### Open Questions

- Google: does behavioral detection begin only at high traffic (>100 queries per session) or earlier?
- Is the 0-delay effect Layer 2 (timing) or Layer 5 (rate-limit) — presumably Layer 5 for IP-blocking, Layer 2 for session-score increase

---

## Layer 3: Session Tracking

### Status Quo

#### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**SOCS Cookie Injection:**
- `config.yml` defines: `consent_cookie: {name: SOCS, value: "CAISHAgCEhJnd3NfMjAyNjA0MDctMCAgIBgEIAEaBgiA_fC8Bg", domain: ".google.com", path: "/", secure: true}`
- Cookie is injected per tab via `NetworkCommands.set_cookie` (CDP `Network.setCookie`) with `same_site=CookieSameSite.LAX`
- Injection happens TWICE:
  1. At browser start in `start_browser()` — the initial tab gets the cookie
  2. Per query in `run_query()` via `_inject_consent_cookie(tab, cfg)` — each new tab gets the cookie
- Effect: Google's cookie wall (consent.google.com redirect + inline consent) is fully bypassed

**use_context: OFF:**
- No fresh browser context per query
- All queries run in the same Chrome profile context (`--user-data-dir=~/.searxng-mcp/browser-session-smoke`)
- Cookies accumulate across the session — no cookie isolation between queries

**Consent Fallback:**
- `_has_inline_consent()` detects inline consent via `'Before you continue'` in body text
- `_handle_consent()` clicks the first matching button from the `consent_buttons` fallback chain
- After consent: 2s settle + re-navigation to the search URL

#### Detection Surface

What Layer 3 checks:

| Signal | What is detected | Our control |
|--------|-----------------|---------------|
| Cookie wall (redirect) | Redirect to consent.google.com | ✅ bypassed via SOCS cookie |
| Inline consent banner | `'Before you continue'` on search URL | ✅ cookie + fallback click |
| Session accumulation | Same session cookies across 30 queries | ⚠️ no use_context — cookies accumulate |
| Cookie fingerprint | SOCS value is fixed — same value on every start | ⚠️ unclear whether Google rotates SOCS |

### Evidence

- SOCS cookie bypass: stress test 2026-04-07 + new baseline 2026-04-21 — both 30/30, not a single CONSENT status
- Brave: no SOCS problem (Brave doesn't use Google's cookie system), but use_context=OFF was active → contributed to session-tracking? Unclear

### Recommendation

Pending — to be determined by stress-test iterations. Current baseline shows the SOCS cookie is sufficient for 30/30 without consent blocking.

### Open Questions

- Brave: does Brave track per IP or per session? `use_context=True` would break session-tracking, not IP-tracking — relevant if Brave work resumes
- SOCS value: does the cookie expire? (format `gws_20260407-0` — date-based?) Does it need periodic renewal?
- Google Scholar: needs its own consent cookie (different domain)? (Scholar engine in src/ — not in the smoke stack)

---

## Layer 4: IP Reputation

### Status Quo

#### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**Direct Connection:**
- No proxy configured
- Requests run over the local IP (Mac developer IP, home network or office network)
- `webrtc_leak_protection: true` — prevents WebRTC-based IP leaks (local IP via STUN)

**No Proxy Support Implemented:**
- `config.yml` has no `proxy` key
- pydoll options have no `proxy` argument in the current smoke implementation

#### Detection Surface

What Layer 4 checks:

| Signal | What is detected | Our control |
|--------|-----------------|---------------|
| Datacenter IP | ASN classification (AWS, GCP, DigitalOcean) | ✅ home-network IP uncritical |
| VPN IP | Known VPN-provider ASNs | ⚠️ unclear (depends on network) |
| Tor exit node | Public Tor exit-node lists | ❌ Tor listed (0/30 Brave with Tor) |
| Proxy lists | Known commercial proxy IPs | ❌ no proxy |
| IP rotation | No rotation between queries | ❌ same IP for all 30 queries |

### Evidence

#### Tor Exit-Node Blocking (2026-04-07)

- Brave with Tor proxy: 0/30 (all Tor exit nodes on blocklist)
- Brave without proxy (direct): 1/30 — shows Layer 4 is more active for Brave than for Google

#### Google IP Tolerance

- Google 30/30 with direct IP confirmed (2026-04-07 + 2026-04-21)
- Google appears not to raise IP-reputation problems on home/office IPs at this query rate

### Recommendation

Pending — currently no problem for Google. Across multiple stress-test runs (IP accumulation), IP-based blocking could kick in.

Residential proxies would be the ideal solution for IP rotation but are not available.

### Open Questions

- Residential proxies: not available — would be optimal IP rotation (not detectable as datacenter/VPN)
- Google: at what query rate / time window does IP-based blocking begin? (not yet stress-tested)
- Multiple back-to-back runs: do IP signals accumulate across runs, or does Google reset after a certain idle interval?

---

## Layer 5: Rate Limiting

### Status Quo

#### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**`delay_between_queries: 0`** — no delay between queries.

Rationale: the 2026-04-07 baseline ran with 0 delay and delivered 30/30. A 10s delay was added 2026-04-16 as a defensive value — without evidence it was needed. In the new smoke stack it was reset to 0.

**`page_load_timeout: 20`** — maximum wait time per navigation.

**`consent_settle: 2.0`** — 2s settle only during consent handling (not between normal queries).

**`wait_for_results.max_cycles: 15`, `interval_seconds: 1.0`** — up to 15 seconds waiting for DOM results per query.

Effective timing per query: navigation (~1–2s) + DOM-wait (0–15s, typically 1–2s) + tab open/close (~0.1s). No explicit delay in between.

Full 30-query run: ~2.5 minutes (from baseline report `smoke_20260421_022343.md`).

#### Detection Surface

What Layer 5 checks:

| Signal | What is detected | Our control |
|--------|-----------------|---------------|
| X requests/window (IP) | Rate > threshold → 429 / redirect to /sorry/ | ❌ no delay — rate is high |
| Request pattern | Too regular (no jitter) | ❌ natural jitter varies via DOM-wait |
| Burst detection | Many requests in short time | ❌ 30 queries in ~2.5min = ~12 req/min |

### Evidence

#### Mojeek Rate Limit (2026-04-09)

- Exactly 15 requests per ~60s sliding window
- From request 16: HTTP 403 "automated queries"
- IP-based — `use_context` (browser rotation) doesn't help
- Independent of query language

#### Google Rate Tolerance (2026-04-07 + 2026-04-21)

- 30/30 with 0 delay in ~2.5min — no rate-limit
- Google appears not to trigger blocking at 12 req/min (with real DOM-wait jitter)
- Stress-test back-to-back Batch 1 conducted 2026-04-22 → see subsection below

#### Google Back-to-Back Stress Batch 1 (2026-04-22)

| Run# | OK | Non-OK | First-Fail-Idx | Nav ms mean/max |
|------|-----|--------|----------------|-----------------|
| 1 | 30/30 | — | — | 520 / 887 |
| 2 | 27/30 | 3× CAPTCHA | Q26 | 422 / 701 |
| 3 | 28/30 | 2× CAPTCHA | Q11 | 345 / 664 |
| 4 | 0/30 | 30× CAPTCHA | Q1 | 537 / 661 |

**Threshold:** hard IP-block after ~90 queries / ~10 minutes across 4 consecutive runs without cooldown.

**Layer attribution: IP-level (Layer 5), NOT fingerprint (Layer 1–3).**

Evidence for IP-block (not fingerprint-detection):
- Run 4 nav-mean 537ms (stable, identical to runs 1–3) — Google serves /sorry/ immediately, no fingerprint scan
- DOM-wait 0ms in run 4 — no DOM processing, immediate redirect
- /sorry/ starts at Q1 in run 4 — no query-specific trigger, full IP block
- Runs 1–3 show normal nav times (345–520ms mean) — fingerprint patches untouched

**Reference:** dev/search_pipeline/01_reports/stress_20260422_012755.md (deleted, see git 1ad627f)

### Recommendation

**Change:** `delay_between_queries: 0 → uniform(12, 18)` in `dev/search_pipeline/config.yml` and analogously `src/search/rate_limiter.py` token bucket to ~4 req/min.

Rationale:
- Empirically (Batch 1, 2026-04-22): 12 req/min breaks after ~90 cumulative queries. Threshold is not instantaneous-rate-based but a cumulative score per IP.
- Community baseline: `karust/openserp` config (active commits April 2026) defaults Google to `rate_requests: 4, rate_burst: 2` — a defensive floor well under any plausible threshold.
- 12–18s gives ~4 req/min with natural jitter. With burst tolerance (openserp `rate_burst: 2`), 2 queries can fire quickly in succession, then throttling kicks in.
- Fits the agentic-search use case (4 queries per engine × N engines → dedup): 4 queries in ~60s per engine instead of 30 queries in 2.5min.

**Stress-test protocol (retained):** for future layer experiments — back-to-back runs without cooldown on a DIFFERENT IP context than a library NAT. Shared-IP scraping distorts both the baseline (other users affect the score) and is ethically questionable (others suffer from our CAPTCHAs).

### Open Questions

- Google: where is the actual rate-limit threshold? → answered 2026-04-22: ~90 queries / 10min back-to-back (Batch 1 break)
- Jitter via DOM-wait: does the natural variance (1–15s per query) suffice to evade regularity detection?

---

## Layer 6: TLS/HTTP Fingerprint

### Status Quo

#### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/01_google_smoke.py`.

**Chrome TLS is real — no intervention needed or possible.**

The smoke stack uses pydoll with a real Chrome binary (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`). Chrome's TLS stack is the real browser stack — JA3 hash, HTTP/2 frame order, and header order are identical to a real Chrome user.

No httpx in this pipeline — no requests via a Python HTTP client (which would produce a different TLS fingerprint).

#### Detection Surface

What Layer 6 checks:

| Signal | What is detected | Our control |
|--------|-----------------|---------------|
| JA3 hash | TLS client-hello fingerprint | ✅ Chrome TLS is real |
| HTTP/2 frame order | SETTINGS frame, WINDOW_UPDATE frame order | ✅ Chrome HTTP/2 is real |
| Header order | User-Agent, Accept, Accept-Language order | ✅ Chrome headers are real |
| ALPN | `h2` negotiation | ✅ Chrome |
| TLS version | TLS 1.3 | ✅ Chrome |

### Evidence

TLS-fingerprint tests were conducted in legacy scripts (`20_tls_fingerprint.py`, `21_cipher_shuffle_verify.py`) — these examined the httpx stack (SearXNG-proxy era), not the pydoll-Chrome stack. For the current Chrome stack, no test is needed — Chrome cannot be faked.

### Recommendation

N/A — no action required. Chrome-based stacks are inherently inconspicuous on Layer 6. Layer 6 becomes relevant only if httpx-based engines (CrossRef, Bing via API fallback) become problematic.

### Open Questions

- None — Layer 6 is solved for Chrome-based requests.

---

## Layer 7: CAPTCHA

### Status Quo

#### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**Detect-only — no solving.**

CAPTCHA detection happens via URL check:
- `config.yml`: `captcha_path: /sorry/` — Google's CAPTCHA redirect path
- In `run_query()`: `if gc["captcha_path"] in current_url: record["status"] = "CAPTCHA"; return record`
- Record gets status `CAPTCHA` and is not processed further

No JavaScript-based solver. No click attempt. No automatic retry.

**Baseline result:** 30/30 run 2026-04-21 without a single CAPTCHA status. Google appears to activate CAPTCHA (`/sorry/`) only at significantly higher traffic.

#### Detection Surface

What Layer 7 is:

| CAPTCHA Type | Engine | Mechanism | Our Status |
|-------------|--------|-------------|--------------|
| reCAPTCHA (/sorry/) | Google | Rate-based redirect after fingerprint suspicion | ✅ detected via URL check |
| PoW CAPTCHA (Argon2) | Brave | Proof-of-work challenge in browser | ✅ detected — not solvable |
| Slider CAPTCHA | Brave (Patchright) | Drag-slider interaction | ✅ detected — not solvable |
| hCaptcha | Various | Challenge-response | ❌ no selector configured |

### Evidence

#### Brave PoW CAPTCHA (2026-04-07)

- Screenshot: "Confirm you're a human being / I'm not a robot" dialog with "Learn more about Proof of Work Captcha"
- Svelte-based CAPTCHA — PoW (proof of work) challenge, no slider
- Occurs from query 2–3 onward (query 1 delivers results)
- With Tor proxy: 0/30 (Tor exit nodes on blocklist → immediate CAPTCHA)

#### Brave PoW Technical Analysis (2026-04-09)

- Algorithm: Argon2 (memory-hard hash) via WASM, computed in a Web Worker
- Challenge parameters: `zero_count=1` (trivial), 21 tokens, `iterations=2`, `memory_size=512KB`
- Privacy Pass: VOPRF protocol (blind tokens) in a separate WASM module
- API endpoint: POST `/api/captcha/pow?brave=0` with solutions + blinded_messages
- Server responds with `signed_tokens` → cookie → access
- Click on "I'm not a robot": spinner "Letting you in..." appears, after 3s no redirect — unclear whether computation was too slow or the server rejected due to fingerprint

**Two CAPTCHA tiers:**
- `PoW ("I'm not a robot")` — for Chrome/pydoll
- `Slider ("Drag the slider")` — for Patchright/Chromium

#### captcha_detect_js Bug (Legacy)

The old legacy stress-test stack had a `captcha_detect_js` JavaScript configured with selector `dialog .captcha-card`. This selector did not match the actual Brave CAPTCHA DOM. The correct selector would be `[class*="pow-captcha"]` or a title check for "Captcha". Not relevant in the new smoke stack (no JS selector for CAPTCHA — only URL check).

### Recommendation

Pending — to be determined by stress-test iterations. Google CAPTCHA occurs only at high traffic — currently not a problem.

**Brave CAPTCHA options (if Brave resumes):**
1. Click + wait longer (10–15s) — unclear whether Argon2 computation completes
2. Solve Argon2 PoW programmatically — technically possible, Privacy Pass VOPRF part is the blocker
3. Brave Search API (2K queries/month free) — no CAPTCHA, but architecture problem remains (see [Engine Status](#engine-status))

### Open Questions

- Brave: CAPTCHA click with 10–15s wait — is that enough time for PoW computation + API call? Or does the server reject due to fingerprint?
- Brave: is the CAPTCHA solvable per session or per IP? (is a click-solution persistent for the session?)
- Google: at what traffic level does `/sorry/` activate? (stress-test finding pending)
