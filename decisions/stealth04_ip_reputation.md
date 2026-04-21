# Stealth Layer 4: IP-Reputation

## Status Quo (IST)

### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**Direct Connection:**
- Kein Proxy konfiguriert
- Requests laufen über die lokale IP (Mac-Entwickler-IP, Heimnetz oder Büro-Netz)
- `webrtc_leak_protection: true` — verhindert WebRTC-basierte IP-Leaks (lokale IP via STUN)

**Kein Proxy-Support implementiert:**
- `config.yml` hat keinen `proxy`-Key
- Pydoll-Options haben kein `proxy`-Argument in der aktuellen Smoke-Implementation

### Detection Surface

Was Layer 4 prüft:

| Signal | Was erkannt wird | Unser Control |
|--------|-----------------|---------------|
| Datacenter-IP | ASN-Klassifikation (AWS, GCP, DigitalOcean) | ✅ Heimnetz-IP unkritisch |
| VPN-IP | Bekannte VPN-Provider-ASNs | ⚠️ unklar (je nach Netz) |
| Tor Exit-Node | Öffentliche Tor-Exit-Node-Listen | ❌ Tor gelistet (0/30 Brave mit Tor) |
| Proxy-Listen | Bekannte kommerzielle Proxy-IPs | ❌ kein Proxy |
| IP-Rotation | Keine Rotation zwischen Queries | ❌ gleiche IP für alle 30 Queries |

## Evidenz

### Tor Exit-Node Blocking (2026-04-07)

- Brave mit Tor-Proxy: 0/30 (alle Tor Exit-Nodes auf Blocklist)
- Brave ohne Proxy (direct): 1/30 — zeigt dass Layer 4 bei Brave aktiver ist als bei Google

### Google IP-Tolerance

- Google 30/30 mit direkter IP bestätigt (2026-04-07 + 2026-04-21)
- Google scheint bei Heimnetz/Büro-IPs keine IP-Reputation-Probleme zu erzeugen bei dieser Query-Rate

## Recommendation (SOLL)

Pending — aktuell kein Problem für Google. Bei Stress-Tests über mehrere Runs hinweg (IP-Akkumulation) könnte IP-basiertes Blocking einsetzen.

Residential Proxies wären die Ideal-Lösung für IP-Rotation, stehen aber nicht zur Verfügung.

## Offene Fragen

- Residential Proxies: Nicht verfügbar — wäre optimale IP-Rotation (nicht detektierbar als Datacenter/VPN)
- Google: Ab welcher Query-Rate / welchem Zeitfenster beginnt IP-basiertes Blocking? (noch nicht stress-getestet)
- Mehrere Back-to-Back Runs: Akkumulieren sich IP-Signale über Runs, oder resettet Google nach gewissem Idle-Intervall?
