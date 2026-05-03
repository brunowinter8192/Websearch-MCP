# SearXNG Plugin

Web search and scraping CLI plugin. Note: the plugin keeps the 'searxng' name for historical reasons — the SearXNG Docker wrapper was replaced by a custom pydoll implementation in the engine-cut refactor 2026-04-15.

## Sources

See [sources/sources.md](sources/sources.md).

## Pipeline Components

### Search Pipeline (`src/search/`, mixed browser + HTTP API)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Engines (active)** | Google, Bing, Google Scholar, DuckDuckGo (pydoll); CrossRef, HN-Algolia (HTTP) | 6-engine set, HN added 2026-05-01, DDG added 2026-05-03 |
| **Engines (plugin)** | ArXiv, GitHub, Reddit | discovery-only, content via MCP plugins |
| **Browser** | pydoll Chrome (stealth fingerprint patches, per-engine JS selectors) | `src/search/browser.py`, `src/search/engines/`, `dev/search_pipeline/01_google_smoke.py` + `config.yml` |
| **Rate Limiting** | Token-bucket per engine with backoff | `src/search/rate_limiter.py` |
| **Orchestration** | `asyncio.gather` parallel fetch across engines, deduplicated, formatted as TextContent. `search_web_workflow` for single query; `search_batch_workflow` for N queries sequentially in one warm-Chrome session | `src/search/search_web.py`, SNIPPET_LENGTH=5000 |
| **Parked** | Brave (PoW CAPTCHA incompatible with parallel architecture) | See `decisions/stealth00_engine_status.md` |

### Scrape Pipeline (Crawl4AI)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Browser** | Normal → Stealth fallback chain | networkidle → domcontentloaded → stealth |
| **Filtering** | PruningContentFilter (scrape_url) / Raw (scrape_url_raw) | threshold=0.48, MIN_CONTENT=200 |
| **Garbage Detection** | is_garbage_content() → str\|None | 6 types: crawl4ai_error, http_error, nav_dump, cookie_wall, login_wall, cloudflare |

### Explore Pipeline (Crawl4AI BFS)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Discovery** | Sitemap → BFS Prefetch cascade | MAX_DEPTH=10, MAX_PAGES=50, TIMEOUT=120s |

### Delivery

| Component | Implementation | Config |
|-----------|---------------|--------|
| **CLI** | `cli.py` via argparse + `~/.local/bin/searxng-cli` wrapper | 6 tools (search_web, search_batch, scrape_url, scrape_url_raw, explore_site, download_pdf) |

### Key Files

| File | Component |
|------|-----------|
| `src/search/search_web.py` | Search orchestrator (parallel engine fetch + dedup) |
| `src/search/browser.py` | pydoll Chrome lifecycle (shared singleton) |
| `src/search/rate_limiter.py` | Per-engine token bucket |
| `src/search/engines/` | Per-engine parsers: `google.py`, `bing.py`, `scholar.py`, `crossref.py`, `hn.py`, `duckduckgo.py` |
| `src/scraper/scrape_url.py` | URL scraping (filtered) |
| `src/scraper/scrape_url_raw.py` | Raw URL scraping (for RAG indexing) |
| `src/scraper/download_pdf.py` | PDF file download |
| `src/scraper/explore_site.py` | Site discovery (sitemap + BFS) |
| `src/routing.py` | Plugin domain routing |
| `src/crawler/crawl_site.py` | Full website crawl with markdown export |
| `src/crawler/explore_site.py` | URL discovery CLI for /crawl-site pipeline |
| `cli.py` | CLI dispatch |

## Project Structure

```
searxng/
├── cli.py                          → CLI dispatch (6 commands incl. search_batch warm-Chrome multi-query)
├── .env.example                    → Template for SEARXNG_PROJECT_ROOT
├── requirements.txt
├── README.md                       → [Setup & External Docs](README.md)
├── DOCS.md                         → [Root Module Docs](DOCS.md)
├── decisions/                      → Pipeline decisions & evidence per step
│   ├── search01_engines.md
│   ├── search02_routing.md
│   ├── search03_ranking.md
│   ├── search04_weights.md
│   ├── scrape01_browser.md
│   ├── scrape02_filtering.md
│   ├── scrape03_garbage.md
│   ├── explore01_discovery.md
│   ├── agent01_search.md
│   ├── agent02_routing.md
│   └── agent03_coverage.md
├── src/                            → [DOCS.md](src/DOCS.md)
│   ├── routing.py                  → Plugin domain routing
│   ├── search/                     → [DOCS.md](src/search/DOCS.md) — search engines (6 active: 4 browser + 2 API)
│   │   └── engines/                → Per-engine parsers (google, bing, scholar, crossref, hn, duckduckgo)
│   ├── scraper/                    → [DOCS.md](src/scraper/DOCS.md)
│   ├── crawler/                    → [DOCS.md](src/crawler/DOCS.md) — CLI-only (`/crawl-site` pipeline)
│   └── spawn/                      → Worker spawn utilities (in src/DOCS.md)
├── dev/                            → [DOCS.md](dev/DOCS.md)
│   ├── search_pipeline/            → [DOCS.md](dev/search_pipeline/DOCS.md) — Per-engine smoke stack (01_google_smoke, 02_burst_smoke, 03_hn_smoke, 04_ddg_smoke, config.yml, 01_reports/)
│   ├── scrape_pipeline/            → [DOCS.md](dev/scrape_pipeline/DOCS.md)
│   │   ├── browser_eval/           → scrape01_browser
│   │   ├── filter_eval/            → scrape02_filtering
│   │   └── garbage_eval/           → scrape03_garbage
│   ├── explore_pipeline/           → [DOCS.md](dev/explore_pipeline/DOCS.md)
│   ├── agent_pipeline/             → [DOCS.md](dev/agent_pipeline/DOCS.md)
│   └── cleanup/                    → [DOCS.md](dev/cleanup/DOCS.md)
```
