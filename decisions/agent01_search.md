# Agent Step 1: Search Strategy

## Status Quo

**Code:** `agents/web-research.md` (Step 1: Search Broadly), `skills/agent-web-research/SKILL.md`

**Model:** claude-haiku (cheap, fast — specified in agent frontmatter)

**Query count:** 5+ variations mandatory
- Rephrase topic 3+ ways
- Try different angles: "X tutorial", "X implementation", "X benchmark", "X vs Y", "X best practices 2025"
- Keep queries short and keyword-focused (2–5 words)

**Pagination:** pageno=1, 2, 3 for every query as simultaneous parallel calls
- Max 50 results per page → up to 150 results per query
- Pages 2 and 3 fired WITHOUT waiting for page 1

**Categories:**
- Default: `category="general"` for all queries
- Also fire `category="science"` in parallel when query contains: "benchmark", "evaluation", "NDCG", "recall", "paper", "comparison", "study", "performance"
- Other available: `news`, `it`

**Engines:** Not explicitly set — SearXNG uses category defaults. Agent can combine: `engines="google,brave,google scholar"`

## Evidenz

Eval across 3 research agents (topics: chunking, embedding, general web):

| Agent | Topic | Queries | tool_uses |
|-------|-------|---------|-----------|
| Agent 4 (test) | general | 7 | 21 |
| Agent 5 (chunking) | chunking | 12 | 35 |
| Agent 6 (embedding) | embedding | 12 | 30 |

**Pagination underuse:** pageno=3 used exactly 0 times across all 3 agents. pageno=2 used rarely.
→ Agents do not follow the "fire pages 1+2+3 simultaneously" instruction in practice.

**Science category underuse:** `category="science"` used only when topic was explicitly academic.
→ Agent 5 (chunking benchmark topic) did NOT fire science queries despite "benchmark" keyword being present.

**Query count compliance:** 12 queries per agent (Agents 5+6) — above minimum of 5. Suggests query variation guidance is followed.

## Entscheidung

Pagination and science-category instructions are not being followed despite being explicit in the agent definition. Two possible causes:
1. Haiku model insufficient for complex multi-step parallel orchestration
2. Instructions not prominent enough (buried after other context)

Current approach (weak enforcement, hope for compliance) is insufficient for systematic coverage.

Recommendation: Restructure Step 1 as a numbered checklist with explicit "MANDATORY" markers. Consider adding a self-check: "Before proceeding to Step 2: how many pages did you fire per query? If <3: fire missing pages now."

## Offene Fragen

- Is Haiku capable of reliable parallel pageno=1/2/3 dispatch, or does this require Sonnet?
- Does adding a self-check at end of Step 1 actually change behavior, or does it just add noise?
- Should pagination be enforced differently: require pageno=3 explicitly in a separate pass, not parallel?
- What is the actual recall improvement from pageno=2+3? If top-50 (page 1) already covers 90% of relevant results, pagination may not be worth the cost.
- `category="it"` is available but never mentioned in agent examples — could improve results for technical queries.

## Quellen

- `agents/web-research.md` — agent definition with Step 1 instructions
- `skills/agent-web-research/SKILL.md` — MCP tool reference with pagination docs
- Eval session findings (2026-03-15): pageno=3 used 0/3 agents, science category underused
- Agent run metadata: Agent 4 (21 tool_uses), Agent 5 (35), Agent 6 (30)
