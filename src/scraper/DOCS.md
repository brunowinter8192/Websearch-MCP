# Scraper Module

URL scraping and site exploration tools powered by Crawl4AI for SearXNG MCP server.

## scrape_url.py

**Purpose:** URL scraping orchestrator. Uses Crawl4AI's AsyncWebCrawler with PruningContentFilter to extract clean page content as markdown. Two-phase browser strategy: normal browser first, stealth fallback for anti-bot sites.
**Input:** URL string and optional maximum content length (default 15000).
**Output:** Filtered markdown content wrapped in TextContent, or error message with plugin hint on failure.

### scrape_url_workflow()

Main orchestrator. Two-phase approach:

1. **Phase 1: Normal browser** — Standard Crawl4AI without stealth patches. Works for most sites (Wikipedia, docs, blogs). Tries `networkidle` first, falls back to `domcontentloaded`.
2. **Phase 2: Stealth browser** — Only if Phase 1 returns empty. Uses `enable_stealth=True` + `UndetectedAdapter` + `AsyncPlaywrightCrawlerStrategy` (Level 3 anti-bot evasion). For sites with bot detection (e.g. TDS, some news sites).

Noise removal via `excluded_selector=COOKIE_CONSENT_SELECTOR` — CSS selectors matching common cookie consent frameworks. `remove_overlay_elements` is NOT used (destroys Wikipedia content by misclassifying DOM elements as overlays).

On empty result, returns error message with plugin hint if URL matches a known domain with dedicated MCP plugin (Reddit, arxiv).

### try_scrape()

Attempts a single scrape with given browser config, optional crawler strategy, and wait strategy. Content selection: `fit_markdown` if >= 200 chars (MIN_CONTENT_THRESHOLD), otherwise falls back to `raw_markdown`. This prevents PruningContentFilter from destroying table-heavy content (e.g. Wikipedia). Checks content via `is_garbage_content()` — if content is an error page, cookie wall, or Crawl4AI error message, returns empty string to trigger fallback chain.

### is_garbage_content()

Detects five categories of garbage content returned as markdown:
1. **Crawl4AI errors:** "Crawl4AI Error:", "Document is empty", "page is not fully supported"
2. **HTTP error pages:** Short content (<1000 chars) with 404/403/NOT_FOUND/Access Denied keywords
3. **Cookie consent walls:** High density of cookie-related terms (>15 occurrences of "cookie"/"consent"/"duration" in first 5000 chars + "consent preferences" or "cookieyes" or "cookie preferences" present). Note: Amazon uses "cookie preferences" instead of "consent preferences".
4. **Navigation dump pages:** ≥20 non-empty lines AND >60% are standalone markdown link lines (`[text](url)` on their own line). Catches large pages that are pure navigation with no content (e.g. 162KB AWS announcement pages).
5. **Cloudflare/JS challenges:** Short content (<500 chars) containing "checking your browser" or "enable javascript and cookies", OR "just a moment" + "cloudflare" anywhere.

Called by both `try_scrape()` and `try_scrape_raw()` after content extraction.

### truncate_content()

Truncates content if exceeding maximum length. Attempts to break at paragraph boundary for clean truncation. Appends truncation notice when content is cut.

### get_plugin_hint()

Returns generic plugin routing hint for failed scrapes on domains that may have dedicated MCP plugins.

### Constants

- `COOKIE_CONSENT_SELECTOR` — CSS selector string matching common cookie consent frameworks: CookieYes (cky-consent, cky-banner, cky-modal), OneTrust, Cookiebot, cc-banner, GDPR, cookie-banner, cookie-consent, cookie-notice, cookie-law. Note: `cky-modal` is critical — CookieYes stores the full Consent Preferences dialog (12K+ chars of cookie descriptions) in this container. Without it, only the small banner (236 chars) is removed.
- `DEFAULT_MAX_CONTENT_LENGTH` — 15000 chars
- `MIN_CONTENT_THRESHOLD` — 200 chars. fit_markdown below this triggers raw_markdown fallback.

## scrape_url_raw.py

**Purpose:** Raw markdown scraping orchestrator for RAG indexing. Same two-phase browser strategy as `scrape_url.py` (normal → stealth fallback) but uses `DefaultMarkdownGenerator()` without PruningContentFilter and saves `raw_markdown` output to a .md file with `<!-- source: URL -->` header. Generates safe filename from URL (domain + path, max 120 chars).
**Input:** URL string and output directory path.
**Output:** TextContent with file path and char count on success, or error message on failure (Cloudflare-specific message when CF-protected).

## explore_site.py

**Purpose:** Site structure reconnaissance. Fast URL discovery via prefetch mode (~200-500ms per page instead of 2-5s). Returns page counts, depth distribution, and URL samples for noise pattern identification. No file export — analysis only.
**Input:** URL string, optional max_pages limit (default 50), optional url_pattern wildcard filter.
**Output:** TextContent with formatted Markdown summary (page count, total chars, depth distribution, 5 URL samples per depth, recommended strategy). Partial results on timeout (120s) with warning.

### explore_site_workflow()

Main orchestrator. Checks sitemap first, then runs BFS discovery. Recommends strategy based on results: sitemap (if found), prefetch (if >1 page discovered), or bfs (JS-heavy/SPA, only 1 page found).

### check_sitemap()

Checks if site has a sitemap via AsyncUrlSeeder. Returns list of discovered URLs (empty list if no sitemap found).

### crawl_for_discovery()

BFS crawl with DomainFilter + ContentTypeFilter (text/html) + optional URLPatternFilter. Uses `prefetch=True` — skips markdown generation and content extraction, only fetches HTML and extracts links. Wrapped in `asyncio.wait_for()` with 120s timeout. Returns tuple `(timed_out: bool, results: list)`. max_depth=10 internally.

### build_site_map()

Aggregates crawl results into summary dict. Deduplicates URLs (trailing slash normalization), extracts depth from metadata, computes per-depth statistics, picks URL samples via `pick_url_samples()`. When `sitemap_urls` provided: integrates sitemap URLs with depth estimated from URL path segments (chars=0 since not fetched), deduplicates against BFS results.

### pick_url_samples()

Selects 5 evenly-spaced URLs per depth level for noise pattern identification.

### format_site_map()

Formats site map dict as readable Markdown with recommended strategy.

## Architecture

Content extraction is delegated entirely to Crawl4AI (v0.8.0):
- **Browser strategy:** Normal browser first, Stealth (Level 3) as fallback. UndetectedAdapter breaks some sites (Wikipedia) by patching the browser too aggressively.
- **Cookie removal:** CSS selector exclusion via `excluded_selector`. Specific selectors per framework (CookieYes, OneTrust, Cookiebot, GDPR etc.). `remove_overlay_elements` is NOT used — it removes legitimate content on some sites.
- **Content filtering:** PruningContentFilter(0.48) + fit_markdown for relevance assessment. raw_markdown fallback when filtered content < 200 chars (table-heavy pages).
- **Markdown generation:** Three modes:
  - **scrape_url (MCP tool):** PruningContentFilter + fit_markdown — noise-filtered, for in-conversation reading
  - **scrape_url_raw (MCP tool):** DefaultMarkdownGenerator + raw_markdown — full fidelity, saves to file for RAG indexing
  - **crawl_site (export script):** DefaultMarkdownGenerator + raw_markdown — full fidelity, batch crawl, noise handled by downstream RAG cleanup agent
- **Known issue:** Crawl4AI captures stdout — always write debug output to files, not print()
- **Cookie-Wall debugging:** Inject JS to enumerate `[class*='cky']` elements and check textLen per element. The largest container is usually the unmissed consent dialog. Add its class to COOKIE_CONSENT_SELECTOR.
