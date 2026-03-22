# Crawler Module

Full-site crawl and URL discovery CLI tools. Used by the `/crawl-site` command pipeline for offline documentation indexing.

## crawl_site.py

**Purpose:** Full website crawl with markdown export. Supports auto-detection cascade (sitemap → prefetch → BFS with SPA auto-detection), direct URL file input, and parallel crawl via `arun_many()` with `SemaphoreDispatcher(concurrency=10)`. Saves pages as markdown files with `<!-- source: URL -->` header.
**Input:** URL, output directory, depth, max_pages, optional include/exclude URL patterns, optional strategy flag, optional url-file for pre-filtered URL lists.
**Output:** Markdown files in output directory (one per page), with domain-prefixed filenames.

### CLI

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | required | Seed URL to crawl |
| `--output-dir` | required | Directory to save markdown files |
| `--depth` | 3 | Max crawl depth |
| `--max-pages` | 100 | Max pages to crawl |
| `--strategy` | auto | `auto` (sitemap→prefetch→bfs), `sitemap`, `prefetch`, `bfs` |
| `--exclude-patterns` | None | Comma-separated URL patterns to exclude |
| `--include-patterns` | None | Comma-separated URL patterns to include |
| `--url-file` | None | Path to text file with URLs (one per line) — skips discovery |
| `--no-prefetch` | false | Use serial BFS with full rendering |

```bash
# Auto-detection cascade
python -m src.crawler.crawl_site --url "https://docs.example.com" --output-dir "./output"

# Force strategy
python -m src.crawler.crawl_site --url "https://docs.example.com" --output-dir "./output" --strategy sitemap

# Pre-filtered URL file
python -m src.crawler.crawl_site --url "https://playwright.dev" --url-file urls_filtered.txt --output-dir "./output"
```

## explore_site.py

**Purpose:** URL discovery CLI for the `/crawl-site` command pipeline. Discovers all URLs of a website and saves to a text file. Wraps `crawl_site.discover_urls()` and `crawl_site.discover_urls_sitemap()` with auto-strategy cascade, redirect detection, and shallow sitemap fallback.
**Input:** URL, strategy (auto/sitemap/prefetch), optional max-pages/depth/include-patterns/exclude-patterns/output/append.
**Output:** Text file with one URL per line plus console summary with URL samples.

### CLI

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | required | Seed URL to explore |
| `--strategy` | auto | `auto` (sitemap→prefetch), `sitemap`, `prefetch` |
| `--max-pages` | 200 | Max pages to discover |
| `--depth` | 10 | Max crawl depth for prefetch BFS |
| `--output` | `/tmp/explore_<domain>_urls.txt` | Output file path |
| `--append` | false | Append to output file instead of overwrite |
| `--include-patterns` | None | Comma-separated URL patterns to include |
| `--exclude-patterns` | None | Comma-separated URL patterns to exclude |

```bash
# Auto-detection cascade
python -m src.crawler.explore_site --url "https://docs.example.com"

# Continue discovery run
python -m src.crawler.explore_site --url "https://docs.example.com" --max-pages 400 --append

# Force prefetch with depth limit
python -m src.crawler.explore_site --url "https://docs.example.com" --strategy prefetch --depth 5
```
