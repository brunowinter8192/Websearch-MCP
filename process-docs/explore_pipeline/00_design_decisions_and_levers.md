# crawler_js_render_discovery — Design Decisions & Lever Trade-offs

Framing doc for the topic. Empirical phase results: Phase A (HTTP BFS), Phase B (Playwright-per-page). This file = architectural decisions + time↔completeness lever analysis + hard constraints + open points, captured from the design discussion.

## Problem

`searxng-cli explore_site` on `https://docs.github.com/de/rest` finds only ~230 of ~305 real pages. The 305 is a deterministic gold standard derived from the `github/docs` `content/rest` repo tree (`dev/explore_pipeline/goldstandard/docs_github_rest.txt`). Repo-derivation is a one-off WORKAROUND — most doc sites have no backing repo. Goal: a discovery method that is **reliable cross-website**, not a per-site crutch.

## Investigation arc

1. No sitemap on docs.github.com (`/sitemap.xml` → 404) → falls to prefetch BFS → SPA (Next.js) nav links are client-rendered → `BFSDeepCrawlStrategy` extracts links via HTTP (proven: 0.18s/page) → JS-rendered links never seen → ~67–75% ceiling (Phase A). External convergence: crawl4ai issue #1665 + IR textbook.
2. Playwright-per-page BFS (`crawler.arun()` + `result.links.internal` from rendered DOM) → 81.3% (248/305), +14pp, 0×429 sequential (Phase B). Rendering mechanism confirmed (single-page check: the link IS in the rendered DOM).
3. Remaining ~19% gap is NOT rendering — it is navigation topology (section-scoped sidebar; categories not linked from seed). See critical open point 1.

## Decisions

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D1 | Discovery method = **Playwright-per-page BFS** (single method). Custom BFS: `crawler.arun(url)` per frontier URL → extract `result.links.internal` from rendered DOM → enqueue. | Correct-by-construction (sees links like a browser). Cross-website TRUST: future sites have no gold standard, so the method must be right by design, not per-site-tuned. | **PORTED to src/ this session.** Phase B: 81.3% (+14pp over HTTP). |
| D1b | REJECTED: cheap `delay_before_return_html` on existing `BFSDeepCrawlStrategy`. | BFS link-extraction is HTTP-structural (180ms proof) — delay affects content capture, not link discovery. No cross-website trust even if it worked. | Rejected. |
| D2 | REMOVE the sitemap cascade. | Cascade trusts a sitemap ≥ `SITEMAP_MIN_THRESHOLD` (5) and STOPS → an incomplete sitemap silently swallows content (documented: ReadTheDocs root-only, Cookiebot homepage-only). | **DONE — cascade removed in src-port.** |
| D2a | drop sitemap ENTIRELY vs ADDITIVE union. | Union can only ADD (never swallow) + catches orphan pages → strictly ≥ completeness. But adds a path. | **RESOLVED: drop ENTIRELY** (user: only Playwright, single path). Additive-union kept as a FUTURE lever if the coverage gap forces it. |
| D3 | Wait = `domcontentloaded` + fixed `delay_before_return_html` + explicit `page_timeout`. **NO `networkidle`.** | `networkidle` unbounded → waiting loops (telemetry/polling sites). HARD user constraint. | Fixed in port. |
| D4 | 429 policy = back-off ONCE, then STOP + report. No retry loops. | HARD user constraint: no waiting/retry loops. Incomplete-then-rerun preferred over blind waiting. | Fixed in port. |
| D5 | Concurrency. Probe shipped sequential (=1, WAF-safe). | User wants parallelism as a speed knob (→10), but 10 = the load that tripped the WAF. | **Shipped sequential.** Concurrency tuning = critical open point 2 (runtime). |
| D6 | GH config (max_pages/depth/include-pattern/delay) = baseline defaults for future crawls. | One validated baseline, tune per saturation signal. | Agreed. |
| D7 | **Saturation/stop-reason message** in output. | Cross-website "did we get everything?" — report WHY discovery stopped. | Ported with the method. |

## Lever trade-offs (within Playwright-per-page BFS)

| Lever | Trades | Shipped | Notes |
|-------|--------|---------|-------|
| `delay_before_return_html` | **time ↔ completeness (the real dial)** | 3.0s | +X sec EVERY page. ~3s sweet spot (#1665: 0s partial, 3s full, 5s/20s no gain). With no networkidle, the ONLY guard for slow-rendering pages → raise for slower sites. |
| `page_timeout` | worst-case load bound | 15s | Ceiling for the LOAD phase (nav→domcontentloaded), NOT the render wait. Healthy pages never hit it. Distinct clock from delay (see Parameter semantics). |
| concurrency | **wall-clock ↔ WAF/429 risk** | 1 (sequential) | The runtime dial (10 → ~2-4min) but parallel load trips the WAF → lost pages = lost completeness. Open point 2. |
| `max_pages` | completeness ceiling | 400 | Set > true site size so it never truncates. Hit → more pages likely exist (saturation signal). |
| `max_depth` | completeness reach | 10 | Generous; with focused include-pattern rarely binds. |
| include/exclude pattern | scope (precision + time) | `/de/rest/` | Tighter = faster + less noise, too tight excludes legit pages. Only scope lever that also saves time. |
| stealth (`enable_stealth` + `UndetectedAdapter`) | 429-avoidance ↔ overhead/fragility | off | Mirrors Phase-2 in `src/scraper/scrape_url.py`. Toggle to dodge Cloudflare WAF; enables higher concurrency. UndetectedAdapter has known fingerprint weaknesses + site-incompat risk. |

**Summary:** `delay` is the one genuine time↔completeness dial. `max_pages`/`depth`/pattern are ceiling/scope (set generous → don't truncate). concurrency + stealth are speed-vs-WAF (touch completeness only via avoided 429s).

## Parameter semantics — `delay` (3s) vs `page_timeout` (15s)

Two different clocks, two phases — NOT contradictory:
- `page_timeout=15s` = max time for the page to LOAD (navigation → `domcontentloaded`). Bites only on a pathologically slow/stuck page; then abort instead of hanging.
- `delay_before_return_html=3s` = fixed wait AFTER load completes, before grabbing HTML, to let JS render.
- Healthy page: nav → domcontentloaded (~0.3s) → +3s delay → capture ≈ 3.3s total. The 15s never engages. "Between 3s and 15s" nothing happens on a normal page — that window only exists for a still-loading stuck page.

## WAF / 429 context

docs.github.com sits behind Cloudflare. WAF returns 429 on parallel HTTP load (`prefetch=True` → 429 after ~100 reqs/session in Phase A; sequential survived; Playwright sequential = 0×429 in Phase B). Stealth (`enable_stealth=True` + `UndetectedAdapter` + `AsyncPlaywrightCrawlerStrategy`) exists in `src/scraper/scrape_url.py` (Phase-2 scrape fallback), now available as the crawler `--stealth` toggle.

Single-page scrape of a docs.github.com page verified clean post plugin-routing-unblock. Per-page SCRAPING is solved; the open problem is purely URL DISCOVERY completeness. The scrape phase shares only the volume-429 concern, not the completeness one.

## Saturation message spec

End-of-crawl stop-reason, so a user can decide crawl-further vs stop on sites without a gold standard:
- `frontier exhausted at N pages (max_pages not hit, max depth reached < cap)` → everything reachable found; raising limits won't help.
- `hit max_pages=N (K URLs still queued)` → capped; more pages likely exist → raise + rerun.
- `hit max_depth=D at frontier edge` → depth-capped → raise depth.

NOTE: the saturation message reports CAP-hits, but it CANNOT detect orphan pages (BFS doesn't know what it can't reach). Orphans are a fundamental link-crawl blind spot — see open point 1.

## CRITICAL OPEN POINTS (post-port, tracked)

### 1. Coverage gap ~19% — navigation topology / orphan pages

Playwright-per-page BFS reaches 81.3% on docs.github.com. The missing ~19% are category pages NOT linked from the seed (section-scoped sidebar: docs.github.com shows nav for the current section only, not a global tree) + their subtrees — e.g. `agent-tasks`, `enterprise-admin`, `announcement-banners`, parts of `billing`. A link-following BFS cannot reach what nothing links to; docs.github.com has no sitemap to enumerate them. Rendering is NOT the cause (single-page check confirmed the links appear once ON the category page).

Untested levers: (a) a global-nav page listing all categories; (b) a sidebar-expand interaction (click collapsed sections) before link extraction; (c) sitemap-union where a sitemap exists; (d) accept the limit + rely on the saturation message + (for GH specifically) the repo-derived 305.

Cross-website implication: pure link-crawl has a HARD ceiling on non-global-nav + no-sitemap sites. This is fundamental, not a docs.github.com quirk. **CRITICAL.**

### 2. Runtime — sequential ~18min

Shipped at concurrency=1 (WAF-safe). 305 pages × ~3.6s (3s delay + render/nav) ≈ 18min. NOT a hard limit: concurrency is the dial (10 → ~2-4min), but parallel load trips the Cloudflare WAF (429), and lost pages = lost completeness. Stealth (`enable_stealth` + `UndetectedAdapter`) is a possible enabler for higher concurrency without 429. Open: the WAF-safe concurrency sweet spot (+ stealth). The 3s delay is the per-page floor; parallelism is the only major runtime lever. **CRITICAL.**

## Resolved this session

- D1 Playwright-per-page BFS: chosen + ported to src/ as the single discovery method.
- D2/D2a sitemap: cascade removed; sitemap dropped ENTIRELY (additive-union kept as a future lever).
- D3/D4: domcontentloaded + delay + page_timeout, no networkidle; 429 back-off-once-then-stop.
- Plugin-routing blocking removed (separate topic) — enabled scraping docs.github.com at all.

## Still-open (non-critical)

- chroma_docs Strategy-C outlier (1.09s/page, Phase A): does `prefetch=False + networkidle` trigger Playwright on some sites? Moot post-port (explicit per-page arun now), kept as a note.

## Cross-refs

- Phase A empirical (HTTP BFS, 67.2%, the HTTP-link-extraction finding).
- Phase B empirical (Playwright, 81.3%, topology root-cause).
- `dev/explore_pipeline/04_render_recall.py`, `05_playwright_bfs.py`, `dev/explore_pipeline/05_reports/docs_github_rest_20260529.md`, `goldstandard/docs_github_rest.txt`.
