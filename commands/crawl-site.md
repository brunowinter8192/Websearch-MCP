---
description: Crawl a website and save pages as Markdown files
---

## Config

```
OUTPUT_DIR=~/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/searxng
```

## Plugin Domains (SKIP — handled by dedicated MCP plugins)

These domains are NEVER crawled. They have their own plugins:
- `github.com` → github-research plugin
- `reddit.com` → reddit plugin
- `arxiv.org` → arxiv plugin
- `huggingface.co` → separate project

If a decision file references these domains, note them as "Plugin-Domain (SKIP)" in the inventory.

---

## Pipeline Flow

```
Phase 1: URL Input
 | Ask user which URLs/domains to crawl
 | Check against Plugin-Domain skip list
Phase 2: Explore
 | Run explore_site.py per domain (parallel)
 | Show URL counts + samples per domain
Phase 3: Assessment
 | Evaluate which URL patterns are relevant vs noise
 | Filter URL lists, user confirms
Phase 4: Crawl
 | crawl_site.py per domain with filtered URL lists
 | Garbage detection + removal
Phase 5: Cleanup
 | Clean up crawled Markdown files (web-md-cleanup agent)
Phase 6: Indexing
 | Ask user if ready to index into RAG
 | /rag:web-md-index (chunk + embed)
```

---

## Step Indicator Rule

**MANDATORY:** Every response MUST start with: `Phase X, Step Y: [Name]`

---

## STOP Point Rule

**CRITICAL:** After each phase, there is a `**STOP**` marker.

- **STOP = END OF RESPONSE.** Do not continue to next phase.
- Wait for user to say "weiter", "proceed", "go", etc.
- NEVER batch multiple phases in one response

---

## Phase 1: URL Input

Ask user: "Welche URLs/Domains sollen gecrawlt werden?"

User provides one or more URLs. These can be:
- A single URL (e.g., `https://docs.crawl4ai.com`)
- Multiple URLs
- A domain name to explore

Check provided URLs against Plugin-Domain skip list. If a Plugin-Domain is provided, inform user and skip it.

### Phase 1 Report

List the confirmed URLs to process.

---

**STOP** - User confirms URL list.

---

## Phase 2: Explore

### Step 1: Run Exploration Per Domain

For each confirmed URL, run explore_site.py (parallel for multiple domains):

```bash
${CLAUDE_PLUGIN_ROOT}/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/explore_site.py \
  --url "$DOMAIN_URL" \
  --strategy auto \
  --output "/tmp/explore_${DOMAIN_NAME}_urls.txt" \
  > /tmp/explore_${DOMAIN_NAME}_output.txt 2>&1
```

Note: If the plugin venv python does not exist, use `./venv/bin/python` (project venv) instead.

### Step 2: Show Results

Show summary per domain: strategy used, URLs discovered, URL samples.

### Phase 2 Report

```
PHASE 2: Explore
=================
[domain]: [strategy] — [N] URLs discovered
[domain]: [strategy] — [N] URLs discovered
TOTAL:    [N] URLs across [M] domains
```

---

**STOP** - User reviews exploration results before assessment.

---

## Phase 3: Assessment

### Step 1: Relevance Evaluation

For each explored domain, evaluate discovered URLs:
- Which URL patterns are relevant?
- Which patterns are noise (language variants, non-content, duplicates, login pages)?

Present per domain:
```
DOMAIN: [domain]
RELEVANT PATTERNS: [list with examples]
NOISE PATTERNS:    [list with examples]
KEEP: [N] URLs
SKIP: [M] URLs
```

### Step 2: Filter URL Lists

Apply filters per domain:

```bash
grep -v -E "NOISE_PATTERN" "/tmp/explore_${DOMAIN}_urls.txt" > "/tmp/filtered_${DOMAIN}_urls.txt"
wc -l "/tmp/filtered_${DOMAIN}_urls.txt"
```

### Phase 3 Report

```
PHASE 3: Assessment
====================
[domain]: [N] relevant / [M] total
[domain]: [N] relevant / [M] total
TOTAL:    [N] URLs to crawl
```

---

**STOP** - User confirms filtered URL lists before crawling.

---

## Phase 4: Crawl

### Step 1: Run Crawler Per Domain

For each confirmed domain (parallel):

```bash
${CLAUDE_PLUGIN_ROOT}/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/crawl_site.py \
  --url "$DOMAIN_URL" \
  --url-file "/tmp/filtered_${DOMAIN}_urls.txt" \
  --output-dir "$OUTPUT_DIR" \
  > /tmp/crawl_${DOMAIN}_output.txt 2>&1
```

### Step 2: Verify Output + Garbage Detection

```bash
grep -E "^(Reading|Loaded|Crawled|Unique|Done)" /tmp/crawl_${DOMAIN}_output.txt
ls "$OUTPUT_DIR" | wc -l
```

**Garbage Detection:** After crawl, find and remove garbage files:

```bash
find "$OUTPUT_DIR" -name "*.md" -size -2k -type f | while read f; do
  if grep -qiE "(page not found|not available|unfortunately we couldn)" "$f" 2>/dev/null; then
    rm "$f"
    echo "REMOVED: $(basename $f)"
  fi
done
```

Common garbage patterns: "Page not found", "This page is not available for Python", "Unfortunately we couldn't find the content".

### Step 3: Verify File Counts

```bash
ls "$OUTPUT_DIR" | sed 's/__.*//' | sort | uniq -c | sort -rn
```

### Phase 4 Report

```
PHASE 4: Crawl
==============
[domain]: [N] files crawled — [Success/Failed]
[domain]: [N] files crawled — [Success/Failed]
GARBAGE:  [N] files removed
TOTAL:    [N] clean markdown files
OUTPUT:   $OUTPUT_DIR
```

---

**STOP** - Report results before cleanup.

---

## Phase 5: Cleanup

### Step 1: Run Cleanup — Parallel Agents Per Domain

Dispatch one `web-md-cleanup` agent per domain prefix, all in parallel via `run_in_background: true`.

**Grouping rules:**
- Large domains (>50 files): one agent each
- Small domains (<50 files): group 2-3 into one agent
- Skip domains that don't need web cleanup: `paper__` (PDF-converted), `web__` (individually scraped)

**Dispatch all agents in a single message** (parallel tool calls):

```
Agent(subagent_type="web-md-cleanup", run_in_background=true, prompt="
Clean up website-crawled markdown files.
INPUT DIRECTORY: $OUTPUT_DIR
FILE PATTERN: ${DOMAIN}__*.md ([N] files)
These are [site description] pages crawled via Crawl4AI.
Remove navigation, footer, sidebar, breadcrumbs, and other UI chrome.
Preserve content and <!-- source: URL --> headers.
Sample 3-5 files first to identify common patterns,
then build a cleanup script that processes all matching files.
")
```

Each agent will:
1. Sample files to identify site-specific chrome patterns
2. Create cleanup script in `dev/cleanup/`
3. Run script on all matching files
4. Report patterns found and char reduction

### Step 2: Verify Cleanup (after all agents complete)

**CRITICAL:** Never trust subagent output. Verify independently.

1. **Spot-check per domain:** Read first 20 lines of 1-2 cleaned files per domain. Should start with content, not navigation.
2. **Source comments preserved:** `grep -l "<!-- source:" "$OUTPUT_DIR"/${DOMAIN}__*.md | wc -l` should equal file count per domain.
3. **Char reduction:** Compare total chars before/after per domain. 10-50% reduction expected. >60% = possible content loss.

### Phase 5 Report

```
PHASE 5: Cleanup
=================
[domain]: [N] files — [X%] reduction — [Success/Failed]
[domain]: [N] files — [X%] reduction — [Success/Failed]
TOTAL:    [N] files cleaned across [M] agents
```

---

**STOP** - Report cleanup results before indexing.

---

## Phase 6: Indexing

### Step 1: Ask User

"Alle Domains gecrawlt und aufgeraeumt. Soll ich jetzt in RAG indexieren? (chunk + embed)"

### Step 2: Check RAG Plugin

```bash
ls ~/.claude/plugins/cache/brunowinter-plugins/rag/*/commands/web-md-index.md 2>/dev/null
```

- If not found → "RAG Plugin nicht installiert. Crawl abgeschlossen."

### Step 3: Run RAG Pipeline

If user confirms:

```
Skill(skill="rag:web-md-index", args="$OUTPUT_DIR")
```

### Phase 6 Report

```
PHASE 6: Indexing
==================
PLUGIN:    [detected / not found]
DIRECTORY: $OUTPUT_DIR
STATUS:    [Indexed / Skipped]
```

---

**STOP** - Pipeline complete.
