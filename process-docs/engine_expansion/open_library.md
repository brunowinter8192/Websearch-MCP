# Open Library — Implemented (2026-05-08)

**Endpoint:** `https://openlibrary.org/search.json?q={q}&limit={n}` (GET, JSON, no key)
**Engine:** `src/search/engines/open_library.py` — BaseEngine subclass, httpx, 4 req/min
**Smoke:** `dev/search_pipeline/22_openlibrary_smoke.py`, `23_books_ab_smoke.py` (A/B pool-widening)
**Class:** GENERAL + `_BOOKS_ENGINES` whitelist (receives `+book` modifier in `--books` mode; modifier excluded for OL itself via `query_modifier_map` filter — it is already a book catalog)
**ENGINE_MAX_RESULTS:** 100 (API supports 1000+, latency server-dominated 1.4-5.8s, 100 is sweet spot)
**Watchdog override:** 6.0s (server-dominated latency, 3.6s default produced ~35% TIMEOUT rate)
**Inner httpx timeout:** `httpx.AsyncClient(timeout=6.0)` — aligned with watchdog override. Without coordination (initial implementation had timeout=3.6) the inner httpx fires before the watchdog → status ERROR instead of TIMEOUT → loses diagnosability.

**Why Open Library:** `--books` mode pool was underwhelming with 3 general engines (google/ddg/mojeek) all returning the same Manning IR textbook for "introduction to information retrieval" — 9 URLs, all same book. Open Library brings a structurally INDEPENDENT source: structured book catalog (~50M+ works) with metadata web-engines don't expose (author, year, edition_count, ebook_access).

**A/B pool-widening empiry (2026-05-08):**
- 9/10 book queries get meaningful pool widening (≥3 OL URLs)
- 81.2 unique OL URLs avg per completed book query
- 40% ebook availability (public/borrowable/printdisabled)
- "introduction to information retrieval" --books: 11 OL URLs out of 20 (vs 0 OL URLs pre-fix), distinct works: Manning, Rowley, IBM 1971, Melucci 2015, etc.

**Snippet template:** `f"{author} ({year}) — {edition_count} eds, ebook: {ebook_access}"` — 4-pillar (author/year/editions/ebook) format that web-engines can't replicate.
