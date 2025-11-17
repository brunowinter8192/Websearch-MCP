---
description: Check if README.md and module DOCS.md files need updates after MCP server code changes
---

# MCP DOCUMENTATION UPDATE CHECK

Systematic review protocol for README.md and module-level DOCS.md updates following CLAUDE.md MCP server standards.

**Execute this command manually after making code changes to determine if documentation updates are required.**

---

## CRITICAL RULE

**WHEN IN DOUBT, ASK THE USER.**

If you are uncertain whether README.md or DOCS.md should be updated or not, ALWAYS ask the user before making the decision.

---

## OVERVIEW

Documentation updates are OPTIONAL - only required when changes affect the documented contract or tool behavior.

**Two separate concerns:**
- **README.md:** Usage focused (How to INSTALL and USE the MCP server)
- **src/domain/DOCS.md:** Architecture focused (How modules in that domain WORK internally)

---

## README.md CHECK

**Purpose:** README documents installation, quick start, environment variables, and tool usage.

### Update Required When:

1. **New tool added to server.py**
   - New @mcp.tool definition
   - New use case for the MCP server

2. **Tool parameters change**
   - New parameter added to existing tool
   - Parameter removed or renamed
   - Default values change

3. **Tool behavior changes**
   - Output format changes
   - New fields in response
   - Different use case guidance in docstring

4. **Environment variables change**
   - New API keys or tokens required
   - .env structure changes
   - .mcp.json env section changes

5. **Installation or setup changes**
   - New dependencies required
   - venv setup changes
   - .mcp.json path changes

### Update NOT Required When:

- Bug fixes in src/ module implementation
- Internal refactoring of workflow functions
- Performance improvements (caching, pagination)
- Code reorganization without changing tool interface
- Function renaming within src/ modules

### Decision Workflow:

1. **Read README** - Check tool descriptions and setup instructions
2. **Identify Impact** - Does user-visible interface change?
3. **Decision:**
   - If tool interface/setup changes then Update README
   - If only internal implementation changes then Document reason for skipping
   - **If uncertain then ASK THE USER**

---

## MODULE DOCS.md CHECK

**Purpose:** Each domain folder in src/ has its own DOCS.md documenting its modules.

**Location:** src/domain_name/DOCS.md

### Update Required When:

1. **New tool module added to domain folder**
   - Add new ## module.py section to that domain's DOCS.md
   - Document workflow and functions

2. **New function added to existing module**
   - Add ### function_name() section
   - Describe WHAT the function does

3. **Function responsibility (WHAT) changes**
   - Function now does something different
   - Function purpose changes

4. **Input/Output contract changes**
   - Function parameters change
   - Return structure changes
   - Error handling behavior changes

5. **Orchestrator call sequence changes**
   - Functions called in different order
   - New functions added to workflow
   - Functions removed from sequence

6. **New domain folder created**
   - Create new DOCS.md in that folder
   - Document all modules in the domain

### Update NOT Required When:

- Bug fixes in function implementation (HOW)
- Internal refactoring within function body
- Performance improvements
- Code reorganization without changing responsibilities
- Variable renaming (internal only)
- Algorithm changes that don't affect contract

### Decision Workflow:

1. **Identify affected domain** - Which src/domain/ folder contains changes?
2. **Read domain DOCS.md** - Locate sections describing changed modules/functions
3. **Identify Impact** - Does the WHAT change, or only the HOW?
4. **Check call sequence** - Did workflow orchestrator order change?
5. **Decision:**
   - If WHAT changed then Update domain's DOCS.md section
   - If only HOW changed then Document reason for skipping
   - **If uncertain then ASK THE USER**

---

## COMPREHENSIVE REVIEW PROTOCOL

### Step 1: Analyze Changes
List all files modified and nature of changes:
- Which files changed? (server.py, src/*.py, .mcp.json, .env)
- What changed in each file?
- Are changes to tool interface or internal implementation?

### Step 2: README Impact Assessment
Ask these questions:
1. Were new tools added to server.py?
2. Did tool parameters change (Annotated + Field)?
3. Did tool docstrings change (use cases)?
4. Did environment variables or setup change?
5. Did .mcp.json configuration change?

**If YES to any then README update likely required**

### Step 3: Module DOCS Impact Assessment
Ask these questions:
1. Were new modules added to a domain folder in src/?
2. Were new functions added to existing modules?
3. Do existing functions do something different (WHAT not HOW)?
4. Did function signatures change (parameters, return types)?
5. Did the workflow orchestrator call sequence change?
6. Was a new domain folder created in src/?

**If YES to any then that domain's DOCS.md update likely required**

### Step 4: Document Decisions
For each file (README, domain DOCS), document:
```
FILE: README.md / src/domain/DOCS.md
CHANGE: <brief description>
SECTION: <which section would be affected>
DECISION: UPDATE REQUIRED / NO UPDATE / UNCERTAIN
REASON: <why WHAT changed or why only HOW changed>
ACTION: <if update required, what to update>
RECOMMENDATION: <formulate question + YES/NO recommendation for user>
```

**IMPORTANT:**
- If DECISION is UNCERTAIN then Ask the user with your recommendation
- If DECISION is UPDATE REQUIRED then Present recommendation to user for confirmation
- If DECISION is NO UPDATE then Present recommendation to user for confirmation

---

## RECOMMENDATION FORMAT

**CRITICAL:** Present a single, consolidated recommendation.

After completing Step 4, summarize:

```
OVERALL RECOMMENDATION:
- README.md: UPDATE / NO UPDATE
- src/domain/DOCS.md: UPDATE / NO UPDATE (list each affected domain)

QUESTION (if applicable): [Specific uncertainty]
RECOMMENDATION: [e.g., "Update src/scraper/DOCS.md yes, README no"]
REASONING: [Brief explanation]
```

**Rules:**
1. One consolidated overview, not per-change
2. Only formulate question if uncertain
3. User makes final decision

---

## MCP-SPECIFIC CHECKS

### server.py Changes
- New @mcp.tool definition then Update README and relevant domain DOCS.md
- Import from src/domain/ added then Update that domain's DOCS.md
- Tool parameter changed then Update README (usage) and domain DOCS.md (function signature)
- Docstring changed then Update README (use case guidance)

### src/domain/ Module Changes
- New module file in domain then Update that domain's DOCS.md (add ## module.py section)
- New function then Update domain's DOCS.md (add ### function_name() section)
- Workflow call sequence changed then Update domain's DOCS.md (orchestrator description)
- Function contract changed then Update domain's DOCS.md (input/output description)
- New domain folder created then Create new DOCS.md in that folder

### Configuration Changes
- .mcp.json paths changed then Update README (installation section)
- New environment variable then Update README (env vars section)
- .gitignore updated then Usually no update needed

---

## EXECUTION CHECKLIST

After running this command, complete the following:

- [ ] List all files modified in this session
- [ ] For each change, identify if WHAT or HOW changed
- [ ] Check README sections affected by tool interface changes
- [ ] Check domain DOCS.md sections affected by architecture changes
- [ ] Identify which domain folders are affected
- [ ] Document update decisions for README and each affected domain's DOCS.md
- [ ] **Formulate recommendations for each decision**
- [ ] **Present recommendations to user:**
  - UNCERTAIN then Ask user with YES/NO recommendation
  - UPDATE REQUIRED then Confirm with user before updating
  - NO UPDATE then Document reasoning only
- [ ] Wait for user approval before making any documentation changes
- [ ] If approved, update sections following CLAUDE.md prose style
- [ ] If not approved, document user's decision
