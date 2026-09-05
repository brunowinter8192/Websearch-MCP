# Making discovery callable, and where the area now stands (2026-09-05)

Continues, and closes, the `url_discovery` area's current plan. `src/crawler/discovery.py` was
finished, measured, and tested, but `src/crawler/DOCS.md` said so literally: its `Called by` line
read "nothing yet." This entry wires it up — `cli.py discover_urls` — and with it the area now
stands at: the discovery step is callable from the command line, its feeders and traversal are
measured against a deterministic local fixture rather than a live host, its pacing values are
measured rather than carried over from a different mechanism, and it no longer depends on any
private crawl4ai attribute. Nothing in `discover_urls_workflow` itself changed this round — this
milestone only wires up what already existed.

## The url-file's two inclusion decisions, argued

`--url-file` (the plain, one-per-line file `pipe_scraper.py`'s own `--url-file` reads) does not
contain every `DiscoveredURL`. Two decisions, each argued rather than picked:

- **Known aliases (`canonical_url` set) are excluded.** The canonical URL already covers that
  content; writing the alias too would spend a real `pipe_scraper` scrape+cleanup+index cycle on
  content already captured, for a caller whose stated goal is coverage, not URL-string
  completeness for its own sake.
- **Unconfirmed URLs (`fetched=False`, whether a genuine fetch failure or a frontier-leftover
  budget cutoff) are INCLUDED.** `pipe_scraper` is a separately-paced, separately-engine-choosable
  scraper (its own `--download-delay`/`--concurrency-per-domain`/`--engine`), and a URL that failed
  under discovery's own traversal pacing may well succeed under it. Dropping these would be a
  silent coverage loss for a retry that is already effectively free — the URL is already known,
  only the fetch itself repeats.

## `max_pages` exposed, `max_depth` not

`--max-pages` is exposed, with help text stating the real ceiling directly (`2026-09-05_pacing_
measurement.md`'s own finding: it cannot go below the pre-traversal seed count, enforced at
BFS-level granularity) — a real override case exists both directions, raising the 500 floor for a
known-huge site or lowering it for a bounded exploratory run. `max_depth` is not exposed:
`DEFAULT_MAX_DEPTH=10` is reach, never the termination lever, and essentially never binds in
practice (measured: `books.toscrape.com` reached depth 2 of 10 available). Exposing it would mainly
invite a caller to accidentally cripple coverage by lowering it, working directly against the one
thing this tool exists to maximize, with no observed compensating benefit.

## Failure handling: a file must never be consumable as a valid empty result

The reason this needed its own decision, not just a default: `pipe_scraper` will happily consume
whatever is in `--url-file`, including nothing, and report a "successful" run over zero pages. A
`discover_urls_workflow` run that comes back `ok=False` (an unusable `seed_url` is the documented
case) sitting silently behind an empty or missing file would be the exact silent-loss failure mode
this whole area exists to prevent, arriving one step later in the pipeline than usual — the kind of
gap `2026-08-28_validation_against_live_sites_was_the_wrong_unit.md` and every entry since have
been closing one at a time.

Decided: on `ok=False`, `cli.py`'s `discover_urls` writes NO file at all, prints
`discover_urls FAILED: <error>` to stderr, and exits 1 — a script or agent checking the exit status
sees failure, and there is no file sitting at the expected path for a later step to misread as a
valid, if empty, result. Verified directly: `discover_urls "not-a-url-at-all" --url-file
/tmp/should_not_exist.txt` → exit code 1, `/tmp/should_not_exist.txt` never created.

A degraded-but-`ok=True` run (a failed feeder, a heavily rate-limited traversal) is explicitly NOT
treated as an error and DOES write the file — that distinction matters, and is not the same
situation. `ok`, `stop_reason`, `failed_feeders`, `pages_fetched`, `pages_failed` print first in the
console summary, unconditionally, even at zero/empty, specifically so a thin result cannot be
mistaken for a complete one just because those facts would otherwise sit below the URL-count fold.
The tooling reports the facts; the agent judges whether the run looks trustworthy enough to act on.

## No CLI-layer test — a deliberate gap, not an oversight

`cli.py` has no existing test file for any of its other three subcommands, and none is added for
`discover_urls` either — the dispatch wiring itself (argument parsing, the file-write/exit-status
branch) was verified by real runs against the fixture (both the success and the `ok=False` path),
matching this file's own established pattern of being verified by use rather than by a dedicated
test suite. `discover_urls_workflow` itself already carries its own full fixture-backed test
coverage from earlier entries in this area — this milestone added no new behavior there to test,
only a thin CLI wrapper around it.

## Verification

Real run against the fixture: `ok=True stop_reason=frontier_exhausted wall_s=21.8`,
`failed_feeders={}`, `pages_fetched=19 pages_failed=1`, `total URLs: 20` (matching
`ground_truth()` exactly, as every prior milestone's run of this fixture has), 1 known alias
excluded, 19 URLs written. The resulting file was parsed with `pipe_scraper.py`'s own exact
`splitlines()`/`strip()`/blank-line-drop logic and produced the same 19 URLs — confirmed directly
usable as its `--url-file` input, not just assumed compatible. Full suite:
`./venv/bin/python3 -m pytest` → 388 passed, unchanged from before this milestone.
