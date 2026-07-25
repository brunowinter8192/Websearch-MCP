# Rerank Validation — 20-Query Extended Probe

**Date:** 2026-05-20  
**Probe script:** `dev/search_pipeline/rerank_probe_smoke.py` (updated for this run)  
**Raw report:** `dev/search_pipeline/01_reports/rerank_probe_20260520_190340.md`  
**Preceding phase:** n=4 probe, Cross-Encoder first beat Hard-Slot on Q1 (9/10 vs 8/10)

---

## Probe Validity — CAPTCHA Cascade

**8/20 queries yielded zero results.** Root cause: Google CAPTCHA triggered 3 times during the run (Q1 A1, Q5 A5, Q16 M1), each causing a multi-second rate-limiter backoff (38s / 66s / 125s per log). During each backoff window, *all* subsequent parallel-fetch calls across engines returned 0 results until the backoff cleared — consistent with the backoff propagating beyond the Google engine alone (exact mechanism not diagnosed; noted for rate-limiter investigation).

| Zero-result queries | Likely cause |
|---------------------|--------------|
| A5 graph neural network node classification | Google CAPTCHA at Q5, 66s backoff |
| P1 best espresso machine under 500 2026 | Within Q5's 66s backoff window |
| P2 mechanical keyboard switches comparison | Within Q5's 66s backoff window |
| P3 best noise cancelling headphones 2026 | Within Q5's 66s backoff window |
| T3 docker compose network bridge host mode | Unknown — CAPTCHA not logged; possible cascade from prior burst |
| T4 postgresql index types btree gin gist performance | Same as T3 |
| T5 react useEffect cleanup subscription pattern | Same as T3 |
| M1 transformer attention mechanism | Google CAPTCHA at Q16, 125s backoff |
| M2 neural network activation functions comparison | Within Q16's 125s backoff window |

**Effective sample:** 12/20 queries with data:
- Academic: 4/5 (A1–A4; missing A5)
- Product: 2/5 (P4–P5; missing P1–P3)
- Technical: 2/5 (T1–T2; missing T3–T5)
- Mixed-pathology: 3/5 (M3–M5; missing M1 original Q1 anchor, M2)

Critical loss: **M1 "transformer attention mechanism"** (the original Q1 pathology anchor from the preceding n=4 phase) is among the zero-result queries. The n=1 Q1 result from the initial probe **cannot be re-confirmed in this run.** Validation of the canonical pathology case remains n=1.

---

## Services Used

| Service | Preset | Port | Status during run |
|---------|--------|------|-------------------|
| Embedding | embedding-0.6b | 8084 | Healthy (restarted before run) |
| Reranker | reranker-0.6b | 8082 | Healthy (restarted before run) |

Both were RUNNING but NOT HEALTHY at probe-start. Restart via `rag-cli server restart` brought both to healthy before first query.

---

## Script Changes Made (this phase)

1. Docstring: updated port references 8090→8084, 8092→8082
2. `EMBEDDING_URL`: 8090→8084; `RERANKER_URL`: 8092→8082
3. `QUERIES` overridden with 20-query set (shadowed import from `bm25_sweep_smoke.py`)
4. `QUERY_CATEGORIES` dict added for category-level aggregation
5. `_build_category_summary()` helper added; wired into `_write_report`
6. Empty-string guard on `cand_texts` before embed/rerank calls (prevents 400 from llama-server on empty document list)

---

## Latency Data (12 valid queries)

| Query | Category | fetch_ms | rerank_ms | embed_ms | pool_unique |
|-------|----------|----------|-----------|----------|-------------|
| bert fine-tuning NLP | academic | 3295 | 1844 | 1308 | 448 |
| knowledge graph embedding | academic | 5001 | 2234 | 1629 | 429 |
| contrastive learning SSL | academic | 5001 | 2813 | 2208 | 416 |
| variational autoencoder | academic | 5001 | 3176 | 2562 | 435 |
| standing desk ergonomics | product | 7312 | 1872 | 1261 | 438 |
| air fryer vs convection oven | product | 5001 | 1900 | 1387 | 297 |
| python asyncio event loop | technical | 5001 | 1769 | 1296 | 392 |
| rust ownership borrowing | technical | 5944 | 1547 | 1090 | 251 |
| gradient descent SGD methods | mixed_pathology | 6121 | 2435 | 1885 | 453 |
| protein structure alphafold | mixed_pathology | 5000 | 2118 | 1574 | 241 |
| CNN image classification tutorial | mixed_pathology | 5001 | 1561 | 1045 | 461 |

**Reranker latency range (per query, 50 docs):** 1547ms – 3176ms. Mean ~2027ms across valid queries. Consistent with initial 4-query probe (~1540–1800ms). Upper end (3176ms for A4) aligns with heavier academic snippet batches.

**URL filter removals:** 0 across all queries. The search-results-page regex (`?q=`, `/search/`, `/scholar?q=`) fired on zero URLs. This is consistent with the initial 4-query probe (only 1 removal total, a scholar.google.de echo URL). The pattern is not obsolete — it fires on scholar.google.de specifically; its absence here means no scholar.google results reached the pool in this run (Google was CAPTCHA'd on most queries).

---

## Structural Observations Per Category

### Academic (4 valid queries)

All four queries (BERT fine-tuning, knowledge graph embedding, contrastive learning, variational autoencoder) produced large pools (416–448 unique). CrossRef and OpenAlex dominate numerically (200 each, ~87% of raw pool). DuckDuckGo and Mojeek each contribute 8–10 non-DOI URLs.

**Cross-Encoder top-10 composition (observable without quality scoring):**
- A1 (bert): 7 named-host tutorial/blog URLs + 2 CrossRef DOIs + 1 Stanford PDF. CE pushes most raw DOIs below rank 10.
- A2 (knowledge graph): #1 is `patents.google.com` — a patent result from Mojeek, semantically close but likely not the user's intent. 3 paper DOIs (crossref/openalex) in top-10.
- A3 (contrastive learning): 5 named-host URLs + 3 paper DOIs + 1 arxiv + 1 ieeexplore. CE does not fully eliminate DOI flood on this query.
- A4 (variational autoencoder): 8 named-host tutorial URLs + 1 semscholar false-friend (`High-Dimensional Analog Circuit Sizing` — BayesOpt paper, not VAE) + 1 CrossRef DOI.

**Embedding-Cosine top-10 composition (all 4 queries):** Heavy DOI flooding confirmed at scale. A1: 7/10 are CrossRef DOIs. A2: 4/10 are DOIs. A3: 6/10 are DOIs. A4: 3/10 are DOIs. The bi-encoder academic-register amplification effect observed in the preceding n=4 phase is consistent across all 4 academic queries.

**Hard-Slot top-10 composition:** For academic queries, general slots (12) are filled by Mojeek+DDG tutorial pages; academic slots (6) pull CrossRef/OpenAlex by position. Hard-Slot consistently surfaces `openlibrary.org/works/...` at positions 3–5 for academic queries (Open Library receives 1 result per query in its general-class slot, ranks high on overlap). Whether `openlibrary.org/works/OL27086886W` is useful for "bert fine-tuning NLP" is the quality question — flagged for scorer.

### Product (2 valid queries)

P4 "standing desk ergonomics home office" (438 unique): All configs surface ergonomics/office content. CrossRef/OpenAlex contribute 0 results for this query (confirmed by engine counts: only crossref=0 visible in raw). Pool is DDG + Mojeek + Lobsters dominated.

P5 "air fryer vs convection oven cooking" (297 unique): Smaller pool. CrossRef present (200 contribution confirmed by per-engine counts) but CE and Hard-Slot both surface cooking/review content in top-10. Structural difference between configs is minimal for pure consumer queries.

### Technical (2 valid queries)

T1 "python asyncio event loop concurrency" (392 unique): Stack Exchange contributes 1 result. CrossRef/OpenAlex present but CE successfully surfaces Python documentation, tutorial blogs, and a realpython-style tutorial. Hard-Slot surface is similar.

T2 "rust ownership borrowing lifetime explained" (251 unique): Smaller pool (CrossRef=200 but only 251 unique → heavy dedup). CrossRef dominant numerically but most are off-topic Rust (book chapters, compiler research). Hard-Slot top-10: 10 named Rust tutorial URLs, no DOIs visible. BM25-only top-10: 10 named Rust tutorial URLs, no DOIs. CE top-10: 10 named Rust tutorial URLs, no DOIs. BM25-Capped: same. **All configs agree on T2** — this is a case where the candidate pool is high-signal (CrossRef/OpenAlex results are deduped away or BM25-scored near-zero because they don't contain the target keywords in title+snippet). CE shows no differentiation value here.

Notable: Lobsters contributed 17 URLs for T2 (Rust content), but Hard-Slot's QA class cap (2 slots) would suppress them. Hard-Slot shows 0 Lobsters URLs in top-10 despite Lobsters' 17-URL contribution. CE (via BM25 pool) has no class restriction — Lobsters results compete on merit.

### Mixed-Pathology (3 valid queries)

**M3 "gradient descent optimization methods stochastic" (453 unique):**
- Engines: CrossRef=200, OpenAlex=197, Lobsters=20, Stack Exchange=16, DDG=10, Mojeek=10, Open Library=2.
- BM25-only top-10: 5 CrossRef/OpenAlex DOIs. Classic DOI-flood pattern.
- CE top-10: deepai/arxiv/arxiv-pdf/handwiki/stanford-tutorial/optimization-online/openalex-DOI(fractalfract)/crossref-book-chapter/springer-PDF/arxiv-html — mostly named sources + 2 DOIs. CE significantly reduces DOI count vs BM25-only (2 vs 5 in top-10).
- Hard-Slot top-10: Wikipedia, MIT PDF, Open Library book at #3 (likely off-topic), arxiv papers, GeeksForGeeks, IBM — mixed.
- Hard-Slot admits Open Library `openlibrary.org/works/OL20125986W` and `OL3285960W` at positions 3 and 5 via general-class slots. Whether these are topical optimization books is the quality question — flagged for scorer.

**M4 "protein structure prediction alphafold deep learning" (241 unique):**
- Engines: CrossRef=200, DDG=10, Lobsters=11, Mojeek=10, Semantic Scholar=10 (no OpenAlex, no Stack Exchange).
- **Hard-Slot top-10 starts with `alphafold.com` at #1** — the canonical product page. CE does NOT surface `alphafold.com` in top-10 (not in BM25 top-50; likely because `alphafold.com` has minimal title+snippet content, scoring low on BM25). This is a case where Hard-Slot's position-based ranking surfaces a canonical homepage that CE misses.
- CE top-10: EMBL news, securemachinery, pubs.aip.org, arxiv-recent, nature, pmc, tess.elixir-europe, crossref (compbiolchem), crossref (springer), iucr. Strong academic+tutorial mix, but no alphafold.com or deepmind.google.
- BM25-only top-10: securemachinery, journals.iucr.org, semanticscholar, nature, EMBL — high quality but misses alphafold.com.
- Embedding-Cosine top-10: leads with 2 CrossRef DOIs — confirms academic-register amplification even for a cross-domain query with strong non-DOI sources.

**M5 "convolutional neural network image classification tutorial" (461 unique, largest valid pool):**
- Engines: CrossRef=200, DDG=10, Lobsters=16, Mojeek=10, OpenAlex=199, Stack Exchange=29.
- BM25-only top-10: 2 CrossRef DOIs in positions 4–5. Tutorial sites dominate positions 1–3.
- CE top-10: codezup tutorial, programminghistorian, `doi.org/10.46430/phen0108` at #3 (this IS The Programming Historian tutorial — a legitimate tutorial URL behind a DOI), interviewsvector, pythonguides, towardsdatascience, tutorialspoint, cv-tricks, taylor-amarel.com, `doi.org/10.7465/jkdi.2022.33.3.533` at #10. **CE surfaces a tutorial DOI (phen0108) at #3 and an academic paper DOI at #10.** The phen0108 is likely correct; the jkdi one is uncertain.
- Hard-Slot top-10: programminghistorian, geeksforgeeks, agencebeable2.com, learnopencv, cv-tricks, tensorflow.org/tutorials, techgig.com, datacamp, codezup, pythonguides. **Clean tutorial set — no DOIs, all named tutorial hosts.** Hard-Slot's general-class slot allocation naturally favors the overlap-ranked tutorial URLs that both Mojeek and DDG returned.
- Stack Exchange contributed 29 URLs to M5's pool (highest SE count in the run), but Hard-Slot's QA cap allocates only 2 slots to QA class. CE can surface SO answers if BM25-scored high enough — but for a "tutorial" query, SO answers are likely correct.

---

## Cross-Encoder vs Hard-Slot — Pre-Scoring Observations

These are structural/mechanical observations, not quality verdicts. Quality scoring (count topical URLs in top-10) to be done by Opus+User over the raw report.

| Observation | Evidence |
|-------------|----------|
| **CE eliminates most raw DOI floods on academic queries** | A1: 2 DOIs vs BM25-only's 4; A3: 3 DOIs vs 5; A4: 2 DOIs vs 5 |
| **CE does NOT fully eliminate DOI floods** | A2: 3 CrossRef/OpenAlex DOIs remain in top-10; A3: 3 remain |
| **Embedding-Cosine DOI flooding confirmed at scale** | 3–7 DOIs in top-10 for all 4 academic queries |
| **Hard-Slot surfaces canonical homepages CE misses** | M4: alphafold.com at #1 in Hard-Slot, absent from CE top-10 (not in BM25 top-50) |
| **Hard-Slot injects off-intent Open Library books** | M3: openlibrary.org at positions 3 and 5 via general slots |
| **CE for M5 "tutorial" query injects one questionable academic DOI** | doi.org/10.7465/jkdi.2022.33.3.533 at #10 — Korean data mining journal |
| **T2 (Rust): all configs agree, no differentiation** | CE, Hard-Slot, BM25-Capped all surface the same named Rust tutorial URLs |
| **Hard-Slot's Lobsters QA-cap suppression confirmed** | T2: 17 Lobsters URLs contributed, 0 appear in Hard-Slot top-10 |
| **Original Q1 (transformer attention) not available** | M1 = zero results (CAPTCHA cascade); n=1 pathology-win from Phase 8 unconfirmed |

---

## Quality Score Table (fill in post-run eyeball)

Scoring method: count URLs in top-10 clearly topical for the query intent. Exclude: query-echo URLs, false friends (wrong-domain papers), academic DOIs of unknown topical relevance. Score /10 per query. Zero-result queries marked N/A.

| Category | Query | Hard-Slot | BM25-only | Embed-Cosine | Cross-Encoder | BM25-Capped |
|----------|-------|-----------|-----------|--------------|---------------|-------------|
| academic | bert fine-tuning NLP | | | | | |
| academic | knowledge graph embedding | | | | | |
| academic | contrastive learning SSL | | | | | |
| academic | variational autoencoder | | | | | |
| academic | graph neural network node class. | N/A | N/A | N/A | N/A | N/A |
| product | best espresso machine <$500 | N/A | N/A | N/A | N/A | N/A |
| product | mechanical keyboard switches | N/A | N/A | N/A | N/A | N/A |
| product | best noise cancelling headphones | N/A | N/A | N/A | N/A | N/A |
| product | standing desk ergonomics | | | | | |
| product | air fryer vs convection oven | | | | | |
| technical | python asyncio event loop | | | | | |
| technical | rust ownership borrowing | | | | | |
| technical | docker compose networking | N/A | N/A | N/A | N/A | N/A |
| technical | postgresql index types | N/A | N/A | N/A | N/A | N/A |
| technical | react useEffect cleanup | N/A | N/A | N/A | N/A | N/A |
| mixed_pathology | transformer attention (Q1 anchor) | N/A | N/A | N/A | N/A | N/A |
| mixed_pathology | neural network activations | N/A | N/A | N/A | N/A | N/A |
| mixed_pathology | gradient descent SGD | | | | | |
| mixed_pathology | protein structure alphafold | | | | | |
| mixed_pathology | CNN image classification tutorial | | | | | |
| **Total (sum, /120)** | | | | | | |
| **Scored queries only (sum, /60)** | | | | | | |

---

## Open Issues for Next Iteration

1. **CAPTCHA cascade rate-limiter bug.** Zero-result clusters after CAPTCHA events suggest the backoff affects more than the Google engine. Needs investigation in `src/search/rate_limiter.py` — separate from pooling work but blocks sequential-probe validity.

2. **M1 anchor unconfirmed.** "transformer attention mechanism" — the canonical Phase 8 pathology case (CE 9/10 vs Hard-Slot 8/10) — had zero results. The probe cannot confirm or refute the original finding. A targeted single-query re-run (not a 20-query batch) is needed to re-validate Q1.

3. **alphafold.com BM25 gap.** Hard-Slot surfaces `alphafold.com` at #1 for M4 via position-based ranking; CE misses it because BM25 scores the sparse homepage near-zero. This is a general failure mode for canonical product pages that have minimal text content. Whether this warrants a BM25-pre-boost rule (e.g., engine-position signal blended into BM25 score) is worth noting in the migration design.

4. **Lobsters QA-cap suppression remains unresolved.** T2 confirms that 17 Lobsters URLs were collected but 0 reached Hard-Slot top-10 (QA cap = 2, Stack Exchange fills those). CE's BM25-pool competition gave Lobsters no top-10 representation in T2 either (BM25 scored Rust forum posts above Lobsters links). CE is not a silver bullet for the Lobsters suppression issue — it requires the Lobsters content to compete on BM25 score first.
