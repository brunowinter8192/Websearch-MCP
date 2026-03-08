# Evaluation Report — Agent ac85e3faa825da65a

**Agent:** github-research:github-search
**Date:** 2026-03-08 22:27
**Size:** 120KB | 10 tool calls
**Model:** Haiku

---

## Session Overview

**Task:** Research the major web crawling/scraping frameworks on GitHub. Previous search was too narrow.

**Dispatch:** 10 specific `search_repos` queries provided, all with `sort_by: stars`. Agent instructed to report repos with 1000+ stars in FILE/VALUE/EVIDENCE format.

**Result:** Agent executed all 10 queries and returned a well-organized, comprehensive landscape report with tier classification.

---

## What Went Well

**1. Full task execution without deviation**
- All 10 queries executed exactly as instructed
- Correct `sort_by: stars` parameter throughout
- No hallucinated repos — all output grounded in actual API results

**Why it matters:** A haiku agent that executes 10 targeted searches reliably and returns structured output is the correct behavior. The agent didn't invent repos, didn't deviate from instructions, didn't return a "plan."

**2. Excellent synthesis in final response**
- Results organized into tiers (Tier 1–5) by star count
- Duplicate repos across searches were collapsed into a single entry
- Ecosystem patterns section added genuine analytical value beyond raw search output

**Why it matters:** The dispatcher asked for FILE/VALUE/EVIDENCE blocks; the agent returned that AND added cross-query synthesis (language distribution, approach taxonomy). This is value-add, not format drift that breaks downstream parsing.

**3. No path hallucinations**
- search_repos output is factual (API responses)
- No constructed paths, no invented repo names

---

## What Went Wrong

### Problem 1: All 10 searches ran sequentially

**What:** 10 independent `search_repos` calls were executed one by one, serially. No query depends on any other query's result — they are fully independent.

**Why (Root Cause):** The agent definition (`github-search.md`) has no instruction about parallel tool calls. The Search Strategy section describes "Start broad, then narrow down" — an inherently sequential pattern. When given 10 independent queries with no dependency chain, Haiku defaults to serial execution.

**Evidence:** Tool Call Summary table shows calls 1–10 with separate entries, sequential timestamps implicit from session flow. No multi-call grouping.

**Model-Specific Pattern (Haiku):** Haiku does not self-initiate parallel calls without explicit instruction. This is expected Haiku behavior — the agent needs to be told when parallelism is appropriate.

**Impact:** ~10x slower than necessary for this type of task. A batch of 5+5 parallel calls would halve execution time. At 10 sequential calls × ~2s each = ~20s vs 5+5 parallel = ~4s total.

---

### Problem 2: Dispatch did not instruct parallelization

**What:** The dispatch prompt listed 10 queries without saying "run them in parallel" or "batch these."

**Why (Root Cause):** The dispatcher SKILL.md (`skills/github/SKILL.md`) has no guidance on when to tell the subagent to parallelize. The dispatch templates ("Template (exploration)") show a sequential list format with no mention of batching.

**Evidence:** Task prompt:
```
Run these searches (SHORT queries, sort by stars to find the big repos):
1. search_repos: "web crawler python" sort by stars
2. search_repos: "web scraper python" sort by stars
...
```
No "run in parallel" instruction anywhere.

**Note on cost:** Dispatcher = Opus (costly), sub = Haiku (cheap). An Opus pre-check to determine if queries are parallelizable would cost more than the sequential haiku overhead. Better to add a blanket rule to the sub: "when given a numbered list of independent searches, run all in parallel."

---

### Problem 3: Redundant query in dispatch (minor)

**What:** Query 2 "web scraper python" returned largely the same repos as Query 1 "web crawler python." Top new unique finds: autoscraper (7k), which is minor. No Tier 1 repos were exclusively found by query 2.

**Why (Root Cause):** The dispatch was pre-scripted with 10 queries without adaptive pruning. Not an agent failure — a dispatch design issue.

**Impact:** 1 wasted tool call. Minor.

---

## Dispatch Quality

**Positive:**
- Task was precise: 10 specific queries, threshold (1000+ stars), output format (FILE/VALUE/EVIDENCE)
- Gave the agent everything it needed — no ambiguity about what to search or how to format

**Negative:**
- No parallelization instruction for independent queries (see Problem 1 & 2)
- Query redundancy (Problem 3) — could have been avoided with a dedup instruction like "skip a query if results overlap heavily with prior query"

---

## Root Cause Table

| Problem | Symptom | Root Cause | Automation File |
|---------|---------|------------|-----------------|
| Sequential execution of 10 independent searches | ~10x slower than needed | No parallel execution instruction in agent definition | `agents/github-search.md` |
| Dispatch did not trigger parallelism | Agent never instructed to batch | No parallelism guidance in dispatch templates | `skills/github/SKILL.md` |
| Redundant query 2 | 1 wasted call, near-zero unique results | No adaptive dedup rule in dispatch | `skills/github/SKILL.md` |

---

## Meta-Finding: eval.md Bug (Unrelated to Agent)

During execution of this eval, the following bug was discovered in `eval.md` (RAG plugin):

**Phase 2 command:**
```bash
$PLUGIN_DIR/venv/bin/python $PLUGIN_DIR/workflow.py index-json ...
```

**Problem:** `$PLUGIN_DIR` = plugin cache. The cache `indexer.py` uses `load_dotenv()` without a path. `load_dotenv()` searches CWD for `.env` — but when called from the searxng project dir, no `.env` with postgres credentials is found. Result: `FATAL: password authentication failed for user "rag"`.

**Fix:** Run using the actual RAG project's workflow.py:
```bash
cd $RAG_PROJECT && ./venv/bin/python workflow.py index-json --input "$PLUGIN_DIR/data/documents/Subagents/${AGENT_ID}.json"
```
Where `RAG_PROJECT=/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/RAG` (not the cache).

**Target file for fix:** `~/.claude/plugins/cache/brunowinter-plugins/rag/1.0.0/Prompts/eval.md` → source: RAG plugin repo.

---

## Proposals

### Proposal 1: Add parallel search instruction to agent definition

**File:** `/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/github/agents/github-search.md`
**Location:** `## Search Strategy` section, after the "Iterative Refinement" subsection

**WHY:** Haiku does not self-initiate parallel calls. When given a list of N independent queries (no result from query N needed for query N+1), it executes them serially by default. An explicit rule prevents this.

**Current:** No mention of parallel tool calls anywhere in the agent definition.

**Proposed — add this subsection after "Iterative Refinement":**

```markdown
### Parallel Execution (Independent Queries)

When given a numbered list of independent searches (e.g., "run these 10 queries"), run them in parallel — not sequentially.

**Independent = no result from query N is needed as input to query N+1.**

Batch them:
- 1–5 queries → run all in parallel in one message
- 6–10 queries → run as two parallel batches (5+5)
- 10+ queries → split into batches of 5, each batch in parallel

**Wrong (sequential):**
Call 1: search_repos("web crawler python")
Call 2: search_repos("web scraper python")  ← waits for Call 1 to finish

**Right (parallel):**
Single message with 5 parallel search_repos calls, then another batch of 5.
```

**Expected Impact:** 2–5x speedup for landscape research tasks. No change to output quality.

---

### Proposal 2: Add parallelism reminder to dispatch template in SKILL.md

**File:** `/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/github/skills/github/SKILL.md`
**Location:** `### How to Prompt` section, `**Template (exploration):**` block

**WHY:** The dispatch template shows a numbered list of search topics without any parallelization hint. Adding one line primes the subagent and reinforces Proposal 1.

**Current:**
```markdown
**Template (exploration):**
```
Research [TOPIC] on GitHub.

Focus on:
1. [Specific aspect 1]
2. [Specific aspect 2]

For each repo found:
- Name, stars, description
- Key implementation files (paths!)
- [Specific evaluation criteria]
```
```

**Proposed — add one line to the template:**
```markdown
**Template (exploration):**
```
Research [TOPIC] on GitHub.

Run all searches in parallel (they are independent — no result from search N is needed for search N+1).

Focus on:
1. [Specific aspect 1]
2. [Specific aspect 2]

For each repo found:
- Name, stars, description
- Key implementation files (paths!)
- [Specific evaluation criteria]
```
```

**Expected Impact:** Dispatcher consistently primes subagent for parallel execution on landscape research tasks.

---

### Proposal 3: Fix eval.md — use RAG project workflow.py for index-json

**File:** RAG plugin source `eval.md` (not the cache)
**Location:** `# Phase 2: JSONL to MD, Chunk, Index` — the `# Index` command

**WHY:** `$PLUGIN_DIR/workflow.py` uses cache's `indexer.py` which calls `load_dotenv()` without a path. CWD during eval is the target project (not RAG project), so `.env` with postgres credentials is never found → auth failure.

**Current:**
```bash
# Index
$PLUGIN_DIR/venv/bin/python $PLUGIN_DIR/workflow.py index-json \
    --input "$PLUGIN_DIR/data/documents/Subagents/<agent_id>.json"
```

**Proposed:**
```bash
# Index (must run from RAG project dir so load_dotenv() finds credentials)
RAG_PROJECT=$(find ~/Documents/ai -name "workflow.py" -path "*/RAG/workflow.py" | head -1 | xargs dirname)
cd $RAG_PROJECT && ./venv/bin/python workflow.py index-json \
    --input "$PLUGIN_DIR/data/documents/Subagents/<agent_id>.json"
```

**Expected Impact:** Indexing works without manual intervention. Eval can run non-interactively.

---

## Cleanup Checklist

- [ ] Delete from RAG: `workflow.py delete --collection Subagents --document ac85e3faa825da65a.md`
- [ ] Remove: `$PLUGIN_DIR/data/documents/Subagents/ac85e3faa825da65a.md`
- [ ] Remove: `$PLUGIN_DIR/data/documents/Subagents/ac85e3faa825da65a_summary.md`
- [ ] Remove: `$PLUGIN_DIR/data/documents/Subagents/ac85e3faa825da65a.json`
