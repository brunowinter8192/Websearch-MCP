# Scraper Module

URL scraping tool powered by Crawl4AI for SearXNG MCP server. Extracts LLM-friendly raw markdown from any URL with JavaScript rendering.

## scrape_url.py

**Purpose:** URL scraping orchestrator. Uses Crawl4AI's AsyncWebCrawler with DefaultMarkdownGenerator to extract full page content as raw markdown.
**Input:** URL string and optional maximum content length (default 15000).
**Output:** Raw markdown content wrapped in TextContent, or error message on failure.

### scrape_url_workflow()

Main orchestrator. Creates Crawl4AI browser and run configuration, fetches URL, extracts raw_markdown (unfiltered content preserving code blocks and formatting). Truncates at paragraph boundary if exceeding max_content_length.

### truncate_content()

Truncates content if exceeding maximum length. Attempts to break at paragraph boundary for clean truncation. Appends truncation notice when content is cut.

## Architecture

Content extraction is delegated entirely to Crawl4AI (v0.8.0):
- **Browser management:** Crawl4AI manages Playwright/Patchright internally
- **JavaScript rendering:** `wait_until="networkidle"` ensures JS-heavy sites are fully rendered
- **Markdown generation:** DefaultMarkdownGenerator without content filter produces raw_markdown preserving all content including code blocks
- **No per-site configuration needed:** Works generically across all website types

Previous versions used PruningContentFilter (threshold 0.48) with fit_markdown, but this destroyed code block formatting (spaces removed, indentation lost). Verified across 86 URLs: 54-76% code integrity with filter vs 94-100% without.
