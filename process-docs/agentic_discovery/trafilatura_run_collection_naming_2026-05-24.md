# Collection Naming Recovery — 2026-05-24

## What happened

Phase 4 of Trafilatura Reference Indexing was executed end-to-end: 25 Trafilatura URLs filtered, crawled, Sphinx-cleaned (5-shape profile, validated), and indexed. The indexing target was `Trafilatura_Reference` (159 chunks produced) — WRONG. The project's convention (one `<project>_reference` collection per project) was violated because the prior session decided `Trafilatura_Reference` without cross-checking the naming convention documented in the web-research skill.

## Recovery

1. Deleted `Trafilatura_Reference` collection (159 chunks, DB only — `--remove-source` NOT used).
2. Removed the 25 leftover `.json` sidecar files from `RAG/data/documents/Trafilatura_Reference/` (created by the wrong indexing run, not moved by the initial `mv *.md`).
3. Moved 25 cleaned `.md` files from `RAG/data/documents/Trafilatura_Reference/` to `searxng_reference/`.
4. Removed now-empty `Trafilatura_Reference/` directory.
5. Re-indexed into `searxng_reference` via `workflow.py index-dir` — incremental add, existing 875 chunks untouched.

**Log summary:** `Skipped (hash unchanged): 2 | Adopted: 0 | To index: 25 → Done: 25 files indexed (159 chunks)`
**Post-state:** `searxng_reference` = 1034 chunks (875 pre-existing + 159 Trafilatura).

## Skill fix

- `skills/web-research/` naming-convention guidance was internally contradictory — one line said `PascalCase, descriptive: SearXNG_Docs, Crawl4AI_Reference, RAG_Survey_2024`, directly contradicting the `<project>_reference` (lowercase, underscore) convention stated elsewhere. Replaced with an explicit "Confirm Collection Target with User (MANDATORY ASK)" block requiring Opus to ask the user before picking a collection name.
- `skills/cleanup-and-index/` Phase 2 — added a prominent `### CRITICAL` block at the top of Phase 2 describing hash-based incremental skip-logic: skipped/adopted/to_index buckets, additive-by-default behavior, `--force` flag. Prevents future workers from assuming index-dir wipes existing chunks.

## Closes

Trafilatura Reference Indexing — complete. Cleaned files in `searxng_reference/`, 159 Trafilatura chunks in `searxng_reference` collection alongside pre-existing 875 chunks.
