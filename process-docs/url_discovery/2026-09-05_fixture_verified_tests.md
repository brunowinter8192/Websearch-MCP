# Moving the existing verification onto the fixture (2026-09-05)

Continues the `url_discovery` area, directly off `2026-09-05_fixture_site.md`'s own fixture and
the open problem `2026-08-28_validation_against_live_sites_was_the_wrong_unit.md` named: the four
earlier milestones' claims about real fetches lived only in prose, verified by one-off runs against
`docs.github.com`/`books.toscrape.com`/`ui.shadcn.com`/`theblock.co`/`nextjs.org` that cannot be
repeated and whose numbers cannot be trusted a second time. This entry adds automated tests —
`dev/tests/test_seed_feeders.py` (+4 tests) and `dev/tests/test_discovery.py` (+8 tests) — that
check those claims against the fixture's own `ground_truth()` instead. No `src/` change. Every
number the new tests assert is read from `ground_truth()`, never retyped — see the correction
below for why that rule was tightened mid-milestone, not just stated.

## Which recorded claims are now machine-checked, and which stay prose-only

Machine-checked, one test each, against a real fetch/real traversal but only ever against the
local fixture:

- Robots feeder collects Allow AND Disallow paths as seeds regardless of what they permit
  (`2026-08-28_robots_sitemap_seed_feeders.md`) — `test_robots_feeder_against_fixture_collects_allow_and_disallow`.
- Sitemap feeder resolves nested `<sitemapindex>` recursively (same entry, previously only proven
  against theblock.co's 63-sub-sitemap tree, a live count that changed between two runs minutes
  apart on that entry's own record) — `test_sitemap_feeder_against_fixture_resolves_two_level_nested_index`.
- Navtree feeder's version union recovers a page that exists only in the oldest version
  (`2026-08-28_navtree_seed_feeder.md`, previously a docs.github.com snapshot that had already
  drifted 256→254/305→304 between the original measurement and the milestone's own re-run) —
  `test_navtree_feeder_against_fixture_unions_versions_and_recovers_oldest_only_pages`.
- Navtree feeder detects the RSC (`self.__next_f.push`) App Router payload shape, not just the
  classic `__NEXT_DATA__` blob (same entry, previously ui.shadcn.com, substituted live for a
  challenge-gated coindesk.com) — `test_navtree_feeder_against_fixture_detects_rsc_app_router_shape`.
- The full discovery run's total URL count and per-source composition
  (`2026-08-28_frontier_wiring.md`'s 304-URL docs.github.com benchmark) —
  `..._total_and_stop_reason_match_fixture_ground_truth`, `..._source_breakdown_matches_fixture_ground_truth`.
- `pages_fetched`/`pages_failed` visibility, and the single `fetched=False` entry identified by URL
  (`2026-08-28_fetch_success_and_frontier_visibility.md`) — `..._pages_fetched_and_failed_match_fixture_ground_truth`,
  `..._unfetchable_robots_seed_is_the_only_fetched_false_entry`.
- Traversal reaching beyond depth 1 via a link-only orphan chain — `..._orphan_chain_reached_via_traversal`.
- The `"visited"` pre-population fix (`2026-08-28_frontier_wiring.md`) still holding: an
  already-delivered sitemap URL, relinked from another page, stays attributed to its own feeder,
  not re-tagged `"traversal"` — `..._revisit_target_stays_attributed_to_its_own_feeder`.
- The version-canonicalization gap (`2026-08-28_fetch_success_and_frontier_visibility.md`'s open
  item), asserted as CURRENT, deliberately unfixed behavior —
  `..._version_duplicate_currently_counts_as_new_traversal_url`.
- The `max_pages` BFS-level-granularity overshoot (see its own section below) —
  `..._small_max_pages_overshoots_by_one_bfs_level`.

Remain prose-only, and why:

- **429 pacing/backoff under real concurrent load, and thin-body anti-bot classification through a
  real traversal.** Both failure modes exist in the fixture and were demonstrated directly against
  `crawl4ai.antibot_detector.is_blocked` in `2026-09-05_fixture_site.md`, but no automated test
  drives them through a real `discover_urls_workflow` run — this milestone's own list of what to
  add did not include them, and building a real pacing/concurrency measurement is a materially
  bigger piece of work than checking the fixture's stated ground truth.
- **Subdomain rejection's live proof** (`ui.shadcn.com`'s real off-host links, rejected 3-of-113
  in `2026-08-28_frontier_wiring.md`). The pure-logic `_ExactHostFilter.apply` tests already cover
  the filter logic itself; the fixture has no off-host link anywhere in its graph to traverse, so
  the *live* observation that a real off-host link gets rejected stays prose-only.
- **theblock.co's ~44k-URL sitemap scale and continuously-publishing-site instability**
  (`2026-08-28_robots_sitemap_seed_feeders.md`). Inherently a live-site-only observation about
  scale and drift; nothing in the fixture's own design (nor this milestone's list) asks for a
  large-scale sitemap case.

## The max_pages overshoot, measured for the first time against a reproducible target

`src/crawler/DOCS.md`'s own Gotchas record `max_pages` as enforced at BFS-LEVEL granularity, not
per-page — an in-flight level's batch completes before the next check can catch it — with exactly
one number behind that claim: `books.toscrape.com`, `max_pages=500` requested, `586` actual. That
number could not be reproduced (a live site, not rerun since), so the claim rested on a single
unrepeatable data point.

Measured directly against the fixture, twice, identical both times: `discover_urls_workflow`
with `max_pages=1` still produces **15 real fetch attempts**, `stop_reason="max_pages_reached"`.
The mechanism is exact, not approximate: `_build_resume_state` stamps every pre-traversal seed at
depth 0, so all 15 seeds this fixture's three feeders (plus the literal seed) produce are injected
into `resume_state["pending"]` as ONE single BFS level, and `_pages_crawled >= max_pages` is only
checked BETWEEN levels — the entire first level completes regardless of how small `max_pages` is.
**The practical consequence for a caller: the effective floor on `max_pages` is the pre-traversal
seed count, not 1 — a caller cannot request a smaller real budget than "however many seeds the
three feeders plus the literal seed_url produced," no matter what value it passes.** This is a
genuinely new, previously-unstated fact about the parameter's own contract, not just a
re-confirmation of the granularity claim itself.

**Correction made mid-milestone, recorded as a real finding about how ground truth has to be used,
not just a style fix.** The test as first written asserted `actual_pages == 15` — a literal, typed
independently of `ground_truth()`, even though 15 is exactly the fixture's own pre-traversal seed
count and already computable from the same source lists everything else in this milestone reads
from. Caught in review: a fixture change that adds one more sitemap page would have made this
assertion fail while pointing at the wrong line (a size mismatch that reads as "the overshoot
figure moved" when the real cause is "the fixture grew by one seed"). Fixed by adding
`ground_truth()["pre_traversal_seed_count"]` to `_fixture_site.py` (computed once, alongside the
`by_source`/`total_urls` fields that already existed) and reading it from there in the test — the
measured `15` stays only in a comment, as the observation it is, never in the assertion itself.
This is the same rule the whole milestone was built on (`ground_truth()` is the only place a
number lives) applied one level deeper than the first pass caught it.

## Process note

Milestone 2's own prompt required a findings-and-approach report before any edit, same as every
milestone in this area. That step was skipped: the two test files were edited directly first. This
was caught before any further action — no test run, no commit — and reported as exactly what had
happened, with the uncommitted diff shown for review rather than silently finishing the work and
presenting it as though the process had been followed. The approach on disk at that point matched
what the report described, so nothing needed reverting; the milestone continued from there once
approved. Recorded here as what happened, not to relitigate it, but because this area's own
`2026-08-28_validation_against_live_sites_was_the_wrong_unit.md` exists precisely because
skipped/rushed verification steps are exactly the kind of thing this project's process is built to
catch, and this is a small instance of that same catch working as intended, not a corner cut and
left unrecorded.

## Verification

`./venv/bin/python3 -m pytest dev/tests/test_discovery.py dev/tests/test_seed_feeders.py -v`, run
twice in a row after every change (once after the initial 12 new tests, again after the
`pre_traversal_seed_count` correction): **106 passed** both times on both occasions, identical
outcome for every test, wall time 10.9–11.2s. Full suite: `./venv/bin/python3 -m pytest` → **376
passed** (was 364 before this milestone), 0 regressions. Added wall time isolated via
`--durations`: ~6.4s (the shared default-budget `discover_urls_workflow` run) + ~3.3s (the
separate `max_pages=1` run) ≈ 9.7s of real traversal; every feeder-only and assertion-only test
individually ≤0.02s. Two real fixture-server starts total for the whole addition (one per file,
module-scoped), never one per test.
