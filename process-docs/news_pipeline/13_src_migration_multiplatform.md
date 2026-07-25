# 13 — src/ Migration & Multi-Platform Architecture

**Date:** 2026-06-08
**State:** SHIPPED on `dev` (4 commits, merged), user-accepted end-to-end. Refines the flat promotion sketch from iter-8 into a multi-platform-extensible structure.

Implementation record (structure, corrections, flow) lives in the prior migration entry and in `src/news/`'s own documentation. This note captures the DESIGN RATIONALE argued in the migration session — the *why*, for future platform authors.

---

## Decision: `src/news/` is a separate, self-contained space

The validated CoinDesk pipeline moved `dev/news_pipeline/` → `src/news/`. `src/news/` sits BESIDE the existing CLI (`src/search/`, `src/scraper/`, `src/crawler/`), not inside it, and does **not import** from them.

**Why separate + self-contained:**
- News ingestion is a different concern from the SearXNG search/scrape/crawl CLI. Entangling them couples two independently-evolving surfaces.
- The news scrape engine is the B2 approach (fresh `AsyncWebCrawler` per URL) — structurally *different* from `src/crawler/pipe_scraper.py` (one shared crawler). The Scrapy gate (`_ensure_domain_state`, `_gate_domain`) is **ported verbatim**, not imported, so a future change to `pipe_scraper.py` cannot silently alter news pacing.
- `dev/news_pipeline/` stays as the prototyping playground: a new platform is validated loosely in `dev/` first, then ported into `src/news/platforms/<name>/`. dev architecture is intentionally free-form; prod is the clean home.

## Decision: Platform contract is the extensibility seam

`platform.py` defines `Platform` (Protocol) + `ScrapeConfig`. A platform supplies everything site-specific; the engine + orchestrator are generic and consume it. Adding a source = a new `platforms/<name>/` subpackage implementing the contract + `register()` — **engine and orchestrator are untouched**. This is the whole point of the structure: extensibility without core surgery.

Contract: `name`, `collection`, `precondition_url`, `regwall_signals`, `scrape_config`, `async discover()`, `cleanup(raw, entry)`. (`precondition_url` travels with the platform — the internet-check URL is site-specific, not orchestrator-generic.)

## Decision: shared vs per-platform split

| Stage | Home | Why |
|---|---|---|
| discover | per-platform | site-dependent (CoinDesk pydoll-UI; others sitemap / `__NEXT_DATA__` / BFS) |
| cleanup | per-platform | each site's chrome differs; macro sites need entirely different strip strategy |
| scrape config (regwall signals, pacing) | per-platform | regwall block strings + WAF tolerance are site-specific |
| scrape engine (B2 + gate + guard mechanism) | shared | the fetch mechanism is generic; only its inputs vary |
| dedup, publish, orchestrator | shared | filesystem-as-seen-state + copy/index + stage-chaining are platform-agnostic |

## Decision: collection per Layer, not per platform

Platform declares its `collection`. CoinDesk + future crypto-native sources (The Block, CoinTelegraph, …) → `searxng_crypto` (Layer 1). Parked Layer 2 (macro) / Layer 3 (sentiment) → separate collections later. Per-source dedup via the `{source}__` filename prefix; NO cross-site dedup (same story from N sources = N docs = stronger signal — see iter-7).

## Improvement: subprocess → in-process

`dev/run_pipeline.py` chained stages as subprocesses and parsed counts from stdout via regex. `src/news/pipeline.py` calls the stage functions directly and passes manifests in-memory — no fragile stdout-regex parsing, cleaner error propagation. The regwall-guard abort changed accordingly: `sys.exit(1)` (right for a subprocess) → `raise RegwallGuardError` caught by the orchestrator (right for in-process; logs ERROR + writes marker + returns, skipping cleanup/publish).

## Gotcha: publication_date flow (latent multi-platform bug, found in review)

The scrape manifest carries `{url, hash, file, char_count, status, error, wait_strategy}` — **no `publication_date`**. The first cut of `_run_cleanup` read `publication_date` from the scrape manifest → always empty. For CoinDesk this was masked: `publish.pub_date_str()` falls back to the URL path `/YYYY/MM/DD/`, so filenames were correct (and consistent with the existing index). But discover's `publication_date` was being **dropped at the scrape→clean seam** — a future platform whose URLs lack a date would silently fall to `__unknown__` despite having the date available.

Fix (commit `4e6e888`): `_run_cleanup` takes `discover_by_url = {url: discover_entry}` (built from `new_entries`) and sources `publication_date` from the discover entry. The URL-path fallback in `pub_date_str()` stays as the secondary net. **Lesson for platform authors:** any discover field needed downstream must be threaded explicitly through `_run_cleanup` via the discover entry — the scrape manifest is NOT a metadata carrier.

## Open: cron (deferred, no issue)

The cron trigger is NOT set up (user-deferred this session, no issue tracked). The entry point `python -m src.news --source coindesk` is the cron target when wired. Next-platform expansion (The Block etc., per iter-7 channel-independence) is the other forward direction.
