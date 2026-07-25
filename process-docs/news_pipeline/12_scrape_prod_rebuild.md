# 12 — Scrape Prod Rebuild: Regwall Investigation + B2 Ship

## Context

Smoke A (prod run) used `pipe_scraper.py`'s shared-session approach on 32 CoinDesk URLs from
`discover_filtered_20260607T195044Z.json`. It confirmed the regwall hypothesis empirically.

## Smoke A Result

**Script:** `dev/news_pipeline/prod_scrape_smoke.py`
**Mechanism:** `scrape_urls_workflow` from `src/crawler/pipe_scraper.py` — shared `AsyncWebCrawler`,
`asyncio.gather`, per-domain `Semaphore`, `domcontentloaded`, `delay_before_return_html=0.5`.
**Result:** 32/32 ok (pipe_scraper classifies >100 bytes as ok); heuristic flagged 17/32 as `REGWALL?`
(bytes ~9k, 5 marker hits — matched the `subscribe/sign up/...` marker set); 15/32 article? (17k-35k bytes).
**Wallclock:** 31s.
**Conclusion:** CoinDesk's cookie-metered regwall triggers after the free-quota is exhausted within a
shared session. Shared BrowserContext = shared cookie jar = counter accumulates across URLs.

## Smoke B — Isolation Candidates

**Script:** `dev/news_pipeline/scrape_isolation_smoke.py`
Two candidates tested on the same 32 URLs.

### Candidate B1 (intended design)

Intended: ONE shared `AsyncWebCrawler` + `asyncio.gather` + `Semaphore(8)` + per-URL distinct
`timezone_id` from `sorted(zoneinfo.available_timezones())`. Rationale: crawl4ai 0.8.6's
`_make_config_signature` includes `timezone_id`; distinct value → distinct signature → fresh
`BrowserContext` → fresh cookie jar.

**Flaw in smoke:** The script was ALREADY RUNNING when B1's implementation was corrected from
"new crawler per URL" to "shared crawler." The reported B1 result came from the pre-edit code
(fresh crawler per URL inside the semaphore — functionally identical to B2). The timezone-bust
mechanism was NEVER empirically tested.

**Smoke B "B1" result (actually B2 behavior):** 0/32 regwall, 32/32 ok, 24s.
**Smoke B "B2" result (correct B2):** 0/32 regwall, 32/32 ok, 24s.
Both rows identical — both rows were B2.

### Candidate B2 (shipped)

Fresh `AsyncWebCrawler` per URL, run concurrently via `asyncio.gather` + `Semaphore(8)`,
`0.5–1.0s` jitter, `domcontentloaded` + `delay_before_return_html=0.5`, `page_timeout=15000`,
no networkidle, no custom UA, no timezone.

**Validated result:** 0/32 regwall, 32/32 ok, 24s.

## Real-B1 (shared crawler + timezone) — Dead End

During the 02b rebuild Phase B, real-B1 was implemented faithfully (shared crawler, `asyncio.gather`,
`Semaphore(8)`, per-URL `timezone_id`) and run on the 32-URL corpus.

**Result:** 7/32 ok, 25/32 empty (all timing out at exactly `PAGE_TIMEOUT_MS = 15000ms`), 0/32 regwall.
**Wallclock:** 64s.

**Root cause:** A single Chromium process cannot sustain 8 concurrent BrowserContext creations
simultaneously. When 8 tasks all enter the semaphore and each triggers a new context on the same
browser process, context creation stalls, `domcontentloaded` never fires within 15s, result is empty.
The fresh-crawler approach (B2) avoids this by spawning 8 independent Chromium processes (each
`AsyncWebCrawler.__aenter__` is its own browser), so there is no shared-process contention.

**Decision: DO NOT RETRY real-B1.** The timeout failure is structural (single-process context
contention), not a tuning parameter. Increasing `page_timeout` or reducing concurrency would help
but would destroy the speed advantage. B2 is the correct mechanism.

## 02b Rebuild — Shipped State

**File:** `dev/news_pipeline/02b_coindesk_scrape_fresh_context.py`
**Mechanism:** B2 — fresh `AsyncWebCrawler` per URL inside `Semaphore(CONCURRENCY=8)`,
`asyncio.gather`, `domcontentloaded` + `delay_before_return_html=0.5`, `page_timeout=15000`,
no networkidle, no custom UA. `_RUN_CFG` defined once at module level (no timezone).

**Regwall guard:**
- Signals (precise): `"from_regwall"`, `"Create a FREE account to continue reading"`,
  `"You've reached your monthly limit"`. Loose markers (subscribe/register) excluded — they fire
  on article footers.
- Per-page: on signal match → no `.md` written, manifest `status="regwall"`, stderr WARN.
- Per-run: any regwall → WARN listing URLs; if `regwall_count/total >= REGWALL_FAIL_THRESHOLD (0.20)`
  → stderr ERROR + `sys.exit(1)`. Orchestrator sees non-zero exit → skips cleanup/publish.

**Standalone verification (post-rebuild):** 32/32 ok, 0/32 regwall, 0 empty, 0 failed, 31s.
Spot-checked `meta-is-paying` (3c7a9e542b5b.md, 22KB) and `michael-saylor-s-rallying-cry`
(945aa8f8fc44.md, 18KB) — both previously regwalled in Smoke A, both full bodies in rebuild.

**I/O contracts preserved:**
- Output: `02b_output/<sha256(url)[:12]>.md` with YAML frontmatter (url, lastmod, publication_date,
  title, section, scraped_at) — unchanged.
- Manifest fields: url, hash, file, char_count, status, error, wait_strategy — unchanged;
  `"regwall"` added as new status value (03_cleanup globs *.md and ignores manifest, so regwall
  pages simply absent from cleanup input — no change needed in 03).
- Stdout: `ok : N`, `failed : N`, `empty : N`, `regwall : N`, `total chars`, `slowest` —
  orchestrator regexes `ok\s*:\s*(\d+)` and `failed\s*:\s*(\d+)` unaffected.
- Exit code: 0 normally; non-zero only when regwall fraction >= 0.20.

## Pacing Restored to Prod Gate

**Problem with initial B2 ship:** bare `asyncio.Semaphore(8)` + `random.uniform(0.5, 1.0)` jitter.
This dropped prod's deliberately-chosen DETERMINISTIC per-domain rate model. Prod's `_gate_domain`
enforces evenly-spaced ~1 req/s start times with no adaptive delay reduction — validated WAF-safe
(0×429 over 316 URLs). Bare semaphore + random jitter is non-deterministic and loses the rate floor.

**Fix:** ported `_ensure_domain_state` and `_gate_domain` verbatim from
`src/crawler/pipe_scraper.py` into `02b`. Constants match prod exactly:
`DOWNLOAD_DELAY = 1.0`, `CONCURRENCY_PER_DOMAIN = 8`. `_fetch_one` flow:
`domain = urlparse(url).netloc` → `state = _ensure_domain_state(domain_states, domain, CONCURRENCY_PER_DOMAIN)`
→ `async with state["sem"]` → `await _gate_domain(state, DOWNLOAD_DELAY)` → fresh crawler → `arun`.

**Result:** 32/32 ok, 0/32 regwall, 0 empty, **32s** wallclock.
Gate floors single-domain 32-URL run at ~32s (~1 req/s), matching the spec prediction.

**Current deviation from prod (`pipe_scraper.py`):** fresh `AsyncWebCrawler` per URL only.
Pacing, concurrency cap, jitter formula, and constants are now identical.

## Live-Blog Filter Broadened

**Root cause found in post-run noise check:** live-blogs lack the `More For You` end-anchor that
03_cleanup relies on, so the full chrome-heavy page leaks into the output. The old substring filter
`"/live-markets-" not in url` missed `/live-updates-` variants.

**Fix:** replaced with precise slug-prefix check — `_is_live_blog(url)` extracts the last path
segment via `urlparse(url).path` and checks `slug.startswith("live-")`. Catches `live-markets-`,
`live-updates-`, and any future `live-X-` without false-firing on mid-slug or suffix "live".

**Regression verify:** applied to `discover_filtered_20260607T195044Z.json` (32 entries) — exactly
1 dropped (`live-updates-bitcoin-below-usd62-000-...`), 31 kept, 0 live-blog leaks in kept.

## Migration to src/news/

**Branch:** `news-migrate`  
**Commits:** 3 chunked commits on branch `news-migrate`.

### Structure created

```
src/news/
  __init__.py              # empty
  __main__.py              # python -m src.news --source coindesk [--skip-index]
  pipeline.py              # async orchestrator (in-process, replaces run_pipeline.py subprocesses)
  registry.py              # name -> Platform; register() / get()
  platform.py              # ScrapeConfig dataclass + Platform Protocol
  engine/
    scrape.py              # B2 engine ported from 02b; RegwallGuardError not sys.exit
    dedup.py               # filter_new_entries(); source-prefixed filename key
    publish.py             # publish_articles(); manifest in-memory
  platforms/coindesk/
    config.py              # REGWALL_SIGNALS, SCRAPE_CONFIG, discovery constants
    discover.py            # pydoll UI pagination; returns entry list (no file I/O)
    cleanup.py             # cleanup(raw_markdown, entry) -> pure body str
    __init__.py            # CoinDeskPlatform; auto-registers on import
```

### Corrections applied

1. **RegwallGuardError** (not `sys.exit(1)`): `engine/scrape.py` defines `class RegwallGuardError(Exception)`;
   `_check_regwall_guard` raises it when `regwall_count/total >= 0.20`. `pipeline.py` catches it,
   logs ERROR, writes marker, returns.
2. **Pure content, no frontmatter**: `engine/scrape.py:_write_body` writes raw markdown only.
   `pipeline.py:_run_cleanup` writes `platform.cleanup(body, entry)` result only. Published files
   are pure content — metadata is in the filename (`{source}__{pubdate}__{hash}.md`).
3. **--skip-index threaded**: `__main__.py` → `run_pipeline(platform, skip_index=...)` →
   `publish_articles(..., skip_index=skip_index)`.

### Self-contained constraint

`src/news/` does NOT import from `src/crawler/` or `src/scraper/`. The Scrapy gate
(`_ensure_domain_state`, `_gate_domain`) is ported verbatim from `src/crawler/pipe_scraper.py`
into `engine/scrape.py`.
