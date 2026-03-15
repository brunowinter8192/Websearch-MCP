# Scrape Pipeline Step 1: Browser Strategy

## Status Quo

**Code:** `src/scraper/scrape_url.py` — `scrape_url_workflow`, `try_scrape`

**Method:** 3-stufige Fallback-Kette mit zwei Browser-Phasen

**Config:**
- Phase 1a: `BrowserConfig(headless=True, verbose=False)` + `wait_until="networkidle"`
- Phase 1b: `BrowserConfig(headless=True, verbose=False)` + `wait_until="domcontentloaded"` (Fallback)
- Phase 2: `BrowserConfig(headless=True, verbose=False, enable_stealth=True)` + `UndetectedAdapter` + `AsyncPlaywrightCrawlerStrategy` + `wait_until="networkidle"`
- `cache_mode=CacheMode.BYPASS` in allen Phasen
- Jede Phase erstellt eine neue `AsyncWebCrawler`-Instanz (kein Session-Reuse)

Phase 1a (`networkidle`) wartet, bis keine Netzwerkrequests mehr offen sind — robuster für SPA/JS-heavy Sites, aber langsamer. Phase 1b (`domcontentloaded`) feuert früher und rettet Sites, bei denen `networkidle` einen Timeout auslöst (z.B. endlose Polling-Requests). Phase 2 (Stealth) greift bei Anti-Bot-Schutz.

## Evidenz

### Session-Findings (2026-03)
- `domcontentloaded`-Fallback hat Sites gerettet, bei denen `networkidle` hängt (Polling-Requests blockieren den Wait)
- Stealth-Phase war notwendig für Sites mit aktivem Bot-Detection (z.B. Cloudflare-geschützte Domains)
- `UndetectedAdapter` hat bekannte Fingerprinting-Vektoren (WebDriver-Flag, Chrome-Devtools-Protokoll-Signaturen)

### Crawl4AI Docs
- `networkidle`: wartet bis 500ms keine Netzwerk-Aktivität — geeignet für JS-rendered Content
- `domcontentloaded`: feuert sobald HTML geparst — kein Warten auf dynamischen Content
- `enable_stealth=True`: aktiviert Playwright-Stealth-Patches (navigator.webdriver=false, etc.)
- `CacheMode.BYPASS`: ignoriert Cache vollständig, jeder Request geht ans Netz

### Bekannte Einschränkungen
- Kein Session-Reuse: jede Phase startet einen neuen Browser-Prozess — hoher Overhead bei mehreren Versuchen
- `UndetectedAdapter` kann mit bestimmten Sites inkompatibel sein (daher Phase 2 als letzter Ausweg)

## Entscheidung

`networkidle` als primäre Strategie, weil JS-rendered Content ohne Wait nicht vollständig geladen ist. `domcontentloaded` als Fallback, weil manche Sites mit Polling-Requests `networkidle` blockieren. Stealth als letzte Phase, weil `UndetectedAdapter` stabiler mit einem frischen Browser ist und nicht alle Sites Bot-Detection haben.

`CacheMode.BYPASS` immer aktiv, weil gecachte veraltete Inhalte in einem MCP-Kontext (Live-Recherche) mehr schaden als nützen.

## Offene Fragen

- Session-Reuse: Könnte ein persistenter Browser über mehrere Scrapes hinweg den Overhead reduzieren — Risiko: State-Pollution zwischen unabhängigen Requests
- `domcontentloaded` + kurzer `js_code`-Wait als Alternative zu `networkidle`
- Phase 2 könnte auch `domcontentloaded`-Fallback bekommen (aktuell nur `networkidle`)
- Timeout-Konfiguration: kein expliziter Timeout gesetzt — Crawl4AI-Default gilt

## Quellen

- `src/scraper/scrape_url.py` (Code-Inspektion)
- Crawl4AI Docs — BrowserConfig, CrawlerRunConfig, wait_until-Optionen (RAG Collection: Crawl4AIDocs)
