---
name: web-research
description: SearXNG web research — tool reference, workflows, and report formats
---

# SearXNG Web Research — Skill

## Tools

| Tool | Purpose |
|------|---------|
| search_web | Search the web via SearXNG. Returns up to 50 results with title, URL, full snippet |
| scrape_url | Fetch page content as filtered markdown (PruningContentFilter). For in-conversation reading |
| scrape_url_raw | Fetch page content as raw markdown and save as .md file. For RAG indexing |
| download_pdf | Download PDF file from URL. Saves to /tmp/ by default or custom directory |

## Search Strategy

Four fundamentally different workflows:

- **Quick search** (user wants links, overviews, or pointers):
  Use `search_web` alone. Returns up to 50 results with title, URL, and full snippet.
  Good for: finding URLs, getting a topic overview, discovering sources.

- **Deep research** (user wants actual content, analysis, or synthesis):
  Use `search_web` first, then `scrape_url` on the most relevant results.
  Good for: reading documentation, extracting tutorials, comparing approaches, analyzing articles.

- **Direct scraping** (user provides a URL):
  Skip search entirely. Use `scrape_url` directly on the given URL.
  Good for: reading a specific page, extracting content from a known source.

- **Scrape for RAG indexing** (user wants to index a URL into knowledge base):
  Use `scrape_url_raw(url, output_dir)` to save full-fidelity raw markdown as .md file.
  Then run `/rag:web-md-index` on the output directory to cleanup + chunk + index.

**Detection:** "Find me articles about X" → quick search. "What does article X say about Y?" → deep research. "Read this URL" → direct scraping. "Index this URL" / "Save this for later" → scrape_url_raw.

## Parameter Reference

### search_web

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query (e.g., "machine learning python tutorial") |
| category | Literal | "general" | Content category: general, news, it, science |
| language | str | "en" | ISO language code |
| time_range | str/None | None | day, month, year |
| engines | str/None | None | Comma-separated engine list (e.g., "google,brave,google scholar") |
| pages | int | 3 | Number of pages to fetch and combine (default 3 = ~150 results) |

**Output:** Plain text numbered list with title, URL, and full snippet per result. Up to 50 results per page.

**Pagination:** The server fetches multiple pages automatically. Use `pages=3` (default) to get up to ~150 deduplicated results per query. Do NOT use `pageno` — pass `pages` instead.

### scrape_url

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | Single URL to fetch and convert to markdown |
| max_content_length | int | 15000 | Character limit for returned content |

**Output:** Filtered markdown with `# Content from: <url>` header.

### scrape_url_raw

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | URL to scrape and save as markdown file |
| output_dir | str | required | Directory to save the .md file (created if not exists) |

**Output:** Confirmation with file path and char count. File saved with `<!-- source: URL -->` header.

### download_pdf

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| url | str | required | URL of the PDF file to download |
| output_dir | str | "/tmp" | Directory to save the downloaded PDF |

**Output:** Confirmation with file path and file size.

## Workflow (MANDATORY)

Maximize data intake. Search broadly, scrape aggressively, return everything useful. Don't curate — collect.

### Step 1: Search Broadly

Fire 5+ search queries with variations:
- Rephrase the topic 3+ ways
- Use category="general" for all queries (includes both web and science engines)
**MANDATORY for academic queries:** When ANY of these words appear in the research topic or query:
  "benchmark", "evaluation", "paper", "study", "performance", "NDCG", "recall", "precision", "F1", "accuracy", "dataset", "methodology", "experiment", "ablation", "state-of-the-art", "SOTA"
  → Fire an additional query with engines="google scholar,semantic scholar,crossref" for EACH such query.
  This is NOT optional.
- For EACH query: `pages=3` is the default — no extra calls needed. The server fetches 3 pages automatically per query.
- Combine engines when useful: engines="google,brave,bing" for web-focused, engines="google scholar,semantic scholar" for academic-focused

**Query tips:**
- Keep queries short and keyword-focused (2-5 words)
- Try different angles: "X tutorial", "X implementation", "X benchmark", "X vs Y"
- "X best practices 2025" for recent content

**Language:** When the research topic is in German or the dispatcher specifies German context:
- Use `language="de"` for ALL queries
- This filters results to German-language content and reduces noise from non-target languages

**Self-Check (MANDATORY before proceeding to Step 2):**
- Did every query use pages=3 (the default)? If you explicitly set pages=1 or pages=2 for any query, re-fire with pages=3.
- Did you fire at least 5 query variations?

### Step 2: Filter Results

From all search results, categorize:

**Plugin-routed** (do NOT scrape):
- arxiv.org → tag as "USE RAG PLUGIN"
- github.com → tag as "USE GITHUB PLUGIN"
- reddit.com → tag as "USE REDDIT PLUGIN"
- youtube.com → SKIP (no useful content from scraping)

**Scrape targets** (everything else that looks relevant)

### Step 3: Scrape Aggressively

For ALL non-plugin URLs that look relevant:
- Call `scrape_url` to read the actual page content
- If a page is thin or garbage, note it and move on
- **Cookie wall detection:** If scrape output contains only consent/GDPR text (no actual content), mark as `[cookie wall]` in report — do NOT rate as HIGH quality. Use the search snippet as fallback and label it explicitly: "Source: search snippet (scrape blocked by cookie wall)"
- **PDF URLs:** If a search result URL ends in `.pdf`, call `download_pdf(url)` to save it locally. Report in output as `[PDF downloaded: /tmp/filename.pdf]`. Do NOT attempt to scrape PDF URLs.
- Look for: concrete content, code, benchmarks, how-tos, data

**For multi-topic tasks:**
Before moving to the next topic, verify:
- [ ] ≥5 unique URLs scraped for THIS topic
- [ ] At least 2 HIGH quality sources for THIS topic
- If either is missing: fire 2-3 additional topic-specific queries before moving on

**For single-topic tasks:**
Target: 10+ scraped URLs. Fire additional queries if below 10 after initial batch.

Don't stop at 5 — scrape 10, 15, 20 if they exist (secondary target once per-topic minimums are met).

### Step 4: Report Everything

Return ALL findings organized clearly using the Report Format below.

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

These URLs require dedicated MCP plugins for proper access:

### arxiv.org (Use RAG plugin)
- <url> — <title>
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

## Guidelines

- **Scrape before summarizing**: Never summarize from search snippets alone
- **Be specific**: "Covers 5 chunking strategies with Python code and RAGAS benchmark scores" > "Discusses chunking"
- **Quantity over perfection**: 20 scraped URLs with quick assessments > 5 carefully curated summaries
- **Don't self-censor**: If a page has content, include it. Let the caller decide what's useful.
- **Note dates**: Flag content dates when visible. Recent > old for rapidly evolving topics.

## Plugin Routing (CRITICAL)

**Do NOT scrape these domains — report them for plugin-based access:**

| Domain | Action |
|--------|--------|
| arxiv.org | Report: "Use RAG plugin (mcp__rag__search_hybrid) or /rag:pdf-convert" |
| github.com | Report: "Use GitHub Research plugin (github__get_file_content)" |
| reddit.com | Report: "Use Reddit plugin (reddit__search_posts)" |
| youtube.com | Skip entirely. Video content cannot be scraped. |

## Scraping Tips

- **Default max_content_length is 15000** — sufficient for most articles/docs. Increase for long documentation pages.
- **JavaScript-rendered content** is supported — Playwright renders the page before extraction.
- **Content-focused sites** (articles, docs, wikis) produce the best results. The scraper is optimized for semantic HTML.
- **Truncation** preserves paragraph boundaries — content is cut at the nearest double newline.
- **Images** are included as markdown references (small/avatar images are filtered out).

## Known Limitations

- **SearXNG instance required** — must be running on localhost:8080
- **Up to ~150 results per query** — server fetches 3 pages by default and deduplicates
- **Scraper optimized for content sites** — articles, docs, wikis work best
- **scrape_url uses PruningContentFilter** — may damage code blocks. Use scrape_url_raw for full fidelity
- **Login-protected pages** will return login forms, not content
- **PDF URLs (.pdf)** — use `download_pdf(url)` to save the file locally. Do NOT use scrape_url on PDFs.

## When to Stop

Stop when ALL of:
- Exhausted 5+ query variations with pagination
- Scraped all non-plugin URLs from top results
- Additional queries return mostly duplicates
