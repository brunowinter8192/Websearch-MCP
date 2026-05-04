# Stealth: Engine Status & Overview

Applies to: `src/search/` (pydoll-based custom engine) + `dev/search_pipeline/` (test suite)

Per-layer detail: [stealth01_fingerprint.md](stealth01_fingerprint.md) · [stealth02_behavioral.md](stealth02_behavioral.md) · [stealth03_session.md](stealth03_session.md) · [stealth04_ip_reputation.md](stealth04_ip_reputation.md) · [stealth05_rate_limiting.md](stealth05_rate_limiting.md) · [stealth06_tls_http.md](stealth06_tls_http.md) · [stealth07_captcha.md](stealth07_captcha.md)

## Detection Layers — Overview

| # | Ebene | Was geprüft wird | Unsere Stellschrauben | Status |
|---|-------|-------------------|----------------------|--------|
| 1 | **Browser-Fingerprint** | webdriver-Flag, WebGL vendor/renderer, Canvas Hash, navigator.plugins, chrome.runtime, Screen-Dimensionen, Permissions API, CSS media queries | screen/DPR/outer/css JS-Patches, `disable_blink_features=AutomationControlled` | 4/4 aktive Patches ON. WebGL, Canvas, chrome.runtime, navigator.plugins nicht implementiert |
| 2 | **Behavioral** | Request-Timing, fehlende Mausbewegung/Scrolling, Klick-Muster | `humanize_click`, `humanize_type`, `humanize_scroll` | Alle OFF |
| 3 | **Session-Tracking** | Cookie-Tracking über Queries, Cookie-Walls | SOCS consent cookie via CDP per Tab, `use_context` | SOCS ON, use_context OFF |
| 4 | **IP-Reputation** | Datacenter-IPs, VPN/Tor Exit-Nodes, Proxy-Listen | `proxy` per Engine | Direct only. Kein Proxy. |
| 5 | **Rate-Limiting** | X Requests/Zeitfenster pro IP | `delay_between_queries` | 0 — kein Delay (bewusst) |
| 6 | **TLS/HTTP-Fingerprint** | JA3 Hash, HTTP/2 Frame-Order, Header-Order | Nicht steuerbar — Chrome ist Chrome | OK (Chrome TLS ist real) |
| 7 | **CAPTCHA** | PoW (Brave), reCAPTCHA, hCaptcha | `captcha_path` URL-Erkennung | Detect-only, kein Solving |

## Stellschrauben-Inventar

### Global (config.yml + 01_google_smoke.py)

| Stellschraube | Ebene | Default (Baseline) | Effekt |
|---------------|-------|--------------------|--------|
| `disable_blink_features: AutomationControlled` | 1 | ON ✅ | Entfernt `navigator.webdriver=true` |
| `js_patches.screen_dimensions` | 1 | ON ✅ | screen.width/height/availWidth/availHeight/colorDepth/pixelDepth Override |
| `js_patches.device_pixel_ratio` | 1 | ON ✅ | window.devicePixelRatio = 2 |
| `js_patches.outer_dimensions` | 1 | ON ✅ | window.outerWidth/outerHeight Override |
| `js_patches.css_active_text` | 1 | ON ✅ | getComputedStyle Proxy — headless CSS-Color-Leak maskiert |
| `webrtc_leak_protection` | 1/4 | ON ✅ | Verhindert IP-Leak via WebRTC |
| WebGL vendor override | 1 | OFF ❌ | WebGL vendor/renderer Override (Apple M1 Pro) |
| Canvas noise | 1 | OFF ❌ | Subtile Canvas-Fingerprint-Randomisierung |
| Permissions override | 1 | OFF ❌ | Permissions.query Override für Notifications |
| chrome.runtime masking | 1 | NICHT IMPLEMENTIERT | chrome.runtime Object Spoofing |
| navigator.plugins spoofing | 1 | NICHT IMPLEMENTIERT | Fake Plugin-Liste für headless |
| `block_popups` | 2 | ON ✅ | Blockiert Pop-ups (kein Behavioral-Signal) |
| `block_notifications` | 2 | ON ✅ | Blockiert Notification-Requests |
| `humanize_click` | 2 | NICHT IMPLEMENTIERT | Menschenähnliche Klick-Muster |
| `humanize_type` | 2 | NICHT IMPLEMENTIERT | Menschenähnliches Tippen |
| `humanize_scroll` | 2 | NICHT IMPLEMENTIERT | Scroll mit Easing/Jitter |
| SOCS consent cookie | 3 | ON ✅ | CDP NetworkCommands.set_cookie pro Tab — bypassed Google Cookie-Wall |
| `use_context` | 3 | OFF ❌ | Frischer Browser-Context pro Query (Cookie-Isolation) |
| `delay_between_queries` | 5 | 0 ❌ | Pause zwischen Queries — 0 = kein Delay (bewusst) — Break bei ~90 queries/10min back-to-back → stealth05 Batch 1 |
| `page_load_timeout` | 5 | 20s | Max Navigation-Wartezeit |

### Per-Engine (in config.yml google-Section)

| Stellschraube | Ebene | Effekt |
|---------------|-------|--------|
| `proxy` | 4 | None (direkt) — kein Proxy konfiguriert |
| `consent_cookie` | 3 | SOCS Cookie + Fallback consent_buttons für Google |
| `wait_for_results` | 2/5 | Max 15 Zyklen × 1s — kein aggressives Polling |
| `consent_settle` | 2 | 2s Settle nach Consent-Handling |

## Engine-Status

### Stresstest 2026-04-07 (Legacy — 9-Engine SearXNG-Stack)

| Engine | Score | Hauptproblem | Erkennungsebene | Routing |
|--------|-------|-------------|-----------------|---------|
| Google | 30/30 ✅ | — | — | direct, consent_cookie |
| Bing | 30/30 ✅ | — | — | direct |
| CrossRef | 30/30 ✅ | — | — | httpx API |
| Mojeek | 15/30 ⚠️ | Block ab Query 16 | Rate-Limiting (IP) | direct |
| DuckDuckGo | 6/30 ⚠️ | Bing-Redirect | Package-Bug (ddgs) | httpx |
| Brave | 1/30 ❌ | PoW CAPTCHA ab Query 2 | Fingerprint + Rate-Limiting | direct (Tor = 0/30) |
| Startpage | 0/30 ❌ | Zero results, kein Error | Unklar | direct |
| Google Scholar | 0/0 ❌ | Engine-Crash | Unklar | direct |
| Semantic Scholar | 3/30 ❌ | 429 Rate-Limit | Rate-Limiting (API) | httpx API |

### Neue Baseline 2026-04-21 (pydoll custom stack, single-engine)

| Engine | Score | Stack | Config |
|--------|-------|-------|--------|
| Google | 30/30 ✅ | headless pydoll Chrome, SOCS cookie, 4 JS-Patches | `dev/search_pipeline/config.yml` + `01_google_smoke.py` |

Dieser Run ist die aktuelle Referenz-Baseline. Details → `dev/search_pipeline/01_reports/smoke_20260421_022343.md`.

## Dropped Engines — Final Verdict

| Engine | Score | Grund |
|--------|-------|-------|
| Brave | 1–10/30 | PoW CAPTCHA, keine Kombination erreicht 30/30 — siehe Rationale unten |
| Startpage | 0/30 | Zero Results, Root Cause unklar |
| DuckDuckGo | 6/30 | Redirect zu Bing via ddgs-Bug |
| Mojeek | 15/30 | IP-basiertes Rate-Limit (15 req/60s, nicht umgehbar) |
| Semantic Scholar | 3/30 | 429 Rate-Limit (API) |

**Survivor-Set (aktiv in `src/search/`):** ~~Google, Bing, Google Scholar, CrossRef~~ — **historisch, vor Engine-Expansion**.

**Aktueller Stand (2026-05-04):** 8 aktive Engines im 4 req/min uniform Rate-Limit-Pool — Google, DuckDuckGo, Mojeek, Lobsters (Browser via pydoll); Google Scholar (Browser, JS-Fix 2026-05-04); CrossRef, OpenAlex, Stack Exchange (HTTP-API). Bing in `src/search/engines/bing.py` aber broken (DOM-drift, nicht aktiv im Smoke). HN dropped 2026-05-04 (rate-limit-cascade-hostile). Siehe [search05_engine_expansion.md](search05_engine_expansion.md) für Engine-Expansion-Historie.

### Brave — Drop-Entscheidung & Rationale

**Entscheidung: Brave wird gedroppt.**

Kern-Grund: Alle CAPTCHA-Lösungen (Warten, Klick-Lösung, API) sind inkompatibel mit der `asyncio.gather` Parallel-Engine-Architektur in `src/search/search_web.py`. Google liefert in ~0.2s. Ein Brave-CAPTCHA erzeugt 10–15s Minimum-Latenz pro Query — macht die gesamte Search-Response unbrauchbar.

Getestet und verworfen:
- Stealth-Patch-Matrix (8 Kombinationen, beste: WebGL +7 → 10/30) — Tabelle in [stealth01_fingerprint.md](stealth01_fingerprint.md)
- Patchright mit Chromium Binary → Slider CAPTCHA statt PoW, 0/30
- Camoufox (Firefox, headless) → 7/30
- PoW Reverse-Engineering (Argon2 + Privacy Pass VOPRF) — lösbar, aber Latenz-Problem bleibt
- Brave Search API (2K/Monat gratis) — kein CAPTCHA, aber Latenz-Architektur-Problem bleibt

### Wie Brave-Arbeit fortgesetzt werden kann

Voraussetzungen für Resume:
1. Architektur-Problem lösen: Brave aus `asyncio.gather` raus (eigener Timeout, Fallback auf restliche 3 Engines)
2. Patchright mit echtem Chrome Binary testen (`patchright install chrome` + `channel="chrome"` + `headless=True`) — wurde nie korrekt getestet
3. Alternativ: Brave Search API evaluieren

## Referenced Files

- `dev/search_pipeline/01_google_smoke.py` — Baseline-Implementation
- `dev/search_pipeline/config.yml` — Baseline-Config
- `dev/search_pipeline/01_reports/smoke_20260421_022343.md` — 30/30 Baseline-Run
- `dev/search_pipeline/01_reports/smoke_20260421_182917.md` — 28/30 Re-verify Run
