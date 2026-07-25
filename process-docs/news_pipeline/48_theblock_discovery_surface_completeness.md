# 48 — The Block discovery surface: is the sitemap complete, or is there a deeper endpoint?

Open question raised after the CoinDesk timeline-API work. NOT started — parked follow-up.

## The assumption being questioned

The Block discovery uses the XML sitemap exclusively: `sitemap_tbco_index.xml` → 64 `post_type_post`
sub-sitemaps → ~47k article URLs. The sitemap was adopted as THE
discovery surface from the first session and never compared against any alternative internal
endpoint. "The sitemap delivers everything" is an assumption, not a measured fact.

## Why it's worth checking

CoinDesk is the counter-example. Its public article-sitemap aggregates to only ~1198 unique URLs over
~1 year, while its internal cursor-paginated timeline API yields 61,628 URLs back to 2017
— ~50× more, and the only complete surface. A site's sitemap CAN be drastically incomplete. The Block's
sitemap completeness has never been tested the same way; if it is incomplete, the backfill silently
misses articles — the exact trap CoinDesk's sitemap would have been.

## What to verify (conclusively)

- **Internal API probe.** Does theblock.co's frontend call an internal "load more" / timeline-style API
  (analogous to CoinDesk's `/api/v1/articles/timeline`) that enumerates more / older articles than the
  sitemap? Capture via browser network/HAR on the article feed, as done for CoinDesk.
- **Sitemap floor sanity.** Oldest article across the 64 sub-sitemaps vs The Block's actual founding /
  earliest published article. A floor well short of founding ⇒ incomplete.
- **Count + span compare.** If an alternative surface exists, compare its unique-URL count and date span
  against the ~47k sitemap inventory.

## Status

Not started. The Block backfill is currently planned on the sitemap surface; this check decides whether
that surface is the complete one.
