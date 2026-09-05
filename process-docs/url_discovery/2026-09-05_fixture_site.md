# A deterministic fixture site, so later milestones have ground truth to measure against (2026-09-05)

Continues the `url_discovery` area, directly off
`process-docs/url_discovery/2026-08-28_validation_against_live_sites_was_the_wrong_unit.md`'s own
open item: "the fixture site does not exist yet." This entry builds it —
`dev/url_discovery/_fixture_site.py` (449 LOC) + `dev/url_discovery/02_fixture_site_server.py`
(45 LOC), a local `ThreadingHTTPServer` serving a small documentation site whose page inventory is
a fact stated in code, not a number measured on a live host. No `src/` changes — this milestone
builds the instrument, it does not touch `src/crawler/discovery.py` or its feeders.

## Ground truth, and where it is stated

`_fixture_site.py`'s `ground_truth()` computes every number below from the SAME source lists
(`NAVTREE_CANONICAL_PAGES`, `NAVTREE_V1_ONLY_PAGES`, `SITEMAP_BLOG_PAGES`, `SITEMAP_LEGAL_PAGES`,
`ROBOTS_DISALLOW_PATHS`, `ROBOTS_ALLOW_PATHS`, `ORPHAN_CHAIN`, `REVISIT_TEST_PAGE`,
`VERSION_DUP_TEST_PAGE`) that `_build_routes()` uses to generate the actual served pages — the
statement drives the pages, not the other way around. Every later milestone in this area gets
checked against these numbers, not against a live host, per the entry this one continues.

Seed URL: `seed_url(port)` = `http://127.0.0.1:<port>/docs/guide`, a `__NEXT_DATA__` page that is
itself both the literal seed and the default-version navtree root (mirroring the real
`docs.github.com/de/rest` case on record, where the seed and the tree's own root coincide).

| number | value | source |
|---|---|---|
| navtree total (via `navtree_feeder_workflow`) | 7 | `NAVTREE_CANONICAL_PAGES` (5) ∪ `NAVTREE_V1_ONLY_PAGES` (2), canonicalized by the version union |
| navtree version-exclusive (oldest-only) | 2 | `NAVTREE_V1_ONLY_PAGES` — present only in the v1 tree, absent from `v2`/`current` |
| sitemap-listed | 5 | `SITEMAP_BLOG_PAGES` (3) + `SITEMAP_LEGAL_PAGES` (2), reached through a TWO-level nested `<sitemapindex>` (`sitemap_index.xml` → `sitemap-docs-group.xml`, itself an index → two leaf `<urlset>`s) |
| robots-listed paths | 3 | `ROBOTS_DISALLOW_PATHS` (2) + `ROBOTS_ALLOW_PATHS` (1) — collected as seeds regardless of what they permit, the deliberate behavior this fixture lets happen rather than prevents |
| robots-listed, real vs. unfetchable | 2 real / 1 unfetchable | `ROBOTS_REAL_PATHS` vs. `ROBOTS_EMPTY_404_PATHS` (`/internal/staging-notes`) |
| orphans (link-only, absent from every feeder) | 2 | `ORPHAN_CHAIN` — a 2-hop chain, proving traversal beyond depth 1 |
| total `discover_urls_workflow` URLs (fresh `/_control/reset`, default depth/budget) | 20 | `ground_truth()["total_urls"]` = 15 pre-traversal seeds (1 seed + 3 robots + 5 sitemap + 6 navtree, the navtree root deduping against the literal seed under first-write-wins) + 5 traversal-only pages (2 orphans + the two test pages below + the version-duplicate URL) |
| expected `pages_fetched` / `pages_failed` | 19 / 1 | every page is real content except the one empty-body 404 |
| expected `stop_reason` | `"frontier_exhausted"` | `max_pages = max(500, 15*2) = 500`, never binding against 20 real URLs |

Verified directly, not just asserted: a real `discover_urls_workflow(seed_url(port))` run against
a freshly-reset fixture matched every one of these numbers exactly on the first attempt —
`ok=True`, `stop_reason="frontier_exhausted"`, `pages_fetched=19`, `pages_failed=1`,
`by_source={'seed':1,'robots':3,'sitemap':5,'navtree_tree':6,'traversal':5}`, total 20 URLs, the
one `fetched=False` entry being exactly `/internal/staging-notes`. No discrepancy to explain away.

An isolated `/rsc-demo` page (+2 children) exists to exercise the OTHER navtree payload shape
(`self.__next_f.push` RSC stream) directly via `navtree_feeder_workflow` — deliberately never
linked from the main graph and deliberately NOT counted in `total_urls`, since a real
`discover_urls_workflow` run only ever calls the navtree feeder once, against the main site's
`__NEXT_DATA__` shape. `navtree_feeder_workflow` against it returned 2 URLs,
`source="navtree_tree"`, confirming the RSC extractor path independently of the main site.

## A crawl4ai finding that shaped the failure-mode design, not written down anywhere before

Read `venv/.../crawl4ai/async_webcrawler.py` and `antibot_detector.py` directly (the same standard
this area already holds itself to) while designing the "genuinely unfetchable seed" case.
**`crawl_result.success = bool(html)` is set unconditionally, before any anti-bot check runs — an
ordinary HTTP 404 with a real, non-empty body reads as `success=True`.** Only four things force
`success=False`: `status_code==429` (unconditional), `status_code in (403, 503)` (content-checked,
near-empty or pattern-matched), or the Tier-3 structural-integrity check (thin/malformed body,
independent of status code, the same mechanism the thin-body failure mode uses). A plain 404 with
BaseHTTPRequestHandler's own small default error page (`<h1>Error response</h1><p>Error code:
404</p>...`) would have `visible_len` comfortably over the 50-char threshold and would contain a
`<p>`/`<h1>` — zero structural signals, `success=True` regardless of the 404 status.

This mattered directly: the fixture needed one robots-declared path whose own re-fetch genuinely
fails, to demonstrate `DiscoveredURL.fetched=False` on a real seed without relying on either
switchable failure mode. An ordinary 404 would have silently produced `fetched=True` instead,
defeating the demonstration. `ROBOTS_EMPTY_404_PATHS` (`/internal/staging-notes`) is therefore a
404 with a literally EMPTY body (`Content-Length: 0`) — `bool("")` is `False`, so `success=False`
is set before the anti-bot layer is even reached. Confirmed directly: `_pre_traversal_seeds()`'s
robots-derived seed for this path shows up in a real run as `source="robots", fetched=False`, the
only such entry.

The same reading also confirmed the thin-body failure mode's exact trigger shape: a page under
5000 bytes needs 2+ of {`minimal_text` (< 50 visible chars after stripping tags), `no_content_elements`
(zero `p`/`h1-6`/`article`/`section`/`li`/`td`/`a`/`pre` anywhere), `script_heavy_shell`} to be
flagged. `THIN_BODY_HTML = '<html><body><div id="app"></div></body></html>'` (~46 bytes) hits both
`minimal_text` and `no_content_elements` — confirmed live: `is_blocked(200, THIN_BODY_HTML)` →
`(True, "Near-empty content (46 bytes) with HTTP 200")`, matching the real 168-byte case already on
record from the `docs.github.com` benchmark. Every OTHER page this fixture serves deliberately
carries a real `<h1>`+`<p>` sentence for the opposite reason, confirmed via
`is_blocked(200, <normal fixture page>)` → `(False, "")` on the same read.

## Two cases added beyond the original design, each carrying a Gotcha already on record

The original design (leaf pages plus a plain 2-hop orphan chain) proved reachability but had no
page that ever links BACK to a URL a feeder already produced — so it could not exercise either of
two behaviors `src/crawler/DOCS.md`'s own Gotchas already document as found by a real run, not by
design review. Two pages were added specifically to make each one observable:

- **`REVISIT_TEST_PAGE` (`/docs/guide/related-links`) links to `REVISIT_TEST_TARGET`
  (`/blog/post-1`, already delivered by the sitemap feeder).** This is `_build_resume_state`'s
  `"visited"` pre-population — ALREADY fixed, already shipped — which stops the traversal from
  spending page budget rediscovering a seed it already has and from undercounting genuine
  traversal-only contribution (the real bug this fixed: an early `ui.shadcn.com/docs` run showed 0
  traversal contribution where some was plausible, traced to `link_discovery` not recognizing an
  already-known seed rediscovered as a link). The fixture's own real run confirms the fix still
  holds: `/blog/post-1` stays `source="sitemap", fetched=True`, not re-tagged `"traversal"`, not
  fetched twice. Kept as a plain root-relative path with no query string deliberately — the
  existing Gotcha notes the `"visited"` comparison mixes two different URL normalizers (this
  project's own vs. crawl4ai's `normalize_url_for_deep_crawl`) that only coincide for simple paths;
  this case is exactly that simple case, not a stress test of the mismatch itself.

- **`VERSION_DUP_TEST_PAGE` (`/docs/guide/see-versions`) links to `VERSION_DUP_TARGET`
  (`/docs/v1/guide/intro`), the explicit-version form of the already-delivered canonical
  `/docs/guide/intro`.** This is the OPEN, deliberately UNFIXED item: `discovery.py`'s traversal
  never runs a discovered link through `seed_feeders_navtree.py`'s own version-canonicalization
  (`_canonicalize_version_url`), because that canonicalization lives inside the navtree feeder and
  nothing exposes the version-key list to the traversal side of the module boundary. Under the
  current code, the fixture's own real run confirms this duplicate counts as a genuinely new
  `source="traversal", fetched=True` entry, distinct from the already-known canonical
  `/docs/guide/intro` — even though it is the same page. This is recorded here as the BEFORE
  number: `ground_truth()["version_duplicate_test"]` states this expected-current-unfixed shape
  explicitly, so whichever future milestone closes this gap (a shared lookup surfaced through
  `FeederResult`? re-detection during traversal? — still an open design question, not decided by
  this entry) has a real, reproducible number to show change against, instead of having to
  re-derive one from a live site first.

## Verification

Direct calls against a running fixture (`start_fixture_server()`/`stop_fixture_server()`, no
subprocess): `robots_feeder_workflow`, `sitemap_feeder_workflow`, and `navtree_feeder_workflow`
(twice — the main site and the isolated `/rsc-demo`) each returned exactly the stated lists. Both
failure modes demonstrated directly against `crawl4ai.antibot_detector.is_blocked`: 429-after-2
(`/_control/rate_limit?after=2`) → requests 1–2 succeed, 3–4 return 429, `is_blocked(429, "")` →
blocked; thin-body (`/_control/thin_body?on=true`) → `is_blocked(200, <46-byte body>)` → blocked;
both reset cleanly via `/_control/reset`. One real, full `discover_urls_workflow` run matched the
ground-truth table above exactly, field for field — reported above, not repeated here as a second
claim. Full suite: `./venv/bin/python3 -m pytest` → 364 passed, 0 regressions (no `src/` file and
no existing test was touched).
