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
| lobste.rs | Web Domain | search05 | Not indexed |
| api.openalex.org | Web Domain | search05 | Not indexed |
| api.stackexchange.com | Web Domain | search05 | Not indexed |

| GitHub Issue #5286 | github.com | Issue | search02_routing | Referenced |
| GitHub Issue #5922 | github.com | Issue | search02_routing | Referenced |
| GitHub PR #5644 | github.com | PR | search01_engines | Referenced |

| daijro/camoufox | Repo | stealth01 | Referenced |
| saifyxpro/HeadlessX | Repo | stealth01 | Referenced |
| nichochar/stealth-browser-mcp | Repo | stealth01 | Referenced |
| Kaliiiiiiiiii-Vinyzu/patchright-python | Repo | stealth01 | Referenced |
| debug-it/brave-captcha-solver | Repo | stealth01 | Referenced |
| nullpt-rs/blog (reversing-botid.mdx) | Web | stealth01 | Referenced |
| FriendlyCaptcha/friendly-challenge | Repo | stealth01 | Referenced |
| BotBrowser CHANGELOG | Repo | stealth01 | Referenced |
| autoscrape-labs/pydoll | Repo | stealth00, stealth01, stealth03 | Referenced |
| opsdisk/yagooglesearch | Repo | stealth05 | Referenced |
| karust/openserp | Repo | stealth05, stealth07 | Referenced |
| 2captcha/2captcha-go | Repo | stealth07 | Referenced |
| github.com/StractOrg/stract | Repo | search05 | Referenced |
| github.com/MarginaliaSearch/MarginaliaSearch | Repo | search05 | Referenced |
| github.com/MarginaliaSearch/docs.marginalia.nu | Repo | search05 | Referenced |
| github.com/cyanheads/hn-mcp-server | Repo | search05 | Referenced |
| github.com/voska/hn-cli | Repo | search05 | Referenced |
| github.com/lucjon/Py-StackExchange | Repo | search05 | Referenced |
| github.com/searxng/searxng | Repo | search05 | Referenced |
| github.com/searxng/searxng (searx/engines/duckduckgo.py) | Repo | search05 | Referenced |
| github.com/searxng/searxng (searx/engines/mojeek.py) | Repo | search05 | Referenced |
| github.com/searxng/searxng (searx/engines/lobsters.py) | Repo | search05 | Referenced |
| github.com/hffmnnj/kagi-skill | Repo | search05 | Referenced |
| github.com/encode/httpx | Repo | search06 | Referenced |
| github.com/lxml/lxml | Repo | search06 | Referenced |

Consult via RAG search before making assumptions. Pipeline step references match `decisions/` files.
