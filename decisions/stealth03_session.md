# Stealth Layer 3: Session-Tracking

## Status Quo (IST)

### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**SOCS Cookie Injection:**
- `config.yml` definiert: `consent_cookie: {name: SOCS, value: "CAISHAgCEhJnd3NfMjAyNjA0MDctMCAgIBgEIAEaBgiA_fC8Bg", domain: ".google.com", path: "/", secure: true}`
- Cookie wird per Tab injiziert via `NetworkCommands.set_cookie` (CDP `Network.setCookie`) mit `same_site=CookieSameSite.LAX`
- Injection erfolgt ZWEIFACH:
  1. Beim Browserstart in `start_browser()` — initial tab bekommt Cookie
  2. Pro Query in `run_query()` via `_inject_consent_cookie(tab, cfg)` — jeder neue Tab bekommt Cookie
- Effekt: Google Cookie-Wall (consent.google.com Redirect + Inline-Consent) wird komplett bypassed

**use_context: OFF:**
- Kein frischer Browser-Context pro Query
- Alle Queries laufen im gleichen Chrome-Profil-Context (`--user-data-dir=~/.searxng-mcp/browser-session-smoke`)
- Cookies akkumulieren über Session — kein Cookie-Isolation zwischen Queries

**Consent-Fallback:**
- `_has_inline_consent()` detektiert Inline-Consent via `'Before you continue'` im Body-Text
- `_handle_consent()` klickt ersten matchenden Button aus `consent_buttons` Fallback-Chain
- Nach Consent: 2s settle + erneute Navigation zur Search-URL

### Detection Surface

Was Layer 3 prüft:

| Signal | Was erkannt wird | Unser Control |
|--------|-----------------|---------------|
| Cookie-Wall (Redirect) | Redirect zu consent.google.com | ✅ SOCS Cookie bypassed |
| Inline-Consent Banner | `'Before you continue'` auf Search-URL | ✅ Cookie + Fallback-Click |
| Session-Akkumulation | Gleiche Session-Cookies über 30 Queries | ⚠️ kein use_context — Cookies akkumulieren |
| Cookie-Fingerprint | SOCS-Wert ist fix — selber Wert bei jedem Start | ⚠️ unklar ob Google SOCS rotiert |

## Evidenz

- SOCS Cookie Bypass: Stresstest 2026-04-07 + neue Baseline 2026-04-21 — beide 30/30, kein einziger CONSENT-Status
- Brave: kein SOCS-Problem (Brave nutzt kein Google Cookie-System), aber use_context=OFF war aktiv → Session-Tracking beigetragen? Unklar

## Recommendation (SOLL)

Pending — wird durch Stress-Test-Iterationen bestimmt. Aktuelle Baseline zeigt, dass SOCS-Cookie ausreicht für 30/30 ohne Consent-Blockierung.

## Offene Fragen

- Brave: Trackt Brave per IP oder per Session? `use_context=True` würde Session-Tracking brechen, nicht IP-Tracking — relevant wenn Brave wieder aufgenommen wird
- SOCS-Wert: Läuft der Cookie ab? (Format `gws_20260407-0` — datum-basiert?) Muss er periodisch erneuert werden?
- Google Scholar: Braucht eigenen Consent-Cookie (anderer Domain)? (Scholar-Engine in src/ — nicht in smoke-Stack)
