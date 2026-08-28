# dev/url_discovery/

## Role
Execution-verified probes for the link-graph-traversal redesign of the capture pipeline's
URL-discovery step (robots.txt/sitemaps/framework-nav feeding seed URLs into a traversal frontier
before crawl4ai's `BFSDeepCrawlStrategy` runs). Touch this directory when a new assumption about
`crawl4ai`'s deep-crawling internals (frontier pre-seeding, filter/scorer behavior, resume/state
shape) needs to be checked by RUNNING it against a real site, not by re-reading the vendored
source. Not the place for the seed-feeder implementations themselves or a discovery CLI — those
belong under `src/` once the design is confirmed.

## Public Interface
No `__init__.py` — the script is a standalone entry point, run directly:
`./venv/bin/python dev/url_discovery/01_resume_state_probe.py`.

## Flow
Fixed set of real `books.toscrape.com` URLs (static, stable, low volume) → four small
`BFSDeepCrawlStrategy` runs against one shared `AsyncWebCrawler`, each isolated to a handful of
real requests via `max_depth`/an `on_state_change` callback that cancels the strategy right after
the first BFS level → measured results (which URLs got fetched, what depth/filter state resulted)
→ one timestamped report under `md/`.

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

## State
No persistent state of its own. Each run's `md/` report is a dated, standalone snapshot; nothing
here is resumed or accumulated across runs.

## Gotchas
- Each of the four experiments cancels its `BFSDeepCrawlStrategy` from inside its own
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
