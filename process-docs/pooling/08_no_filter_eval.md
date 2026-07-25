# Pooling Phase 12 — No-Filter V2 Eval, Algorithmic Backlog

**Date:** 2026-05-23
**Predecessor:** Phase 11's 8-engine eval, blocked by the search-engine rate-limiter backoff cascade
**Probe artifacts:**
- `dev/search_pipeline/stage1_pool_fetch.py` — Stage 1, no URL filter
- `dev/search_pipeline/stage3_method_run.py` — Stage 3, dynamic reranker URL via RAG `ensure_ready/find_server_url`
- `dev/search_pipeline/stage4_aggregate.py` — Stage 4, ts_dir-scoped output
- `dev/search_pipeline/01_reports/value_eval_v2_20260523_000156/` — 98 files (16 pool.json + 16 engine_report.md + 16 oracle.json + 16 oracle.md + 16 methods.json + 16 eval.md + 1 engine_summary + 1 eval_summary)

---

## Methodology Changes vs Phase 11

**Stage split** — the combined `value_eval_probe.py` (369 LOC, fetch+methods together) refactored into three separate scripts. Each stage is its own invocation with explicit ts_dir argument:

| Stage | Script | Output |
|-------|--------|--------|
| 1 — Pool Fetch | `stage1_pool_fetch.py` | `<mode>_<slug>_pool.json` + `<mode>_<slug>_engine_report.md` per pair, `engine_report_summary.md` global |
| 2 — Oracle | (worker, no script) | `<mode>_<slug>_oracle.json` + `<mode>_<slug>_oracle.md` per pair |
| 3 — Methods | `stage3_method_run.py` | `<mode>_<slug>_methods.json` per pair (C1, C2, C2', C3 Top-10) |
| 4 — Aggregate | `stage4_aggregate.py` | `<mode>_<slug>_eval.md` per pair, `eval_summary.md` global |

Each stage stops at a natural review point. v1 `value_eval_probe.py` + `value_eval_aggregate.py` retained as historical artifact.

**URL filter dropped** — `_filter_pool()` calls removed from stage1. The `+book` / `+pdf` / `+documentation` query modifier on general engines stays — it biases engine results — but no post-merge URL filter is applied. C-methods now operate on the un-URL-filtered capped pool. The rationale: the URL whitelists (`src/search/{book_whitelist,pdf_filter,docs_filter}.py`) are query-blind (host/path-based only) and routinely admit topic-irrelevant URLs (Open Library returns Husserl Cartesian Meditations for any query containing "attention"). Semantic relevance is exactly what cross-encoder + BM25 methods are designed to handle from title+snippet content. The eval validates whether they can replace URL filtering. Production filter code in `src/search/` retained unchanged — only dev/ eval scripts changed. Migration decision pending eval verdict.

**Dynamic reranker URL** — `stage3_method_run.py` calls `ensure_ready("reranker")` + `find_server_url("reranker")` from RAG's `server_manager`. Replaces the hardcoded `RERANKER_URL = "http://127.0.0.1:8082/v1/rerank"` from `rerank_probe_smoke.py` (Phase 11 hardcoded port 8082, conflicts with Monitor_CC mitmdump session-proxy on this machine). RAG's `_resolve_port` handles the conflict by falling back to a dynamic port; `find_server_url` reads the state file to get the actual running port. Production-grade reliability for any future call site (including the eventual `merge.py` migration).

**Pool cap fallback** — `K = google_count if google_count > 0 else 10`. When Google fails (CAPTCHA, error, empty), K falls back to 10. Important in this run because Google CAPTCHA'd 15/16 pairs (IP-level escalation from heavy daily usage — separate from cascade behavior which is gone).

---

## Per-Engine Reliability (16 pools)

| Engine | n_pools | OK% | Dominant Failure | Total URLs (raw) |
|--------|---------|-----|------------------|------------------|
| crossref | 16 | 100% | — | 3200 |
| duckduckgo | 16 | 100% | — | 160 |
| lobsters | 16 | 100% | — | 216 |
| mojeek | 16 | 100% | — | 160 |
| openalex | 16 | 100% | — | 2080 |
| semantic_scholar | 16 | 56% | EMPTY_NO_CONTAINER (44%) | 86 |
| stack_exchange | 16 | 50% | EMPTY (50%, topic-mismatch) | 244 |
| open_library | 16 | 25% | EMPTY (69%, books-specific) | 16 |
| **google** | 16 | **6%** | **EMPTY_BLOCK (94%, IP-CAPTCHA escalation)** | **11** |

Effective eval ran on 8 engines (Google de facto out). Six engines (crossref, ddg, lobsters, mojeek, openalex, plus partial SS/SE/OL) carried the entire pool fanout. Pool sizes per pair 40-76 URLs (mean ~57). Phase 11's "Google CAPTCHA'd on all 16 pairs" returns under a different mechanism — not the exponential backoff cascade (removed, commit `c7b71b5`) but IP-level reputation degradation from cumulative same-IP queries during the day.

---

## Per-Mode Mean Jaccard

| Mode | C1 Overlap-Count | C2 BM25 vanilla | C2' BM25-Capped | C3 Cross-Encoder | Winner |
|------|---|---|---|---|--------|
| general | 0.164 | 0.179 | 0.164 | **0.242** | C3 (+0.063) |
| pdf | 0.113 | 0.131 | 0.118 | **0.213** | C3 (+0.082) |
| books | 0.115 | 0.100 | 0.118 | **0.236** | **C3 (+0.118)** |
| docs | 0.117 | 0.098 | **0.197** | 0.179 | **C2' BM25-Capped (+0.018)** |

**Overall winner — C3 Cross-Encoder:** mean Jaccard 0.218 across 16 pairs vs C2' 0.149 vs C1/C2 both 0.127. C3 wins 3 of 4 modes with comfortable margins.

**docs-mode inversion vs Phase 11:** Phase 11 had C3 narrowly ahead in docs (+0.012, statistical noise). Phase 12 has C2' ahead +0.018, also small but opposite direction. Hypothesis: docs queries have extremely lexical vocabulary ("postgresql index types btree gin gist performance"), official documentation has those exact terms in title+path. BM25 is lexical-match-optimized, scores postgresql.org/docs high. Cross-encoder spreads scoring more broadly across semantically-similar sites including SEO content. Without URL filter, docs pool now includes Stack Overflow + GitHub + blog noise that the previous filter removed — exactly the rank-noise that BM25 handles better than C3 because the canonical docs URL is lexically anchored.

**Absolute Jaccard is structurally lower than Phase 11** (overall 0.218 vs 0.609). Pool sizes ~57 URLs (Phase 11 ~30 URLs after URL filter) — picking Top-10 from a larger pool produces lower set-overlap mathematically. The relative ordering of methods is what informs the migration decision, not the absolute number.

---

## Qualitative Finding — Jaccard Doesn't Tell the Full Story

Sample inspection of C3 Top-10 picks revealed a quality issue not captured by Jaccard overlap with the oracle:

**general × transformer attention mechanism — C3 picks:**

```
1. vitalflux.com/attention-mechanism-in-transformers-examples
2. datasciencedojo.com/blog/understanding-attention-mechanism
3. vitalflux.com/attention-mechanism-workflow-example
4. mljourney.com/beginners-guide-to-understanding-attention-mechanism
5. link.springer.com/chapter/...     ← solid
6. machinelearningmastery.com/the-transformer-attention-mechanism
7. deeplearningdaily.com/the-transformer-attention-mechanism
8. hakia.com/tech-insights/attention-mechanisms
9. baeldung.com/cs/attention-mechanism-transformers
10. developer.nvidia.com/blog/...     ← solid
```

Versus Oracle picks: Vaswani 2017 (arxiv.org/abs/1706.03762), Jay Alammar Illustrated Transformer, Lil Log Attention?Attention, D2L textbook, Sebastian Raschka self-attention guide, Wikipedia, OSF survey, 3Blue1Brown lesson, Machine Learning Mastery, e2eml.school.

**The canonical primary sources (Vaswani, Jay Alammar, Lil Log, D2L) are all in the pool** — verified by direct pool.json inspection. The oracle picked them. C3 ranked them outside the Top-10 in favor of SEO/listicle content.

**docs × postgresql** shows the same pattern: postgresql.org/docs/current/indexes-types.html lands at C3 position 7, six SEO blogs ranked above it. C3's #1-5 are all SEO blogs with the exact query keywords in title.

**books × transformer:** of C3's Top-10, only the Springer chapter (rank 3) is an actual book. Yet C3 had the largest mode-lead here (+0.118). Why? Because the other methods are even worse at books-mode discrimination, and the oracle in the undersized books pool was also forced to fall back to surveys. Jaccard's set-overlap inflates when both oracle and method default to the same "fallback layer" of comprehensive papers.

**Structural explanation:** Cross-encoder scores semantic similarity between query and (title + snippet). SEO content is optimized for exact-keyword title matching. The vitalflux/datasciencedojo blogs literally have "Attention Mechanism in Transformers Examples" in title — perfect match to "transformer attention mechanism" query. Vaswani's paper is titled "Attention Is All You Need" — semantically equivalent but lexically/structurally less query-aligned. Cross-encoder gives the SEO site the higher score. The model has no "source authority" signal — it sees text similarity, not reputation.

**Conclusion: the pool is good, the selection layer is the bottleneck.** Adding more engines would not fix this — Vaswani is already in the pool, an 11th engine would just put it there a second time. The next iteration needs a better SELECTION method, not more SOURCES.

---

## Migration Decision: Deferred

Original plan after Phase 11 was C3 → `merge.py` migration. Phase 12 evidence makes that premature:

1. C3 wins the relative comparison but the absolute pick quality is mediocre (SEO-heavy, canonical sources demoted).
2. Migration would commit production code to a ranker we already know we want to improve. Re-migration after the next iteration would be wasted engineering.
3. The eval infrastructure (16 pool.json + 16 oracle.json/md) is preserved as the reference set for the next iteration — every new method gets tested against the same data.

**Decision:** keep `src/search/merge.py` slot-allocation logic in place. Migrate only when an algorithmic option produces a selection that doesn't systematically pick SEO over canonical sources.

---

## Algorithmic Backlog (Next Iteration)

Four algorithmic options that have NOT been systematically tested. Ordered by engineering cost ascending:

**1. Qwen3-Reranker with instruction prefixing.** The Qwen3-Reranker-0.6B model supports instruction tokens via the standard Qwen3 instruction format. Currently `stage3_method_run.py` feeds only `<query>` to the reranker. With an instruction prefix like `"Instruction: Find authoritative primary or official sources for the query: {query}"`, the model would explicitly bias toward source-authority signals it learned during instruction tuning. Cost: ~5 lines of code change in `stage3_method_run.py`. Zero additional latency (same model, same forward pass). Test via re-run of Stage 3 + Stage 4 on the existing v2 ts_dir, compare Jaccard.

**2. Reciprocal Rank Fusion (RRF) + C3 hybrid.** RRF score `score(d) = Σ 1/(k + rank_i)` summed over all engines that surfaced URL `d`. Phase 3 (Q1 2026-05-09) ran RRF in isolation against hard-slot allocation, found Q1 issues (Lobsters QA-classification bug + DOI flooding). Those issues are gone in post-bucket Phase 12 — Lobsters has no class assignment, DOI flooding is mitigated by the K=10 cap. RRF in the new architecture has different structural properties: it boosts URLs surfaced by MULTIPLE engines (consensus signal), which orthogonally weights cross-engine confirmation against C3's text-similarity scoring. SEO sites typically appear in only 1-2 web engines; canonical sources (Vaswani) appear in multiple academic + general engines. Hybrid score: `final = α × c3_score + β × rrf_score`. Tune α/β on the existing 16 pool.json + methods.json data without re-running engine fanout. Cost: aggregator extension to compute RRF from existing `engines` field per URL + Stage 4 re-run.

**3. Two-stage C3 + LLM-Filter.** C3 pre-retrieves Top-20 cheaply (~2s), then a small local LLM (Qwen3 4B-7B class) filters those 20 to clean Top-10 (~1-2s additional). Total ~3-4s vs current ~2s — added latency acceptable for real-time search. LLM-filter has explicit reasoning capacity to detect SEO/listicle content based on URL structure + title patterns + snippet quality, things C3 cannot encode. Constraint: requires another managed GPU service (Qwen3-4B preset in RAG `server_manager`, register if not present). Higher operational complexity than (1) or (2) but quality lift could approach oracle-level. Test via new stage3 variant `stage3_method_run_twostage.py` or flag.

**4. Engine-class authority weighting (lightweight re-revisit).** A subset of the originally-rejected Authority-Domain-List approach. Not a hardcoded URL list but an engine-class signal: URLs surfaced by openalex/crossref/scholar get an "academic-authority" boost; URLs from SE/lobsters get a "community-vetted" boost; URLs from google/ddg/mojeek alone (no academic/community confirmation) get a slight demotion. This is essentially RRF with engine-class weights — a generalization of option 2. Cost: aggregator extension + parameter tuning. Risk: overweights certain engine classes for queries where that class is wrong (academic-boost on "best espresso machine" is unhelpful).

**Order priority for next session:** (1) → (2) → (3). Option (1) is free, (2) is cheap, (3) is the high-investment option that should be reserved until (1) and (2) are exhausted. Each test uses the same 16-pool/16-oracle reference set — no re-fetching of pools, no new LLM-oracle calls, just stage3 + stage4 re-runs.

---

## Drill-Down Feature Status

**Not implemented yet.** The cache schema in `src/search/cache.py` stores per-URL `engines` (list of engine names that surfaced the URL) and `snippets` (dict per-engine snippet text). This is sufficient for an MVP drill-down command:

```
searxng-cli search_engine_tail <query> --engine <name>
```

Reads the cached pool, filters URLs where `<name> in engines`, returns all such URLs that were not in the user-visible Top-N. Per-engine position (rank within each engine's original output) is NOT stored — that's a future schema extension if richer drill-down semantics turn out to be useful in practice.

Deferred along with the merge.py migration — both wait for the algorithmic selection question to settle.

---

## Sources

DB-state unchanged from Phase 11 cleanup (2026-05-09): Croft 2010 (868 chunks) + Cormack 2009 RRF paper (7 chunks) in `searxng_reference` collection. No new sources extracted in Phase 12.

| Source | Type | Relevance | Status |
|---|---|---|---|
| Cormack et al. SIGIR 2009 — Reciprocal Rank Fusion outperforms Condorcet | Paper | Foundational RRF formula for backlog option (2) | Indexed (RAG: searxng_reference) |
| Croft / Metzler / Strohman 2010 — Search Engines IR in Practice | Book | Source-selection / fusion synthesis | Indexed (RAG: searxng_reference) |

