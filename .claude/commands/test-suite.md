---
description: Run scraping suite baseline and comparison to validate production code quality
argument-hint: [optional-context]
---

## Purpose

Validate scraping quality after production code changes by running the scraping_suite baseline and comparison scripts, then automatically assessing the results.

**Context:** $ARGUMENTS

---

## Phase 1: Execute Baseline Suite

**CRITICAL:** Run the baseline scraper against all test domains.

**Location:** `debug/scraping_suite/run_baseline.py`

**Execution:**
```bash
cd debug/scraping_suite
python run_baseline.py
```

**What it does:**
- Scrapes all URLs from `domains.txt` using production `scrape_url_workflow()`
- Creates new numbered iteration for each domain (e.g., iteration_006.md)
- Saves metadata (char_count, word_count, timestamp) as JSON

**Expected output:**
- New iteration files in `debug/scraping_suite/baselines/[domain]/`
- Console output showing domains processed

---

## Phase 2: Compare Iterations

**CRITICAL:** Generate diff report comparing last two iterations.

**Location:** `debug/scraping_suite/compare_iterations.py`

**Execution:**
```bash
cd debug/scraping_suite
python compare_iterations.py
```

**What it does:**
- Compares last two iterations for each domain
- Calculates character/word count changes with percentages
- Generates unified diffs showing content changes
- Creates timestamped report in `debug/scraping_suite/reports/`

**Expected output:**
- New diff report: `reports/diff_report_YYYYMMDD_HHMMSS.txt`
- Console output showing report location

---

## Phase 3: Analyze Results & Assess Quality

**CRITICAL:** Read the generated diff report and analyze quality impact.

**Report location:** `debug/scraping_suite/reports/diff_report_[latest].txt`

**Analysis Criteria:**

### For each domain, check:

1. **Status Classification** (from report):
   - `IDENTICAL` - No changes detected
   - `MINOR_CHANGE` - < 5% character/word count change
   - `MODERATE_CHANGE` - 5-20% change
   - `MAJOR_CHANGE` - > 20% change

2. **Content Quality**:
   - Review unified diffs to understand what changed
   - Assess if changes are improvements or regressions
   - Check for missing content, broken extraction, formatting issues

3. **Domain-by-domain evidence**:
   - Concrete character/word count changes
   - Specific content differences from unified diffs
   - Assessment of each change (improvement/neutral/regression)

### Overall Assessment Logic:

```
IF all domains are IDENTICAL or show improvements:
  → PASS

IF some domains show MINOR/MODERATE changes that need review:
  → REVIEW

IF any domain shows clear content loss, broken extraction, or quality degradation:
  → FAIL
```

---

## Phase 4: Present Assessment to User

**Format:**

```
SCRAPING SUITE VALIDATION REPORT
=================================

Baseline Execution: ✅ Completed
Comparison Report: debug/scraping_suite/reports/diff_report_[timestamp].txt

DOMAIN-BY-DOMAIN ANALYSIS
--------------------------

[Domain 1 Name]:
- Status: [IDENTICAL/MINOR_CHANGE/MODERATE_CHANGE/MAJOR_CHANGE]
- Character Count: [old] → [new] ([+/-X%])
- Word Count: [old] → [new] ([+/-X%])
- Content Changes: [Brief description of what changed based on unified diff]
- Assessment: ✅ Improvement / ⚪ Neutral / ❌ Regression
- Evidence: [Specific examples from diff]

[Domain 2 Name]:
- Status: [...]
- Character Count: [...]
- Word Count: [...]
- Content Changes: [...]
- Assessment: [...]
- Evidence: [...]

[Repeat for all domains...]

OVERALL ASSESSMENT
------------------

Result: [PASS / REVIEW / FAIL]

PASS:
- All domains maintain or improve quality
- No regressions detected
- Production code is validated

REVIEW:
- [X] domains show changes requiring review
- Changes detected: [list specific areas]
- Recommendation: [Review these specific diffs and verify intended behavior]

FAIL:
- [X] domains show quality degradation
- Regressions detected: [list specific issues]
- Recommendation: [Refine the fix to address these regressions]

CONCLUSION
----------

[Clear summary of findings and next steps]
```

**IMPORTANT:** Provide concrete evidence from the diff report. Don't just say "changes detected" - show actual character counts, percentages, and content examples.

---

## Usage Notes

- Run this command manually after implementing fixes to production code
- Requires `debug/scraping_suite/` directory with run_baseline.py and compare_iterations.py
- Uses production `scrape_url_workflow()` from `src/scraper/scrape_url.py`
- Test domains defined in `debug/scraping_suite/domains.txt`
