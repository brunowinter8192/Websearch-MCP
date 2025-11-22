---
description: Systematic refactoring analysis after feature implementation to assess module complexity and suggest improvements
argument-hint: [optional: module-path or "auto" to detect recent changes]
---

## Context

**When to use:** After successful feature implementation (via `/debug` or `/feature`), before `/check-docs`.

**Assumption:** Claude has codebase knowledge from recent feature work.

**Purpose:** Systematically assess if modules have become too complex/large and suggest concrete refactoring options.

---

## Phase 1: Identify Changed Modules

**CRITICAL:** Determine which modules to analyze based on recent work.

### Auto-Detection (if no $ARGUMENTS provided):

```bash
# Check git for recently modified files
git diff --name-only HEAD~1 HEAD | grep "^src/.*\.py$"
```


## Phase 2: Collect Module Metrics

**CRITICAL:** Measure objective code metrics for each module.

For each identified module, collect:

### 2.1 Basic Metrics

Use `Read` tool to analyze module files:

1. **Lines of Code (LOC)**
   - Total lines in file
   - Excluding blank lines and comments
   - Threshold: ⚠️ > 400 LOC

2. **Function Count**
   - Count all function definitions (def ...)
   - Exclude nested functions
   - Threshold: ⚠️ > 15 functions

3. **Section Compliance**
   - Check INFRASTRUCTURE / ORCHESTRATOR / FUNCTIONS sections exist
   - Verify ORCHESTRATOR has minimal logic (only function calls)

### 2.2 Complexity Indicators

1. **Long Functions**
   - Functions > 50 LOC?
   - Too many nested blocks (> 4 levels)?

2. **Code Duplication**
   - Similar logic patterns across multiple functions?
   - Repeated code blocks (> 10 lines identical)?

3. **Cross-Module Dependencies**
   - How many other modules does this import from?
   - Threshold: ⚠️ > 5 cross-module imports

### 2.3 SOLID Principle Violations

1. **Single Responsibility Principle (SRP)**
   - Does module handle multiple unrelated concerns?
   - Example violation: Parsing HTML + API calls + Database writes

2. **Open/Closed Principle**
   - Are there many conditional branches that would require changes for new features?

**Metrics Template:**

```
MODULE: src/[module_path].py
============================

Basic Metrics:
- Lines of Code: [X] ([✅ OK | ⚠️ ABOVE THRESHOLD])
- Function Count: [Y] ([✅ OK | ⚠️ ABOVE THRESHOLD])
- CLAUDE.md Structure: [✅ COMPLIANT | ❌ NON-COMPLIANT]

Complexity Indicators:
- Long Functions (>50 LOC): [count] functions
  - [function_name]: [X] LOC
- Deeply Nested Blocks (>4 levels): [count] locations
- Code Duplication: [✅ NONE | ⚠️ DETECTED - describe]

Cross-Module Dependencies:
- Imports from: [list of src/ modules]
- Imported by: [list of src/ modules]
- Dependency Count: [X] ([✅ OK | ⚠️ HIGH])

SOLID Violations:
- SRP: [✅ OK | ⚠️ MULTIPLE CONCERNS - list concerns]
- OCP: [✅ OK | ⚠️ MANY CONDITIONALS]
```

---

## Phase 3: Refactoring Opportunity Identification

**CRITICAL:** Based on metrics, identify concrete refactoring opportunities.

### 3.1 Pattern Recognition

Scan for common refactoring patterns:

1. **Extract Module Pattern**
   - Trigger: Module > 400 LOC with distinct functional groups
   - Action: Split into focused modules
   - Example: "HTML parsing" + "Markdown conversion" → separate modules

2. **Extract Function Pattern**
   - Trigger: Functions > 50 LOC with sub-tasks
   - Action: Break into smaller helper functions
   - Example: Large orchestrator with inline logic → extract helpers

3. **Consolidate Duplication Pattern**
   - Trigger: Similar code in multiple places
   - Action: Extract to shared utility module
   - Example: Common validation logic → src/utils/validators.py

4. **Introduce Abstraction Pattern**
   - Trigger: Many similar functions with slight variations
   - Action: Create generic function with parameters
   - Example: 5 similar scrapers → parameterized scraper

### 3.2 Impact Analysis

For each identified opportunity, analyze:

**What Would Refactoring Require?**

```
OPPORTUNITY: [Pattern Name]
===========================

Current State:
- [Describe current structure]

Proposed Change:
- [Describe refactored structure]

Required Actions:
1. Create: [new files to create]
2. Modify: [existing files to change]
3. Move: [code to relocate]
4. Update: [imports/dependencies]
5. Document: [DOCS.md updates]

Affected Files:
- src/[module1].py:[lines] - [what changes]
- src/[module2].py:[lines] - [what changes]
- server.py:[lines] - [if tool imports change]
- src/[domain]/DOCS.md - [new sections to add]

Effort Estimate: [LOW | MEDIUM | HIGH]
- LOW: < 1 hour (simple extraction)
- MEDIUM: 1-3 hours (module split)
- HIGH: > 3 hours (major restructuring)
```

---

## Phase 4: Generate Refactoring Proposal

**CRITICAL:** Create concrete, actionable proposal with clear reasoning.

### 4.1 Proposal Format

For each refactoring opportunity (prioritize by impact/effort ratio):

```
REFACTORING PROPOSAL #[N]
==========================

Trigger:
[Specific metric that triggered this proposal]
Example: "src/scraper/scrape_url.py has 450 LOC (threshold: 400)"

Analysis:
New implementation would require:
- [Specific requirement 1]
- [Specific requirement 2]

I suggest:
[Concrete refactoring action]
Example: "Auslagerung der Funktionen convert_nodes_to_markdown, clean_markdown_artifacts,
          clean_whitespace in neues Modul src/scraper/markdown_converter.py"

Rationale:
+ [Benefit 1 with specific improvement]
+ [Benefit 2 with specific improvement]
+ [Benefit 3 with specific improvement]

Tradeoffs:
- [Cost 1 with specific concern]
- [Cost 2 with specific concern]

Effort: [LOW|MEDIUM|HIGH] ([X] hours estimated)

CLAUDE.md Compliance Impact:
- Structure: [Will maintain | Will improve] 3-section pattern
- Dependencies: [X] new cross-module imports
- Documentation: [X] DOCS.md sections to update
```

### 4.2 No Refactoring Needed

If all metrics are within thresholds:

```
REFACTORING ASSESSMENT
======================

All modules analyzed:
✅ src/[module1].py - 285 LOC, 12 functions, no violations
✅ src/[module2].py - 180 LOC, 8 functions, no violations

Conclusion: NO REFACTORING NEEDED
- All modules within acceptable complexity thresholds
- CLAUDE.md compliance maintained
- No code duplication detected
- SOLID principles followed

Recommendation: Proceed to /check-docs
```

---

## Phase 5: Present Options to User

**CRITICAL:** Use AskUserQuestion tool with Multiple Choice.

### 5.1 When Refactoring Suggested

Present analysis, then ask:

```
[First output the full analysis from Phase 2-4]

Now presenting decision options...
```

Use AskUserQuestion:

```json
{
  "questions": [{
    "question": "Should we refactor as suggested above?",
    "header": "Refactoring",
    "multiSelect": false,
    "options": [
      {
        "label": "Refactor now - implement proposal",
        "description": "Execute the suggested refactoring immediately (Effort: [X] hours)"
      },
      {
        "label": "Keep as is - complexity acceptable",
        "description": "Current structure is maintainable, no refactoring needed"
      },
      {
        "label": "Suggest alternative approach",
        "description": "Current proposal doesn't fit, I'll suggest a different refactoring"
      },
      {
        "label": "Defer to later",
        "description": "Acknowledge the issue but refactor in a future session"
      }
    ]
  }]
}
```

### 5.2 When No Refactoring Needed

Simply inform user:

```
REFACTORING ASSESSMENT COMPLETE
================================

Result: ✅ NO REFACTORING NEEDED

All modules are within acceptable complexity thresholds.
You can proceed with /check-docs to update documentation.
```

---

## Phase 6: Execute Decision (if applicable)

### 6.1 If User Chose: "Refactor now"

Follow the approved refactoring proposal:

1. **Create new module(s)** if needed
   - Follow INFRASTRUCTURE / ORCHESTRATOR / FUNCTIONS pattern
   - Move extracted code with proper function header comments

2. **Modify existing module(s)**
   - Remove moved code
   - Add imports for new modules
   - Update orchestrators to call new functions

3. **Update server.py** if tool imports change
   - Adjust import statements
   - Verify tool definitions still work

4. **Test the refactoring**
   - Ensure functionality unchanged
   - Run existing debug scripts
   - Verify no regressions

5. **Update DOCS.md**
   - Add sections for new modules
   - Update sections for modified modules
   - Document new cross-module interactions

**Report:**
```
REFACTORING EXECUTED
====================

Files Created:
✓ src/[new_module].py - [description]

Files Modified:
✓ src/[existing_module].py - [what changed]
✓ server.py - [if changed]

DOCS.md Updated:
✓ src/[domain]/DOCS.md - [new sections added]

Testing:
✓ [test results]

Next Step: Run /check-docs to finalize documentation
```

### 6.2 If User Chose: "Keep as is"

Document decision:

```
REFACTORING DECISION: KEEP AS IS
=================================

Rationale: [User's reasoning if provided, or "User accepted current complexity"]

Documented for future reference:
- Module metrics recorded in this analysis
- Refactoring opportunity identified
- Decision to keep current structure

Next Step: Proceed with /check-docs
```

### 6.3 If User Chose: "Suggest alternative"

Ask follow-up questions to understand user's preferred approach, then re-run Phase 3-4 with new constraints.

### 6.4 If User Chose: "Defer to later"

```
REFACTORING DEFERRED
====================

Issue acknowledged: [summary of complexity concerns]
Proposal documented: [brief summary]

Action: Create issue/note for future refactoring session

Next Step: Proceed with /check-docs
```

---

## Usage Examples

### Example 1: Auto-detect after feature implementation

```
User: /refactor-ask
```

→ Claude scans git diff, finds changed modules, analyzes, suggests refactoring

### Example 2: Specific module analysis

```
User: /refactor-ask src/scraper/scrape_url.py
```

→ Claude analyzes only the specified module

### Example 3: Multiple modules

```
User: /refactor-ask src/scraper/scrape_url.py src/scraper/search_web.py
```

→ Claude analyzes both modules and suggests consolidated refactoring

---

## Metrics Thresholds Reference

**Module Size:**
- ✅ OK: < 400 LOC
- ⚠️ WARNING: 400-600 LOC (consider refactoring)
- 🚨 CRITICAL: > 600 LOC (strongly recommend refactoring)

**Function Count:**
- ✅ OK: < 15 functions
- ⚠️ WARNING: 15-20 functions (review SRP)
- 🚨 CRITICAL: > 20 functions (likely multiple responsibilities)

**Function Length:**
- ✅ OK: < 30 LOC per function
- ⚠️ WARNING: 30-50 LOC (consider extracting helpers)
- 🚨 CRITICAL: > 50 LOC (definitely extract sub-tasks)

**Cross-Module Dependencies:**
- ✅ OK: < 5 imports from other src/ modules
- ⚠️ WARNING: 5-8 imports (high coupling)
- 🚨 CRITICAL: > 8 imports (too tightly coupled)

---

## Integration with Workflow

**Typical Workflow:**

1. User implements feature via `/feature` or `/debug`
2. Feature successfully implemented and tested
3. User runs `/refactor-ask` to assess code health
4. Claude analyzes and suggests refactoring (or confirms no action needed)
5. User decides: refactor now, defer, or keep as is
6. If refactored: Claude executes and tests
7. User runs `/check-docs` to finalize documentation
8. User commits changes

**Benefits:**
- Prevents technical debt accumulation
- Maintains CLAUDE.md compliance over time
- Catches complexity issues early
- Systematic decision-making for refactoring

---

## Important Notes

1. **Objective Metrics:** Use concrete LOC/function counts, not subjective "feels complex"

2. **CLAUDE.md Alignment:** All refactoring must maintain or improve CLAUDE.md compliance

3. **User Decision:** Always defer to user choice - Claude suggests, user decides

4. **No Premature Optimization:** Only suggest refactoring when thresholds exceeded, not "nice to have"

5. **Effort-Aware:** Always estimate effort to help user prioritize

6. **Test Coverage:** Verify refactoring doesn't break existing functionality
