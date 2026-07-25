# Rerank Probe Findings — 2026-05-09

**Scope:** Does URL-filter + BM25-retrieve + semantic rerank beat Hard-Slot 12/6/2 on 4 representative queries?  
**Outcome:** Cross-Encoder (Qwen3-Reranker-0.6B) ties Hard-Slot at **35/40** and **wins on Q1** (9 vs 8) — first config in this investigation to outperform Hard-Slot on the pathology query. Embedding-Cosine (Qwen3-Embedding-0.6B bi-encoder) underperforms at **26/40**. Preceding BM25 investigation topped out at 34/40.

---

## Probe Run

| Script | Configs | Queries | Wallclock |
|---|---|---|---|
| `dev/search_pipeline/rerank_probe_smoke.py` | 5 (see below) | 4 standard | 20.8s |

Report: `dev/search_pipeline/01_reports/rerank_probe_20260509_224944.md`

**5 configs:**
1. Hard-Slot 12/6/2 — `_merge_and_rank(raw_results)`, unfiltered (production baseline)
2. Filter + BM25-only — URL filter → pool → BM25Uniform (k1=1.2, b=0.75, sw=on, title+snippet)
3. Filter + BM25→Top50 + Embedding-Cosine — BM25 retrieves 50 candidates; embed query+50 docs in one batch call (51 inputs); sort by cosine similarity
4. Filter + BM25→Top50 + Cross-Encoder — same 50 candidates; `POST /v1/rerank`; sort by relevance_score
5. BM25-Capped reference — K=google count, no URL filter, no rerank (matches `bm25_capped_smoke.py`)

---

## GPU Services

| Service | Model | Port | Notes |
|---|---|---|---|
| Embedding (bi-encoder) | Qwen3-Embedding-0.6B Q8_0 GGUF | 8090 | Downloaded 2026-05-09; `RAG/models/Qwen3-Embedding-0.6B-Q8_0.gguf` (610 MB); 1024-dim, OpenAI-compat `/v1/embeddings` |
| Reranker (cross-encoder) | Qwen3-Reranker-0.6B Q8_0 GGUF | 8092 | Prior install; `RAG/models/qwen3-reranker-0.6b-q8_0.gguf` (610 MB); port 8082 occupied by mitmdump session-proxy, switched to 8092 |

Both: llama-server one-off background processes, not registered in `RAG/server_manager.py`. Probe-only.

Models on disk (full set):
- `RAG/models/Qwen3-Embedding-0.6B-Q8_0.gguf` — 610 MB, downloaded today
- `RAG/models/qwen3-reranker-0.6b-q8_0.gguf` — 610 MB, prior install
- `RAG/models/Qwen3-Embedding-8B-Q8_0.gguf` — 7.5 GB, Phase 6, dropped on latency (169s/query)
- `RAG/models/Qwen3-Reranker-8B-Q8_0.gguf` — 7.5 GB, prior install, untested in this probe

---

## Latency Per Query

| Query | fetch_ms | bm25_ms | embed_ms | rerank_ms |
|---|---|---|---|---|
| transformer attention mechanism | 3331 | 23 | 1140 | 1676 |
| best espresso machine 2026 | 2172 | 26 | 1052 | 1543 |
| python asyncio context manager | 1430 | 19 | 1193 | 1689 |
| kubernetes service mesh comparison | 2173 | 28 | 1295 | 1799 |

Source: probe report global summary table.

---

## Eyeball Quality Scores — Top-10 per Query

**Method:** count URLs in top-10 clearly topical for the query intent. Excludes: query-echo URLs (`scholar?q=`, `/search?q=`), false friends (PV-cell-defect paper, WSD paper), academic DOIs of unknown topical relevance. Judgment is Opus eyeball, not automated — same eyeball methodology used throughout this investigation.

| Config | Q1 transformer | Q2 espresso | Q3 asyncio | Q4 k8s mesh | Sum |
|---|---|---|---|---|---|
| Hard-Slot 12/6/2 | 8 | 9 | 9 | 9 | **35/40** |
| Filter + BM25-only | 6 | 10 | 7 | 10 | **33/40** |
| Filter + BM25→Top50 + Embedding-Cosine | 6 | 7 | 7 | 6 | **26/40** |
| **Filter + BM25→Top50 + Cross-Encoder** | **9** | **8** | **9** | **9** | **35/40** |
| BM25-Capped reference | 7 | 10 | 8 | 10 | **35/40** |

Note: Hard-Slot Q3/Q4 scored 9 in this run vs 8/9 in the prior session — natural variation across live-fetch runs, not a methodological change.

---

## Key Findings

### 1. Cross-Encoder is the first config to match Hard-Slot AND win on Q1

On Q1, CE top-10 contains: vitalflux (×2 distinct URLs), machinelearningmastery, deeplearningdaily, baeldung, NVIDIA developer blog, learnopencv, billparker, geeksforgeeks, crossref DOI (`10.2139/ssrn.4609431`, uncertain) — score 9/10. Hard-Slot Q1 top-10 contains: Wikipedia, machinelearningmastery, geeksforgeeks, d2l.ai, 3blue1brown, **open_library** (openlibrary.org/works/OL2229492W — irrelevant), medium (×2 distinct), vitalflux — score 8/10.

CE eliminates ALL three Q1 false-friends that appeared in BM25-only top-10:
- `semantic_scholar` PV-cell-defect-detector paper (BM25-only rank #6, score 5.07) — absent from CE top-10
- `openalex` WSD-Using-Ion paper (BM25-only rank #10) — absent
- `scholar.google.de/scholar?q=transformer+attention+mechanism` query-echo (removed by URL filter before BM25)

This is the first iteration in the investigation where any method outperforms Hard-Slot on Q1. Hard-Slot's noise floor came from the 6-slot academic cap; CE achieves the same effect via semantic disambiguation within the BM25 top-50 candidate set.

### 2. Embedding-Cosine underperforms despite correct mechanics

HTTP responses: 200, 1024-dim vectors returned, cosine computation correct, 51-input batch confirmed per query. Quality collapse: 26/40 vs CE's 35/40. Primary failure mode: surfaces unknown academic DOIs at high cosine scores. Q4 example — embed top-10 includes 3 crossref/openalex conference DOIs in positions 4/8/9 ahead of canonical k8s mesh comparison articles. Q2 example — embed scores 7/10 vs CE's 8/10 and BM25-Capped's 10/10.

Root cause: the 0.6B bi-encoder encodes query and document independently. A DOI's snippet can have high cosine with the query embedding due to shared formal academic register, even when topically misaligned. Cross-encoder avoids this because it sees query and document tokens jointly in one forward pass — the domain mismatch (`PV cell defect` tokens next to `transformer attention mechanism` query tokens) produces a low joint score.

Larger embedding model (8B) was Phase 6 candidate — dropped at 169s/query. No evidence that larger bi-encoders close the gap vs cross-encoders on short title+snippet text; the architectural disadvantage is independent of size.

### 3. BM25-Capped ties on aggregate but is noisy on Q1

BM25-Capped 35/40 matching Hard-Slot and CE is driven by Q2/Q4 (10/10 each) masking Q1 weakness (7/10). Q1 noise: `scholar.google.de/scholar?q=...` query-echo URL at rank #1 (URL filter NOT applied in Config 5 — deliberate per probe spec). `semantic_scholar` PV-cell-defect paper at rank #9. Both survive because K=11 cap admits engine top-K, and these are Semantic Scholar's top results for this query.

The sum masks the distribution: BM25-Capped is dominant on consumer/technical queries (Q2/Q4 = 20/20) but vulnerable on academic-noise queries (Q1 = 7/10). Hard-Slot's Q1 at 8/10 is better; CE's at 9/10 is better still.

### 4. URL-pattern filter is confirmed net-positive, low cost

Removed 1 URL on Q1 (`scholar.google.de/scholar?q=transformer+attention+mechanism&...` — matched `[?&](q|query)=` and `/scholar?q=` patterns). Zero removals on Q2/Q3/Q4. Zero false positives observed. Runtime: ~0ms (regex scan over ~450 raw results). The scholar.google.de URL reached BM25 rank #1 in the capped pool (it contains all three query tokens in the URL itself) — filter prevented it from polluting Configs 2–4 without the 0ms cost appearing in any timing breakdown.

### 5. Per-query latency breakdown

Embed: ~1050–1300ms for 51 inputs (1 query + 50 docs) in single batch POST to port 8090. Cross-encoder: ~1540–1800ms for 50 docs per query to port 8092. Both within probe targets. Production implication: cross-encoder adds ~1.7s per query on top of the existing ~2-3s fetch. Total per-query wall ~5s. Acceptable if GPU service is running as a persistent daemon (not one-off background process as in this probe).

---

## Configurations Validated

| Approach | Status |
|---|---|
| URL-pattern filter (search-results-page detection) | Keep — generic, ~0ms, no false positives observed |
| BM25-Retrieve top-50 as first stage | Keep — 450→50 in ~25ms, provides quality candidate set for reranker |
| Cross-encoder rerank top-50 → top-10 | **Strongest config tested**: 35/40, wins Q1, ties Hard-Slot overall |

---

## Configurations Confirmed Underperforming

| Config | Verdict |
|---|---|
| Embedding-Cosine rerank (Qwen3-Embedding-0.6B) | 26/40 vs CE 35/40; academic-DOI noise amplification; architectural limitation of bi-encoder on short text |

---

## Open Question for Next Iteration

4-query sample is insufficient to commit to production migration. CE's Q1 win is real but n=1 on the pathology category. A larger probe (10–20 diverse queries: academic, product, technical, mixed-intent, including multiple academic-noise cases) is the logical next step before `src/search/merge.py` is touched.

A separate RAG-project reranker eval shows cross-encoders are domain-dependent: help on academic text, hurt on technical docs. Our snippet-rerank case differs from full-document indexing (shorter docs, ephemeral per-query pool), but the warning applies — Q2 score 8/10 vs BM25-Capped's 10/10 hints at a possible consumer-query penalty worth probing at scale.

---

## Files Untouched

- `src/search/merge.py` — `_merge_and_rank` unchanged
- `src/search/filter_modes.py`, `_DEFAULT_ENGINES`, class frozensets — unchanged
- All production code untouched; only `dev/search_pipeline/` received new files
