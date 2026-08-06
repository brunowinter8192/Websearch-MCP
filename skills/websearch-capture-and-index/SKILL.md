---
name: websearch-capture-and-index
description:
---

# Capture-and-Index — Skill

## /tmp files are written with a heredoc, never with Write

Every file this pipeline produces under `/tmp` — URL lists, discovery scripts, cleaner scripts — is written from Bash via a quoted heredoc (`cat > /tmp/x <<'EOF' … EOF`). The Write tool is for repo files; a throwaway under `/tmp` is a shell artifact and stays in the shell. Quote the delimiter (`<<'EOF'`) so nothing in the body gets expanded.

### Web-MD Capture (discovery → select → scrape → clean → index)

Pipeline: Discovery → URL Selection (pre-scrape) → Scrape (raw) → Cleanup (incl. post-scrape drop) → Index.

**Multiple domains = step-by-step across ALL of them, never domain-by-domain.**
Given N seed domains, run every step to completion for all N before entering the next step: discover all → select all → ONE Step-3 stop covering all → scrape all → clean all → index once at the end. `rag-cli index` operates on the whole collection directory, not on single files — indexing after domain 1 sweeps up domain 2's raw, uncleaned files and indexes them as garbage. Index is therefore the LAST action of the entire run and runs exactly once.

**Scraper posture — best-effort, not guaranteed.** `src/crawler/pipe_scraper.py` is a GENERAL scraper; do NOT assume the scrape worked. Coverage verification is a first-class duty: every discovered URL that survives the cull must actually yield real content.

**A reachability problem is REPORTED, never acted on.** The scraper runs ONE fixed calibration; it exposes no stealth, wait-strategy or per-domain lever — tuning happens in a separate session, never mid-capture. On any scrape failure pattern: do NOT stop, do NOT re-run, do NOT vary the config. Capture what does come through, carry it to Index, and let the error count + error-URL file in the Completion Report speak. A partial capture that is honestly reported beats a halted one.

#### Step 1 — Discovery

Deliverable: `/tmp/<domain>_discovered_urls.txt` — one URL per line, maximum coverage of the target domain/section.

Write your discovery scripts to `/tmp` — no pinned reference script. Choose the path below based on structural signals from the seed page. **Any errors during discovery (HTTP failures, 429s, blocked fetches) MUST be recorded for the Completion Report.**

##### Step 0 — Structural Signals (always, ~30s)

Fetch the seed page HTML (plain HTTP, no browser). Check:

- `/sitemap.xml` and `/sitemaps/sitemap-0.xml` — does one exist?
- `<script id="__NEXT_DATA__">` in the raw HTML — signals Next.js SSR (see Path A).

`robots.txt` is NOT consulted.

##### Path A — `__NEXT_DATA__` Extraction (Next.js SSR sites, preferred)

Applicable when: `<script id="__NEXT_DATA__">` found in seed HTML.

No browser needed.

**Procedure:**

1. Parse the `__NEXT_DATA__` JSON blob from the seed page.
2. Walk any field containing `childPages`, `items`, or `navigation` keys paired with `href` or `url` strings — that is the nav tree. Key path is site-specific — discover by inspection (grep the blob for fields containing `childPages`/`href` pairs; do NOT assume `props.pageProps.mainContext.sidebarTree`).
3. Collect all URL strings matching the target section/domain from the primary nav (latest / free-pro-team / main version).
4. Check for an `allVersions`, `versions`, or equivalent version-list field in the blob. For EACH version:
   - Construct the version-scoped root URL.
   - Fetch it via plain HTTP.
   - Extract its nav tree (same walk logic).
   - Normalize version-prefixed URLs to canonical form (strip the version segment: `/de/enterprise-cloud@latest/rest/X` → `/de/rest/X`).
   - Union into the main set.
5. **Always check the OLDEST version** (same walk: construct its root URL, extract nav, union in).
6. Write the normalized union to `/tmp/<domain>_discovered_urls.txt`.

**Expected outcome:** 100% of pages appearing in ANY version's sidebar, in ~1–5s.

**Sitemap-coverage trap:** if the site also exposes a sitemap, verify it covers the target section (spot-check ≥5 known pages against the sitemap) before trusting it as an alternative.

##### Path B — Sitemap (non-Next.js, sitemap exists and is verified)

Applicable when: sitemap found AND spot-check confirms it covers the target section adequately.

Fetch and parse the sitemap; filter to target section URLs; write to `/tmp/<domain>_discovered_urls.txt`.

##### Path C — Playwright BFS (fallback — no `__NEXT_DATA__`, no usable sitemap)

Applicable when: neither Path A nor Path B applies.

Write a /tmp BFS script using `crawler.arun()` per frontier URL; extract `result.links.internal` from the fully rendered DOM. Config:

```python
wait_until = "domcontentloaded"
delay_before_return_html = 3.0   # the one genuine time↔completeness dial
page_timeout = 15000             # load ceiling; does NOT add to delay
concurrency = 1                  # WAF-safe default
```

429 policy: back off 5s once; stop if second consecutive batch also 429 — report `stop_reason="429_persistent"`. No retry loops.

`stop_reason="frontier_exhausted"` means all link-reachable pages were found.

Write discovered URLs to `/tmp/<domain>_discovered_urls.txt`.

#### Step 2 — URL Selection (pre-scrape)

The cull happens on the URL LIST, before any scraping — not by reading scraped `.md` files. Inspect `/tmp/<domain>_discovered_urls.txt`, decide which URLs are obvious noise (e.g. changelog/archive/legal/asset paths, known-dead sections), and write a `/tmp` script that rewrites the list so only the URLs worth scraping remain.

Record which patterns were dropped and why — this goes into the Completion Report (`URLs dropped (pre-scrape, pattern): K — patterns + why`).

Do NOT read page content here; that is impossible pre-scrape. This step is purely list-level pattern selection.

#### Step 3 — Opus Cull Review (MANDATORY STOP)

After the pattern-noise cull, the list still contains pages that are valid content but may be **irrelevant to what the user actually needs**. Do NOT edit the list for relevance; present it, and **Opus edits the `/tmp` file directly**.

STOP here. Report to Opus:
- the URL-list path (`/tmp/<domain>_discovered_urls.txt`) and total count
- a **per-section breakdown**: group URLs by their first path segment under the target root, with counts — e.g. `rest/actions: 41 · rest/repos: 28 · rest/enterprise-admin: 35 · …`

Then WAIT. Opus strips the unwanted URLs from `/tmp/<domain>_discovered_urls.txt` itself. When Opus says go, re-read the now-shorter file and proceed to Step 4 — do NOT modify the list yourself.

Do NOT scrape before Opus says go.

**Pre-scrape line-count gate (MANDATORY).** In a Bash call of its OWN — never chained onto the scrape command — run `wc -l` on the URL file and compare it against the count Opus gave with the go. Mismatch → STOP and report to Opus; do not scrape. A stale or un-culled list otherwise burns a full scrape run against hundreds of unwanted URLs and is only noticed afterwards. Keep it a separate call: anything chained onto the scrape command defeats auto-backgrounding.

#### Step 4 — Scrape

Scrape every URL in the filtered list **raw and maximal** — no content filter, no truncation.

```bash
mkdir -p $OUTPUT_DIR
```

Run the pipe-scraper via the absolute source path:

```bash
WEBSEARCH=/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch
cd "$WEBSEARCH" && ./venv/bin/python -m src.crawler.pipe_scraper \
    --url-file /tmp/<domain>_discovered_urls.txt \
    --output-dir $OUTPUT_DIR > /tmp/<domain>_scrape.log 2>&1
```

**Engine choice (`--engine {chromium,camoufox}`, default chromium):** a per-RUN choice, OPTIONAL — no reliability data yet favors either engine per site type. Default (omit the flag) is the chromium/crawl4ai engine. `--engine camoufox` runs the Camoufox lane (Playwright-Firefox, fingerprint spoofing) — measured to pass Akamai Bot Manager where chromium gets a block page, but launches a fresh browser per URL and serializes per domain (concurrency default 1 vs chromium's 8), so it is MUCH slower at volume. Use it only when the run is spawned with that instruction; a heavy anti-bot error pattern in a chromium run goes into the Completion Report, and a re-run on the other engine happens only if Opus says so. A camoufox record may carry raw HTML instead of markdown (`content_is_raw_html` in the pipe log) — such files still index but flow through Cleanup like any other.

> You own Scrape → Cleanup → Index end-to-end — never hand back to Opus mid-pipeline. When the run returns, read `/tmp/<domain>_scrape.log` ONCE for the `Scraped N/N ok` summary, then continue on your own to Cleanup → Index → final report.

The scraper's own output is short: a console line with **success count, error count, and total duration**, plus a full per-URL report written to `/tmp/<domain>_scrape_report.md` (per-URL status + outcome). It does NOT dump a per-URL list to the console — failures live in the report md.

Take from that console line for the Completion Report: scraped N, errors K, **duration T**. When E > 0, write the failed URLs (one per line) to `/tmp/<domain>_error_urls.txt` — the Completion Report links this file.

#### Step 5 — Cleanup

Diagnose first. Don't write cleanup regex before classifying shape.

##### Diagnose Pass

Build a small script that scans ALL `.md` files in OUTPUT_DIR, extracts per-file fingerprints (h1 count, h2 count, prose density, table presence, source domain from `<!-- source: URL -->` comment, total LOC). Cluster by fingerprint similarity to identify 4-5 shape groups. ~50 LOC, ~5s runtime.

**Fold in — Block Detection (cookie / paywall / JS-wall / captcha).** In the same diagnose pass, ALSO match each file against a BROAD, high-recall block-signature list (case-insensitive substring set, extend freely):

```
cookie/consent : "accept cookies", "we use cookies", "cookie policy", "consent", "gdpr", "manage preferences"
paywall/sub    : "subscribe to", "sign in to continue", "members only", "create a free account", "register to read"
js/bot wall    : "enable javascript", "javascript is required", "verify you are human", "captcha", "checking your browser", "access denied"
```

A file is a CANDIDATE when it matches a signature AND is small (byte-size in the thin-page range). For every candidate, the diagnose script PRINTS its `<!-- source -->` URL + first ~15 lines into its own output — confirm real-block vs false-positive from that output. If the candidate set is large (dozens+) → STOP and report to Opus.

A confirmed block page is garbage → **DELETE it** (same as a thin page) — no content-stripping. REPORT the confirmed-block count + example URLs in the Completion Report.

##### Post-Scrape Drop — thin successful pages (part of the diagnose pass)

Scrape gaps (429 / timeout / http_error) are already reported by the scraper. The only thing to analyse here are the **successful but very small** `.md` files (HTTP 200, tiny byte size): pages that scraped fine but carry little or no real content (stub, redirect landing, pure nav).

Delete those. Record the count for the Completion Report. Re-read only the small successful files, not every page.

The two numbers stay separate in the report: scrape errors come from the scraper, thin/noise comes from this check.

##### The Five Shapes

1. **Blog-Shape** — one h1 in first 20%, prose-heavy, h2 sections, footer markers (Continue reading / Comments / Copyright / breadcrumb).
   - Strip pre-h1 chrome + footer from earliest tail-marker.
   - Keep: source comment, h1 title, posted/updated metadata, ToC, body content.

2. **Paper-Landing-Shape** — academic title h1/h2, author list, abstract, metadata table (Subjects, DOI). Short overall.
   - Strip site nav, sidebar forms, "View PDF/HTML" link clusters, license footer.
   - Keep title, authors, abstract, subject table, DOI.
   - Variant: ACL Anthology uses `## [Title]` not `# Title` — anchor on first `## ` h2 if no h1.

3. **Forum-Thread-Shape** — markdown-table layout, top-nav row, story/comment rows.
   - Site-specific (HN: anchor on first `vote?id=` link, strip everything before).
   - Keep story title row + comment threads. Markdown-table syntax stays.

4. **Repo-Heavy-Chrome-Shape** — very long pre-content chrome (>100 lines), many h1 chrome lines (search box, feedback, sponsor, repo headers), real title appears late.
   - GitHub issue/PR: extract `#<N>` from URL, find `^# .+ #<N>` line, strip everything before.
   - GitHub repo home: anchor on README's first h1 or file-tree end-marker.

5. **Index-Aggregator-Shape** — page is mostly link list, no real prose. Wikipedia category pages, blog index pages, doc TOC pages.
   - Flag as low-content. Optionally exclude from indexing (skip the file).

##### Web-Specific: Sphinx Documentation

Sphinx-generated docs (SearXNG, ReadTheDocs, many Python project docs) have a distinctive pattern.

Header (top of file, before first `# ` heading):
- `### Navigation` block with index/modules/next/previous links
- Breadcrumb trail with `»` separators
- Strip: everything between `<!-- source:` line and first `# ` heading

Footer (after last content line):
- Logo image line: `[ ![Logo of ...](...) ](...)` — content-end marker
- `### [Table of Contents]`, `### Project Links`, second `### Navigation`, `### Quick search`, `### This Page`, `© Copyright`
- Strip: everything from `^\[ !\[Logo of ` to EOF

Inline noise (`_modules_*` files only): `[docs][](URL)` markers before class/function defs. Regex: `\[docs\]\[]\(https://[^)]*\)`.

##### Per-Shape Cleaner Pattern

For each detected shape, write ONE small script in `/tmp/clean_<shape>_<COLLECTION_lower>.py` (~20-30 LOC each). NOT one big function with N patterns.

##### Script Safety Rules (CRITICAL)

- Every `while` loop MUST increment in ALL code paths (skip/continue/break/normal — all)
- Test on 1 file FIRST, then run on all
- ALWAYS `python3` (not `python`)
- Use `Path(__file__).parent` — NEVER hardcode absolute paths like `/Users/...`
- Preserve `<!-- source: URL -->` comments in every file
- Overwrite originals in-place
- After cleaning, spot-check 2-3 files

##### Edge Cases

- Files with no `# ` heading (auto-generated redirect pages) → keep content between source comment and logo line
- Files nearly empty after cleanup (<5 lines) → still output, don't delete
- `user_None.md` / `user_{}.md` files = crawled error pages, minimal content expected

---

### Step 6 — Index (final, web-md)

One script call, once per run. `rag-cli index` is incremental (hash-based skip) — re-running only embeds new/changed files. It indexes the ENTIRE collection directory, so every file in it must be cleaned before this runs — with multiple domains that means all domains scraped AND cleaned first.

**Important — OUTPUT_DIR must be the collection dir.** Set `OUTPUT_DIR` to the rag-cli collection directory:

```bash
RAG_ROOT=~/Documents/ai/Meta/ClaudeCode/cli/rag-cli
OUTPUT_DIR="$RAG_ROOT/data/documents/$COLLECTION"
mkdir -p "$OUTPUT_DIR"
```

Set this BEFORE the Scrape step (Step 4).

Then run the index:

```bash
PYTHONUNBUFFERED=1 rag-cli index --collection "$COLLECTION" \
    > /tmp/${COLLECTION}_index.log 2>&1
```

The script prints per file `Indexed <doc> -> N chunks` and a final summary line:

```
Done: N files indexed (X chunks), Y skipped, Z adopted
```

Report `N` (files indexed) and `X` (chunks) from that line — `N` is the **final md** count for the Completion Report. When the run returns, read `/tmp/${COLLECTION}_index.log` ONCE for the summary line, then output the Completion Report.

No separate verify step inside the pipe.

---

### Completion Report

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
