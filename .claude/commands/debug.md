---
description: Systematic debugging with context gathering, debug-specialist subagent and bug documentation
argument-hint: [observation/error-description]
---

## Problem Observation

User observes: $ARGUMENTS

---

## Phase 1: Context Gathering

User defines the problem in arguments. Main Agent gathers context:

1. Check `bug_fixes/` for similar past issues
2. Check `not_working/` for fixes that failed
3. Find relevant files (max 3-4, focused)
4. Gather: Error messages, stack traces, File:Line references

### Scraper-Specific Context

**CRITICAL: No Overfitting**

We build a GENERAL scraper, not one that overfits to the 6 baseline sites. Fixes must work for ANY website, not just the test domains.

**Understand the Problem:**

Read the latest iteration in `debug/scraping_suite/baselines/*/` to see what user's problem description actually looks like in the output.

**Test Domains:**

Agents test against URLs from `debug/scraping_suite/domains.txt`

### Phase 1 Output: Context Summary

```
CONTEXT SUMMARY
===============

PROBLEM: [User's problem from arguments]

RELEVANT FILES:
- /path/to/file1.py - [why relevant]
- /path/to/file2.py - [why relevant]

PAST ATTEMPTS:
- bug_fixes/xyz.md - [what was tried]
- not_working/abc.md - [what failed and why]

PROPOSED LANES:
- Agent 1: [Lane description]
- Agent 2: [Lane description] (if needed)

===============
```

**STOPPER**

Proceed to Phase 2?
- Yes, launch agents
- No, remarks/clarifications needed

**CRITICAL:** Do NOT proceed to Phase 2 unless user explicitly confirms.

---

## Phase 2: Launch Debug Agents

**Workspaces:**
- Agent 1 → `debug/Agent_1/`
- Agent 2 → `debug/Agent_2/` (if used)

**Agent Prompt must contain:**
1. **Problem** - What's broken, expected vs actual
2. **Relevant Files** - Absolute paths with line refs
3. **Proposed Lane** - Specific focus area

**Agent Prompt Template:**

```
## Your Lane: [LANE DESCRIPTION]

You are Agent [X]. Your ONLY focus is: [specific problem/road to investigate]

## Problem Description
[Precise description of what is failing, expected vs actual]

## Relevant Production Files
[Absolute paths]:
- /path/to/file1.py
- /path/to/file2.py

## Your Task (Steps 1-2 only, then STOP and report)

**Step 1: Root Cause Analysis**
- Analyze the code
- Identify WHERE and WHY the bug occurs
- Document File:Line references

**Step 2: Reproduce**
- Create `debug/Agent_[X]/reproduce_[issue].py`
- Copy affected production function(s) 1:1
- Reproduce the bug with real data
- Document: Bug reproduced YES/NO + findings

**Step 2.5: STOP and Report**
After reproduce, provide this report and STOP:

AGENT [X] CHECKPOINT REPORT
===========================
LANE: [Your assigned lane]

ROOT CAUSE:
- File: [module.py:line]
- Issue: [What you found]
- Why: [Explanation]

REPRODUCTION:
- Success: YES/NO
- Script: debug/Agent_[X]/reproduce_[issue].py
- Findings: [What reproduction revealed]

PLANNED FIX:
- Approach: [How you plan to fix it]
- Files to modify: [List]

AWAITING: GO/REDIRECT instruction
===========================

## CRITICAL Rules
- Stay on YOUR lane only
- NO mocks - copy production code 1:1
- Test against real data
- Your workspace: debug/Agent_[X]/
```

**If 2 agents:** Launch BOTH in a single message (parallel execution).

---

## Phase 3: Checkpoint Assessment

Review agent checkpoint reports. Check:
- Lane adherence: Is agent still on assigned problem?
- Reproduction success: Did agent reproduce the bug?

```
CHECKPOINT ASSESSMENT
=====================

AGENT 1:
- Lane: [assigned] → [actual]: OK / DRIFTED
- Reproduced: YES / NO
- Decision: GO / REDIRECT
- Instruction: [If redirect, what to fix]

AGENT 2 (if used):
- Lane: [assigned] → [actual]: OK / DRIFTED
- Reproduced: YES / NO
- Decision: GO / REDIRECT
- Instruction: [If redirect, what to fix]

=====================
```

**STOPPER**

Resume agents for fix?
- Yes, GO
- No, REDIRECT with corrections

**CRITICAL:** Do NOT proceed to Phase 4 unless user explicitly confirms.

---

## Phase 4: Resume Agents for Fix

Resume each agent with GO or REDIRECT instruction:

```
## [GO/REDIRECT] - Continue to Fix

[If GO]: Your checkpoint report is good. Proceed with your planned fix.
[If REDIRECT]: [Specific correction needed]

## Your Task (Steps 3-4)

**Step 3: Implement Fix**
- Create `debug/Agent_[X]/solution_[issue].py`
- Apply fix to copied production code
- Validate fix works with real data

**Step 4: Final Report**

AGENT [X] FINAL REPORT
======================
LANE: [Your lane]

ROOT CAUSE CONFIRMED:
- File: [module.py:line]
- Issue: [Final diagnosis]

FIX IMPLEMENTED:
- Solution script: debug/Agent_[X]/solution_[issue].py
- What was changed: [Specific code changes]
- Validation: [How you confirmed it works]

PRODUCTION FIX:
- Files to modify: [List with line numbers]
- Exact changes needed: [Code diff or description]

CONFIDENCE: [HIGH/MEDIUM/LOW]
- Why: [What makes you confident or uncertain]
======================
```

---

## Phase 5: Synthesis

Combine agent findings into recommendation:

```
SYNTHESIS
=========

AGENT FINDINGS:

Agent 1 ([Lane]):
- Root Cause: [What they found]
- Fix: [Their solution]
- Confidence: [Their self-assessment]

Agent 2 ([Lane]) - if used:
- Root Cause: [What they found]
- Fix: [Their solution]
- Confidence: [Their self-assessment]

RECOMMENDED FIX:
[Concrete recommendation based on agent findings]

WHAT COULD BE WRONG:
- [Uncertainty 1]
- [Uncertainty 2]

=========
```

**STOPPER**

Proceed to implementation?
- Yes, write plan
- No, investigate further

**CRITICAL:** Do NOT proceed to Phase 6 unless user explicitly confirms.

---

## Phase 6: Write Plan

1. Write fix plan to system plan file (path from Plan Mode system message)
2. Call ExitPlanMode

---

## Phase 7: Implementation

1. Implement the fix
2. Commit changes

---

## Phase 8: User Testing

User validates fix in production environment.

### Handoff

```
FIX IMPLEMENTED
===============

Files modified:
- [List of changed files with line numbers]

Changes made:
- [Summary of what was changed]

Ready for user testing.
===============
```

### After User Confirmation
- If fix works → Run `/document-fix` to document in `bug_fixes/`
- If fix fails → Return to Phase 1 with new findings, document in `not_working/`
