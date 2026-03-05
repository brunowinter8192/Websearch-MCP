# SearXNG MCP Server

Web search and URL scraping tools for Claude Code via a local SearXNG instance.

## Installation

### As Plugin (recommended)

In a Claude Code session:

```
/plugin marketplace add brunowinter8192/claude-plugins
/plugin install searxng
```

Restart the session after installation.

### Manual (.mcp.json)

Add to your project's `.mcp.json` (all paths must be absolute):

```json
{
  "mcpServers": {
    "searxng": {
      "command": "/absolute/path/to/venv/bin/fastmcp",
      "args": ["run", "/absolute/path/to/server.py"]
    }
  }
}
```

## Prerequisites

- Docker and Docker Compose
- Python 3.10+

### SearXNG Setup

1. Start SearXNG container:
```bash
docker compose up -d
```

2. Verify SearXNG is running:
```bash
curl "http://localhost:8080/search?q=test&format=json"
```

SearXNG runs on `localhost:8080` by default. Configuration: `searxng/settings.yml`.

### Updating SearXNG

The Docker image uses `searxng/searxng:latest`. Pull updates regularly:

```bash
docker compose pull && docker compose up -d
```

## Plugin Components

| Component | Name | Description |
|-----------|------|-------------|
| **Skill** | `searxng` | Tool usage context and search strategy |
| **MCP Server** | `searxng` | 2 tools: web search + URL scraper |
| **Subagent** | `web-research` | Deep web research specialist |

## MCP Tools

### search_web

Search the web with category filtering via SearXNG.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query (start broad, then refine) |
| `category` | `"general"` / `"news"` / `"it"` / `"science"` | `"general"` | Category filter |

**Category Guide:**

| Question Type | Category |
|--------------|----------|
| Code, implementation | it |
| Recent events | news |
| Academic papers | science |
| Everything else | general |

### scrape_url

Fetch full page content as markdown with JavaScript rendering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to scrape |
| `max_content_length` | int | `15000` | Maximum content length in characters |

Use after `search_web` identifies relevant URLs that need full content extraction.

## Scripts

### crawl_site.py

Crawl an entire website and save pages as Markdown files. Uses Crawl4AI BFS (Breadth-First Search) with automatic link discovery.

```bash
venv/bin/python crawl_site.py \
  --url "https://docs.searxng.org/" \
  --collection "SearXNG_Docs" \
  --depth 3 \
  --max-pages 100
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--url` | required | Seed URL to start crawling |
| `--collection` | required | Output folder name |
| `--depth` | 3 | Maximum crawl depth |
| `--max-pages` | 100 | Maximum pages to crawl |

Output is saved to the RAG data directory as individual `.md` files per page. Uses `raw_markdown` (preserves HTML in code blocks) with only permalink artifact cleanup.

## Directory Structure

```
searxng/
├── .claude-plugin/          # Plugin distribution
│   └── plugin.json          # Plugin metadata
├── agents/                  # Subagent definitions
│   └── web-research.md
├── skills/                  # Skill definitions
│   ├── searxng/SKILL.md
│   └── agent-web-research/SKILL.md
├── src/                     # Source modules
│   ├── searxng/             # Search module
│   │   ├── search_web.py
│   │   └── DOCS.md
│   └── scraper/             # Scraper module
│       ├── scrape_url.py
│       ├── html_parser.py
│       ├── markdown_converter.py
│       ├── content_filter.py
│       └── DOCS.md
├── searxng/                 # SearXNG Docker config
│   └── settings.yml
├── crawl_site.py            # Website crawler (standalone script)
├── server.py                # MCP entry point
├── docker-compose.yml       # SearXNG container
├── mcp-start.sh             # Plugin startup script
└── requirements.txt         # Python dependencies
```

## Documentation

| Doc | Content |
|-----|---------|
| `src/searxng/DOCS.md` | Search module implementation details |
| `src/scraper/DOCS.md` | Scraper module implementation details |
| `skills/searxng/SKILL.md` | Tool usage guide |
| `agents/web-research.md` | Subagent instructions |
