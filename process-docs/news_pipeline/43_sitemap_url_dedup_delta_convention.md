# 43 — Discovery convention: sitemap-URL-set + hash-dedup, no lastmod date filtering

Supersedes the `48h` mode and the `lastmod`-range mode from prior stages for The Block. Origin: a 2018
backfill test returned only 19 articles for the whole year, which forced the question of what date
info the sitemaps actually carry.

## Trigger — the 19-article anomaly

`--timeframe 2018-01-01:2018-12-31` → 19 entries. Investigation showed this is NOT "articles published
in 2018" but "articles whose sitemap `<lastmod>` falls in 2018". The two are very different.

## Evidence — what the sitemaps carry (cached XML, `dev/news_pipeline/theblock/acquire_pipe/acquire_pipe_output/`)

A `<url>` block has exactly four children: `<loc>`, `<lastmod>`, `<changefreq>`, `<priority>`.
The ONLY date field is `<lastmod>`. Counted across all 27 `post_type_post` sub-sitemaps:

- `<lastmod>`: 26,926
- `publication_date` / `news:` namespace: **0**

So the sitemap carries no publication date at all. `datePublished` exists only inside each article's
JSON-LD and is known only POST-fetch.

### Sub-sitemaps are paginated by `lastmod`, ascending, contiguous

27 `post_type_post` subs (`post_0` … `post_26`), 1000 URLs each (last = 926) = 26,926 total.
Per-sub `lastmod` windows are contiguous and increase with sub-number:

| sub | urls | lastmod_min | lastmod_max |
|---|---|---|---|
| 0 | 1000 | 2018-09-10 | 2020-03-24 |
| 1 | 1000 | 2020-03-24 | 2021-06-17 |
| 2 | 1000 | 2021-06-17 | 2022-04-07 |
| … | … | … | … |
| 25 | 1000 | 2026-02-19 | 2026-04-19 |
| 26 | 926 | 2026-04-20 | 2026-06-15 (≈now) |

Post-IDs are scattered WITHIN each sub (post_0 holds IDs 202…59671) → ID is not the sort key, `lastmod`
is. **Consequence:** when an old article is re-touched, its `lastmod` bumps and it MIGRATES to a
higher-numbered sub. post_0 (the oldest) already shows `lastmod` up to 2020-03. That is exactly why a
`lastmod ∈ 2018` filter catches only the handful never-touched-since-2018 articles (the 19): the rest
of 2018's articles have bubbled up into later subs.

## Decision — the convention

The sitemap URL-set is the source of truth for WHICH articles exist. Dedup on URL-hash
(`dedup_mode="hash_only"`, glob `theblock__*__{hash}.md`) decides what is new. Scrape the difference.
**No date from the sitemap is used for inclusion/exclusion** — `lastmod`'s unreliability becomes
irrelevant because it is never a gate.

### Discover modes (all date-filter-free)

| Mode | Target subs | Use |
|---|---|---|
| `full` | all 27 post subs | complete backfill (~26,926 URLs) |
| `delta` (default) | top-2 highest-numbered subs | recurring run — replaces `48h` |
| `sub:N` | the single sub with index N | bounded backfill chunk (e.g. `sub:0` = oldest 1000) |

- **Delta = top-2, not top-1** — rollover safety. When the highest sub fills to 1000 and a new one is
  created, fetching only the highest would briefly miss articles now sitting in the second-highest.
  Top-2 (≈2000 recent URLs, dedup makes the overlap free) closes that gap. A new publication always
  has `lastmod = now = max` → always lands in the highest sub; a re-touched old article lands there
  too but is skipped by hash-dedup. So top-2 + hash-dedup = exactly the genuinely-new articles.
- **Skip-index:** everything except `delta` auto-skips RAG indexing (inspect first); `delta` (the
  routine run) auto-indexes. Replaces the old `non-48h → skip` rule with `non-delta → skip`.

## Range mode addition (`sub:A-B`)

Added `sub:A-B` as a fourth discover mode to support contiguous multi-sub backfill without resorting to `full`. The user works in chunks (e.g. subs 24-27 of 27), and having to issue a separate `sub:N` call per sub was impractical. The new mode adds `_subs_in_range(urls, a, b)` in `discover.py` — returns all existing subs whose trailing index falls in [A, B] inclusive, sorted descending (newest-first, consistent with `delta`). Validation mirrors the existing `sub:N` pattern: non-int parts and A > B raise `RuntimeError` before any URL lookup; an empty result set (valid range but no matching subs) raises the same way `sub:N` does when not found. The `--skip-index` auto-skip in `__main__.py` already covers all non-delta timeframes, so `sub:A-B` gets that behaviour for free.

## Open question — update-blindness of hash-dedup (user-flagged, accepted)

`hash_only` dedup keys on URL existence → one snapshot per URL forever. If an already-scraped article
is later edited (content changed, same URL), it is NOT re-fetched — we keep the first-fetch version.
For the article-sentiment goal this is correct (we want the as-published text, not later edits), and
post-publish substance changes are assumed rare. Flagged as potentially worth a later verification:
how often / how materially do The Block articles change after publication? No clean alternative seen
that wouldn't re-introduce a content-hash or lastmod comparison (the very signal we just discarded).
Status: ACCEPTED trade-off, verification OPEN.
