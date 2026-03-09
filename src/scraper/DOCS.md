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

## explore_site.py

**Purpose:** Site structure reconnaissance. Crawls a website using BFS to discover all pages and build a summary with depth distribution, page counts, and character counts. No file export — analysis only.
**Input:** URL string and optional max_pages limit (default 200).
**Output:** Dict with seed_url, domain, total_pages, total_chars, depth_distribution (count + chars per level).

### explore_site_workflow()

Main orchestrator. Extracts domain from URL, runs BFS discovery crawl, builds site map from results.

### crawl_for_discovery()

BFS crawl with DomainFilter + ContentTypeFilter (text/html). Uses max_depth=10 internally to discover full site structure. Returns raw CrawlResult list.

### build_site_map()

Aggregates crawl results into summary. Deduplicates URLs (trailing slash normalization), extracts depth from `result.metadata["depth"]` (set by Crawl4AI BFS strategy), computes per-depth statistics. Returns only aggregated counts, no individual URL list.

## Architecture

Content extraction is delegated entirely to Crawl4AI (v0.8.0):
- **Browser management:** Crawl4AI manages Playwright/Patchright internally
- **JavaScript rendering:** `wait_until="networkidle"` ensures JS-heavy sites are fully rendered
- **Markdown generation:** DefaultMarkdownGenerator without content filter produces raw_markdown preserving all content including code blocks
- **No per-site configuration needed:** Works generically across all website types

Previous versions used PruningContentFilter (threshold 0.48) with fit_markdown, but this destroyed code block formatting (spaces removed, indentation lost). Verified across 86 URLs: 54-76% code integrity with filter vs 94-100% without.
