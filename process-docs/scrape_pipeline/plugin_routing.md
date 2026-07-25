# Plugin Routing

*Snapshot as of 2026-06 — historical process record; the live current state is the source code, not this file.*

## Current State

**No domain blocking.** `scrape_url` attempts to scrape any URL without restriction. `get_plugin_hint()` in `src/scraper/scrape_url.py` returns `""` unconditionally.

**PDF URLs:** when a `.pdf`-suffix URL is passed to `scrape_url`, `cli.py` detects it via `urlparse(url).path.lower().endswith(".pdf")` and returns the error `"PDF must be downloaded by the user: <url>"` without scraping. The user downloads PDFs themselves.

**Previously blocked domains** (github.com, raw.githubusercontent.com, reddit.com, arxiv.org, youtube.com, youtu.be) are now scraped like any other domain.

## Evidence

**Root cause of removal:**

1. **docs.github.com wrongly blocked.** The `host.endswith(".github.com")` subdomain branch caught rendered documentation pages on `docs.github.com`. The GitHub plugin (`get_file_content`) is for raw repo-file access only — it cannot serve rendered HTML docs. Blocking docs.github.com left no valid access path.

2. **Plugin availability ≠ scrape incompatibility.** The existence of a plugin for github/reddit/arxiv does not mean scraping is broken. Workers should choose the best tool per URL shape; a hard CLI-level block prevents informed choice.

3. **Product decision:** unrestricted scraping is the correct default. Plugin tools remain available and are often superior for their specific use cases (structured data, auth, large files), but the scraper must not preempt the choice.

## Open Questions

None — prior questions about huggingface.co, gist.github.com, and paperswithcode.com routing are moot given unrestricted scraping.

## Sources

None — internal decision, no external sources.
