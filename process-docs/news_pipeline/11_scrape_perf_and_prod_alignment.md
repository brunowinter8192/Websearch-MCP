# Iter 11 — Scrape Performance & Prod Alignment

**Date:** 2026-06-07
**State:** Problem analyzed, directive clear. Rebuild of 02b is the next step, pending.

---

## Scrape Performance Problem (run 2026-06-07)

**Symptom:** Stage 02b ran into the orchestrator timeout (600s, ERROR in log). Result: 0 ok / 0 failed → cleanup + publish skipped → run 1 indexed **nothing**.

**Measured rate:** 19 MDs produced in 600s = ~31s/URL.

**Root cause (code-backed, rate-supported):**

`02b` uses `fetch_with_fallback` — networkidle first, domcontentloaded as fallback:

```python
async def fetch_with_fallback(crawler, url, run_config, run_config_fallback):
    result = await crawler.arun(url=url, config=run_config)   # wait_until="networkidle"
    content = result.markdown.raw_markdown if result.markdown else ""
    if content:
        return content, "networkidle"
    # Empty or timeout: retry with domcontentloaded
    result = await crawler.arun(url=url, config=run_config_fallback)
    ...
```

On ad- and tracker-heavy news sites like CoinDesk, networkidle never settles fully → runs into the ~30s page timeout per URL → only then does the fast domcontentloaded fallback kick in. On top of that: a fresh `AsyncWebCrawler` (= new Playwright browser process) per URL, ~2–5s startup, plus fully sequential processing. Sum: ~31s/URL is explainable and expected.

---

## Prod Comparison (src/crawler/pipe_scraper.py)

The prod scraper does the same task ~30x faster:

| Dimension | 02b (dev) | Prod (pipe_scraper.py) |
|---|---|---|
| Browser session | Fresh `AsyncWebCrawler` instance per URL | One shared session |
| Concurrency | Fully sequential | `asyncio.gather` + `Semaphore(8)` per-domain |
| Page-wait | networkidle (primary) + domcontentloaded fallback | `delay_before_return_html` (fixed delay, no networkidle) |
| Rate-limit | `asyncio.sleep(1.0)` fixed | Scrapy `DOWNLOAD_DELAY=1.0` + jitter |
| Measurement | ~31s/URL (19 URLs in 600s) | ~1s/URL (316 URLs in 319s) |

The shared-session approach was the regwall trigger in iter 1 (`02_coindesk_scrape.py`, 21/25 regwall'd). The switch to fresh-per-URL in iter 2 (`02b`) fixed that — but at the cost of per-URL startup. Prod solves it differently: shared browser instance + fresh **context** per request (within the same instance), which can give both speed and cookie isolation.

---

## Sitemap-vs-Discover Comparison (verified 2026-06-07)

Sample: 32 discover URLs vs. CoinDesk sitemap (`news-sitemap-index` + `articles-1.xml` / `articles-2.xml`), window 2026-06-04 … 2026-06-07.

**A\B = 0: all 32 discover URLs are in the sitemap** (sitemap is a superset).

Per date:

| Date | Discover | Sitemap | Sitemap-only |
|---|---|---|---|
| 2026-06-07 | 4 | 4 | 0 |
| 2026-06-06 | 13 | 13 | 0 |
| 2026-06-05 | 14 | 20 | 6 |
| 2026-06-04 | 1 | 25 | 24 |

**Conclusion:** for the target window (today + yesterday), discover and sitemap are **identical** — the browser discover is complete for the pipeline-relevant zone. The 30 extras sit entirely in the overshoot zone (06-04 / 06-05), which the discover only partially paginates due to early termination (`PRE_48H_THRESHOLD`).

Practical implication: the sitemap would be equivalent, simpler, and more complete for deeper windows, should a wider backfill window ever be needed. For the daily 48h run, the browser discover is validated.

---

## Minor: Live-Blog Filter Too Narrow

The current filter in `filter_live_blogs()` only catches `/live-markets-` in the URL:

```python
kept = [e for e in entries if "/live-markets-" not in e["url"]]
```

A `/live-updates-` article slipped through in the 2026-06-07 run. For one-day windows this is usually not a problem; for larger windows (more pagination), such URLs accumulate. The filter should be widened to a broader pattern (e.g. `/live-`).

---

## Directive — Next Step: Rebuild 02b to the Prod Approach

**One option, no selection needed:** rebuild 02b to the prod approach — shared session + `asyncio.gather` + `Semaphore` + fixed delay instead of networkidle. Goal: ~30x speed-up, so 32 URLs run in <60s instead of >600s.

**Known risk (to verify empirically, not a blocker):** a shared session may re-trigger the CoinDesk regwall (the iter-1 problem). This is a test, not a choice — if the regwall returns, resolve during the rebuild, e.g.:
- Fresh Playwright browser context per URL within the shared browser instance (cookie isolation without browser-process startup).
- Prod already does this for other sites — check whether pipe_scraper.py provides this as a pattern.

**Fix the orchestrator timeout alongside it:** the fixed 600s timeout per stage (`run_pipeline.py:_run()`) is too rigid for the scrape. Scale with URL count (e.g. `60 + n_urls * 30`) or set a more generous fixed value (e.g. 1800s). Handle during the 02b rebuild.

**Widen the live-blog filter:** add `/live-` instead of `/live-markets-` during the rebuild (minor, not a separate task).
