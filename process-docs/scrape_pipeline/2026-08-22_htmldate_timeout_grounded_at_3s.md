# HTMLDATE_TIMEOUT_S grounded from gut-5.0 to 3.0 on library internals (2026-08-22)

Re-grounds `HTMLDATE_TIMEOUT_S` in `src/scraper/scrape_url.py` from `5.0` (an ungrounded early "safety"
value) to `3.0`, and rebooks both acquisition budgets by the −2.0s knock-on
(`TOTAL_SCRAPE_BUDGET_CDP_S` 247.8→245.8, `TOTAL_SCRAPE_BUDGET_HEADLESS_S` 221.3→219.3). Third and
last of the ad-hoc chromium lane's ungrounded-value cleanups this day (after `MIN_CONTENT_THRESHOLD`
and `COOKIE_CONSENT_SELECTOR` in this area's two other 2026-08-22 entries). Cross-references
`process-docs/time_budget/`'s R-rules for the budget composition.

## What the 5.0 guarded, and why it was ungrounded

`extract_date` wraps `htmldate.find_date` in `asyncio.wait_for(asyncio.to_thread(find_date, ...),
timeout=HTMLDATE_TIMEOUT_S)`. The guard exists because the date is an OPTIONAL field and `find_date`'s
extensive mode invokes `dateparser` (flagged slow in htmldate's own source) — a hang there must never
stall or fail the scrape; on any timeout/exception the date degrades to `None` and full content still
returns. The 5.0s height itself had no derivation — the `time_budget` entry carried it as "this
project's own pre-existing guard, passes R6," i.e. inherited, not reasoned.

## Why own measurement was rejected as the grounding method (user's own point)

A dev probe timing `find_date` over a sample of URLs was considered and dropped: it would measure THOSE
pages' parse time, not the worst case for the next unknown page — the same single-sample confound this
project rejects everywhere (calibration comes from external sources, never own sweeps). The grounding
had to come from the libraries themselves.

## External grounding (GitHub source + issue tracker, orchestrator-side research)

- **htmldate exposes no per-call timeout.** `find_date`'s signature (adbar/htmldate `core.py`) is
  `(htmlobject, extensive_search=True, original_date=False, ...)` — no deadline/timeout param. So there
  is no library-level bound to defer to; an external wrapper guard is NECESSARY, which grounds the
  guard's EXISTENCE (not a stylistic choice).
- **htmldate bounds its own work internally.** `settings.py`: `MAX_POSSIBLE_CANDIDATES=1000` (cap on
  date candidates), segment length 6–52 chars, `CACHE_SIZE=8192` (lru_cache on parses),
  `MAX_FILE_SIZE=20MB`. So `find_date` is structurally bounded — at most ~1000 dateparser calls on
  short, cached strings — not an open-ended parse.
- **dateparser's own worst documented realistic pathology is ~3s per call**, and that was a since-fixed
  bug: scrapinghub/dateparser#457 (a locale-accumulation leak in long-running processes pushing per-call
  time from hundreds of ms to ~3s). Normal calls are ms-range; most dateparser cost is one-time import
  (~0.3–0.6s, #253/#1051), not per-call. dateparser also exposes no per-call timeout.

## The value: 3.0, and its accepted trade-off

3.0 sits at the documented pathology edge (dateparser's ~3s worst case) and far above normal
sub-second completion — bounding a true hang without a magic number. The operational log corroborated
that the guard almost never bites: 67 of 68 ad-hoc `ok` scrapes carried a `published_date`, none near
the old 5.0s cap (the single date-less record was a genuinely date-less page, not a timeout). User
decision: set 3.0 rather than keep 5.0 or split the difference — the exact height is operationally
near-irrelevant (it only fires on a hang), so the tighter figure at the documented edge is the cleaner
grounded choice. Accepted trade-off, stated in the code comment: a legitimately slow 3–5s extraction
now loses the (optional) date rather than extending the budget — acceptable given the field is optional
and normal completion is fast.

## Note on the deeper lever (recorded, not acted on)

The genuinely doc-grounded lever over the whole slow path is the extensive-vs-fast mode choice
(`2026-08-02_publication_date_at_scrape_time.md`): fast mode drops dateparser entirely, eliminating the
hang class the guard protects against, at a recall cost (0.993→0.927 on htmldate's own benchmark). That
decision stands (extensive kept for recall); the 3.0s guard is the insurance for keeping it. Not
revisited here.
