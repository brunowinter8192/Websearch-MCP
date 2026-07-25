# Stack Exchange — Implemented (2026-05-04)

**Endpoint:** `https://api.stackexchange.com/2.3/search/advanced?site=stackoverflow&filter=withbody` (GET, JSON)
**Engine:** `src/search/engines/stack_exchange.py` — BaseEngine subclass, httpx, 4 req/min
**Smoke:** `dev/search_pipeline/10_stack_exchange_smoke.py` — 30-query baseline, report in `01_reports/se_smoke_*.md`

**Why Stack Exchange:** Programmatic Q&A content from stackoverflow.com. Complements general web engines with structured developer answers that rarely surface at the top of general search. Free API, no browser needed. `filter=withbody` returns the question body for real snippet content vs. pure metadata. Anonymous quota 300 req/day; 10k/day with free registered API key.

**Fields used:** `link` (URL), `title` (HTML-decoded), `body` (HTML stripped to plaintext, truncated 500 chars), `score`, `answer_count`, `tags` (fallback snippet when body absent).

**Smoke baseline (2026-05-04):** 15/30 OK (report deleted, see git history at 1ad627f)
- 15/30 OK — German queries (6× EMPTY expected), pydoll/crawl4ai/trafilatura/SPLADE niche queries EMPTY (no SO matches)
- No rate-limit block — anonymous 300/day quota not exhausted; 4 req/min token bucket paces correctly (59s wait every 4 queries)
- Live CLI harness: 26 results for "python asyncio best practices" with body snippets + preview

**Sources:** Stack Exchange API docs — `api.stackexchange.com/docs/search`
