# Ad-hoc lane's guessed outcome and guessed date removed (2026-09-06)

Applies the same fact-vs-verdict line drawn earlier the same day for `src/crawler/pipe_scraper*.py`
(`process-docs/scrape_pipeline/2026-09-06_pipe_scraper_outcome_removed.md`) to the ad-hoc single-URL
lane (`src/scraper/chromium_scrape.py`, `camoufox_scrape.py`, `scrape_logger.py`) — the two modules
that milestone explicitly left untouched as a separate, deferred task.

## Two removals, two different shapes

**`outcome`** (`meta.get("acquisition_error") or ("ok" if content else "empty")`, both engines) —
`ok`/`empty` were a pure re-derivation of `bytes_returned`, already logged; deleted outright, no new
field needed. `budget_exhausted`/`browser_missing`/`exception` were different: real facts about this
module's own code, previously visible ONLY through the collapsed `outcome` string — chromium's log
never had a bare `acquisition_error` field of its own before this. That fact was added to both
engines' log records FIRST (`"acquisition_error": meta.get("acquisition_error")`), then the
`outcome` branch was deleted, the same order the pipe path's own removal used. The sidecar header's
`outcome` line was worse than redundant: `write_sidecar` only runs when `content` is truthy, so
`acquisition_error` is structurally always `None` in that exact context — every one of the 405
`ok`-outcome sidecars on record read `"ok"` regardless of what had actually happened, carrying zero
information. Removed with no replacement line, since there is no fact to put there that isn't
already guaranteed constant.

**`published_date`/`date`** (`htmldate.find_date` guessing a publication date from raw HTML) — a
third-party guess about the remote page, not a fact about this module's own observation or
configuration. Real known failure on record (`src/scraper/DOCS.md`): a Trustpilot review page, a
page class with no publication date at all, was given today's date. Replaced with `og_published_time`,
read directly off `result.metadata["og:published_time"]` — a field crawl4ai's own
`content_scraping_strategy.py` already populates for every non-prefetch scrape
(`extract_metadata_using_lxml` collects every `og:`-prefixed `<head>` meta tag), verified by reading
that source directly before relying on it, not assumed. Null whenever the page declares no such tag.
`htmldate`, `HTMLDATE_TIMEOUT_S`, and `extract_date` are gone entirely, including from
`requirements.txt`; `TOTAL_SCRAPE_BUDGET_S` dropped by htmldate's own former `+3.0` summand
(245.8 → 242.8), since no separate date-extraction step runs anymore.

## The coverage question, measured honestly, not glossed over

The old `published_date`/`date` field's hit rate is on record: 273 of 409 production records
carried one. The new `og_published_time` field's hit rate is UNMEASURED — the 405 sidecars on disk
under `src/logs/scrape_content/` no longer carry the raw HTML `htmldate` parsed (sidecars store
converted markdown, not the source `<head>`), so the old corpus cannot be replayed against the new
extraction to get a real before/after number. The one live check this milestone ran (a real
`cli.py scrape_url_chromium` call against a github.blog article) returned `og_published_time: null`
— confirmed independently, by curling the same URL directly, that the page carries
`article:published_time` in its `<head>`, NOT `og:published_time`. `extract_metadata_using_lxml`
collects only `og:`-prefixed tags (plus `article:`-prefixed ones separately, under their own keys —
this milestone reads only the `og:` one, exactly as specified); a page using the `article:` namespace
instead reads null under this field, correctly, by construction.

**The two numbers are not comparable, and it would be dishonest to imply otherwise by placing them
side by side.** 273/409 measured how often a GUESS happened to land on something; a guess can be
"right" by chance, by coincidence with an unrelated last-modified footer, or by genuinely finding a
real date — the number does not distinguish those cases, which is exactly why the field was worth
removing regardless of its hit rate. Whatever `og_published_time`'s own real hit rate turns out to
be, it counts something categorically different: how often a page's own operator chose to publish
an Open Graph tag naming a date, using the specific `og:` vocabulary rather than the also-common
`article:` one. A lower hit rate is not a regression to fix; a higher one would not have been a
success to claim. Measuring `og_published_time`'s real coverage requires accumulating fresh
production records under the new schema — not attempted here, since the honest answer today is "not
yet measured," not a number invented to fill the gap.

## Verification

Full suite: 378 passed (was 367; 15 new tests added, 0 deleted — every touched test's subject still
existed and was rewritten in place, none tested only a removed mechanism outright). Real run against
a live github.blog article (chosen before its exact `<head>` shape was known, then independently
confirmed via `curl` afterward): agent-facing output rendered `og:published_time (...): None`
unconditionally inside the Acquisition facts block; the JSONL record carried `"acquisition_error":
null` and `"og_published_time": null`, no `"outcome"` key at all; the sidecar header carried
`url`/`ts`/`bytes`/`mode`/`engine` only, no `outcome` line.

## Callers fixed, not left broken

`dev/lane_choice/01_backfill_pairs.py` and `04_lane_metrics.py` both read `outcome` off the exact
production log this milestone changed. `01_backfill_pairs.py`'s own `fire_one_pair` would have
raised `KeyError: 'outcome'` on the very next fresh pair — fixed with a local `_derive_outcome()`
that reconstructs the identical three-way label (`acquisition_error`, or `"ok"`/`"empty"` from
`bytes_returned`) for this script's OWN reporting, a local dev-tool derivation, not a revival of the
production verdict. `04_lane_metrics.py`'s `_latest_ok_records_by_url_engine` filtered on
`record.get("outcome") != "ok"` — which would NOT have raised, only silently excluded every record
written after this removal (no `"outcome"` key at all makes the check permanently true), the exact
silent-data-loss shape this project's own standing philosophy warns against. Fixed to check
`acquisition_error`/`bytes_returned` directly, which reads identically on records from before and
after this removal. Both fixes and their reasoning are also recorded in `dev/lane_choice/DOCS.md`'s
own Gotchas.
