# M1 — Internal rename searxng-cli → websearch

As of 2026-07-25, milestone 1 of a multi-milestone project rename landed: every INTERNAL self-reference to the project renamed from `searxng-cli`/`SearXNG` to `websearch`. Trigger: the SearXNG stack was removed in an engine-cut on 2026-04-15 — the codebase had been a self-built web-search/scrape/news CLI since, wearing a stale name. Directory rename, GitHub repo, plugin marketplace, RAG collections, and external consumers are later milestones, deliberately untouched here.

## Scope decided

Explicit deliverables (plugin manifest, 3 skill dirs + SKILL.md content, `.rag-docs.json` collection, 2 named env vars, cache/session/lock dirs, one help-text string, 2 path comments, `cli.py` description, all `DOCS.md` present-tense self-refs) were extended by investigation to 4 additional items, confirmed before implementation:

1. **4 more `SEARXNG_*` env vars** beyond the 2 explicitly named, found by grepping the whole tree for the `SEARXNG_` prefix: `SEARXNG_HEADED` (`src/search/browser.py`), `SEARXNG_QUERY_LOG_PATH` (`src/search/query_logger.py`), `SEARXNG_SCRAPE_LOG_PATH` (`src/scraper/scrape_logger.py`), `SEARXNG_LOG_RETENTION_DAYS` (`src/log_janitor.py`) — same self-naming convention, all read by active `src/` code. Renamed to `WEBSEARCH_*`, with matching `DOCS.md` "Reads:" line updates in `src/DOCS.md`, `src/search/DOCS.md`, `src/scraper/DOCS.md`.
2. **A second `box_lock.py`** at `dev/news_pipeline/theblock/acquire_pipe/box_lock.py`, independent of the explicitly-named `src/news/engine/proxy_pool/box_lock.py`, defining the same `LOCK_DIR = ~/.searxng-cli-locks`. Renamed for lock-namespace consistency — it is active pipeline code (imported by `acquire_pipe.py`), not a historical report, so the dev/** negative-scope exclusion didn't apply.
3. **Shell-variable rename vs. path-literal preservation**: `skills/websearch-capture-and-index/SKILL.md` had `SEARXNG=/Users/.../cli/searxng-cli`. The variable name became `WEBSEARCH=`; the path VALUE stayed `.../cli/searxng-cli` since the on-disk directory isn't renamed until a later milestone. This split (identifier renamed, literal path preserved) is the general pattern for any doc that both self-references the project AND points at the still-`searxng-cli`-named directory.
4. **Skill title convention**: sibling skill H1s carry no product name (`# Capture-and-Index — Skill`, `# PDF → MD → Index — Skill`). `# SearXNG Web Research — Skill` was normalized to `# Web Research — Skill` (dropped the name entirely) rather than inserting "Websearch", matching the existing pattern.

## Explicitly NOT renamed (verified via residual grep)

Grepping `-ri searxng` over all active surfaces post-rename returns exactly 4 hits, all external-SearXNG-software or historical references, not project self-naming:

- `src/crawler/crawl_site.py:296` — `"docs.searxng.org": "searxng"`, a domain-mapping key for crawling SearXNG's OWN documentation site (unrelated external software).
- `src/search/engines/scholar.py:36` — `(bead searxng-f3i)`, a historical ticket-ID comment; renaming it would falsify the migration history it records (same write-once logic as process-docs, applied to a code comment).
- `skills/websearch-capture-and-index/SKILL.md:193` — "Sphinx-generated docs (SearXNG, ReadTheDocs, ...)", a pattern-recognition example naming SearXNG's docs site as one of several Sphinx-doc examples.
- `skills/websearch-capture-and-index/SKILL.md:127` — the `WEBSEARCH=.../searxng-cli` path literal from decision 3 above.

Also confirmed out of scope: `dev/cleanup/clean_web_searxng.py` and its `DOCS.md` entry — these clean the SearXNG-website RAG collection (`RAG/data/documents/searxng/`), an external-content cleanup tool, not project self-naming. `dev/scrape_pipeline/garbage_eval/DOCS.md`'s "fires a live SearXNG search" line was flagged as ambiguous (could read as either "uses the project's search" or a stale reference to the old SearXNG backend) but left untouched — low-value, ambiguous, and outside the explicit deliverable list.

One dead env var surfaced during investigation: `SEARXNG_PROJECT_ROOT` (now `WEBSEARCH_PROJECT_ROOT` in `.env.example`) is set by `dev/scrape_pipeline/garbage_eval/10_live_garbage_test.py` but consumed by no active `src/` code as of this rename — a vestige from the pre-engine-cut era. Renaming it in `.env.example` per the explicit deliverable list was a no-op functionally; the dev script that sets it was left untouched (dev/** negative scope) with zero behavioral consequence either way.

## Verification performed

- Residual `grep -ri searxng` over `cli.py`, `src/`, `skills/`, `.claude-plugin/`, `.rag-docs.json`, `.env.example`, top-level `DOCS.md` → 4 hits, all itemized above as intentional.
- CLI smoke test: `./venv/bin/python cli.py search_web "test query"` via the worktree, using the venv at the original (still `searxng-cli`-named) repo root → exit 0, correct engine-breakdown output including the renamed `websearch search_engine_drilldown` hint text.
- Import-level check: `cache.CACHE_DIR`, `browser.SESSION_DIR`, `box_lock.LOCK_DIR`, `log_janitor.get_retention_days`, `query_logger.log_query`, `scrape_logger.log_scrape`, `crossref._fetch_results`, `pipeline.PROJECT_ROOT`, `coindesk.config.PROJECT_ROOT` all imported and resolved to the renamed values (`~/.cache/websearch`, `~/.websearch/browser-session`, `~/.websearch-locks`).
- NOT verified: actual runtime creation of the renamed cache/session/lock directories under a live proxy-pool or browser run — the smoke test didn't exercise those code paths. Per the migration note carried into this milestone, these directories start empty and regenerate; no migration code was added.

## Mechanical note

`gcommit`'s secrets skip-list excludes `.env*` files, so `.env.example` silently did not stage on the first commit — caught by checking `git status` post-commit, staged and committed separately with plain `git add`/`git commit`. Any future task touching `.env.example` under this repo's `gcommit` wrapper should expect the same and verify explicitly.
