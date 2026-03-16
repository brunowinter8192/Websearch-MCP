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

### is_cloudflare_content()

Separate Cloudflare detection function with same patterns as is_garbage_content() check #5. Used by `try_scrape_raw()` to return `CLOUDFLARE_SENTINEL` instead of empty string, enabling `scrape_url_raw_workflow()` to give a specific "Cloudflare-protected" error message to the user instead of generic "No content extracted".

### truncate_content()

Truncates content if exceeding maximum length. Attempts to break at paragraph boundary for clean truncation. Appends truncation notice when content is cut.

### get_plugin_hint()

Checks URL against PLUGIN_HINTS dict. Returns hint string for domains with dedicated MCP plugins (reddit.com, arxiv.org), empty string otherwise.

### Constants

- `COOKIE_CONSENT_SELECTOR` — CSS selector string matching common cookie consent frameworks: CookieYes (cky-consent, cky-banner, cky-modal), OneTrust, Cookiebot, cc-banner, GDPR, cookie-banner, cookie-consent, cookie-notice, cookie-law. Note: `cky-modal` is critical — CookieYes stores the full Consent Preferences dialog (12K+ chars of cookie descriptions) in this container. Without it, only the small banner (236 chars) is removed.
- `PLUGIN_HINTS` — Dict mapping domains to plugin usage hints
- `DEFAULT_MAX_CONTENT_LENGTH` — 15000 chars
- `MIN_CONTENT_THRESHOLD` — 200 chars. fit_markdown below this triggers raw_markdown fallback.

### scrape_url_raw_workflow()

Raw markdown scraping orchestrator for RAG indexing. Same two-phase browser strategy as `scrape_url_workflow` but uses `DefaultMarkdownGenerator()` without PruningContentFilter and `raw_markdown` output. Saves result as .md file with `<!-- source: URL -->` header to specified output directory. Generates safe filename from URL (domain + path, max 120 chars). Returns file path and char count on success.

### try_scrape_raw()

Raw variant of `try_scrape()`. Uses `raw_markdown` instead of `fit_markdown`, no content filter. Checks `is_cloudflare_content()` BEFORE `MIN_CONTENT_THRESHOLD` check (CF responses are 168-224 bytes, below the 200-byte threshold). Returns `CLOUDFLARE_SENTINEL` on CF detection, empty string on other failures.

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

## explore_site.py (root level CLI)

**Purpose:** URL discovery CLI for the `/crawl-site` command pipeline. Discovers all URLs of a website and saves to a text file. Wraps `crawl_site.discover_urls()` and `crawl_site.discover_urls_sitemap()` with auto-strategy cascade and fixes for common discovery failures.
**Input:** URL, strategy (auto/sitemap/prefetch), optional max-pages/depth/include-patterns/exclude-patterns.
**Output:** Text file with one URL per line + console summary with URL samples.

### Auto-strategy cascade (strategy=auto)

1. **Redirect detection:** HEAD request to resolve final URL. If domain changes (e.g. `docs.anthropic.com` → `platform.claude.com`), uses final domain for BFS DomainFilter. Without this, all links on the redirect target are blocked.
2. **Sitemap check:** Try sitemap discovery, then filter by seed path (see below).
3. **Shallow sitemap threshold:** If sitemap returns `< SITEMAP_MIN_THRESHOLD` (5) URLs, also try prefetch BFS and take the larger result set. Fixes: ReadTheDocs sitemaps with only version root URLs, Cookiebot sitemaps returning only homepage.
4. **No sitemap:** Fall through to prefetch BFS.

### resolve_redirect()

HEAD request with `allow_redirects=True` to resolve redirect chains before BFS. Returns `(final_url, final_domain)`. Fixes discovery for `docs.anthropic.com` (→ `platform.claude.com`) and `api.search.brave.com` (→ `api-dashboard.search.brave.com`).

### filter_sitemap_by_seed_path()

Filters sitemap URLs to match the seed URL's path prefix. Fixes: `playwright.dev/python/docs` seed → sitemap returns `/docs/` (JS docs) instead of `/python/docs/` → filter keeps only URLs containing the seed path.

### Constants

- `SITEMAP_MIN_THRESHOLD` — 5. Sitemap with fewer URLs triggers prefetch fallback.
- `UNLIMITED_PAGES` — 100000. Used when `--max-pages 0`.

## crawl_site.py (root level)

**Purpose:** Full website crawl with markdown export. Supports auto-detection cascade (sitemap → prefetch → BFS with SPA auto-detection), direct URL file input, and parallel crawl via `arun_many()` with `SemaphoreDispatcher(concurrency=10)`.
**Input:** URL, output directory, depth, max_pages, optional include/exclude URL patterns, optional --strategy flag, optional --url-file for pre-filtered URL lists.
**Output:** Markdown files in output directory (one per page), with source URL comment header and domain-prefixed filenames.

### Auto-detection cascade (strategy=auto)

1. Try sitemap discovery
2. If no sitemap: try prefetch BFS
3. If prefetch finds ≤1 URL: SPA detected → fall back to full-rendering BFS

### Redirect detection in discover_urls()

HEAD request before constructing DomainFilter. If seed URL redirects to a different domain, uses the final domain for filtering. Same fix as explore_site.py but applied to the BFS discovery function directly.

### save_markdown()

Saves crawled pages as markdown files. Two pre-write checks:
1. **HTTP status check:** Skips pages with `status_code >= 400` (404, 403, etc.). Prints `[skip] <url> (HTTP <code>)`.
2. **Garbage content check:** Calls `is_garbage_content()` (imported from `src/scraper/scrape_url.py`) on the raw markdown. Catches soft-404s (status 200 but "Page not found" content). Prints `[skip] <url> (garbage content)`.

### url_to_filename()

Generates domain-prefixed filenames from URLs. Uses `DOMAIN_PREFIX` dict for known domains (e.g. `docs.searxng.org` → `searxng`), falls back to `domain.replace(".", "_")` for unknown domains. Path segments separated by `__`. Example: `https://docs.crawl4ai.com/core/quickstart` → `crawl4ai__core__quickstart.md`.

### DOMAIN_PREFIX

Dict mapping known domains to short prefixes for filenames. Currently: searxng, crawl4ai, playwright, tor, cookieyes, onetrust, sitemaps, trafilatura, anthropic, cookiebot.

### CLI

```bash
# Auto-detection cascade (sitemap → prefetch → BFS)
python crawl_site.py --url "https://sbert.net" --output-dir "./output"

# Force specific strategy
python crawl_site.py --url "https://docs.example.com" --output-dir "./output" --strategy sitemap

# Pre-filtered URL file (skips discovery)
python crawl_site.py --url "https://playwright.dev" --url-file urls_filtered.txt --output-dir "./output"
```

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
