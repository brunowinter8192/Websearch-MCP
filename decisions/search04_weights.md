# Search Pipeline Step 4: Engine Weights

## Status Quo

**Code:** `src/searxng/settings.yml` (engines section)
**Method:** Static per-engine weights influencing SearXNG's internal score formula

### Current Weights

| Engine | Category | Weight | Proxy |
|--------|----------|--------|-------|
| google | general | 2 | direct |
| bing | general | 1 | direct |
| mojeek | general | 1 | direct |
| brave | general | 2 | Tor |
| startpage | general | 1 | Tor |
| duckduckgo | general | — | disabled |
| google scholar | general | 2 | — |
| semantic scholar | general | 2 | — |
| crossref | general | 1 | — |
| arxiv | plugin | 2 | — |
| github | plugin | 1 | — |
| reddit | plugin | 1 | — |

Weight rationale (initial): Google and Brave assigned weight=2 as highest-quality web engines; Scholar engines (Google Scholar, Semantic Scholar) weight=2 for academic coverage; discovery-only plugin engines lower.

## Evidenz

_Pending — run `dev/search_pipeline/10_engine_consensus.py` and paste results here._

Metrics to collect per engine:
- Consensus Rate (% of URLs found by ≥2 engines)
- Unique URLs (discovery value)
- Avg Position in combined ranking
- Top-20 Coverage

## Recommendation (SOLL)

Pending — needs evaluation via `10_engine_consensus.py`.

## Offene Fragen

- Do high-weight engines (google, brave) dominate consensus, or do lower-weight engines contribute disproportionate unique value?
- Is Crossref weight=1 too low given its role in academic queries?
- SearXNG score formula: `weight = Π(engine_weights) × len(positions)`, `score = Σ(weight / position_i)` — does weight amplification warrant non-linear scaling?
- Plugin engines (arxiv, github, reddit) are discovery-only; their weight affects ranking of the discovery URL. Is weight=2 for arxiv appropriate?

## Quellen

- `src/searxng/settings.yml` — current weight configuration
- `dev/search_pipeline/10_engine_consensus.py` — consensus evaluation script
- `decisions/search01_engines.md` — engine selection rationale
- `searxng/searxng` GitHub Repo (`searx/results.py`) — score formula
