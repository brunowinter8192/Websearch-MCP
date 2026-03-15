# Search Pipeline Step 1: Engines

## Status Quo

**Code:** `src/searxng/settings.yml`
**Method:** SearXNG aggregiert Ergebnisse aus mehreren Suchmaschinen pro Query
**Config:**

| Engine | Aktiv | Weight | Tor | Timeout |
|--------|-------|--------|-----|---------|
| Google | ja | 2 | nein (proxies: {}) | default 5s |
| DuckDuckGo | ja | 1 | nein (proxies: {}) | default 5s |
| Brave | ja | 2 | ja (global proxy) | default 5s |
| Startpage | ja | 2 | ja (global proxy) | default 5s |
| Google Scholar | ja | 2 | nein (kein Override) | 10s |
| Qwant | nein | — | — | — |

Alle aktiven Engines werden bei jedem Query parallel abgefragt. SearXNG merged die Ergebnisse und berechnet einen Score aus Engine-Votes und Hostname-Priorität (→ search03_ranking.md).

## Evidenz

### Qwant — Access Denied
Qwant liefert bei Direktanfragen ohne Account regelmäßig HTTP 403 / "Access Denied". Kein zuverlässiger Betrieb möglich → `disabled: true`.

### Google Scholar — Erhöhter Timeout
Google Scholar hat nachweislich höhere Latenz als Consumer-Suchmaschinen (akademische Indizes, komplexere Backend-Queries). `timeout: 10` verhindert vorzeitigen Abbruch bei wissenschaftlichen Suchen. Bei `time_range`-Filterung ist Scholar dennoch unzuverlässig.

### DuckDuckGo — Weight 1 statt 2
DDG hat in der Praxis eine niedrigere Trefferqualität für technische Queries als Google oder Brave. Weight 1 reduziert den Einfluss auf den finalen Score ohne DDG komplett zu deaktivieren (Redundanz-Fallback).

### Google + DDG — Kein Tor
Google und DDG blockieren Tor-Exit-Nodes aggressiv (CAPTCHA, IP-Ban). Direktverbindung ist die einzige funktionierende Option für diese beiden Engines. Siehe auch search02_routing.md.

## Entscheidung

Engine-Set und Weights wurden empirisch gewählt — kein formaler Benchmark. Kriterien:
- **Abdeckung:** 4 aktive Engines aus unterschiedlichen Index-Quellen (Google, DDG, Brave/Startpage als europäische Alternativen, Scholar für Wissenschaft)
- **Zuverlässigkeit:** Engines mit häufigen Fehlern (Qwant) werden deaktiviert
- **Tor-Kompatibilität:** Engines, die Tor-Exit-Nodes blockieren, erhalten direkten Bypass (→ search02_routing.md)
- **Weight-Logik:** Weight bestimmt wie stark ein Engine-Vote den finalen Score beeinflusst. Google und Brave/Startpage erhalten Weight 2 als zuverlässigste Quellen.

## Offene Fragen

- Ist Startpage via Tor zuverlässig genug? Startpage ist ein Google-Proxy — unklar ob Tor-IP-Sperren von Google durchschlagen
- Google Scholar bei `time_range`: Scholar ignoriert time_range-Filter teilweise. Eigener Query-Parameter nötig?
- Bing fehlt komplett: SearXNG hat Bing-Engine, aber Bing blockiert Scraping stark. Wäre ein Test wert.
- Weight-Werte sind nicht kalibriert — eine systematische Qualitätsmessung (Precision@10 pro Engine) fehlt

## Quellen

- `src/searxng/settings.yml` — Engine-Konfiguration
- SearXNG Docs (RAG Collection: SearXNG_Docs) — Engine-Parameter, Weight-Semantik
- Erfahrungswerte aus Betrieb (Qwant-Deaktivierung, DDG-Weight)

### Zum Indexieren (für systematische Verbesserung)

- SearXNG GitHub Issues — Engine-spezifische Bugs, neue Engines, Tor-Kompatibilität: https://github.com/searxng/searxng/issues
- SearXNG Engine Docs — Engine-Implementierungen, supported_languages, timeouts: https://docs.searxng.org/dev/engines/
- Brave Search API Docs — falls Umstieg von Scraper-Engine auf API-Engine: https://api.search.brave.com/app/documentation
