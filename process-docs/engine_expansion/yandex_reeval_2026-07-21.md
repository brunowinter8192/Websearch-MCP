# Yandex Search Re-Evaluation — Dev Probe (2026-07-21)

**Probe:** `dev/search_pipeline/29_yandex_probe.py` (self-contained, no `src/` import)
**Report:** `dev/search_pipeline/md/yandex_probe_20260721_235722.md`
**Decision criterion (relaxed):** DROP only if there is truly no way through — blocked from the very first query, never a single usable result. A handful of clean hits before any eventual block is a CANDIDATE, since real usage is low-volume (3-4 queries every few days) — the same reasoning that landed Brave as a production candidate.

## Verdict: CANDIDATE

8/10 queries returned real, usable results; **longest consecutive clean run was 7** (queries 1-7 back-to-back), well past even a strict 3-4-in-a-row bar. Only 2 of 10 blocked, and both with hard evidence — a genuine redirect to `https://yandex.com/showcaptcha?cc=1&...` captured in the diagnosis, not an inferred text marker. This is explicitly the "blocks after clean hits" outcome the relaxed criterion treats as a pass, not the DROP condition (blocked-from-query-1, zero usable results ever).

## Framing: new coverage, not redundancy

Unlike Bing (direct-major alongside DuckDuckGo's surrogate) and Startpage (a Google-index frontend, redundant to direct Google), **Yandex runs its own independent crawler and index** — a genuinely new-coverage candidate for the general web axis, not a second path to an index already represented in the pool. This distinguishes it from the other engines evaluated this week.

## Selectors (current, live-verified)

- Search URL: `https://yandex.com/search/?text=<q>` — the international domain (`yandex.com`, deliberately NOT `yandex.ru`). Yandex auto-redirects to append `&lr=<region_id>` (an IP-geolocation-based region parameter) with no consent step and no block.
- Result container: `li.serp-item` — the old selector reference had NOT drifted, still the live container shape.
- Title + href: `a.OrganicTitle-Link` inside the container — **href is the direct destination URL, no tracking-redirect wrapper** (unlike Bing's `ck/a`, no `_clean_url`-equivalent unwrap needed).
- Snippet: `.OrganicText .OrganicTextContentSpan` (falls back to `.OrganicText`).
- Block detection: the URL-path check (`showcaptcha`/`checkcaptcha`/`/captcha` substrings in `window.location.href`) is what actually fired on both blocked queries — the title/body EN+RU text-marker scan was present as a fallback layer but the URL redirect was the decisive, reliable signal in practice.

## Quality axis, called honestly

German-axis queries (`beste kaffeemaschine test`, `gebrauchte waschmaschine frankfurt`, `hausgeräte händler frankfurt`, `gebrauchtwagen ankauf frankfurt`) all returned genuinely relevant, real German business/comparison-site results — `testbericht.de`, `faz.net`, `kleinanzeigen.de`, `quoka.de`, `markt.de`, `wmz-horn.de` — comparable in quality to the Google/Bing/Startpage results seen this same week, not junk or region-skewed. A plausible (worker's read, not independently confirmed) contributing factor is the IP-geolocation-driven `lr` region parameter, which resolved to Germany (region name "Weimar" observed in the raw page data) — giving Yandex a real local signal to work from rather than defaulting to a Russia-centric result set. That explanation is offered as a reasonable hypothesis for WHY the quality holds up; the quality DATA itself (the actual returned titles/URLs, eyeballed directly) is solid regardless of whether that specific mechanism is the correct explanation.

One minor artifact, not a quality failure: the `how does DNS work` result set included one `yandex.com/video/preview/...` self-referential link mixed among the real external results — the generic `li.serp-item` selector also matches a video-carousel SERP feature, not only organic web results.

## Two integration notes for a future wiring milestone

1. **Detect the `showcaptcha` redirect early.** In this probe, a blocked query burned the full `_wait_for_results` poll budget (~6-8s, MAX_WAIT_CYCLES × WAIT_INTERVAL) before the diagnosis step ran and found the redirect — the two blocked queries were the only ones to exceed the 5s latency gate (8335ms, 6639ms) specifically because of this ordering. A production engine should check `window.location.href` for the `showcaptcha`/`checkcaptcha` substrings immediately after `go_to()` returns, before entering the result-wait poll loop, to return `S.EMPTY_BLOCK` fast rather than waiting out the full poll budget on a page that will never produce results.
2. **Filter out `yandex.com`-domain self-referential URLs.** The video-carousel artifact above means a production parser should treat any `li.serp-item` whose `a.OrganicTitle-Link.href` resolves to the `yandex.com` domain itself as non-organic and skip it, rather than surfacing an internal Yandex page as if it were an external search result.
