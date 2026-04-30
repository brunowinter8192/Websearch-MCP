---
name: web-research
description: SearXNG web research — CLI tool reference (search_web, scrape_url, scrape_url_raw, explore_site, download_pdf)
---

# SearXNG Web Research — Skill

Web research CLI plugin with 4 active search engines (Google, Bing, Google Scholar, CrossRef), Crawl4AI-based scraping, and site exploration. Each invocation is a fresh CLI process — fire calls in parallel for maximum throughput.

## CLI Invocation

All tools are invoked via the `searxng-cli` wrapper (installed at `~/.local/bin/searxng-cli`, in PATH):

```
searxng-cli <cmd> [args]
```

### Quick Reference — All 5 Tools

```bash
# Search
searxng-cli search_web "machine learning retrieval" --category general --pages 3
searxng-cli search_web "SPLADE sparse retrieval" --engines "google scholar,crossref" --pages 3
searxng-cli search_web "RAG pipeline python" --language de --time-range month

# Scrape
searxng-cli scrape_url "https://example.com/article"
searxng-cli scrape_url "https://docs.example.com/api" --max-content-length 30000

# Scrape to file (RAG indexing)
searxng-cli scrape_url_raw "https://example.com/article" /tmp/rag_output/

# Explore site structure
searxng-cli explore_site "https://docs.example.com" --max-pages 50
searxng-cli explore_site "https://example.com" --url-pattern ".*\/blog\/.*"

# Download PDF
searxng-cli download_pdf "https://arxiv.org/pdf/2310.01526" --output-dir /tmp/papers/
```

On error (import failure, missing dependency, engine timeout): the CLI prints to stderr and exits non-zero.

## Tools

| Tool | Purpose |
|------|---------|
| search_web | Search across 4 engines in parallel. Returns deduplicated results with title, URL, full snippet |
| scrape_url | Fetch page content as filtered markdown (PruningContentFilter). For in-conversation reading |
| scrape_url_raw | Fetch page content as raw markdown and save as .md file. For RAG indexing |
| explore_site | Discover URLs via sitemap + BFS prefetch. Returns structured URL list |
| download_pdf | Download PDF file from URL to local disk |

## Parameter Reference

### search_web

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query (2–5 keywords) |
| --category | general/news/it/science | general | Content category |
| --language | str | en | ISO language code (e.g. "de") |
| --time-range | day/month/year | None | Restrict results by recency |
| --engines | str | None | Comma-separated engine list (e.g. "google,bing" or "google scholar,crossref") |
| --pages | int | 3 | Result pages to fetch and combine (~50 results/page, deduped) |

**Output:** Plain text numbered list — title, URL, full snippet per result. Up to 50 results per page × pages.

**Engine set:** Google, Bing, Google Scholar, CrossRef are always active. Use `--engines` to override and target specific engines.

### scrape_url

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | URL to fetch and convert to markdown |
| --max-content-length | int | 15000 | Character limit for returned content |

**Output:** Filtered markdown with `# Content from: <url>` header.

**Plugin routing:** arxiv.org, github.com, reddit.com URLs are automatically rejected with a routing message — use the dedicated plugins instead.

### scrape_url_raw

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | URL to scrape and save as markdown file |
| output_dir | str | required | Directory to save the .md file (created if not exists) |

**Output:** Confirmation with file path and char count. File saved with `<!-- source: URL -->` header.

**Plugin routing:** Same blocking as scrape_url — routed domains return a message, no file is saved.

### explore_site

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | Root URL to explore |
| --max-pages | int | 200 | Max pages to discover |
| --url-pattern | str | None | Regex filter for discovered URLs |

**Output:** Structured URL list discovered via sitemap → BFS cascade. MAX_DEPTH=10, TIMEOUT=120s.

### download_pdf

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | URL of the PDF to download |
| --output-dir | str | /tmp | Directory to save the downloaded PDF |

**Output:** Confirmation with file path and file size.

## Search Strategy

### Parallel 4-queries pattern

Fire 4 `searxng-cli search_web` calls in parallel, each with a query variation. Each call queries all 4 engines (Google, Bing, Scholar, CrossRef) simultaneously → 16 concurrent browser tabs total. Results are deduplicated across calls at report time.

```bash
# Example: 4 parallel calls for a deep research task
searxng-cli search_web "SPLADE sparse retrieval" --pages 3
searxng-cli search_web "sparse vector retrieval benchmark" --pages 3
searxng-cli search_web "SPLADE vs BM25 performance" --pages 3
searxng-cli search_web "learned sparse retrieval neural" --pages 3
```

**Query tips:**
- Keep queries short and keyword-focused (2–5 words)
- Try different angles: "X tutorial", "X implementation", "X benchmark", "X vs Y"
- "X best practices 2025" for recent content

### Academic / paper topics

For queries containing: benchmark, evaluation, paper, study, performance, NDCG, recall, precision, F1, accuracy, dataset, methodology, experiment, ablation, SOTA — add a dedicated academic query with `--engines "google scholar,crossref"`:

```bash
searxng-cli search_web "SPLADE retrieval NDCG" --engines "google scholar,crossref" --pages 3
```

### Language

For German-language research, add `--language de` to all queries. This filters results to German-language content.

### Workflow

1. **Search broadly:** Fire 4+ parallel queries with variations
2. **Filter results:** Categorize as scrape targets vs. plugin-routed (see Plugin Routing below)
3. **Scrape aggressively:** Call `searxng-cli scrape_url` on all relevant non-plugin URLs
4. **Report everything:** Return all findings using the Report Format below

For multi-topic tasks: before moving to the next topic, verify ≥5 unique URLs scraped for the current topic and ≥2 HIGH quality sources. Fire 2–3 additional topic-specific queries if below minimum.

For single-topic tasks: target 10+ scraped URLs. Fire additional queries if below 10 after initial batch.

**Cookie wall detection:** If scrape output contains only consent/GDPR text, mark as `[cookie wall]` — do NOT rate as HIGH quality. Use the search snippet as fallback, labeled "Source: search snippet (scrape blocked by cookie wall)".

**PDF URLs:** If a result URL ends in `.pdf`, call `download_pdf` instead of `scrape_url`. Report as `[PDF downloaded: /tmp/filename.pdf]`.

## Plugin Routing (CRITICAL)

**Do NOT scrape these domains — report them for plugin-based access:**

| Domain | Action |
|--------|--------|
| arxiv.org | Report: "Use RAG plugin (mcp__rag__search_hybrid) or /rag:pdf-convert" |
| github.com | Report: "Use GitHub Research plugin (github__get_file_content)" |
| reddit.com | Report: "Use Reddit plugin (reddit__search_posts)" |
| youtube.com | Skip entirely. Video content cannot be scraped. |

`scrape_url` and `scrape_url_raw` enforce this routing at the CLI level — they will return a routing message and exit without scraping. No need to pre-filter manually; scrape calls on routed domains are safe (they fail gracefully).

## Report Format

```
## Scraped Content

### 1. <Title>
**URL:** <url>
**Domain:** <domain>
**Content Quality:** [high/medium/low]
**Key Content:**
[2-5 sentences: What does this page actually contain? Concrete takeaways, code examples, benchmark numbers, methodologies.]

### 2. <Title>
...

[ALL scraped URLs, not limited to 10]

## Plugin-Routed URLs

These URLs require dedicated plugins for proper access:

### arxiv.org (Use RAG plugin)
- <url> — <title>

### github.com (Use GitHub Research plugin)
- <url> — <title>

### reddit.com (Use Reddit plugin)
- <url> — <title>

## Search Metadata
**Queries Used:** query1, query2, query3, ...
**Total Results Reviewed:** N
**URLs Scraped:** N
**Plugin-Routed:** N
**Skipped (garbage/thin):** N
```

## Content Assessment

**HIGH quality:** Tutorials with code, benchmarks with numbers, API docs with examples, research papers with methodology
**MEDIUM quality:** Blog posts with some substance, overviews with useful links, discussion with concrete answers
**LOW quality:** Thin wrapper around other content, mostly links, surface-level overview without depth

## Scraping Tips

- **Default `--max-content-length` is 15000** — sufficient for most articles/docs. Increase for long documentation pages.
- **JavaScript-rendered content** is supported — Playwright renders the page before extraction.
- **Content-focused sites** (articles, docs, wikis) produce the best results. The scraper is optimized for semantic HTML.
- **Truncation** preserves paragraph boundaries — content is cut at the nearest double newline.
- **Images** are included as markdown references (small/avatar images are filtered out).
- **Scrape before summarizing:** Never summarize from search snippets alone. If a page has content, scrape it.
- **Quantity over perfection:** 20 scraped URLs with quick assessments > 5 carefully curated summaries.

## Known Limitations

- **Up to ~150 results per query** — CLI fetches 3 pages by default and deduplicates across engines
- **Scraper optimized for content sites** — articles, docs, wikis work best
- **scrape_url uses PruningContentFilter** — may damage code blocks. Use `scrape_url_raw` for full fidelity
- **Login-protected pages** will return login forms, not content
- **PDF URLs (.pdf)** — use `download_pdf` to save the file locally. Do NOT use `scrape_url` on PDFs.

## When to Stop

Stop when ALL of:
- Exhausted 4+ query variations (per parallel batch)
- Scraped all non-plugin URLs from top results
- Additional queries return mostly duplicates
