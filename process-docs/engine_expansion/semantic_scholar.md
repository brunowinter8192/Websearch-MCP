# Semantic Scholar — Re-added via Browser Path (2026-05-07, DOM-drift fix 2026-05-08)

**Engine:** `src/search/engines/semantic_scholar.py` — BaseEngine subclass, pydoll Chrome browser, 4 req/min, ENGINE_MAX_RESULTS=10
**Endpoint:** `https://www.semanticscholar.org/search?q={q}` (no sort param — `&sort=...` causes HTTP 400)
**Smoke:** `dev/search_pipeline/21_semscholar_smoke.py`
**Class:** ACADEMIC, priority 4 (after openalex/crossref)
**Watchdog override:** 5.0s (CSR-React-hydration takes 0.5-2.5s post-navigate)

**Why re-added via browser:** API tier still blocked (verified 2026-05-07: 3 consecutive 429s + business-mail key gate). Browser path bypasses both — Web search UI accessible to anonymous users. Stealth probe: MILD severity (no Cloudflare/CAPTCHA on baseline queries).

**DOM-Drift fix (2026-05-08):** original `[data-test-id="paper-abstract-toggle"]` snippet selector returned 0 matches — SS replaced abstract toggles with TLDR summaries. New selector: `.tldr-abstract-replacement`. Plus SSR→CSR shift required `MAX_WAIT_CYCLES=5, WAIT_INTERVAL=0.5` (2.5s polling window) to catch React-rendered results. Container `div.cl-paper-row` and title `[data-test-id="title-link"]` selectors confirmed unchanged via `dev/search_pipeline/inspections/inspect_engine_dom.py` (new tooling for engine selector drift recovery, 329 LOC).
