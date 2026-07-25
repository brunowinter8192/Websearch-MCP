# Pooling Phase 10 — Single-Query Pool Dump (Q14 postgresql index types)

**Date:** 2026-05-21  
**Predecessor:** Phase 9's 20-query garbage-floor verdict (C2/C3/C4 all 0 obvious-garbage)  
**Probe artifacts:** `dev/search_pipeline/single_query_pool_dump.py` (385 LOC) + `dev/search_pipeline/01_reports/single_query_pool_postgresql_index_types_btree_g_20260521_231405.md` (878 lines)

---

## Motivation

Phase 9 verdict: C2 BM25, C3 Cross-Encoder, C4 Embedding-Cosine all produce 0 obvious-garbage across 20 queries × Top-google_count slots. The garbage-Eyeball methodology was floor-tied for the three text-scoring strategies — could not discriminate them. Open question: do the rankers differ on **what they MISS** (Blind Spot B from the Phase 9 narrative — Pool-URLs that don't make Top-N)?

Phase 10 takes one technical query, dumps the full capped pool alongside each config's Top-N picks, and compares URL-by-URL via a comparison matrix.

## Setup

- **Query:** `postgresql index types btree gin gist performance` (Q14 — technical category, high surface-match-trap potential due to specific terms btree/gin/gist)
- **Architecture:** bucket-uniformity-fixed codebase (commit `af77cc5`). All 9 default engines fire on every query, RATE_WAIT_TIMEOUT=60.
- **Pool composition:** per-engine top-K cap at K=google_count=10. After dedup across 9 engines: **57 unique URLs**.
- **Engines that returned results:** crossref→10, duckduckgo→10, google→10, lobsters→6, mojeek→10, openalex→5, semantic_scholar→8. (open_library + stack_exchange returned 0 for this query.)
- **All 4 configs applied:** C1 Overlap-Count, C2 BM25, C3 Cross-Encoder (Qwen3-0.6B), C4 Embedding-Cosine (Qwen3-0.6B).

## Key Numbers

| Metric | Value |
|---|---:|
| Capped pool size | 57 |
| URLs picked by AT LEAST ONE config (in some Top-10) | 23 |
| URLs picked by NO config (all four `—`) | 34 |
| URLs picked by ALL 4 configs simultaneously | **0** |

**Striking finding 1:** Zero consensus across all 4 strategies. There is no URL that all four rankers agree belongs in Top-10. The strategies fundamentally disagree on what's "best".

**Striking finding 2:** 60% of pool URLs (34/57) are picked by no ranker. Most are expected noise (off-topic crossref DOIs, openalex/semscholar papers on unrelated topics). But hidden in the "missed by all" group are 8 high-quality expert sources.

## The High-Quality Sources All Rankers Missed

| Source | Engine | Why high-quality |
|---|---|---|
| hakibenita.com/postgresql-correlation-brin | Lobsters | Haki Benita — prominent PostgreSQL author |
| hakibenita.com/postgresql-hash-index | Lobsters | Same author |
| 2ndquadrant.com/en/blog/parallelism | Lobsters | 2ndQuadrant — major PostgreSQL company |
| percona.com/blog/...hypothetical | Lobsters | Percona — DB specialist firm |
| pganalyze.com/blog/gin-index | Google (deep tail) | pganalyze — PostgreSQL diagnostics company |
| citusdata.com/blog/2017/10/17/tour-of-pg-indexes | Google (deep tail) | Citus — PostgreSQL extension company |
| thoughtbot.com/blog/postgres-index-types | Google (deep tail) | thoughtbot — solid technical blog |
| depesz.com/2014/05/12/joining-btree | Mojeek | Hubert Lubaczewski — prominent PostgreSQL expert |

These are exactly the sources an experienced PostgreSQL engineer wants for a btree/gin/gist performance question. All 4 ranking strategies — including the GPU-cost C3 Cross-Encoder and C4 Embedding — failed to surface any of them in Top-10.

### Why each strategy misses these

- **C1 Overlap-Count:** every expert URL is single-engine (Lobsters, Google deep-tail, or Mojeek — never overlapping). Sort key `(-engine_count, min_position)` → engine_count=1 demotes all of them behind anything with engine_count≥2. On this query, only 1 URL has engine_count=3 and 2 URLs have engine_count=2; positions 3-10 in C1's output are essentially "the engine #1 of each single-engine URL sorted by min_position", which is structurally close to random.
- **C2 BM25:** lexical density wins. The expert posts have concise titles (e.g. "GIN Index", "B-Tree Index Types") that don't repeat the query keywords. Listicle/tutorial titles like "How to Choose Between PostgreSQL Index Types" or "PostgreSQL Indexing: BTree, GIN, GiST" pack more query tokens and score higher.
- **C3 Cross-Encoder:** semantically prefers tutorial-style structured content over expert-knapper posts. blog.devops.dev "how to choose..." wins #1; docs.bswen.com, rurutia1027 Medium win positions 2-3. The expert posts (often without query-keyword-rich snippets) get demoted.
- **C4 Embedding-Cosine:** floats reddit.com/r/ExperiencedDevs to #1 — a discussion thread with broad semantic match to "experienced PostgreSQL engineers picking index types". Other Top-3 are similar discussion-oriented content. Expert blogs with terser snippets don't match the query embedding as closely.

## Engine Attribution of Expert URLs

**Lobsters: 4/8 (50%).** The tech-link-aggregator surfaces the dominant share of high-signal expert content. This makes intuitive sense — Lobsters is humans-curated by tech practitioners and historically routes traffic to expert blogs (Haki Benita, 2ndQuadrant, Percona are all classic Lobsters-front-page material).

**Google: 3/8.** Google has the expert content but in positions 4-10 (deep tail of its own ranking) — not in Google's #1-3 which are typically the SEO-optimized tutorial sites. Per-engine top-K cap at K=10 catches them, but the rankers then demote them.

**Mojeek: 1/8.** Less variety, but surfaced depesz.com which neither Google nor Lobsters had at the same position.

**Implication:** Lobsters is structurally the most valuable engine for expert-content discovery on technical queries. But the current pool architecture penalizes Lobsters (single-engine → engine_count=1 → C1 demotes). Text rankers (C2/C3/C4) don't see Lobsters as "different" — they treat Lobsters URLs like any other pool entry and rank by text content, which favors keyword-stuffed titles over expert-knappness.

## What Each Config Picked at #1

| Config | Top-1 URL | Source |
|---|---|---|
| C1 Overlap | postgresql.org/docs/current/indexes-types | google + duckduckgo (engine_count=2) |
| C2 BM25 | stackoverflow.com/questions/1540374/why-are... | mojeek (single-engine, high term density) |
| C3 Cross-Encoder | blog.devops.dev/how-to-choose-between-index-types | duckduckgo (tutorial-style content) |
| C4 Embedding | reddit.com/r/ExperiencedDevs/... | google (discussion thread) |

The official PostgreSQL docs (canonical answer) are #1 only for C1. C2/C4 demote them to #4/#8. **C3 Cross-Encoder excludes postgresql.org/docs from Top-10 entirely** — a striking result for the GPU-cost strategy.

## Methodological Conclusion

**garbage-Eyeball is a floor test, not a quality discriminator.** It measures "did the ranker produce obviously-wrong URLs" (= the negative-quality floor). For finer differentiation between rankers, a **top-quality-recall test** is needed: define the high-signal URLs in the pool (per query), measure how many each ranker surfaces in Top-N.

The bottleneck for automating this: identifying "high-signal URLs in the pool" is itself a judgment call. Phase 10 did it via human spot-check (Opus reading the dump + recognizing PostgreSQL expert names). To automate:

1. **Authority lookup:** maintain a small curated list of "high-signal domains" per technical area (postgresql expert domains: hakibenita.com, pganalyze.com, depesz.com, citusdata.com, 2ndquadrant.com, percona.com). Boost or flag pool URLs from these domains. Trivial but brittle — domain lists need maintenance per topic area.
2. **Lobsters-as-curation-signal:** treat Lobsters origin as a strong positive prior. If Lobsters surfaced a URL, the URL has passed humans-curated review. Could be implemented as a ranking-bonus (`if "lobsters" in engines: score *= 1.5`) without changing the pool composition. Cheap, broadly applicable, leverages the existing per-engine attribution data.
3. **LLM-as-quality-judge:** for each pool URL, ask an LLM "is this from a topic-area expert source?" using URL + title + snippet. Scalable, but expensive (~50 URLs × LLM call per query). Could be done as a one-time pool-augmentation step.

Direction (1) is cheapest, direction (2) is most general, direction (3) is most flexible but expensive. The combination "Lobsters-boost as a structural prior + occasional domain-list refinements" is probably the highest-leverage path.

## Status of `_merge_and_rank` Production Migration

**Migration is BLOCKED on this finding.** Phase 9 suggested "BM25 wins, migrate now" because garbage was floor-tied. Phase 10 reveals that the garbage-floor masked a more important quality dimension: top-source recall, where all 4 strategies are demonstrably suboptimal. Migrating to BM25 now would lock in a strategy that misses Lobsters-curated expert content.

Next session: solve top-URL-identification automation first (Lobsters boost prototype + reference-set methodology), THEN migrate `_merge_and_rank` with the improved ranking strategy.

## Open Questions for Next Session

- Lobsters-as-curation-signal: implement a ranking-bonus for Lobsters origin and measure whether expert-recall improves (in Top-N) and whether garbage-rate stays low
- Reference-set methodology: for a small query set (5-10 queries), manually define "the top-5 URLs in the pool" per query, measure each ranker's Recall@5 against that set. Build the eval as a probe.
- Per-engine-cap revisit: does K=google_count make sense if Lobsters routinely surfaces expert content in positions 1-6? Maybe a larger K for trusted-curator engines (= "give Lobsters the full 6 it returned, not capped to google's 10").

## Sources

- Phase 9 predecessor: 20-query garbage-floor verdict
- Phase 10 probe artifacts: `dev/search_pipeline/single_query_pool_dump.py`, `dev/search_pipeline/01_reports/single_query_pool_postgresql_index_types_btree_g_20260521_231405.md`
- Pool integrity precondition: search-engine rate-limiter cascade bug fixed prior to this run (bucket-uniformity-fixed codebase, commit `af77cc5`)
