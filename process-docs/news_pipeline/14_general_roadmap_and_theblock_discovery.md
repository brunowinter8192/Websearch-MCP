# 14 — General News-Source Roadmap + The Block Discovery Status

**Date:** 2026-06-10
**State:** Roadmap crystallized; The Block = first source under it, discovery IN PROGRESS (CF-blocked, resume next session).

## General Roadmap (every new news source)

Methodical procedure, crystallized from CoinDesk (iter 01–13) + The Block. Applies to all subsequent news sites.

1. **Pull the source** — identify discovery surfaces (sitemap families, RSS, UI listing).
2. **Find the method that yields the MOST unique article URLs.** Anchor = max total unique URLs on the domain (= backfill coverage), NOT the 48h window. Compare methods empirically; this step INCLUDES solving any anti-bot (e.g. Cloudflare) that gates the URLs. Winner = the method (or union) with the most unique URLs.
3. **Backfill as deep as the source's own surface allows + site-specific cleaning** — scrape the full available archive; take whatever depth the source's discovery surface gives (2017, 2023, whatever the floor is — the exact depth target is secondary, max available coverage is the goal). No external-aggregator chase for deeper-than-source history. Cleaning adapted per-site (NOT dynamic).
4. **Add the 48h going-forward pipe** — the daily delta on top of the backfill.

**Principles:** no assumptions — read sources, define empirically. No PRODUCTION fallback chains (explorative roadmaps to FIND the one method are correct and encouraged). Per-site cleaning, not dynamic. Step 2's anchor and the "2 contradictory results" resolution, and the channel-independence selection criterion, were both established in earlier iterations of this record.

## The Block — Discovery Status (first instance)

**Domain:** theblock.co. Discovery = sitemap-based (Path B; no `__NEXT_DATA__`, only `application/ld+json`).

**Sitemap structure (verified, live):** robots.txt lists `sitemap_tbco_index.xml` (index of 64 sub-sitemaps) + `sitemap_tbco_news.xml` (Google-News, ~48–72h rolling window).

**64-sub taxonomy (verified):**
- `post`×27 — articles, `/post/<id>/<slug>`, archive reaches back to ~2018 (post_0 lastmod 2018-09), ~27k URLs total.
- `linked`×8 — `/linked/<id>/<slug>`, link-out / aggregation posts (~8k).
- `token`×8 — `/price/...` ticker pages (~7.7k, noise).
- ×1–2 each: chart, daily, page, learn, converter, etf, index, person, press-release, rating, stock, treasury, 5 taxonomy subs, authors, news.

**Filter decision:** keep `/post/` (original articles); drop `/linked/` (aggregation — violates the channel-independence criterion), `token`/price, and the non-article families. (Worker classifies by first path segment — mechanical, not editorial; filter decision is ours.)

**Method comparison + finding:** the **full archive-sitemap union is the max-coverage method**. The news-sitemap leaks the older edge — structural Google-News ~48h window; sample window (≥2026-06-08): archive had 56 recent articles, news-sitemap only 40, **16 missing** (news ⊆ archive, news-only=0). RSS (20), news-sitemap (41), bounded UI crawl (28) are tiny recent subsets; completeness-check found no real gap (their IDs sit inside the not-yet-fetched newest archive subs, IDs 403K–404K). No method beats the archive union.

**URL date anchor:** `/post/<id>/<slug>` has NO date in the path → date comes from the sitemap tag (`news:publication_date` in news-sitemap / `lastmod` in archive subs), must be threaded from the discover entry (the same threading lesson from the CoinDesk migration applies directly — no URL-path fallback like CoinDesk had).

**Worker cache state (committed on dev):** ~19,000 `/post/` URLs cached (IDs 136–342,769), ~21 of 64 subs fetched before the CF block hit; ~43 subs (post_21–26 + all non-post families) still missing. Next session resumes from this cache — only the ~43 missing subs need fetching. The CF block and the method to get past it are covered in the following entry.
