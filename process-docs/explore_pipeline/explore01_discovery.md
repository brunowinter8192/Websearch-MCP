# Explore Pipeline Step 1: Site Discovery

*Snapshot as of 2026-06 — historical process record; the live current state is the source code, not this file.*

## Current State

**Code:** `src/crawler/crawl_site.py` — `discover_urls_playwright()` (BFS engine) + `crawl_site_workflow()` (CLI entry point + content crawl). `explore_site.py` and `filter_urls.py` were removed; `discover_urls_playwright` is now an internal function of `crawl_site.py` only, not exposed as a CLI tool.

**Method:** Single discovery method — `discover_urls_playwright()` in `crawl_site.py`. Manual BFS: `crawler.arun()` per frontier URL in a real Playwright browser; links extracted from `result.links.internal` (post-JS rendered DOM). No sitemap cascade, no prefetch BFS, no `BFSDeepCrawlStrategy`.

**Config:**
```python
DEFAULT_DELAY_S = 3.0            # delay_before_return_html
DEFAULT_PAGE_TIMEOUT_MS = 15000  # page_timeout per page
DEFAULT_DISCOVER_CONCURRENCY = 1 # sequential, WAF-safe default
wait_until = "domcontentloaded"  # fixed, not configurable
```

**Discovery flow (`discover_urls_playwright`):**
1. Normalize seed URL → init frontier deque + visited set.
2. Open one `AsyncWebCrawler` context for the full BFS.
3. Per batch (size = concurrency): `crawler.arun(url, config=run_cfg)` → extract `result.links.internal` → filter by domain + include/exclude substrings → enqueue new URLs.
4. **429 policy:** if a batch returns 429 → back off 5s (once); if second consecutive batch also 429 → stop, set `stop_reason="429_persistent"`. No retry loops.
5. **Stop reason** (D7 saturation signal) on exit:
   - `"frontier_exhausted"` — ran out of reachable links before hitting max_pages
   - `"max_pages_reached"` — capped; more pages likely exist → raise `--max-pages`
   - `"429_persistent"` — WAF stopped the run; retry with `--stealth` or after cooldown

**Stealth toggle:** `--stealth` enables `BrowserConfig(enable_stealth=True)` + `UndetectedAdapter` + `AsyncPlaywrightCrawlerStrategy` — mirrors Phase-2 in `src/scraper/scrape_url.py`. Off by default.

**Skill integration:** URL discovery is governed by the `capture-and-index` skill Phase 0 (worker-side guideline: `__NEXT_DATA__`-first → sitemap if usable → Playwright BFS fallback; worker writes /tmp scripts situationally). `discover_urls_playwright()` in `crawl_site.py` serves as the BFS implementation backing that fallback path.

## Evidence

### Playwright-per-page BFS vs HTTP BFS — Phase B recall probe

Script: `dev/explore_pipeline/05_playwright_bfs.py`
Report: `dev/explore_pipeline/05_reports/docs_github_rest_20260529.md`
Dataset: `dev/explore_pipeline/goldstandard/docs_github_rest.txt` (305 URLs, docs.github.com/de/rest)

| Strategy | Recall % | Matched | Time | ms/page | 429 |
|----------|----------|---------|------|---------|-----|
| HTTP BFS — crawl4ai BFSDeepCrawlStrategy (Phase A baseline) | 67.2% | 205/305 | 59.2s | 180ms | 0 |
| Playwright-per-page BFS — concurrency=1 (Phase B) | 81.3% | 248/305 | 1094.5s | 4112ms | 0 |

**+14.1pp recall** over HTTP BFS. Sequential concurrency (1) survived Cloudflare WAF without any 429.

### Mechanism verified

Single-page check: `https://docs.github.com/de/rest/agent-tasks` rendered with `wait_until=domcontentloaded` + `delay=3.0s` → `result.links.internal` contains `/de/rest/agent-tasks/agent-tasks` (46 internal links, React sidebar fully rendered). The rendering mechanism is correct.

### Navigation topology ceiling (81.3%)

Post-run diagnostic on seed page `/de/rest`: only 35 `/de/rest/*` links in rendered DOM. `agent-tasks`, `enterprise-admin`, `announcement-banners` not present. Sidebar is section-scoped: categories only appear in navigation when the user is within that section. The 18.7% gap is a navigation topology constraint, not a rendering failure. Knowingly accepted; superseded by __NEXT_DATA__ approach below.

### __NEXT_DATA__ nav-tree extraction — agentic discovery experiment

Script: `dev/explore_pipeline/06_nextdata_probe.py`  
Report: `dev/explore_pipeline/06_reports/gh_live_discovery_20260531_0256.md`  
Dataset: `dev/explore_pipeline/goldstandard/docs_github_rest.txt` (305 URLs)

| Strategy | Recall % | Matched | Time | Mechanism |
|----------|----------|---------|------|-----------|
| Playwright BFS (Phase B, above) | 81.3% | 248/305 | ~18 min | Playwright, 3s/page |
| __NEXT_DATA__ union — FPT only | 83.3% | 254/305 | 0.3s | 1 HTTP fetch |
| __NEXT_DATA__ union — FPT + GHEC | 98.0% | 299/305 | 0.5s | 2 HTTP fetches |
| __NEXT_DATA__ union — FPT + GHEC + GHES all (6 versions) | **100.0%** | **305/305** | **1.6s** | **8 HTTP fetches** |

**Method:** GitHub Docs is Next.js SSR. Every page embeds a `<script id="__NEXT_DATA__">` block
in the initial HTML containing the full nav tree (`props.pageProps.mainContext.sidebarTree`).
No browser needed. `allVersions` field lists all content variants; fetching each version's
REST root page and unioning their normalized sidebars gives complete coverage.

**Key finding:** The 18.7% BFS gap is entirely explained by version-scoped nav:
- GHEC (`enterprise-cloud@latest`): adds `enterprise-admin`, `announcement-banners`, `scim` + extra pages in 8 shared categories (36 net new)
- GHES 3.16 (oldest version): holds deprecated `projects-classic/*` + `repos/tags` not in any newer sidebar (6 net new)
- Noise: 11 URLs (version root pages + scim — all return HTTP 200, outside goldstandard scope)

### HTTP BFS is always HTTP-speed regardless of wait_until

Phase A proof: `BFSDeepCrawlStrategy` with `wait_until="networkidle"` or `prefetch=False` still ran at 0.18s/page (HTTP speed). Changing wait_until in the old code has zero effect on link extraction. Prefetch BFS: parallel HTTP requests → Cloudflare 429 after ~100 reqs/session.

### Redirect resolution (kept)

HEAD-request before BFS. Fixes domain-mismatch for redirect chains (e.g. `docs.anthropic.com` → `platform.claude.com`). Still required since `discover_urls_playwright`'s domain filter uses the resolved domain.

## Open Questions

- Concurrency >1 WAF behavior: does `--concurrency 3` on docs.github.com trigger 429 without stealth?
- `__NEXT_DATA__` key-path portability: `props.pageProps.mainContext.sidebarTree` is GitHub-Docs-specific — what's the discovery heuristic for the nav-tree key on an unknown Next.js site?

## Sources

- `dev/explore_pipeline/05_playwright_bfs.py` — Phase B probe implementation
- `dev/explore_pipeline/05_reports/docs_github_rest_20260529.md` — Phase B run report
- `dev/explore_pipeline/04_render_recall.py` — Phase A HTTP BFS baseline
- `dev/explore_pipeline/06_nextdata_probe.py` — __NEXT_DATA__ discovery implementation
- `dev/explore_pipeline/06_reports/gh_live_discovery_20260531_0256.md` — __NEXT_DATA__ run report (305/305)
- Crawl4AI issue #1665 — BFSDeepCrawlStrategy captures page before JavaScript loads
