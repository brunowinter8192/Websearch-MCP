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
| scrape_url | url | Page → full markdown (chromium lane) |
| scrape_url_camoufox | url | Page → full markdown (Camoufox lane) |

**The two scrape lanes are a free per-call choice.**
Page didn't come through → try the other lane once, then report both failures plainly.

## Search Strategy

1. `search_web` for the engine breakdown. For a deep dive, fire 2–4 parallel calls with query variations.
2. `search_engine_drilldown` to get an engine's URLs — which engine(s) is your free choice, guided by the breakdown counts.
3. `scrape_url` the relevant URLs. PDFs and books: give the user the exact URLs from the search results — the user downloads them. Do not `scrape_url` a `.pdf` URL (it returns an error: the PDF must be downloaded by the user).

**Write the query in the language you want results in.**
The user-chat language does not apply here — a German conversation still gets English queries when English results are wanted.

---

## Permanent Capture Workflow

When the user wants to permanently capture a whole domain into RAG — "crawl X and index it", "RAG-fähig machen". A worker drives the capture; this is your setup. The worker activates `websearch-capture-and-index`. (PDF → MD conversion is a separate flow — see the `websearch-pdf` skill.)

### Step 1 — Source

Identify the source: a seed domain URL.

### Step 2 — Collection

Confirm the target collection with the user (MANDATORY ASK — never pick it yourself):
> "Target collection: `<project>-reference`. OUTPUT_DIR: `~/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/<project>-reference/`. Confirm or override?"

Default is `<current_project>-reference`, but it may be another project's reference collection. Collection names are hyphen-separated (`websearch-reference`), never underscore — an underscore variant creates a second, parallel collection instead of appending to the existing one.

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
STOP at your skill's Step 3 (cull review) — report the URL-list path + per-section breakdown and WAIT for my cull decision before scraping. Then report the funnel when done (incl. blocks-detected). No commit needed (output is data files).
```

```bash
worker-cli spawn capture-<collection_lower> /tmp/spawn-<name>.md <current_project_root> sonnet
```

### Step 4 — Cull Review

When the worker stops at its cull gate it reports the URL-list path + a per-section breakdown. Review it against what the user actually needs this session — drop sections that are valid content but off-topic (e.g. a GitHub REST capture aimed at search/contents/git-trees does not need `actions`/`enterprise-admin`/`scim`). This is YOUR call, not the worker's.

**YOU edit the `/tmp` URL-list file itself — never send the worker patterns to apply.**
Strip the unwanted URLs from the file, then tell the worker the resulting line count and give it go. The worker re-reads the same path and scrapes whatever is in it; it never rewrites the list. Rationale: the culled file on disk IS the verifiable state — its line count says exactly what will be scraped. Handing over patterns instead defers the cull into the worker and makes it visible only after the scrape has already run.

### Step 5 — Funnel Report

When the worker reports the funnel, check two lines.

`blocks detected` — non-zero means it found cookie/paywall MDs (not auto-stripped). Decide from the reported patterns whether a `src/` strip-script is warranted.

`systemic gap` — anything other than `none` means a domain class did not come through. **Flag it to the user and keep rolling.** The capture is already indexed with whatever passed; there is nothing to re-run. The scraper carries one fixed calibration and exposes no per-domain lever, so this is NOT a value to adjust here — it is input for a separate tuning session against this repo and `src/logs/pipe_scrape_log.jsonl`. Report to the user: the domain, the failure pattern, the count, the worker's evidence and suspected cause, and that resolving it needs its own session. Then continue whatever the user actually asked for.

**Between Step 4 and Step 5, the worker owns Scrape → Cleanup → Index end-to-end.**
You intervene at exactly TWO points: (a) hand the worker the culled `/tmp` URL list + go (Step 4), and (b) receive the final funnel report (Step 5).
