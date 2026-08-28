# Fetch-success pacing and frontier visibility (2026-08-28)

Review round on `src/crawler/discovery.py` (`process-docs/url_discovery/2026-08-28_frontier_wiring.md`).
Three items: diagnosing and fixing why the `docs.github.com` benchmark's traversal contribution
measured 0, making fetch failures visible on the result (the same silent-conflation pattern
already flagged on the seed fetch and the feeders), and including frontier URLs the page budget
never got to fetch. A fourth item — traversal-discovered links never being run through the
navtree feeder's own version-canonicalization — was found during this investigation and is
recorded here as a deliberately deferred open item, not folded into this milestone.

## Diagnosis: why traversal contributed 0 on docs.github.com

The milestone's own report explained a 0-traversal-contribution result as the navigation tree
already being near-exhaustive. That explanation was written without checking success/failure
counts, and was wrong. Three real, instrumented checks (not a guess) separated the candidate
mechanisms:

1. **`filter_chain.stats` on the real seed page's real extracted links**: `total≈214, passed≈209,
   rejected≈5` (two independent isolated fetches gave `209/214` and `208/216`). The filter works
   correctly when links reach it — not the cause.
2. **The seed page's own real extracted internal links, cross-referenced against the known
   304-URL seed set**: 9 genuinely net-new same-host candidates existed on the seed page alone
   (a bare `/de` language root, two paths missing the `/de/` prefix, several
   `/de/free-pro-team@latest/rest/...` explicit-version duplicates of already-known pages, two
   `/de/site-policy/...` footer pages). The frontier had real material to find — not a coverage
   ceiling.
3. **Success/failure counts from an `on_state_change`-instrumented run of the ACTUAL production
   `resume_state`/strategy**: **101 success / 682 failure** out of 783 attempts. Failures were
   dominated by `"Blocked by anti-bot protection: Structural: minimal_text on small page (168
   bytes, 17 chars visible)"` and real `HTTP 429`. `link_discovery` only runs `if result.success:`
   — most pages never had their links examined at all.

**Diagnosis: fetch failures, not filter rejections and not link-extraction gaps.** The frontier
came back empty because the fetches feeding it were failing upstream of everything in this
module's own logic (filter, extraction, dedup).

**Whether the 168-byte responses were a rate-limit or a rendering artifact — checked, not
assumed**: the identical URL that returned the 168-byte stub under concurrent batch load returned
a normal ~363KB real page when fetched in complete isolation immediately after.
`wait_until="networkidle"` (full JS execution) produced byte-identical link counts to
`wait_until="domcontentloaded"` on the same page, and a plain `curl` (no browser, no JS at all)
already lacks the same content the "missing" case was checking for. Rate-limit artifact, confirmed
— the fix is pacing/concurrency, not `wait_until`.

## Fix 1: per-domain pacing

`BFSDeepCrawlStrategy` exposes no dispatcher configuration at all (confirmed: no "dispatcher"
anywhere in `bfs_strategy.py`/`base_strategy.py`) — it calls `crawler.arun_many(urls=urls,
config=batch_config)` with no dispatcher argument. Reading `async_webcrawler.py`'s `arun_many`
directly: when `dispatcher is None`, it builds its own `MemoryAdaptiveDispatcher`, reading
`max_session_permit` and the `RateLimiter`'s `base_delay` straight off
`CrawlerRunConfig.semaphore_count`/`mean_delay`/`max_range`. crawl4ai already has a working,
tested, per-domain (`RateLimiter.domains: Dict[str, DomainState]`), exponential-backoff-on-429/503
pacing mechanism — it just isn't reachable through `BFSDeepCrawlStrategy`'s own constructor, only
through the `CrawlerRunConfig` handed to it. `discovery.py` now sets
`mean_delay=1.0, max_range=0.5, semaphore_count=8` (`TRAVERSAL_MEAN_DELAY_S`/
`TRAVERSAL_MAX_RANGE_S`/`TRAVERSAL_CONCURRENCY`) explicitly — not values invented for this module,
but this project's own MEASURED chromium pacing (`pipe_scraper_constants.DOWNLOAD_DELAY=1.0`/
`CONCURRENCY_PER_DOMAIN=8`, validated by a real concurrency probe,
`process-docs/pipe_scraper_hardening/2026-08-04_stealth_concurrency_probe.md`). crawl4ai's own
defaults (`mean_delay=0.1s, max_range=0.3s, semaphore_count=5`) are tuned for speed against
whatever target, not for a real anti-bot-protected site under this project's own
hundreds-of-seeds-in-one-BFS-level traffic pattern.

**Verification is PARTIAL, recorded honestly.** "Before" is solid: two independent real
measurements under crawl4ai's unpaced defaults, both severely degraded (101/682 from the
instrumented run above; a second, smaller bounded check gave 39/162). A clean "after" could not
be measured the same day — this project's OWN repeated testing against `docs.github.com` today
(including the "before" measurements themselves) pushed the rate-limit state for this
environment's IP into a sustained penalty. Confirmed directly and repeatedly: even 3 isolated,
minimal-volume single-page fetches kept returning `429` well after the offending burst, and a
20+ minute full-scale paced run stalled without completing. What IS verified: the pacing wiring
itself (unit-tested — the three constants reach `CrawlerRunConfig` correctly) and a full real run
of the complete, paced `discover_urls_workflow` against `books.toscrape.com` (587 total, 586
fetched, 0 failed, `stop_reason="max_pages_reached"`) — proving the change does not regress a
real, working target. The actual docs.github.com before/after delta needs re-measuring in a
future session once the rate-limit state has genuinely cleared; the "before" numbers recorded here
are a dated snapshot, not a number to still trust unchanged by then.

## Fix 2: fetch failures and unfetched frontier URLs are now visible on the result

Two additions to the shared result shape, both addressing the same underlying complaint: a
caller must not see "N URLs" and have no way to learn how much of that N was actually confirmed.

- `DiscoveryResult` gained `pages_fetched`/`pages_failed` — aggregate counts of every real fetch
  attempt the traversal made.
- `DiscoveredURL` gained `fetched: bool` (default `True`). A seed is now marked `fetched=False` if
  its OWN traversal re-fetch attempt failed (attribution/source stays what a feeder already
  established — the failure doesn't erase that a feeder found it). A URL the frontier held when
  the page budget ran out — real, found, never attempted at all — is now included in the result
  too, tagged `"traversal"`/`fetched=False`, rather than silently discarded. Captured via the
  same `on_state_change` mechanism M0's own probe used: the LATEST captured state's `"pending"`
  list, at the moment the run stops, IS the leftover frontier.

Verified live on `books.toscrape.com`: **800 total URLs** in the result (up from 586 before this
fix), **586 `fetched=True`**, **214 `fetched=False`** — real book-detail pages the frontier had
found and validated through the scope filter, but the 500-page budget ran out before they were
ever fetched. Previously these 214 were silently gone.

One flag intentionally does double duty here: `fetched=False` does not distinguish "tried and
failed" from "never tried at all" — both collapse into the same boolean. Noted as a Gotcha in
`src/crawler/DOCS.md`, not fixed here; `_traverse`'s own two source lists (`fetched`,
`frontier_leftover`) are kept separate internally and could be threaded through as two fields
later if a caller ever needs the distinction (e.g. to retry only the never-attempted set).

## Open item, deferred: version-canonicalization crosses the navtree/discovery boundary

Found during check #2 above, real, not hypothetical: a link discovered mid-traversal to an
explicit-version URL (`/de/free-pro-team@latest/rest/quickstart`, found on the real seed page) is
treated as distinct from the already-known canonical seed (`/de/rest/quickstart`), even though
they are the same page. `seed_feeders_navtree.py`'s `_canonicalize_version_url` exists and is
correct for the case it was built for — unioning each version's OWN navtree walk, inside the
navtree feeder itself — but nothing calls it on a URL `discovery.py`'s own traversal finds, and
the version-key list canonicalization needs lives inside the navtree feeder's own internals, not
anywhere `discovery.py` currently has access to. This needs its own design decision (a shared
lookup surfaced through `FeederResult`? re-detected independently during traversal? something
else?) rather than a quick patch, and crosses a module boundary this milestone did not open.
Deliberately not fixed here — its own milestone, next.

## Verification

`./venv/bin/python -m pytest dev/tests/test_discovery.py -v` → 29 passed (24 before this round +
5 new `_merge_results` tests). Full suite: `./venv/bin/python -m pytest` → 344 passed, 0
regressions against the prior 339. Real runs: `books.toscrape.com` full `discover_urls_workflow`
(paced) — 800 total / 586 fetched / 214 frontier-leftover / 0 failed / `max_pages_reached` /
107.1s. `docs.github.com` — see the PARTIAL note above; "before" numbers real and cited, "after"
numbers not obtainable this session due to self-inflicted rate-limiting.
