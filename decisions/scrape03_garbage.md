# Scrape Pipeline Step 3: Garbage Detection

## Status Quo

**Code:** `src/scraper/scrape_url.py` — `is_garbage_content`, `_GARBAGE_MESSAGES`, `get_plugin_hint`

**Method:** Rule-based Garbage-Detektion in 6 typisierten Kategorien + differenzierte Fehlermeldungen + Logging

**Return type:** `is_garbage_content()` returns `str | None` (None = not garbage, str = garbage type identifier)

**Config:**
- `crawl4ai_error` — Crawl4AI-Fehlermeldungen als Content:
  - Trigger: `"crawl4ai error:"`, `"document is empty"`, `"page is not fully supported"`
  - Bedingung: Pattern in `content.lower()`
- `http_error` — HTTP-Fehlerseiten (zwei Checks):
  - **Primary (status_code):** `result.status_code >= 400` in `try_scrape()` — direkt nach `crawler.arun()`, VOR Content-Analyse. Fängt gepolsterte 404-Seiten unabhängig von Content-Länge.
  - **Secondary (content heuristic):** `len(content) < 1000` UND eines von `"not_found"`, `"404"`, `"403"`, `"forbidden"`, `"access denied"`, `"page not found"` — Fallback wenn status_code nicht verfügbar
- `nav_dump` — Navigation-Dumps:
  - Trigger: `len(lines) >= 20` UND `link_lines / len(lines) > 0.6`
  - Bedingung: Mehr als 60% der Zeilen sind reine Markdown-Links
- `cookie_wall` — Cookie-Consent-Walls:
  - Trigger: `count("cookie") + count("consent") + count("duration") > 15` in ersten 5000 chars
  - UND `"consent preferences"` oder `"cookieyes"` oder `"cookie preferences"` im Sample
- `login_wall` — Login/Paywall-Seiten:
  - Trigger: `len(content) < 2000` UND eines von `"sign in"`, `"log in"`, `"login"`, `"subscribe to continue"`, `"create account"`, `"create an account"`, `"premium content"`, `"paywall"`, `"members only"`, `"subscriber only"`
- `cloudflare` — Cloudflare-Protection:
  - Trigger: `len(content) < 500` UND `"checking your browser"` oder `"enable javascript and cookies"`
  - ODER: `"just a moment"` UND `"cloudflare"` (ohne Längenlimit)

**Error Messages:** `_GARBAGE_MESSAGES` dict maps jede Kategorie auf eine menschenlesbare Fehlermeldung. `scrape_url_workflow()` trackt `last_garbage` über alle 3 Scrape-Versuche und gibt differenzierte Meldung zurück.

**Logging:** `logger.warning("Garbage detected [%s]: %s", garbage_type, url)` bei jeder Garbage-Erkennung in `try_scrape()`.

**PDF-URLs:** Neues MCP Tool `download_pdf(url, output_dir="/tmp")` als Lösung — PDFs werden heruntergeladen statt gescrapt. Agent-Instructions verweisen auf `download_pdf` statt "nicht scrapebar".

- `PLUGIN_HINTS`: generischer Hint via `get_plugin_hint()`, wird an Fehlermeldung angehängt wenn alle Phasen fehlschlagen

## Evidenz

### Session-Findings (2026-03)
- CookieYes-Wall (cky-modal fehlte in Selector): `is_garbage_content()` hat als zweite Verteidigungslinie korrekt als Garbage erkannt und `""` zurückgegeben — Fallback auf Phase 2 (Stealth) hat geholfen
- TDS (Towards Data Science): Cookie-Consent-Density-Check hat ausgelöst
- LanceDB 404-Seite: Kategorie 2 (kurz + "404" im Text) hat korrekt gefeuert
- `"duration"` als Cookie-Signal: CookieYes-Walls enthalten typischerweise Cookie-Laufzeiten ("Duration: 1 year") — erhöht den Signal-Score

### Schwäche des aktuellen Ansatzes
- `http_error`: 1000-char-Limit ist willkürlich — eine kurze, valide One-Pager-Seite könnte fälschlicherweise als Garbage eingestuft werden, wenn sie zufällig "403" im Text hat (z.B. ein Artikel über HTTP-Statuscodes)
- `cookie_wall`: Threshold 15 wurde nicht systematisch kalibriert — ein legitimer Cookie-Policy-Artikel könnte fälschlicherweise getriggert werden
- `login_wall`: 2000-char-Limit + generische Patterns ("log in", "sign in") könnten auf kurzen Login-Tutorial-Seiten false-positive triggern

### PLUGIN_HINTS Logik
- Hints werden nur ausgespielt, wenn ALLE Phasen Garbage/leer zurückgeben
- Zwei fixe Domain-Mappings — nicht konfigurierbar ohne Code-Änderung

## Entscheidung

6-Kategorien-Ansatz mit typisierten Returns für die häufigsten Failure-Cases im MCP-Kontext:
1. `crawl4ai_error`: direkte String-Matches zuverlässig, da Crawl4AI feste Error-Templates hat
2. `http_error`: Kombination aus Länge und Keyword ist robuster als nur Keyword — kurze Error-Pages haben charakteristisches Profil
3. `nav_dump`: Link-Density-Check fängt Seiten die nur Navigation ohne Content liefern
4. `cookie_wall`: Density-Check statt DOM-Matching (DOM ist schon durch `excluded_selector` behandelt) — fängt Walls, die der Selector verpasst
5. `login_wall`: Kurzer Content + Login-Pattern-Matching für Paywalls und Login-geschützte Seiten
6. `cloudflare`: Bot-Protection-Detection (Cloudflare "Just a moment" und Browser-Check-Seiten)

Typisierte Returns ermöglichen differenzierte Fehlermeldungen für den Caller und Logging für Debugging.

`PLUGIN_HINTS` als letzter Ausweg: liefert dem Nutzer einen konkreten Handlungshinweis statt blankem Fehler.

PDF-URLs: Eigenes MCP Tool `download_pdf` statt Scraping-Versuch. Agent-Instructions aktualisiert.

## Offene Fragen

- ~~Login/Paywall-Erkennung fehlt komplett~~ → DONE: `login_wall` Kategorie implementiert
- ~~Garbage-Typ als Return-Value~~ → DONE: `str | None` Return-Type mit 6 Kategorien
- ~~Kein Logging wenn Garbage erkannt~~ → DONE: `logger.warning()` in `try_scrape()`
- `http_error`: False-Positive-Risiko bei kurzen legitimen Pages mit Zahlen wie "404" im Fließtext
- `cookie_wall`: Threshold-Kalibrierung (15 cookie-signals) nicht durch Testdaten validiert
- `login_wall`: False-Positive-Risiko bei kurzen Login-Tutorial-Seiten — 2000-char-Limit + generische Patterns
- `PLUGIN_HINTS` ist hardcoded — eine konfigurierbare Map in `config.py` oder `server.py` wäre flexibler

## Persistent Failure Logging

**Added (2026-03):** Every final scrape failure — all 3 attempts exhausted — is appended as a JSONL record to `dev/scrape_pipeline/failures.jsonl`.

**Implementation:** `log_scrape_failure(url, garbage_type, status_code)` in `src/scraper/scrape_url.py`, called from `scrape_url_workflow()` at the final `if not content:` exit.

**Fields per record:** `ts` (ISO 8601 UTC), `url`, `garbage_type` (str | null), `status_code` (int | null)

**`try_scrape()` return type** extended from `tuple[str, str | None]` to `tuple[str, str | None, int | None]` to propagate `result.status_code` to the caller. `scrape_url_workflow()` tracks `last_status_code` alongside `last_garbage` across all 3 attempts.

**Silent fail:** `log_scrape_failure()` wraps all I/O in try/except — a logging failure never crashes the MCP tool.

**File path:** `dev/scrape_pipeline/failures.jsonl` (gitignored, local analysis only). See `dev/scrape_pipeline/DOCS.md` for jq usage examples.

## Consent-Prefix Stripping (2026-04)

**Added:** `strip_consent_prefix()` in `src/scraper/scrape_url.py` as a recovery mechanism for `cookie_wall` pages.

**What it does:** When `is_garbage_content()` returns `cookie_wall`, `try_scrape()` attempts to strip the leading consent block and recover actual page content instead of immediately discarding.

**When it triggers:** Only on `cookie_wall` detection. All other garbage types are still discarded immediately.

**Algorithm:**
1. Count CONSENT_WORDS (`cookie`, `consent`, `einwilligung`, `tracking`, `akzeptieren`, `datenschutz`, `zweck`) in first 3000 chars
2. If density ≤ 5 (CONSENT_DENSITY_THRESHOLD): return original content unchanged (baseline pages safe)
3. Search for first `#` or `##` heading after offset 300 (CONSENT_SKIP_OFFSET)
4. If heading found: return content from that heading onward
5. If no heading: return original content unchanged

**Recovery condition:** Stripped content must (a) differ from original and (b) pass `is_garbage_content()` returning None. If either condition fails, falls through to normal garbage discard.

**Prototype source:** `dev/scrape_pipeline/09_garbage_fix_prototype.py` — constants and algorithm taken directly. Evidence in `dev/scrape_pipeline/09_reports/`.

**`cookie_wall` threshold item:** Partially addressed — stripping recovers content from pages that mix consent prefix with real content. Pages that are pure consent walls (no heading after offset) are still discarded. Threshold calibration (>15 cookie-signals for detection) remains open.

## Quellen

- `src/scraper/scrape_url.py` (Code-Inspektion)
- Session-Findings: CookieYes cky-modal, TDS Cookie-Wall, LanceDB 404
- Crawl4AI Docs (RAG Collection: Crawl4AIDocs) — Error-Format, result.markdown-Struktur

### Zum Indexieren (für systematische Verbesserung)

- Crawl4AI GitHub Issues "empty content" — Error-as-Content Pattern, Browser-Failures: https://github.com/unclecode/crawl4ai/issues?q=empty+content
- CookieYes DOM Reference — Klassen-Naming für neue Selector-Patterns: https://www.cookieyes.com/documentation/
- OneTrust Developer Docs — Cookie-Banner DOM-Struktur: https://developer.onetrust.com/
- Cookiebot Developer Docs — Dialog-Klassen: https://www.cookiebot.com/en/developer/
