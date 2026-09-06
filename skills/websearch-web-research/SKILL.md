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
   - For papers and books, prefer drilling `openalex` — its entries carry a `PDF:` line with the direct full-text URL.
3. `scrape_url_chromium` the relevant URLs. PDFs and books: give the user the exact URLs from the search results — the user downloads them. Do not scrape a `.pdf` URL (it returns an error: the PDF must be downloaded by the user).

**Write the query in the language you want results in.**
The user-chat language does not apply here — a German conversation still gets English queries when English results are wanted.

---

## Permanent Capture Workflow

### Step 1 — Source

1. Ask the user for the target collection and propose `<current_project>-reference`.

2. Drill down to the seed URL via `search_web` → `search_engine_drilldown`.

3. Spawn the worker.

   ```bash
   worker-cli spawn capture-<collection_lower> /tmp/spawn-<name>.md <current_project_root> sonnet
   ```

   Its prompt activates the capture skill and carries the seed URL:

   ```markdown
   You are a WORKER.
   FIRST: activate the websearch-capture-and-index skill via Skill(skill="websearch-capture-and-index").
   SEED_URL: <seed url>
   ```

**Insight**
- The worker runs discovery, reports the path of the full URL list, and goes idle.

### Step 2 — Cull Review

**Input, handed over by the worker.**
- `/tmp/<domain>_urls.txt` holds the full discovery list, one URL per line.

1. Shrink the list by pattern: keep one language, drop app routes and API reference. No judgment, pure matching.
2. Read every remaining line in full, with the Read tool.
3. Write the kept URLs to `/tmp/<domain>_urls_culled.txt` yourself, and leave `/tmp/<domain>_urls.txt` untouched.

4. Confirm every kept URL appears in `/tmp/<domain>_urls.txt`.

   ```bash
   comm -23 <(sort /tmp/<domain>_urls_culled.txt) <(sort /tmp/<domain>_urls.txt)
   ```

5. Give the worker the go and name `/tmp/<domain>_urls_culled.txt` as the file to scrape.

### Step 3 — Funnel Report

1. Receive the worker's funnel report.

2. Tell the user the error count, "bei X URLs ging was schief", and nothing else.
