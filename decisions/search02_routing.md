# Search Pipeline Step 2: Routing & Proxy

## Status Quo

**Code:** `src/searxng/settings.yml` — `outgoing` + per-Engine `proxies`/`using_tor_proxy`
**Method:** Split-Routing: Default Tor, Ausnahmen direkt für Engines die Tor-Exit-Nodes blockieren

### Globaler Tor-Default

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

**DIREKT (Tor-Bypass via `proxies: {}` + `using_tor_proxy: false`):**

| Engine | Kategorie | Grund |
|--------|-----------|-------|
| Google | general | Blockiert Tor-Exit-Nodes (CAPTCHA/403) |
| Bing | general | Blockiert Tor-Exit-Nodes wie Google |
| DuckDuckGo | general | Blockiert Tor-Exit-Nodes (Bing-Backend) |
| Mojeek | general | Kleinere Engine, Tor-Exit-Nodes vermutlich geblockt |

**TOR (erbt globalen Default — kein Override nötig):**

| Engine | Kategorie | Grund |
|--------|-----------|-------|
| Brave | general | Toleriert Tor, profitiert von IP-Rotation |
| Startpage | general | Google-Proxy über Tor, IP-Rotation |
| Google Scholar | general | API-Endpunkt, seltener Tor-Blocking als Consumer-Google |
| Semantic Scholar | general | API-basiert, kein Tor-Blocking bekannt |
| CrossRef | general | API-basiert, kein Tor-Blocking |
| ArXiv | plugin | API-basiert, kein Tor-Blocking |
| GitHub | plugin | API-basiert |
| Reddit | plugin | Scraper, Tor-Kompatibilität ungetestet |

### Suspension Times

| Fehlertyp | Sperrzeit |
|-----------|-----------|
| SearxEngineAccessDenied | 600s (10 min) |
| SearxEngineCaptcha | 600s (10 min) |
| SearxEngineTooManyRequests | 300s (5 min) |
| cf_SearxEngineCaptcha (Cloudflare) | 1800s (30 min) |
| cf_SearxEngineAccessDenied | 600s (10 min) |
| recaptcha_SearxEngineCaptcha | 3600s (60 min) |

### Timeout-Kaskade

- `request_timeout: 5.0` — normaler Engine-Timeout
- `max_request_timeout: 15.0` — absolutes Maximum
- `extra_proxy_timeout: 10` — zusätzlicher Buffer für Tor-Latenz
- `timeout: 10` auf Google Scholar — Scholar-spezifischer Override

## Evidenz

### Tor-Exit-Nodes — Aggressive Blockierung
Google, Bing, DuckDuckGo und wahrscheinlich Mojeek blockieren bekannte Tor-Exit-Nodes zuverlässig mit CAPTCHA oder sofortigem 403. Direktverbindung ist die einzige funktionierende Option. Per-Engine `proxies: {}` und `using_tor_proxy: false` überschreiben den globalen Tor-Default.

**CRITICAL:** Beide Felder müssen gesetzt werden. `using_tor_proxy: false` allein deaktiviert nur die Tor-Verification, nicht den Proxy. `proxies` wird unabhängig von `using_tor_proxy` aus `outgoing.proxies` geerbt (SearXNG network.py initialize function).

### Brave + Startpage — Tor-Benefit
Brave und Startpage blockieren keine Tor-Exit-Nodes. Tor-Routing bietet IP-Rotation bei Rate-Limiting und verhindert Session-Tracking über Queries hinweg.

### API-Engines — Tor unproblematisch
Semantic Scholar, CrossRef, ArXiv und GitHub nutzen offizielle APIs. Diese blockieren in der Regel keine Tor-Exit-Nodes, da sie für programmatischen Zugriff ausgelegt sind. Tor bietet hier zusätzlichen Anonymitäts-Schutz ohne Nachteil.

### Reddit — Ungetestet
Reddit Engine ist ein Scraper (nicht API). Tor-Kompatibilität muss empirisch getestet werden. Fallback: `proxies: {}` + `using_tor_proxy: false` wenn Tor-Blocking auftritt.

### extra_proxy_timeout
Tor-Routing fügt ~1-3s Latenz pro Hop hinzu. `extra_proxy_timeout: 10` erweitert das effektive Timeout für Tor-Engines, ohne den normalen `request_timeout` zu erhöhen.

### Suspension Times — Cloudflare-Sonderbehandlung
Cloudflare-geschützte Sites haben aggressiveres Rate-Limiting. 1800s (30 min) für `cf_SearxEngineCaptcha` verhindert wiederholtes Triggern. recaptcha = härtester Blocker → 3600s.

## Entscheidung

Split-Routing-Architektur: **Default Tor, Ausnahmen direkt.** Rationale:
- Globaler Tor-Default schützt alle Engines mit IP-Rotation ohne Einzelkonfiguration
- Gezielter Bypass für 4 Engines (Google, Bing, DDG, Mojeek) die Tor blockieren
- API-basierte Engines (Scholar, Semantic Scholar, CrossRef, ArXiv, GitHub) profitieren von Tor ohne Nachteile
- Reddit-Engine als Scraper noch ungetestet — bei Problemen auf DIREKT umstellen
- Tor-Container läuft als Docker-Service (`tor:9150`), keine externe Abhängigkeit

## Offene Fragen

- Reddit via Tor: Empirisch testen ob Reddit-Scraper über Tor funktioniert
- Google Scholar via Tor: Nicht explizit getestet ob Scholar Tor-Exit-Nodes blockiert
- Startpage via Tor: Startpage ist ein Google-Proxy — unklar ob Google-Sperren durchschlagen
- Mojeek Tor: ANNAHME dass Tor geblockt wird (nicht verifiziert). Bei Bedarf testen.
- Tor-Container Failover: Kein Fallback wenn Tor-Container down — alle Tor-Engines fallen gleichzeitig aus

## Quellen

- `src/searxng/settings.yml` — Routing-Konfiguration
- `searxng/searxng` GitHub Repo (`searx/network.py`) — Proxy-Inheritance-Logik
- SearXNG Docs (RAG Collection: searxng) — outgoing, proxy, suspended_times Parameter
- search01_engines.md — Engine-Auswahl und Kategorie-Zuordnung

## Implementiert (Session 2026-04-03)

### Engine Suspension Disabled

Alle `suspended_times`-Werte und `ban_time_on_fail` auf `0` gesetzt.

**Rationale:** SearXNG's internes Suspension-System war kontraproduktiv. Wenn eine Engine rate-limited wird, sperrt SearXNG sie zusätzlich für 300–3600 Sekunden — doppelte Bestrafung:
1. Engine ist ohnehin temporär blockiert (Google-seitige 403, Tor-Blocking, etc.)
2. SearXNG-Suspension verhindert Recovery ohne Docker-Restart

Engines sollen ihre eigene Rate-Limiting-Logik handhaben. SearXNG greift nicht ein.

**Konfiguration in `settings.yml`:**
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

Update von 2026.3.10 → 2026.4.3 behebt Blocking für Google, Brave, Google Scholar durch neuen GSA iPhone User-Agent. Diese 3 Engines liefern seitdem wieder stabile Ergebnisse.

### TLS Fingerprint Investigation

Skripte `20_tls_fingerprint.py` + `21_cipher_shuffle_verify.py` entwickelt (legacy — aus dem SearXNG-Proxy-Stack, inzwischen gelöscht).

**Ergebnisse:**
- JA3 Hash: `cdb8399d0ce47cc19f2ef0756148891e` (gemessen via tls.browserleaks.com)
- Cipher Shuffling wirksam: 12/12 Requests produzieren unterschiedliche JA3-Hashes ✓
- Gap identifiziert: `Accept: */*` Header fehlt in SearXNG-Requests (kein unmittelbarer Blocking-Grund)

### Mojeek Patch — .pyc Cache Lektion

Mojeek-Patch (`src/searxng/patches/mojeek.py`) hatte Stale `.pyc` Cache im Docker-Container — aktualisierter Patch wurde ignoriert.

**Lösung:** `docker compose build --no-cache` löscht `.pyc` Files und erzwingt Re-Kompilierung.

**Lesson:** Docker volume-mounted Patches können durch stale `.pyc` ignoriert werden. Bei Patch-Updates immer Container neu bauen.

**Fix:** `arc=none` hardcoded (statt `arc=us` aus Default-Engine) — behebt Bot-Detection.

### Semantic Scholar — Direktrouting + Session Cookies

Semantic Scholar von Tor auf DIREKT umgestellt (`proxies: {}` + `using_tor_proxy: false`). Session-Cookie-Tracking inkompatibel mit Tor-IP-Rotation.

**Patch:** `src/searxng/patches/semantic_scholar.py` — Cookies (`s2Exp`, `tid`) werden 300s gecacht und bei nachfolgenden Requests mitgesendet.

**Einschränkung:** Soft-Limit ~6 Requests/Session. Nach ~6 Queries liefert Semantic Scholar 0 Ergebnisse. Kein Hard-Block — Recovery durch SearXNG-Restart oder Session-Rotation.

## Resolved Offene Fragen (2026-04-03)

- ✅ **Google Scholar via Tor:** Scholar via SearXNG 2026.4.3 wieder funktional; läuft direkt (kein Tor)
- ✅ **Mojeek Tor:** Mojeek stabil über Direktverbindung mit arc=none Patch
- ✅ **Startpage via Tor:** Funktioniert stabil über Tor nach SearXNG 2026.4.3 Update
- ⏳ **Reddit via Tor:** Noch offen — nicht getestet
- ⏳ **Tor-Container Failover:** Noch offen — kein Fallback implementiert
