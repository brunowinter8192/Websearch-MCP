# CoinDesk Probe — Iteration 1: Regwall Discovery

## Iteration scope

First probe iteration of the CoinDesk news-scraping pipeline. Raw crawl4ai scrape via Mozilla UA (`Chrome/120`), shared `AsyncWebCrawler` session across all 25 URLs sequentially with `asyncio.sleep(1.0)` between fetches, `networkidle` wait, `DefaultMarkdownGenerator`, no stealth adapter, no content filter. Goal was raw markdown for filter-design inspection — blocked by regwall before filter-design could begin.

## Findings

| Metric | Value |
|---|---|
| Sitemap URLs (24h window) | 25 |
| HTTP-level successes | 25 / 25 |
| Real article body retrieved | 4 / 25 |
| Regwall'd (monthly-limit page) | 21 / 25 |
| Regwall hit rate | 84% |
| Regwall char range | 23k – 26k |
| Real article char range | 34k – 49k |
| Regwall detection marker | `grep -l 'monthly limit'` sufficient |

Non-regwall'd articles in this run (4): #1 coindesk-indices/crypto-long-and-short (49k), #2 business/bis-project-tokenization (34k), #3 markets/crypto-ipos-jefferies (38k), #15 markets/bitcoin-etf-accumulation (35k). Distribution: 1× coindesk-indices, 1× business, 2× markets — scattered, NOT section-based. Confirms session-visit-count trigger, not a section-level policy.

File size split is clean: regwall pages are 23–26k chars (nav + consent banner + footer + "you've reached your monthly limit" block); real articles are 34k+ (full body + nav/footer). No overlap in the 25-URL set — threshold at ~30k chars would classify all 25 correctly.

Regwall trigger text: `You've reached your monthly limit` — appears reliably in the markdown body of all 21 blocked pages. Single `grep` is sufficient for detection; no heuristic needed.

## Root cause hypothesis

Shared `AsyncWebCrawler` session propagates cookies across all 25 `arun()` calls within one context. CoinDesk's visit counter increments per page load on the session cookie, fires the regwall after 3–4 reads. Mozilla UA + headless=True alone does not prevent this — the trigger is cookie-state, not fingerprinting. First 3–4 URLs succeed before the counter trips; all subsequent URLs in the same session hit the wall.

## Implications for next iteration

Regwall must be resolved before filter-design makes sense — 21/25 files are noise, not signal.

Options ranked by implementation cost:
- **(a) Fresh browser context per URL** — `AsyncWebCrawler` instantiated inside the per-URL loop (`async with AsyncWebCrawler(...) as crawler:` scoped per iteration), no cookie carryover between fetches. Cost: ~5s/URL × 25 = ~+2 min total runtime. Simple, no new deps.
- **(b) UndetectedAdapter + Stealth** — mirrors `src/scraper/scrape_url_raw.py` production fallback chain (`BrowserConfig(enable_stealth=True)` + `UndetectedAdapter()` + `AsyncPlaywrightCrawlerStrategy`). Stealth patches fingerprint, may also reset cookie jar per context depending on crawl4ai internals. Higher complexity.
- **(c) Combination** — fresh context (a) + stealth (b). Maximum isolation, highest cost.

Recommendation: try (a) first — it directly addresses the root cause (shared session state) without stealth complexity. If CoinDesk adds fingerprint checks later, layer (b) on top.

Filter-design deferred until re-scrape with ≥80% body-success-rate is verified.

## Artifacts

Run numbers: `dev/news_pipeline/01_reports/coindesk_scrape_2026-05-27.md`

Per-URL evidence: `dev/news_pipeline/02_output/manifest.json` (gitignored, persists locally for inspection until next scrape run overwrites)
