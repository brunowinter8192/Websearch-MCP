# Scrape Pipeline Step 3: Garbage Detection

## Status Quo

**Code:** `src/scraper/scrape_url.py` — `is_garbage_content`, `PLUGIN_HINTS`

**Method:** Rule-based Garbage-Detektion in 3 Kategorien + Plugin-Hints als Fallback

**Config:**
- Kategorie 1 — Crawl4AI-Fehlermeldungen als Content:
  - Trigger: `"crawl4ai error:"`, `"document is empty"`, `"page is not fully supported"`
  - Bedingung: Pattern in `content.lower()`
- Kategorie 2 — HTTP-Fehlerseiten:
  - Trigger: `len(content) < 1000` UND eines von `"not_found"`, `"404"`, `"403"`, `"forbidden"`, `"access denied"`, `"page not found"`
  - Bedingung: kurzer Content + Error-Keyword
- Kategorie 3 — Cookie-Consent-Walls:
  - Trigger: `count("cookie") + count("consent") + count("duration") > 15` in ersten 5000 chars
  - UND `"consent preferences"` oder `"cookieyes"` im Sample
- `PLUGIN_HINTS`: bei `is_garbage_content()` → `""` zurück → Fallback-Kette → wenn alle Phasen leer → Fehlermeldung mit Hint
  - `reddit.com` → Reddit MCP Plugin
  - `arxiv.org` → RAG MCP Plugin

## Evidenz

### Session-Findings (2026-03)
- CookieYes-Wall (cky-modal fehlte in Selector): `is_garbage_content()` hat als zweite Verteidigungslinie korrekt als Garbage erkannt und `""` zurückgegeben — Fallback auf Phase 2 (Stealth) hat geholfen
- TDS (Towards Data Science): Cookie-Consent-Density-Check hat ausgelöst
- LanceDB 404-Seite: Kategorie 2 (kurz + "404" im Text) hat korrekt gefeuert
- `"duration"` als Cookie-Signal: CookieYes-Walls enthalten typischerweise Cookie-Laufzeiten ("Duration: 1 year") — erhöht den Signal-Score

### Schwäche des aktuellen Ansatzes
- Kategorie 2 (HTTP-Fehler): 1000-char-Limit ist willkürlich — eine kurze, valide One-Pager-Seite könnte fälschlicherweise als Garbage eingestuft werden, wenn sie zufällig "403" im Text hat (z.B. ein Artikel über HTTP-Statuscodes)
- Kategorie 3 (Cookie-Wall): Threshold 15 wurde nicht systematisch kalibriert — ein legitimer Cookie-Policy-Artikel könnte fälschlicherweise getriggert werden
- Keine Logging/Reporting-Funktion: wenn Garbage erkannt wird, ist es intern — kein Signal nach außen, welche Kategorie ausgelöst hat
- Login-Walls (Paywalls) werden nicht erkannt — nur Cookie-Consent-Walls

### PLUGIN_HINTS Logik
- Hints werden nur ausgespielt, wenn ALLE Phasen Garbage/leer zurückgeben
- Zwei fixe Domain-Mappings — nicht konfigurierbar ohne Code-Änderung

## Entscheidung

3-Kategorien-Ansatz als pragmatische Lösung für die häufigsten Failure-Cases im MCP-Kontext:
1. Crawl4AI-Fehler: direkte String-Matches zuverlässig, da Crawl4AI feste Error-Templates hat
2. HTTP-Fehler: Kombination aus Länge und Keyword ist robuster als nur Keyword — kurze Error-Pages haben charakteristisches Profil
3. Cookie-Walls: Density-Check statt DOM-Matching (DOM ist schon durch `excluded_selector` behandelt) — fängt Walls, die der Selector verpasst

`PLUGIN_HINTS` als letzter Ausweg: liefert dem Nutzer einen konkreten Handlungshinweis statt blankem Fehler.

## Offene Fragen

- Login/Paywall-Erkennung fehlt komplett (z.B. Medium, WSJ) — typisches Muster: kurzer Content + Login-Formulare oder "Subscribe" CTA
- Kategorie 2: False-Positive-Risiko bei kurzen legitimen Pages mit Zahlen wie "404" im Fließtext
- Threshold-Kalibrierung: 15 cookie-signals und 1000-char-Limit wurden nicht durch Testdaten validiert
- Garbage-Typ als Return-Value: aktuell nur `""` — ein Enum (CRAWL4AI_ERROR, HTTP_ERROR, COOKIE_WALL) würde bessere Diagnose und differenziertes Fallback ermöglichen
- `PLUGIN_HINTS` ist hardcoded — eine konfigurierbare Map in `config.py` oder `server.py` wäre flexibler
- Kein Logging wenn Garbage erkannt — schwer zu debuggen, welche Kategorie für Failures verantwortlich ist

## Quellen

- `src/scraper/scrape_url.py` (Code-Inspektion)
- Session-Findings: CookieYes cky-modal, TDS Cookie-Wall, LanceDB 404
- Crawl4AI Docs — Error-Format, result.markdown-Struktur (RAG Collection: Crawl4AIDocs)
