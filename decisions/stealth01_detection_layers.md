# Custom Search Engine: Stealth & Detection Layers

Applies to: `src/search/` (pydoll-based custom engine) + `dev/search_pipeline/engines_eval/` (test suite)

## Status Quo (IST)

**Code:** `dev/search_pipeline/engines_eval/stealth_config.py` (global patches), `dev/search_pipeline/engines_eval/engine_selectors.py` (per-engine config)

### Detection Layers

Bot-Detection operiert auf mehreren Ebenen. Jede Suchmaschine nutzt eine andere Kombination.

| # | Ebene | Was geprüft wird | Unsere Stellschrauben | Status |
|---|-------|-------------------|----------------------|--------|
| 1 | **Browser-Fingerprint** | webdriver-Flag, WebGL vendor/renderer, Canvas Hash, navigator.plugins (leer in headless), chrome.runtime (fehlt in headless), Screen-Dimensionen, Permissions API, CSS media queries | `patch_webgl`, `patch_canvas_noise`, `patch_permissions`, `patch_computed_style`, Screen/Navigator-Overrides, `disable_blink_features=AutomationControlled`, `headless_new=True` | 2/5 Patches ON. chrome.runtime + navigator.plugins nicht implementiert |
| 2 | **Behavioral** | Request-Timing (zu schnell, zu regelmäßig), fehlende Mausbewegung/Scrolling, Klick-Muster | `humanize_click`, `humanize_type`, `humanize_scroll` | Alle OFF |
| 3 | **Session-Tracking** | Gleicher Browser/Cookies über Queries → Tracking, Cookie-Walls | `use_context` (frischer Browser-Context pro Query), `consent_cookie` Injection via CDP | use_context OFF bei allen Engines |
| 4 | **IP-Reputation** | Datacenter-IPs, VPN/Tor Exit-Nodes, bekannte Proxy-Listen | `proxy` per Engine (Tor socks5, direct, custom) | Nur Tor oder direct verfügbar. Keine residential Proxies. |
| 5 | **Rate-Limiting** | X Requests/Zeitfenster pro IP | `between_query_delay`, `settle_seconds` | Kein Delay = provoziert Blocking (gewollt für Tests) |
| 6 | **TLS/HTTP-Fingerprint** | JA3 Hash, HTTP/2 Frame-Order, Header-Order | Nicht steuerbar — Chrome ist Chrome. httpx-Engines haben anderen Fingerprint. | OK (Chrome TLS ist real) |
| 7 | **CAPTCHA** | PoW (Brave Svelte Slider), reCAPTCHA, hCaptcha als letzte Verteidigung | `captcha_detect_js` (erkennt, löst nicht), `captcha_path` (URL-basierte Erkennung) | Detect-only, kein Solving |

### Stellschrauben-Inventar

#### Global (stealth_config.py DEFAULT_CONFIG)

| Stellschraube | Ebene | Default | Effekt |
|---------------|-------|---------|--------|
| `headless_new` | Fingerprint | True ✅ | `--headless=new` — schwerer zu detecten als altes headless |
| `disable_blink_features` | Fingerprint | AutomationControlled ✅ | Entfernt `navigator.webdriver=true` Flag |
| `patch_computed_style` | Fingerprint | True ✅ | Fixt headless CSS color detection |
| `patch_webgl` | Fingerprint | False ❌ | WebGL vendor/renderer Override (Apple M1 Pro) |
| `patch_canvas_noise` | Fingerprint | False ❌ | Subtile Canvas-Fingerprint-Randomisierung |
| `patch_permissions` | Fingerprint | False ❌ | Permissions.query Override für Notifications |
| chrome.runtime masking | Fingerprint | NICHT IMPLEMENTIERT | chrome.runtime Object Spoofing |
| navigator.plugins spoofing | Fingerprint | NICHT IMPLEMENTIERT | Fake Plugin-Liste für headless |
| `humanize_click` | Behavioral | False ❌ | Menschenähnliche Klick-Muster |
| `humanize_type` | Behavioral | False ❌ | Menschenähnliches Tippen |
| `humanize_scroll` | Behavioral | False ❌ | Scroll mit Easing/Jitter |
| `set_useragent_override` | Fingerprint | False ❌ | CDP UA Override |
| `block_urls` | Behavioral | None | Tracking/Analytics blockieren |

#### Per-Engine (engine_selectors.py config dict)

| Stellschraube | Ebene | Effekt |
|---------------|-------|--------|
| `proxy` | IP-Reputation | None (direkt), socks5 (Tor), oder custom Proxy URL |
| `settle_seconds` | Behavioral | DOM-Wartezeit nach Navigation (gibt JS Zeit zum Rendern) |
| `use_context` | Session | Frischer Browser-Context pro Query (Cookie-Isolation) |
| `captcha_detect_js` | CAPTCHA | JS das truthy returned wenn CAPTCHA präsent |
| `between_query_delay` | Rate-Limiting | Pause zwischen Queries (Sekunden) |
| `consent_cookie` | Session | Cookie-Injection via CDP vor Navigation |

### Engine-Status (Stresstest 2026-04-07)

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

### Google vs Brave — Warum gleiche Config, unterschiedliches Ergebnis

Google 30/30 und Brave 1/30 nutzen identische Stealth-Config (DEFAULT_CONFIG). Unterschied:
- Google: Consent-Cookie löst Cookie-Wall → kein Blocker. Minimale Stealth reicht. Google setzt auf reCAPTCHA (/sorry/) erst bei hohem Traffic.
- Brave: Kein Consent-Problem, aber aggressivere Fingerprint-Detection. PoW CAPTCHA ab Query 2 trotz headless_new + AutomationControlled. Brave prüft vermutlich tiefere Fingerprint-Signale (WebGL, Canvas, chrome.runtime, navigator.plugins).

## Evidenz

### Brave PoW CAPTCHA (2026-04-07)
- Screenshot: "Confirm you're a human being / I'm not a robot" Dialog mit "Learn more about Proof of Work Captcha"
- Svelte-basierter CAPTCHA — PoW (Proof of Work) Challenge, nicht Slider
- Tritt ab Query 2-3 auf (Query 1 liefert Results)
- Mit Tor-Proxy: 0/30 (Tor Exit-Nodes auf Blocklist)
- captcha_detect_js Selektor (`dialog .captcha-card`) matcht nicht das tatsächliche DOM — korrekt wäre `[class*="pow-captcha"]` oder Title-Check

### Brave PoW CAPTCHA Technische Analyse (2026-04-09)
- Algorithmus: Argon2 (Memory-Hard Hash) via WASM, berechnet in Web Worker
- Challenge-Parameter: zero_count=1 (trivial), 21 Tokens, iterations=2, memory_size=512KB
- Privacy Pass: VOPRF-Protokoll (Blind Tokens) in separatem WASM-Modul
- API-Endpoint: POST `/api/captcha/pow?brave=0` mit solutions + blinded_messages
- Server antwortet mit signed_tokens → Cookie → Zugang
- Klick auf "I'm not a robot": Spinner "Letting you in..." erscheint, nach 3s keine Weiterleitung — unklar ob Berechnung zu langsam oder Server rejected wegen Fingerprint
- Zwei CAPTCHA-Tiers: PoW ("I'm not a robot") für Chrome/pydoll, Slider ("Drag the slider") für Patchright/Chromium

### Stealth-Patch-Matrix Brave (2026-04-09)

| Stack / Patch | X/30 | Erste Failure | Delta vs Baseline |
|---------------|------|---------------|-------------------|
| pydoll Baseline (settle=0.0, proxy=None) | 3/30 | Query 3 | — |
| pydoll + patch_webgl=True | 10/30 | Query 11 | +7 |
| pydoll + patch_canvas_noise=True | 6/30 | Query 7 | +3 |
| pydoll + patch_permissions=True | 0/30 | Query 1 | -3 (kontraproduktiv) |
| pydoll + chrome.runtime + navigator.plugins | 0/30 | Query 1 | -3 (kontraproduktiv) |
| pydoll + alle Patches kombiniert | 0/30 | Query 1 | -3 (schlechte Patches dominieren) |
| Patchright (Chromium Binary) | 0/30 | Query 1 | -3 (Slider CAPTCHA statt PoW) |
| Camoufox (Firefox, headless) | 7/30 | Query 8 | +4 |

Erkenntnis: WebGL-Fingerprint ist das stärkste Einzelsignal. Browser-Typ (Chrome vs Firefox) ist sekundär. Brave detects JS-Overrides von Permissions und navigator.plugins direkt → kontraproduktiv. Keine Kombination erreicht >10/30.

### puppeteer-extra-plugin-stealth Vergleich (2026-04-07)
- Fehlende Patches vs. puppeteer-extra: chrome.runtime Masking, navigator.plugins Spoofing
- Quelle: GitHub puppeteer-extra-plugin-stealth Source
- Nachträglich implementiert und getestet: beide kontraproduktiv bei Brave (0/30)

### Brave Detection-Signale (2026-04-09, aus Reverse-Engineering)
- CDP Runtime.enable + Error.stack Getter Trap (pydoll betroffen, Patchright fixt es)
- navigator.userAgentData.brands: "Chromium" vs "Google Chrome" (Patchright mit Chromium-Binary betroffen)
- __playwright_evaluation_script__ in Function.prototype.toString
- navigator.webdriver = true
- WebGL SwiftShader Renderer (starkes Signal — WebGL-Patch bringt +7)
- navigator.brave.isBrave fehlt (Soft-Signal)
- Quellen: nullpt-rs/blog (Brave CAPTCHA Reverse-Engineering), BotBrowser CHANGELOG, stealth-browser-mcp Source

### Mojeek Rate-Limit (2026-04-09)
- Exakt 15 Requests pro ~60s Sliding Window
- Ab Request 16: 403 "automated queries"
- Unabhängig von Sprache (Deutsch war Red Herring)
- IP-basiert (use_context + Browser-Rotation helfen nicht)

## Recommendation (SOLL)

### Brave — Stealth allein reicht nicht

Stealth-Patches verzögern die CAPTCHA, verhindern sie nicht. Bester Wert: 10/30 (WebGL). Keine Kombination von Fingerprint-Patches erreicht 30/30. Brave's Detection ist multi-layered: Fingerprint-Score bestimmt Rate-Limit-Schwelle, nach 7-10 schnellen Queries kommt CAPTCHA egal welcher Stack.

**Verbleibende Optionen (nicht getestet):**
1. Clean Slate: use_context=True (frischer Browser-Context pro Query) — verhindert Session-Accumulation. Unklar ob Brave per IP oder per Session trackt.
2. CAPTCHA lösen: Klick + länger warten (10-15s), oder Argon2 PoW programmatisch lösen (Privacy Pass VOPRF ist der Blocker).
3. Patchright mit echtem Chrome: `patchright install chrome` + `channel="chrome"` + headless=True — nie korrekt getestet (vorheriger Test nutzte Chromium Binary).
4. Brave Search API: 2K Queries/Monat gratis, $3/15K. Kein CAPTCHA, kein Fingerprint. Pragmatischste Lösung.

### Andere Engines

Pending — nur 5-Query-Tests durchgeführt, keine belastbaren 30/30 Runs.

## Offene Fragen

- Brave: Trackt Brave per IP oder per Session? (use_context=True würde Session-Tracking brechen, nicht IP-Tracking)
- Brave: CAPTCHA-Klick mit 10-15s Wartezeit — reicht die Zeit für PoW + API-Call? Oder rejected Server wegen Fingerprint?
- Brave: Patchright mit echtem Chrome Binary (nicht Chromium) — wurde nie korrekt getestet
- Brave captcha_detect_js: Falscher Selektor — korrekt wäre `[class*="pow-captcha"]` oder Title-Check auf "Captcha"
- Startpage: Root Cause komplett unklar (0/30 im Stresstest, "transient" laut Worker — nicht belastbar)
- Google Scholar: Engine-Crash Root Cause unklar ("transient" — nicht belastbar)
- Residential Proxies als Alternative zu Tor: Nicht verfügbar, aber wäre optimale IP-Rotation
- Camoufox: Könnte mit zusätzlichen Firefox-spezifischen Stealth-Settings besser werden — nicht weiter exploriert

## Verdict: Brave & Dropped Engines — Final Decision (2026-04-xx)

### Dropped Engines

| Engine | Score | Grund |
|--------|-------|-------|
| Brave | 1–10/30 | PoW CAPTCHA, keine Kombination erreicht 30/30 |
| Startpage | 0/30 | Zero Results, Root Cause unklar |
| DuckDuckGo | 6/30 | Redirect zu Bing via ddgs-Bug |
| Mojeek | 15/30 | IP-basiertes Rate-Limit (15 req/60s, nicht umgehbar) |
| Semantic Scholar | 3/30 | 429 Rate-Limit (API) |

**Survivor-Set:** Google, Bing, Google Scholar, CrossRef — alle 30/30 im Stresstest 2026-04-07.

### Brave — Entscheidung & Rationale

**Entscheidung: Brave wird gedroppt.**

Kern-Grund: Alle CAPTCHA-Lösungen (Warten, Klick-Lösung, API) sind inkompatibel mit der `asyncio.gather` Parallel-Engine-Architektur in `src/search/search_web.py`. In `_query_engines_concurrent()` laufen alle Engines parallel — die langsamste Engine blockiert die gesamte Search-Response bis alle fertig sind. Google liefert in ~0.2s. Ein Brave-CAPTCHA erzeugt 10–15s Minimum-Latenz pro Query. Das macht die gesamte Search-Response unbrauchbar.

**Getestetes + verworfen:**
- Stealth-Patch-Matrix (8 Kombinationen, beste: WebGL +7 → 10/30) — Tabelle in "Evidenz" Section
- Patchright mit Chromium Binary → Slider CAPTCHA statt PoW, 0/30
- Camoufox (Firefox, headless) → 7/30
- PoW Reverse-Engineering (Argon2 + Privacy Pass VOPRF) — technisch lösbar, aber Latenz-Problem bleibt
- Brave Search API (2K/Monat gratis) — hätte kein CAPTCHA, aber Latenz-Architektur-Problem bleibt bei Fallbacks

**Parked state:** Brave-Config und Selektoren bleiben in `engine_selectors.py` und `stealth_config.py` (als `# PARKED` kommentiert). Brave-Entry in `28_stress_test.py` ist auskommentiert.

### Wie Brave-Arbeit fortgesetzt werden kann

**Dev-Scripts für Brave-Testing:**
- `dev/search_pipeline/engines_eval/27_stealth_test.py brave "<query>" --screenshot` — Single-Query, zeigt CAPTCHA sofort
- `dev/search_pipeline/engines_eval/28_stress_test.py --engine brave --limit 30` — 30-Query Stresstest

**Park-State:**
- `engine_selectors.py`: Brave-Entry auskommentiert (`# PARKED`)
- `stealth_config.py` `rate_limits`: Brave-Entry bleibt (aktiv für dev-Tests via 27_stealth_test.py)
- `28_stress_test.py` `PYDOLL_ENGINES`: Brave auskommentiert

**Voraussetzung für Resume:**
1. Architektur-Problem lösen: Brave muss aus `asyncio.gather` raus (eigener Timeout, Fallback auf restliche 3 Engines wenn CAPTCHA)
2. Dann: Patchright mit echtem Chrome Binary testen (`patchright install chrome` + `channel="chrome"` + headless=True) — wurde nie korrekt getestet
3. Alternativ: Brave Search API evaluieren (kein CAPTCHA, aber dann Fallback-Architektur nötig)

## Quellen

- `dev/search_pipeline/engines_eval/stealth_config.py` — Patch-Implementierung
- `dev/search_pipeline/engines_eval/engine_selectors.py` — Per-Engine Config
- `dev/search_pipeline/engines_eval/28_reports/stress_20260407_184152.md` — Stresstest Baseline
- puppeteer-extra-plugin-stealth (GitHub) — Fehlende Patch-Analyse
- pydoll GitHub Source + Docs — Stealth-Capabilities
- daijro/camoufox (GitHub) — Firefox-basierte Stealth-Automation
- saifyxpro/HeadlessX (GitHub) — Camoufox-basierte Plattform
- nichochar/stealth-browser-mcp (GitHub) — Patchright + Chrome + Xvfb Referenz-Implementation
- Kaliiiiiiiiii-Vinyzu/patchright-python (GitHub) — Playwright-Fork mit CDP-Leak-Fix
- debug-it/brave-captcha-solver (GitHub) — YOLO v11n PoW CAPTCHA Solver
- nullpt-rs/blog (GitHub) — Brave CAPTCHA Reverse-Engineering (reversing-botid.mdx)
- FriendlyCaptcha/friendly-challenge (GitHub) — PoW CAPTCHA Referenz-Implementation
- BotBrowser CHANGELOG (GitHub) — Browser-Fingerprint-Emulation Details
