# 37 — The Block article structure (probe findings)

What we learned from fetching real `/post/` articles — the basis for The Block's cleanup + 48h-delta
design. Probe: `dev/news_pipeline/theblock/probe_48h_article_fetch.py` (parallel proxy_http fetch).

## Article page — server-rendered, body in raw HTML

A fetched `/post/` page (410-430 KB) is **server-rendered**, NOT a JS shell:
- No `__NEXT_DATA__`; only ~9 `<script>`; real `<article>` + `<p>` prose in the HTML.
- A **JSON-LD `NewsArticle`** block carries everything structured:
  - `headline` — title
  - `datePublished` (e.g. `2026-06-13T11:25:20-04:00`) — exact publication time, in the HTML
  - `author` — structured (name + url)
  - `articleBody` — the **full, clean body HTML**, no page chrome

**Cleanup consequence — The Block is simpler than CoinDesk.** No browser / crawl4ai needed (CoinDesk
needed both, plus H1-anchor chrome-stripping). The Block path: proxy_http fetch → parse JSON-LD
`NewsArticle` → `articleBody` HTML→MD. Do NOT scrape raw `<p>` tags (they pull in CSS, nav, tickers).

## Dedup + dates

- URLs are canonical `/post/<id>/<slug>` — numeric post-id, no tracking params → stable dedup key
  (URL-hash / post-id). Same filename-existence dedup as CoinDesk: `theblock__{pubdate}__{hash}.md`.
- `pubdate` source = JSON-LD `datePublished` (clean, exact). Sitemaps carry per-URL `<lastmod>` but
  NO `<news:publication_date>` (count 0 despite the `news:` namespace being declared) — lastmod is the
  sitemap-level recency signal, `datePublished` the article-level truth.

## 48h-delta discovery

- Index → article sub-sitemaps are the `post_type_post*` family. Pages are paginated **ascending**
  (`post_type_post_0` starts 2018; newest = highest-numbered). The daily delta fetches only the
  **highest-numbered** post sub-sitemap (or last 1-2), not all ~27.
- Parse `<loc>` + `<lastmod>`, filter `lastmod ≥ now − (48h + overlap)`. 24h cadence + 48h window +
  overlap → completeness; filename-existence dedup drops the overlap. Exactly the CoinDesk pattern,
  recency sourced from `<lastmod>` instead of feed order.

## Probe process notes (errors from the same investigation)

- The first probe version full-scanned all 27 `post_type_post` sub-sitemaps to "confirm" the ascending
  pagination — wasteful, the pagination was already established from a raw sitemap, and the run was
  advised to continue. Reworked to fetch only the highest-numbered page.
- The parallel rewrite then had a single-128-wave bug (`random.sample(pool, 128)` — only 128 of ~18k
  tried, no pool walk) → failed on the large `post_26` → fixed to a wave-loop over the full pool.
