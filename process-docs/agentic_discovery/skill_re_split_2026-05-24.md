# Skill Re-Split: web-research ↔ cleanup-and-index

**Date:** 2026-05-24
**Status:** Re-split executed. Reverts the 2026-05-23 consolidation.

## Context

On 2026-05-23, the `cleanup-and-index` skill was merged into `web-research` to consolidate the permanent-capture workflow into a single skill. After one end-to-end test session (Trafilatura Reference Indexing), the consolidation showed an architectural problem.

## Why the merger was wrong

`web-research` is Opus-loaded — it orchestrates search, scrape, explore, two-stage filtering, decides collection name, spawns the worker. The Phase 0/1/2 protocol (acquisition crawl command, Five Shapes cleanup pattern, Sphinx-specific strip patterns, indexing skip-logic) is purely worker-internal — Opus never executes any of it. After the merge, every Opus session that activated web-research loaded ~400 LOC of Phase-0/1/2 detail into Opus context for no benefit, while the actual worker prompt (which DOES need that detail) had to re-load the same skill on the worker side.

## The split

- `skills/web-research/` (481 LOC) — Opus-side: CLI tools (search_web, scrape_url, explore_site, filter_urls, …), Search Strategy, Plugin Routing, Permanent Capture Workflow → Setup (Identify Source, Explore + Filter URLs two-stage flow, Collection Name) + Common Inputs + Spawn-Worker template + Wait-Verify.
- `skills/cleanup-and-index/` (391 LOC) — Worker-side: Mode 1 Web-MD (Phase 0 Acquisition / Phase 1 Cleanup with Five Shapes + Sphinx-specifics + Safety Rules / Phase 2 Index), Mode 2 PDF (same shape), Completion Report, Anti-Patterns.

Spawn-Worker template inside web-research changed: worker prompt now says `activate the cleanup-and-index skill via Skill(skill="cleanup-and-index")` instead of `activate the web-research skill`.

## What changes for Opus context

After the split, activating web-research loads 481 LOC instead of 865. The 384-LOC difference is exactly the worker-protocol content that Opus never read for orchestration purposes.

## What changes for the worker

Worker prompt is unchanged in structure (still 4 inputs: MODE / INPUT / COLLECTION / OUTPUT_DIR). Worker activates `cleanup-and-index` instead of `web-research`. All phase content is preserved verbatim, no protocol changes.

## Supersedes

The 2026-05-23 consolidation. That merger is now reverted. No content was lost — only relocated.
