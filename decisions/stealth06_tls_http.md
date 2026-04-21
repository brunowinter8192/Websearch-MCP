# Stealth Layer 6: TLS/HTTP-Fingerprint

## Status Quo (IST)

### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/01_google_smoke.py`.

**Chrome TLS ist real — kein Eingriff nötig oder möglich.**

Der Smoke-Stack verwendet pydoll mit echtem Chrome Binary (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`). Chrome's TLS-Stack ist der echte Browser-Stack — JA3-Hash, HTTP/2 Frame-Order und Header-Order sind identisch mit einem echten Chrome-User.

Kein httpx in dieser Pipeline — keine Requests via Python-HTTP-Client (die einen anderen TLS-Fingerprint erzeugen würden).

### Detection Surface

Was Layer 6 prüft:

| Signal | Was erkannt wird | Unser Control |
|--------|-----------------|---------------|
| JA3 Hash | TLS Client-Hello Fingerprint | ✅ Chrome TLS ist real |
| HTTP/2 Frame-Order | SETTINGS Frame, WINDOW_UPDATE Frame Reihenfolge | ✅ Chrome HTTP/2 ist real |
| Header-Order | User-Agent, Accept, Accept-Language Reihenfolge | ✅ Chrome Headers sind real |
| ALPN | `h2` negotiation | ✅ Chrome |
| TLS Version | TLS 1.3 | ✅ Chrome |

## Evidenz

TLS-Fingerprint-Tests wurden in Legacy-Scripts durchgeführt (`20_tls_fingerprint.py`, `21_cipher_shuffle_verify.py`) — diese untersuchten den httpx-Stack (SearXNG-Proxy-Ära), nicht den pydoll-Chrome-Stack. Für den aktuellen Chrome-Stack ist kein Test nötig — Chrome ist nicht fälschbar.

## Recommendation (SOLL)

N/A — keine Handlung erforderlich. Chrome-basierte Stacks sind bei Layer 6 inherent unauffällig. Relevant wird Layer 6 nur wenn httpx-basierte Engines (CrossRef, Bing via API-Fallback) problematisch werden.

## Offene Fragen

- Keine — Layer 6 ist für Chrome-basierte Requests gelöst.
