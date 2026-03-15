# Search Pipeline Step 3: Ranking & Result Processing

## Status Quo

**Code:** `src/searxng/settings.yml` (hostnames), `src/searxng/search_web.py` (MAX_RESULTS, SNIPPET_LENGTH)
**Method:** SearXNG-internes Ranking + Hostname-Priorität + Post-Processing-Truncation
**Config:**

```python
# search_web.py
MAX_RESULTS = 50
SNIPPET_LENGTH = 5000
```

```yaml
# settings.yml — hostnames
high_priority:
  - github.com / *.github.com
  - stackoverflow.com / *.stackexchange.com
  - wikipedia.org
  - docs.python.org
  - developer.mozilla.org
  - arxiv.org
  - huggingface.co
  - pytorch.org
  - readthedocs.io
  - anthropic.com
  - openai.com

low_priority:
  - pinterest.*
  - quora.com
  - w3schools.com
  - hub.docker.com
  - linkedin.com
  - amazon.*

remove:
  - pinterest.*
```

**Ranking-Pipeline:**
1. SearXNG berechnet internen Score (Engine-Votes × Engine-Weight + Position-Decay)
2. Hostname-Regeln modifizieren Score: `high_priority` erhöht, `low_priority` senkt
3. `remove`-Einträge werden vollständig aus Ergebnissen entfernt (vor Ausgabe)
4. `fetch_search_results()` nimmt die ersten `MAX_RESULTS=50` aus dem SearXNG-JSON
5. `format_results()` trunciert jeden Snippet auf `SNIPPET_LENGTH=5000` Zeichen

## Evidenz

### Hostname-Priorität — Technikfokus
Das Projekt ist ein MCP-Server für technische Recherche (Code, ML, Docs). Die `high_priority`-Liste enthält ausschließlich technische Quellen:
- **Code/Fragen:** github.com, stackoverflow.com, stackexchange.com
- **Dokumentation:** docs.python.org, developer.mozilla.org, readthedocs.io, pytorch.org
- **ML/AI:** arxiv.org, huggingface.co, anthropic.com, openai.com
- **Referenz:** wikipedia.org

### Hostname-Depriorisierung — Rausch-Reduktion
`low_priority`-Quellen bringen für technische Queries konsistent schlechte Ergebnisse:
- **pinterest, amazon:** SEO-Spam, keine technischen Inhalte
- **quora:** Qualität stark schwankend, oft veraltet
- **w3schools:** Oberflächliche Tutorials, von MDN übertroffen
- **linkedin:** Job-Listings statt technischer Inhalte
- **hub.docker.com:** Docker Hub Registry — Image-Seiten, kein Lerninhalt

### Pinterest — Remove statt nur Low Priority
Pinterest erscheint bei vielen Queries als Spam (Bildgalerien, keine Textinhalte). `remove` verhindert vollständig das Erscheinen, nicht nur Score-Senkung.

### MAX_RESULTS = 50
SearXNG liefert maximal ~10 Ergebnisse pro Engine pro Seite. Bei 4-5 aktiven Engines sind 50 Ergebnisse der praktische Ceiling (Duplikate werden vor Ausgabe gemergt). Höherer Wert würde keinen Nutzen bringen.

### SNIPPET_LENGTH = 5000
Snippets werden im MCP-Response direkt an Claude übergeben. 5000 Zeichen (~750-1000 Wörter) bieten genug Kontext für Relevanzbeurteilung ohne den MCP-Response zu überfrachten. SearXNG-Snippets sind typischerweise 200-500 Zeichen — das Limit ist ein Sicherheits-Ceiling, kein aktiver Truncator.

## Entscheidung

Hostname-Liste und Limits wurden manuell kuratiert — kein A/B-Test oder Recall-Messung. Entscheidungsbasis:
- Erfahrungswerte aus technischer Recherche: welche Domains liefern konsistent nützliche Ergebnisse
- `MAX_RESULTS=50` entspricht dem praktischen SearXNG-Ceiling bei 4-5 Engines
- `SNIPPET_LENGTH=5000` ist konservativ hoch gewählt (reale Snippets sind kleiner)

## Offene Fragen

- Hostname-Liste ist nicht empirisch validiert — Precision/Recall-Messung per Domain fehlt
- `remove: pinterest` ist redundant zu `low_priority: pinterest` — oder überschreibt `remove` den `low_priority`-Eintrag? SearXNG-Dokumentation sollte das klären.
- Fehlende Domains in `high_priority`: docs.rs (Rust), pkg.go.dev (Go), developer.apple.com, learn.microsoft.com
- `hub.docker.com` in `low_priority` aber Docker Hub ist manchmal relevant (offizielle Images, Tags). Registry-Seiten vs. Dokumentationsseiten unterscheiden?
- SNIPPET_LENGTH: Wenn SearXNG künftig längere Snippets liefert, würde 5000 Zeichen aktiv truncaten. Monitoring fehlt.

## Quellen

- `src/searxng/settings.yml` — hostnames Konfiguration
- `src/searxng/search_web.py` — MAX_RESULTS, SNIPPET_LENGTH Konstanten
- SearXNG Docs (RAG Collection: SearXNG_Docs) — hostname Plugin, Score-Berechnung

### Zum Indexieren (für systematische Verbesserung)

- SearXNG Hostname Plugin Source — Score-Modifikation, Priority-Multiplikatoren: https://github.com/searxng/searxng/blob/master/searx/plugins/hostnames.py
- SearXNG Result Ranking Source — Engine-Weight × Position, Score-Aggregation: https://github.com/searxng/searxng/blob/master/searx/results.py
