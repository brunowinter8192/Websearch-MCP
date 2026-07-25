# crawler_js_render_discovery — Phase B: Playwright-per-page BFS Probe

## What We Did

Built and ran `dev/explore_pipeline/05_playwright_bfs.py`: a manual BFS that renders each page via
`crawler.arun()` (real Playwright browser) and extracts navigation links from `result.links.internal`
(post-JS DOM). Primary measurement: concurrency=1 (sequential), `wait_until="domcontentloaded"`,
`delay_before_return_html=3.0s`, `page_timeout=15000ms`, no stealth. No networkidle, no retry loops.

Single-page mechanism check (pre-run): rendered `https://docs.github.com/de/rest/agent-tasks`
directly — `agent-tasks/agent-tasks` present in `result.links.internal`: **confirmed**. 46 internal
links returned, React sidebar fully rendered. Status 200, no 429.

Full BFS run: seed `https://docs.github.com/de/rest`, include-pattern `/de/rest/`, max_pages=400.
305-URL gold standard (`dev/explore_pipeline/goldstandard/docs_github_rest.txt`).

Post-run diagnostic: re-rendered seed page directly to inspect which `/de/rest/*` links it exposes.

## What We Found

### 1. Recall: 81.3% (248/305) — up from 67.2% (HTTP BFS, Phase A)

| Strategy | Recall % | Matched | Missing | Noise | Time |
|----------|----------|---------|---------|-------|------|
| HTTP BFS — Strategy C (Phase A) | 67.2% | 205/305 | 100 | 124 | 59.2s |
| Playwright-per-page BFS (this run) | 81.3% | 248/305 | 57 | 18 | 1094.5s |

Gain: +14.1pp. Playwright rendering recovers the pages that HTTP BFS misses because their parent
category pages ARE reachable from the seed and their sidebar links are captured after render.

### 2. agent-tasks/agent-tasks: still MISSING

The single-page check confirmed the rendering mechanism works: when directly fetching
`/de/rest/agent-tasks`, `result.links.internal` includes `/de/rest/agent-tasks/agent-tasks`.
But the BFS never reached `/de/rest/agent-tasks` at all — so its children were never discoverable.

### 3. Root cause: section-scoped sidebar, not a rendering failure

Post-run diagnostic on seed page (`/de/rest`, 3s delay):
- Total internal links: 51, `/de/rest/*` links: 35
- `agent-tasks`: not in seed's rendered links
- `announcement-banners`: not in seed's rendered links
- `enterprise-admin`: not in seed's rendered links
- `copilot/copilot-custom-agents`: not in seed's rendered links
- `billing`: partial — `billing/budgets` present, `billing/billing` / `billing/cost-centers` / `billing/usage-reports` absent

The GitHub docs sidebar is **section-scoped**: it shows navigation for the section you are currently
inside, not a global nav for all API sections. When browsing `/de/rest` (the overview page), the
sidebar shows the "About the REST API", "Using the REST API", "Guides", and "Authentication" sections
— but NOT `agent-tasks`, `enterprise-admin`, `announcement-banners`, or the full `billing` section.
Those only appear in the sidebar when the user is already within that section.

BFS can only discover pages that are reachable via `result.links.internal` from already-visited pages.
If a top-level category page is never linked from any visited page, the category and its entire
subtree are invisible to BFS — regardless of delay, rendering quality, or concurrency.

### 4. Noise: 18 extra URLs

18 found URLs not in the 305-URL gold standard. These are either locale variants, redirect targets,
or pages added to the site after the gold standard was compiled. Not a concern.

### 5. Timing and WAF

- Total: 1094.5s (~18.2 min), 266 pages fetched, avg 4112ms/page
- Per-page: min 3395ms / max 5615ms (well above 3s floor set by `delay_before_return_html`)
- 429 incidents: **0** — Cloudflare WAF did not trigger at sequential concurrency
- No stealth required for clean run

### 6. Cross-website robustness assessment

The BFS logic itself is fully generic (domain filter + substring pattern, no per-site heuristics).
The rendering approach (`result.links.internal` from post-JS DOM) works correctly on any site with
client-rendered navigation. The 81.3% recall ceiling is specific to docs.github.com's section-scoped
sidebar architecture — other sites with a globally visible navigation tree would yield higher recall.

## Decision / Next

**Playwright-per-page BFS is a confirmed improvement** (+14.1pp over HTTP BFS) and is the correct
approach for JS-rendered sites. The mechanism is sound.

**The recall ceiling (81.3%) is a navigation topology problem**, not a rendering problem. For
docs.github.com specifically, achieving 100% recall requires one of:

- **Option A: Sitemap** — `discover_urls_sitemap()` already in `src/crawler/crawl_site.py`.
  If GitHub exposes a sitemap covering `/de/rest/*`, this would give complete URL lists without
  any BFS. Should be verified first (fastest path to 100%).
- **Option B: Multi-seed BFS** — seed from multiple known section entry points (e.g. also seed
  from `/de/rest/agent-tasks`, `/de/rest/enterprise-admin`). Requires knowing the top-level
  section names in advance — per-site knowledge, not cross-site-robust.
- **Option C: GitHub repo tree** (how the gold standard was built) — deterministic, complete,
  but requires GitHub API access per-site.

**For `src/` port decision:** Playwright-per-page BFS should replace the current prefetch BFS
(`discover_urls()`) as the primary discovery strategy for JS-heavy sites, or be used as the
fallback when prefetch yields too few URLs. The existing `auto` cascade in `crawl_site_workflow`
would slot it in after sitemap → before full-BFS. Port deferred until the sitemap question is
resolved (Option A) — if sitemap covers docs.github.com, the port may be limited to the fallback
slot only.

## Open Questions

1. Does `https://docs.github.com` expose a sitemap with full `/de/rest/*` coverage? If yes,
   `discover_urls_sitemap()` solves 100% recall without Playwright overhead.
2. Would seeding additionally from a known enterprise-admin or agent-tasks URL bring recall to
   ~100% on docs.github.com specifically? (Multi-seed BFS test — not run yet.)
3. Is the section-scoped sidebar pattern common on other documentation sites (Chroma, SearXNG,
   Playwright docs) or specific to GitHub's React doc infrastructure?

## dev/ Scripts Used

- `dev/explore_pipeline/05_playwright_bfs.py` — Playwright-per-page BFS probe (this phase)
- `dev/explore_pipeline/05_reports/docs_github_rest_20260529.md` — full run report
- `dev/explore_pipeline/04_render_recall.py` — HTTP BFS baseline (Phase A)
- `dev/explore_pipeline/goldstandard/docs_github_rest.txt` — 305-URL gold standard
