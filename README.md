# SearXNG MCP Server

Web search and URL scraping tools for LLM workflows.

**Remote:** https://github.com/brunowinter8192/searxng-mcp

After major changes, push to remote:
```bash
git add -A && git commit -m "Your message" && git push
```

## Prerequisites

- Docker and Docker Compose
- Python 3.10+

## Quick Start

1. Start SearXNG container:
```bash
docker compose up -d
```

2. Verify SearXNG is running:
```bash
curl "http://localhost:8080/search?q=test&format=json"
```

3. Install dependencies:
```bash
pip install fastmcp requests pydantic playwright
playwright install chromium
```

4. Run MCP server:
```bash
fastmcp run server.py
```

## Tools

### search_web
Search the web with category filtering.

Parameters:
- `query`: Search string
- `category`: general | news | it | science (default: general)

Returns 20 results with title, url, content snippet.

### scrape_urls
Fetch full page content from URLs with JavaScript rendering.

Parameters:
- `urls`: List of URLs to scrape
- `concurrency`: Number of parallel requests (default: 5)

Returns list of results with url, content (markdown), success status.

## Configuration

SearXNG settings: `src/searxng/settings.yml`

### MCP Registration

Two configuration files are provided:

- **`.mcp.json.example`** - Template for integrating into other projects. Copy and adjust paths.
- **`.mcp.json`** - Production configuration with absolute paths for active development.

To use in Claude Code:
```bash
cp .mcp.json.example .mcp.json
# Edit .mcp.json with your absolute paths
```

## Development

Bug fixes and debugging scripts go in `bug_fixes/` directory. This folder is gitignored and not tracked in version control.

## Documentation

Module documentation lives in each source directory:
- `src/scraper/DOCS.md` - Scraper module documentation
- `src/searxng/DOCS.md` - SearXNG configuration documentation
