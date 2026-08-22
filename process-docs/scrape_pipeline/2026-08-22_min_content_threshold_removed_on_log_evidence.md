# MIN_CONTENT_THRESHOLD + fit→raw fallback removed, on operational-log evidence (2026-08-22)

Removes the `fit_markdown`→`raw_markdown` selection fallback (`MIN_CONTENT_THRESHOLD=200`) from
`src/scraper/scrape_url.py`'s `_acquire_scrape`. Content is now `fit_markdown` unconditionally. The
threshold was one of two remaining ungrounded config values on the ad-hoc chromium lane (the other,
the `COOKIE_CONSENT_SELECTOR` list, is out of scope here). This continues the content-selection
lineage of this area's `content_judgment_removal_2026-08-05.md` — that removal deliberately KEPT the
fit/raw fallback as "selection between two crawl4ai candidates, not a verdict"; this entry retires it
too, on evidence the earlier one did not have.

## What the value was, and its thin origin

The rule: in `_acquire_scrape`, if `len(fit_markdown) < 200` and `raw_markdown` is non-empty, return
`raw_markdown` instead of `fit_markdown` (stamped `meta["fallback_to_raw"]`). Not a discard/verdict —
a selection between the PruningContentFilter-filtered output and the unfiltered one. Origin was a
2026-03 session anecdote (`scrape_pipeline.md` Session findings): fit_markdown over-filters short API
docs / one-pagers, raw saves them. Never a measured figure — 200 was set as a baseline "safety" with
no derivation.

## The operational-log analysis that settled it

Read `src/logs/scrape_log.jsonl` (the accumulating per-URL prod log, the project's own
"log-before-config-change" calibration surface), 74 records, 69 on the chromium lane. Findings:

- **The fallback fired exactly ONCE in 69 scrapes** — `praxis-am-marbachweg.de`, a degenerate page
  where BOTH `fit` and `raw` were ~1 byte. It swapped, but there was nothing to swap TO. Useless.
- **Zero non-fallback records sit in the 1-199 fit-byte band.** By construction: `fit < 200` with
  non-empty raw always triggers the fallback, so the only way to land in that band without it is a
  doubly-empty page (which is the degenerate case above). The threshold cleanly separates nothing in
  real data.
- **The one near-threshold case argues AGAINST raising it, not for.** `hornbach.de` category page:
  `fit=321`, `raw=2537` (7.9x). Fallback did not fire (fit > 200). A higher threshold would have
  flipped to raw and returned 8x more — but a category page's raw excess is link-chrome, exactly what
  `PruningContentFilter` exists to remove, and the 2026-05 sweep's asymmetric-preference frame
  (chrome retention worse than content loss) says returning it would be a regression, not a rescue.
- Bulk of the lane is nowhere near the boundary: 53 of 68 non-fallback records are ≥ 2000 bytes.

Net: at n=69 the mechanism never usefully engaged, its one firing was inert, and its one
near-boundary datapoint cuts against the direction the anecdote implied. No specific value is
groundable from this data — the honest conclusion is not "pick a better number" but "the mechanism
carries no measured benefit."

## Why removal, not re-grounding

The original 2026-03 concern (over-filtered short pages, specifically code-heavy API docs) is now
covered elsewhere: `preserve_tags=["pre","code"]` (added 2026-08-03, `pruning_filter_code_block_
guard_2026-08-03.md`) stops the filter destroying code blocks, the concrete way short technical pages
used to collapse. With that concern separately handled and the log showing zero useful firings,
keeping a baseless guard contradicts the standing premise that an unmotivated "safety" with no
concrete evidence gets removed. Consistent with the 2026-08-05 direction (this module reports facts,
does not decide what the agent may see) — the fallback was the last place the module silently
substituted one content candidate for another.

## What was kept, and what a future revisit would need

`meta["raw_markdown_bytes"]` / log's `bytes_raw_markdown` KEPT as a pure reported fact — raw markdown
size is a filter-ratio signal against `bytes_returned` (live example: an rfc-editor.org scrape,
540416 raw → 511762 filtered), independent of the now-gone selection. Config-stamp shape changed
(`min_content_threshold` dropped, `fallback_to_raw` dropped from the log record) — `config_hash` will
not group across the boundary, the same accepted trade-off as the 2026-08-05 `max_content_length`
drop. If over-filtering of a thin real page is ever observed in the accumulating log AFTER this
change, that observation — a concrete failing URL with a measurable filtered-vs-raw gap that is real
content, not chrome — would be the grounded basis a reintroduced mechanism needs, and did not have
before.
