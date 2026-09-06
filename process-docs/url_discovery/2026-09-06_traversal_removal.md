# Removing discovery.py's browser-driven link-graph traversal (2026-09-06)

Closes the `url_discovery` area's two-phase design that every prior entry in this folder measured,
tuned, and hardened: phase one (the three seed feeders, plain HTTP, seconds) and phase two (a
`crawl4ai` headless-browser `BFSDeepCrawlStrategy` traversal over the resulting URL set, purely to
read each page's links and find pages no feeder had listed). Phase two is gone. The decision was
made before this entry, not re-litigated here: link-following moves into the scrape step, which
already loads each page for its content anyway, so a separate link-only traversal was a duplicate
fetch of every page in the run.

## The number that closed the question

Measured against `https://platform.claude.com/docs`: the three feeders returned 3571 URLs in about
two seconds. The traversal over those same 3571 URLs was still running after twelve minutes, with a
projected runtime well over an hour. A re-run of the same seed_url against the now-feeder-only
`discover_urls_workflow` (this milestone's own end state) returned the same 3571 URLs
(`navtree_flat=6, robots=1, seed=1, sitemap=3563`) in 0.6s internal / 1.56s wall including process
startup, writing `pipe_scraper`'s own `--url-file` shape unchanged. Against the local
`dev/url_discovery/_fixture_site.py` fixture, the equivalent run returned all 15 expected URLs
(`navtree_tree=6, robots=3, seed=1, sitemap=5`, matching `ground_truth()` exactly) in under 0.1s.

## What went with the traversal, and why each piece had no purpose left

Everything removed from `src/crawler/discovery.py` existed solely to run the traversal or to make
its own findings legible — nothing was removed that the feeders themselves still needed:

- The `crawl4ai` import itself (`AsyncWebCrawler`, `BrowserConfig`, `CrawlerRunConfig`, `CacheMode`,
  `deep_crawling.BFSDeepCrawlStrategy`/`FilterChain`/`URLFilter`) — discovery.py no longer opens a
  browser or fetches a page at all; every fetch now happens once, inside the feeders themselves.
- `_ExactHostFilter`, `_traverse`, `_build_resume_state`/`_validate_resume_state`,
  `_determine_stop_reason` — all traversal-only scope/frontier/termination machinery.
- `_extract_version_keys`/`_resolve_canonical_alias` and `_merge_results` — these existed to
  recognize, after a real traversal fetch, that a mid-crawl-discovered URL was an explicit-version
  duplicate of an already-known seed (closed as its own milestone, `2026-09-05_version_duplicate_
  recognition.md`). With no traversal fetch left to annotate, the mechanism has nothing to operate
  on.
- Constants `DEFAULT_MAX_DEPTH`, `MIN_MAX_PAGES`, `MAX_PAGES_PER_SEED`, `TRAVERSAL_MEAN_DELAY_S`,
  `TRAVERSAL_MAX_RANGE_S`, `TRAVERSAL_CONCURRENCY` — every one of them tuned a traversal that no
  longer runs. `TRAVERSAL_CONCURRENCY`'s own correction from 8 to 1 (`2026-09-05_pacing_
  measurement.md`) and the BFS-level-granularity overshoot finding (586 vs. a requested 500 on
  `books.toscrape.com`) are now historical facts about a removed mechanism, not properties of the
  current code — left in this folder's own prior entries, not restated as current in `DOCS.md`.
- `DiscoveryResult.stop_reason`/`pages_fetched`/`pages_failed` and
  `DiscoveredURL.fetched`/`canonical_url` — all four existed to make the traversal's own partial,
  budget-bounded, sometimes-failing fetch legible to a caller. A `DiscoveredURL` produced by a
  feeder was never itself "fetched" by discovery.py in the sense these fields meant; keeping them
  would have meant every entry reporting a fixed, uninformative value.
- `discover_urls_workflow`'s `max_depth`/`max_pages` parameters and `cli.py`'s `--max-pages` flag —
  there is no page budget left to override once no page is fetched.

`seed_feeders_navtree.py`'s `canonicalize_version_url` and `FeederResult.version_keys` were the
traversal's only consumer outside `seed_feeders.py` itself. Both stay on the feeder contract — the
navtree feeder still uses `canonicalize_version_url` internally for its own version union, which is
a real, independent need — but neither is called from outside `seed_feeders_navtree.py` anymore.
Removing them was judged out of scope: doing so would touch the feeders' own behavior, which this
milestone was explicitly told to leave alone, and the field costs nothing to leave in place on a
data contract a future caller may still want.

## What `discover_urls_workflow` is now

Feeders run concurrently over plain HTTP, merged into one `{url: source}` seed set with the literal
`seed_url` first-write-wins, same as before this milestone — `_assemble_seeds` itself did not
change and its own tests were left untouched. The result is `DiscoveryResult(urls, ok, wall_s,
failed_feeders, error)`, `urls` a flat `list[DiscoveredURL(url, source)]`. `cli.py discover_urls`
still writes the same plain one-URL-per-line file `pipe_scraper.py`'s own `--url-file` reads; the
only change to the CLI surface is that the console summary no longer reports the four now-removed
fields, and `--max-pages` is gone.

## Test and fixture consequences

`dev/tests/test_discovery.py` dropped 41 tests that exercised only the removed traversal
machinery (resume-state building/validation, stop-reason determination, the exact-host scope
filter, `_merge_results`'s fetched/frontier-leftover/canonical_url handling, version-duplicate
alias recognition, the max_pages-overshoot property) — deleted, not weakened to still pass against
the new shape. The four `_assemble_seeds` tests and `test_seed_feeders.py` in full were left
untouched, since neither ever tested the traversal.

`dev/url_discovery/_fixture_site.py`'s `ground_truth()` dropped every traversal-derived field
(`pages_fetched_expected`/`pages_failed_expected`/`expected_stop_reason`/
`pre_traversal_seed_count`/`robots.unfetchable*`/`orphans`/`revisit_test`/`version_duplicate_test`);
`total_urls`/`by_source` now state the feeder-only seed set directly. `ORPHAN_CHAIN`,
`REVISIT_TEST_PAGE`/`TARGET`, and `VERSION_DUP_TEST_PAGE`/`TARGET`/`CANONICAL` were deleted from the
fixture along with their routes and links from the seed page — each existed solely to give the
traversal something to find that no feeder listed, and had no other consumer once that traversal's
own tests were gone. `NAVTREE_V1_ONLY_PAGES` was NOT touched: it tests the navtree feeder's own
version union, a real, still-live feeder behavior, not the traversal.

The fixture's rate-limit/thin-body failure-mode switches (`/_control/*`) were deliberately left in
place even though no current test exercises them — they were built to validate the traversal's own
pacing (`2026-09-05_pacing_measurement.md`), but are generic HTTP-server capabilities, not
traversal-specific code, and a future caller that fetches these same discovered URLs for real (the
scrape step) may still want them. Removing them was judged a separate, larger, unrequested change
and was not made here.
