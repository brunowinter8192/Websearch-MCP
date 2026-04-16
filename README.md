# SearXNG

Web search, URL scraping, and site crawling for Claude Code — powered by a pydoll-based stealth browser engine.

## Features

- **Multi-Engine Web Search** — 4 search engines (Google, Bing, Google Scholar, CrossRef) with automatic deduplication and ranking
- **JavaScript-Aware Scraping** — full page rendering via Crawl4AI with stealth fallback, cookie consent removal, and garbage detection
- **Site Exploration** — sitemap and BFS-based URL discovery for crawl planning
- **Autonomous Research Agent** — Haiku-powered agent that searches broadly, scrapes aggressively, and routes domain-specific results to specialized plugins (arXiv→RAG, GitHub→GitHub, Reddit→Reddit)

## Quick Start

```
/plugin marketplace add brunowinter8192/claude-plugins
/plugin install searxng
# Restart session — mcp-start.sh bootstraps the Python venv automatically
```

## Prerequisites

- Python 3.10+
- Playwright Chromium (auto-installed by `mcp-start.sh`)

`mcp-start.sh` bootstraps the Python venv and sets up Playwright Chromium on first run. No Docker required.

## Setup

**1. Clone + venv**

```bash
git clone https://github.com/brunowinter8192/SearXNG.git
cd SearXNG
python -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/playwright install chromium
```

## Usage

### MCP Tools

| Tool | What it does | When to use |
|------|-------------|-------------|
| `search_web` | Search the web with category, language, and time-range filters | Any web search — categories: `general`, `news`, `it`, `science` |
| `scrape_url` | Fetch a page as filtered markdown with JS rendering | Read full content of a search result |
| `scrape_url_raw` | Fetch a page as raw markdown, saved to file | Prepare content for RAG indexing |
| `explore_site` | Discover all URLs on a site via sitemap/BFS | Plan a crawl before committing to it |

### Skills & Commands

- `/searxng:crawl-site` — Crawl an entire website to markdown files. 6-phase pipeline: explore → assess → crawl → cleanup → index. Optionally spawns a RAG indexing worker (requires the RAG plugin with `/rag:web-md-index`).

### Agents

- **web-research** — Autonomous web research specialist. Searches with 5+ query variations, paginates through results, scrapes 10-15+ URLs per batch, and routes plugin-domain results (arXiv, GitHub, Reddit) to their respective MCP plugins. Dispatched automatically when deep web research is needed.

## Workflows

**Search → Scrape**

1. `search_web` with broad query → ranked results from 4 engines
2. Pick relevant URLs → `scrape_url` for full page content as markdown
3. Plugin-domain URLs (arXiv, GitHub, Reddit) get routed to specialized plugins instead

**Crawl → RAG**

1. `/searxng:crawl-site https://docs.example.com` — explore site structure
2. Filter URL patterns (exclude noise like login pages, language variants)
3. Crawl selected URLs → markdown files with garbage detection
4. Optional: LLM cleanup (web-md-cleanup agent) → chunk + index into RAG

## Troubleshooting

<details>
<summary>Scraping returns empty content</summary>

Some sites block headless browsers. The scraper tries normal mode first, then stealth mode with an undetected adapter. If both fail, the site likely has aggressive bot detection — try `scrape_url_raw` as an alternative.

</details>

<details>
<summary>Playwright/Chromium not installed</summary>

`mcp-start.sh` installs Chromium automatically. For manual installation:

```bash
./venv/bin/playwright install chromium
```

</details>

## License

MIT
