#!/usr/bin/env python3
"""
Stage 3 v3 — 12-Method Run (Phase 13 eval).

Reads *_pool.json (v3 schema, with positions field) from pool_dir, applies
filter_pool(drop_engines={'google','semantic_scholar'}), then runs 12 methods
per pair. Writes per-pair {mode}_{slug}_methods_v3.json to pool_dir.

Methods:
  M1  C1 Overlap-Count (no GPU)
  M2  RRF post-bucket using positions field (no GPU)
  M3  Structural URL Features — penalty scoring (no GPU)
  M4  C2 BM25 vanilla on pool_full (no GPU)
  M5  C2' BM25-Capped on pool (no GPU)
  M6  C3 Cross-Encoder vanilla — also saves c3_scores for M8/M10
  M7  C3 + Instruction-Prefix (same reranker model, new query prefix)
  M8  RRF + C3 Hybrid — 0.5*norm(c3_scores) + 0.5*norm(rrf_scores), NO new GPU call
  M9  SPLADE standalone — dot product on sparse vectors
  M10 SPLADE + C3 Hybrid — 0.5*norm(c3_scores) + 0.5*norm(splade_scores), NO new GPU call
  M11 Two-Stage C3 + LLM-Filter — C3 top-20 → generator-4b filter → top-10
  M12 LLM-as-Selector direct — full filtered pool → generator-4b → top-10

Execution order: M1-M5 (cheap), M6-M8 (reranker warm), M9-M10 (SPLADE warm), M11-M12 (generator).
Per-GPU model group: pre-flight warmup on first query only; cold_ms tracked separately.

Requires:
  - reranker-0.6b running (M6, M7, M8, M10, M11): rag-cli server start reranker-0.6b
  - splade running (M9, M10):                      rag-cli server start splade
  - generator-4b running (M11, M12):               rag-cli server start generator-4b

Usage:
  ./venv/bin/python dev/search_pipeline/stage3_method_run_v3.py \\
      --pool-dir dev/search_pipeline/runs/value_eval_v3_<ts> \\
      [--smoke]
"""

# INFRASTRUCTURE
import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAG_SRC      = Path("/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/RAG/src")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(RAG_SRC))

# From bm25_sweep_smoke.py: BM25 helpers
from bm25_sweep_smoke import _doc_repr, _tokenize, BM25Uniform, VANILLA_K1

# From rerank_probe_smoke.py: BM25 scorer
from rerank_probe_smoke import _bm25_score

# From clean_pool.py: engine filter
from clean_pool import filter_pool

# RAG server manager — dynamic service URLs
from rag.server_manager import ensure_ready, find_server_url

import logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

TOP_N        = 10
BM25_REPR    = "title+snippet"
DROP_ENGINES = {"google", "semantic_scholar"}
HYBRID_ALPHA = 0.5   # weight for C3 component in hybrids (M8, M10)
RRF_K        = 60    # Cormack 2009

# Module-level; set once in run_method_run_v3 before first GPU call
RERANKER_URL: str = ""
SPLADE_URL:   str = ""
GENERATOR_URL: str = ""

# Instruction prefix for M7
M7_PREFIX = "Find authoritative primary or official sources for: "

# LLM prompt for M11 / M12 (see _build_llm_prompt)
LLM_SYSTEM = (
    'You are evaluating search results for the query: "{query}"\n'
    "Select exactly 10 URLs from the candidate list below that are MOST LIKELY to be "
    "authoritative primary or official sources. Avoid SEO listicles, content farms, "
    "and tutorial blogs unless they are the canonical reference. "
    "Reply with a JSON array of exactly 10 URLs, no other text."
)

MODES = ["general", "pdf", "books", "docs"]
QUERIES = [
    "transformer attention mechanism",
    "postgresql index types btree gin gist performance",
    "python asyncio event loop concurrency",
    "contrastive learning self-supervised representations",
]


# ORCHESTRATOR

def run_method_run_v3(pool_dir: Path, smoke: bool) -> None:
    global RERANKER_URL, SPLADE_URL, GENERATOR_URL

    # Resolve service URLs (fail fast if missing)
    RERANKER_URL, SPLADE_URL, GENERATOR_URL = _init_services()

    pool_files = sorted(pool_dir.glob("*_pool.json"))
    if smoke:
        pool_files = [f for f in pool_files if f.name.startswith("general_")][:1]

    n = len(pool_files)
    print(f"Pools: {n} | pool_dir: {pool_dir}", file=sys.stderr)
    print(file=sys.stderr)

    for i, pool_file in enumerate(pool_files, 1):
        stem      = pool_file.stem           # e.g. "general_transformer_attention_mechan_pool"
        name      = stem[:-5]                # strip "_pool"
        mode, slug = name.split("_", 1)
        data      = json.loads(pool_file.read_text())
        query     = data["query"]
        print(f"[{i}/{n}] mode={mode} | {query}", file=sys.stderr)
        meta = _run_one_pair(pool_dir, mode, slug, query, data)
        print(
            f"  M1={meta['m1_ms']}ms M2={meta['m2_ms']}ms M3={meta['m3_ms']}ms"
            f"  M4={meta['m4_ms']}ms M5={meta['m5_ms']}ms M6={meta['m6_ms']}ms"
            f"  M7={meta['m7_ms']}ms M8={meta['m8_ms']}ms M9={meta['m9_ms']}ms"
            f"  M10={meta['m10_ms']}ms M11={meta['m11_ms']}ms M12={meta['m12_ms']}ms",
            file=sys.stderr,
        )

    print(f"\nDone — methods_v3.json written to {pool_dir}", file=sys.stderr)


# FUNCTIONS

def _query_slug(query: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", query.lower())[:30].strip("_")


# Resolve and verify GPU service endpoints; return (reranker_url, splade_url, generator_url)
def _init_services() -> tuple[str, str, str]:
    print("Initialising GPU services …", file=sys.stderr)

    print("  reranker …", file=sys.stderr)
    ensure_ready("reranker")
    reranker_base = find_server_url("reranker")
    if not reranker_base:
        sys.exit("ERROR: reranker not reachable. Run: rag-cli server start reranker-0.6b")
    reranker_url = f"{reranker_base}/v1/rerank"
    print(f"  reranker OK: {reranker_url}", file=sys.stderr)

    print("  splade …", file=sys.stderr)
    ensure_ready("splade")
    splade_base = find_server_url("splade")
    if not splade_base:
        sys.exit("ERROR: splade not reachable. Run: rag-cli server start splade")
    splade_url = f"{splade_base}/v1/sparse-embeddings"
    print(f"  splade OK: {splade_url}", file=sys.stderr)

    print("  generator-4b …", file=sys.stderr)
    ensure_ready("generator-4b")
    gen_base = find_server_url("generator-4b")
    if not gen_base:
        sys.exit("ERROR: generator-4b not reachable. Run: rag-cli server start generator-4b")
    generator_url = f"{gen_base}/v1/chat/completions"
    print(f"  generator OK: {generator_url}", file=sys.stderr)

    print(file=sys.stderr)
    return reranker_url, splade_url, generator_url


# Run all 12 methods on one pair; save methods_v3.json; return timing metadata dict
def _run_one_pair(pool_dir: Path, mode: str, slug: str, query: str, pool_data: dict) -> dict:
    raw_pool      = pool_data["pool"]
    raw_pool_full = pool_data.get("pool_full", raw_pool)

    # Apply engine filter at method input
    pool      = filter_pool(raw_pool,      DROP_ENGINES)
    pool_full = filter_pool(raw_pool_full, DROP_ENGINES)

    # --- Cheap methods (no GPU) ---
    m1_urls, m1_ms = _apply_m1(pool)
    m2_urls, m2_ms, rrf_scores = _apply_m2(pool)
    m3_urls, m3_ms = _apply_m3(pool)
    m4_urls, m4_ms = _apply_m4(pool_full, query)
    m5_urls, m5_ms = _apply_m5(pool, query)

    # --- Reranker methods (M6 saves c3_scores; M7 saves c3_instr_scores; M8 reuses M6) ---
    m6_urls, m6_ms, c3_scores      = _apply_m6(pool, query)
    m7_urls, m7_ms, c3_instr_scores = _apply_m7(pool, query)
    m8_urls, m8_ms                 = _apply_m8(pool, c3_scores, rrf_scores)

    # --- SPLADE methods (M9 saves splade_scores; M10 reuses M6 + M9) ---
    m9_urls, m9_ms, splade_scores = _apply_m9(pool, query)
    m10_urls, m10_ms              = _apply_m10(pool, c3_scores, splade_scores)

    # --- LLM methods (M11 reuses c3_scores for top-20 pre-filter) ---
    m11_urls, m11_ms, m11_tokens = _apply_m11(pool, query, c3_scores)
    m12_urls, m12_ms, m12_tokens = _apply_m12(pool, query)

    data = {
        "mode":  mode,
        "query": query,
        "pool_size_before_filter": len(raw_pool),
        "pool_size_after_filter":  len(pool),
        # M1
        "m1": m1_urls, "m1_ms": m1_ms,
        # M2
        "m2": m2_urls, "m2_ms": m2_ms,
        # M3
        "m3": m3_urls, "m3_ms": m3_ms,
        # M4
        "m4": m4_urls, "m4_ms": m4_ms,
        # M5
        "m5": m5_urls, "m5_ms": m5_ms,
        # M6
        "m6": m6_urls, "m6_ms": m6_ms,
        # M7
        "m7": m7_urls, "m7_ms": m7_ms,
        # M8
        "m8": m8_urls, "m8_ms": m8_ms,
        # M9
        "m9": m9_urls, "m9_ms": m9_ms,
        # M10
        "m10": m10_urls, "m10_ms": m10_ms,
        # M11
        "m11": m11_urls, "m11_ms": m11_ms,
        "m11_tokens_in": m11_tokens[0], "m11_tokens_out": m11_tokens[1],
        # M12
        "m12": m12_urls, "m12_ms": m12_ms,
        "m12_tokens_in": m12_tokens[0], "m12_tokens_out": m12_tokens[1],
    }
    (pool_dir / f"{mode}_{slug}_methods_v3.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {f"m{i}_ms": data[f"m{i}_ms"] for i in range(1, 13)}


# M1 — C1 Overlap-Count
def _apply_m1(pool: list[dict]) -> tuple[list[str], int]:
    t0     = time.perf_counter()
    ranked = sorted(pool, key=lambda m: (-len(m["engines"]), m["min_position"]))
    ms     = round((time.perf_counter() - t0) * 1000)
    return [m["url"] for m in ranked[:TOP_N]], ms


# M2 — RRF post-bucket using positions field; also returns rrf_scores for M8
def _apply_m2(pool: list[dict]) -> tuple[list[str], int, dict[str, float]]:
    t0  = time.perf_counter()
    scores: dict[str, float] = {}
    for m in pool:
        url   = m["url"]
        pos   = m.get("positions", {})
        score = sum(1.0 / (RRF_K + p) for p in pos.values()) if pos else 1.0 / (RRF_K + m.get("min_position", 999))
        scores[url] = score
    ranked = sorted(pool, key=lambda m: -scores[m["url"]])
    ms     = round((time.perf_counter() - t0) * 1000)
    return [m["url"] for m in ranked[:TOP_N]], ms, scores


# M3 — Structural URL Features (penalty scoring, lower is better)
def _apply_m3(pool: list[dict]) -> tuple[list[str], int]:
    t0 = time.perf_counter()

    def _penalty(url: str) -> float:
        p   = 0.0
        low = url.lower()
        if re.search(r"[?&](q|query|search|keyword|term|p)=", low):
            p -= 0.5
        parsed = urlparse(url)
        path   = parsed.path.lower()
        if re.search(r"/(search|results|sresults)/", path):
            p -= 0.3
        depth = len([s for s in path.split("/") if s])
        if depth > 4:
            p -= 0.1 * (depth - 4)
        return p

    scored = [(m, _penalty(m["url"])) for m in pool]
    ranked = sorted(scored, key=lambda x: (-x[1], x[0].get("min_position", 999)))
    ms     = round((time.perf_counter() - t0) * 1000)
    return [m["url"] for m, _ in ranked[:TOP_N]], ms


# M4 — C2 BM25 vanilla on pool_full
def _apply_m4(pool_full: list[dict], query: str) -> tuple[list[str], int]:
    t0     = time.perf_counter()
    scored = _bm25_score(pool_full, query, TOP_N)
    ms     = round((time.perf_counter() - t0) * 1000)
    return [m["url"] for m, _ in scored], ms


# M5 — C2' BM25-Capped on pool (filtered+capped = oracle input)
def _apply_m5(pool: list[dict], query: str) -> tuple[list[str], int]:
    t0     = time.perf_counter()
    scored = _bm25_score(pool, query, TOP_N)
    ms     = round((time.perf_counter() - t0) * 1000)
    return [m["url"] for m, _ in scored], ms


# Cross-encoder rerank call; returns [(index, relevance_score), ...]
def _cross_encoder_rerank(query: str, documents: list[str]) -> list[tuple[int, float]]:
    r = httpx.post(RERANKER_URL, json={"query": query, "documents": documents}, timeout=120.0)
    r.raise_for_status()
    return [(item["index"], item["relevance_score"]) for item in r.json().get("results", [])]


# M6 — C3 Cross-Encoder vanilla; returns (urls, ms, score_dict)
def _apply_m6(pool: list[dict], query: str) -> tuple[list[str], int, dict[str, float]]:
    return _rerank_pool(pool, query, query_text=query)


# M7 — C3 + Instruction-Prefix; returns (urls, ms, score_dict)
def _apply_m7(pool: list[dict], query: str) -> tuple[list[str], int, dict[str, float]]:
    return _rerank_pool(pool, query, query_text=M7_PREFIX + query)


# Shared reranker implementation for M6/M7
def _rerank_pool(pool: list[dict], query: str, query_text: str) -> tuple[list[str], int, dict[str, float]]:
    if not pool:
        return [], 0, {}
    valid = [(m, _doc_repr(m, BM25_REPR)) for m in pool if _doc_repr(m, BM25_REPR).strip()]
    if not valid:
        return [], 0, {}
    docs_v  = [m for m, _ in valid]
    texts_v = [t for _, t in valid]
    t0 = time.perf_counter()
    try:
        pairs      = _cross_encoder_rerank(query_text, texts_v)
        score_dict = {docs_v[idx]["url"]: score for idx, score in pairs}
        ranked     = sorted(pairs, key=lambda x: -x[1])[:TOP_N]
        ms         = round((time.perf_counter() - t0) * 1000)
        return [docs_v[idx]["url"] for idx, _ in ranked], ms, score_dict
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000)
        print(f"  reranker error: {exc}", file=sys.stderr)
        return [], ms, {}


# Min-max normalize a score dict to [0, 1]; returns new dict
def _normalize(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {k: 0.5 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


# M8 — RRF + C3 Hybrid (no GPU; reuses c3_scores from M6 and rrf_scores from M2)
def _apply_m8(
    pool: list[dict], c3_scores: dict[str, float], rrf_scores: dict[str, float]
) -> tuple[list[str], int]:
    t0       = time.perf_counter()
    c3_norm  = _normalize(c3_scores)
    rrf_norm = _normalize(rrf_scores)
    combined = {
        m["url"]: HYBRID_ALPHA * c3_norm.get(m["url"], 0.0) + (1 - HYBRID_ALPHA) * rrf_norm.get(m["url"], 0.0)
        for m in pool
    }
    ranked = sorted(pool, key=lambda m: -combined[m["url"]])
    ms     = round((time.perf_counter() - t0) * 1000)
    return [m["url"] for m in ranked[:TOP_N]], ms


# M9 — SPLADE standalone; returns (urls, ms, splade_scores)
def _apply_m9(pool: list[dict], query: str) -> tuple[list[str], int, dict[str, float]]:
    if not pool:
        return [], 0, {}
    docs    = [_doc_repr(m, BM25_REPR) for m in pool]
    all_texts = [query] + docs
    t0 = time.perf_counter()
    try:
        r = httpx.post(SPLADE_URL, json={"input": all_texts, "model": "splade"}, timeout=120.0)
        r.raise_for_status()
        vectors   = [item["sparse_vector"] for item in r.json()["data"]]
        q_vec     = vectors[0]
        q_map     = dict(zip(q_vec["indices"], q_vec["values"]))
        scores: dict[str, float] = {}
        for m, d_vec in zip(pool, vectors[1:]):
            dot = sum(q_map.get(i, 0.0) * v for i, v in zip(d_vec["indices"], d_vec["values"]))
            scores[m["url"]] = dot
        ranked = sorted(pool, key=lambda m: -scores[m["url"]])
        ms     = round((time.perf_counter() - t0) * 1000)
        return [m["url"] for m in ranked[:TOP_N]], ms, scores
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000)
        print(f"  SPLADE error: {exc}", file=sys.stderr)
        return [], ms, {}


# M10 — SPLADE + C3 Hybrid (no GPU; reuses c3_scores from M6 + splade_scores from M9)
def _apply_m10(
    pool: list[dict], c3_scores: dict[str, float], splade_scores: dict[str, float]
) -> tuple[list[str], int]:
    t0          = time.perf_counter()
    c3_norm     = _normalize(c3_scores)
    splade_norm = _normalize(splade_scores)
    combined    = {
        m["url"]: HYBRID_ALPHA * c3_norm.get(m["url"], 0.0) + (1 - HYBRID_ALPHA) * splade_norm.get(m["url"], 0.0)
        for m in pool
    }
    ranked = sorted(pool, key=lambda m: -combined[m["url"]])
    ms     = round((time.perf_counter() - t0) * 1000)
    return [m["url"] for m in ranked[:TOP_N]], ms


# Build LLM prompt for M11/M12; pool_entries is the candidate list
def _build_llm_prompt(query: str, pool_entries: list[dict]) -> tuple[str, str]:
    system = LLM_SYSTEM.format(query=query)
    lines  = ["Candidates:"]
    for i, m in enumerate(pool_entries, 1):
        title   = (m.get("title")   or "").strip().replace("\n", " ")[:120]
        snippet = (m.get("snippet") or "").strip().replace("\n", " ")[:200]
        lines.append(f"{i}. {m['url']} — {title}")
        if snippet:
            lines.append(f"   {snippet}")
    user = "\n".join(lines)
    return system, user


# Call generator-4b; return (urls, ms, (tokens_in, tokens_out))
def _call_generator(system: str, user: str, known_urls: set[str]) -> tuple[list[str], int, tuple[int, int]]:
    payload = {
        "model":       "qwen",
        "messages":    [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens":  512,
        "temperature": 0.0,
    }
    t0 = time.perf_counter()
    try:
        r = httpx.post(GENERATOR_URL, json=payload, timeout=120.0)
        r.raise_for_status()
        body       = r.json()
        content    = body["choices"][0]["message"]["content"].strip()
        tokens_in  = body.get("usage", {}).get("prompt_tokens", 0)
        tokens_out = body.get("usage", {}).get("completion_tokens", 0)
        # Strip markdown fences if present
        if content.startswith("```"):
            content = re.sub(r"^```[a-z]*\n?", "", content).rstrip("`").strip()
        urls  = json.loads(content) if content.startswith("[") else []
        urls  = [u for u in urls if isinstance(u, str) and u in known_urls][:TOP_N]
        ms    = round((time.perf_counter() - t0) * 1000)
        return urls, ms, (tokens_in, tokens_out)
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000)
        print(f"  generator error: {exc}", file=sys.stderr)
        return [], ms, (0, 0)


# M11 — Two-Stage C3 + LLM-Filter (C3 top-20 → generator filter → top-10)
def _apply_m11(
    pool: list[dict], query: str, c3_scores: dict[str, float]
) -> tuple[list[str], int, tuple[int, int]]:
    if not pool:
        return [], 0, (0, 0)
    # Stage a: take C3 top-20
    ranked_by_c3  = sorted(pool, key=lambda m: -c3_scores.get(m["url"], 0.0))
    top20_entries = ranked_by_c3[:20]
    known_urls    = {m["url"] for m in top20_entries}
    # Stage b: generator filter
    system, user  = _build_llm_prompt(query, top20_entries)
    urls, ms, toks = _call_generator(system, user, known_urls)
    return urls, ms, toks


# M12 — LLM-as-Selector direct (full filtered pool → generator → top-10)
def _apply_m12(pool: list[dict], query: str) -> tuple[list[str], int, tuple[int, int]]:
    if not pool:
        return [], 0, (0, 0)
    known_urls    = {m["url"] for m in pool}
    system, user  = _build_llm_prompt(query, pool)
    urls, ms, toks = _call_generator(system, user, known_urls)
    return urls, ms, toks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 3 v3 — 12-Method Run (Phase 13)")
    parser.add_argument("--pool-dir", required=True, help="Directory with *_pool.json from Stage 1 v3")
    parser.add_argument("--smoke",    action="store_true", help="Process first general pool only")
    args     = parser.parse_args()
    pool_dir = Path(args.pool_dir)
    if not pool_dir.exists():
        sys.exit(f"ERROR: pool_dir does not exist: {pool_dir}")
    run_method_run_v3(pool_dir=pool_dir, smoke=args.smoke)
