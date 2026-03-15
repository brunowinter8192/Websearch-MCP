---
description: Crawl a website and save pages as Markdown files
---

## Config

```
OUTPUT_DIR=~/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/searxng
DECISIONS_DIR=decisions/
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
Phase 1: Preparation
 | Step 1: Extract all URLs from decision files
 | Step 2: Show output directory + existing documents inventory
 | Step 3: Explore domains (explore_site.py per crawlable domain)
Phase 2: Assessment
 | Evaluate which URLs/patterns are relevant per domain
 | User confirms selection
Phase 3: Crawl
 | crawl_site.py per domain with filtered URL lists
 | Save as Markdown to $OUTPUT_DIR
Phase 4: Cleanup
 | Clean up crawled Markdown files (web-md-cleanup agent)
Phase 5: Indexing
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

## Phase 2: Assessment

### Step 1: Relevance Evaluation

For each explored domain, evaluate discovered URLs:
- Which URL patterns are relevant for our pipeline decisions?
- Which patterns are noise (language variants, non-content, duplicates)?

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

### Phase 2 Report

```
PHASE 2: Assessment
====================
[domain]: [N] relevant / [M] total
[domain]: [N] relevant / [M] total
TOTAL:    [N] URLs to crawl
```

---

**STOP** - User confirms filtered URL lists before crawling.

---

## Phase 3: Crawl

### Step 1: Run Crawler Per Domain

For each confirmed domain:

```bash
${CLAUDE_PLUGIN_ROOT}/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/crawl_site.py \
  --url "$DOMAIN_URL" \
  --url-file "/tmp/filtered_${DOMAIN}_urls.txt" \
  --output-dir "$OUTPUT_DIR" \
  > /tmp/crawl_${DOMAIN}_output.txt 2>&1
```

### Step 2: Verify Output

```bash
grep -E "^(Reading|Loaded|Crawled|Unique|Done)" /tmp/crawl_${DOMAIN}_output.txt
ls "$OUTPUT_DIR" | wc -l
```

### Phase 3 Report

```
PHASE 3: Crawl
==============
[domain]: [N] files crawled — [Success/Failed]
[domain]: [N] files crawled — [Success/Failed]
TOTAL:    [N] new markdown files
OUTPUT:   $OUTPUT_DIR
```

---

**STOP** - Report results before cleanup.

---

## Phase 4: Cleanup

### Step 1: Run Cleanup

Dispatch web-md-cleanup agent(s) on the newly crawled Markdown files.

For each domain batch, use the `web-md-cleanup` agent:

```
Agent(subagent_type="web-md-cleanup", prompt="Clean these markdown files in $OUTPUT_DIR matching pattern ${DOMAIN}__*")
```

### Step 2: Verify Cleanup

Spot-check a few cleaned files to ensure quality.

### Phase 4 Report

```
PHASE 4: Cleanup
=================
FILES CLEANED: [N]
QUALITY:       [spot-check summary]
```

---

**STOP** - Report cleanup results before indexing.

---

## Phase 5: Indexing

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

### Phase 5 Report

```
PHASE 5: Indexing
==================
PLUGIN:    [detected / not found]
DIRECTORY: $OUTPUT_DIR
STATUS:    [Indexed / Skipped]
```

---

**STOP** - Pipeline complete.
