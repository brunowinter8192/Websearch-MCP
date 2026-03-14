# Scraper Module

URL scraping and site exploration tools powered by Crawl4AI for SearXNG MCP server.

## scrape_url.py

**Purpose:** URL scraping orchestrator. Uses Crawl4AI's AsyncWebCrawler with multi-layer noise removal and PruningContentFilter to extract clean page content as markdown.
**Input:** URL string and optional maximum content length (default 15000).
**Output:** Filtered markdown content wrapped in TextContent, or error message with plugin hint on failure.

### scrape_url_workflow()

Main orchestrator. Uses Stealth Mode + UndetectedAdapter (Level 3 anti-bot evasion) for all requests. Attempts scrape with `networkidle` wait strategy first, falls back to `domcontentloaded` on timeout/error. Three noise-removal layers applied in sequence:

1. `remove_overlay_elements=True` — JS-based removal of cookie banners, modals, sticky elements from DOM before scraping
2. `excluded_selector=COOKIE_CONSENT_SELECTOR` — CSS selector matching 16 common cookie consent frameworks (CookieYes, OneTrust, Cookiebot, cc-banner, GDPR etc.), elements removed from HTML before markdown conversion
3. `PruningContentFilter(threshold=0.48)` + `fit_markdown` — content scoring filter removes remaining low-quality blocks

On empty result, returns error message with plugin hint if URL matches a known domain with dedicated MCP plugin (Reddit, arxiv).

Note: PruningFilter destroys code block formatting (whitespace stripped). Acceptable for MCP use case (relevance assessment). For full-fidelity export, use crawl_site.py with raw_markdown.

### try_scrape()

Attempts a single scrape with given wait strategy. Creates CrawlerRunConfig with all noise-removal layers, runs AsyncWebCrawler, returns fit_markdown content or empty string on any exception.

### truncate_content()

Truncates content if exceeding maximum length. Attempts to break at paragraph boundary for clean truncation. Appends truncation notice when content is cut.

### get_plugin_hint()

Checks URL against PLUGIN_HINTS dict. Returns hint string for domains with dedicated MCP plugins (reddit.com, arxiv.org), empty string otherwise.

### Constants

- `COOKIE_CONSENT_SELECTOR` — CSS selector string matching common cookie consent frameworks: CookieYes (cky-*), OneTrust, Cookiebot, cc-banner, GDPR, cookie-banner, cookie-consent, cookie-notice, cookie-law
- `PLUGIN_HINTS` — Dict mapping domains to plugin usage hints
- `DEFAULT_MAX_CONTENT_LENGTH` — 15000 chars

## explore_site.py

**Purpose:** Site structure reconnaissance. Fast URL discovery via prefetch mode (~200-500ms per page instead of 2-5s). Returns page counts, depth distribution, and URL samples for noise pattern identification. No file export — analysis only.
**Input:** URL string, optional max_pages limit (default 200), optional url_pattern wildcard filter.
**Output:** TextContent with formatted Markdown summary (page count, total chars, depth distribution, 5 URL samples per depth). Partial results on timeout (120s) with warning.

### explore_site_workflow()

Main orchestrator. Extracts domain from URL, runs BFS discovery crawl with timeout, builds site map with URL samples, formats as Markdown. Returns tuple-based results from crawl_for_discovery (timed_out, results).

### crawl_for_discovery()

BFS crawl with DomainFilter + ContentTypeFilter (text/html) + optional URLPatternFilter. Uses `prefetch=True` — skips markdown generation and content extraction, only fetches HTML and extracts links. Wrapped in `asyncio.wait_for()` with 120s timeout. Returns tuple `(timed_out: bool, results: list)`. max_depth=10 internally.

### build_site_map()

Aggregates crawl results into summary dict. Deduplicates URLs (trailing slash normalization), extracts depth from metadata, computes per-depth statistics, picks URL samples via `pick_url_samples()`. Includes `timed_out` flag in output.

### pick_url_samples()

Selects 5 evenly-spaced URLs per depth level for noise pattern identification. If fewer than 5 URLs at a depth, returns all. Used by LLM to identify URL noise patterns (version switchers, unrelated sections) before crawling.

### format_site_map()

Formats site map dict as readable Markdown. Includes domain, seed URL, total pages, total chars, depth distribution, and URL samples per depth. Shows partial results warning on timeout.

## crawl_site.py (root level)

**Purpose:** Full website crawl with markdown export. Supports 3-level auto-detection cascade (sitemap → prefetch → BFS), direct URL file input, and parallel crawl via `arun_many()` with `SemaphoreDispatcher(concurrency=10)`.
**Input:** URL, output directory, depth, max_pages, optional include/exclude URL patterns, optional --strategy flag, optional --url-file for pre-filtered URL lists.
**Output:** Markdown files in output directory (one per page), with source URL comment header.

### crawl_site_workflow()

Main orchestrator. Strategy selection: (1) --url-file: read URLs from file, skip discovery. (2) --strategy auto: cascade sitemap → prefetch → BFS with SPA auto-detection. (3) --strategy sitemap/prefetch/bfs: force specific strategy. Deduplicates results, saves as markdown files.

### discover_urls_sitemap()

Fastest discovery strategy. Uses AsyncUrlSeeder with SeedingConfig(source="sitemap") to fetch sitemap URLs. Supports optional include_patterns for sitemap filtering. Returns list of URL strings, empty list on failure.

### read_url_file()

Reads URL list from text file (one URL per line). Used with --url-file flag to skip discovery entirely and crawl a pre-curated list.

### discover_urls()

BFS crawl with `prefetch=True` for fast URL discovery. Applies DomainFilter, ContentTypeFilter, optional URLPatternFilter. Returns deduplicated URL list with trailing slash normalization.

### crawl_urls()

Parallel crawl of discovered URLs via `arun_many()` with `SemaphoreDispatcher(max_session_permit=10)`. Uses `networkidle` wait strategy and `DefaultMarkdownGenerator` for full content extraction.

### crawl_bfs()

Fallback: Serial BFS crawl with full browser rendering. For JS-heavy/SPA sites where prefetch cannot discover links. Same filters as discover_urls but with `networkidle` and `DefaultMarkdownGenerator`.

### CLI

```bash
# Auto-detection cascade (sitemap → prefetch → BFS)
python crawl_site.py --url "https://sbert.net" --output-dir "./output"

# Force specific strategy
python crawl_site.py --url "https://docs.example.com" --output-dir "./output" --strategy sitemap

# Pre-filtered URL file (skips discovery)
python crawl_site.py --url "https://playwright.dev" --url-file urls_filtered.txt --output-dir "./output"

# With URL pattern filter
python crawl_site.py --url "https://docs.pytorch.org/docs/stable/mps.html" --output-dir "./output" --include-patterns "*stable*mps*"
```

## Architecture

Content extraction is delegated entirely to Crawl4AI (v0.8.0):
- **Anti-bot evasion:** Level 3 always active — BrowserConfig(enable_stealth=True) + UndetectedAdapter + AsyncPlaywrightCrawlerStrategy. Removes navigator.webdriver, modifies fingerprints, applies deep-level CDP patches. Limitation: Cloudflare with headless=True still blocks (ResearchGate).
- **Browser management:** Crawl4AI manages Playwright/Patchright internally
- **JavaScript rendering:** scrape_url uses `networkidle` with `domcontentloaded` fallback; explore_site uses `prefetch=True` (HTML + links only, no rendering)
- **Noise removal:** Three layers — DOM cleanup (overlays), CSS selector exclusion (cookie banners), content scoring (PruningFilter)
- **Markdown generation:** Two modes depending on use case:
  - **scrape_url (MCP tool):** PruningContentFilter(0.48) + fit_markdown — noise-filtered, for relevance assessment
  - **crawl_site (export script):** DefaultMarkdownGenerator without filter + raw_markdown — full fidelity, noise handled by downstream RAG cleanup agent
