# BM25 Evaluation Findings — 2026-05-09

**Scope:** Did BM25 in any tested configuration beat Hard-Slot 12/6/2 production baseline on 4 representative queries?  
**Outcome:** No. Hard-Slot 34/40. Best BM25 variant — BM25+Weighting — ties at 34/40; BM25-Capped 33/40; Vanilla BM25 and BM25+IDF 32/40.

---

## Probes Run (this session)

| Probe | Script | Configs | Pool Size | Rank Latency |
|---|---|---|---|---|
| Parameter Sweep | `bm25_sweep_smoke.py` | 16-config grid (b×stopwords×doc_repr, k1=1.2) + 4 k1 sensitivity | ~400–455 unique | ~250ms |
| Side-by-Side Compare | `bm25_compare_smoke.py` | 5: HS / Vanilla / b=0 / b=1 / Title3x | same | ~50ms |
| IDF + Engine Weighting | `bm25_idf_engine_smoke.py` | 5: HS / Vanilla / +IDF / +Wt / +IDF+Wt | same | ~50ms |
| Per-Engine Top-K Cap | `bm25_capped_smoke.py` | 3: HS / Uncapped / Capped (K=google count) | 64–85 capped | ~15ms |

Reports: `dev/search_pipeline/01_reports/bm25_{sweep,compare,idf_engine,capped}_20260509_*.md`. Prior RRF baseline: `rrf_vs_hardslot_20260509_013940.md` (commit `86b7b0a`).

---

## Sensitivity Findings (from sweep)

| Axis | Values Tested | Q1 (transformer — academic) | Q2–Q4 |
|---|---|---|---|
| k1 | 0.5, 1.2, 2.0, 3.0 | 20/20 overlap w/ vanilla at all values | 17–20/20; near-zero effect |
| stopwords | on, off | ~2 URL difference | ~0–2 URL difference |
| b | 0.0, 0.5, 0.75, 1.0 | **dominant**: b=0 → 3/20; b=0.5 → 14/20; b=0.75 → 20/20; b=1.0 → 7/20 | 17–20/20 across values |
| doc_repr | title+snippet, title3x | title3x → 12/20 overlap w/ vanilla | 16–19/20 |

`b` is the only axis with meaningful effect; dominant on Q1 only. `k1` has near-zero effect on short documents (title+snippet avg ~60 chars). `b=0.75` optimal on Q1. `title3x` causes meaningful divergence but worse quality.

---

## Quality Evaluation — Eyeball Top-10 per Query

**Method:** count URLs in top-10 clearly topical for the query intent. Excludes: query-echo URLs (`scholar?q=`, `/search?q=`), false friends (PV-cell-defect paper for "transformer", tugboat-scheduling paper for "transformer", Word Sense Disambiguation paper for "transformer"), and DOI filler that is semantically off-topic. Judgment is Opus eyeball, not automated.

| Config | Q1 transformer | Q2 espresso | Q3 asyncio | Q4 k8s mesh | Sum |
|---|---|---|---|---|---|
| Hard-Slot 12/6/2 | 8 | 9 | 8 | 9 | **34/40** |
| Vanilla BM25 (k1=1.2, b=0.75, sw=on, no IDF) | 5 | 10 | 7 | 10 | **32/40** |
| BM25 + per-pool IDF (Okapi) | 5 | 10 | 7 | 10 | **32/40** |
| BM25 + engine-inverse-weighting (1/n) | 6 | 10 | 9 | 9 | **34/40** |
| BM25 + IDF + Weighting | 6 | 10 | 9 | 9 | **34/40** |
| BM25-Capped (K = google result count) | 6 | 10 | 7 | 10 | **33/40** |

Q2–Q4 are consumer/technical queries where all general engines agree on canonical domains (Wirecutter, Forbes, realpython, toptal). Q1 (transformer attention mechanism) is the discriminating query — academic-engine noise (crossref/openalex/semscholar surface keyword-matching papers about tugboat scheduling, biology, PV-cell defect detection) breaks every BM25 variant while Hard-Slot limits the damage to 6 academic slots.

---

## Key Findings

### 1. IDF makes no meaningful difference on our pool/query shapes

Per-pool Okapi BM25 vs Uniform BM25 (IDF=1.0): identical top-10 on Q1 and Q4, 2–3 URL differences on Q2/Q3, zero quality change across all 4 queries. Root cause: the pool is ~400–455 short documents (title+snippet) for 3–4 word queries. Crossref/OpenAlex each return 200 results that surface-match all query tokens — term frequencies are nearly uniform across the pool. IDF needs sparse term-document distribution to discriminate; our per-query ephemeral pool has none. Validates user's pre-session call to drop IDF.

### 2. Engine-inverse-weighting (1/engine_count) is bipolar

Formula: `final_score = bm25_score × Σ(1/engine_count[e] for e in doc.engines)`.

Helps Q3 (asyncio): lifts multi-engine consensus URLs — realpython+bbc.github.io at top-3, quality 7 → 9. Helps Q2 (espresso): Wirecutter+Forbes at #1–2 (both matched by google+mojeek or duckduckgo+mojeek).

Breaks Q4 (k8s mesh): `stack_exchange` returned 2 URLs for this query → `weight = 1/2 = 0.5/URL`, highest in the pool (next highest: google/duckduckgo/mojeek at 0.09–0.10). SO question `stackoverflow.com/questions/49268369/istio-egresses-with-kubernetes-services` lands at rank #1 (score 2.09) ahead of toptal comparison guide (score 1.28). The "reward low-volume engines" design over-boosts sparse engines unpredictably. Q4 quality: 10 → 9 (one noise URL at #1 displaces a comparison article).

### 3. Per-engine top-K cap controls depth-tail noise but not top-K noise

Cap rule: admit top-K URLs per engine where K=google result count (11–12 for these queries). Pool shrinks 5–7×: Q1 457→85, Q2 438→64, Q3 399→74, Q4 447→67. Crossref/OpenAlex positions 12–200 eliminated. Rank latency: ~250ms → ~15ms.

Q1 quality 5 → 6 (uncapped → capped). Improvement is real but limited. Semantic Scholar's top-K includes false-friend papers at positions 1–10 (PV-cell-defect, WSD) — these survive the cap because they're the engine's highest-ranked results. Cap addresses depth-tail noise; it cannot remove top-K noise from an engine whose own ranking is semantically off for the query.

### 4. BM25 ignores the multi-engine-overlap signal — Hard-Slot's structural advantage

`_merge_and_rank` general pool sort key: `(-_n_general(m), m["min_position"])` (`merge.py` L82). URLs appearing in more general engines rank first. A URL ranked by Google+DDG+Mojeek is statistically more likely canonical than a URL ranked by only one engine. This overlap count is Hard-Slot's main quality lever.

BM25 encodes zero engine information. It scores `title+snippet` text alone. Consequence: Q1 Vanilla BM25 #1 is `scholar.google.de/scholar?q=transformer+attention+mechanism` (query-echo URL) — highest BM25 score because its snippet contains all query tokens. Hard-Slot's overlap-sort immediately promotes multi-engine consensus and demotes single-engine results. This is the gap no BM25 parameterization tested here could close.

### 5. Hard-Slot's class-cap is a noise-floor that BM25 cannot replicate

Hard-Slot caps academic at 6 slots. Even if all 6 go to noise (biology, fluid dynamics, tugboat-scheduling DOIs from crossref/openalex), 14 general+QA slots remain and are filled by Google/DDG/Mojeek results which are on-topic by construction (they matched the query via full-document retrieval, not surface keyword match on short metadata). Academic-class noise damage is bounded at 6/20.

BM25 ranks all 400–455 candidates uniformly by text score. On Q1, semantic_scholar's PV-cell-defect paper scores 5.06 on Vanilla BM25 (rank #7). Nothing in BM25's design prevents academic-origin noise from occupying 11+ of the 20 final slots. Hard-Slot's class boundary is a noise-floor by construction; BM25's failure mode on academic-noise queries is also by construction.

---

## Configurations Confirmed Useless

| Config | Evidence |
|---|---|
| IDF (per-pool Okapi) | ≤2 URL difference vs uniform IDF across all 4 queries; zero quality change (Finding 1) |
| k1 tuning | 20/20 overlap on Q1/Q2 at all tested values; 17–20/20 on Q3/Q4 — no tuning surface for short docs |
| Stopwords off | ~0–2 URL difference; marginal; keep on (no cost) |
| doc_repr title3x | Diverges meaningfully on Q1 (12/20 vs vanilla) but produces worse quality; worse or equal on Q2–Q4 |

---

## Configurations Worth Future Investigation

| Approach | Rationale |
|---|---|
| `bm25_score × f(n_engines)` where `f = log(1+n)` or `n^0.5` | Directly encodes multi-engine-overlap signal BM25 is blind to (Finding 4); theory-aligned with metasearch independence assumption |
| Hard per-engine URL cap M (not continuous weight) | Prevents SE-overboost (Finding 2) without continuous penalty that over-rewards sparse engines |
| Pre-rank URL-pattern filter (query-echo: `scholar?q=`, `/search?q=`, `/results?query=`) | Generic, query-independent; eliminates the BM25 #1 artifact on Q1 in one rule |
| Overlap multiplier + hard cap combination | Addresses both Finding 4 and Finding 2; depends on the two items above being validated individually first |

---

## Open Question for Next Session

How do production meta-search systems handle engine-fusion / result-merging? Do any implement an overlap-weighted ranking step?

Planned: GitHub code search on `searxng/searxng`, `nicowillis/presearch-node-docker` / presearch ranking code, `metager/MetaGer`, yacy source. Search terms: `merge`, `rank`, `fusion`, `combine` in ranking-adjacent paths. Goal: find prior art for `overlap × text_score` hybrid, or confirm the gap is novel. Kagi's published blog posts on result fusion also on the list.

---

## Files Untouched

- `src/search/merge.py` — `_merge_and_rank` unchanged throughout session
- `src/search/filter_modes.py`, `_DEFAULT_ENGINES`, `GENERAL`/`ACADEMIC`/`QA` frozensets — all unchanged
- Only `dev/search_pipeline/` received new probe scripts and reports
