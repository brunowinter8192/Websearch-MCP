# Use Case: Quant Finance Domain Expertise

## Situation

- FreqAI's Feature-Set wird kopiert ohne zu verstehen WARUM diese Choices getroffen wurden
- 59% Accuracy bei Binary Classification ist kaum ueber Zufall — koennte reines Rauschen sein
- Look-Ahead Bias zeigt: subtile Fehler werden eingebaut ohne es zu merken
- Trainingsdaten sind kein Ersatz fuer Domain-Expertise in Quantitative Finance

## Konkreter Recherche-Bedarf

1. **Lopez de Prado lesen:** "Advances in Financial Machine Learning" — die Bibel fuer ML im Trading. Behandelt exakt die Probleme: Look-Ahead Bias, Feature Engineering, warum naive Backtests luegen, wie man Walk-Forward Validation richtig macht. Ohne dieses Fundament wird im Dunkeln geraten.

2. **FreqAI Codebase systematisch studieren** — nicht Features kopieren, sondern verstehen: Warum walk-forward? Warum bestimmte Normalisierung? Warum Purging/Embargo beim Split?

3. **Relevante Docs in RAG indexieren** — Lopez de Prado, FreqAI Docs, evtl. QuantConnect Tutorials. Verifiziertes Referenzmaterial statt moeglicherweise falsche Annahmen.

4. **Edge definieren:** Jeder Trading-Bot braucht einen Edge — eine Hypothese WARUM das Modell besser sein kann als der Markt. "LightGBM auf technische Indikatoren" ist kein Edge, das macht jeder. Ohne klare Antwort darauf ist der Rest Optimierung ins Leere.

## Ziel

Lopez de Prado besorgen, relevante Kapitel (Feature Engineering, Backtesting, Cross-Validation fuer Zeitreihen) in RAG indexieren, und DANN mit Verstaendnis weiterarbeiten. Kostet 1-2 Sessions, spart Wochen Irrweg.

## Query-Fokus

Die Queries in queries.txt zielen auf diesen Recherche-Bedarf ab: Lopez de Prado Inhalte, FreqAI Internals, Walk-Forward Validation, Look-Ahead Bias Prevention, Feature Engineering fuer Zeitreihen.
