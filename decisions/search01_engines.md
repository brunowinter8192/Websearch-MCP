# Search Pipeline Step 1: Engines

> **⚠️ Superseded (2026-04-15 engine-cut + ongoing):** This file documents the historical SearXNG-aggregator architecture. The path `src/searxng/settings.yml` no longer exists — replaced by direct pydoll engines in `src/search/engines/` after the engine-cut. **For current state read [src/search/DOCS.md](../src/search/DOCS.md) (live engine list + per-engine description) and [search05_engine_expansion.md](search05_engine_expansion.md) (post-cut engine additions: HN, DDG, Mojeek, Lobsters, OpenAlex, Stack Exchange + drop history).** Current pool (2026-05-04): 8 engines uniform 4 req/min — Google, DuckDuckGo, Mojeek, Lobsters, Google Scholar (Browser); CrossRef, OpenAlex, Stack Exchange (HTTP). Bing, HN, Brave, Startpage, Semantic Scholar dropped.

## Status Quo (Historical, pre-engine-cut)

**Code:** `src/searxng/settings.yml`
**Method:** SearXNG aggregiert Ergebnisse aus mehreren Suchmaschinen pro Query

### Kategorie-System

Zwei Custom-Kategorien statt SearXNG-Defaults:

- **general** — Scrapeable Engines (Web + Science). URLs können mit Crawl4AI geholt werden.
- **plugin** — Discovery-Only. Content wird über dedizierte MCP Plugins geholt (ArXiv, GitHub, Reddit).

### general Engines

| Engine | Weight | Tor | Index-Typ | Timeout |
|--------|--------|-----|-----------|---------|
| Google | 2 | nein (proxies: {}) | Eigener Index | default 5s |
| Bing | 1 | nein (proxies: {}) | Eigener Index | default 5s |
| Brave | 2 | ja (global proxy) | Eigener Index | default 5s |
| Startpage | 1 | ja (global proxy) | Google-Proxy | default 5s |
| DuckDuckGo | 1 | nein (proxies: {}) | Bing-basiert | default 5s |
| Mojeek | 1 | nein (proxies: {}) | Eigener Crawler | default 5s |
| Google Scholar | 2 | nein (kein Override) | Akademisch | 10s |
| Semantic Scholar | 2 | nein | Akademisch (AI) | default 5s |
| CrossRef | 1 | nein | DOI/Citations | default 5s |

### plugin Engines

| Engine | Weight | MCP Plugin | Zweck |
|--------|--------|------------|-------|
| ArXiv | 2 | arxiv | Paper-Discovery → Plugin holt Volltext |
| GitHub | 1 | github-research | Repo/Code-Discovery → Plugin für Details |
| Reddit | 1 | reddit | Thread-Discovery → Plugin für Comments |

### disabled Engines

| Engine | Grund |
|--------|-------|
| Qwant | HTTP 403 / Access Denied ohne Account |

## Scoring-Algorithmus (Referenz)

Aus `searxng/searxng` GitHub Source (`searx/results.py`):

```
weight = Π(engine_weights) × len(positions)
score = Σ(weight / position_i)  # pro Engine-Position
```

- **Weights sind MULTIPLIKATIV** — alle Engine-Weights werden miteinander multipliziert
- **Position inversely proportional** — Rank 1 = voller Score, Rank 10 = 1/10
- **priority='high'** ignoriert Position (voller Weight), **'low'** skippt komplett
- Ergebnisse von mehr Engines = höherer Score (positions-Liste wächst)

## Evidenz

### Kategorie-Trennung general/plugin
Plugin-Domains (arxiv.org, github.com, reddit.com) können nicht effektiv gescrapt werden (API-Walls, Rate-Limits, dynamischer Content). Dedizierte MCP Plugins liefern strukturierte Daten. SearXNG-Engines für diese Domains dienen nur der URL-Discovery — der web-research Agent routet sie an die Plugins (→ agent02_routing.md).

### Bing — Neuer eigener Index
Bing hat den zweitgrößten unabhängigen Web-Index weltweit. DDG basiert auf Bing, hat aber eigenes Ranking. Bing direkt aktivieren diversifiziert die Ergebnisse. Weight 1 zum Start (Qualität unbekannt, Tor-Kompatibilität unklar → proxies: {} als Bypass).

### Mojeek — Unabhängiger Crawler
Einziger komplett unabhängiger Crawler-Index neben Google, Bing und Brave. Kleinerer Index, aber diversifiziert Ergebnisse die sonst von den 3 großen dominiert werden. Weight 1 zum Start.

### Semantic Scholar — AI-powered Academic
Allen Institute for AI. Nutzt ML für Zitationsanalyse und Paper-Empfehlungen. Ergänzt Google Scholar mit anderem Ranking-Ansatz. Weight 2 weil akademische Qualität hoch.

### CrossRef — DOI/Citation Nische
Findet Papers über DOI und Zitationsnetzwerke. Nischenquelle, Weight 1.

### Startpage — Weight 2 → 1
Startpage ist ein Google-Proxy. Mit Weight 2 (wie Google) wurden Google-Ergebnisse massiv überrepräsentiert: eine URL die Google UND Startpage finden bekommt `weight = 2 × 2 × 2 = 8` statt `2 × 1 = 2`. Weight 1 reduziert den Google-Bias bei gleichzeitigem Erhalt als Tor-Fallback für Google-Ergebnisse.

### Index-Diversität
Vorher: 3 unabhängige Indizes (Google, Bing via DDG, Brave). Jetzt: 4 (+ Mojeek). Plus 2 akademische (Scholar, Semantic Scholar) und 1 Citation-Netzwerk (CrossRef).

### Qwant — Access Denied
Qwant liefert bei Direktanfragen ohne Account regelmäßig HTTP 403 / "Access Denied". Kein zuverlässiger Betrieb möglich → `disabled: true`.

### Google Scholar — Erhöhter Timeout
Google Scholar hat nachweislich höhere Latenz als Consumer-Suchmaschinen. `timeout: 10` verhindert vorzeitigen Abbruch.

### Google, DDG, Bing, Mojeek — Kein Tor
Diese Engines blockieren Tor-Exit-Nodes aggressiv (CAPTCHA, IP-Ban). Direktverbindung via `proxies: {}` als Bypass. Siehe auch search02_routing.md.

## Entscheidung

Engine-Set und Weights basieren auf Index-Diversifizierung und Kategorie-Trennung:

- **general:** Maximale Index-Diversität (4 unabhängige Web-Indizes + 3 akademische Quellen). Weights: 2 für bewährte Quellen (Google, Brave, Scholar, Semantic Scholar), 1 für neue/redundante (Bing, DDG, Startpage, Mojeek, CrossRef).
- **plugin:** Discovery-Only. Weights nach Relevanz für Tech/ML Use Case (ArXiv=2, GitHub/Reddit=1).
- **Tor-Routing:** Engines die Tor blockieren bekommen `using_tor_proxy: false` + `proxies: {}`. Details → search02_routing.md.

## Offene Fragen

- Weight-Kalibrierung: Precision@10 pro Engine fehlt. Aktuelle Weights sind Startpunkte, nicht kalibriert.
- Google Scholar bei `time_range`: Scholar ignoriert time_range-Filter teilweise.
- Bing/Mojeek Zuverlässigkeit: Noch nicht empirisch getestet. Können nach einigen Wochen Betrieb evaluiert werden.

## Quellen

- `src/searxng/settings.yml` — Engine-Konfiguration
- `searxng/searxng` GitHub Repo (`searx/results.py`) — Scoring-Algorithmus
- `searxng/searxng` GitHub Repo (`searx/settings.yml`) — Default Engine-Konfigurationen
- SearXNG Docs (RAG Collection: searxng) — Engine-Parameter, Weight-Semantik
- Erfahrungswerte aus Betrieb (Qwant-Deaktivierung, DDG-Weight, Startpage-Redundanz)

## Engine Status Update (2026-04-03)

### SearXNG 2026.4.3 — Engine Fixes

Update von 2026.3.10 → 2026.4.3 behebt Blocking für 3 Engines über neuen GSA iPhone User-Agent:
- **Google** — wieder stabil ✓
- **Brave** — wieder stabil ✓
- **Google Scholar** — wieder stabil ✓

### DDG Recovery Confirmed

DuckDuckGo ist wieder funktional (vorher CAPTCHA-Blocking, upstream issue #4824). Aktuell noch `disabled: true` in `settings.yml` — Re-Enablement pending. DDG wird nicht re-enabled solange Bing direkt verfügbar ist (DDG basiert auf Bing, bietet keinen Mehrwert bei identischem Index).

### Aktueller Engine-Status (alle 8 + DDG)

| Engine | Status | Routing | Tor | Patch | Weight |
|--------|--------|---------|-----|-------|--------|
| Google | ✅ aktiv | direkt | nein | nein | 2 |
| Bing | ✅ aktiv | direkt | nein | nein | 1 |
| Brave | ✅ aktiv | Tor | ja | nein | 2 |
| Startpage | ✅ aktiv | Tor | ja | nein | 1 |
| Mojeek | ✅ aktiv | direkt | nein | arc=none | 1 |
| Google Scholar | ✅ aktiv | direkt | nein | nein | 2 |
| Semantic Scholar | ✅ aktiv | direkt | nein | session cookies | 2 |
| CrossRef | ✅ aktiv | Tor | ja | nein | 1 |
| DuckDuckGo | ⏸ disabled | direkt | nein | nein | 1 |
