---
description: Systematic debugging with context gathering, debug-specialist subagent and bug documentation
argument-hint: [observation/error-description]
---

## Problem Observation

User observes: $ARGUMENTS

---

## Phase 1: Context Gathering

**CRITICAL:**
- Read the codebase BROADLY to understand the user's problem and effectively prompt the subagent
- If unclear what the user means, ask clarifying questions before prompting the subagent

1. Identify affected modules based on the observation
2. Check bug_fixes/ in root to see if such an issue existed before, it's possible the issue was previously fixed but reappeared due to a new feature
3. Find relevant files in the codebase (max 3-4, focused)
4. Check `logs/` folder if present
5. Determine debug/ location: root-level (simple MCP) or src/[module]/debug/ (complex MCP)
6. Gather: Error messages, stack traces, affected functions with File:Line references

---

## Phase 2: Call Debug-Specialist

After gathering all information, call the Task tool:

```json
{
  "tool": "Task",
  "parameters": {
    "description": "debug issue",
    "subagent_type": "debug-specialist",
    "prompt": "## Problem Description\n<Precise description of what is failing, expected vs actual behavior>\n\n## Investigation Results\n<Findings from Phase 1: error messages, stack traces, affected functions with File:Line references>\n\n## Recommended Starting Points\n<Specific folders and files the subagent should examine first, ordered by relevance>"
  }
}
```

---

## Phase 3: Wait for User Approval

After receiving the debug report from the subagent:
- Present the findings to the user
- **WAIT for explicit user confirmation** before proceeding
- Ask: "Should I implement the fix?"

---

## Phase 4: Implementation and Documentation (after Approval)

### 4.1 Implement Fix
- Apply the proposed fix
- Test the changes

### 4.2 Document Bug Fix
**Location:** `bug_fixes/` (in project root)

**Filename:** `[descriptive-name]_YYYYMMDD_HHMMSS.md`

**Format (CONCISE):**
```markdown
# [Short Bug Title]

**Date:** YYYY-MM-DD HH:MM

## Problem
[How the problem manifested - 2-3 sentences max]

## Root Cause
[What was the root cause - 2-3 sentences max]

## Fix
[How it was fixed - File:Line references]
```

**IMPORTANT:** Documentation must be short and concise - no prose, only facts.
