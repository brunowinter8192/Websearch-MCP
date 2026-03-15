# Search Pipeline Step 2: Routing & Proxy

## Status Quo

**Code:** `src/searxng/settings.yml` — `outgoing` + per-Engine `proxies`/`using_tor_proxy`
**Method:** Split-Routing: sensibelere Engines via Tor, blockierte Engines direkt
**Config:**

```yaml
outgoing:
  request_timeout: 5.0
  max_request_timeout: 15.0
  proxies:
    all://:
      - socks5h://tor:9150
  using_tor_proxy: true
  extra_proxy_timeout: 10

# Per-Engine Overrides:
# Google:      proxies: {},  using_tor_proxy: false  → DIREKT
# DuckDuckGo:  proxies: {},  using_tor_proxy: false  → DIREKT
# Brave:       (kein Override)                       → TOR
# Startpage:   (kein Override)                       → TOR
# G. Scholar:  (kein Override)                       → TOR
```

**Suspension Times (settings.yml):**

| Fehlertyp | Sperrzeit |
|-----------|-----------|
| SearxEngineAccessDenied | 600s (10 min) |
| SearxEngineCaptcha | 600s (10 min) |
| SearxEngineTooManyRequests | 300s (5 min) |
| cf_SearxEngineCaptcha (Cloudflare) | 1800s (30 min) |
| cf_SearxEngineAccessDenied | 600s (10 min) |
| recaptcha_SearxEngineCaptcha | 3600s (60 min) |

**Timeout-Kaskade:**
- `request_timeout: 5.0` — normaler Engine-Timeout
- `max_request_timeout: 15.0` — absolutes Maximum
- `extra_proxy_timeout: 10` — zusätzlicher Buffer für Tor-Latenz
- `timeout: 10` auf Google Scholar — Scholar-spezifischer Override

## Evidenz

### Tor-Exit-Nodes — Google/DDG-Blockierung
Google und DuckDuckGo blockieren bekannte Tor-Exit-Nodes zuverlässig mit CAPTCHA oder sofortigem 403. Direktverbindung ist die einzige funktionierende Option. Per-Engine `proxies: {}` und `using_tor_proxy: false` überschreiben den globalen Tor-Default.

### Brave + Startpage — Tor-Benefit
Brave und Startpage blockieren keine Tor-Exit-Nodes. Tor-Routing bietet IP-Rotation bei Rate-Limiting und verhindert Session-Tracking über Queries hinweg.

### extra_proxy_timeout
Tor-Routing fügt ~1-3s Latenz pro Hop hinzu. `extra_proxy_timeout: 10` erweitert das effektive Timeout für Tor-Engines, ohne den normalen `request_timeout` zu erhöhen.

### Suspension Times — Cloudflare-Sonderbehandlung
Cloudflare-geschützte Sites haben aggressiveres Rate-Limiting als Standard-Sperren. 1800s (30 min) für `cf_SearxEngineCaptcha` verhindert wiederholtes Triggern des Cloudflare-Schutzes. recaptcha verhält sich als härtester Blocker → 3600s.

### ban_time_on_fail / max_ban_time_on_fail
`ban_time_on_fail: 5` und `max_ban_time_on_fail: 120` steuern das exponenzielle Back-off bei allgemeinen Verbindungsfehlern (unabhängig von den Suspension Times). Kurze Basiszeit für schnellen Retry nach transienten Fehlern.

## Entscheidung

Split-Routing-Architektur: **Default Tor, Ausnahmen direkt.** Rationale:
- Globaler Tor-Default schützt alle Engines mit IP-Rotation ohne Einzelkonfiguration
- Gezielter Bypass für Google/DDG da Tor dort kontraproduktiv ist (sofortige CAPTCHA)
- Google Scholar erbt Tor — Scholar-Blockierungen via Tor sind seltener als bei Consumer-Google (anderer Endpunkt)
- Tor-Container läuft als Docker-Service (`tor:9150`), keine externe Abhängigkeit

## Offene Fragen

- Google Scholar via Tor: Nicht explizit getestet ob Scholar Tor-Exit-Nodes genauso aggressiv blockt wie consumer-google. Könnte bei Scholar-Fehlern der Grund sein.
- Startpage via Tor: Startpage ist ein Google-Proxy — unklar ob Google-Sperren durch Startpage durchschlagen
- Fallback wenn Tor-Container down: Kein Fallback konfiguriert. Alle Tor-Engines würden gleichzeitig fehlschlagen.
- `socks5h://tor:9150` — der `h` in socks5h bedeutet DNS-Auflösung durch den Proxy. Korrekt für Tor (verhindert DNS-Leaks), aber konfigurationsabhängig.

## Quellen

- `src/searxng/settings.yml` — Routing-Konfiguration
- SearXNG Docs (RAG Collection: SearXNG_Docs) — outgoing, proxy, suspended_times Parameter
- search01_engines.md — Engine-Auswahl und Tor-Kompatibilität

### Zum Indexieren (für systematische Verbesserung)

- SearXNG network.py Source — Proxy-Inheritance-Logik (proxies vs using_tor_proxy): https://github.com/searxng/searxng/blob/master/searx/network.py
- SearXNG GitHub Issues "proxy" — Tor-Routing-Probleme, Suspension-Verhalten: https://github.com/searxng/searxng/issues?q=proxy+tor
- Tor Project FAQ — Exit-Node-Blocking, Circuit-Renewal: https://support.torproject.org/
