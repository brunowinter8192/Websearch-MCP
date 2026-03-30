---
name: agent-web-research
description: SearXNG MCP tool reference for web research agents
---

# SearXNG MCP Tools — Reference

## Tools

| Tool | Purpose |
|------|---------|
| search_web | Search the web via SearXNG. Returns up to 50 results with title, URL, full snippet |
| scrape_url | Fetch page content as filtered markdown (PruningContentFilter). For in-conversation reading |
| scrape_url_raw | Fetch page content as raw markdown and save as .md file. For RAG indexing |

## Search Strategy

Four fundamentally different workflows:

- **Quick search** (user wants links, overviews, or pointers):
  Use `search_web` alone. Returns up to 50 results with title, URL, and full snippet.
  Good for: finding URLs, getting a topic overview, discovering sources.

- **Deep research** (user wants actual content, analysis, or synthesis):
  Use `search_web` first, then `scrape_url` on the most relevant results.
  Good for: reading documentation, extracting tutorials, comparing approaches, analyzing articles.

- **Direct scraping** (user provides a URL):
  Skip search entirely. Use `scrape_url` directly on the given URL.
  Good for: reading a specific page, extracting content from a known source.

- **Scrape for RAG indexing** (user wants to index a URL into knowledge base):
  Use `scrape_url_raw(url, output_dir)` to save full-fidelity raw markdown as .md file.
  Then run `/rag:web-md-index` on the output directory to cleanup + chunk + index.

**Detection:** "Find me articles about X" → quick search. "What does article X say about Y?" → deep research. "Read this URL" → direct scraping. "Index this URL" / "Save this for later" → scrape_url_raw.

## Scraping Tips

- **Default max_content_length is 15000** — sufficient for most articles/docs. Increase for long documentation pages.
- **JavaScript-rendered content** is supported — Playwright renders the page before extraction.
- **Content-focused sites** (articles, docs, wikis) produce the best results. The scraper is optimized for semantic HTML.
- **Truncation** preserves paragraph boundaries — content is cut at the nearest double newline.
- **Images** are included as markdown references (small/avatar images are filtered out).

## Parameter Reference

### search_web

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query (e.g., "machine learning python tutorial") |
| category | Literal | "general" | Content category: general, news, it, science |
| language | str | "en" | ISO language code |
| time_range | str/None | None | day, month, year |
| engines | str/None | None | Comma-separated engine list (e.g., "google,brave,google scholar") |
| pages | int | 3 | Number of pages to fetch and combine (default 3 = ~150 results) |

**Output:** Plain text numbered list with title, URL, and full snippet per result. Up to 50 results per page.

**Pagination:** The server fetches multiple pages automatically. Use `pages=3` (default) to get up to ~150 deduplicated results per query. Do NOT use `pageno` — pass `pages` instead.

### scrape_url

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | Single URL to fetch and convert to markdown |
| max_content_length | int | 15000 | Character limit for returned content |

**Output:** Filtered markdown with `# Content from: <url>` header.

### scrape_url_raw

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | URL to scrape and save as markdown file |
| output_dir | str | required | Directory to save the .md file (created if not exists) |

**Output:** Confirmation with file path and char count. File saved with `<!-- source: URL -->` header.

## Plugin Routing (CRITICAL)

**Do NOT scrape these domains — report them for plugin-based access:**

| Domain | Action |
|--------|--------|
| arxiv.org | Report: "Use RAG plugin (mcp__rag__search_hybrid) or /rag:pdf-convert" |
| github.com | Report: "Use GitHub Research plugin (github__get_file_content)" |
| reddit.com | Report: "Use Reddit plugin (reddit__search_posts)" |
| youtube.com | Skip entirely. Video content cannot be scraped. |

## Search Categories

| Category | Best for |
|----------|----------|
| general | Broad web search (default) |
| news | Current events, recent articles |
| it | Technical topics, programming, tools |
| science | Academic, research, scientific papers |

## Aggressive Search Pattern

```
1. search_web("topic keywords", category="general") → fetches 3 pages automatically (~150 results)
2. search_web("topic variation", category="general") → different angle
3. search_web("topic keywords", category="science") → academic results
4. Filter results: skip plugin domains, deduplicate
5. scrape_url(url) for each non-plugin URL → read content
6. Report: scraped content + plugin-routed URLs separately
```

## Known Limitations

- **SearXNG instance required** — must be running on localhost:8080
- **Up to ~150 results per query** — server fetches 3 pages by default and deduplicates
- **Scraper optimized for content sites** — articles, docs, wikis work best
- **scrape_url uses PruningContentFilter** — may damage code blocks. Use scrape_url_raw for full fidelity
- **Login-protected pages** will return login forms, not content
- **PDF URLs (.pdf) cannot be scraped** — scrape_url returns only the header `# Content from: <url>` with no content. Do NOT attempt to scrape PDF URLs. Log them as `[PDF — nicht scrapebar]` in the report and note the URL for manual access.
