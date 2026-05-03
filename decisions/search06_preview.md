# search06 — URL Content Preview

## Status Quo (IST)

Default-on preview feature added 2026-05-03. Every `search_web_workflow` call fetches `og:description` and `meta name="description"` from the top-20 result URLs after dedup, before format.

**Parameters (first cut — see bead searxng-j0r comment 2026-04-30):**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `PREVIEW_TOP_N` | 20 | Covers a full 2-page result set; beyond top-20 value drops fast |
| `PREVIEW_CONCURRENCY` | 8 | Semaphore cap — empirically ~1.5s wall overhead at 20 URLs |
| `PREVIEW_TIMEOUT` | 3s | Per-URL; aggressive to keep total latency bounded |
| Fail behaviour | Silent skip | `preview=None` if fetch fails, format skips block |
| What is fetched | og:description + meta:description | HTTP-only, no browser, no Crawl4AI |

**Integration point in `search_web.py`:** after `_deduplicate`, before `_format_results`. Single `await fetch_previews(deduped)` call in `search_web_workflow`. `search_batch_workflow` inherits automatically (calls `search_web_workflow` internally).

**Output format (`_format_results`):**
```
N. {title}
   URL: {url}
   Snippet: {engine snippet}
   Preview (og): {og:description}       ← shown if present
   Preview (meta): {meta description}   ← shown if present and differs from og
```

## Evidenz

Smoke run `dev/search_pipeline/05_search_smoke.py --engines google duckduckgo` over 30 baseline queries.

<!-- Populated after first smoke run — report path: dev/search_pipeline/01_reports/search_smoke_<ts>.md -->

## Quellen

| Source | Type | Notes |
|--------|------|-------|
| [encode/httpx](https://github.com/encode/httpx) | Repo | AsyncClient, timeout, follow_redirects |
| [lxml/lxml](https://github.com/lxml/lxml) | Repo | lxml.html.fromstring, xpath string() extraction |
| searxng-j0r bead comment 2026-04-30 | Internal | Parameter baseline discussion (og+meta, top-20, 3s/8-parallel/silent-skip) |
