# The frontier: feeders into traversal (2026-08-28)

Milestone 3 of the URL-discovery redesign, and the one that makes the three feeders
(`process-docs/url_discovery/2026-08-28_robots_sitemap_seed_feeders.md`,
`2026-08-28_navtree_seed_feeder.md`) into an actual discovery step. Module:
`src/crawler/discovery.py` (227 LOC), public entry `discover_urls_workflow(seed_url,
max_depth=None, max_pages=None) -> DiscoveryResult`. Re-read
`process-docs/url_discovery/2026-08-28_resume_state_preseed_probe.md` before designing, per this
milestone's own instruction — three of its results shaped the design directly and are cited by
name below.

## Seed assembly and failed-feeder handling

All three feeders run concurrently against `seed_url`. The literal `seed_url` is always injected
as its own seed (tagged `"seed"`), independent of what any feeder returns — this is what makes a
traversal-only host (zero feeder seeds) still have a starting point. Feeder output merges into one
`{url: source}` dict, first-write-wins (seed, then robots, then sitemap, then navtree). A feeder
returning `ok=False` contributes nothing SILENTLY: its name and error land in
`DiscoveryResult.failed_feeders`, always visible, and the run still proceeds on whatever the other
feeders (plus the always-present literal seed) produced. The run itself is only `ok=False` when
`seed_url` cannot be used at all — the same precondition class every feeder already uses. A
degraded-but-nonzero seed set is a successful, partial run, not a failed one; that is a real
information difference `failed_feeders` exists to preserve rather than being flattened into "found
nothing" the way M0 found `resume_state`'s own silent failures do.

## Injection: resume_state shape and validation

`{"pending": [{"url": u, "parent_url": None} for u in seeds], "depths": {u: 0 for u in seeds},
"visited": list(seeds)}`. Every seed's depth is stamped EXPLICITLY at 0, not left to
`BFSDeepCrawlStrategy`'s own default — M0's Result 3 already showed an unstamped seed silently
defaults to 0 anyway; this makes that choice visible in the data instead of relying on
undocumented default behavior. `_validate_resume_state` fails fast (raises `ValueError`) before
ever calling `.arun()`, targeting M0's two silent-failure shapes directly: an empty dict and a
wrong/missing `"pending"` key, plus a missing `depths` entry for any pending URL.

**A real gap found only by a live run, not by design review: `"visited"` needs pre-populating
too, and the first implementation didn't do it.** `link_discovery`'s own dedup (`bfs_strategy.py`)
checks ONLY the `resume_state`-derived `"visited"` set, never the `"pending"`/seeds list itself —
so an already-known seed rediscovered as a link FROM another page was not recognized as
already-known, wasting part of the page budget "rediscovering" URLs the run already had and
undercounting genuine traversal-only contribution. Caught via the subdomain-rejection verification
run below (`ui.shadcn.com/docs`, 247 seeds from `navtree_tree` alone): traversal-sourced count
came back 0 even at a small bounded budget, which should have had at least a chance to show
something. Fixed by adding `"visited": list(seeds)` to the built `resume_state`. Not a complete
fix: `link_discovery` normalizes a rediscovered link via crawl4ai's OWN
`normalize_url_for_deep_crawl` (strips tracking params, does not collapse `www.`/apex, does not
strip default ports) before comparing against `"visited"`, which is populated here with THIS
project's own `normalize_url`-normalized strings — the two coincide for typical simple doc-site
paths, not guaranteed for every URL shape (documented as a Gotcha, not chased further).

## Scope during traversal

The scope decision — the seed host and only the seed host, not path-prefixed, not subdomains — is
enforced by a custom `URLFilter` subclass, `_ExactHostFilter`, doing exact `urlsplit().hostname`
comparison with `www.`/apex collapsed via a shared `host_key` helper (promoted from a
`seed_feeders.py`-private function to `seed_feeders_scope.py`, alongside `require_host`, so
`discovery.py` and the feeders apply the identical host-comparison rule instead of two subtly
different ones). Passed as the strategy's `filter_chain`, with `include_external=True` set
explicitly on the strategy.

**Why not crawl4ai's own `DomainFilter`, and why `include_external=True`: read the actual source,
not the docstring.** `DomainFilter._is_subdomain` deliberately treats a CHILD subdomain as
in-scope (`domain.endswith(f".{parent}")`) — correct for a filter meant to allow a domain family,
wrong for "not subdomains." More surprising: crawl4ai's own `internal`/`external` link
classification (`utils.py`) is not a scope mechanism at all — `url_base = url.split("/")[2]; if
url_base not in href: external` is a SUBSTRING check against the CURRENT PAGE's own netloc (not
the seed's), meaning `docs.github.com` would substring-match inside a hostile
`docs.github.com.evil.com`, and this project's own `www.`/apex-is-the-same-host scope decision
would be silently violated (a plain string mismatch reads as "external" under this check). Relying
on crawl4ai's `include_external=False` default would have been exactly the kind of assumption this
milestone explicitly warned against verifying instead of reading. `include_external=True` ensures
crawl4ai's own crude split never gets a chance to matter; `_ExactHostFilter` is the sole scope
authority.

**Verified by two real runs, not by reading the API.** `docs.github.com/de/rest`'s real homepage
links to `github.com` (parent domain), `support.github.com`/`services.github.com` (genuine
SIBLING subdomains of the parent, different subdomains than `docs.github.com` itself), confirmed
directly via `curl` before any run. `ui.shadcn.com/docs`'s real homepage links to `github.com`,
`vercel.com`, `twitter.com`. A direct, low-level check (fetch the real `ui.shadcn.com/docs` page,
extract its real 113 links via crawl4ai, apply `_ExactHostFilter` to each) recorded exactly 3
off-host candidates (`github.com/shadcn-ui/ui`, `vercel.com/new`, `twitter.com/shadcn`), all 3
rejected, 110 same-host links accepted — `filter_chain.stats` confirms `total=113 passed=110
rejected=3`. This is the airtight version of the proof: not merely that no off-host URL appeared
in a final result (which coverage limits alone could produce), but that the filter was actually
exercised against a real off-host link and rejected it.

## Budget and termination — re-derived once, against the wrong driving scenario first

The first draft sized both `max_depth` and `max_pages` against the MANY-seeds case (`docs.github.com`,
304 seeds): `max_depth=1` (shallow, reasoned as "each seed is an independent root, so depth must
stay small") and `max_pages=seeds+200`. Both were wrong, for the same underlying reason: depth was
being used as a second safety device when only `max_pages` needs that job.
`BFSDeepCrawlStrategy._pages_crawled >= max_pages` is checked unconditionally between every BFS
level regardless of `max_depth`'s value — termination never depends on depth. Capping depth caps
REACH, not WORK. The inversion showed up in the one-seed case: a traversal-only host (no feeder
seeds at all) with `max_depth=1` and a ~201-page ceiling could not even reach the 248-page
bare-link-following figure already on record for `docs.github.com` from a much earlier BFS probe —
undershooting a benchmark this project already knew it could beat, in the one scenario (zero
feeder help) where traversal is the ONLY mechanism operating.

**Re-derived:** `DEFAULT_MAX_DEPTH = 10` — generous, not protective, since `max_pages` alone
guarantees termination no matter how generous depth is. `MIN_MAX_PAGES = 500`,
`MAX_PAGES_PER_SEED = 2`, resolved default `max(500, num_seeds * 2)` — the floor drives the
single-seed/traversal-only case and is sized against the one real number on record (248), roughly
doubled for headroom; the per-seed term only matters once seed count is large enough to need more
budget just to visit every seed once, and stays linear (not compounding with depth) regardless of
how generous `max_depth` is.

**500 is a chosen starting value, not a measured optimum for any particular site.** It was not
derived from a study of real site sizes; it is defensible because a caller LEARNS whether it was
ever binding from `DiscoveryResult.stop_reason` ("max_pages_reached" means yes; "frontier_exhausted"
means the real site needed less), not because 500 is asserted as the right number anywhere. A
future site hitting "max_pages_reached" is not evidence 500 was wrong — it may simply be bigger
than 500 pages, exactly the case the explicit `max_pages` override parameter exists for.

**A genuine contract detail found only by running it, not by reading the source comment alone:
`max_pages` is enforced at BFS-LEVEL granularity, not per-page.** The `_pages_crawled >= max_pages`
check only runs BETWEEN levels; an entire in-flight level's batch (crawl4ai's own default
dispatcher, `MemoryAdaptiveDispatcher(max_session_permit=20)`, confirmed via source) completes
before the next check can catch it. Measured directly: `max_pages=500` against
`books.toscrape.com` (single seed, no feeder coverage) produced **586** actual
`strategy._pages_crawled`, not 500. The cap is still real — bounded overshoot, not unbounded, so
termination is never in question — but a caller should read "max_pages" as "max_pages plus up to
one level's worth," not an exact ceiling.

`_determine_stop_reason` reads `strategy._pages_crawled`, a crawl4ai PRIVATE (underscore-prefixed)
attribute. Fine to use — comparing it against `strategy.max_pages` is the only way to distinguish
the two stop reasons without re-deriving crawl4ai's own internal bookkeeping — but a future
crawl4ai upgrade could rename or restructure it without any compatibility guarantee; flagged as a
Gotcha in `src/crawler/DOCS.md`, not just here.

## Provenance in the output

`DiscoveryResult.urls` is `list[DiscoveredURL(url, source)]`, `source` ∈ `{"seed", "robots",
"sitemap", "navtree_tree", "navtree_flat", "traversal"}`. A URL that is BOTH a seed and
successfully re-fetched during traversal keeps its ORIGINAL attribution (first-write-wins in the
seed dict, never overwritten to `"traversal"`) — only a genuinely new URL, absent from every
feeder's output and from the literal seed, is tagged `"traversal"`. This is what makes "how much
did traversal contribute that no feeder had already found" a direct count, not an estimate.

## Verification — three real runs

**`docs.github.com/de/rest` (primary benchmark).** `ok=True, stop_reason="frontier_exhausted",
wall_s=176.0`. Total: **304** URLs — `navtree_tree: 303, seed: 1` (the seed page was itself one of
navtree's 304 URLs, so it kept the `"seed"` tag under first-write-wins). **Traversal-only
contribution: 0.** `failed_feeders: {}`. All 304 hosts confirmed `docs.github.com`, none other.
Relative to the milestone's own reference points: the navigation-tree feeder alone was already
measured at 304 in M2; this run's total is identical because traversal genuinely found nothing new
to add — navtree's coverage of this specific site is already close to exhaustive (304 of the
dated 305 gold standard), so there is little marginal room left for link-following to contribute.
`stop_reason="frontier_exhausted"` (not budget) is itself informative: the run was never
budget-constrained here, `max_pages=max(500, 304*2)=608` was never approached — a clean
demonstration of the "frontier exhausted" path, distinct from the budget-driven runs below.
(This run needed a retry: the first attempt, at the many-seeds default before the redesign above,
ran into real GitHub rate-limiting (`429`) partway through — confirmed directly via isolated
single-page fetches before and after — and was killed after ~20 minutes rather than trusted; a
later attempt, after the rate limit cleared on its own, is the number reported here.)

**Traversal-only host: `books.toscrape.com`** (already established in M0/M1/M2 as carrying no
sitemap, no useful robots.txt, no framework payload — re-confirmed here: `failed_feeders={}`, all
three feeders returned `ok=True` with empty `urls`). `ok=True, stop_reason="max_pages_reached",
wall_s=64.4`. Total: **586** URLs — `seed: 1, traversal: 585`. All 586 hosts confirmed
`books.toscrape.com`. This is the scenario the re-derived defaults were built for: with zero
feeder help, `max_pages=max(500, 1*2)=500` (the floor) drove the run, comfortably clearing the
248-page reference figure (more than double), and the stop was budget-driven, not
depth-driven — the real max depth reached was 2 out of the 10 available.

**Subdomain rejection.** Reported above under Scope — the direct, instrumented check against
`ui.shadcn.com/docs`'s real 113 extracted links (110 accepted, 3 rejected, all 3 being real
off-host links) is the strongest evidence; the full `discover_urls_workflow` run against the same
site (`max_pages=60` override, purely to bound the proof) additionally confirmed zero off-host
URLs across all 248 final results.

## Tests

`dev/tests/test_discovery.py` (225 LOC, 24 tests) — pure-logic coverage: seed assembly/merge
priority/failed-feeder recording, `resume_state` building (including the `"visited"`
pre-population fix) and validation (every M0-documented malformed shape plus a missing depths
entry), stop-reason determination (a tiny stub, including the real 586-vs-500 overshoot case as an
assertion), and `_ExactHostFilter.apply` (same-host, `www.`/apex collapse, sibling-subdomain,
child-subdomain, parent-domain, and malformed-input rejection). The full crawl4ai-driven traversal
itself is verified by the three real runs above, not mocked — matching M0's own precedent.
`./venv/bin/python -m pytest dev/tests/test_discovery.py -v` → 24 passed. Full suite:
`./venv/bin/python -m pytest` → 339 passed, 0 regressions against M2's 315.
