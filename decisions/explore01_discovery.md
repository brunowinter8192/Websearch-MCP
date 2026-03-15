# Explore Pipeline Step 1: Site Discovery

## Status Quo

**Code:** `src/scraper/explore_site.py`
**Method:** Zwei-Phasen-Discovery: Sitemap-Check → BFS-Crawl mit Prefetch
**Config:**

```python
MAX_DEPTH = 10
DEFAULT_MAX_PAGES = 50
CRAWL_TIMEOUT = 120  # Sekunden
```

**Discovery-Kaskade (`explore_site_workflow`):**
1. `check_sitemap(domain)` — Crawl4AI `AsyncUrlSeeder` mit `source="sitemap"`. Gibt alle Sitemap-URLs zurück (normalisiert: dict→string).
2. `crawl_for_discovery(url, domain, max_pages, url_pattern)` — BFS-Crawl unabhängig von Sitemap-Ergebnis, immer ausgeführt
3. `build_site_map()` — Merged BFS-Ergebnisse + Sitemap-URLs (dedupliziert via `seen` Set)
4. Strategy-Empfehlung basierend auf Ergebnissen:
   - Sitemap vorhanden → `"sitemap (N URLs)"`
   - >1 BFS-Seite gefunden → `"prefetch"`
   - Nur 1 BFS-Seite → `"bfs (JS-heavy, prefetch found only 1 page)"`

**BFS-Konfiguration (`crawl_for_discovery`):**
```python
BFSDeepCrawlStrategy(
    max_depth=MAX_DEPTH,      # 10
    include_external=False,
    filter_chain=FilterChain([
        DomainFilter(allowed_domains=[domain]),
        ContentTypeFilter(allowed_types=["text/html"]),
        URLPatternFilter(patterns=[url_pattern])  # optional
    ]),
    max_pages=max_pages,      # default 50
)

CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    wait_until="domcontentloaded",
    prefetch=True,             # HTML+Links, kein Content-Rendering
)
```

**Timeout:** `asyncio.wait_for(run_crawl(), timeout=120)` — bei Überschreitung wird `timed_out=True` gesetzt, Partial-Ergebnisse werden weiterverwendet.

## Evidenz

### Sitemap als Discovery-Quelle
Sitemap-URLs sind die vollständigste Quelle für eine Site-Struktur — vom Site-Betreiber explizit gepflegt, keine Crawl-Limitierung. `AsyncUrlSeeder` mit `source="sitemap"` prüft `/sitemap.xml` und gängige Varianten automatisch. Sitemap-URLs werden als Seeds in `build_site_map` integriert: Sie erhalten `chars=0` (kein Content gecrawlt) und eine geschätzte Tiefe via URL-Pfad-Segmente.

### BFS immer ausführen (parallel zu Sitemap)
Der BFS-Crawl läuft unabhängig vom Sitemap-Ergebnis. Rationale: BFS liefert tatsächliche Link-Struktur und HTML-Größen (`chars`), die Sitemap nicht hat. Selbst bei vorhandener Sitemap ist die BFS-Tiefenverteilung für die Strategy-Empfehlung relevant.

### Prefetch = True
`prefetch=True` in `CrawlerRunConfig` aktiviert den Crawl4AI-Prefetch-Modus: Seiten werden gecrawlt um Links zu extrahieren, aber kein Full-Rendering oder Content-Extraktion. Deutlich schneller als normaler Crawl, ausreichend für Discovery-Zweck (URL-Struktur, nicht Content).

### CacheMode.BYPASS
Discovery soll aktuelle Site-Struktur zeigen, nicht gecachte Versionen. `BYPASS` stellt sicher dass jede Seite frisch gecrawlt wird.

### wait_until="domcontentloaded"
Schnellster sinnvoller Trigger — wartet auf DOM-Parse ohne JavaScript-Execution. Für reine Link-Extraktion ausreichend. JS-schwere Sites benötigen `networkidle` — das ist der Grund für die Strategy-Empfehlung "bfs" wenn Prefetch nur 1 Seite findet.

### MAX_DEPTH = 10
Praktisch unlimitierte Tiefe für normale Sites (die meisten Sites haben Tiefe ≤ 5). Echte Begrenzung kommt via `max_pages=50`. MAX_DEPTH=10 verhindert nur pathologische Fälle (zirkuläre Redirects, unendlich tiefe generierte URLs).

### DEFAULT_MAX_PAGES = 50
Balanciert Discovery-Vollständigkeit gegen Crawl-Zeit. Bei `request_timeout=5s` pro Seite und Prefetch-Overhead sind 50 Seiten in ~30-60s erreichbar. Überschreitung des CRAWL_TIMEOUT=120s bei 50 Seiten möglich bei langsamen Sites.

### CRAWL_TIMEOUT = 120s
Verhindert dass `explore_site_workflow` unbegrenzt blockiert. Partial-Ergebnisse werden bei Timeout weiterverwertet (`timed_out=True` im Output signalisiert Unvollständigkeit).

### Sitemap dict→string Normalisierung
`AsyncUrlSeeder` gibt teils `dict`-Objekte statt `str` zurück (undokumentiertes Verhalten). `check_sitemap` normalisiert: `u if isinstance(u, str) else u.get("url", str(u))`. Gleiche Normalisierung in `build_site_map` für Sitemap-URLs.

## Entscheidung

Zwei-Phasen-Architektur wurde iterativ entwickelt:
- Sitemap-Phase zuerst: gibt sofortige vollständige URL-Liste ohne Crawl-Overhead
- BFS immer: ergänzt Sitemap mit strukturellen Daten (Tiefe, Char-Count) die für Strategy-Empfehlung nötig sind
- Prefetch statt Full-Crawl: Exploration braucht URL-Struktur, nicht Content — Prefetch ist 3-5x schneller
- Strategy-Empfehlung gibt dem Caller (Claude) einen konkreten Hinweis für den nächsten Tool-Aufruf (scrape_url vs. weitere Crawl-Parameter)

## Offene Fragen

- BFS läuft immer auch wenn Sitemap vollständige URL-Liste liefert: könnte übersprungen werden wenn Sitemap ≥ max_pages URLs enthält
- Sitemap-Tiefenschätzung via URL-Segmente ist ungenau (z.B. `/docs/v2/api/endpoint` hat Tiefe 3 laut Schätzung, aber BFS würde andere Tiefe messen)
- `wait_until="domcontentloaded"` reicht nicht für SPAs (React/Vue/Angular). Bei SPAs findet Prefetch meist nur 1 Seite → Strategy "bfs" korrekt, aber BFS ohne `networkidle` hilft auch nicht. Keine Lösung konfiguriert.
- URLPatternFilter ist optional — bei Sites mit vielen Noise-URLs (Pagination, Query-Parameter) empfehlenswert aber nicht automatisch gesetzt
- `include_external=False` ist korrekt für Discovery, schließt aber CDN-gehostete Docs aus (z.B. assets.example.com)

## Quellen

- `src/scraper/explore_site.py` — vollständige Implementation
- Crawl4AI Docs (RAG Collection: Crawl4AIDocs) — BFSDeepCrawlStrategy, CrawlerRunConfig, prefetch, AsyncUrlSeeder
- `src/scraper/DOCS.md` — Scraper-Übersicht
