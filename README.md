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

**Parameters:**
- `query`: Search string
- `category`: general | news | it | science (default: general)

**Returns:** Plain text numbered list with title, URL, snippet per result (max 20).

**Output Format:**
```
Found 15 results for "query"

1. Title
   URL: https://...
   Snippet: First 200 chars...
```

**Search Strategy:** Start with 1-2 core keywords, check results, then refine. Too many keywords yields poor results. Iterate: broad query first, then progressively more specific.

**Category Guide:**
| Question Type | Category |
|--------------|----------|
| Code/implementation | it |
| Recent news | news |
| Academic papers | science |
| General | general |

### scrape_url
Fetch full page content as markdown with JavaScript rendering.

**Parameters:**
- `url`: Single URL to scrape
- `max_content_length`: Maximum content length in characters (default: 15000)

**Returns:** Markdown content with header showing source URL.

**Output Format:**
```
# Content from: https://example.com

[Full markdown content]

[Content truncated...]
```

**When to use:** After search_web identifies relevant URLs that need full content extraction. Uses networkidle wait strategy for complete JavaScript rendering.

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

## Testing

The scraping suite provides continuous quality monitoring for the URL scraper. Located in `debug/scraping_suite/`, it tests content extraction across diverse web page types and detects regressions.

### Running Tests

Generate baseline for all test domains:
```bash
python debug/scraping_suite/run_baseline.py
```

Compare with previous iteration:
```bash
python debug/scraping_suite/compare_iterations.py
```

See `debug/scraping_suite/README.md` for detailed documentation on test domains, workflow, and output structure.

## Documentation

Module documentation lives in each source directory:
- `src/searxng/DOCS.md` - SearXNG search module and configuration
- `src/scraper/DOCS.md` - URL scraper module documentation
- `debug/scraping_suite/README.md` - Test suite documentation
