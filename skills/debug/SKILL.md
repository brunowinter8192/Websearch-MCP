---
name: debug
description: Structured debugging workflow for scraper/crawler bugs
---

# Debug Skill — Structured Bug Investigation

This skill is for Opus (the orchestrator), not for workers. It defines the steps to follow when investigating and fixing bugs in the scraping/crawling pipeline.

## When to Activate

When a bug is discovered in:
- `src/scraper/scrape_url.py` (scraping failures, garbage detection, content extraction)
- `crawl_site.py` (crawl failures, file saving, URL discovery)
- `explore_site.py` (exploration failures, strategy issues)

## Steps (SEQUENTIAL — do not skip)

### Step 1: Identify URLs

Collect the concrete URLs that exhibit the bug. For each URL:
- What is the expected behavior?
- What actually happens?
- What error/output do we get?

### Step 2: Identify Required Sources

Before any fix attempt, list what you need to understand:
- Which production code files are involved?
- Which docs/RAG collections have relevant information? (e.g. Crawl4AI Docs for CrawlResult fields)
- Which dev suite scripts can test the fix?

**READ the production code BEFORE proposing fixes.** Claims like "function X doesn't do Y" must be verified by reading the code.

### Step 3: Activate Required Skills

Activate skills needed for investigation:
- `/rag:RAG` for Crawl4AI Docs, SearXNG Docs lookup
- `/searxng:searxng` for MCP tool testing

### Step 4: Check Dev Suite

Look in `dev/` for existing test infrastructure:
- `dev/scraping_suite/` — scrape_url testing (baselines, filters, JS rendering)
- `dev/crawling_suite/` — crawl/explore testing (strategies, filters)
- `dev/scraping_suite/domains.txt` — test URL categories

Determine if new test URLs need to be added to `domains.txt` for regression testing.

### Step 5: Evaluate Fix Approaches

For each bug, consider multiple approaches:
- Present as table: Approach | Pro | Contra
- Give clear recommendation with reasoning
- Consider false positive risk for detection changes

### Step 6: Spawn Workers (if code changes needed)

**Pre-flight checklist before spawning:**
- [ ] venv symlinked into worktree: `ln -sf "$PROJECT/venv" "$WORKTREE/venv"`
- [ ] Worker prompt includes concrete test commands
- [ ] Worker prompt includes false-positive test URLs (legitimate content that must NOT be flagged)
- [ ] Worker prompt specifies which dev suite scripts to run for verification

**One worker per independent fix** (parallel if they touch different files).

### Step 7: Verify (YOU, not the workers)

**CRITICAL: Never trust worker "verified" claims.**

After merging worker branches, run the actual tests yourself:
```bash
# Test the bug URL — should now be handled correctly
./venv/bin/python -c "import asyncio; from src.scraper.scrape_url import scrape_url_raw_workflow; print(asyncio.run(scrape_url_raw_workflow('BUG_URL', '/tmp/test')))"

# Test legitimate URLs — must still work
./venv/bin/python -c "import asyncio; from src.scraper.scrape_url import scrape_url_raw_workflow; print(asyncio.run(scrape_url_raw_workflow('GOOD_URL', '/tmp/test')))"
```

If workers reported "tests passed" but you can see they had no venv/browser — the tests did NOT pass. Re-test.

## Anti-Patterns (from session 2026-03-16)

- **Claiming code behavior without reading it:** "scrape_url_raw has no stealth fallback" was WRONG — code had stealth at lines 152-159
- **Trusting worker "verified" claims:** Workers said "verified" but had no venv — tests never ran
- **Fixing symptoms instead of root cause:** AWS 162KB file was not a nav-dump but an Amazon Cookie Wall with different wording ("cookie preferences" vs "consent preferences")
- **Spawning fix workers before consulting docs:** RAG search for CrawlResult fields showed status_code exists — should have been done BEFORE writing worker prompts
