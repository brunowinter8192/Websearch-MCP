# SearXNG MCP Server

Web search and scraping via local SearXNG instance.

## Sources

**searxng** — Single RAG collection with all indexed sources. Search with `mcp__rag__search_hybrid(collection="searxng")`.

| Source | Type | Pipeline Steps | Status |
|--------|------|---------------|--------|
| searxng | RAG Collection | search01, search02, search03, scrape01, scrape02, scrape03, explore01 | Indexed |
| docs.searxng.org | Web Domain | search01, search02, search03, agent01 | Indexed |
| docs.crawl4ai.com | Web Domain | scrape01, scrape02, scrape03, explore01 | Indexed |
| docs.anthropic.com | Web Domain | agent01 | Indexed |
| playwright.dev | Web Domain | scrape01 | Indexed |
| trafilatura.readthedocs.io | Web Domain | scrape02 | Indexed |
| cookieyes.com | Web Domain | scrape02, scrape03 | Indexed |
| cookiebot.com | Web Domain | scrape03 | Indexed |
| developer.onetrust.com | Web Domain | scrape03 | Indexed |
| sitemaps.org | Web Domain | explore01 | Indexed |
| support.torproject.org | Web Domain | search02 | Indexed |
| github.com | Web Domain | search01, search02, search03, scrape01, scrape02, scrape03, explore01 | Not indexed |
| api.search.brave.com | Web Domain | search01 | Not indexed |
| huggingface.co | Web Domain | agent02 | Not indexed |
| info.arxiv.org | Web Domain | agent02 | Not indexed |

Consult via RAG search before making assumptions. Pipeline step references match `decisions/` files.

## Pipeline Components

### Search Pipeline (SearXNG API)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Engines (general)** | Google, Bing, Brave, Startpage, Mojeek, Scholar, Semantic Scholar, CrossRef | weights 1-2, DDG disabled |
| **Engines (plugin)** | ArXiv, GitHub, Reddit | discovery-only, content via MCP plugins |
| **Routing** | Tor SOCKS5 proxy (Brave, Startpage) / Direct (Google, DDG, Bing, Mojeek) | Split architecture |
| **Ranking** | Hostname priority/depriority/remove plugin | MAX_RESULTS=80, SNIPPET_LENGTH=5000 |

### Scrape Pipeline (Crawl4AI)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Browser** | Normal → Stealth fallback chain | networkidle → domcontentloaded → stealth |
| **Filtering** | PruningContentFilter (scrape_url) / Raw (scrape_url_raw) | threshold=0.48, MIN_CONTENT=200 |
| **Garbage Detection** | is_garbage_content() | Crawl4AI errors, 404/403, cookie walls |

### Explore Pipeline (Crawl4AI BFS)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Discovery** | Sitemap → BFS Prefetch cascade | MAX_DEPTH=10, MAX_PAGES=50, TIMEOUT=120s |

### Agent Pipeline (web-research)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Search** | 5+ queries, pagination pageno 1-3, general+science | Haiku model |
| **Routing** | Plugin routing (arxiv→RAG, github→GH, reddit→Reddit) | youtube→skip |
| **Coverage** | Per-topic URL tracking, 10+ URLs/topic target | Aggressive scraping |

### Key Files

| File | Component |
|------|-----------|
| `src/searxng/search_web.py` | Search API wrapper |
| `src/searxng/settings.yml` | SearXNG instance config (engines, proxy, hostnames) |
| `src/scraper/scrape_url.py` | URL scraping (filtered + raw) |
| `src/scraper/explore_site.py` | Site discovery (sitemap + BFS) |
| `server.py` | MCP tool registration |
| `agents/web-research.md` | Agent definition |
| `skills/searxng/SKILL.md` | SearXNG skill (strategy, dispatch) |
| `skills/agent-web-research/SKILL.md` | Agent tool reference |

## Project Structure

```
searxng/
├── server.py
├── crawl_site.py
├── explore_site.py
├── mcp-start.sh
├── requirements.txt
├── README.md                       → [Setup & External Docs](README.md)
├── DOCS.md                         → [Root Module Docs](DOCS.md)
├── decisions/                      → Pipeline decisions & evidence per step
│   ├── search01_engines.md
│   ├── search02_routing.md
│   ├── search03_ranking.md
│   ├── scrape01_browser.md
│   ├── scrape02_filtering.md
│   ├── scrape03_garbage.md
│   ├── explore01_discovery.md
│   ├── agent01_search.md
│   ├── agent02_routing.md
│   └── agent03_coverage.md
├── src/                            → [DOCS.md](src/DOCS.md)
│   ├── scraper/                    → [DOCS.md](src/scraper/DOCS.md)
│   ├── searxng/                    → [DOCS.md](src/searxng/DOCS.md)
│   │   └── patches/                → SearXNG engine patches (Docker volume-mounted)
│   └── spawn/                      → Worker spawn utilities (in src/DOCS.md)
├── dev/                            → [DOCS.md](dev/DOCS.md)
│   ├── search_pipeline/            → [DOCS.md](dev/search_pipeline/DOCS.md)
│   ├── scrape_pipeline/            → [DOCS.md](dev/scrape_pipeline/DOCS.md)
│   ├── explore_pipeline/           → [DOCS.md](dev/explore_pipeline/DOCS.md)
│   ├── agent_pipeline/             → [DOCS.md](dev/agent_pipeline/DOCS.md)
│   └── cleanup/                    → [DOCS.md](dev/cleanup/DOCS.md)
```
