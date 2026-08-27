---
name: websearch-web-research
description:
---

# Web Research — Skill

**Default = Permanent Capture Workflow.**
Assume permanent capture into RAG — always. Ad-hoc in-chat scraping only when the user EXPLICITLY asks for it. (PDF → MD conversion is a separate flow — see the `websearch-pdf` skill.)

Run via `websearch <command>` (in PATH), foreground — no `&`, no redirect.

## Commands

| Command | Args | Does |
|---|---|---|
| search_web | query (2–5 keywords) | Search: counts per engine |
| search_engine_drilldown | query --engine <name> | URLs for one engine from the prior search_web |
| scrape_url_chromium | url | Page → full markdown |

**One scrape lane, no per-call choice.**
It returns pruned markdown (PruningContentFilter). Page didn't come through → report the failure plainly with the acquisition facts the command prints; do not retry silently.

## Search Strategy

1. `search_web` for the engine breakdown. For a deep dive, fire 2–4 parallel calls with query variations.
2. `search_engine_drilldown` to get an engine's URLs — which engine(s) is your free choice, guided by the breakdown counts.
3. `scrape_url_chromium` the relevant URLs. PDFs and books: give the user the exact URLs from the search results — the user downloads them. Do not scrape a `.pdf` URL (it returns an error: the PDF must be downloaded by the user).

**Write the query in the language you want results in.**
The user-chat language does not apply here — a German conversation still gets English queries when English results are wanted.

---

## Permanent Capture Workflow

### Step 1 — Source

Identify the seed domain URL via the search pipe: `search_web` → `search_engine_drilldown` → the domain(s) worth capturing are in those URLs.

**One capture job may span MULTIPLE domains — that is fully supported, not an exception.**
Hand the worker several seed domains (or a mixed, pre-curated URL list across domains) in a single job. The `websearch-capture-and-index` skill processes them step-by-step across ALL domains — discover all → select all → one cull stop → scrape all → clean all → index once at the end — never domain-by-domain.

### Step 2 — Collection

Confirm the target collection with the user (MANDATORY ASK — never pick it yourself):
> "Target collection: `<project>-reference`. OUTPUT_DIR: `~/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/<project>-reference/`. Confirm or override?"

Default is `<current_project>-reference`, but it may be another project's reference collection.

### Step 3 — Spawn

Spawn the worker. It activates the `websearch-capture-and-index` skill and runs the pipe: Discovery → URL Selection → **STOP (cull review, your gate)** → Scrape → Cleanup → Index. You provide the seed, collection, output dir.

Worker prompt (`/tmp/spawn-<name>.md`):

```markdown
You are a WORKER.
FIRST: activate the websearch-capture-and-index skill via Skill(skill="websearch-capture-and-index").
Inputs:
- SEED_URL: <root domain URL>
- COLLECTION: <name>
- OUTPUT_DIR: ~/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/<name>/
STOP at your skill's Step 3 (cull review) — report the URL-list path + per-section breakdown and WAIT for my cull decision before scraping. Then report the funnel when done. No commit needed (output is data files).
```

```bash
worker-cli spawn capture-<collection_lower> /tmp/spawn-<name>.md <current_project_root> sonnet
```

### Step 4 — Cull Review

When the worker stops at its cull gate it reports the URL-list path + a per-section breakdown. Review it against what the user actually needs this session — drop sections that are valid content but off-topic (e.g. a GitHub REST capture aimed at search/contents/git-trees does not need `actions`/`enterprise-admin`/`scim`). This is YOUR call, not the worker's.

**YOU edit the `/tmp` URL-list file itself — never send the worker patterns to apply.**
Strip the unwanted URLs from the file, then tell the worker the resulting line count and give it go.

### Step 5 — Funnel Report

Receive the worker's funnel report. Tell the user the error count — "bei X URLs ging was schief" — nothing else.
