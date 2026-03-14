---
name: searxng-tools
description: SearXNG web search and URL scraping strategy
---

# SearXNG MCP Tools — Search & Scraping Strategy

## Pipeline Overview

### MCP Tools (ad-hoc, in-conversation)

```
search_web("topic")          → find interesting URLs
scrape_url("url")            → quick single-page check
explore_site("domain.com")   → ad-hoc site check (max 50 pages, strategy recommendation)
```

### Crawl Pipeline (structured, multi-step via /crawl-site)

```
explore_site.py --url X      → strategy auto-detect + full URL list as file
  review URL samples         → grep/stichproben for noise patterns
  filter noise               → grep -v, produce filtered list
crawl_site.py --url-file     → batch crawl filtered URLs
  (optional) RAG indexing    → /rag:web-md-index
```

MCP explore_site is for quick ad-hoc checks in chat. The crawl pipeline uses explore_site.py (CLI script) for full discovery — they are separate tools for separate purposes.

## Search Strategy

Two fundamentally different workflows:

- **Quick search** (user wants links, overviews, or pointers):
  Use `search_web` alone. Returns up to 20 results with title, URL, and snippet.
  Good for: finding URLs, getting a topic overview, discovering sources.

- **Deep research** (user wants actual content, analysis, or synthesis):
  Use `search_web` first, then `scrape_url` on the most relevant results.
  Good for: reading documentation, extracting tutorials, comparing approaches, analyzing articles.

- **Direct scraping** (user provides a URL):
  Skip search entirely. Use `scrape_url` directly on the given URL.
  Good for: reading a specific page, extracting content from a known source.

**Detection:** "Find me articles about X" → quick search. "What does article X say about Y?" → deep research. "Read this URL" → direct scraping.

## search_web Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `query` | required | Search query string |
| `category` | "general" | general, news, it, science |
| `language` | "en" | ISO language code (en, de, fr...) |
| `time_range` | None | day, month, year |
| `engines` | None | Comma-separated engine list (e.g., "google,brave") |
| `pageno` | 1 | Page number for pagination |

## Tool Selection

| Goal | Primary Tool | Secondary |
|------|-------------|-----------|
| Find URLs on a topic | search_web | — |
| Get topic overview with snippets | search_web | — |
| Read a specific page | scrape_url | — |
| Research a topic in depth | search_web | scrape_url (top 3-5) |
| Compare information across sources | search_web | scrape_url (multiple) |
| Extract documentation content | scrape_url | — |
| Understand site structure before crawling | explore_site | — |
| Crawl entire site to markdown files | /crawl-site | explore_site (optional) |

## Subagent Dispatch (web-research)

| Agent | subagent_type | Model | Output |
|-------|---------------|-------|--------|
| web-research | `web-research` | Haiku | URLs + 1-2 sentence summaries with scraped content |

**Usage:** `Task(subagent_type="web-research", prompt="...")`

### When to Dispatch

- Multi-query research (>2 different search queries needed)
- Deep research requiring scraping 3+ URLs
- User wants a curated summary of web sources on a topic
- Comparative analysis across multiple pages

### When NOT to Dispatch (do it yourself)

- Single search query with quick-glance results
- Scraping a single known URL
- User already provided the URL to read

### Workflow: Dispatch First → Verify

**1. Dispatch (subagent)**
- Include: research question, suggested search queries, category preference
- Agent searches + scrapes top results + synthesizes findings
- Agent returns: URLs with summaries capturing actual page content

**2. Verify (you)**
- Spot-check at least 1 URL: call `scrape_url` yourself
- Verify the summary matches actual page content
- Check URLs are valid

**3. Present to user**
- Include verified results
- Flag any unverified claims

### How to Prompt

**BAD:**
- "Search the web for Python" (too vague)
- "Find information about X" (no scope)

**GOOD:**
```
Research: Best practices for SearXNG configuration in production

Search queries to try:
- "searxng production configuration"
- "searxng docker deployment best practices"
- "searxng settings.yml optimization"

Category: it
Focus on: Concrete configuration examples, performance tuning, security hardening
```

### After Agent Returns

**Agent = Scout, not Authority**

**You MUST:**
1. Spot-check at least 1 URL by calling `scrape_url`
2. Verify summary matches actual page content
3. Never present agent summaries without at least 1 verification

## Site Exploration (explore_site)

Use `explore_site` when the user wants to understand a website's structure before committing to a full crawl.

**Output:** Site map with depth distribution, page counts per level, total character count, and full URL list.

**Typical workflow:**
1. `explore_site("https://docs.example.com")` — see structure
2. User reviews depth distribution and total size
3. User decides: crawl everything, limit depth, or use filters
4. `/crawl-site https://docs.example.com` — full crawl with chosen settings

**Parameters:**
- `url` — seed URL to explore
- `max_pages` — discovery limit (default 200, increase for large sites)

**When to use:**
- User asks "how big is this site?"
- Before crawling an unknown site
- When deciding crawl scope (depth, filters)

**When NOT to use:**
- User already knows the site and wants to crawl directly → `/crawl-site`
- Single page → `scrape_url`

## Crawl Site (/crawl-site)

Slash command for full website crawling. Multi-phase pipeline: explore, filter, crawl, optional RAG indexing.

**Usage:** `/crawl-site https://docs.example.com`

**The command walks through 4 phases:**
1. **Explore** — explore_site.py auto-detects strategy (sitemap/prefetch/BFS), discovers URLs, saves URL list to output directory
2. **Review & Filter** — user reviews URL samples, grep -v filters noise patterns
3. **Crawl** — crawl_site.py batch-crawls filtered URLs to markdown
4. **RAG Pipeline** — optional: runs /rag:web-md-index (cleanup + chunk + embed)

**Default export path:** `~/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/<website>/`

### Crawl Strategy Selection

crawl_site.py has a 3-level auto-detection cascade (`--strategy auto`, default):
1. **Sitemap** (AsyncUrlSeeder) — seconds for thousands of URLs, no rendering
2. **Prefetch BFS** — ~200-500ms per page, HTML+links only
3. **BFS full rendering** — ~2-5s per page, networkidle (fallback for SPA/JS-heavy)

Each level falls back to the next if it fails. Force a specific strategy with `--strategy sitemap|prefetch|bfs`.

### Crawl4AI Config (Production)

Two scraping modes with different content filter strategies:

- **scrape_url (MCP tool):** `PruningContentFilter(threshold=0.48)` + `fit_markdown` — filters navigation, sidebars, cookie banners. Trade-off: code block formatting destroyed. Acceptable for MCP use case.
- **crawl_site (export script):** `DefaultMarkdownGenerator()` without content filter + `raw_markdown` — full fidelity. Noise handled by downstream RAG cleanup agent.

Both use `wait_until="networkidle"` and `BrowserConfig(headless=True, verbose=False)`.

Config changes: test via dev/scraping_suite and dev/crawling_suite scripts.

### crawl_site.py CLI reference

```bash
${CLAUDE_PLUGIN_ROOT}/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/crawl_site.py \
  --url "https://docs.example.com" \
  --output-dir "/path/to/output" \
  --depth 3 \
  --max-pages 100 \
  --exclude-patterns "/genindex*,/search*" \
  --include-patterns "/docs/*,/api/*"
```

**Filters:**
- `--exclude-patterns` — comma-separated URL patterns to exclude
- `--include-patterns` — comma-separated URL patterns to include
- ContentTypeFilter (text/html) is always active

### SearXNG Engine Types

Scraper engines (brave, google, duckduckgo) parse web UI HTML — no API key but get blocked. API engines (braveapi) use official REST API — stable but require registration.

Current engine routing: Brave and Startpage via Tor proxy (IP rotation), Google and DuckDuckGo direct (Tor exit nodes blocked).

**Per-engine proxy override:** To bypass global Tor proxy, BOTH settings required:
```yaml
- name: duckduckgo
  using_tor_proxy: false
  proxies: {}
```
`using_tor_proxy: false` alone does NOT remove the proxy — `proxies` config is inherited from `outgoing.proxies` independently.

## Scraping Tips

- **Default max_content_length is 15000** — sufficient for most articles/docs. Increase for long documentation pages.
- **JavaScript-rendered content** is supported — Playwright renders the page before extraction.
- **Content-focused sites** (articles, docs, wikis) produce the best results. The scraper is optimized for semantic HTML.
- **Truncation** preserves paragraph boundaries — content is cut at the nearest double newline.
- **Images** are included as markdown references (small/avatar images are filtered out).

## Search Categories

| Category | Best for |
|----------|----------|
| general | Default. Broad web search |
| news | Current events, recent developments |
| it | Technical topics, programming, software |
| science | Academic, scientific topics |

## Known Limitations

- **SearXNG container must be running** on `localhost:8080` — `mcp-start.sh` handles this automatically
- **Max 20 search results** per query — use specific queries for better relevance
- **Scraper optimized for content sites** — complex SPAs, heavy JavaScript apps, or login-protected pages may not render well
- **Snippet length is 500 chars** — for full content, always scrape the URL
- **Pagination supported** — use `pageno` parameter for additional result pages
- **Engine availability varies** — Google/Brave/DDG may be temporarily suspended (CAPTCHA, rate limits). Startpage is the most reliable engine.
