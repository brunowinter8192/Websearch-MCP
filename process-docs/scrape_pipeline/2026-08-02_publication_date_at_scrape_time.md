# Publication date extraction at scrape time (htmldate)

Date: 2026-08-02

## Problem

Search-engine-surfaced dates (prior milestones, `process-docs/search_pipeline/`) only cover 7 of 14 engines and only exist when a search result was involved at all. `scrape_url_workflow` had no date extraction of its own — a URL scraped directly (or via any of the 7 dateless engines) carried no date information whatsoever.

## External library: htmldate, not a hand-rolled cascade

`htmldate` (adbar/htmldate) — its cascade covers JSON-LD, OpenGraph, meta tags, `<time>` elements, URL patterns, and class/id heuristics, deliberately not reimplemented. Two required call-site facts:
- `original_date=True` — REQUIRED. Default behavior returns last-modified, not original publication date (documented 3-year gap between the two on the library's own example page).
- `outputformat` default (`%Y-%m-%d`) already matches this codebase's day-precision ISO convention (`process-docs/search_pipeline/` established the same day-precision cap for all engine-sourced dates), no override needed.

## Decision 1 — extensive mode

Extensive (`extensive_search=True`, htmldate's default — set explicitly at the call site for clarity). Benchmark given: extensive 0.993 recall / 0.903 accuracy at 1.8x parse time vs fast 0.927 recall / 0.924 accuracy at 1x. This scraper's cost center is a full headless-browser page load (`page_timeout=60000`) — the 1.8x parse-time multiplier is negligible against a fetch that can run to tens of seconds; the recall gap (0.993 vs 0.927) is real and matters for an optional field, the accuracy gap (0.903 vs 0.924) is rounding-level.

## Decision 2 — raw HTML channel: `try_scrape`'s local `result.html`, not threaded outward

Verified by reading crawl4ai's own source (`async_webcrawler.py`), not trusted from a docstring: `async_response.html` (the fetch's raw HTML, captured before crawl4ai's own cleaning/markdown pipeline touches it — JSON-LD/meta/`<time>` all intact) flows unmodified through `aprocess_html(html=html, ...)` into `CrawlResult(html=html, ...)`. So `result.html` inside `try_scrape` is genuinely the raw page HTML.

Kept the raw HTML local to `try_scrape` — extraction (`extract_date(html, url)`) happens right there, and only the resulting `str | None` crosses into `meta["date"]`. Threading the full HTML string out through `meta` to the orchestrator was considered and rejected: it would bloat `meta`'s contract with a large payload that has exactly one consumer (the date extraction itself), for zero benefit.

**Placement matters:** `extract_date` is called right after `raw_md` is computed, BEFORE the cookie-wall/garbage-detection branches — a consent-walled markdown extract can still sit on top of raw HTML carrying real date metadata (the wall is often just a client-rendered overlay banner, not a server-side content replacement), so computing the date once, upstream of that branching, covers all downstream outcomes uniformly.

## Decision 3 — where the date surfaces

**Output:** `Published: <date>` line between `# Content from: <url>` and the blank-line/body boundary; omitted entirely when absent (no placeholder). **JSONL log (`log_scrape`):** yes, `"published_date"` field added to the schema — same category of per-call metadata as `bytes_returned`/`truncated`/`garbage_type`. **Sidecar (`write_sidecar`):** deliberately NOT touched — the date is already visible in both the returned content and the JSONL log; a third copy in the sidecar's HTML-comment header was judged redundant, not worth widening that function's signature for zero new information.

**Collision-risk check (explicitly required, not assumed):** the header-to-body blank line is unconditional regardless of whether the `Published:` line is present (1-line vs 2-line header block, always followed by `\n\n`). Verified against a body that itself starts with a markdown heading, both with and without a date line present — the boundary held cleanly in both shapes, no corruption, no ambiguity for a line-based parser. Example (no-date case, real scrape of a plain static page whose body opens with its own `##` heading):
```
# Content from: https://motherfuckingwebsite.com/

## Seriously, what the fuck else do you want?
...
```
and (dated case, body opens with its own `###` heading):
```
# Content from: https://docs.python.org/3/library/asyncio.html
Published: 2026-08-02

### Navigation
...
```

## Safety

`extract_date` never lets htmldate touch the scrape's success/failure path: `asyncio.wait_for(asyncio.to_thread(find_date, html, extensive_search=True, original_date=True, url=url), timeout=5.0)` — runs off the event loop (so `dateparser`, flagged slow in htmldate's own source, can't stall concurrent work) and hard-bounded (any exception, any timeout, any absence → `None`). Verified live by forcing both failure modes directly against the real async wrapper (not a mock of the wrapper): a monkeypatched `find_date` that raises returned `None` in 0.00s; one that sleeps 30s returned `None` at ~1.0s against a lowered test timeout — confirming the bound actually holds, not just that the code compiles.

## Observed limitation — htmldate accuracy on date-less reference pages

`extensive_search=True` + `original_date=True` does not guarantee an absent date stays absent: on `docs.python.org`'s asyncio reference page (no JSON-LD/meta date tags at all), htmldate's only candidate was a Sphinx-generated `"Last updated on Aug 02, 2026 (18:25 UTC)"` build-timestamp footer, and it returned that as the date. This is not a bug in this wiring — the code adds no heuristics of its own and forwards htmldate's actual finding faithfully — but it's a real, observed characteristic of extensive-mode's cascade on pages with no true publication-date concept (reference docs, continuously-updated wikis). Consistent with the disclosed ~90% (not 100%) accuracy figure. A genuinely date-less page (`motherfuckingwebsite.com`, plain static HTML, no metadata at all) was used for the milestone's actual "no date" proof instead, specifically because the Sphinx-docs case would have proven nothing about the degradation path — it would have proven a wrong value doesn't happen to occur on THAT page, not that absence is handled correctly.
