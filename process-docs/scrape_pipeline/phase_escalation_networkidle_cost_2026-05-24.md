# Scrape Phase-Escalation: networkidle Timeout Cost

**Date:** 2026-05-24
**Topic:** Why tracker-heavy static sites incur 60s+ wall time; three candidate mitigations; hamster-wheel risk of per-domain tuning.

## Sources

- `src/scraper/scrape_url.py:71-138` — phase escalation code (fastpath → browser_1a → browser_1b → browser_2_stealth)
- `src/logs/scrape_log.jsonl` — per-scrape timing record schema (timings_ms.fastpath / browser_1a / browser_1b / browser_2_stealth / filter / total_wall)
- Live observation: 2026-05-24 session, BfN.de scrape, 90s wall time

## Observation

A live `searxng-cli scrape_url "https://www.bfn.de/artenportraits/castor-fiber"` (BfN beaver artenportrait page) took **90 seconds total wall time**. Log record from `src/logs/scrape_log.jsonl`:

| Phase | Duration | Outcome |
|---|---|---|
| fastpath | 5027ms | `network_error` miss |
| browser_1a (networkidle) | 60989ms | TIMEOUT — never reached |
| browser_1b (domcontentloaded) | 23935ms | SUCCESS |
| total_wall | 89966ms | |

Result quality was good: 92,779 bytes raw markdown → 13,329 bytes after PruningContentFilter (86% reduction). Full content captured correctly.

## Root Cause

`networkidle` is Crawl4AI's strictest wait strategy: waits for 500ms of zero network activity. BfN.de runs **etracker.com** analytics plus likely social-media pixels (Facebook/LinkedIn/Xing/Pinterest/WhatsApp share links present in page) — these fire continuously, asynchronously. The idle condition is never reached → 60s default timeout fires → fallback to browser_1b kicks in.

This is a structural property of the site class, not a transient failure: any government portal or institutional site with third-party analytics will exhibit the same pattern.

## Why the Current 3-Phase Order Exists

The pipeline `fastpath → browser_1a (networkidle) → browser_1b (domcontentloaded)` is **content-quality optimized, not speed optimized**:

- **fastpath first:** if a URL serves clean markdown directly (ReadTheDocs, GitHub Markdown rendering, JSON-API responses), skip all browser overhead. ~1s typical when it hits.
- **networkidle next:** for JS-heavy single-page-apps (React, Vue, Angular), meaningful content is often injected AFTER initial DOM parse. `domcontentloaded` only would scrape an empty shell. `networkidle` ensures full async render has completed.
- **domcontentloaded fallback:** for tracker-heavy or sluggish sites where `networkidle` never converges, `domcontentloaded` gets the static HTML at minimum.

This order maximizes content quality at the cost of higher wall time on tracker-heavy static-content sites. The BfN case is the canonical worst case: static content, heavy third-party analytics, no JS-injected meaningful content — `networkidle` times out 100% of the time.

## Three Candidate Optimizations

None implemented. All are future-work options pending measurement.

### 1. Domain allowlist for domcontentloaded-first

- **Hypothesis:** certain domain classes are reliably static-content (government portals, Wikipedia, RTD, blog platforms) and never need `networkidle`.
- **Mechanism:** per-domain mapping or pattern-based regex → for matched domains, skip browser_1a and start directly at browser_1b.
- **Cost:** per-domain maintenance burden; false-positives if a "static" domain later adds JS-injected content.
- **Win:** saves the full 60s `networkidle` timeout on every matched domain.

### 2. networkidle timeout reduction

- **Hypothesis:** 60s is too conservative. Most real JS-SPAs finish rendering in 5–15s; sites taking longer are either broken or tracker-heavy (where we'd fall back to browser_1b anyway).
- **Mechanism:** reduce the effective `networkidle` timeout from 60s to e.g. 15s via `CrawlerRunConfig` page timeout.
- **Cost:** legitimately slow SPAs that need 30–60s fall back to browser_1b unnecessarily → lower-quality output on that minority.
- **Win:** 45s saved on every tracker-heavy site; no per-domain knowledge required.

### 3. Concurrent fastpath + browser_1a

- **Hypothesis:** fastpath miss takes ~5s. browser_1a Chrome startup overlaps with that 5s anyway. Running both in parallel and taking the first successful result eliminates the sequential 5s cost.
- **Mechanism:** `asyncio.gather(fastpath_task, browser_1a_task)`; on first successful return, cancel the other.
- **Cost:** increased code complexity; browser_1a startup cost incurred even when fastpath succeeds.
- **Win:** saves ~5s on every URL that misses fastpath.

## Hamster-Wheel Risk

User observation (2026-05-24, translated from German):

> "This quickly turns into a website-specific hamster wheel where you have to fine-tune endlessly and end up no smarter than before."

Per-domain or per-pattern tuning of scrape behavior tends to be a hamster wheel — fine-tune for site A, site B regresses, fine-tune for site B, site C surfaces a new edge case. Without a domain-agnostic strategic win, time invested in fine-tuning doesn't accumulate.

This concern targets candidate **#1 (Domain allowlist)** specifically — it is explicitly per-domain by design. Candidates **#2 (timeout reduction)** and **#3 (concurrent fastpath+1a)** are domain-agnostic and do not fall into this trap. They are the only structurally sound options if optimization is pursued.

## Open Question

Is there a **domain-agnostic** optimization that meaningfully wins, or are we structurally stuck choosing between:

- **Universal-conservative** (current): slow on tracker-heavy static sites, high content quality on JS-SPAs.
- **Universal-aggressive**: faster, but risks empty-shell scrapes on real SPAs.

Candidates #2 and #3 are the only domain-agnostic options on the table. Neither has been measured. Before any implementation, both need profiling against a representative URL sample: known JS-SPAs (React/Angular apps where `domcontentloaded` alone would yield empty shells), tracker-heavy static sites, and fastpath-hit domains.

If profiling shows no clear win on that sample, the correct conclusion is: **accept current behavior.** Interactive scrape is slow on tracker-heavy sites (90s worst case), but tolerable for one-off use. Batch indexing runs offline and has no wall-time constraint. The 60s cost is structural, not a bug.
