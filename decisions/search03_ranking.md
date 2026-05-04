## Status

**SUPERSEDED by `decisions/search07_ranking_format.md` (2026-05-04)** — this file documents the pre-engine-cut SearXNG-Docker pipeline (`src/searxng/`, `MAX_RESULTS=80`, hostname-priority via SearXNG-Plugin). That implementation no longer exists in the codebase as of the engine-cut refactor (2026-04-15). Kept for historical reference only.

# Search Pipeline Step 3: Ranking & Result Processing

## Status Quo

**Code:** `src/searxng/settings.yml` (hostnames), `src/searxng/search_web.py` (MAX_RESULTS, SNIPPET_LENGTH)
**Method:** SearXNG-internes Ranking + Hostname-Priorität + Post-Processing-Truncation
**Config:**

```python
# search_web.py
MAX_RESULTS = 80
SNIPPET_LENGTH = 5000
```

### Hostname Priority

```yaml
high_priority:
  # Code & Q&A
  - github.com, stackoverflow.com, stackexchange.com
  # Documentation
  - docs.python.org, developer.mozilla.org, readthedocs.io, pytorch.org
  - docs.rs, pkg.go.dev, learn.microsoft.com
  # ML/AI
  - arxiv.org, huggingface.co, anthropic.com, openai.com, semanticscholar.org
  # Reference
  - wikipedia.org

low_priority:
  - pinterest.*, quora.com, w3schools.com, hub.docker.com, linkedin.com, amazon.*

remove:
  - pinterest.*
```

### Ranking-Pipeline

1. SearXNG berechnet internen Score: `weight = Π(engine_weights) × len(positions)`, `score = Σ(weight / position_i)` (→ search01_engines.md)
2. Hostname-Regeln modifizieren Score: `high_priority` = priority='high' (voller Weight statt Weight/Position), `low_priority` = priority='low' (Score 0)
3. `remove`-Einträge werden vollständig aus Ergebnissen entfernt (vor Ausgabe)
4. `fetch_search_results()` nimmt die ersten `MAX_RESULTS=80` aus dem SearXNG-JSON
5. `format_results()` trunciert jeden Snippet auf `SNIPPET_LENGTH=5000` Zeichen

## Evidenz

### Hostname-Priorität — Kategorisiert nach Nutzung

**Code/Q&A:** github.com, stackoverflow.com, stackexchange.com — konsistent hochwertige technische Inhalte. github.com ist zusätzlich Plugin-Domain (Discovery → github-research Plugin).

**Dokumentation:** docs.python.org, developer.mozilla.org, readthedocs.io, pytorch.org — offizielle Docs, immer relevant. Ergänzt um docs.rs (Rust), pkg.go.dev (Go), learn.microsoft.com (Azure, .NET, TypeScript) für breiteren Tech-Stack.

**ML/AI:** arxiv.org, huggingface.co, anthropic.com, openai.com — Kern-Quellen für ML/AI Recherche. semanticscholar.org neu (korrespondiert mit Semantic Scholar Engine). arxiv.org ist Plugin-Domain.

**Reference:** wikipedia.org — breite Referenz, konsistent gut für Konzepterklärungen.

### Hostname-Depriorisierung — Rausch-Reduktion

- **pinterest, amazon:** SEO-Spam, keine technischen Inhalte
- **quora:** Qualität stark schwankend, oft veraltet
- **w3schools:** Oberflächliche Tutorials, von MDN übertroffen
- **linkedin:** Job-Listings statt technischer Inhalte
- **hub.docker.com:** Registry-Seiten, kein Lerninhalt

### Pinterest — Remove statt nur Low Priority

Pinterest erscheint bei vielen Queries als Spam (Bildgalerien, keine Textinhalte). `remove` entfernt vollständig.

### MAX_RESULTS = 80 (von 50 erhöht)

Mit 10 aktiven Engines (7 general + 3 plugin) statt vorher 5 liefert SearXNG deutlich mehr unique Ergebnisse pro Query. 50 war das Ceiling bei 4-5 Engines; mit 10 Engines sind 80 ein besserer Schnitt. Höherer Wert würde den MCP-Response unnötig aufblähen.

### SNIPPET_LENGTH = 5000

Snippets werden im MCP-Response direkt an Claude übergeben. 5000 Zeichen (~750-1000 Wörter) bieten genug Kontext. Reale SearXNG-Snippets sind typischerweise 200-500 Zeichen — das Limit ist ein Sicherheits-Ceiling.

## Entscheidung

- Hostname-Listen kategorisiert nach Nutzungstyp (Code/Docs/ML/Reference)
- 4 neue high_priority Domains: docs.rs, pkg.go.dev, learn.microsoft.com, semanticscholar.org
- MAX_RESULTS 50→80 wegen doppelt so vielen aktiven Engines
- SNIPPET_LENGTH bleibt 5000 (reale Snippets liegen weit darunter)

## Offene Fragen

- Hostname-Priority-Multiplikatoren: Wie genau modifiziert high_priority/low_priority den Score? SearXNG Hostnames Plugin Source (searx/plugins/hostnames.py) sollte gelesen werden für exakte Formel.
- Fehlende Domains: developer.apple.com? tensorflow.org? docs.docker.com?
- `remove: pinterest` ist redundant zu `low_priority: pinterest` — oder überschreibt `remove` den `low_priority`-Eintrag?
- Weight-Kalibrierung der Hostname-Liste basierend auf empirischer Precision@10 pro Domain fehlt

## Quellen

- `src/searxng/settings.yml` — hostnames Konfiguration
- `src/searxng/search_web.py` — MAX_RESULTS, SNIPPET_LENGTH Konstanten
- `searxng/searxng` GitHub Repo (`searx/results.py`) — Score-Berechnung
- `searxng/searxng` GitHub Repo (`searx/plugins/hostnames.py`) — Priority-Modifikation
- SearXNG Docs (RAG Collection: searxng) — hostname Plugin
