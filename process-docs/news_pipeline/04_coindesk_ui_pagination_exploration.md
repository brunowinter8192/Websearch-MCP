# CoinDesk Probe — Iteration 3: UI Pagination Exploration

## Findings

### Sitemap cap discovery
`news-sitemap-index` returns a fixed top-25 list, NOT a rolling 24h window. All 25 entries in the iter-1 run were from a single day (2026-05-27). The sitemap is ordered by recency and truncates at 25 entries regardless of time span — the oldest entry visible depends on publishing cadence, not a fixed lookback window.

### Cross-source coverage comparison (2026-05-27 run)

| Source | URLs | Today (05-27) | Yesterday (05-26) | Total |
|---|---|---|---|---|
| Sitemap (`news-sitemap-index`) | 25 | 25 | 0 | 25 |
| UI pagination (`/latest-crypto-news`, 1 click) | 32 | 29 | 3 | 32 |

Sitemap miss rate: 7/32 = **22%** — misses yesterday's articles entirely + 4 of today's that weren't in the top-25 at time of fetch. Miss rate varies with publishing cadence; on high-volume days (>25 articles) it is structurally worse.

### UI pagination mechanics

**Entry point:** `https://www.coindesk.com/latest-crypto-news`

**Button:** `BUTTON` element, text `"More stories"`, class `bg-surface-default hover:opacity-80 cursor-pointer border border-brand-fixed`. No `id`, no `data-*` attrs. Stable across 3 runs.

**Container:** `main a[href]` scoped extraction with `ASIDE / NAV / FOOTER / HEADER` exclusion. CoinDesk uses `<div>` cards, not `<article>` elements. Card wrapper: `DIV.bg-surface-default.flex`. One noise URL (`/2023/02/20/`) in `<footer>` — excluded by tag filter.

**Pagination behavior:** AJAX-loaded, no page navigation. 1 click appends ~16 articles (observed: 16 initial + 16 after click = 32 total). Load confirmed by polling feed-scoped URL count.

**Measured (iter 3, 2026-05-27, headed, fresh session):**
- Initial load: 16 feed articles (all 2026-05-27)
- After 1 click: +16 → 32 total (29 × 2026-05-27, 3 × 2026-05-26)
- Pre-today threshold (≥3 articles from before today): hit after **1 click**
- No regwall, no CAPTCHA, no consent wall on listing page

**Termination heuristic:** stop when ≥3 articles with URL date < today. Robust against day-boundary noise; does not depend on oldest-article age (which was fragile — a single pinned sidebar link fired it prematurely in iter A.1).

### Implication for production discovery

UI pagination is the better discovery source:
- Covers yesterday's articles (sitemap misses them structurally)
- 1 click sufficient for 24h window on normal publishing cadence
- Button selector is stable (class-based, no id or data-attr needed)
- No auth friction on the listing page

**Production-Discovery-Rewrite (iter 4):** replace `01_coindesk_discover.py` (sitemap-based) with UI-pagination approach. Reuse probe's JS selectors (`_JS_EXTRACT`, `_JS_CLICK_BTN`, termination logic). Output format stays identical (`{url, lastmod, publication_date, title, section}`) so Stage 2 scraper (`02b_coindesk_scrape_fresh_context.py`) requires no changes. `lastmod` / `publication_date` will be derived from URL date (no sitemap metadata available) — acceptable for 24h-window use case.

## Artifacts

Probe scripts: `dev/news_pipeline/exploration/01_coindesk_ui_probe.py`
Run reports: `dev/news_pipeline/exploration/01_output/probe_20260527T185853Z.json`
