# Lobsters — Implemented (2026-05-03)

**Endpoint:** `https://lobste.rs/search?q={query}&what=stories&order=relevance` (GET, server-rendered HTML, no JS required)
**Engine:** `src/search/engines/lobsters.py` — BaseEngine subclass, pydoll Chrome, 4 req/min
**Smoke:** `dev/search_pipeline/07_lobsters_smoke.py` — 30-query baseline, report in `01_reports/lobsters_smoke_*.md`

**Why Lobsters:** Link-aggregator focused on tech/programming. Curated community with high signal-to-noise for developer queries. Complements Google/DDG/Mojeek with community-filtered content rather than crawl-ranked results. Free, no auth, no API-key, no bot challenge observed.

**Phase-A DOM probe findings (2026-05-03):**
- Selectors verified live: `li.story` (20 hits), `a.u-url` (20 hits, href = direct destination URL), `a.domain` (domain-as-displayed string)
- `a.u-url.href` is direct destination URL — no redirect wrapper, no `_clean_url` needed
- No CAPTCHA form, no cookie banner, no bot-block on first contact. html_bytes = 47870 (normal page).
- `page_title` pattern: `"Search | Lobsters"` — used in `_derive_status` BLOCKED check (`"Lobsters" not in title`)
- No URL redirect on navigation — `current_url` matches input URL exactly
- `a.domain` shows Lobsters' display domain which may include path prefix for GitHub (e.g. `github.com/joaocarvalhoopen`) — correct link-aggregator behavior, not a parsing error

**Snippet caveat:** Lobsters search page has no body text — only title + domain + tags + comments-count + submitter. Snippet = `a.domain` (domain-as-displayed) by design. `og:description` from preview-fetch fills the description field downstream.

**Smoke baseline (2026-05-03):** 16/30 OK at 0-delay stress (report deleted, see git history at 1ad627f)
- 16/30 OK at 0-delay stress — 11× EMPTY (German queries + content-empty: crawl4ai, pydoll, epidemiology, climate change), 3× SUSPECT (3 results, low domain diversity)
- No rate-limit block observed — EMPTY = Lobsters simply has no matching content for those queries
- Nav timing: mean 488ms / max 1639ms; DOM-wait mean 477ms / max 613ms
- Production 4 req/min limiter stays within burst threshold

**Sources:** `searxng/searxng searx/engines/lobsters.py` (selector reference)
