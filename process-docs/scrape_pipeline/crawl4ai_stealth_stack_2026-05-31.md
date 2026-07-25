# crawl4ai Stealth Stack — Findings for the Scraping Phase

**Session:** 2026-05-31
**Versions:** crawl4ai 0.8.6, playwright-stealth 2.0.2, patchright 1.58.2
**Source:** github_issues collection (crawl4ai stealth issues), verified via `pip show` + import repro

---

## As-of-2026-05-31: Two Stealth Mechanisms, One Broken

### Mechanism A: playwright-stealth / `enable_stealth=True` — BROKEN

`BrowserConfig(enable_stealth=True)` injects playwright-stealth JS. Dependency:

```python
# src/crawl4ai/async_crawler_strategy.py → browser_adapter.py:161
from playwright_stealth import stealth_async   # ImportError on 0.8.6
```

`playwright_stealth` no longer exports `stealth_async` in 2.0.x — an API break between
playwright-stealth 1.x → 2.0. On crawl4ai 0.8.6 + playwright-stealth 2.0.2, every
`enable_stealth=True` call throws an **`ImportError`** on the first actual stealth inject.

**Fix:** crawl4ai PR #1960 (not yet released on 0.8.6). On this version,
`enable_stealth=True` is a **no-op** (or crashes, depending on code path).

### Mechanism B: `UndetectedAdapter` + patchright — WORKS

```python
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai import UndetectedAdapter

strategy = AsyncPlaywrightCrawlerStrategy(
    browser_config=cfg,
    browser_adapter=UndetectedAdapter(),
)
```

Different mechanism: patchright 1.58.2 patches Playwright at the C++ level (V8 fingerprint hiding,
`navigator.webdriver = false`, canvas/WebGL noise). Not touched by PR #1959 (playwright-stealth
import fix). This is the **only working stealth path** on 0.8.6.

Active at the time in `src/crawler/explore_site.py`'s `--stealth` flag and `src/scraper/scrape_url.py`'s
Phase-2 escalation — both used this path.

---

## Gotcha: UndetectedAdapter + High Concurrency = Unstable

**crawl4ai Issue #1500:** `UndetectedAdapter` at concurrency > 1 crashes frequently with:

```
Target page/context/browser has been closed
```

Cause: patchright patching is not thread-/task-safe under parallel `arun()` calls.
Symptom: non-deterministic (sometimes concurrency=2 works, sometimes it crashes immediately).

**Consequence for the scraping phase:**
- Stealth + concurrency > 1 = unstable / not reproducible — **do not use**
- Stealth scraping stays sequential (concurrency=1)
- Without stealth: concurrency up to 3 documented per `05_playwright_bfs.py` (WAF behavior
  at higher concurrency not yet measured at the time — treat as experimental)

---

## Decision Matrix for the Scraping Phase (as of 2026-05-31)

| Requirement | Mechanism | Stable? |
|------------|------------|---------|
| Stealth, sequential (WAF-protected sites) | `UndetectedAdapter` + patchright, concurrency=1 | Yes |
| Stealth, parallel | `UndetectedAdapter` + concurrency >1 | No (Issue #1500) |
| No stealth, parallel | Standard `BrowserConfig`, concurrency 2-3 | Experimental |
| `enable_stealth=True` (any) | playwright-stealth ImportError | No (0.8.6) |

---

## Sources

- crawl4ai Issue #1500: UndetectedAdapter crash at high concurrency
- crawl4ai PR #1959: playwright-stealth `stealth_async` import fix (not yet in 0.8.6 at the time)
- crawl4ai PR #1960: enable_stealth code-path fix (not yet in 0.8.6 at the time)
- `pip show crawl4ai playwright-stealth patchright` — version verification this session
- Import repro: `from playwright_stealth import stealth_async` → `ImportError` on 0.8.6 + playwright-stealth 2.0.2
