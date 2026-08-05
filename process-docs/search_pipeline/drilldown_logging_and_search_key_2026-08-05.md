# Drilldown logging + search_key correlation (2026-08-05)

Closed a gap in `src/search/query_logger.py`: a scraped URL could not be traced back to which
engine(s) offered it, or whether any engine offered it at all.

## The incident that exposed it

On 2026-08-02 at 00:04:03, `scrape_url` fetched an idealo.de `OffersOfProduct` URL by numeric
product ID while researching a FritzBox router. That product ID today resolves to an unrelated
women's outdoor jacket — idealo ignores the URL slug entirely and serves whatever product
currently sits under the numeric ID (verified: a deliberately nonsense slug on the same ID lands
on the same jacket page). The question that mattered — did a search engine hand us that URL, or
did it come from somewhere else — was unanswerable from the logs: `query_log.jsonl` recorded the
search, `scrape_log.jsonl` recorded the scrape, nothing recorded which engines were drilled into
or which URLs they returned. Re-running the same search today, brave and startpage both return a
DIFFERENT product ID that correctly resolves to the FritzBox — nothing reproduces the old ID, and
whether an engine ever served it stays unknown. That is exactly the case this closes for future
incidents.

## What is and is not attributable — the constraint that shaped the design

A URL can NEVER be attributed to exactly one engine — engines overlap heavily, and drilling
several engines routinely surfaces the same URL in all of them. What IS recordable and sufficient:
the search (with its per-engine counts, already logged) and, per drilldown, which engine was
drilled and which URLs it returned. That answers the backwards question — "which engines offered
this URL in this session" — possibly several, and, decisively, possibly none. The none-case is
what the incident needed and could not get.

## Design

New `record_type: "drilldown"` in `query_log.jsonl` (same file, third record type alongside the
existing `engine_run`/`workflow_summary` — a drilldown is a third kind of event in the same
session, not a separate log), written from a new `_log_drilldown` helper in `cli.py`'s
`search_engine_drilldown` branch, on ALL FOUR sub-cases: cache hit, cache-miss-then-fresh-search,
cache-miss-then-search-still-failed, and requested-engine-not-in-pools. Fail-soft via the existing
`log_query`, same posture as the rest of this file.

Fields: `mode`, `engine`, `search_key`, `cache_status` (`"hit"` | `"miss_then_searched"` |
`"miss_then_search_failed"` — makes the cache-miss-triggers-a-fresh-search path explicit rather
than indistinguishable from an ordinary hit), `engine_in_pools` (distinguishes "engine excluded
upstream / never ran" from "engine ran, returned zero results" — both currently silent early
returns in `cli.py`), and `urls`: plain URL strings only, in pool order (position recoverable from
list index) — deliberately NOT full cached result objects (title/snippet/date/position); a URL
list answers "did engine X ever offer URL Y", which is all the backwards question needs, and the
full objects still live in the cache file (`~/.cache/websearch/<key>.json`, 1h TTL) if ever needed.

## search_key — the correlation mechanism

Added ONE field, `search_key`, to `workflow_summary` records (`= cache.cache_key(query, language,
engines, time_range, modifier_id=mode)`'s own output, threaded through `_build_query_log_entry`'s
existing signature — a 3-line diff in `search_web.py`, the one deliberate touch outside `cli.py`
this session made, flagged and confirmed before implementing rather than slipped in). Chosen over
inventing a new random id because it is ALREADY the exact value that determines which cached pools
a drilldown will read — reusing it means a `drilldown` record and the `workflow_summary` of the
search it came from are provably the same search whenever they share the value, with no new
concept for a reader to learn. Verified live end-to-end: `workflow_summary.search_key` and the
following `drilldown.search_key` matched byte-for-byte on both a real cache-hit run and a real
cache-miss run (the miss path's freshly-triggered internal search wrote its own `workflow_summary`
moments before the `drilldown` record, sharing the same key).

**Limit, stated in the schema comment itself (not only here):** `query_log.jsonl` is lazily pruned
on a 14-day window (`log_janitor`). A `drilldown` record can outlive the `workflow_summary` it
points at. A `search_key` that resolves to nothing in the file is ordinary retention, not an
orphaned record or a corrupted log — a later reader must read it that way.

**What remains impossible, precisely:** correlation does not extend to `src/logs/scrape_log.jsonl`
(a separate file). No shared identifier was added — explicitly out of scope this session. What it
would take: `scrape_url_workflow`/`cli.py`'s `scrape_url` dispatch accepting an optional
correlation id and writing it into `scrape_log.jsonl`'s own record, PLUS a way for the agent
calling `scrape_url` to actually know that id at call time (it would need to be surfaced in
`format_engine_pool`'s printed drilldown output, not just logged) — a real design decision, on
record, not built here.

## Verification

Real CLI runs, both paths, actual JSONL records inspected:
- Cache hit (`search_web` then `search_engine_drilldown` on the same query, `--engine google`):
  `workflow_summary.search_key` = `625d6a0c835be49b`, `drilldown.search_key` = same — exact match.
  3 records total per run (`engine_run`, `workflow_summary`, `drilldown`).
- Cache miss (drilldown on a never-searched query, `--engine brave`): `cache_status` =
  `"miss_then_searched"`, `search_key` = `4b381d70862c7078` on both the freshly-triggered
  `workflow_summary` and the `drilldown` record that followed it.

Unit tests: 3 new in `tests/test_query_logger.py` — `log_query` accepting the drilldown shape;
`search_key` in a REAL (mocked-engine, no network) `search_web_workflow` run matching the REAL
`cache.cache_key(...)` output, not a stubbed value; `cli.py`'s real `_log_drilldown` exercised via
an isolated subprocess (importing `cli.py` in-process reconfigures the root logger via
`logging.basicConfig` and registers an `atexit` chrome-kill hook — side effects that must not
bleed into the rest of the suite), covering hit-with-urls, hit-with-engine-absent, and
miss-then-search-failed. Full suite: `9 failed, 137 passed, 0 errors` (was 134 passed) — diffed
the `FAILED` line list against the standing baseline, identical, no drift. The 9 pre-existing
`test_query_logger.py`/`test_proxy_pool.py` failures unrelated and unchanged.

## Two findings, neither part of this session's scope, both fixed or noted where discovered

`tests/test_query_logger.py`'s shared `_make_mock_engine` helper sets `.search` on its mock, but
the real `_engine_with_timing` calls `.search_with_reason()` (returns `(results, empty_reason)`) —
a different, newer interface. This is the actual root cause of `test_engine_with_timing_ok/timeout
/empty` failing, and part of why `test_search_web_workflow_writes_log` fails too: those tests were
written against an interface `search_web.py` no longer has, not a transient flake. Not fixed (out
of scope, pre-existing) — a new, separate, correctly-shaped local mock was written for this
session's own new test rather than reusing or patching the stale shared helper.

`query_logger.py`'s schema comment documented a `"preview"` field on `workflow_summary` that the
real `_build_query_log_entry` has never written in the current codebase (confirmed: no `preview`
logic exists anywhere in `search_web.py`) — a stale line, corrected while already rewriting that
exact comment block for the `search_key`/`drilldown` additions. Consistent with this area's own
prior record of the preview-fetch feature's removal.
