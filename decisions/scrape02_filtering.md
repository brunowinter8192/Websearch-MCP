# Scrape Pipeline Step 2: Content Filtering

## Status Quo

**Code:** `src/scraper/scrape_url.py` — `scrape_url_workflow`, `scrape_url_raw_workflow`, `truncate_content`

**Method:** PruningContentFilter mit fit_markdown-Fallback auf raw_markdown

**Config:**
- `scrape_url_workflow`: `PruningContentFilter(threshold=0.48)` + `fit_markdown`
  - Fallback auf `raw_markdown` wenn `fit_markdown < MIN_CONTENT_THRESHOLD` (200 chars)
  - `DEFAULT_MAX_CONTENT_LENGTH = 15000` chars
  - Truncation an Absatzgrenze (`\n\n`) wenn `last_newline > max_length * 0.8`
- `scrape_url_raw_workflow`: `DefaultMarkdownGenerator()` ohne Filter + `raw_markdown`
  - Speichert mit `<!-- source: URL -->` Header in Datei
  - Kein Truncation (für Dev/Suite-Verwendung)
- `COOKIE_CONSENT_SELECTOR`: CSS-Selektor-Liste für DOM-Elemente vor dem Crawl entfernen
  - CookieYes: `cky-consent`, `cky-banner`, `cky-modal`
  - OneTrust: `onetrust-*`
  - Cookiebot: `CookiebotDialog`, `CookiebotWidget`
  - Generisch: `cc-banner`, `cc-window`, `gdpr`, `cookie-banner/consent/notice/law`

`PruningContentFilter` entfernt Blöcke mit niedrigem Informationsgehalt (Navigation, Footer, Werbung) anhand eines Scoring-Algorithmus. `fit_markdown` ist das gefilterte Ergebnis, `raw_markdown` der ungefilterte HTML-zu-Markdown-Output.

## Evidenz

### Session-Findings (2026-03)
- `cky-modal` fehlte initial in `COOKIE_CONSENT_SELECTOR` — führte zu ~12K chars CookieYes-Consent-Wall als Content
- TDS (Towards Data Science) Cookie-Wall wurde durch den Selector nicht vollständig eliminiert — `is_garbage_content()` hat als zweite Verteidigungslinie gegriffen
- `fit_markdown`-Fallback auf `raw_markdown` rettet Short-Pages (z.B. simple API-Docs, One-Pager)

### Crawl4AI Docs
- `PruningContentFilter(threshold=0.48)`: Blöcke unterhalb des Scores werden entfernt. Höherer Threshold = aggressivere Filterung
- Bekannte Limitation: PruningFilter kann Code-Blöcke zerstören, wenn sie als "low-density" eingestuft werden (wenig natürliche Sprache)
- `DefaultMarkdownGenerator()` ohne Filter: vollständiger HTML→Markdown, kein Scoring — für Dev-Suites sinnvoller als für Live-MCP
- `content_source`-Option in `CrawlerRunConfig`: alternative Quelle (z.B. `fit_html`, `cleaned_html`) statt Markdown-Pipeline

### Truncation-Logik
- 15000 chars entspricht ~3750 Wörtern — ausreichend für die meisten Artikel, vermeidet Context-Window-Overflow im MCP
- Absatzgrenze-Truncation (`\n\n` wenn > 80% der Grenze) verhindert mid-sentence cuts

## Entscheidung

`PruningContentFilter(threshold=0.48)` als Standard: reduziert Boilerplate erheblich und hält Context klein. Threshold 0.48 ist empirisch — niedrig genug, um echten Content zu behalten, hoch genug, um Navigation/Footer zu entfernen.

`raw_markdown`-Fallback bei < 200 chars: sichert Short-Pages, wo der Filter zu aggressiv filtert.

`COOKIE_CONSENT_SELECTOR` als DOM-Intervention vor dem Crawl: entfernt Cookie-Walls auf DOM-Ebene, bevor Crawl4AI den Content verarbeitet — zuverlässiger als Post-Processing.

`scrape_url_raw` bewusst ohne Filter: Dev-Suites und Vergleiche brauchen den Roh-Output, keine Filterung.

## Offene Fragen

- Threshold 0.48 nicht durch systematische Tests belegt — könnte per Domain konfigurierbar sein
- Code-Seiten (GitHub, Docs): PruningFilter destruktiv für Code-Blöcke — `scrape_url_raw` oder separater Code-Pfad wäre besser
- `content_source="fit_html"` als Alternative: strukturierter als Markdown, könnte besser für Code-heavy Sites sein
- Cookie-Consent via `excluded_selector` entfernt den DOM-Node, aber manchmal bleibt ein Overlay-Backdrop — JS-basierte Dismissal wäre robuster
- `MIN_CONTENT_THRESHOLD` (200 chars) ggf. zu niedrig — 200 chars kann auch ein valider Error-Text sein

## Quellen

- `src/scraper/scrape_url.py` (Code-Inspektion)
- Crawl4AI Docs (RAG Collection: Crawl4AIDocs) — PruningContentFilter, DefaultMarkdownGenerator, content_source
- Session-Findings: CookieYes cky-modal Fix, TDS Cookie-Wall, Truncation-Logik

### Zum Indexieren (für systematische Verbesserung)

- Crawl4AI GitHub Issues "PruningContentFilter" — Threshold-Tuning, Code-Block-Destruction: https://github.com/unclecode/crawl4ai/issues?q=pruning+filter
- Crawl4AI Content Filter Source — PruningContentFilter Algorithmus: https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/content_filter_strategy.py
- Trafilatura Docs — Alternative Content-Extraction (Benchmark-Vergleich): https://trafilatura.readthedocs.io/
- Mozilla Readability — Reference Content-Extraction-Algorithmus: https://github.com/mozilla/readability
- CookieYes Developer Docs — DOM-Struktur, Klassen-Konventionen: https://www.cookieyes.com/documentation/
