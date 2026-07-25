# Pooling Phase 13 — 12-Method Eval

**Date:** 2026-05-23
**Probe artifacts:**
- `dev/search_pipeline/stage3_method_run_v3.py` — 12-method runner
- `dev/search_pipeline/stage4_aggregate_v3.py` — aggregate + latency + Pareto
- `dev/search_pipeline/01_reports/value_eval_v3_20260523_021216/eval_summary_v3.md` — full tables
- Oracle: `value_eval_v2_20260523_000156/*_oracle_v3clean.json` (backfilled in Phase 13-Prep: schema extended with per-engine positions, 5 lost oracle picks replaced from the filtered pool)

---

## Setup

**Eval baseline:** v3 pools (7 engines — google+SS filtered at method input via `filter_pool`).
Pool sizes: 40–88 raw → 30–60 after filter (mean ~47 URLs per pair).
**Oracle:** `oracle_v3clean.json` — 16 pairs, 10 picks each, 4 loss-pairs backfilled (3.1% churn).
**Pairs:** 4 modes × 4 queries = 16. All 16 produced oracle + methods.

---

## Results — Overall Mean Jaccard

| Method | Mean Jaccard | Mean Latency (ms) | Pareto |
|--------|--------------|-------------------|--------|
| M11 C3→LLM-Filter | **0.259** | 7403 | optimal |
| M9 SPLADE | 0.252 | 1649 | dominated (M10 matches at 0ms marginal) |
| M10 SPLADE+C3 | 0.252 | 0* | optimal |
| M7 C3+InstrPrefix | 0.246 | 1938 | dominated |
| M6 C3 Cross-Encoder | 0.204 | 1858 | dominated |
| M12 LLM-Selector | 0.192 | 10579 | dominated |
| M8 RRF+C3 Hybrid | 0.155 | 0* | dominated |
| M5 BM25-Capped | 0.142 | 1 | dominated |
| M1 C1 Overlap-Count | 0.135 | 0 | dominated |
| M2 RRF post-bucket | 0.135 | 0 | dominated |
| M3 Structural URL | 0.133 | 0 | dominated |
| M4 BM25 vanilla | 0.122 | 10 | dominated |

*M10 and M8 are 0ms marginal — they reuse scores computed by M6+M9 and M6+M2 respectively.
In isolation, their prerequisites cost ~3.5s (M6 + M9 for M10) and ~1.8s (M6 for M8).

---

## Results — Per-Mode

| Mode | Best | 2nd | Δ | Notes |
|------|------|-----|---|-------|
| general | **M9 SPLADE** 0.329 | M10 0.329 | 0.000 | SPLADE + C3 tied; LLM less effective here |
| pdf | **M7 C3+Instr** 0.262 | M11 0.240 | 0.022 | Instruction prefix helps on PDF-intent queries |
| books | **M11 LLM-Filter** 0.252 | M12 0.213 | 0.039 | LLM excels at books — context-aware authority |
| docs | **M9 SPLADE** 0.273 | M10 0.273 | 0.000 | SPLADE strong on docs vocabulary |

C3 Phase 12 winner: 0.609 overall Jaccard. Phase 13 C3 vanilla: 0.204. The **drop is expected** — Phase 12 used google+SS-inclusive pools (richer, Google-boosted), Phase 13 uses 7-engine filtered pools (~60% smaller). The relative ordering is the signal.

---

## Key Findings

### 1. SPLADE is the surprise winner
M9 SPLADE standalone (0.252) beats C3 Cross-Encoder vanilla (0.204) by +0.048. Wins outright in general and docs modes. Explanation: SPLADE's learned sparse expansion captures query-document term alignment on the title+snippet input that neither BM25 nor dense C3 handles as cleanly. BM25 lacks synonym expansion; C3 cross-encoder excels at full-sentence semantic alignment but short snippets give it less signal. SPLADE operates in between: learned expansion + sparse scoring.

### 2. Instruction prefix adds consistent value
M7 (C3+InstrPrefix) at 0.246 vs M6 (C3 vanilla) at 0.204 — delta +0.042, uniform across all 4 modes. The prefix `"Find authoritative primary or official sources for: {query}"` shifts the reranker's relevance axis toward authority/primary-source, aligning with oracle methodology. Near-zero extra cost (~80ms) for a +0.042 gain. **The prefix should become the default for any C3 call in the merged pipeline.**

### 3. M11 (C3→LLM-Filter) is overall winner — marginally
0.259 vs M9/M10's 0.252 (+0.007). The LLM filter on C3 Top-20 adds a second relevance pass that catches a few oracle picks the reranker alone misses. Cost: 7.4s per query (vs ~1.8s for M7 or ~1.6s for M9). For books mode the margin is larger (+0.039 over M7) — the LLM's world knowledge about canonical book sources (publisher pages, Open Library) aligns with oracle methodology.

### 4. M12 (LLM-Selector direct) underperforms M11
0.192 vs 0.259 — delta -0.067, and costs 10.6s vs 7.4s. More tokens (58837 vs 25314 input), worse result. The full pool (~47 URLs) is too much for a 4B model to compare holistically; C3 pre-filtering to top-20 concentrates the LLM's attention productively. This confirms the two-stage design of M11 is necessary.

### 5. Hybrid methods deliver less than expected
- M8 (RRF+C3): 0.155 — **below M6** (0.204). RRF signal pollutes C3 ranking. The raw position scores (M2 = M1 = 0.135) drag the blend down; equal alpha=0.5 gives too much weight to M2's weak signal.
- M10 (SPLADE+C3): 0.252 — matches M9 SPLADE alone. C3 scores don't add value over SPLADE on this eval set; SPLADE already captures what C3 sees. The hybrid's 0ms marginal cost makes it not harmful, but not a quality gain.

### 6. RRF post-bucket adds nothing over C1 Overlap-Count
M2 = M1 = 0.135. The per-engine positions field (Phase 13-Prep's schema addition) was available and used, but the RRF formula over 7 engines on a pre-capped pool produces near-identical ranking to simple overlap-count. The Cormack (2009) RRF advantage applies when multiple rankers are diverse and independent — our 7 engines are not (crossref+openalex partially overlap, BM25-type engines cluster similarly on factual queries).

### 7. Cheap method tier (M1-M5): all 0.12-0.14, below any GPU method
No cheap method approaches any GPU method. The 0ms methods (M1-M3) score 0.133-0.135; BM25 (0.122-0.142) is marginally better at best. Any GPU service (even SPLADE at 1.6s) dominates the cheap tier by +0.11 Jaccard.

---

## Latency Profile

| Tier | Methods | Mean ms | Quality range |
|------|---------|---------|---------------|
| Free | M1, M2, M3, M8*, M10* | 0 | 0.133–0.252 |
| BM25 | M4, M5 | 1–10 | 0.122–0.142 |
| SPLADE | M9 | 1649 | 0.252 |
| Reranker | M6, M7 | 1858–1938 | 0.204–0.246 |
| Two-stage | M11 | 7403 | 0.259 |
| LLM direct | M12 | 10579 | 0.192 |

*M8/M10 are 0ms marginal only; full cost requires prerequisites M6 (M8) or M6+M9 (M10).

---

## Production Migration Recommendation

**Recommended: M7 (C3+InstrPrefix) as default ranker.**

Rationale:
- 0.246 Jaccard — 2nd overall, within 0.013 of best (M11)
- 1938ms mean latency — production-acceptable (~2s total for reranker call)
- Consistent across all 4 modes (wins pdf outright; competitive everywhere)
- Operationally simple: one reranker call, one model, dynamic port via `find_server_url`

**M11 as opt-in premium tier (quality-first queries):**
- +0.013 quality gain at 3.8× latency cost (7.4s vs 2s). Justifiable for research/deep queries where oracle-quality selection matters, not for interactive search.
- M11 relies on M6 C3 scores as prerequisite — if M7 is the default, M11 adds one generator call (~7s) on top.

**M9 SPLADE as low-latency alternative:**
- 0.252 Jaccard at 1649ms — slightly faster than M7 (~300ms), slightly lower quality (-0.006). Valid fallback if reranker GPU is unavailable (separate llama-server process).

**Do NOT use for production:**
- M12: too slow (10.6s), worse quality than M11
- M8: RRF pollutes C3; use M6/M7 instead
- M1-M5: all dominated by GPU methods at quality threshold that matters

**Migration path:**
1. Register reranker-0.6b in RAG SERVERS dict (replace one-off llama-server) — prerequisite already noted in Phase 11 findings
2. Modify `src/search/merge.py:_merge_and_rank` to call M7 pattern: filter pool → `_doc_repr(m, "title+snippet")` → POST reranker with instruction-prefixed query → top-20 sorted by relevance_score
3. Rate-limiter fail-fast refactor still required (see rate_limiting area) — ensures CAPTCHA cascade doesn't starve the reranker call window

---

## What Would Change the Recommendation

- **Larger oracle set** (>16 pairs, broader query types): current oracle is 4 queries × 4 modes; QA-type queries underrepresented. SPLADE's strong performance on general+docs may not generalize.
- **Tuning M8/M10 hybrid α**: fixed 0.5/0.5 was the spec. α=0.2 for RRF (M8) might avoid pollution. Not tested.
- **M11 with M7 prefix** (C3+Instr pre-filter → LLM): not tested; M11 currently uses vanilla C3 scores (M6) for its pre-filter. Using M7 scores instead may further improve the top-20 candidate quality.
