# Search Pipeline Step 2: Routing & Proxy

> **⚠️ Superseded (2026-04-15 engine-cut):** This file documents the SearXNG-Docker Tor-routing architecture. That stack (src/searxng/, Docker Tor container, SearXNG suspension times) was removed in the engine-cut. Current architecture uses pydoll Chrome + httpx with no proxy — all engines run direct. Rate-limiting is a token-bucket in `src/search/rate_limiter.py`, not SearXNG suspension times.

## Status Quo (Historical, pre-engine-cut)

**Code:** src/searxng/settings.yml (deleted 2026-04-15) — `outgoing` + per-Engine `proxies`/`using_tor_proxy`
**Method:** Split routing: Tor by default, direct exceptions for engines that block Tor exit nodes

### Global Tor Default

```yaml
outgoing:
  request_timeout: 5.0
  max_request_timeout: 15.0
  proxies:
    all://:
      - socks5h://tor:9150
  using_tor_proxy: true
  extra_proxy_timeout: 10
```

### Per-Engine Routing

**DIRECT (Tor bypass via `proxies: {}` + `using_tor_proxy: false`):**

| Engine | Category | Reason |
|--------|-----------|-------|
| Google | general | Blocks Tor exit nodes (CAPTCHA/403) |
| Bing | general | Blocks Tor exit nodes like Google |
| DuckDuckGo | general | Blocks Tor exit nodes (Bing backend) |
| Mojeek | general | Smaller engine, Tor exit nodes presumably blocked |

**TOR (inherits global default — no override needed):**

| Engine | Category | Reason |
|--------|-----------|-------|
| Brave | general | Tolerates Tor, benefits from IP rotation |
| Startpage | general | Google proxy over Tor, IP rotation |
| Google Scholar | general | API endpoint, less Tor-blocking than consumer Google |
| Semantic Scholar | general | API-based, no known Tor blocking |
| CrossRef | general | API-based, no Tor blocking |
| ArXiv | plugin | API-based, no Tor blocking |
| GitHub | plugin | API-based |
| Reddit | plugin | Scraper, Tor compatibility untested |

### Suspension Times

| Error Type | Suspension |
|-----------|-----------|
| SearxEngineAccessDenied | 600s (10 min) |
| SearxEngineCaptcha | 600s (10 min) |
| SearxEngineTooManyRequests | 300s (5 min) |
| cf_SearxEngineCaptcha (Cloudflare) | 1800s (30 min) |
| cf_SearxEngineAccessDenied | 600s (10 min) |
| recaptcha_SearxEngineCaptcha | 3600s (60 min) |

### Timeout Cascade

- `request_timeout: 5.0` — normal engine timeout
- `max_request_timeout: 15.0` — absolute maximum
- `extra_proxy_timeout: 10` — additional buffer for Tor latency
- `timeout: 10` on Google Scholar — Scholar-specific override

## Evidence

### Tor Exit Nodes — Aggressive Blocking
Google, Bing, DuckDuckGo, and likely Mojeek reliably block known Tor exit nodes with CAPTCHA or immediate 403. Direct connection is the only working option. Per-engine `proxies: {}` and `using_tor_proxy: false` override the global Tor default.

**CRITICAL:** Both fields must be set. `using_tor_proxy: false` alone only disables Tor verification, not the proxy. `proxies` is inherited from `outgoing.proxies` independent of `using_tor_proxy` (SearXNG network.py initialize function).

### Brave + Startpage — Tor Benefit
Brave and Startpage do not block Tor exit nodes. Tor routing provides IP rotation under rate-limiting and prevents session tracking across queries.

### API Engines — Tor Unproblematic
Semantic Scholar, CrossRef, ArXiv, and GitHub use official APIs. These generally do not block Tor exit nodes, as they are designed for programmatic access. Tor provides additional anonymity protection here without downside.

### Reddit — Untested
The Reddit engine is a scraper (not API). Tor compatibility needed empirical testing. Fallback: `proxies: {}` + `using_tor_proxy: false` if Tor blocking occurs.

### extra_proxy_timeout
Tor routing adds ~1-3s latency per hop. `extra_proxy_timeout: 10` extends the effective timeout for Tor engines without raising the normal `request_timeout`.

### Suspension Times — Cloudflare Special Handling
Cloudflare-protected sites have more aggressive rate-limiting. 1800s (30 min) for `cf_SearxEngineCaptcha` prevents repeated triggering. recaptcha = hardest blocker → 3600s.

## Decision

Split-routing architecture: **Tor by default, direct exceptions.** Rationale:
- Global Tor default protects all engines with IP rotation without per-engine config
- Targeted bypass for 4 engines (Google, Bing, DDG, Mojeek) that block Tor
- API-based engines (Scholar, Semantic Scholar, CrossRef, ArXiv, GitHub) benefit from Tor with no downside
- Reddit engine as scraper still untested — switch to DIRECT if problems arise
- Tor container runs as a Docker service (`tor:9150`), no external dependency

## Open Questions

- Reddit via Tor: empirically test whether the Reddit scraper works over Tor
- Google Scholar via Tor: not explicitly tested whether Scholar blocks Tor exit nodes
- Startpage via Tor: Startpage is a Google proxy — unclear whether Google blocks propagate through
- Mojeek Tor: ASSUMPTION that Tor is blocked (not verified). Test if needed.
- Tor container failover: no fallback if the Tor container is down — all Tor engines fail simultaneously

## Sources

- src/searxng/settings.yml (deleted 2026-04-15) — routing configuration
- `searxng/searxng` GitHub Repo (`searx/network.py`) — proxy inheritance logic
- SearXNG Docs (RAG Collection: searxng) — outgoing, proxy, suspended_times parameters
- engine selection and category assignment rationale (search pipeline)

## Implemented (Session 2026-04-03)

### Engine Suspension Disabled

All `suspended_times` values and `ban_time_on_fail` set to `0`.

**Rationale:** SearXNG's internal suspension system was counterproductive. When an engine gets rate-limited, SearXNG additionally suspends it for 300–3600 seconds — double penalty:
1. Engine is already temporarily blocked (Google-side 403, Tor blocking, etc.)
2. SearXNG suspension prevents recovery without a Docker restart

Engines are meant to handle their own rate-limiting logic. SearXNG does not intervene.

**Configuration in `settings.yml`:**
```yaml
search:
  suspended_times:
    SearxEngineAccessDenied: 0
    SearxEngineCaptcha: 0
    SearxEngineTooManyRequests: 0
    cf_SearxEngineCaptcha: 0
    cf_SearxEngineAccessDenied: 0
    recaptcha_SearxEngineCaptcha: 0
  ban_time_on_fail: 0
```

### SearXNG 2026.4.3 — GSA iPhone UA Fix

Update from 2026.3.10 → 2026.4.3 fixed blocking for Google, Brave, Google Scholar via a new GSA iPhone User-Agent. These 3 engines delivered stable results again afterward.

### TLS Fingerprint Investigation

Scripts `20_tls_fingerprint.py` + `21_cipher_shuffle_verify.py` developed (legacy — from the SearXNG proxy stack, since deleted).

**Results:**
- JA3 Hash: `cdb8399d0ce47cc19f2ef0756148891e` (measured via tls.browserleaks.com)
- Cipher shuffling effective: 12/12 requests produced distinct JA3 hashes ✓
- Gap identified: `Accept: */*` header missing from SearXNG requests (not an immediate blocking cause)

### Mojeek Patch — .pyc Cache Lesson

Mojeek patch (src/searxng/patches/mojeek.py, deleted 2026-04-15) had a stale `.pyc` cache in the Docker container — the updated patch was ignored.

**Fix:** `docker compose build --no-cache` clears `.pyc` files and forces recompilation.

**Lesson:** Docker volume-mounted patches can be ignored due to stale `.pyc`. Always rebuild the container on patch updates.

**Fix:** `arc=none` hardcoded (instead of `arc=us` from the default engine) — resolved bot detection.

### Semantic Scholar — Direct Routing + Session Cookies

Semantic Scholar switched from Tor to DIRECT (`proxies: {}` + `using_tor_proxy: false`). Session-cookie tracking is incompatible with Tor IP rotation.

**Patch:** src/searxng/patches/semantic_scholar.py (deleted 2026-04-15) — cookies (`s2Exp`, `tid`) were cached for 300s and resent on subsequent requests.

**Limitation:** Soft limit ~6 requests/session. After ~6 queries, Semantic Scholar returned 0 results. No hard block — recovery via SearXNG restart or session rotation.

## Resolved Open Questions (2026-04-03)

- ✅ **Google Scholar via Tor:** Scholar functional again via SearXNG 2026.4.3; runs direct (no Tor)
- ✅ **Mojeek Tor:** Mojeek stable over direct connection with the arc=none patch
- ✅ **Startpage via Tor:** Worked stably over Tor after the SearXNG 2026.4.3 update
- ⏳ **Reddit via Tor:** Still open — not tested
- ⏳ **Tor container failover:** Still open — no fallback implemented
