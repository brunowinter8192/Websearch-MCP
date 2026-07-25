# crawler_js_render_discovery — Phase A: Recall Probe

## What We Did

Designed and ran a recall probe (`dev/explore_pipeline/04_render_recall.py`) comparing three crawl4ai BFS strategies against a 305-URL gold standard derived from the github/docs `content/rest` repo tree. Goal: determine whether JS rendering (`networkidle` vs `domcontentloaded`) explains the ~75 URL gap between production `explore_site` output (~230) and the true page count (~305) for `https://docs.github.com/de/rest`.

Gold standard: `dev/explore_pipeline/goldstandard/docs_github_rest.txt` (305 URLs, deterministic from repo tree).

Strategies:
- A: `prefetch=True + domcontentloaded` (mirrors `discover_urls` in production)
- B: `prefetch=True + networkidle`
- C: `prefetch=False + networkidle` (mirrors `crawl_bfs` structure)

## What We Found

### 1. crawl4ai BFS is HTTP-based regardless of wait_until

`BFSDeepCrawlStrategy` uses an HTTP client for link extraction at every depth, regardless of `wait_until` or `prefetch` settings. Confirmed empirically: Strategy C (`prefetch=False + networkidle`) ran at 0.18s/URL — HTTP speed — not 2–5s/URL expected for real Playwright rendering. Changing `wait_until` in `discover_urls` or `crawl_bfs` would have **zero effect** on recall.

The original hypothesis (switch to `networkidle` fixes the recall gap) is therefore NOT testable through `BFSDeepCrawlStrategy`.

### 2. GitHub Cloudflare WAF rate-limits prefetch=True immediately

`prefetch=True` sends parallel HTTP prefetch requests. GitHub's Cloudflare WAF returns 429 on the seed URL after ~100 requests from a session, terminating BFS with 1 URL found. Strategies A and B were both rate-limited in this probe. Strategy C (sequential HTTP) survived.

The production measurement of ~230 URLs must have run during a window without rate limiting (or with a lower max_pages cap that finished before triggering the limit).

### 3. Measured recall: Strategy C = 67.2% (205/305)

Strategy C (the only strategy that ran without rate limiting): found 329 total URLs, 205 matched gold, 124 noise, 100 missing. Time: 59.2s.

The production baseline (~230 gold) is higher than measured C (205) — likely because A (prefetch=True) makes parallel requests and covers more pages in the same time window when not rate-limited.

### 4. Missing URL pattern confirms client-rendered sidebar hypothesis

The 100 missing URLs fall into two groups:

**Category index pages** (e.g. `/de/rest/actions`, `/de/rest/agent-tasks`) — these appear exclusively in the sidebar navigation, which is a React component rendered client-side. HTTP BFS cannot see them.

**Leaf pages under missing categories** (e.g. `/de/rest/agent-tasks/agent-tasks`) — accessible only via the category index. If the category is missing, its children are unreachable by BFS.

`agent-tasks/agent-tasks` specifically: missing because `agent-tasks` (the category page) is missing, and it is only linked from the client-rendered sidebar.

### 5. Regression check

| Domain | A | C | Notes |
|--------|---|---|-------|
| docs.searxng.org | 50 URLs / 3.9s | 49 URLs / 5.8s | Static Sphinx — same recall, C 1.5× slower |
| docs.trychroma.com | 1 URL (rate-limited) | 70 URLs / 76.2s | C immune to this Cloudflare; 1.09s/URL suggests Playwright activated |

No regression on static sites. chroma_docs C result (1.09s/URL) is an interesting outlier — may indicate `prefetch=False` triggers Playwright rendering on JS-heavy sites where HTTP returns minimal content.

### 6. dev/ scripts used

- `dev/explore_pipeline/04_render_recall.py` — main probe (three strategies, recall computation, regression check, report generation)
- `dev/explore_pipeline/goldstandard/docs_github_rest.txt` — 305-URL gold standard fixture

## Decision / Next

**Original target (change wait_until to networkidle): INVALID.** Changing `wait_until` in `BFSDeepCrawlStrategy` has no effect since BFS is HTTP-based.

**Actual fix direction: Playwright-per-page BFS.** Replace or supplement `BFSDeepCrawlStrategy` with a custom BFS that uses `crawler.arun()` per URL and extracts `result.links.internal`. With `wait_until="networkidle"`, `links.internal` is populated from the fully rendered DOM — including the React sidebar navigation — which would reveal the missing category pages and their children.

**Estimated recall gain:** +75–100 URLs, from ~67–75% to ~100% on docs.github.com/de/rest.

**Time trade-off:** ~2–5s/page × 305 pages = 10–25 min per full crawl (vs 59s for HTTP BFS). Acceptable for `explore_site` which is a one-time indexing operation.

**Open question:** chroma_docs/C ran at 1.09s/URL, which suggests `prefetch=False + networkidle` MAY activate Playwright on some sites (where HTTP returns too little content and crawl4ai falls back). This needs verification — if confirmed, `prefetch=False + networkidle` could be the fix without requiring a custom BFS.

**Phase B:** Implement `discover_urls_playwright` probe in `dev/explore_pipeline/` using the `crawler.arun() + links.internal` approach. Verify `agent-tasks/agent-tasks` is found. Measure time per page. Then port to `src/crawler/crawl_site.py` if confirmed.
