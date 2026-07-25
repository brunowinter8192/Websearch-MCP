## Status

**SUPERSEDED (2026-05-04)** — this file documents the pre-engine-cut SearXNG-Docker pipeline (`src/searxng/`, `MAX_RESULTS=80`, hostname-priority via SearXNG plugin). That implementation no longer exists in the codebase as of the engine-cut refactor (2026-04-15). Kept for historical reference only.

# Search Pipeline Step 3: Ranking & Result Processing

## Status Quo

**Code:** `src/searxng/settings.yml` (hostnames), `src/searxng/search_web.py` (MAX_RESULTS, SNIPPET_LENGTH)
**Method:** SearXNG-internal ranking + hostname priority + post-processing truncation
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

### Ranking Pipeline

1. SearXNG computes an internal score: `weight = Π(engine_weights) × len(positions)`, `score = Σ(weight / position_i)`
2. Hostname rules modify the score: `high_priority` = priority='high' (full weight instead of weight/position), `low_priority` = priority='low' (score 0)
3. `remove` entries are removed entirely from results (before output)
4. `fetch_search_results()` takes the first `MAX_RESULTS=80` from the SearXNG JSON
5. `format_results()` truncates each snippet to `SNIPPET_LENGTH=5000` characters

## Evidence

### Hostname Priority — Categorized by Usage

**Code/Q&A:** github.com, stackoverflow.com, stackexchange.com — consistently high-quality technical content. github.com is additionally a plugin domain (discovery → github-research plugin).

**Documentation:** docs.python.org, developer.mozilla.org, readthedocs.io, pytorch.org — official docs, always relevant. Extended with docs.rs (Rust), pkg.go.dev (Go), learn.microsoft.com (Azure, .NET, TypeScript) for a broader tech stack.

**ML/AI:** arxiv.org, huggingface.co, anthropic.com, openai.com — core sources for ML/AI research. semanticscholar.org new (corresponds to the Semantic Scholar engine). arxiv.org is a plugin domain.

**Reference:** wikipedia.org — broad reference, consistently good for concept explanations.

### Hostname Deprioritization — Noise Reduction

- **pinterest, amazon:** SEO spam, no technical content
- **quora:** quality varies widely, often outdated
- **w3schools:** superficial tutorials, superseded by MDN
- **linkedin:** job listings instead of technical content
- **hub.docker.com:** registry pages, no learning content

### Pinterest — Remove Instead of Just Low Priority

Pinterest appears as spam on many queries (image galleries, no text content). `remove` eliminates it entirely.

### MAX_RESULTS = 80 (raised from 50)

With 10 active engines (7 general + 3 plugin) instead of the previous 5, SearXNG delivers significantly more unique results per query. 50 was the ceiling at 4-5 engines; with 10 engines, 80 is a better cut. A higher value would unnecessarily bloat the MCP response.

### SNIPPET_LENGTH = 5000

Snippets are passed directly to Claude in the MCP response. 5000 characters (~750-1000 words) offer enough context. Real SearXNG snippets are typically 200-500 characters — the limit is a safety ceiling.

## Decision

- Hostname lists categorized by usage type (Code/Docs/ML/Reference)
- 4 new high_priority domains: docs.rs, pkg.go.dev, learn.microsoft.com, semanticscholar.org
- MAX_RESULTS 50→80 due to twice as many active engines
- SNIPPET_LENGTH stays at 5000 (real snippets are well below it)

## Open Questions

- Hostname priority multipliers: how exactly does high_priority/low_priority modify the score? The SearXNG hostnames plugin source (searx/plugins/hostnames.py) should be read for the exact formula.
- Missing domains: developer.apple.com? tensorflow.org? docs.docker.com?
- `remove: pinterest` is redundant with `low_priority: pinterest` — or does `remove` override the `low_priority` entry?
- Weight calibration of the hostname list based on empirical Precision@10 per domain is missing

## Sources

- `src/searxng/settings.yml` — hostnames configuration
- `src/searxng/search_web.py` — MAX_RESULTS, SNIPPET_LENGTH constants
- `searxng/searxng` GitHub Repo (`searx/results.py`) — score calculation
- `searxng/searxng` GitHub Repo (`searx/plugins/hostnames.py`) — priority modification
- SearXNG Docs (RAG Collection: searxng) — hostname plugin
