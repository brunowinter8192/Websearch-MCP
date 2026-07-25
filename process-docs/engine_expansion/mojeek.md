# Mojeek — Implemented (2026-05-03)

**Endpoint:** `https://www.mojeek.com/search?q={query}&safe=1` (GET, server-rendered HTML, no JS required)
**Engine:** `src/search/engines/mojeek.py` — BaseEngine subclass, pydoll Chrome, 4 req/min
**Smoke:** `dev/search_pipeline/06_mojeek_smoke.py` — 30-query baseline, report in `01_reports/mojeek_smoke_*.md`

**Why Mojeek:** Own crawler index (not Bing-derivative). After Google + DDG, the first engine with a genuinely independent index in the stack. Free, non-commercial-friendly, no API-key, no free-tier limit.

**Phase-A DOM probe findings (2026-05-03):**
- Selectors verified live: `ul.results-standard > li > a.ob` (10 hits), `li h2 a` (title), `li p.s` (snippet)
- `a.ob.href` is direct destination URL — no redirect wrapper, no `_clean_url` needed
- No CAPTCHA form (`captcha_cf=0`, `captcha_gen=0`), no cookie banner (`cookie_ban_elements=0`) on first contact
- In-page "×Mojeek User Survey" notification does not block result parsing
- `page_title` pattern: `"{query} - Mojeek Search"` — used in `_derive_status` BLOCKED check

**Smoke baseline (2026-05-03):** 7/30 OK at 0-delay stress (report deleted, see git history at 1ad627f)
- 7/30 OK at 0-delay stress — 403 block kicks in at query 10 (~9 queries in 7.5s = ~1.2 req/s burst)
- 2× SUSPECT: valid results (10 hits) with low domain diversity (4 domains) — not a detection signal
- Production 4 req/min limiter (1 query per 15s) stays well within burst threshold
- Nav timing queries 1-9: mean 286ms / max 1033ms

**Sources:** `searxng/searxng searx/engines/mojeek.py` (selector reference, s-param note)
