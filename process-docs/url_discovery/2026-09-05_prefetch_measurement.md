# Measuring crawl4ai's prefetch short-circuit against the fixture, then switching it on (2026-09-05)

Continues the `url_discovery` area. `discovery.py`'s traversal generates markdown for every page
and `link_discovery` (`bfs_strategy.py`) reads only `result.links` — crawl4ai's `prefetch=True`
skips the scraping strategy, markdown generation, content filtering and media extraction, returning
a `CrawlResult` built from crawl4ai's own separate `quick_extract_links` (`utils.py`) instead. The
question this entry answers, measured against `2026-09-05_fixture_site.md`'s fixture rather than a
live host: does that swap change what the discovery step finds, and what does it save. No `src/`
change until both answers were in.

## Set identity, and how it was produced

Three runs per configuration, `discover_urls_workflow(seed_url(port))` against a freshly-reset
fixture, comparing the full `(url, source, fetched)` tuple set of every `DiscoveredURL` — not a
count, a set. Method: `src.crawler.discovery.CrawlerRunConfig` monkeypatched in a one-shot
`/tmp` script (never staged) to inject `prefetch=True` for the "prefetch" runs; the unmodified
import for the "baseline" runs. `src/` was untouched for the entire measurement phase.

Result: **every run, both configurations, `total=20, pages_fetched=19, pages_failed=1,
stop_reason="frontier_exhausted"`, and the full 20-entry tuple set was byte-identical between
configurations** — `only_in_baseline = set()`, `only_in_prefetch = set()`. All 3 runs within each
configuration were also identical to each other (fully deterministic against this fixture). This
covers the already-fixed "visited" pre-population case and the still-open version-duplicate case
(`2026-09-05_fixture_verified_tests.md`) identically in both configurations — neither behavior
moved.

## Timing: measured, and explicitly bounded to what this fixture can say

Two measurements, not one. Full-run wall time, 3 repetitions each: baseline `6.23s, 6.31s, 6.03s`
(mean 6.19s); prefetch `5.78s, 6.13s, 5.78s` (mean 5.90s) — a ~0.29s (~4.7%) average delta that
sits inside the baseline configuration's OWN run-to-run spread (its 3 runs alone span 0.28s).
Isolated single-page fetch (no BFS, no pacing — `AsyncWebCrawler.arun()` direct, prefetch toggled,
5 repetitions each) to separate fetching from processing cleanly: baseline `0.167, 0.171, 0.166,
0.166, 0.167s` (mean 0.1674s); prefetch `0.177, 0.167, 0.165, 0.166, 0.165s` (mean 0.168s) — no
measurable difference, prefetch not even consistently faster.

**This does not generalize, and is not reported as if it does.** This fixture's pages are a few
hundred bytes; the real page this area's own benchmark measured, `docs.github.com`, was ~360KB.
Markdown generation on a page a few hundred bytes long is not real work to skip — the isolated
measurement shows exactly that, a non-event. Markdown generation on a 360KB page is not the same
claim, and this fixture cannot make it: its own design (small, simple, deterministic pages) is
precisely what makes the processing cost disappear into measurement noise. The honest reading is
"unmeasurable on this fixture, and this fixture cannot answer the real-page question" — not
"prefetch saves nothing."

## The failure-mode gap, closed with byte-identical measurements

The concern: `async_webcrawler.py`'s prefetch short-circuit builds its `CrawlResult` with
`success=True` written in literally. If that value survived to the caller, prefetch would silently
convert a blocked/failed fetch into a reported success — destroying exactly the visibility
`2026-08-28_fetch_success_and_frontier_visibility.md` spent a milestone building
(`pages_fetched`/`pages_failed`/`DiscoveredURL.fetched`). Reading `async_webcrawler.py` suggested
`success` is reassigned OUTSIDE `aprocess_html` (`bool(html)`, then `is_blocked()` on the raw
html/status code, both independent of which path built the result) — but a reading is not a
measurement, and the fixture exists for exactly this case.

Both of the fixture's failure modes were armed and both configurations run against them:

- **429-after-N**: armed past the measured feeder-only request cost (9 requests, measured
  directly by calling `_run_feeders` alone against a reset counter — not assumed) plus a small
  traversal budget. Full-run `pages_fetched`/`pages_failed` matched in magnitude between
  configurations; the exact set of WHICH URLs landed inside the threshold varied run to run — but
  confirmed to vary just as much between two `prefetch=False` runs of the IDENTICAL configuration
  (10 vs. 13 failures on two consecutive baseline-only runs, same threshold), so this is a
  concurrency race under `semaphore_count=8`, not a prefetch effect. The clean, unambiguous
  read is the isolated single-page fetch under 429: **byte-identical** in both configurations —
  `success=False, status_code=429, error_message="Blocked by anti-bot protection: HTTP 429 Too
  Many Requests", html_len=168`.
- **thin-body-200**: full run byte-identical between configurations (`pages_fetched=0,
  pages_failed=1`, the one seed correctly marked unfetched both times — thin-body-on from the
  start also starves the three feeders of anything to find, expected and not the point). Isolated
  single-page fetch: **byte-identical** — `success=False, status_code=200, error_message="Blocked
  by anti-bot protection: Near-empty content (59 bytes) with HTTP 200", html_len=59`.

Confirms the reading exactly: `success`/`is_blocked` classification does not depend on whether
`aprocess_html` took the prefetch short-circuit.

## The decision, and what it follows from

**The switch follows from set identity, not from the timing result.** The timing measurement
produced no usable saving on this fixture — reported as exactly that, not papered over into a
justification. What decided it: the coverage-and-failure-visibility measurements came back clean
on both counts (identical URL sets, identical success/failure classification under both failure
modes), and `prefetch=True` is free on the one thing actually measured and never negative on the
other. `src/crawler/discovery.py`: `prefetch=True` added to `_traverse`'s `CrawlerRunConfig`. No
flag, no env var — one line, permanent, per the milestone's own constraint.

## A false comment, corrected — worth recording as its own case

`_traverse`'s own comment claimed "no markdown generation (this milestone only harvests URLs)"
since the milestone that wrote it. That was never true: nothing in `CrawlerRunConfig` disabled
`markdown_generator`, and `async_configs.py` defaults it to a real `DefaultMarkdownGenerator` —
every page's markdown was generated and immediately discarded, every run, since the frontier-wiring
milestone. The comment asserted a configuration nobody had checked, and it went unchecked because
nothing downstream ever looked at the markdown, so a wrong claim about it never produced a wrong
result — the exact shape of a comment that can go stale silently, with no test or run ever able to
catch it, because nothing exercises the gap between what a comment says a config is and what it
actually is. It is corrected now (the same line, describing `prefetch=True`) because prefetch
makes the OLD claim true for the first time, not because the comment was re-audited on its own.

## Verification

`./venv/bin/python3 -m pytest dev/tests/test_discovery.py dev/tests/test_seed_feeders.py -v` after
the switch: 106 passed, unchanged, no test edited. Full suite, run twice after the switch: 376
passed both times, identical, ~22.1–22.5s. The existing fixture-backed tests needed no changes —
built in the previous milestone specifically to catch a regression here, and confirming none
occurred.
