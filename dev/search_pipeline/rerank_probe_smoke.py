#!/usr/bin/env python3
"""
URL-Filter + BM25-Retrieve + Semantic Rerank Probe.

5 configs side-by-side, top-10 each, on 20 diverse queries (5 academic / 5 product /
5 technical / 5 mixed-intent pathology):
  1. Hard-Slot baseline (12/6/2, no URL filter)
  2. Filter + BM25-only
  3. Filter + BM25-Retrieve-50 + Embedding-Cosine Rerank (Qwen3-Embedding-0.6B)
  4. Filter + BM25-Retrieve-50 + Cross-Encoder Rerank (Qwen3-Reranker-0.6B)
  5. BM25-Capped reference (K=google count, no filter, no rerank)

Services required:
  Embedding:    http://127.0.0.1:8084/v1/embeddings   (preset: embedding-0.6b)
  Cross-encoder: http://127.0.0.1:8082/v1/rerank      (preset: reranker-0.6b)

Output: dev/search_pipeline/md/rerank_probe_<ts>.md
"""

# INFRASTRUCTURE
import asyncio
import math
import os
import re
import sys
import time
import warnings
from collections import Counter
from datetime import datetime
from pathlib import Path

import httpx
import numpy as np

SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from bm25_sweep_smoke import (
    BM25Uniform,
    QUERIES,
    STOPWORDS,
    VANILLA_K1,
    _build_pool,
    _doc_repr,
    _tokenize,
)
from src.search.browser import close_browser
from src.search.merge import _merge_and_rank
from src.search.search_web import _query_engines_concurrent, _select_engines

import logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

# Override imported 4-query set with 20-query validation set (g82 extended probe)
QUERIES = [
    # ACADEMIC (A1-A5) — paper-style; Scholar/CrossRef/OpenAlex contribute
    "bert fine-tuning natural language processing",
    "knowledge graph embedding relational learning",
    "contrastive learning self-supervised representations",
    "variational autoencoder latent space generative model",
    "graph neural network node classification",
    # PRODUCT (P1-P5) — consumer-intent; general-web engines dominate
    "best espresso machine under 500 2026",
    "mechanical keyboard switches comparison tactile linear",
    "best noise cancelling headphones 2026",
    "standing desk ergonomics home office",
    "air fryer vs convection oven cooking",
    # TECHNICAL (T1-T5) — how-to/implementation; Stack Exchange + Lobsters contribute
    "python asyncio event loop concurrency",
    "rust ownership borrowing lifetime explained",
    "docker compose network bridge host mode",
    "postgresql index types btree gin gist performance",
    "react useEffect cleanup subscription pattern",
    # MIXED-INTENT / PATHOLOGY (M1-M5) — academic-noise pathology + Lobsters misclassification
    "transformer attention mechanism",           # original Q1 anchor
    "neural network activation functions comparison",
    "gradient descent optimization methods stochastic",
    "protein structure prediction alphafold deep learning",
    "convolutional neural network image classification tutorial",
]

QUERY_CATEGORIES: dict[str, str] = {
    "bert fine-tuning natural language processing":              "academic",
    "knowledge graph embedding relational learning":             "academic",
    "contrastive learning self-supervised representations":      "academic",
    "variational autoencoder latent space generative model":     "academic",
    "graph neural network node classification":                  "academic",
    "best espresso machine under 500 2026":                      "product",
    "mechanical keyboard switches comparison tactile linear":    "product",
    "best noise cancelling headphones 2026":                     "product",
    "standing desk ergonomics home office":                      "product",
    "air fryer vs convection oven cooking":                      "product",
    "python asyncio event loop concurrency":                     "technical",
    "rust ownership borrowing lifetime explained":               "technical",
    "docker compose network bridge host mode":                   "technical",
    "postgresql index types btree gin gist performance":         "technical",
    "react useEffect cleanup subscription pattern":              "technical",
    "transformer attention mechanism":                           "mixed_pathology",
    "neural network activation functions comparison":            "mixed_pathology",
    "gradient descent optimization methods stochastic":          "mixed_pathology",
    "protein structure prediction alphafold deep learning":      "mixed_pathology",
    "convolutional neural network image classification tutorial": "mixed_pathology",
}

REPORT_DIR = SCRIPT_DIR / "md"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = SCRIPT_DIR / "jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TOP_N       = 10
RETRIEVE_N  = 50   # BM25 retrieve candidate count before reranking
BM25_K1     = VANILLA_K1   # 1.2
BM25_B      = 0.75
BM25_SW     = True
BM25_REPR   = "title+snippet"

EMBEDDING_URL = "http://127.0.0.1:8084/v1/embeddings"
RERANKER_URL  = "http://127.0.0.1:8082/v1/rerank"

# Search-results-page URL patterns (generic, query-independent)
SEARCH_PAGE_RE = re.compile(
    r'[?&](q|query|search|keyword|term|p)='
    r'|/search/'
    r'|/sresults/'
    r'|/scholar\?q='
)


# ORCHESTRATOR

async def run_probe() -> None:
    _verify_services()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"rerank_probe_{ts}.md"
    probe_log_path = DATA_DIR / f"rerank_probe_{ts}.queries.jsonl"
    os.environ["SEARXNG_QUERY_LOG_PATH"] = str(probe_log_path)

    selected, _ = _select_engines(None)
    print(f"Engines ({len(selected)}): {', '.join(sorted(selected.keys()))}", file=sys.stderr)
    print(f"Report: {report_path}", file=sys.stderr)
    print(file=sys.stderr)

    query_sections: list[str] = []
    summaries: list[dict]     = []
    t_total = time.perf_counter()
    try:
        for qi, query in enumerate(QUERIES):
            print(f"[{qi + 1}/{len(QUERIES)}] {query}", file=sys.stderr)
            section, summary = await _run_one_query(query, selected)
            query_sections.append(section)
            summaries.append(summary)
            print(
                f"  fetch={summary['fetch_ms']}ms  hardslot={summary['hardslot_ms']}ms  "
                f"bm25={summary['bm25_ms']}ms  embed={summary['embed_ms']}ms  "
                f"rerank={summary['rerank_ms']}ms  "
                f"filtered_out={summary['removed_by_filter']}  "
                f"unique={summary['unique_after_dedup']}",
                file=sys.stderr,
            )
    finally:
        await close_browser()

    total_ms = round((time.perf_counter() - t_total) * 1000)
    _write_report(query_sections, summaries, report_path, total_ms)
    print(f"\nReport:     {report_path}", file=sys.stderr)
    print(f"Total wall: {total_ms}ms", file=sys.stderr)


# FUNCTIONS

# Abort immediately if either service is unreachable
def _verify_services() -> None:
    print("Verifying services …", file=sys.stderr)
    try:
        r = httpx.post(EMBEDDING_URL, json={"input": ["warmup"], "model": "qwen-emb-0.6b"}, timeout=10.0)
        r.raise_for_status()
        print(f"  Embedding service OK ({r.elapsed.microseconds // 1000}ms)", file=sys.stderr)
    except (httpx.HTTPError, httpx.ConnectError) as e:
        sys.exit(f"ERROR: Embedding service unreachable at {EMBEDDING_URL}: {e}")

    try:
        r = httpx.post(RERANKER_URL, json={"query": "warmup", "documents": ["test"]}, timeout=10.0)
        r.raise_for_status()
        print(f"  Reranker  service OK ({r.elapsed.microseconds // 1000}ms)", file=sys.stderr)
    except (httpx.HTTPError, httpx.ConnectError) as e:
        sys.exit(f"ERROR: Reranker service unreachable at {RERANKER_URL}: {e}")
    print(file=sys.stderr)


# Return True if URL looks like a search-results page (not a content page)
def is_search_results_url(url: str) -> bool:
    return bool(SEARCH_PAGE_RE.search(url))


# Embed batch of texts; returns list of embedding vectors
def embed_batch(texts: list[str]) -> list[list[float]]:
    r = httpx.post(EMBEDDING_URL, json={"input": texts, "model": "qwen-emb-0.6b"}, timeout=60.0)
    r.raise_for_status()
    return [item["embedding"] for item in r.json()["data"]]


# Cross-encoder rerank; returns [(original_index, relevance_score), ...]
def cross_encoder_rerank(query: str, documents: list[str]) -> list[tuple[int, float]]:
    r = httpx.post(RERANKER_URL, json={"query": query, "documents": documents}, timeout=60.0)
    r.raise_for_status()
    results = r.json().get("results", [])
    return [(item["index"], item["relevance_score"]) for item in results]


# Cosine similarity between two embedding vectors
def cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na > 0 and nb > 0 else 0.0


# BM25 score pool; return top-N as [(doc, score), ...]
def _bm25_score(pool: list[dict], query: str, top_n: int) -> list[tuple[dict, float]]:
    if not pool:
        return []
    corpus = [_tokenize(_doc_repr(m, BM25_REPR), BM25_SW) for m in pool]
    qtoks  = _tokenize(query, BM25_SW)
    bm25   = BM25Uniform(corpus, k1=BM25_K1, b=BM25_B)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        scores = bm25.get_scores(qtoks)
    scores = np.nan_to_num(scores, nan=0.0)
    ranked = sorted(range(len(pool)), key=lambda i: -float(scores[i]))
    return [(pool[i], float(scores[i])) for i in ranked[:top_n]]


# K = google result count; fallback 10
def _compute_K(engine_stats: dict) -> int:
    K = engine_stats.get("google", {}).get("result_count", 0)
    return K if K > 0 else 10


# Run all 5 configs for one query; return (section_md, summary_dict)
async def _run_one_query(query: str, selected: dict) -> tuple[str, dict]:
    # --- Fetch ---
    t0 = time.perf_counter()
    raw_results, engine_stats = await _query_engines_concurrent(query, "en", 10, selected)
    fetch_ms = round((time.perf_counter() - t0) * 1000)

    raw_count = len(raw_results)

    # --- URL filter ---
    removed_urls    = [r.url for r in raw_results if is_search_results_url(r.url)]
    filtered_raw    = [r     for r in raw_results if not is_search_results_url(r.url)]
    filtered_count  = len(filtered_raw)
    removed_count   = raw_count - filtered_count
    # Pattern histogram
    pattern_hist = Counter()
    for url in removed_urls:
        if re.search(r'[?&](q|query|search|keyword|term|p)=', url):
            pattern_hist["query_param"] += 1
        if "/search/" in url:
            pattern_hist["/search/"] += 1
        if "/sresults/" in url:
            pattern_hist["/sresults/"] += 1
        if "/scholar?q=" in url:
            pattern_hist["/scholar?q="] += 1

    # --- Pool build (filtered) ---
    pool          = _build_pool(filtered_raw)
    unique_count  = len(pool)

    # --- Config 1: Hard-Slot (unfiltered, production baseline) ---
    t0 = time.perf_counter()
    hs_ranked, slot_counts = _merge_and_rank(raw_results)
    hs_top = [{"url": r.url, "engines": r.engines or [r.engine], "score": None} for r in hs_ranked[:TOP_N]]
    hardslot_ms = round((time.perf_counter() - t0) * 1000)

    # --- Config 2: Filter + BM25-only ---
    t0 = time.perf_counter()
    bm25_pairs   = _bm25_score(pool, query, TOP_N)
    bm25_top     = [{"url": d["url"], "engines": d["engines"], "score": s} for d, s in bm25_pairs]
    bm25_ms      = round((time.perf_counter() - t0) * 1000)

    # --- Config 3 & 4: BM25 retrieve top-50, then rerank ---
    t0 = time.perf_counter()
    bm25_candidates = _bm25_score(pool, query, RETRIEVE_N)
    bm25_ms += round((time.perf_counter() - t0) * 1000)  # add to bm25_ms

    cand_docs  = [d for d, _ in bm25_candidates]
    # Filter out empty/whitespace-only texts — reranker returns 400 on empty documents
    _raw_texts = [_doc_repr(d, BM25_REPR) for d in cand_docs]
    _valid     = [(d, t) for d, t in zip(cand_docs, _raw_texts) if t.strip()]
    cand_docs  = [d for d, _ in _valid]
    cand_texts = [t for _, t in _valid]

    # --- Config 3: Embedding-Cosine Rerank ---
    t0 = time.perf_counter()
    if cand_texts:
        all_texts = [query] + cand_texts
        embeddings = embed_batch(all_texts)
        query_emb  = embeddings[0]
        doc_embs   = embeddings[1:]
        cosine_scores = [cosine_sim(query_emb, de) for de in doc_embs]
        cos_ranked = sorted(range(len(cand_docs)), key=lambda i: -cosine_scores[i])
        embed_top  = [
            {"url": cand_docs[i]["url"], "engines": cand_docs[i]["engines"], "score": cosine_scores[i]}
            for i in cos_ranked[:TOP_N]
        ]
    else:
        embed_top = []
    embed_ms = round((time.perf_counter() - t0) * 1000)

    # --- Config 4: Cross-Encoder Rerank ---
    t0 = time.perf_counter()
    if cand_texts:
        ce_pairs  = cross_encoder_rerank(query, cand_texts)
        ce_sorted = sorted(ce_pairs, key=lambda x: -x[1])
        ce_top    = [
            {"url": cand_docs[idx]["url"], "engines": cand_docs[idx]["engines"], "score": score}
            for idx, score in ce_sorted[:TOP_N]
        ]
    else:
        ce_top = []
    rerank_ms = round((time.perf_counter() - t0) * 1000)

    # --- Config 5: BM25-Capped reference ---
    K           = _compute_K(engine_stats)
    capped_raw  = [r for r in raw_results if r.position <= K]
    capped_pool = _build_pool(capped_raw)
    t0 = time.perf_counter()
    capped_pairs = _bm25_score(capped_pool, query, TOP_N)
    capped_ms    = round((time.perf_counter() - t0) * 1000)
    capped_top   = [{"url": d["url"], "engines": d["engines"], "score": s} for d, s in capped_pairs]

    # --- Build section ---
    section = _build_query_section(
        query       = query,
        engine_stats = engine_stats,
        raw_count   = raw_count,
        filtered_count = filtered_count,
        removed_count  = removed_count,
        pattern_hist   = pattern_hist,
        unique_count   = unique_count,
        slot_counts    = slot_counts,
        K              = K,
        unique_capped  = len(capped_pool),
        fetch_ms    = fetch_ms,
        hardslot_ms = hardslot_ms,
        bm25_ms     = bm25_ms,
        embed_ms    = embed_ms,
        rerank_ms   = rerank_ms,
        capped_ms   = capped_ms,
        n_candidates = len(bm25_candidates),
        hs_top      = hs_top,
        bm25_top    = bm25_top,
        embed_top   = embed_top,
        ce_top      = ce_top,
        capped_top  = capped_top,
    )

    summary = {
        "query":            query,
        "fetch_ms":         fetch_ms,
        "hardslot_ms":      hardslot_ms,
        "bm25_ms":          bm25_ms,
        "embed_ms":         embed_ms,
        "rerank_ms":        rerank_ms,
        "capped_ms":        capped_ms,
        "removed_by_filter": removed_count,
        "unique_after_dedup": unique_count,
    }
    return section, summary


# Build markdown section for one query
def _build_query_section(
    query: str,
    engine_stats: dict,
    raw_count: int,
    filtered_count: int,
    removed_count: int,
    pattern_hist: Counter,
    unique_count: int,
    slot_counts: dict,
    K: int,
    unique_capped: int,
    fetch_ms: int,
    hardslot_ms: int,
    bm25_ms: int,
    embed_ms: int,
    rerank_ms: int,
    capped_ms: int,
    n_candidates: int,
    hs_top: list[dict],
    bm25_top: list[dict],
    embed_top: list[dict],
    ce_top: list[dict],
    capped_top: list[dict],
) -> str:
    ok_engines  = [(n, s["result_count"]) for n, s in sorted(engine_stats.items()) if s["result_count"] > 0]
    engine_line = ", ".join(f"{n}={c}" for n, c in ok_engines)

    hist_str = ", ".join(f"{p}={c}" for p, c in pattern_hist.most_common()) if pattern_hist else "none"

    lines = [
        f"## {query}",
        "",
        f"**Raw results:** {raw_count} → **After URL filter:** {filtered_count} "
        f"(removed_by_filter={removed_count}, patterns: {hist_str})  ",
        f"**Unique after dedup:** {unique_count}  ",
        f"**Engines with results ({len(ok_engines)}):** {engine_line}  ",
        f"**Hard-Slot slot counts:** general={slot_counts.get('general', 0)}, "
        f"academic={slot_counts.get('academic', 0)}, qa={slot_counts.get('qa', 0)}  ",
        f"**BM25-Capped:** K={K}, unique_capped={unique_capped}  ",
        f"**BM25→top-{RETRIEVE_N} candidates used for embed/rerank:** {n_candidates}  ",
        f"**Timing:** fetch={fetch_ms}ms | hardslot={hardslot_ms}ms | bm25={bm25_ms}ms "
        f"| embed={embed_ms}ms | rerank={rerank_ms}ms | capped={capped_ms}ms",
        "",
    ]

    # Config 1 — Hard-Slot
    lines += [
        f"### 1. Hard-Slot Baseline (12/6/2) — unfiltered raw (production behavior)",
        "",
        "| # | Score | Engines | URL |",
        "|---|-------|---------|-----|",
    ]
    for i, item in enumerate(hs_top, 1):
        lines.append(f"| {i} | — | {', '.join(item['engines'])} | {item['url'][:95]} |")
    lines.append("")

    # Config 2 — Filter + BM25
    lines += [
        f"### 2. Filter + BM25-only (k1={BM25_K1}, b={BM25_B}, sw=on, repr={BM25_REPR})",
        "",
        "| # | BM25 Score | Engines | URL |",
        "|---|------------|---------|-----|",
    ]
    for i, item in enumerate(bm25_top, 1):
        lines.append(f"| {i} | {item['score']:.4f} | {', '.join(item['engines'])} | {item['url'][:95]} |")
    lines.append("")

    # Config 3 — Embedding-Cosine
    lines += [
        f"### 3. Filter + BM25→Top{RETRIEVE_N} + Embedding-Cosine Rerank (Qwen3-Embedding-0.6B)",
        "",
        "| # | Cosine | Engines | URL |",
        "|---|--------|---------|-----|",
    ]
    for i, item in enumerate(embed_top, 1):
        lines.append(f"| {i} | {item['score']:.4f} | {', '.join(item['engines'])} | {item['url'][:95]} |")
    lines.append("")

    # Config 4 — Cross-Encoder
    lines += [
        f"### 4. Filter + BM25→Top{RETRIEVE_N} + Cross-Encoder Rerank (Qwen3-Reranker-0.6B)",
        "",
        "| # | CE Score | Engines | URL |",
        "|---|----------|---------|-----|",
    ]
    for i, item in enumerate(ce_top, 1):
        lines.append(f"| {i} | {item['score']:.4f} | {', '.join(item['engines'])} | {item['url'][:95]} |")
    lines.append("")

    # Config 5 — BM25-Capped
    lines += [
        f"### 5. BM25-Capped reference (K={K}, no filter, no rerank)",
        "",
        "| # | BM25 Score | Engines | URL |",
        "|---|------------|---------|-----|",
    ]
    for i, item in enumerate(capped_top, 1):
        lines.append(f"| {i} | {item['score']:.4f} | {', '.join(item['engines'])} | {item['url'][:95]} |")
    lines.append("")

    return "\n".join(lines)


# Build per-category latency + pool-stats aggregation block
def _build_category_summary(summaries: list[dict]) -> str:
    from collections import defaultdict
    cats: dict[str, list[dict]] = defaultdict(list)
    for s in summaries:
        cat = QUERY_CATEGORIES.get(s["query"], "unknown")
        cats[cat].append(s)

    cat_order = ["academic", "product", "technical", "mixed_pathology"]
    lines = [
        "## Per-Category Aggregation",
        "",
        "### Latency (averages across queries in category)",
        "",
        "| Category | n | avg_fetch_ms | avg_rerank_ms | avg_embed_ms | avg_pool_unique |",
        "|----------|---|--------------|---------------|--------------|-----------------|",
    ]
    for cat in cat_order:
        grp = cats.get(cat, [])
        if not grp:
            continue
        n = len(grp)
        avg_fetch  = round(sum(s["fetch_ms"]  for s in grp) / n)
        avg_rerank = round(sum(s["rerank_ms"] for s in grp) / n)
        avg_embed  = round(sum(s["embed_ms"]  for s in grp) / n)
        avg_pool   = round(sum(s["unique_after_dedup"] for s in grp) / n)
        lines.append(f"| {cat} | {n} | {avg_fetch} | {avg_rerank} | {avg_embed} | {avg_pool} |")
    lines.append("")

    lines += [
        "### Pathology Markers (mixed_pathology category — URL filter removals + pool size)",
        "",
        "| Query | removed_filter | pool_unique |",
        "|-------|----------------|-------------|",
    ]
    for s in cats.get("mixed_pathology", []):
        q_short = s["query"][:55]
        lines.append(f"| {q_short} | {s['removed_by_filter']} | {s['unique_after_dedup']} |")
    lines.append("")

    lines += [
        "### Quality Score Table (fill in post-run eyeball — count topical top-10 per query)",
        "",
        "| Category | Query | Hard-Slot | BM25-only | Embed-Cosine | Cross-Encoder | BM25-Capped |",
        "|----------|-------|-----------|-----------|--------------|---------------|-------------|",
    ]
    for cat in cat_order:
        for s in cats.get(cat, []):
            q_short = s["query"][:45]
            lines.append(f"| {cat} | {q_short} | | | | | |")
    lines += [
        "",
        "**Total (sum):** | | | | | | |",
        "",
    ]
    return "\n".join(lines)


# Write full report: global summary + per-query sections
def _write_report(
    sections: list[str],
    summaries: list[dict],
    path: Path,
    total_ms: int,
) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sum_lines = [
        "# Rerank Probe — URL-Filter + BM25 + Semantic Rerank",
        "",
        f"**Date:** {ts}  ",
        f"**Queries:** {len(summaries)}  ",
        f"**Configs:** Hard-Slot / Filter+BM25 / Filter+BM25→Embed / Filter+BM25→CrossEncoder / BM25-Capped  ",
        f"**BM25 params:** k1={BM25_K1}, b={BM25_B}, sw=on, repr={BM25_REPR}  ",
        f"**Retrieve-N for reranking:** {RETRIEVE_N}  ",
        f"**Total wallclock:** {total_ms}ms ({total_ms / 1000:.1f}s)",
        "",
        "## Global Latency Summary",
        "",
        "| Query | fetch_ms | hardslot_ms | bm25_ms | embed_ms | rerank_ms | removed_filter | unique |",
        "|-------|----------|-------------|---------|----------|-----------|----------------|--------|",
    ]
    for s in summaries:
        q_short = s["query"][:40]
        sum_lines.append(
            f"| {q_short} | {s['fetch_ms']} | {s['hardslot_ms']} | {s['bm25_ms']} "
            f"| {s['embed_ms']} | {s['rerank_ms']} | {s['removed_by_filter']} | {s['unique_after_dedup']} |"
        )
    sum_lines.append("")

    category_block = _build_category_summary(summaries)

    header = "\n".join(sum_lines)
    path.write_text("\n\n---\n\n".join([header, category_block] + sections), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(run_probe())
