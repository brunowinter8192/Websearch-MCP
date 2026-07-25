# Trafilatura Reference Indexing — Initial Exploration

**Date:** 2026-05-24
**Session:** end-of-day Phase 4 test of the consolidated web-research pipeline
**Status:** URL discovery + filtering complete. Mass-scrape + cleanup + index pending next session.

---

## Scope

Index the Trafilatura library's official documentation (Sphinx-hosted at `trafilatura.readthedocs.io/en/latest/`) into a project-reference RAG collection. Collection name: `Trafilatura_Reference`. Purpose: long-term reference material for the library — accessible via `rag-cli search_hybrid "<query>" Trafilatura_Reference` without needing to re-scrape.

The indexing is **independent of any benchmarking concern** — clarified mid-session 2026-05-24. The PruningContentFilter-vs-Trafilatura benchmark applies only to on-the-fly single-URL scrapes via `scrape_url` (filtered mode). The crawling-and-indexing pipeline ALWAYS uses `scrape_url_raw` (no filter, raw markdown), so the cleanup-and-index workflow does not bias the comparison either way.

## Why Trafilatura specifically

- Tagged as a future-work indexing target for months
- THE library we will benchmark `PruningContentFilter` against eventually (separate scope, not this work)
- Test-bed for the consolidated `web-research` SKILL Mode 1 (Web-MD Capture) — first end-to-end run since the cleanup-and-index merger
- Sphinx-generated docs trigger our empirically-validated 5-shape cleanup profile (Sphinx-Specific: header avg 10.7 LOC, footer 52.6 LOC, 37% noise) — high-confidence cleanup path

## Discovery — sitemap strategy result (2026-05-24 02:37 UTC)

Command run: `searxng-cli explore_site "https://trafilatura.readthedocs.io/en/latest/" --output /tmp/trafilatura_urls.txt`

Strategy chosen: `sitemap` (confirmed via cli.log `INFO __main__:194 - explore_site complete: strategy=sitemap domain=trafilatura.readthedocs.io urls=41 output=/tmp/trafilatura_urls.txt`).

Output: 41 URLs total. Breakdown:

| Category | Count | Decision | Rationale |
|---|---|---|---|
| Real doc pages (background, quickstart, usage*, tutorial*, settings, corefunctions, ...) | 28 | **KEEP** | Canonical content for indexing |
| `genindex.html` | 1 | **DROP** | Auto-generated alphabetical cross-reference index; zero original content, only links to other pages |
| `_modules/trafilatura/*.html` (Sphinx source-code listings) + `_modules/index.html` | 12 | **DROP** | Library's Python source rendered as HTML with `[docs][]` markers; not informational documentation; source-code browsing is better-served via GitHub when needed; would inflate the index by 30% with non-doc material |

Filtered list (28 URLs) below.

## The 28 URLs to index

Sphinx Sphinx default URL pattern: each file under `/en/latest/<name>.html`.

```
background.html
compendium.html
corefunctions.html
corpus-data.html
crawls.html
deduplication.html
downloads.html
evaluation.html
index.html
installation.html
quickstart.html
settings.html
sources.html
troubleshooting.html
tutorial-dwds.html
tutorial-epsilla.html
tutorial0.html
tutorial1.html
tutorial2.html
tutorials.html
url-management.html
usage.html
usage-api.html
usage-cli.html
usage-gui.html
usage-python.html
usage-r.html
used-by.html
```

Absolute URL form: prefix each line with `https://trafilatura.readthedocs.io/en/latest/`. Next session can either re-run `explore_site` and re-filter (cheap, ~5s wallclock, sitemap is stable), or `printf` the absolute URLs from the list above directly into `/tmp/trafilatura_urls.txt`.

## Next-Session Workflow

Concrete steps to execute next session:

1. **Re-generate filtered URL list if /tmp got wiped** — run `searxng-cli explore_site "https://trafilatura.readthedocs.io/en/latest/" --output /tmp/trafilatura_urls.txt`, then filter to 28 per the table above (or grep-out `_modules` and `genindex` mechanically).
2. **Spawn worker with the consolidated web-research skill Mode 1 Web-MD Capture.** Worker prompt is short (per skill template): activate `web-research` skill, MODE=`web-md`, INPUT=`<absolute path to filtered url list>`, COLLECTION=`Trafilatura_Reference`, OUTPUT_DIR=`~/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/Trafilatura_Reference/`.
3. **Worker executes** Phase 0 (crawl all 28 URLs via crawl_site `--url-file`), Phase 1 (Sphinx cleanup profile — should be a clean trigger, ~37% noise stripped per empirical baseline), Phase 2 (index into `Trafilatura_Reference`, lock-aware polling).
4. **Verify** via `rag-cli search_hybrid "url discovery sitemap" Trafilatura_Reference --top-k 3` — top hit should be `sources.html` or `url-management.html`.

## Pending decisions (none open)

All design questions are resolved:
- Domain target: trafilatura.readthedocs.io ✓
- Collection name: `Trafilatura_Reference` ✓
- URL filter: 28 docs, drop genindex + _modules ✓
- Workflow: existing web-research Mode 1 (no changes needed) ✓

## Sources cited

- `src/explore/explore_site.py` — sitemap → BFS cascade discovery architecture
- Central FileHandler-only logging config ensures the upcoming worker run won't pollute stdout with crawl4ai or per-engine warnings (2026-05-24)

---

**Superseded 2026-05-24:** collection name corrected from `Trafilatura_Reference` to `searxng_reference` per project convention.
