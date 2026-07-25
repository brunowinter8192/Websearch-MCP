# CoinDesk Probe — Iteration 2: Fresh Context (Option A)

## Approach

`async with AsyncWebCrawler(config=browser_config)` scoped inside the per-URL loop — every URL gets its own Chrome process launch, its own `BrowserManager`, its own empty `contexts_by_config` dict, and therefore a fresh Playwright `BrowserContext` with no prior cookies. All other config identical to iter 1: same Mozilla UA, same `CrawlerRunConfig` (`networkidle`, `CacheMode.BYPASS`, `DefaultMarkdownGenerator`), same `asyncio.sleep(1.0)` between URLs. Same 25-URL input (`discover_20260527T164927Z.json`).

## Root cause confirmation (source code)

`browser_manager.py:1662–1675` — `get_page()` non-managed-browser path:

```python
config_signature = self._make_config_signature(crawlerRunConfig)
if config_signature in self.contexts_by_config:
    context = self.contexts_by_config[config_signature]   # ← same BrowserContext reused
else:
    context = await self.create_browser_context(crawlerRunConfig)
    self.contexts_by_config[config_signature] = context   # ← cached for next arun()
```

In iter 1, a single `AsyncWebCrawler` instance was kept open for all 25 `arun()` calls. After the first `arun()`, the context was cached under the config signature; all 24 subsequent calls reused it, inheriting the accumulated cookies and CoinDesk's visit counter. Fresh `AsyncWebCrawler` per URL destroys and reinitialises the entire `BrowserManager` including `contexts_by_config`, guaranteeing a clean context every time.

## Before / after

| Metric | Iter 1 (shared session) | Iter 2 (fresh context) | Δ |
|---|---|---|---|
| URLs | 25 | 25 | — |
| HTTP-level ok | 25 | 23 ok + 2 empty | — |
| Regwall hits | 21 (84%) | **0 (0%)** | −21 |
| Real body retrieved | 4 (16%) | **23 (92%)** | +19 |
| Timeout / empty | 0 | 2 (networkidle 60s) | +2 |
| Failed | 0 | 0 | — |
| Total chars | 678,228 | 832,897 | +154k |
| Real article char range | 34k–49k | 32k–49k | similar |
| Regwall char range | 23k–26k | — | gone |
| Runtime | 107s | 284s | +177s (~2.7× Chrome-launch overhead) |

The 2 empties are networkidle timeouts (both logged at exactly 60.5s, crawl4ai's default networkidle deadline):
- `business/…/dtcc-plans-to-bring-tokenized-assets-to-stellar`
- `policy/…/singapore-charges-former-hodlnaut-ceo-zhu-juntao`
These are unrelated to regwall — likely pages with persistent background network activity that never fires `networkidle`. `domcontentloaded` wait_until would likely resolve them; deferred to next iteration.

## Verdict

**PASS** — 92% real bodies (23/25), 0 regwall hits. Fresh context per URL fully resolves the visit-counter trigger. The 2 timeout empties are a separate, minor issue (wait_until strategy, not auth).

Filter-design is now unblocked. Next step: design and test site-specific filters to strip nav chrome / price ticker / social share buttons from the raw markdown bodies.

## Artifacts

Run numbers: `dev/news_pipeline/01_reports/coindesk_scrape_2026-05-27_freshctx.md`

Per-URL evidence: `dev/news_pipeline/02b_output/manifest.json` (gitignored)
