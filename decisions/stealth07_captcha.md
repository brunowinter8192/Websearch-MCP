# Stealth Layer 7: CAPTCHA

## Status Quo (IST)

### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**Detect-only — kein Solving.**

CAPTCHA-Erkennung erfolgt über URL-Check:
- `config.yml`: `captcha_path: /sorry/` — Google's CAPTCHA-Redirect-Pfad
- In `run_query()`: `if gc["captcha_path"] in current_url: record["status"] = "CAPTCHA"; return record`
- Record bekommt Status `CAPTCHA` und wird nicht weiter verarbeitet

Kein JavaScript-basierter Solver. Kein Klick-Versuch. Kein automatisches Retry.

**Baseline-Ergebnis:** 30/30 Run 2026-04-21 ohne einzigen CAPTCHA-Status. Google scheint CAPTCHA (`/sorry/`) erst bei signifikant höherem Traffic zu aktivieren.

### Detection Surface

Was Layer 7 ist:

| CAPTCHA-Typ | Engine | Mechanismus | Unser Status |
|-------------|--------|-------------|--------------|
| reCAPTCHA (/sorry/) | Google | Rate-basierter Redirect nach Fingerprint-Verdacht | ✅ Erkannt via URL-Check |
| PoW CAPTCHA (Argon2) | Brave | Proof-of-Work Challenge im Browser | ✅ Erkannt — nicht lösbar |
| Slider CAPTCHA | Brave (Patchright) | Drag-Slider Interaktion | ✅ Erkannt — nicht lösbar |
| hCaptcha | Diverse | Challenge-Response | ❌ Kein Selector konfiguriert |

## Evidenz

### Brave PoW CAPTCHA (2026-04-07)

- Screenshot: "Confirm you're a human being / I'm not a robot" Dialog mit "Learn more about Proof of Work Captcha"
- Svelte-basierter CAPTCHA — PoW (Proof of Work) Challenge, kein Slider
- Tritt ab Query 2–3 auf (Query 1 liefert Results)
- Mit Tor-Proxy: 0/30 (Tor Exit-Nodes auf Blocklist → sofort CAPTCHA)

### Brave PoW Technische Analyse (2026-04-09)

- Algorithmus: Argon2 (Memory-Hard Hash) via WASM, berechnet in Web Worker
- Challenge-Parameter: `zero_count=1` (trivial), 21 Tokens, `iterations=2`, `memory_size=512KB`
- Privacy Pass: VOPRF-Protokoll (Blind Tokens) in separatem WASM-Modul
- API-Endpoint: POST `/api/captcha/pow?brave=0` mit solutions + blinded_messages
- Server antwortet mit `signed_tokens` → Cookie → Zugang
- Klick auf "I'm not a robot": Spinner "Letting you in..." erscheint, nach 3s keine Weiterleitung — unklar ob Berechnung zu langsam oder Server rejected wegen Fingerprint

**Zwei CAPTCHA-Tiers:**
- `PoW ("I'm not a robot")` — für Chrome/pydoll
- `Slider ("Drag the slider")` — für Patchright/Chromium

### captcha_detect_js Bug (Legacy)

Im alten `engines_eval/`-Stack war ein `captcha_detect_js` JavaScript konfiguriert mit Selektor `dialog .captcha-card`. Dieser Selektor matchte nicht das tatsächliche Brave CAPTCHA-DOM. Korrekt wäre `[class*="pow-captcha"]` oder Title-Check auf "Captcha". Im neuen Smoke-Stack nicht relevant (kein JS-Selektor für CAPTCHA — nur URL-Check).

## Recommendation (SOLL)

Pending — wird durch Stress-Test-Iterationen bestimmt. Google CAPTCHA tritt erst bei hohem Traffic auf — aktuell kein Problem.

**Brave CAPTCHA Optionen (wenn Brave resume):**
1. Klick + länger warten (10–15s) — unklar ob Argon2-Berechnung abschließt
2. Argon2 PoW programmatisch lösen — technisch möglich, Privacy Pass VOPRF-Teil ist der Blocker
3. Brave Search API (2K Queries/Monat gratis) — kein CAPTCHA, aber Architektur-Problem (siehe [stealth00_engine_status.md](stealth00_engine_status.md))

## Offene Fragen

- Brave: CAPTCHA-Klick mit 10–15s Wartezeit — reicht die Zeit für PoW-Berechnung + API-Call? Oder rejected Server wegen Fingerprint?
- Brave: Ist das CAPTCHA per Session oder per IP lösbar? (Klick-Lösung persistent für die Session?)
- Google: Ab welchem Traffic-Level schaltet `/sorry/` ein? (Stress-Test-Erkenntnis pending)

## Quellen

- debug-it/brave-captcha-solver (GitHub) — YOLO v11n PoW CAPTCHA Solver
- nullpt-rs/blog (GitHub, reversing-botid.mdx) — Brave CAPTCHA Reverse-Engineering
- FriendlyCaptcha/friendly-challenge (GitHub) — PoW CAPTCHA Referenz-Implementation
