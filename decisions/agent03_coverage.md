# Agent Step 3: Scrape Coverage & Stop Conditions

## Status Quo

**Code:** `agents/web-research.md` (Step 3: Scrape Aggressively, When to Stop)

**Scrape target:** "10, 15, 20 if they exist" — global count, not per-topic
- No per-topic minimum enforced by default
- Exception: when task defines multiple topics, Step 3 includes: "verify minimum 5 scraped URLs attributed to THAT topic. If fewer: fire additional topic-specific queries before moving on."

**Content quality tiers:**
- HIGH: Tutorials with code, benchmarks with numbers, API docs, research papers with methodology
- MEDIUM: Blog posts with substance, overviews with useful links, concrete discussion answers
- LOW: Thin wrappers, mostly links, surface-level overview

**Stop conditions** (ALL must be true):
1. Exhausted 5+ query variations with pagination
2. Scraped all non-plugin URLs from top results
3. Additional queries return mostly duplicates

**Report format:** Scraped Content (per URL: title, URL, domain, quality, key content) + Plugin-Routed URLs + Search Metadata (queries, total reviewed, scraped count, plugin-routed count, skipped count)

## Evidenz

Per-topic coverage from eval (multi-topic research tasks):

| Agent | Topic | URLs Scraped | Target |
|-------|-------|-------------|--------|
| Agent 5 (chunking) | Topic 1 | 5 | 10+ |
| Agent 5 (chunking) | Topic 3 | 8 | 10+ |
| Agent 6 (embedding) | Topic 2 | 5 | 10+ |
| Agent 6 (embedding) | Topic 3 | 4 | 10+ |

All topics fell short of the 10+ global target. Per-topic minimum of 5 was barely met (Agent 6 Topic 3: 4 URLs — below minimum).

**Root cause hypothesis:** Agents track a global scraped count, not per-topic. Once global count hits 10+, stop conditions trigger even if individual topics are undercovered. The per-topic instruction exists in Step 3 but is easy to miss once global target appears met.

**Total scraped across agents:**
- Agent 4: ~7 scraped (21 tool_uses, minus search calls and plugin routes)
- Agent 5: ~12–15 scraped (35 tool_uses)
- Agent 6: ~12–15 scraped (30 tool_uses)

## Entscheidung

Per-topic coverage tracking is the critical gap. The global "10-15-20" target is misleading in multi-topic tasks — it creates false confidence that coverage is complete when topics are unevenly covered.

The per-topic minimum of 5 already exists in the instructions but is not enforced structurally. Agents comply when single-topic but drift when multi-topic.

Recommendation: Restructure Step 3 for multi-topic tasks to use a per-topic checklist:
- Before moving to next topic: verify "≥5 scraped for THIS topic" explicitly
- Before triggering stop: verify per-topic minimums, not just global count
- Remove global target ("10-15-20") as the primary stop signal for multi-topic tasks

For single-topic tasks, global count remains appropriate.

## Offene Fragen

- Is 5 per topic the right minimum, or should it scale with topic specificity? (Niche topic may only have 3 high-quality sources.)
- Should quality tiers affect the minimum? (3 HIGH > 8 LOW in practice.)
- What is the actual max useful URLs per topic? At some point, additional scraping yields redundant content — eval didn't measure marginal value.
- The stop condition "scraped all non-plugin URLs from top results" is vague — what counts as "top results"? First page only? All 3 pages?
- Agent 6 Topic 3: 4 URLs (below the stated 5 minimum). Was this a one-off or structural? Need more eval runs to determine failure rate.
- Does forcing ≥5 per topic increase total tool_uses significantly? If agents are already near the Haiku context limit, this may cause truncation instead of improvement.

## Quellen

- `agents/web-research.md` — Step 3 scrape instructions and stop conditions
- Eval session findings (2026-03-15): Agent 5 (Topic 1=5, Topic 3=8), Agent 6 (Topic 2=5, Topic 3=4)
- Agent run metadata: Agent 4 (21 tool_uses), Agent 5 (35), Agent 6 (30)
- Eval proposals from session: 4 proposals covering pagination, science category, and per-topic coverage gaps
