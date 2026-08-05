# Removed the stored same_target verdict; the landed-URL line is now unconditional (2026-08-14)

Reverses part of the design set by three preceding entries in this area:
`landed_url_comparison_primitive_2026-08-06.md` (built `is_same_target`), the milestone-2 wiring
entry that gave the ad-hoc path (`src/scraper/scrape_url.py`) a conditional acquisition-facts line
gated on that verdict, and the milestone-4 entry that gave the pipe path
(`src/crawler/pipe_scraper.py`) a tri-state version of the same stored field. Those entries stand
as written — this is a new, dated snapshot recording the reversal, not an edit to them.

## Why both stored verdicts were the wrong call

Two separate channels carry this information, and neither one needed a pre-computed conclusion:

- **The JSONL logs** (`scrape_log.jsonl`, `pipe_scrape_log.jsonl`) are read only by an agent,
  always after the fact, with the requested URL and `landed_url` already sitting in the same
  record. Storing `same_target` alongside them was a re-derivable conclusion kept as data — the
  agent can compare the two strings itself. The pipe log's tri-state design in particular was
  justified at the time on "the agent cannot reconstruct why a landed_url is missing" — that
  justification collapses on inspection: `crawl4ai_fallback_fetch_used` and `pipe_fallback_used`
  are in the very same record and say exactly which acquisition route ran and therefore why
  `landed_url` reads the way it does. Nothing about the route was actually unreconstructable.
- **The ad-hoc path's rendered acquisition-facts block** is the other channel — read live, during
  a production run, not after the fact from a log. Every other line in that block (HTTP status,
  byte counts, crawl4ai's diagnosis) is unconditional; the landed-URL line was the ONE place where
  this module's own code decided whether the agent gets to see a fact, gated on whether
  `is_same_target` said it differed. That is exactly the class of decision the 2026-08-05
  content-judgment removal was written to eliminate — this milestone closes the one instance of it
  the landed-URL work itself had reintroduced.

Both channels needed the same thing: the two raw URLs, unconditionally, nothing decided on the
agent's behalf. Neither needed a verdict.

## What changed, concretely

Deleted entirely from `src/scraper/scrape_url.py`: `is_same_target`, `_normalize_percent_encoding`,
`_normalize_host`, `_normalize_path`, `_DEFAULT_PORTS`, `_UNRESERVED_CHARS`, `_PERCENT_ENCODED_RE`
— confirmed via a full-repo grep before deleting that nothing outside this module and
`pipe_scraper.py` (which only imported the function, never redefined it) referenced any of them.
`same_target` removed from both log schemas and from every call site in both scraper modules.
`landed_url` itself untouched everywhere, on every route, including every route that writes it
null — those nulls (crawl4ai's own fallback route hardcoding `redirected_url` to the requested URL;
a curl_cffi fetch that never completed) are still correct and their reasoning still lives in both
schema comments, unchanged in substance.

The ad-hoc acquisition-facts line became unconditional: `- Landed URL (the URL the browser actually
returned content from): <url>`, rendered on every scrape, wording deliberately clear of any
"redirected"/"different target" language since nothing decides that anymore. An absent landed URL
renders the line with a literal `None` — matching the block's own existing convention for other
absent facts (e.g. HTTP status on a `budget_exhausted` record) rather than inventing new phrasing
for this one case.

Both retired `same_target` fields got a narrow-window historical note, not a one-directional one:
ABSENT before the field was introduced, PRESENT on records written while each scraper still
computed the verdict, ABSENT again from this change onward — a reader crossing either boundary
needs that middle state named, not just "field added" or "field removed" in isolation.

## The comparison rule did not disappear — it moved

`skills/websearch-web-research/SKILL.md` was updated separately, outside this worktree, so the
calling agent now compares the requested and landed URLs itself and flags a real target difference
to the user directly. The rule this milestone removed from code is the same rule, relocated to
where it belongs: a judgment made by the agent reading the two facts, not a conclusion pre-computed
and handed to it.

## Verification

Test count dropped from 175 to 148 (27 fewer) — entirely accounted for by the 26 deleted
parametrized `is_same_target` cases (11 spelling-equivalence + 5 real-difference + 5
missing-input + 5 malformed-URL) plus one now-meaningless `_format_scrape_output`
spelling-difference test; no other test was removed, several were renamed/rewritten in place with
the same assertion count. Full suite: `9 failed, 148 passed`, `FAILED` list diffed against the
standing baseline (7 `test_query_logger.py` + 2 `test_proxy_pool.py`) — identical, no drift.

Real CLI runs on both paths, both URLs and JSONL records inspected directly: ad-hoc against a
redirecting URL (`docs.anthropic.com/en/api/getting-started` → `platform.claude.com/docs/en/api/
overview`, HTTP 301) and a non-redirecting one (`rfc-editor.org/info/rfc2616/`, HTTP 200) — the
line rendered unconditionally in both, `same_target` confirmed absent from both written records.
Pipe path against 4 URLs including the confirmed 302 (`rfc-editor.org/rfc/rfc2616` →
`rfc-editor.org/info/rfc2616/`) — `landed_url` correct on every record, `same_target` absent from
all four.
