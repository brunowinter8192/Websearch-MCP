# SearXNG MCP Server

Web search and scraping via local SearXNG instance.

## Sources

**Crawl4AI Docs** — Indexed in RAG. Search with `mcp__rag__search_hybrid(collection="Crawl4AIDocs")`.
**SearXNG Docs** — Indexed in RAG. Search with `mcp__rag__search_hybrid(collection="SearXNG_Docs")`.

| Source | Type | Pipeline Steps | Status |
|--------|------|---------------|--------|
| Crawl4AIDocs | RAG Collection | scrape01, scrape02, explore01 | Indexed |
| SearXNG_Docs | RAG Collection | search01, search02, search03 | Indexed |
| anthropic.com/news/contextual-retrieval | Web | agent02 (plugin routing rationale) | Not indexed |
| blog.vectorchord.ai/.../colbert-rerank-postgresql | Web | scrape02 (content quality comparison) | Not indexed |
| developer.nvidia.com/.../chunking-strategy | Web | scrape02 (filter evaluation) | Not indexed |
| research.trychroma.com/evaluating-chunking | Web | scrape02 (filter metrics) | Not indexed |
| weaviate.io/blog/late-chunking | Web | scrape01 (browser strategy for long docs) | Not indexed |
| crunchydata.com/.../hnsw-indexes | Web | explore01 (crawl performance) | Not indexed |

Consult via RAG search before making assumptions. Pipeline step references match `decisions/` files.

## Pipeline Components

### Search Pipeline (SearXNG API)

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Engines** | Google, Brave, Startpage, DDG, Google Scholar | weights 1-2, Qwant disabled |
| **Routing** | Tor SOCKS5 proxy (Brave, Startpage) / Direct (Google, DDG) | Split architecture |
| **Ranking** | Hostname priority/depriority/remove plugin | MAX_RESULTS=50, SNIPPET_LENGTH=5000 |

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
├── requirements.txt
├── README.md                       → [Setup & External Docs](README.md)
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
├── src/
│   ├── scraper/                    → [DOCS.md](src/scraper/DOCS.md)
│   └── searxng/                    → [DOCS.md](src/searxng/DOCS.md)
├── dev/
│   ├── crawling_suite/             → [DOCS.md](dev/crawling_suite/DOCS.md)
│   ├── searching_suite/            → [DOCS.md](dev/searching_suite/DOCS.md)
│   └── scraping_suite/             → [DOCS.md](dev/scraping_suite/DOCS.md)
```
