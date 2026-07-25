# 46 — CoinDesk archive discovery surfaces (pre-feed-window history)

**SUPERSEDED by a later stage's timeline-API HTTP method** — that approach made an archive-specific surface unnecessary.
Records the Wayback archive investigation: why CoinDesk's deep history seemed to need a separate surface,
and why Wayback turned out to be a dead end (incomplete + dirty). Kept for the measurement record and the
2018-cutoff scope decision. See the Resolution section at the bottom.

## Trigger

The feed-traversal work discovers articles via the cursor-paginated timeline feed. Open question
from the user: is the feed "everything" CoinDesk exposes, or do other surfaces yield older / more URLs?

## Findings (this session)

### The deep archive is LIVE
Old CoinDesk articles still resolve 200 on the live site. Verified via curl against URLs pulled from the
Wayback CDX index, e.g. `https://www.coindesk.com/2018-a-record-breaking-year-for-crypto-exchange-hacks`
→ HTTP 200. So the archive content exists and is scrapeable — the problem is purely DISCOVERY (enumerating
the old URLs), not availability.

### URL-scheme transition ~2020 (the structural key)
CoinDesk changed its article URL scheme around 2020:
- **Pre-2020:** flat slug, often year-prefixed — `coindesk.com/2018-<slug>` (no date path).
- **2020 onward:** date path with section — `coindesk.com/<section>/YYYY/MM/DD/<slug>`.

Evidence: Wayback CDX flat-slug counts (`coindesk.com/YYYY-*`, collapse=urlkey, statuscode:200) are
non-zero for 2015–2019 and **zero for 2020–2026**. (Caveat: these counts only catch articles whose slug
*starts with the year* — a minority — so they do NOT measure true per-year density; they only pin the
scheme transition.)

### Implication for the feed discover
The production/dev discover recognizes article URLs via `DATE_RE = /\d{4}/\d{2}/\d{2}/` (date path only).
Pre-2020 flat-slug URLs do NOT match → if the feed paginates back into the flat-slug era, those articles
are filtered out as non-matching, the run sees "0 new", and plateau-terminates. So the feed + current
filter is expected to densely cover **~2020 → today** and self-floor around the 2020 transition — NOT the
flat-slug archive. (Hypothesis — the feed's real floor is measured by the earlier deep run.)

### Candidate archive-enumeration surface: Wayback CDX
The Wayback Machine CDX API lists effectively every coindesk.com URL ever archived and is a plain HTTP
query (no browser, no clicking). Pattern for an archive backfill: CDX → filter to article URLs → dedup →
scrape the LIVE coindesk pages (200). Wayback is the URL SOURCE; the live site is the scrape source.

### Sitemap is not the archive surface
From an earlier finding: the 19 `articles-*.xml` sitemaps aggregate to ~1198 unique URLs over ~1 year — shallower than
the feed, not a route to the deep archive.

## Scope cut (user)

Backfill only **2018 onward**. Rationale: Binance candles start ~2017; news older than the candle history
has nothing to map onto, so pre-2018 articles are out of scope regardless of reachability.

## Resolution — Wayback is a DEAD END, superseded by the timeline API

Wayback density WAS then measured properly (full CDX pull, `collapse=urlkey`, strict date-path filter):
**~15,500 clean date-path articles total.** The URL-scheme story above was largely a red herring — date-path
URLs (`/section/YYYY/MM/DD/<slug>`) exist in the CDX back to **2013** (CoinDesk migrated old articles), so
the "2020 transition" is NOT a hard boundary. But Wayback is unusable as a backbone:

- **Incomplete:** ~15.5k vs CoinDesk's real ~60k+ output (≈20–25% even for the well-covered years);
  2017–2019 nearly empty (28 / 15 / 171 strict articles for three whole years vs thousands actually published).
- **Dirty:** crawl-mangled URLs (line-wrapped `busi-ness`, truncated slugs ending in `-`).

Two measurement traps along the way (recorded so they're not repeated): (a) a loose `/YYYY/MM/DD/`-anywhere
grep counted the `?p=…datePublished:…` JSON-LD-noise URLs as "articles" (inflated to ~91k — false); (b) the
CDX `filter=mimetype:text/html` + a broken resume-key loop made one worker see only ~13k total / 3 date-path
(false). The truth: 463,536 total distinct coindesk URLs, ~15.5k strict date-path articles.

The feed-floor / archive-vs-feed split is moot: **the timeline API walked by its cursor over plain HTTP gives
the COMPLETE inventory to the floor** — 61,628 articles 2017–2026 (a later stage's measurement), no Wayback, no browser, no scheme
split. Wayback abandoned. The 2018-cutoff scope-cut still holds (Binance candles); a later entry covers the method.
