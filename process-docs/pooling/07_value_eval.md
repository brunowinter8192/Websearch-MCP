# Pooling Phase 11 — LLM-Oracle Value-Eval, Mode-Spanning

**Date:** 2026-05-22
**Predecessor:** Phase 10's top-source-recall finding (Q14 single-query pool dump), which blocked migration
**Probe artifacts:**
- `dev/search_pipeline/value_eval_probe.py` (369 LOC) — Stage 1+2 fetch + score
- `dev/search_pipeline/value_eval_aggregate.py` (333 LOC, after B2 fixes) — Stage 4 Jaccard + MDs
- 16 pool/methods JSONs + 16 oracle JSONs + 14 per-query MDs + summary MD under `dev/search_pipeline/01_reports/value_eval_20260522_015113/` and `01_reports/value_eval_*_20260522_021950.md` (per-query) + `value_eval_summary_20260522_021950.md`

---

## Session Setup — Three Directions Rejected First

Three approaches were originally proposed for the top-URL-identification automation that blocks the pooling migration:

1. **Authority-domain lookup per topic area.** User rejected: brittle, per-topic maintenance, doesn't scale.
2. **LLM-as-quality-judge per URL.** User rejected: too slow / heavy for runtime — would add an LLM call per pool URL per query.
3. **Lobsters-as-curation-signal (boost multiplier).** User rejected: too specific to one engine, not a structural algorithm.

A fourth direction emerged during the session — **structural-feature mining** (slug-length, listicle-verb-counts, query-token-density, date-in-path patterns). User rejected as too query-specific: works for the Phase-10 PostgreSQL pathology but doesn't generalize.

**Final user-driven architecture decision:** keep the ranker simple (one of the C-methods), add a **runtime LLM-driven engine-drill-down tool** that lets the calling LLM (the searcher) query for engine-X URLs that were not in the merged top-N. The ranker stays cheap; topic-awareness for engine selection lives in the LLM, not in the ranker. This is the actual architecture going forward.

**Dependency chain for that architecture:**

1. Decide which C-method becomes the production ranker (Phase 11, this document).
2. Migrate `_merge_and_rank` to the chosen method.
3. Extend cache format to preserve per-engine position (small additive change).
4. Build the engine-drill-down CLI subcommand.
5. Wrap into a `searxng-cli` shortcut + update the searxng-mcp skill.

Phase 11 closes step 1.

---

## Methodology — LLM-as-Oracle, Scripted Comparison

**Why not garbage-Eyeball at scale.** Phase 9 showed garbage-Eyeball as a floor metric only: C2/C2'/C3 all 0 garbage across 20 queries, no discrimination. Phase 10 showed that the more important quality dimension (top-source recall) is not garbage-bounded — all 4 methods missed the same expert URLs. Continuing with the same eyeball methodology would have produced more null results.

**Why not LLM-runtime-quality-judge.** Same reason it's rejected for production: too slow for per-URL per-query judgment. But the same primitive — LLM judgment — is acceptable as a **one-time eval signal** if the LLM doesn't see C-method outputs and picks Top-N independently.

**The eval design:**

| Stage | Actor | Output |
|---|---|---|
| 1+2 | Probe script (Python) | Per (mode, query): full pool fetch + filter + cap. C1/C2/C2'/C3 Top-10 computed on appropriate pools. Persisted as `pool.json` (url+title+snippet sorted alphabetically — no engine/score/position signal) and `methods.json` (each C-method's Top-10 + latency). |
| 3 | Worker (Sonnet) | Reads `pool.json` only — does NOT open `methods.json`. Picks Top-10 with rationale per URL. Writes `oracle.json`. Independence is the methodological core. |
| 4 | Aggregator (Python) | Per (mode, query): Jaccard `|oracle ∩ method| / |oracle ∪ method|` for each C-method. Per-mode mean + overall mean. Per-query MD with pool dump + oracle + each C-method + comparison matrix. Summary MD with winner table. |

**Why Jaccard.** Top-10 vs Top-10, ordering doesn't matter for the binary "is this URL in my Top-10". Jaccard is the natural set-similarity metric. Range 0-1, symmetric, denominator-normalized.

**Pool-design subtlety.** Different methods see different pools:
- **Oracle, C1 Overlap, C2' BM25-Capped, C3 Cross-Encoder:** the **capped+filtered pool** (per-engine top-K=google_count cap, then mode URL filter). Typically 40-80 URLs in general/docs, 0-15 in pdf/books.
- **C2 BM25 vanilla:** the **full filtered pool** (no cap). Typically 200-450 URLs. This reflects C2's defining property — BM25 across the deep tail.

C2 may surface URLs the Oracle never saw (because they're outside the capped pool). Jaccard handles this honestly: if C2 picks a deep-tail URL not in oracle, that counts as disagreement. This is intentional — the question is "does C2 produce URLs the oracle would have chosen if it had seen them too", and the answer is empirically "rarely".

---

## Query Set — Strict from Canonical 20

User-locked option (a): four queries strict from the canonical 20-query set (`dev/search_pipeline/rerank_probe_smoke.py:57-82`), **same four queries across all four modes**. Thinness in non-natural modes is accepted as the cost of methodological consistency.

| # | Query | Category | Notes |
|---|---|---|---|
| Q1 | `transformer attention mechanism` | M1 | Phase-8 anchor, academic-leaning |
| Q2 | `postgresql index types btree gin gist performance` | T4 | Phase-10 pathology case |
| Q3 | `python asyncio event loop concurrency` | T1 | Technical Q&A leaning |
| Q4 | `contrastive learning self-supervised representations` | A3 | Academic, strong PDF signal |

Two academic-leaning + two technical. All four have non-trivial signal in `--pdf`, marginal signal in `--books`, mixed signal in `--docs`. Product queries (P1-P5) and pathology queries (M4 alphafold, etc.) were considered and dropped — products collapse entirely in pdf/docs/books modes, pathology academic queries are too narrow.

---

## C-Methods Compared

| Method | Pool | Sort key | Reference impl |
|---|---|---|---|
| C1 Overlap-Count | capped+filtered | `(-len(engines), min_position)` | `src/search/merge.py` step 2 (current prod) |
| C2 BM25 vanilla | full+filtered | `_bm25_score(pool, query, top_n)` k1=1.2 b=0.75 sw=on title+snippet | `dev/search_pipeline/bm25_sweep_smoke.py:BM25Uniform` |
| C2' BM25-Capped | capped+filtered | same BM25 on capped pool | `single_query_pool_dump.py` config |
| C3 Cross-Encoder | capped+filtered | rerank score from Qwen3-Reranker-0.6B (port 8082) | `rerank_probe_smoke.py:cross_encoder_rerank` |

Embedding-Cosine (C4 from Phase 8) was **not** evaluated — Phase 8 dropped it at 26/40 quality (bi-encoder architectural limit on short snippets, not parameter-count-fixable).

---

## Execution — Two-Worker Split

Phase A (1 worker): scripts built, smoke validated on (general × M1), filter modes inlined to avoid src/ imports, reranker service restarted + health-verified. Architecture correction by worker: oracle on capped pool (76 URLs manageable), C2 vanilla on full pool (defining property). Merged.

Phase B split into two workers due to oracle-selection context cost (16 pools × ~12k tokens read + reasoning + write ≈ 240-320k tokens):
- **B1:** ran the full probe (16 pairs, ~3-4 min wallclock), did oracle selection for general + pdf (8 of 16). Merged. Killed.
- **B2:** read existing pools/methods JSONs, did oracle selection for books + docs (8 of 16). Fixed aggregator bugs found at runtime (`oracle_top10` → `top_10` key mismatch, string-vs-dict item handling, empty-pool skip). Ran aggregator. Merged. Killed.

Worker pattern: Sonnet, fresh context per phase, oracles committed per mode (4 commits per worker max). Phase A worker built the architecture cleanly; B2 worker caught Phase A bugs at runtime — expected and benign drift.

---

## Results

### Per-Mode Mean Jaccard

| Mode | C1 Overlap | C2 BM25 | C2' BM25-Cap | C3 Cross-Encoder | Winner |
|---|---|---|---|---|---|
| general | 0.179 | 0.181 | 0.162 | **0.302** | C3 (margin +0.121) |
| docs | 0.195 | 0.400 | 0.446 | **0.458** | C3 (margin +0.012) |
| pdf | 0.871 | 0.871 | 0.871 | 0.871 | tie — pool too small, no signal |
| books | 1.000 | 1.000 | 1.000 | 1.000 | tie — pool ≤ oracle size, no signal |

### Overall Mean Jaccard (all 16 probes, equal-weighted)

| Method | Overall mean |
|---|---|
| C1 Overlap-Count | 0.498 |
| C2 BM25 vanilla | 0.558 |
| C2' BM25-Capped | 0.565 |
| **C3 Cross-Encoder** | **0.609** |

C3 wins. Margin over runner-up (C2') is 0.044 overall, 0.121 in general (the most-reliable signal), 0.012 in docs (statistical noise).

### Pool-Size Snapshot

| # | Mode | Query | Filtered Pool |
|---|------|-------|---------------|
| 1-4 | general | (all 4) | 40, 56, 45, 63 |
| 5-8 | pdf | (all 4) | 14, 2, 5, 11 |
| 9-12 | books | (all 4) | 4, 0, 10, 0 |
| 13-16 | docs | (all 4) | 44, 23, 40, 33 |

PDF and books are dominated by oracle-saturation pathology (pool ≤ 10): all methods trivially get Jaccard ≈ 1.0 because the pool is too small to permit disagreement. **Effective discriminating data: 8 pairs** (general + docs).

---

## Caveats (Critical for Migration Confidence)

### Google CAPTCHA — Out on All 16 Pairs

`/tmp/value_eval_probe_run.log` shows 4 Google CAPTCHA events (pairs 1, 2, 4, 7) with escalating backoffs: 34s, 65s, 123s, 244s. Once the first CAPTCHA triggered the rate_limiter's exponential backoff, subsequent pairs within the backoff window all hit `RATE_WAIT_TIMEOUT=60s` and got RATE_SKIP for Google. Total: google=0 across all 16 pairs.

**The eval ran as 8-engine, not 9-engine.** All 4 C-methods saw the same reduced pool, so the **method comparison is internally fair** — the winner is who-ranks-the-reduced-pool-best, and that's still C3. But Google's deep-tail (which Phase 10 showed contributes unique expert URLs not surfaced by other engines) is missing, so this eval cannot definitively claim C3 is the best in a 9-engine production scenario. A re-run with Google in the pool (after rate-limiter fail-fast cleanup + pacing strategy) would tighten the conclusion.

### Undersized Pools — pdf and books

- `pdf × postgresql` (pool=2), `pdf × asyncio` (pool=5), `books × transformer` (pool=4), `books × asyncio` (pool=10): pool is at-or-below oracle Top-10 capacity. Methods cannot discriminate.
- `books × postgresql` (pool=0), `books × contrastive` (pool=0): zero results passed BOOK_WHITELIST. Aggregator skips these pairs in per-mode means (effective N for books = 2, not 4).

This is a known limitation of running the canonical 20-query set against narrow filter modes. The query set was not optimized for cross-mode signal.

### Engine-Coverage Pathologies (Worker Observations)

Worker B2 flagged three concrete engine-level issues during oracle selection (not eval-blocking, but Future Work):

1. **books mode is broken for ML/DL queries.** Open Library returns Husserl Cartesian Meditations, 1893 World's Fair history, 19th-century philosophy — zero ML relevance — for transformer/postgresql/contrastive queries. Only `books × asyncio` returned a coherent pool, and it collapsed to one Fowler book replicated across 7 retailer/platform pages. The BOOK_WHITELIST may be over-restrictive; Open Library may need topic-filtering. Separate work item.

2. **Open Library pollutes general/docs pools too.** Same Husserl/Rosmini entries appear in `docs × transformer` pool. Open Library isn't restricted to books-mode in the engine fanout. Separate work item.

3. **docs mode has academic-engine precision noise.** `docs × asyncio` pool contains 8+ off-topic papers from OpenAlex/Semantic Scholar matching "asyncio"/"concurrency" as incidental keywords — Julia HEP performance, RFSoC SDR, autonomous driving digital twins, Power HiL, Smart City IoT. `docs × postgresql` pool contains "Performance of the Bispectral Index During Electrocautery" (medical paper matching `index`, `performance`, partial `btree`/`bispectral`). Classic academic title-word matching noise. Separate work item (academic engine over-eager keyword matching).

---

## Status of `_merge_and_rank` Production Migration

**C3 Cross-Encoder is the recommended winner.** It clearly leads in general (+0.121 margin), narrowly leads in docs (+0.012, statistical tie), and dominates overall (+0.044 over C2'). Phase 8 independent corroboration: C3 ties Hard-Slot 35/40 and wins Q1 9-vs-8 on the n=4 sample.

**Migration remains BLOCKED on the following dependencies (none are pure code refactors of `merge.py`):**

1. **rate_limiter fail-fast cleanup** (separate scope, new work item created). Without it, Google CAPTCHA cascades will keep the eval inconclusive and any 16+-query rapid-fire batch in production will produce wasted wallclock + no Google results. Decision: remove exponential backoff entirely (fail-fast, no artificial delay, no session-scoped failure memory).

2. **Cache format extension for per-engine position** (small additive change to `merge.py` + `cache.py`). Needed for the engine-drill-down tool that follows the ranker migration. Not blocking the migration itself.

3. **Optional: 9-engine re-eval** with Google included (rate-limiter cleanup + mode-spacing pacing) to tighten confidence in the general-mode margin. Sound migration cause to want this; not strictly required if C3's lead is accepted as robust.

4. **Cross-encoder service operational concerns** — `reranker-0.6b` on port 8082. Currently runs as ad-hoc llama-server in some sessions. Needs SERVERS-dict registration in RAG infrastructure for production reliability (open item flagged since 2026-05-09).

---

## Sources

- Phase 8 predecessor with rubric scoring (n=4): CE ties Hard-Slot 35/40, wins Q1 9-vs-8
- Phase 9 garbage-floor: C2/C2'/C3 all 0 obvious-garbage across 20 queries
- Phase 10 top-source-recall (Q14 single-query pool dump): all 4 methods missed the same expert URLs
- Probe scripts: `dev/search_pipeline/value_eval_probe.py`, `value_eval_aggregate.py`
- Result artifacts: `dev/search_pipeline/01_reports/value_eval_summary_20260522_021950.md` + 14 per-query MDs same prefix
- Probe-run log: `/tmp/value_eval_probe_run.log` (Google CAPTCHA timeline)
