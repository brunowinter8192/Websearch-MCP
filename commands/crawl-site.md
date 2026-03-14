---
description: Crawl a website and save pages as Markdown files
argument-hint: [url]
---

## Input

URL: $ARGUMENTS

---

## Pipeline Flow

```
URL (from search_web or user)
 | explore_site.py (Strategy auto-detect + URL list)
 | User reviews URL samples for noise
 | grep -v filters noise patterns
 | crawl_site.py --url-file (batch crawl filtered URLs)
 | deduplicate + clean permalinks
output-dir/*.md (raw)
 | (optional) Sonnet worker
 | /rag:web-md-index (cleanup + chunk + embed)
indexed in RAG
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

## Phase 1: Explore

### Step 1: Resolve URL

If `$ARGUMENTS` contains a URL, use it. Otherwise ask user for the URL to crawl.

### Step 2: Ask for Output Directory

Ask user: "Where should the Markdown files be saved?"

Default: `~/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/<sitename>/`

### Step 3: Run Exploration

```bash
${CLAUDE_PLUGIN_ROOT}/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/explore_site.py \
  --url "$URL" \
  --strategy auto \
  --output "$OUTPUT_DIR/urls.txt" \
  > /tmp/explore_output.txt 2>&1
```

Note: If the plugin venv python does not exist, use `./venv/bin/python` (project venv) instead.

Redirect output to file, then show the summary lines and URL samples:

```bash
cat /tmp/explore_output.txt
```

### Phase 1 Report

```
PHASE 1: Explore
================
URL:       [url]
STRATEGY:  [sitemap/prefetch/bfs]
URLs:      [N] discovered
DURATION:  [X.X]s
URL FILE:  [path]
```

Show URL samples from the output so user can identify noise patterns.

---

**STOP** - User reviews URL samples and identifies noise patterns to filter.

---

## Phase 2: Review & Filter

### Step 1: Discuss Noise

Based on URL samples, discuss with user which patterns are noise. Examples:
- Language variants: `/java/`, `/dotnet/`, `/docs/` (without `/python/`)
- Test/CI pages: `/test-*`, `/ci-*`
- Non-content: `/search`, `/genindex`, `/community/`

### Step 2: Filter URL List

Apply user-approved filters:

```bash
grep -v -E "PATTERN1|PATTERN2" "$OUTPUT_DIR/urls.txt" > "$OUTPUT_DIR/urls_filtered.txt"
wc -l "$OUTPUT_DIR/urls_filtered.txt"
```

Show filtered count and a few samples from the filtered list.

### Phase 2 Report

```
PHASE 2: Filter
================
ORIGINAL:  [N] URLs
FILTERED:  [M] URLs
REMOVED:   [N-M] URLs
PATTERNS:  [list of excluded patterns]
FILE:      [filtered file path]
```

---

**STOP** - User confirms filtered list before crawling.

---

## Phase 3: Crawl

### Step 1: Run Crawler

```bash
${CLAUDE_PLUGIN_ROOT}/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/crawl_site.py \
  --url "$URL" \
  --url-file "$FILTERED_URL_FILE" \
  --output-dir "$OUTPUT_DIR" \
  > /tmp/crawl_output.txt 2>&1
```

### Step 2: Verify Output

```bash
grep -E "^(Reading|Loaded|Crawled|Unique|Done)" /tmp/crawl_output.txt
ls "$OUTPUT_DIR" | head -10
ls "$OUTPUT_DIR" | wc -l
```

### Phase 3 Report

```
PHASE 3: Crawl
==============
URL FILE:  [filtered file path]
OUTPUT:    [output-dir]
FILES:     [N] markdown files
STATUS:    [Success/Failed]
```

---

**STOP** - Report results. Then check if RAG plugin is available (see Phase 4).

---

## Phase 4: RAG Pipeline (auto-detect)

### Step 1: Check RAG Plugin

Check if the RAG plugin is active by looking for the `web-md-index` command:

```bash
ls ~/.claude/plugins/cache/brunowinter-plugins/rag/*/commands/web-md-index.md 2>/dev/null
```

- If found → RAG plugin is active. Ask user: "RAG Plugin erkannt. Soll ich /rag:web-md-index starten? (cleanup + chunk + embed)"
- If not found → Report: "RAG Plugin nicht installiert. Crawl abgeschlossen." → **STOP**

### Step 2: Run RAG Pipeline

If user confirms, invoke the skill directly:

```
Skill(skill="rag:web-md-index", args="$OUTPUT_DIR")
```

This runs the full RAG pipeline inline: cleanup (web-md-cleanup agent) → chunk → index.

### Phase 4 Report

```
PHASE 4: RAG Pipeline
======================
PLUGIN:    [detected / not found]
DIRECTORY: $OUTPUT_DIR
STATUS:    [Started / Skipped]
```

---

**STOP** - Pipeline complete.
