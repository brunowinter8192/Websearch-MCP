# 44 — CoinDesk discovery: pagination via the timeline API beats the sitemap

Decides the discovery surface for CoinDesk's backfill + delta. Conclusion: **UI pagination, driven by a
cursor-based timeline API, is denser AND deeper than CoinDesk's article-sitemap.** The sitemap is dropped
as the backfill surface. Builds on the URL-set + hash-dedup convention established for The
Block — CoinDesk gets the same "fetch the URL set, dedup, scrape the difference" model, with the timeline
API as the URL source.

## Question

CoinDesk's current discovery (`src/news/platforms/coindesk/discover.py`) is browser UI-pagination of
`/latest-crypto-news` with a 48h termination — structurally a delta pipe, no backfill. Open: what is the
discovery surface for a CoinDesk backfill — the article-sitemap or (un-capped) UI pagination?

## Evidence — sitemap [VERIFIED live, this session]

`sitemap-index.xml` lists 19 `articles-1..19.xml` (+ 41 `crypto-N.xml` = `/price/` ticker pages, non-article,
dropped). All 19 article sitemaps fetched + aggregated:
- **9499 total `<loc>`, only 1198 UNIQUE** (87% duplication — articles-2..19 are overlapping rolling
  windows, ~90% pairwise overlap; articles-1 is the freshest ~500, mostly distinct).
- Unique URL-date range: **2025-06-16 … 2026-06-15 (~1 year floor)**. `articles-20.xml` = 404 (consistent with earlier findings).
- 1198 unique for a full year ≈ 3/day — implausibly sparse for CoinDesk → the sitemap is incomplete even
  within its 1-year window.

## Evidence — pagination [probe `dev/news_pipeline/exploration/02_coindesk_pagination_probe.py`]

Playwright probe (system Chrome via `channel="chrome"`, headless), depth mode (click until stop / 150-cap):
- **The first ~5 clicks** reveal articles pre-embedded in the initial SSR HTML (Next.js App Router RSC
  payload, `self.__next_f.push`) — NO network request fires (HAR confirms: only `/_next/image` to
  coindesk.com).
- **From ~click 6 (SSR buffer exhausted)** each click fires a cursor-based API:
  `GET https://www.coindesk.com/api/v1/articles/timeline?size=16&lastId=<UUID>&lastDisplayDate=<ISO>`
  — `size=16` fixed, cursor = last article's UUID + displayDate. Reverse-chronological.
- **150 clicks → 2414 unique URLs, oldest 2026-01-23 (~5 months), button still active (no ceiling hit).**
  2414 URLs in 5 months ≫ the sitemap's 1198/year → pagination is denser AND deeper.

**Conclusion:** pagination via the timeline API is the CoinDesk discovery surface; the sitemap is dropped.

## The 403 gate [VERIFIED, this session]

The timeline API is plain `GET → 200` in-browser, but headless replay is gated: plain `curl` AND
`curl_cffi` (impersonate=chrome), with/without Referer + X-Requested-With, all return `{"error":"Forbidden"}`
(403). So it is NOT only a TLS-fingerprint block — the Next.js client sends something extra (a header / token
/ cookie set on page load) that a naked HTTP call lacks. Cracking this is deferred to the production build:
the build worker drives the real browser, captures the COMPLETE timeline request (URL + all headers), and
either replicates it via `httpx`/`curl_cffi` (fast, no browser) OR — if the gate is browser-bound — drives
pagination through the browser.

## Process notes (mis-steps, for the record)

- Opus first recommended "switch CoinDesk to sitemap discovery like The Block" without checking the dev/
  record — wrong; corrected by the user (pagination was already found more comprehensive vs the 25-cap
  Google-News sitemap, per earlier findings). The deep sitemap-vs-pagination question, however, was genuinely unsettled
  until this probe.
- The probe's Stage-1 (5 clicks) concluded "no API, all pre-embedded" — premature, an artifact of staying
  inside the SSR buffer. The depth run (150 clicks) revealed the timeline API. Lesson: the API only appears
  past the SSR buffer; a short click-probe misses it.

## Open / next

- **Build CoinDesk discovery on the timeline API** (separate task / issue): capture the real browser request,
  decide HTTP-replay vs browser-driven, loop the cursor to the floor, feed the URL set into the existing
  dedup → scrape → clean → publish pipeline (pubdate is already in the URL `/YYYY/MM/DD/`, so `pubdate`
  dedup stays; `browser` scrape engine stays for the regwall).
- How deep does the timeline API actually go (floor)? Not measured — button still active at 150 clicks /
  5 months. The HTTP-loop (once the 403 is cracked) measures it fast.
