# Scrape Phase-Escalation: Native Crawl4AI Strategy

**Date:** 2026-06-01
**Topic:** Replacing the hand-built 4-phase chain with a single crawl4ai browser call with a documented anti-bot baseline.

## Sources

- `src/scraper/scrape_url.py` — code before and after the migration
- `venv/lib/python3.14/site-packages/crawl4ai/async_configs.py:1399–1519` — CrawlerRunConfig 0.8.6 constructor
- `venv/lib/python3.14/site-packages/crawl4ai/async_crawler_strategy.py:76,117,762–763` — UndetectedAdapter wiring, page_timeout
- `venv/lib/python3.14/site-packages/crawl4ai/browser_manager.py:95,763` — enable_stealth GPU flags + StealthAdapter condition

## Starting Point

The old chain (`fastpath → browser_1a/networkidle → browser_1b/domcontentloaded → browser_2_stealth`) had three structural weaknesses:

1. **Non-deterministic runtime.** networkidle timeout of 60s was the worst case on tracker-heavy sites (BfN.de: 90s total wall, per an earlier analysis of networkidle timeout cost, 2026-05-24). No hard navigation limit — only an implied Crawl4AI default.
2. **Cascading overhead.** Every phase starts a new `AsyncWebCrawler` instance. On fastpath-miss + networkidle-timeout + domcontentloaded-fallback, three browser processes were started before the stealth phase was even reached.
3. **Complexity without strategic gain.** Per-phase tuning (which wait strategy for which site type?) is the hamster-wheel component: fine-tune for site A, site B regresses. The earlier finding was that only domain-agnostic optimizations are structurally sound.

## Target Config and Derivation

**Single call, four parameter decisions:**

### `wait_until="load"` instead of the networkidle/domcontentloaded cascade

`networkidle` waits for 500ms of zero network activity — on tracker-heavy sites (analytics, social pixels) never reached → 60s timeout inevitable. `domcontentloaded` fires too early, misses JS-injected content on real SPAs. `load` is the middle ground: fired when the page and all subresources (images, scripts) have loaded — complete enough for most sites, but without the idle wait of networkidle. Less prone to hanging on polling-heavy sites.

### `page_timeout=60000` (explicit)

Hard navigation limit. Confirmed as the navigation timeout in `async_crawler_strategy.py:762–763`:
```python
response = await page.goto(url, wait_until=config.wait_until, timeout=config.page_timeout)
```
Worst case: 60s navigation + short Crawl4AI overhead = ~64s/URL. Determinism: the call fails cleanly with a known timeout instead of hanging indefinitely.

### `magic=True`

crawl4ai documentation: "attempts automatic handling of overlays/popups". Complements `excluded_selector=COOKIE_CONSENT_SELECTOR` at the JS level: the selector removes DOM nodes before the crawl, `magic` dismisses dynamically generated overlays that have no static DOM markup. Together: a no-blocking baseline without per-site JS code.

### `enable_stealth=True` + `UndetectedAdapter` — coherence and #1959

The original question was: is `enable_stealth=True` in 0.8.6 a no-op when `UndetectedAdapter` is already used?

**Code analysis 0.8.6:**

`browser_manager.py:763`:
```python
if self.config.enable_stealth and not self.use_undetected:
    from .browser_adapter import StealthAdapter
    self._stealth_adapter = StealthAdapter()
```

`async_crawler_strategy.py:117`:
```python
use_undetected=isinstance(self.adapter, UndetectedAdapter)
```

When `UndetectedAdapter` is wired, `use_undetected=True` → the condition in `browser_manager.py:763` is `True and not True = False` → `StealthAdapter` (playwright-stealth) is NOT loaded. This is not a bug — it is intentional: `UndetectedAdapter` (Patchright) is the stronger mechanism, playwright-stealth would be redundant.

**`enable_stealth=True` still contributes** via `browser_manager.py:95`:
```python
if not config.enable_stealth:
    flags.extend([
        "--disable-gpu",
        "--disable-gpu-compositing",
        "--disable-software-rasterizer",
    ])
```
With `enable_stealth=True`, these flags are omitted → WebGL stays active → anti-bot sensors that use GPU absence as a headless signal find no signal. Complementary to Patchright, not redundant.

**Relation to GitHub Issue #1959:** #1959 concerns the case where `enable_stealth` in certain 0.8.x versions was a complete no-op (playwright-stealth was not loaded correctly). On 0.8.6 this does NOT apply to us: the playwright-stealth path via `StealthAdapter` is deliberately skipped (because `use_undetected=True`), but the WebGL/GPU-flags effect of `enable_stealth` is active. UndetectedAdapter provides the primary evasion via Patchright; `enable_stealth=True` is a coherent addition, not an empty annotation.

## Fastpath Removal

The httpx fastpath (`fetch_markdown_fastpath`) was removed. User's rationale: the adoption probe (May 2026) showed adoption was low (~0% on non-Cloudflare-CDN customers). The scraper's use case is ad-hoc agent research with 2-3 URLs — time is NOT the criterion. The added `httpx` import and HTTP round-trip complexity were disproportionate to the rarely-triggering benefit. Ship-and-observe as the verification method: scraping quality is observed in day-to-day use via `scrape_log.jsonl` (outcome field, garbage_type), no formal pre-merge eval.

## Log Schema Simplification

Alongside the code simplification: phase fields removed from the JSONL record (`phases_attempted`, `fastpath_hit`, `fastpath_miss_reason`, `timings_ms.*` phase keys, `phase_used`). `phase_used` dropped entirely — fully derivable from `outcome` (`outcome="ok"` ↔ success). Cleaner schema without redundancy. `timings_ms` now contains only `total_wall`.

## Verification Strategy

Ship-and-observe. No formal eval before merge — the user explicitly decided to adopt 1:1 in production. Observation via:
- `src/logs/scrape_log.jsonl`: `outcome` field (garbage_type, empty vs ok rate)
- Anecdotal quality checks in day-to-day use (agent research, 2-3 URLs per session)
- No rollback plan documented — on systematic regressions: a new process-docs entry.

## First Live Verification (2026-06-01)

Post-merge, live-tested via the production CLI (`searxng-cli scrape_url`) on two targeted cases from a DDG search ("rag chunking strategies"):

- **Medium** (`medium.com/@.../15-advanced-chunking-techniques-...`) — the hard bot/cookie/login-wall case. Result: `outcome=ok`, full article (all 15 techniques in the sidecar), `total_wall` 4510ms, `garbage_type=null`, pruning 13307→7037 bytes (~47% boilerplate). **Empirical confirmation of the #1959 conclusion:** the stealth combo (UndetectedAdapter/Patchright + `enable_stealth` GPU flags) passed Medium's bot detection — no login wall, real content. Residual chrome at the top (`Sign up`/`Get app`) + one cookie line at the bottom = a known prune_048 tradeoff, not content loss.
- **Microsoft Learn** (`learn.microsoft.com/.../rag-chunking-phase`) — JS-heavy docs SPA, `wait_until="load"` test. Result: full rendered article, ending with `[Content truncated...]` due to the existing 15K `DEFAULT_MAX_CONTENT_LENGTH` cap (intended, not an error). A generic "requires authorization" banner appeared but did NOT block the content.

Both confirm determinism (well under the 60s page_timeout), completeness (`wait_until=load`), and no-blocking (stealth) on real traffic. Further E2E test run to follow, user-side.
