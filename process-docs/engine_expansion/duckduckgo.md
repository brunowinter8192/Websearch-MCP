# DuckDuckGo — Implemented (2026-05-03)

**Endpoint:** `https://html.duckduckgo.com/html/?q={query}&kl=wt-wt` (GET, server-rendered HTML, no JS required)
**Engine:** `src/search/engines/duckduckgo.py` — BaseEngine subclass, pydoll Chrome, 4 req/min
**Smoke:** `dev/search_pipeline/04_ddg_smoke.py` — 30-query baseline, report in `01_reports/ddg_smoke_*.md`

**Phase-A DOM probe findings (2026-05-03):**
- Selectors verified live: `#links > div.web-result` (containers), `h2 a` (title+href), `a.result__snippet` (snippet)
- No consent banner on first contact — no CDP cookie injection needed
- No bot challenge (`form#challenge-form` = 0) with real Chrome + Mac UA
- URL cleaning required: `a.href` → `https://duckduckgo.com/l/?uddg=<encoded_target>` → extract `uddg` param
- Sec-Fetch-* headers sent automatically by Chrome via `Page.navigate` — no `Network.setExtraHTTPHeaders` call

**Sources:** `searxng/searxng searx/engines/duckduckgo.py` (selector reference, header rationale)
