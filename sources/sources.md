# Sources

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
