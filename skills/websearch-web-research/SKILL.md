---
name: websearch-web-research
description:
---

# Web Research — Skill

**Default = Permanent Capture Workflow (worker).** When the user wants a source pulled in, assume they want it captured into RAG — spawn the capture worker (bottom of this file). Only run ad-hoc in-chat scraping (`search_web` / `search_engine_drilldown` / `scrape_url` directly) when the user EXPLICITLY says "ad hoc" (or equivalent: "nur kurz nachschauen", "nicht indexieren").

Ad-hoc web research via `websearch`: search across engines, drill into one engine for its URLs, scrape a page to filtered markdown. To permanently capture a whole domain into RAG, use the Permanent Capture Workflow at the bottom — that spawns a worker; this CLI is for in-chat lookups. (PDF → MD conversion is a separate flow — see the `websearch-pdf` skill.)

## CLI Invocation

All tools run via the `websearch` wrapper (in PATH). Run them in the foreground — no `&`, no redirect.

```bash
# Search — engine breakdown (counts per engine, no URLs)
websearch search_web "machine learning retrieval"
websearch search_web --docs "react hooks"

# URLs for one engine (from the search_web cache)
websearch search_engine_drilldown "machine learning retrieval" --engine google

# Scrape a page to filtered markdown
websearch scrape_url "https://example.com/article"
```

On error (missing dependency, engine timeout): prints to stderr, exits non-zero.

## Parameters

### search_web

| Parameter | Type | Description |
|-----------|------|-------------|
| query | str (required) | Search query, 2–5 keywords |
| --books | flag | Book lookup (+book modifier + book-domain whitelist). Mutually exclusive with --pdf / --docs |
| --pdf | flag | PDF lookup (+pdf modifier + PDF-host whitelist). Mutually exclusive with --books / --docs |
| --docs | flag | Docs lookup (+documentation modifier + noise blacklist). Mutually exclusive with --books / --pdf |

All three mode flags restrict the engine set to google/duckduckgo/mojeek, append the modifier to the query, and post-filter URLs; use the same flag on the matching `search_engine_drilldown` call.

Engines: google, duckduckgo, mojeek, lobsters, semantic_scholar, openalex, crossref, stack_exchange, open_library.

### search_engine_drilldown

| Parameter | Type | Description |
|-----------|------|-------------|
| query | str (required) | Must match the prior search_web call |
| --engine | str (required) | One engine name (see list above) |
| --books / --pdf / --docs | flag | Must match the prior search_web call's mode |

### scrape_url

| Parameter | Type | Description |
|-----------|------|-------------|
| url | str (required) | URL to fetch as filtered markdown |

Returns 15k-capped markdown (PruningContentFilter) with a `# Content from: <url>` header. No options. For raw, full-fidelity capture of a whole domain, use the Permanent Capture Workflow — not this.

## Search Strategy

1. `search_web` for the engine breakdown. For a deep dive, fire 2–4 parallel calls with query variations.
2. `search_engine_drilldown` per engine with a useful count to get its URLs.
3. `scrape_url` the relevant URLs. PDFs and books: give the user the exact URLs from the search results — the user downloads them. Do not `scrape_url` a `.pdf` URL (it returns an error: the PDF must be downloaded by the user).

Write the query in the language you want results in.

Query diversity: when investigating an entity X, vary the angle across queries — X as the anchor, the broader category without X, alternatives/competitors, the underlying technique.

---

## Permanent Capture Workflow

When the user wants to permanently capture a whole domain into RAG — "crawl X and index it", "RAG-fähig machen". A worker drives the capture; this is the Opus-side setup. The worker activates `websearch-capture-and-index`. (PDF → MD conversion is a separate flow — see the `websearch-pdf` skill.)

**1.** Identify the source: a seed domain URL.

**2.** Confirm the target collection with the user (MANDATORY ASK — never pick it yourself):
> "Target collection: `<project>_reference`. OUTPUT_DIR: `~/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/<project>_reference/`. Confirm or override?"

Default is `<current_project>_reference`, but it may be another project's reference collection.

**3.** Spawn the worker. It activates the `websearch-capture-and-index` skill and runs the pipe: Discovery → URL Selection → **STOP (Opus cull, Phase 1b)** → Scrape → Cleanup → Index. Opus provides the seed, collection, output dir.

Worker prompt (`/tmp/spawn-<name>.md`):

```markdown
You are a WORKER.
FIRST: activate the websearch-capture-and-index skill via Skill(skill="websearch-capture-and-index").
Inputs:
- SEED_URL: <root domain URL>
- COLLECTION: <name>
- OUTPUT_DIR: ~/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/<name>/
STOP at Phase 1b — report the URL-list path + per-section breakdown and WAIT for my cull decision before scraping. Then report the funnel when done (incl. blocks-detected). No commit needed (output is data files).
```

```bash
worker-cli spawn capture-<collection_lower> /tmp/spawn-<name>.md <current_project_root> sonnet
```

### Opus gates

**4.** Cull review. When the worker stops at Phase 1b it reports the URL-list path + a per-section breakdown. Review it against what the user actually needs this session — drop sections that are valid content but off-topic (e.g. a GitHub REST capture aimed at search/contents/git-trees does not need `actions`/`enterprise-admin`/`scim`). Send the worker the sections/patterns to drop. The worker applies the cull and proceeds. This is YOUR call, not the worker's.

**5.** When the worker reports the funnel, check `blocks detected` — non-zero means it found cookie/paywall MDs (not auto-stripped). Decide from the reported patterns whether a `src/` strip-script is warranted.

**Between step 4 and step 5, Opus does NOTHING.** No log-checking, no `rag-cli status` polling, no waking the worker for Cleanup/Index, no progress probes. The worker owns Scrape → Cleanup → Index end-to-end. Opus intervenes at exactly TWO points: (a) hand the worker the culled `/tmp` URL list + go (step 4), and (b) receive the final funnel report (step 5).
