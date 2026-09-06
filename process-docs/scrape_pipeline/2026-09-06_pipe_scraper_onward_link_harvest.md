# pipe_scraper collects onward links from pages it already fetches (2026-09-06)

Closes the gap `process-docs/url_discovery/2026-09-06_traversal_removal.md` opened on the same day:
a browser-driven link traversal used to live in `discovery.py`, re-fetching every already-discovered
URL a second time purely to read its links, and was removed as a duplicate fetch. That traversal's
actual job — surfacing pages that nothing but another page's body links to, since discovery's own
feeders (robots.txt, sitemap, framework navigation tree) cannot see those — needed a new home. This
milestone puts it on pages `pipe_scraper.py` is fetching anyway, at zero extra fetch cost.

## Where the links come from, and the two calls made on purpose

`_scrape_one`'s success path already holds a full `crawl4ai` `CrawlResult` for every scraped page,
including `result.links` (`{"internal": [...], "external": [...]}`, hrefs already resolved to
absolute URLs — confirmed by reading `content_scraping_strategy.py` directly, not assumed, since
this is the real non-prefetch path `pipe_scraper` uses, not the cruder `quick_extract_links`
prefetch shortcut). Two design calls, both made deliberately rather than defaulted into:

- **Union crawl4ai's own `"internal"`/`"external"` buckets instead of trusting either.** That split
  is crawl4ai's own classification, already distrusted for scope once in this project — the
  now-removed `discovery.py` traversal built `_ExactHostFilter` specifically because crawl4ai's own
  internal/external split (in the DIFFERENT prefetch code path it used) was a crude same-page-netloc
  substring check. This module's own scraping path uses a more sophisticated `is_external_url`/
  `get_base_domain` check internally, but its exact semantics (subdomain-family vs. exact host) are
  a vendor implementation detail this project does not control or want to depend on for something
  it cares about being exactly right. Unioning both buckets and applying this project's own
  `host_key` comparison (`seed_feeders_scope.py`) keeps the scope decision in this codebase's own
  hands, consistent with the precedent the removed traversal already set.
- **Return `None`, not `[]`, when the engine cannot collect links at all.** `try_scrape_camoufox`
  returns content and metadata, no link set — `_scrape_one_camoufox`'s return dict never gets a
  `'links'` key at all (absent, not empty), `_collect_onward_links` returns `None` for
  `engine == "camoufox"` regardless of what any individual result happens to carry, and both
  `_print_summary` and `_write_onward_links_file` treat `None` specially (an explicit "not
  collected" string on the console, no file written at all) rather than a bare `0`/empty file a
  caller could mistake for "chromium looked and found nothing." The same shape this project already
  uses for "camoufox record does not carry chromium-only fields at all" (`pipe_scraper_records.py`)
  extended to a capability distinction, not just a field-presence one.

## The measurement that shaped the normalization

A real 50-page hand-check of `platform.claude.com` found 224 distinct on-host links, 174 not in the
50-page input, 57 of those genuinely unknown against the domain's own full 3571-URL discovery list
— and 54 of those 57 worthless. All 54 traced to exactly two failure shapes: 50 were the SAME
`/login` page linked from page navigation, one per scraped source page, each carrying a different
`returnTo=` query string that a plain string-dedup could not collapse; 3 were the SAME `/playground`
page differing only by a `model=` query; 1 was a `.gif`.

This directly overruled reusing `seed_feeders_scope.normalize_url` as-is: that function keeps the
query string on purpose, because its own worst case for merging two URLs is a seed that is never
fetched at all. This file's worst case inverts — it is a supplementary, non-authoritative candidate
list for a follow-up scrape round, never the sole record of a page's existence — and the measured
noise showed the query string was exactly where the false-positive "new pages" lived.
`_onward_link_identity` therefore drops the query string and fragment entirely (scheme/host
lowercased, the rest of the identity untouched), and `_NON_PAGE_EXTENSIONS` (a small, evidence-based
blocklist — image/style/script/font/document/media extensions) drops the one asset-link shape found.

## What pipe_scraper does NOT try to know

`_collect_onward_links` excludes a discovered link only against the RUN'S OWN input `urls` list —
never against `discovery.py`'s full discovery output, which is not, and structurally cannot be,
passed into `pipe_scraper` at all (the two tools are invoked independently, at different pipeline
steps, by an agent that holds both file paths, not by one tool calling the other). A link that
happens to already be on the full discovery list but wasn't part of this particular batch's own
input still appears in the onward-links file — confirmed in the verification run below (`/playground`
collapsed to one entry in the 122-line output, and IS already a known discovery-list URL, so it
correctly drops out of the "not in the full discovery list" count without pipe_scraper needing to
know that fact at all). Cross-referencing the onward-links file against a broader known-URL set, if
wanted, stays the calling agent's own job, done externally — exactly how the verification numbers
below were produced, with a plain `comm -23` between two files, not a new dependency wired into
`pipe_scraper` itself.

Also deliberately out of scope: `_own_fallback_rescue`'s successful `raw:<html>` conversion (path b)
produces its own `CrawlResult` with a `.links` attribute too, but its links are not extracted. The
`raw:` pseudo-URL has no real netloc for relative-href resolution to resolve against, and verifying
whether crawl4ai handles that case sensibly was not done — this milestone's own motivating framing
was specifically about the NORMAL, already-in-hand browser result, not the rescue path.

## Verification

Full suite: 367 passed (was 346 before this milestone's 21 new tests). Real run against
`/tmp/platform_claude_com_urls_culled.txt` (the same 50-URL input the hand-check used) to a fresh
output dir: console line `Scraped 50 URLs in 52s — status: 200=50 — 0 returned 0 bytes — 122 onward
links collected`. Subtracting `/tmp/platform_claude_com_urls.txt` (the domain's full 3571-URL
discovery list) from the 122-line onward-links file via `comm -23` left exactly 4 lines: three real,
previously-unknown content pages (`prompt-engineering`, `release-notes/api`,
`release-notes/system-prompts`) and exactly one `/login` — the collapsed, deduplicated survivor of
the 50-variant noise source, not a leftover of it. Zero of the 54 named noise URLs survive verbatim;
their exact query-bearing forms no longer exist by construction. Independently reproduced by the
reviewer against the live files with the same 122/4 result, matching the pre-milestone hand-count.
