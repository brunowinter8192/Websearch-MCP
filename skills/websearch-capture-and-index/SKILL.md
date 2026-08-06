---
name: websearch-capture-and-index
description:
---

# Capture-and-Index — Skill

Pipeline: Discovery → URL Selection → STOP (Opus cull) → Scrape → Cleanup → Index.

**/tmp files are written with a heredoc, never with Write.**
Every file this pipeline produces under `/tmp` — URL lists, discovery scripts, cleaner scripts — is written from Bash via a quoted heredoc (`cat > /tmp/x <<'EOF' … EOF`).

**Multiple domains = step-by-step across ALL of them, never domain-by-domain.**
Discover all → select all → ONE Step-3 stop covering all → scrape all → clean all → index once at the end. `rag-cli index` operates on the whole collection directory — indexing after domain 1 sweeps up domain 2's raw, uncleaned files as garbage. Index is the LAST action and runs exactly once.

**Scrape failures are reported in the Completion Report, never acted on mid-capture.**

## Step 1 — Discovery

Deliverable: `/tmp/<domain>_discovered_urls.txt` — one URL per line, maximum coverage of the target domain/section. Discovery scripts go to `/tmp`.

First (~30s): fetch the seed page HTML (plain HTTP, no browser). Check `/sitemap.xml` and `/sitemaps/sitemap-0.xml`, and grep for `<script id="__NEXT_DATA__">`. `robots.txt` is NOT consulted. Then pick a path:

### Path A — `__NEXT_DATA__` extraction (Next.js SSR, preferred)

No browser needed. Parse the `__NEXT_DATA__` JSON blob from the seed page; walk fields with `childPages`/`items`/`navigation` keys paired with `href`/`url` strings — that is the nav tree (key path is site-specific, discover by inspection). Collect the primary nav's URLs, then for EACH entry in an `allVersions`-style version list: fetch that version's root, extract its nav, normalize version-prefixed URLs to canonical form (`/de/enterprise-cloud@latest/rest/X` → `/de/rest/X`), union in. Always include the OLDEST version. Write the normalized union.

**Sitemap-coverage trap:** if the site also has a sitemap, spot-check ≥5 known pages against it before trusting it as an alternative.

### Path B — Sitemap (sitemap exists and spot-check confirms coverage)

Fetch and parse the sitemap; filter to target section URLs; write the list.

### Path C — Playwright BFS (fallback)

Write a /tmp BFS script using `crawler.arun()` per frontier URL; extract `result.links.internal` from the rendered DOM.

```python
wait_until = "domcontentloaded"
delay_before_return_html = 3.0   # the one genuine time↔completeness dial
page_timeout = 15000             # load ceiling; does NOT add to delay
concurrency = 1                  # WAF-safe default
```

429 policy: back off 5s once; second consecutive 429 batch → stop, report `stop_reason="429_persistent"`. No retry loops. `stop_reason="frontier_exhausted"` = all link-reachable pages found.

## Step 2 — URL Selection (pre-scrape)

The cull happens on the URL LIST, before any scraping. Inspect the list, drop obvious noise (changelog/archive/legal/asset paths, known-dead sections) via a `/tmp` script that rewrites the file. Record dropped patterns + why for the Completion Report. No page content exists yet — this is purely list-level pattern selection.

## Step 3 — Opus Cull Review (MANDATORY STOP)

The list still contains valid-but-possibly-irrelevant pages. Do NOT edit the list for relevance — STOP and report to Opus:

- the URL-list path and total count
- a **per-section breakdown**: URLs grouped by first path segment, with counts — e.g. `rest/actions: 41 · rest/repos: 28 · …`

Then WAIT. Opus edits the file itself. On go, re-read the file and proceed — do NOT modify the list yourself.

**Pre-scrape line-count gate (MANDATORY).** In a Bash call of its OWN — never chained onto the scrape command (chaining defeats auto-backgrounding) — `wc -l` the URL file and compare against the count Opus gave with the go. Mismatch → STOP and report; do not scrape.

## Step 4 — Scrape

Scrape every URL in the filtered list **raw and maximal** — no content filter, no truncation.

```bash
mkdir -p $OUTPUT_DIR
WEBSEARCH=/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch
cd "$WEBSEARCH" && ./venv/bin/python -m src.crawler.pipe_scraper \
    --url-file /tmp/<domain>_discovered_urls.txt \
    --output-dir $OUTPUT_DIR > /tmp/<domain>_scrape.log 2>&1
```

**Engine choice (`--engine {chromium,camoufox}`, default chromium).**
Per-RUN choice. Camoufox passes WAFs chromium doesn't, but launches a fresh browser per URL at concurrency 1 — MUCH slower at volume. Use it only when the run was spawned with that instruction; a heavy anti-bot error pattern goes into the Completion Report, a re-run on the other engine only on Opus's say-so. A camoufox record may carry raw HTML instead of markdown (`content_is_raw_html` in the pipe log) — such files flow through Cleanup like any other.

> You own Scrape → Cleanup → Index end-to-end — never hand back to Opus mid-pipeline. When the run returns, read `/tmp/<domain>_scrape.log` ONCE for the summary line, then continue on your own.

The scraper prints one console line (success count, error count, duration) and writes a per-URL report to `/tmp/<domain>_scrape_report.md` — failures live there, not on the console. When errors > 0, write the failed URLs (one per line) to `/tmp/<domain>_error_urls.txt` — the Completion Report links this file.

## Step 5 — Cleanup

Diagnose first. Don't write cleanup regex before classifying shape.

### Diagnose pass

One small script (~50 LOC) scanning ALL `.md` files in OUTPUT_DIR: per-file fingerprints (h1/h2 count, prose density, table presence, source domain from the `<!-- source: URL -->` comment, LOC), clustered into 4-5 shape groups.

In the same pass, match each file against a BROAD block-signature list (case-insensitive substrings, extend freely):

```
cookie/consent : "accept cookies", "we use cookies", "cookie policy", "consent", "gdpr", "manage preferences"
paywall/sub    : "subscribe to", "sign in to continue", "members only", "create a free account", "register to read"
js/bot wall    : "enable javascript", "javascript is required", "verify you are human", "captcha", "checking your browser", "access denied"
```

A CANDIDATE = signature match AND small (thin-page byte range). The script prints each candidate's source URL + first ~15 lines — confirm real-block vs false-positive from that output. Candidate set in the dozens → STOP and report to Opus. A confirmed block page is garbage → **DELETE it**, no content-stripping.

Also delete **thin successful pages** (HTTP 200, tiny byte size — stubs, redirect landings, pure nav). Re-read only the small files, not every page.

### The five shapes

1. **Blog** — one h1 in first 20%, prose-heavy, footer markers. Strip pre-h1 chrome + footer from earliest tail-marker; keep source comment, title, metadata, ToC, body.
2. **Paper landing** — academic title, authors, abstract, metadata table. Strip nav/sidebar/license footer; keep title, authors, abstract, subject table, DOI. ACL Anthology: anchor on first `## ` h2 (no h1).
3. **Forum thread** — markdown-table layout. Site-specific (HN: anchor on first `vote?id=` link, strip before). Keep story row + comments.
4. **Repo heavy chrome** — >100 lines pre-content chrome, real title late. GitHub issue/PR: find `^# .+ #<N>` (N from URL), strip before. Repo home: anchor on README's first h1.
5. **Index/aggregator** — mostly link list, no prose. Flag low-content; optionally skip from indexing.

### Sphinx documentation

Header: `### Navigation` block + `»` breadcrumbs — strip everything between `<!-- source:` line and first `# ` heading.
Footer: logo image line `[ ![Logo of ...](...) ](...)` is the content-end marker — strip from `^\[ !\[Logo of ` to EOF (covers `### [Table of Contents]`, `### Project Links`, `### Quick search`, `© Copyright`).
Inline (`_modules_*` files only): strip `\[docs\]\[]\(https://[^)]*\)`.

### Cleaner scripts

One small script per detected shape in `/tmp/clean_<shape>_<COLLECTION_lower>.py` (~20-30 LOC each) — NOT one big function with N patterns.

Safety rules (CRITICAL):

- Every `while` loop MUST increment in ALL code paths
- Test on 1 file FIRST, then run on all
- ALWAYS `python3` (not `python`)
- `Path(__file__).parent` — NEVER hardcode absolute paths
- Preserve `<!-- source: URL -->` comments in every file
- Overwrite originals in-place
- After cleaning, spot-check 2-3 files

Edge cases: no `# ` heading (redirect pages) → keep content between source comment and logo line. Nearly empty after cleanup (<5 lines) → still output, don't delete. `user_None.md`/`user_{}.md` = crawled error pages, minimal content expected.

## Step 6 — Index (final)

One call, once per run, AFTER all domains are scraped and cleaned — `rag-cli index` indexes the ENTIRE collection directory, incrementally (hash-based skip).

**OUTPUT_DIR must be the collection dir** — set BEFORE Step 4:

```bash
RAG_ROOT=~/Documents/ai/Meta/ClaudeCode/cli/rag-cli
OUTPUT_DIR="$RAG_ROOT/data/documents/$COLLECTION"
mkdir -p "$OUTPUT_DIR"
```

```bash
PYTHONUNBUFFERED=1 rag-cli index --collection "$COLLECTION" \
    > /tmp/${COLLECTION}_index.log 2>&1
```

When the run returns, read the log ONCE for the summary line (`Done: N files indexed (X chunks), …`) — `N` is the final-md count for the Completion Report.

## Completion Report

Output back to Opus when done — the funnel:

```
URLs discovered:                    N
URLs dropped (pre-scrape, pattern): K    — which patterns + why
URLs scraped:                       N − K
Scrape:                             M ok, E errors   ·   duration: T
Final md indexed:                   <count>
Collection:                         <COLLECTION>
Error URLs:                         /tmp/<domain>_error_urls.txt   (one URL per line; omit the line when E = 0)
```

End with this report. STOP. No commit needed (output is data files, not code).
