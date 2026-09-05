# dev/url_discovery/

## Role
Two independent tools for the link-graph-traversal redesign of the capture pipeline's
URL-discovery step (`src/crawler/discovery.py` + its three seed feeders): (1) execution-verified
probes of `crawl4ai`'s deep-crawling internals against a REAL site (`01_resume_state_probe.py`) —
touch this when a new assumption about frontier pre-seeding/filter/scorer/resume-state shape needs
to be checked by running it, not by re-reading the vendored source; (2) a deterministic LOCAL
fixture site (`_fixture_site.py`/`02_fixture_site_server.py`) whose page inventory is a fact stated
in code, replacing a live host as the thing `discover_urls_workflow`'s feeders/traversal get
checked against — see
`process-docs/url_discovery/2026-08-28_validation_against_live_sites_was_the_wrong_unit.md` for why
live-site verification stopped being trustworthy. Not the place for the seed-feeder implementations
themselves or a discovery CLI — those belong under `src/` once a design is confirmed.

## Public Interface
No `__init__.py`. Two standalone entry points, run directly:
`./venv/bin/python dev/url_discovery/01_resume_state_probe.py` (live-site probe) and
`./venv/bin/python3 dev/url_discovery/02_fixture_site_server.py [--port N]` (fixture server,
Ctrl+C to stop). `_fixture_site.py` is also imported directly by any future dev script/test that
needs a deterministic discovery target: `start_fixture_server()`/`stop_fixture_server()`/
`ground_truth()`/`seed_url()`.

## Flow
`01_resume_state_probe.py`: fixed set of real `books.toscrape.com` URLs → four small
`BFSDeepCrawlStrategy` runs against one shared `AsyncWebCrawler` → one timestamped report under
`md/`. `_fixture_site.py`/`02_fixture_site_server.py`: source lists of page paths (navtree
versions, sitemap entries, robots paths, orphans) → generated HTML/XML routes served by a
`ThreadingHTTPServer` → a caller (a real `discover_urls_workflow` run, or a feeder called directly)
gets checked against `ground_truth()`, computed from those same source lists.

## Modules

### 01_resume_state_probe.py (280 LOC)

**Purpose:** Verifies, by running it, whether `BFSDeepCrawlStrategy(resume_state=...)` can
pre-populate the BFS frontier with an arbitrary URL set instead of a single `start_url` — and, if
so, the exact `resume_state` dict shape, `start_url`'s fate, depth bookkeeping against `max_depth`,
and whether injected URLs bypass the `FilterChain` the way a depth-0 seed does.
**Reads:** nothing on disk; fetches live pages from `books.toscrape.com` via `crawl4ai`.
**Writes:** `md/01_resume_state_probe_report_<ts>.md` (one per run, never overwritten).
**Called by:** run directly, ad hoc, when the pre-seeding assumption needs re-verifying (e.g.
after a `crawl4ai` version bump).
**Calls out:** `crawl4ai` (`AsyncWebCrawler`, `BrowserConfig`, `CrawlerRunConfig`, `CacheMode`,
`crawl4ai.deep_crawling.BFSDeepCrawlStrategy`/`FilterChain`/`URLPatternFilter`).

---

### _fixture_site.py (487 LOC)

**Purpose:** Deterministic local HTTP fixture for `src/crawler/discovery.py`'s three seed feeders
and its BFS traversal — a documentation site with a nested `<sitemapindex>`, a `robots.txt`
carrying `Allow`/`Disallow`/`Sitemap`, a 3-version `__NEXT_DATA__` navtree (2 pages exclusive to
the oldest version), an isolated RSC (`self.__next_f.push`) demo page, link-only orphan pages, and
two switchable failure modes: thin-body-200 (on/off), and a genuine SLIDING-WINDOW 429
(`/_control/rate_limit?limit=M&window=T` — "at most M requests in the trailing T seconds",
recoverable once a caller slows down, not an absolute counter that trips once and never recovers).
`ground_truth()` states total/orphan/
version-exclusive/sitemap-listed/robots-listed counts (plus `pre_traversal_seed_count`, the size of
the single BFS level every pre-traversal seed is injected into — the real ceiling a small
`max_pages` override lands on), computed from the same source lists that generate the served pages.
**Reads:** nothing on disk — ground truth is stated as source lists in this file itself.
**Writes:** nothing (in-memory HTTP responses only).
**Called by:** `02_fixture_site_server.py` (standalone use); any future dev script/test needing a
deterministic discovery target.
**Calls out:** stdlib only (`http.server`, `threading`, `json`, `urllib.parse`) — no
`crawl4ai`/`httpx` dependency, since this module is a target, never a client.

### 02_fixture_site_server.py (45 LOC)

**Purpose:** Standalone entry point — starts `_fixture_site.py` on a fixed/given port, prints its
seed URL + `ground_truth()`, blocks until Ctrl+C, then shuts it down cleanly.
**Reads:** nothing on disk.
**Writes:** stdout/stderr only (the startup banner).
**Called by:** run directly, ad hoc: `./venv/bin/python3 dev/url_discovery/02_fixture_site_server.py [--port N]`.
**Calls out:** `_fixture_site.py` (same directory, `sys.path`-inserted import, matching
`dev/browser_posture/_lib.py`'s own convention).

---

## State
`01_resume_state_probe.py`: no persistent state of its own — each run's `md/` report is a dated,
standalone snapshot, nothing resumed or accumulated across runs. `_fixture_site.py`: `_ROUTES`
(built fresh per `start_fixture_server()` call) and `_STATE` (request counter + the two
failure-mode flags, mutated only via `/_control/*` and read under `_STATE_LOCK`) are both
module-level — see the Gotcha below on the one-instance-per-process consequence of that.

## Gotchas
- **The 429 failure mode is a sliding window (`rate_limit_limit`/`rate_limit_window_s` +
  `_REQUEST_TIMESTAMPS`), not an absolute counter — this replaced an earlier `rate_limit_after=N`
  shape that could NOT distinguish a well-paced caller from a badly-paced one.** Both eventually
  send N total requests and both tripped the old counter identically, with no way back — the exact
  property this fixture exists to let a caller measure (process-docs/url_discovery/
  2026-09-05_pacing_measurement.md). The window is pruned lazily on every request check
  (`_REQUEST_TIMESTAMPS[0] < now - window` popped before counting), guarded by the same
  `_STATE_LOCK` every other piece of shared state uses — no separate lock, no separate race.
- **`_fixture_site.py`'s `_ROUTES`/`_STATE` are module-level globals, not per-instance — only ONE
  fixture server is meant to run per process at a time.** A second `start_fixture_server()` call in
  the same process overwrites the first's routes/state (the first server keeps serving on its own
  port, but against the second's route table). Tests/scripts that need genuine isolation should run
  in separate processes, not just separate threads.
- **A plain HTTP 404 with a real (non-empty) body does NOT read as a failed fetch to crawl4ai —
  confirmed by reading `async_webcrawler.py`/`antibot_detector.py` directly, not assumed.**
  `crawl_result.success = bool(html)` is set before any anti-bot check runs; only `status_code==429`
  (unconditional), `403`/`503` (content-checked), or a genuinely thin/malformed body (the Tier-3
  structural check, independent of status code) force `success=False`. This is why
  `ROBOTS_EMPTY_404_PATHS` (`/internal/staging-notes`) is a genuine EMPTY-body 404, not an ordinary
  one with a small default error page — an ordinary 404 page would still be `fetched=True` in a
  real `discover_urls_workflow` run, which would silently defeat the one case this fixture needs to
  demonstrate a robots-declared seed's own re-fetch genuinely failing.
- **`THIN_BODY_HTML`'s exact shape (`<div id="app"></div>`, no `p`/`h1`/etc.) is deliberate, not
  arbitrary minification.** `antibot_detector._structural_integrity_check` needs 2+ signals to
  block a page this small (`<5000` bytes): 0 visible chars after stripping tags (`minimal_text`)
  AND 0 of `p/h1-6/article/section/li/td/a/pre` anywhere in the html (`no_content_elements`). Every
  other page this fixture serves deliberately carries a real `<h1>`+`<p>` sentence for the opposite
  reason — to never accidentally trip this same check on the "normal" ground-truth run.
- **`/rsc-demo` and its two children are deliberately never linked from the main site graph, and
  are NOT counted in `ground_truth()`'s `total_urls`.** They exist solely so
  `navtree_feeder_workflow` can be called directly against the RSC (`self.__next_f.push`) shape,
  since a real `discover_urls_workflow` run only ever calls the navtree feeder once, against the
  main site's `__NEXT_DATA__` shape. Wiring `/rsc-demo` into the main graph would change
  `total_urls` and conflate two independent purposes (shape-detection demo vs. the site's own
  ground truth) — do not link it in.
- **`VERSION_DUP_TEST_PAGE`'s link to `VERSION_DUP_TARGET` (`/docs/v1/guide/intro`) now closes the
  version-canonicalization gap `src/crawler/DOCS.md`'s Gotchas used to record as open.**
  `discovery.py`'s traversal recognizes this URL, after genuinely fetching it, as an
  explicit-version duplicate of the already-known canonical `/docs/guide/intro` —
  `DiscoveredURL.canonical_url` is set on the duplicate's own entry, which still appears in the
  result with its own real `source`/`fetched` status (the fetch still happens; this closes the
  MISCLASSIFICATION gap, not the fetch cost — see `src/crawler/DOCS.md`'s Gotchas for the
  annotation-vs-prevention tradeoff argued there). The canonical entry itself is never touched.
  `ground_truth()`'s `version_duplicate_test.expected_behavior` states this explicitly.
  `total_urls`/`by_source` do NOT change from this fix — the duplicate was already counted as its
  own entry before, only its shape changes now.
- **`REVISIT_TEST_PAGE`'s link to `REVISIT_TEST_TARGET` (`/blog/post-1`, already delivered by the
  sitemap feeder) is the opposite case: already-fixed, already-shipped behavior.**
  `_build_resume_state`'s `"visited"` pre-population (see `src/crawler/DOCS.md`'s Gotchas) means
  this rediscovery should NOT be re-fetched and should NOT be re-tagged `"traversal"` — a real
  `discover_urls_workflow` run against this fixture confirmed `/blog/post-1` stays
  `source="sitemap"`, fetched exactly once. Kept as a simple root-relative path with no query
  string deliberately — the DOCS.md Gotcha on this fix notes the "visited" comparison uses TWO
  different URL normalizers (this project's own vs. crawl4ai's `normalize_url_for_deep_crawl`) that
  are only guaranteed to coincide for simple paths; this fixture's own test case is exactly that
  simple case, not a stress test of the normalization-mismatch edge itself.
- Each of the four `01_resume_state_probe.py` experiments cancels its `BFSDeepCrawlStrategy` from inside its own
  `on_state_change` callback right after the single seed URL's first BFS level is processed —
  the discovered next-level URLs are inspected via the captured state dict, never actually
  fetched. This keeps every run to a handful of real requests; it also means `results` lists in
  the report only ever contain the directly-injected seed(s), not their children.
- `resume_state={}` (empty dict) is FALSY in Python, so `BFSDeepCrawlStrategy` silently takes the
  non-resume branch and crawls `start_url` normally instead of entering "zero pending URLs" resume
  mode — confirmed in Experiment 2c. A caller that constructs an empty dict on an empty-seed-list
  path will get a silent single-URL fallback, not an empty crawl and not an error.
- A wrong key in a non-empty `resume_state` (e.g. `"seed_urls"` instead of `"pending"`) fails
  silently too: the dict is truthy so resume mode IS entered, but `.get("pending", [])` finds
  nothing, `current_level` is empty, and `start_url` is never used either — the crawl produces
  zero results with no exception raised (Experiment 2b).
- Experiment 3's `children_discovered_count` reads `holder.get("state", {}).get("pending", [])`
  — a plain `.get()` chain with a `0`-shaped default at every level. `on_state_change` does fire
  whenever `result.success` is `True` regardless of what `link_discovery` found (confirmed by
  reading `_arun_batch`), and both variants' seed fetches did succeed, so the `0` reported for
  Variant A is a genuine "zero children" measurement here, not an artifact of a callback that
  never ran. But the code has no assertion that `"state" in holder` before reading the count, so
  the same pattern reused against a failing seed fetch would silently report `0` for the wrong
  reason. A stricter version would assert `"state" in holder` before trusting the count.
