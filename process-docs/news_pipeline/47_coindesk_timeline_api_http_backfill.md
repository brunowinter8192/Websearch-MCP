# 47 — CoinDesk discovery: the timeline API is pure-HTTP backfillable (THE method)

Crystallizes the CoinDesk article-discovery method after a long investigation that ruled out two other
surfaces. Conclusion: **CoinDesk's own timeline API, walked by its cursor, is the complete and fast
discovery surface for BOTH backfill and delta — reachable by plain HTTP, no browser, no cookie.** A single
full run produced the entire 2017–2026 inventory: **61,628 articles in ~40 minutes**, each with a
day-precise date and URL.

## The journey (three surfaces, two dead ends)

1. **Browser UI-pagination** (earlier stage) — clicking "More stories" drives the timeline API internally; reading
   article URLs from the DOM. WORKS but the DOM grows unbounded → per-click time climbs O(n²)→O(n) (0.6s →
   3s+ over ~600 clicks); neither delta-extraction nor href-strip-pruning flattened it (the browser holding
   a 9k-node DOM is the wall, not our scan). Abandoned as the backfill surface — too slow at depth.
2. **Wayback CDX archive** (earlier stage) — enumerate old article URLs from the Internet Archive. Measured:
   ~15,500 clean date-path articles, **incomplete** (≈20% of CoinDesk's real output; 2017–2019 nearly empty
   at ~700/yr) and **dirty** (line-wrapped/truncated slugs like `busi-ness`). Dead end as a backbone.
3. **Timeline API direct HTTP** (this doc) — the winner. The same API the browser fires, called directly.

## The API

`GET https://www.coindesk.com/api/v1/articles/timeline?size=16&lastId=<UUID>&lastDisplayDate=<ISO>&lang=en`

- **Cursor-based, reverse-chronological.** Each response = 16 articles. The next cursor = the last article's
  `_id` (→ `lastId`) + `articleDates.displayDate` (→ `lastDisplayDate`). `&lang=en` required.
- A call WITHOUT a cursor → 403. The API only answers "give me the 16 after X", never "give me the newest".
  The starting cursor comes from a browser feed-load (the SSR-embedded newest articles).
- Each article JSON carries: `_id`, `pathname` (the URL path), `articleDates.displayDate` (day-precise
  date — no scrape needed for the date), `title`, `storyType`, `sectionDetails`, `tagDetails`.

## The 403 crack — only 5 headers, no cookie

Plain `curl`/`curl_cffi` got 403 EARLIER because the request lacked the right headers — NOT a TLS or token
gate. The minimal working header set (captured via pydoll HAR recorder from a real browser request):
- `Referer: https://www.coindesk.com/latest-crypto-news`
- `User-Agent: <Chrome UA>`
- `sec-ch-ua: "Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"` (exact GREASE string matters)
- `sec-ch-ua-mobile: ?0`
- `sec-ch-ua-platform: "macOS"`

No Cookie, no auth header. httpx-plain AND curl_cffi both return 200 with this set. (Opus's cold-repro
attempts failed on reconstructed headers — the exact `sec-ch-ua` GREASE value + omitting a spurious `Accept`
header mattered; capture beats reconstruction.)

## Two findings that corrected earlier hypotheses

- **The "bad cursor" 403 is TRANSIENT, not a storyType rule.** The deterministic call-8 break at article
  `cc8f264d` was a red herring — that article is a standard `News` piece, and the same cursor returned 200
  from a later session. storyType distribution over 128 articles: 91% News / 5% live_news / 3% Opinion — no
  special anchor types. Mitigation = **retry-on-403 with cursor fallback** (anchor on the N-1, N-2 article).
  In the full run this fired **0 times**.
- **IP warmth is real but generous — and in practice a non-issue.** A single browser feed-page load warms
  the IP for ≥5 min (IP-level, not process-level). But the 40-minute full run did **0 re-warms** — one
  initial warmup carried the entire 3,855-call run. Whether a plain httpx feed-GET re-warms (vs needing a
  browser) was never exercised (no re-warm triggered) — OPEN, see below.

## Evidence — the full backfill run

Script `dev/news_pipeline/exploration/06_*` (httpx cursor loop, retry-on-403 fallback, stop-at-floor-date):

```
DONE | calls=3855 articles=61628 oldest=2016-12-31 rewarms=0 fallbacks=0   wall≈2412s, ~0.3s/call (flat)
```

Per-year inventory (stop floor set at <2017-01-01):

| Year | Articles | Year | Articles |
|---|---|---|---|
| 2017 | 3,224 | 2022 | 9,488 |
| 2018 | 4,192 | 2023 | 8,181 |
| 2019 | 4,020 | 2024 | 5,696 |
| 2020 | 6,217 | 2025 | 8,864 |
| 2021 | 8,001 | 2026 | 3,743 (partial) |
| | | **TOTAL** | **61,628** |

Counts track CoinDesk's real publishing history (ramp-up, peak 2021–2023, slight decline) — plausible and
complete, unlike Wayback's sparse 2017–2019. This is the authoritative inventory: CoinDesk's own backend
walked exhaustively to the floor. Only theoretical gap = content the timeline index itself excludes.

**Inventory location (preserved, gitignored):** `data/news/coindesk/backfill_urls/coindesk_<year>.txt`,
one line per article `<YYYY-MM-DD>\t<url>`. 61,628 lines total. This is the Stage-2 (scrape) input.

## Backfill + delta = one mechanism, two stop conditions (decided)

The same cursor loop serves both, mirroring The Block's `full`/`delta` modes:
- **`full` (backfill):** walk from newest to a floor date (2017-01-01). Done once.
- **`delta` (recurring):** walk from newest, stop when reaching already-collected articles (hash/pubdate
  dedup against the existing collection) OR after a fixed safety window (e.g. ~2 months). Each run ≈ 50–100
  calls ≈ ~30s. Loss-tolerant: a skipped run just walks back further next time until it hits known articles.

This dissolves the earlier worry that the recurring CoinDesk run would be maintenance-heavy (the
browser-clicking delta). Pure HTTP for both. pubdate comes from `articleDates.displayDate`, so the existing
CoinDesk `pubdate`-based dedup convention is preserved.

## Artifacts

- `dev/news_pipeline/exploration/04_coindesk_timeline_replay_probe.py` — browser capture (pydoll HAR) + httpx/curl_cffi replay; proved the 403 crack.
- `dev/news_pipeline/exploration/05_*` / `05b_*` — cursor storyType walk + IP-warmth ladder.
- `dev/news_pipeline/exploration/06_*` — the full discovery run (cursor loop + retry-fallback + per-year output).

## Open / next (deferred to src-port session)

- **Port to `src/`** as a CoinDesk discovery lane (`full`/`delta` timeframe modes), replacing the current
  browser UI-pagination discover. The discovery is HTTP-only; the warmup needs the one browser feed-load
  (or — verify — a plain httpx feed-GET).
- **Verify httpx re-warm**: can a plain httpx GET of the feed page warm the IP (→ fully browserless), or is
  a browser load required? Untested (the full run never re-warmed).
- **Stage 2 — scrape** the 61,628 URLs (start with 2017 as a test, then the rest), then port the scrape lane.
