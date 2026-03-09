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
 | crawl_site.py (Crawl4AI BFS)
 | deduplicate + clean permalinks
output-dir/*.md (raw)
 | Sonnet worker (tmux_spawn.sh)
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

## Phase 1: Confirm Parameters

### Step 1: Resolve URL

If `$ARGUMENTS` contains a URL, use it. Otherwise ask user for the URL to crawl.

### Step 2: Ask for Output Directory

Ask user: "Where should the Markdown files be saved?"

### Step 3: Confirm Crawl Settings

Present parameters and ask for confirmation:

```
URL:        [url]
Output Dir: [path]
Depth:      3 (default)
Max Pages:  100 (default)
```

Ask: "Start crawl with these settings? Adjust depth/max-pages if needed."

---

**STOP** - Wait for user confirmation before crawling.

---

## Phase 2: Crawl

### Step 1: Run Crawler

```bash
${CLAUDE_PLUGIN_ROOT}/.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/crawl_site.py \
  --url "$URL" \
  --output-dir "$OUTPUT_DIR" \
  --depth $DEPTH \
  --max-pages $MAX_PAGES
```

**Note:** Crawling can take several minutes depending on site size and depth.

### Step 2: Verify Output

```bash
ls -la "$OUTPUT_DIR"
wc -l "$OUTPUT_DIR"/*.md | tail -1
```

### Phase 2 Report

```
PHASE 2: Crawl
==============
URL:     [url]
OUTPUT:  [output-dir]
FILES:   [N] markdown files
STATUS:  [Success/Failed]
```

---

**STOP** - Report results. Ask: "Spawn Sonnet worker for RAG pipeline? (requires RAG plugin with `web-md-index` command)"

---

## Phase 3: RAG Pipeline (Sonnet Worker)

**Prerequisite:** RAG plugin must be installed with the `web-md-index` command available.

### Step 1: Spawn Worker

```bash
source ${CLAUDE_PLUGIN_ROOT}/src/spawn/tmux_spawn.sh

TASK="/rag:web-md-index $OUTPUT_DIR"

spawn_claude_worker "workers" "web-cleanup" "$PWD" "sonnet" "$TASK"
```

### Step 2: Report

```
PHASE 3: RAG Worker
====================
TMUX SESSION: workers
TMUX WINDOW:  web-cleanup
MODEL:        sonnet
COMMAND:      /rag:web-md-index $OUTPUT_DIR
STATUS:       Spawned
```

Inform user: "Worker spawned. Ghostty window should open. The worker runs the full RAG pipeline: cleanup (web-md-cleanup agent) -> chunk -> index."

---

**STOP** - Pipeline complete. Crawl finished, RAG worker spawned.
