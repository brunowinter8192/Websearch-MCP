# Iter 09 — Deep News Backfill Feasibility & Sourcing (parked)

**Date:** 2026-06-07
**State:** CLOSED/FOLDED (2026-06-12) — the dedicated deep-history-to-2017 track is dropped. Backfill depth is now bounded by each source's own discovery surface, folded into the general playbook. Findings below kept as record. See Resolution at end.

## Motivation

1s Binance candles are available from Aug 2017. The news component for the LLM-sentiment trading layer is missing. Goal: establish news-to-candle mapping for backtesting. Core question investigated: how deep can we backfill crypto news, with a target of ~2017?

---

## CoinDesk Sitemap Depth — [VERIFIED 2026-06-07, live fetch]

- `robots.txt` lists two sitemap roots: `sitemap-index.xml` (main) and `arc/outboundfeeds/news-sitemap-index` (Google-News, ~48h window only — not useful for backfill).
- `sitemap-index.xml` → 78 sub-sitemaps.

**Article sitemaps:**
- `articles-1.xml` … `articles-19.xml` — ~500 URLs each, ~9,500 articles total.
- URL format: `/<section>/YYYY/MM/DD/<slug>` — 100% carry a date in the path.
- Verified depth floor: oldest article URL-path date in the sitemaps = **2025-06-07** (approx. 1 year ago).
- `articles-20.xml` returns **HTTP 404** → sitemap sequence ends at 19.
- **Hard conclusion: CoinDesk sitemap = ~1 year floor. Nothing deeper available via sitemap.**

**Ticker pages (noise):**
- `crypto-1.xml` … `crypto-41.xml` — ~20k URLs, all `/price/<coin>` ticker pages, NOT articles. Dropped from any news pipeline.

**Date reliability:**
- `<lastmod>` in sitemaps is unreliable on older articles (re-touched on edits).
- The URL path `/YYYY/MM/DD/` is the reliable publication date anchor — this is what `dev/news_pipeline/01_coindesk_discover.py` already uses.

**Below the sitemap floor:**
- CoinDesk articles exist at their URLs back to ~2013 but are NOT listed in the current sitemap.
- Reaching them would require an external index (Wayback Machine / archive.org CDX).
- **[TO VERIFY]** CDX queries this session returned empty results, most likely because pre-~2020 CoinDesk URL structure differs from `/YYYY/MM/DD/` (the CDX filter matched nothing). Wayback feasibility for deep CoinDesk history is therefore **unverified**. Assessment: high effort, messy (old URL structures, scraping from snapshots), likely diminishing returns.

---

## How Practitioners Source Historical Crypto News — [VERIFIED 2026-06-07, reddit-cli-posts collection]

**Method note:** first attempt skipped subreddit discovery and hand-picked subs from memory — a process error corrected by making `search_subreddits` mandatory in the reddit-cli skill. Final discovery queries used: `cryptocurrency trading`, `algorithmic trading`, `quantitative finance`, `datasets`, `crypto news sentiment`. Subs searched: r/datasets, r/algotrading, r/quant, r/kaggle, r/CryptoMarkets. Index query: `crypto news dataset`. Collection `reddit-cli-posts` ended at 78 MDs / 391 chunks.

**Core finding: no clean off-the-shelf historical crypto-news archive exists.**

- The r/algotrading "Historical Crypto News Dataset" request is effectively unanswered — only "Coinness" was suggested; CryptoPanic described as "limited in time."
- Serious practitioners BUILD their own scraper pipeline. Two concrete examples found:
  - One researcher scraped ~5,000 CoinDesk headlines and mapped them to 1m Binance BTC/USDT candles (only 6 months of data; the full set sold on Gumroad).
  - Another runs a daily RSS/API + light-scrape pipeline for going-forward data.
- Named primary source outlets: CoinDesk, CoinTelegraph, The Block + aggregators + X/Telegram.
- Closest "deep" datasets found in the search: academic *Newswire* (a century of US wire news — not crypto-specific); CoinGecko API (price/volume back to 2013 — price, not news).

**Cross-outlet dedup sub-problem** (relevant when we add a second source site):
- The same event written differently by Reuters and CoinDesk passes text-similarity checks but is one event.
- Technique reported by a practitioner: embed headline + first paragraph, cluster with HDBSCAN, take the earliest timestamp per cluster as ground-truth event T0.
- Our current dedup is URL-hash based — correct for single-site CoinDesk, insufficient for cross-outlet.

**Empirical signal data point** (from the 5,000-headline study):
- Volatility concentrates in the first ~5-minute window after a headline.
- The majority of news is noise — only a small fraction triggers a >1% move within the first hour.

---

## Deep-History Sourcing: The Two Realistic Paths

### Path 1 — Free: GDELT

**[VERIFIED — appeared in the quant alt-data list: "GDELT — Global news events & entities; updated as often as 15 minutes. Free", gdeltproject.org]**

- Timestamped → in principle mappable to candles.
- Sentiment is document-level "tone" — coarse, not crypto-specific.
- **[TO VERIFY]** depth back to ~2015, crypto coverage volume from 2017, and whether its tone signal is usable for a crypto backtest. This is exactly what a future GDELT probe must measure.

### Path 2 — Paid: crypto-sentiment vendors

**[TO VERIFY — Opus general knowledge, NOT researched this session]**

- Santiment, LunarCrush, TheTie — pre-computed crypto social/news sentiment time-series reportedly back to ~2017/18.
- For a backtest, a ready sentiment time-series may be more directly usable than raw articles (no LLM re-inference over old text needed).
- Pricing and coverage depth are unverified.

---

## Architectural Conclusion — Going-Forward vs Backfill Are Different Data Problems

| Dimension | Going-forward (now → ∞) | Backfill (2017 → now) |
|---|---|---|
| Source | Own scraper (CoinDesk daily pipe + cron) | External aggregator (GDELT or paid vendor) |
| Control | Full — raw articles + LLM layer | Dependent on aggregator's coverage + format |
| Effort | Already in progress | DEFERRED |
| Data form | Raw MD → LLM sentiment | May be pre-computed sentiment time-series |
| Next action | Implement Stages 4 + 5 (dedup + publish) | GDELT probe on resume |

**Decision sequence when resumed:**
1. Run GDELT probe — measure crypto tone coverage depth and signal quality from 2017.
2. If GDELT crypto tone is usable → free deep backfill is solved.
3. If too coarse → becomes a paid-vendor cost decision (Santiment / LunarCrush / TheTie).

---

## Status

CLOSED/FOLDED (2026-06-12). The dedicated deep-2017 track is dropped; backfill depth is bounded by each source's own surface, folded into the general playbook. Findings above kept as record.

---

## Resolution (2026-06-12) — Dedicated deep-2017 track dropped

Pre-sitemap-floor history via external aggregators (GDELT / paid vendors) is NOT pursued as a separate track. Decision: backfill goes **as deep as each source's own discovery surface allows** — the floor is whatever the source gives (CoinDesk ~1yr, The Block ~2018); the exact depth (2017/2023/whatever) is secondary to maximizing available coverage. This principle is baked into the general playbook.

The findings above (CoinDesk sitemap ~1yr floor, GDELT free-tier option, paid-vendor options, cross-outlet dedup via HDBSCAN clustering, the 5-min-volatility signal data point) are preserved as record. If deeper-than-source history is ever wanted again, this iteration is the starting point — but it is no longer a tracked roadmap item.
