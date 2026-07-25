# Iter 8 — Dev Pipeline Completion Plan (Production-Migration Prep)

**Date:** 2026-05-28
**Scope:** Design session — decide storage layout, dedup mechanism, metadata policy, and missing dev stages so the CoinDesk pipeline reaches end-to-end runnable state with only a cron trigger missing.

No code written this session. Decisions captured here as the resume anchor for the next IMPLEMENT session.

## Storage Layout

- **Path:** `/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/crypto_news/`
- **Collection name:** `crypto_news` (= directory name; RAG's `index-dir` defaults collection to dir basename)
- **Rationale:** RAG repo is data-storage-only; searxng owns all pipeline logic + state. Collection scoped to Layer 1 (crypto-native), separate from parked Layer 2 (macro) / Layer 3 (sentiment) which need different filter strategies.
- **Subdirectories:** flat. Existing collections (`reddit_posts`, `searxng_reference`) are all flat — source encoded in filename via `__` separator.

## Filename Convention

- **Pattern:** `coindesk__<sha256(url)[:12]>.md`
- **Hash source:** existing `dev/news_pipeline/02b_coindesk_scrape_fresh_context.py:49` already computes `hashlib.sha256(url.encode()).hexdigest()[:12]`. Stage 5 just prepends the source-prefix on copy.
- **Per-source uniqueness:** prefix isolates sites. `coindesk__abc123.md` vs `theblock__abc123.md` — cross-source hash collision structurally impossible (URL is the hash input; different URLs → different hashes; same URL but different sites is meaningless because URLs are site-scoped).

## Dedup Mechanism — Filesystem-as-Seen-State

**Decision:** no separate seen-URLs JSON state file. The presence of `coindesk__<hash>.md` in the RAG storage dir IS the seen marker.

**Stage 4 (dedup gate) logic:**
1. Read newest `01_output/discover_*.json`.
2. For each entry, compute `target = RAG_DIR/crypto_news/coindesk__<sha256(url)[:12]>.md`.
3. If `target` exists → skip. Else → include in filtered output.
4. Write `04_output/discover_filtered_<ts>.json` with same schema as discover.

**Rationale over a separate state file:**
- Single source of truth — no drift between "claimed seen" and "actually stored".
- Reproducible from cold start by listing the storage dir.
- No I/O contention on a shared JSON if multiple sites ever run in parallel.
- Cron is idempotent without extra plumbing.

**Failure tolerance:** orphan files (copied but not yet indexed, e.g. RAG-server down between copy and index) self-heal — next Stage 4 sees file → skips URL; next Stage 5 sees file already in place → idempotent re-copy is harmless; next `index-dir` sees unindexed hash → indexes. No manual cleanup required.

## Metadata Policy — None

**Decision:** MD content is exactly what Stage 3 currently produces — `# <title>\n\n<cleaned body>`. No embedded `**URL:**` / `**Source:**` / `**Published:**` header block.

**Reason:** Reddit-collection convention with embedded metadata header has been retired going forward (user direction this session). Dedup mechanism is filesystem-based, not content-based — needs zero metadata in MD body. Title is content (H1 anchor), not metadata.

**Implication:** RAG search results return clean prose chunks without metadata clutter. Reverse-lookup hash → URL is not supported by MD content. If ever needed, can be reconstructed externally from `03_output/manifest.json` snapshots or by re-running discover on the source.

## Missing Stages

### Stage 4 — Dedup Gate (NEW)

- File: `dev/news_pipeline/04_dedup.py`
- Input: newest `01_output/discover_*.json` (auto-pick) + `RAG_DIR/crypto_news/`
- Output: `04_output/discover_filtered_<ts>.json` (same schema as discover, subset of entries)
- CLI: `--input <path>` override; `--rag-dir <path>` override (default hardcoded to canonical RAG path); `--source coindesk` to set the filename-prefix used in the existence check
- Logic: pure-Python, no browser, no network — just file existence checks. Hash function reused from Stage 2b (`hashlib.sha256(url.encode()).hexdigest()[:12]`).

### Stage 5 — Publish (NEW)

- File: `dev/news_pipeline/05_publish.py`
- Input: `03_output/*.md` + `03_output/manifest.json`
- Output: copies each MD to `RAG_DIR/crypto_news/coindesk__<hash>.md` (rename with source-prefix); then triggers `subprocess.run(["python", "workflow.py", "index-dir", "data/documents/crypto_news"], cwd=RAG_REPO)` to index.
- CLI: `--input <dir>` override; `--rag-dir <path>` override; `--source coindesk` for filename-prefix; `--skip-index` for testing without triggering RAG
- Idempotency: `shutil.copy2` is safe to re-run; RAG hash-skip in `index-dir` handles re-index of already-indexed files.

### Stage 2b — Input-Fallback Tweak (SMALL EDIT)

- File: `dev/news_pipeline/02b_coindesk_scrape_fresh_context.py`
- Current: `pick_latest_input()` auto-picks `01_output/discover_*.json`
- Needed: try `04_output/discover_filtered_*.json` first, fall back to `01_output/discover_*.json` if no 04_output exists
- Reason: when Stage 4 runs, Stage 2b should consume its filtered output. When Stage 2b is invoked standalone (no dedup desired), the fallback to raw discover preserves current behavior.

## Run Sequence (Cron Wrapper Will Just Chain These)

1. `01_coindesk_discover.py --headless`
2. `04_dedup.py`
3. `02b_coindesk_scrape_fresh_context.py` (auto-picks 04_output via the fallback edit)
4. `03_coindesk_cleanup.py`
5. `05_publish.py` (copies + triggers RAG index-dir)

## Validation Workflow (Next Session)

1. Build Stages 4 + 5, edit Stage 2b's input fallback
2. End-to-end run from a fresh `01_output/`
3. User spot-checks sample MDs in `RAG_DIR/crypto_news/`
4. Test RAG queries: `rag-cli search_hybrid "<query>" crypto_news`
5. If queries return sane results → src/ promotion (separate step, possibly next-next session)

## Promotion Path — Deferred

Promotion `dev/news_pipeline/` → `src/news/` (or similar) is NOT part of this iteration. Sequence after validation:

1. Refactor scripts into `src/news/{discover.py, dedup.py, scrape.py, cleanup.py, publish.py}` + a `pipeline.py` orchestrator
2. Single entry script accepting `--source coindesk` (later `--source theblock` etc.)
3. Cron points to that entry script

## Next-Site Discovery — Deferred

After CoinDesk runs end-to-end in prod, next Layer-1 site selected per the channel-independence criterion. Candidates from the active-layer list: The Block, CoinTelegraph, Decrypt, CryptoSlate, Bitcoin Magazine, NewsBTC, AmbCrypto, BeInCrypto, CoinGape, Crypto Briefing, Bankless, The Defiant, U.Today, BTC-ECHO.

## Open Questions

None.
