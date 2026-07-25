# OpenAlex — Implemented (2026-05-03)

**Endpoint:** `https://api.openalex.org/works?search={query}&per_page=10[&mailto={email}]` (GET, JSON, no auth)
**Engine:** `src/search/engines/openalex.py` — BaseEngine subclass, httpx-only, 4 req/min
**Smoke:** `dev/search_pipeline/09_openalex_smoke.py` — 30-query baseline, report in `01_reports/openalex_smoke_*.md`

**Why OpenAlex:** Successor to Microsoft Academic Graph. ~250M works (papers, preprints, books, datasets). Free, open, no API key required. Provides rich structured metadata including abstracts (as inverted index), citation counts, author lists, and external IDs (arXiv, DOI, PMID, MAG). Strongest academic coverage in the HTTP-engine category — complements CrossRef (DOI-focused). No CAPTCHA, no browser load, no stealth concerns.

**Abstract inverted index:** OpenAlex stores abstracts as `{word: [position1, position2, ...]}`. Reconstruction: build position→word mapping, sort by position, join with spaces. ~5 lines of Python. Not all papers have abstracts (some only have `tldr`-equivalent from the works API).

**URL strategy:** `ids.arxiv` (full URL `https://arxiv.org/abs/...`, best for CS/ML papers) > `doi` (full URL `https://doi.org/...`, journal papers) > `id` (full URL `https://openalex.org/W...`, always present, lowest signal value).

**Rate limiting:** Anonymous polite-pool: no published hard limit, but OpenAlex asks for `mailto=` parameter to identify polite users. Set `OPENALEX_MAILTO` env var — engine includes it in all requests when present. No default (don't hardcode an email). Production 4 req/min limiter stays well within observed anonymous limits.

**Semantic Scholar HTTP drop rationale (same session):** Tested 2026-05-03. Anonymous tier blocked after 3 rapid requests; 429 persisted for > 180s. Even with 4 req/min limiter, startup/warmup scenarios (prior session already hit the API) would cause persistent 429. Free key requires academic-institution email gate. OpenAlex provides equivalent academic metadata without the rate-cascade risk. (Semantic Scholar was later re-added via browser path 2026-05-07.)
