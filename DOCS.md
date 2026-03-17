# Root Modules

MCP server entry point, batch crawl tools, and startup script.

## server.py

**Purpose:** FastMCP server exposing web search and scraping capabilities as MCP tools. Registers four tools: `search_web`, `scrape_url`, `scrape_url_raw`, `explore_site`.
**Input:** None (server process started by mcp-start.sh or Claude Code).
**Output:** MCP tool responses via FastMCP protocol.

## mcp-start.sh

**Purpose:** MCP server startup script. Starts SearXNG Docker container if not running, bootstraps Python venv if missing (installs requirements.txt, installs Chromium for Playwright), then launches FastMCP server via exec.
**Input:** None.
**Output:** FastMCP server process (exec — replaces shell process).

```bash
./mcp-start.sh
```

## crawl_site.py

**Purpose:** Full website crawl with markdown export. Supports auto-detection cascade (sitemap → prefetch → BFS with SPA auto-detection), direct URL file input, and parallel crawl via `arun_many()` with `SemaphoreDispatcher(concurrency=10)`.
**Input:** URL, output directory, depth, max_pages, optional include/exclude URL patterns, optional `--strategy` flag, optional `--url-file` for pre-filtered URL lists.
**Output:** Markdown files in output directory (one per page), with `<!-- source: URL -->` comment header and domain-prefixed filenames.

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

### CLI

```bash
# Auto-detection cascade (sitemap → prefetch → BFS)
python crawl_site.py --url "https://sbert.net" --output-dir "./output"

# Force specific strategy
python crawl_site.py --url "https://docs.example.com" --output-dir "./output" --strategy sitemap

# Pre-filtered URL file (skips discovery)
python crawl_site.py --url "https://playwright.dev" --url-file urls_filtered.txt --output-dir "./output"
```

## explore_site.py

**Purpose:** URL discovery CLI for the `/crawl-site` command pipeline. Discovers all URLs of a website and saves to a text file. Wraps `crawl_site.discover_urls()` and `crawl_site.discover_urls_sitemap()` with auto-strategy cascade and fixes for common discovery failures.
**Input:** URL, strategy (auto/sitemap/prefetch), optional max-pages/depth/include-patterns/exclude-patterns/output/append.
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
