# Soft function-size targets outside the news area (2026-08-20)

Step-2 milestone continuing the `refactor_sweep` area: three functions flagged in the 50-99
code-line soft-target range — `src/crawler/crawl_site.py::discover_urls_playwright` (58),
`src/search/search_web.py::_engine_with_timing` (57) and `search_web_workflow` (39-42, borderline).
Pure refactor — zero behavior change, verified against the standing 182-passed/10-failed baseline.

## Pre-move check: monkeypatch/import targets

`crawl_site.py` has zero test coverage (no `tests/test_crawl_site.py`) and no `dev/` imports of its
internals — no re-pointing risk at all. `search_web.py` has no dedicated test file either, but
`tests/test_query_logger.py` imports and CALLS (not monkeypatches) `_engine_with_timing` and
`search_web_workflow` directly — 3 of those calls are already part of the standing baseline's
failing set (mock engine exposes `.search`, not the `.search_with_reason` interface these functions
actually use — a pre-existing, documented mismatch, unrelated to this session). Numerous
`dev/search_pipeline/*.py` scripts import `_query_engines_concurrent`/`_select_engines`/
`search_web_workflow` directly — none of those three names were touched, only the internals of the
two target functions changed, so nothing needed re-pointing anywhere.

## `discover_urls_playwright`: one more coherent helper found

Already had four sibling helpers from a prior session (`_fetch_page`, `_build_crawler_config`,
`_handle_429_batch`, `_extract_frontier_links`). One coherent unit remained inside the BFS loop
itself: per-batch result classification (status filtering → collect `found`/`page_latencies` →
expand `frontier`/`visited` via the existing `_extract_frontier_links`), extracted as
`_process_batch_results` (mutates the passed containers in place, matching the original inline
loop's own mutation style — no return value needed). 58 → 44 code lines. Its 3-line header comment
duplicated `src/crawler/DOCS.md`'s existing Purpose paragraph (`stop_reason` enum) near-verbatim —
condensed to one line, nothing lost (category 3, already covered).

## `_engine_with_timing`: six near-duplicate except clauses collapsed

Each of six except clauses computed `search_ms` then returned an identical-shaped 5-tuple —
extracted `_classify_engine_exception(exc, timeout, search_ms) -> (status, drop_reason)`, an
isinstance chain in the EXACT SAME match order as the original except clauses. 57 → 34 code lines.

**BaseException-only-type check (requested verification):** confirmed programmatically (`issubclass`
+ full MRO printed for all six original except-clause types: `asyncio.TimeoutError`,
`httpx.TimeoutException`, `pydoll.exceptions.PydollException`, `websockets.exceptions.
WebSocketException`, `ConnectionError`, `httpx.HTTPError`, `json.JSONDecodeError`, `KeyError`,
`ValueError`, `AttributeError`) that every one is an `Exception` subclass — none is
`BaseException`-only (`asyncio.CancelledError`, `KeyboardInterrupt`, `SystemExit` are all
`BaseException`-direct, never matched by any of the six). The original code's own final clause was
ALREADY `except Exception as e:` (the catch-all, clause six) — meaning `CancelledError`/
`KeyboardInterrupt`/`SystemExit` were never caught by this function even before this refactor.
Collapsing all six into one `except Exception as e:` dispatching through `_classify_engine_exception`
therefore changes nothing about which exception types get caught: Python's own except-clause
resolution IS sequential isinstance matching against the first-listed type, which is exactly what
the extracted helper's if/isinstance chain reproduces in the same order.

## `search_web_workflow`: one small coherent unit extracted, rest is orchestrator pipeline

Measured at 39-42 code lines (Opus's 50 vs. this session's AST-measured 42 — both already under or
at the soft-target boundary). Already delegates to `_select_engines`/`_run_engine_fanout`/
`_format_breakdown`/`_build_query_log_entry` from a prior session; the remaining body is the
orchestrator's own linear pipeline (fanout → pool-build → cap → format → cache → log → return). One
small, nameable, single-responsibility unit remained: the pool-cap computation (K derived from
Google's pool size, each pool trimmed to `pool[:K]`) — extracted as `_cap_pools(pools) -> dict`.
Modest line savings (~4 lines) but a real coherent extraction, not a padding one — done because Opus
flagged this function explicitly as a target, and a genuine standalone unit did exist even though
the function was already close to/under the soft threshold.

## Verification

`tests/test_query_logger.py`: 8 failed / 2 passed, identical failure-name list to the pre-refactor
baseline (confirmed via `git stash` + re-run) — including `test_engine_with_timing_timeout`'s exact
assertion (`status == 'ERROR_OTHER'` not `'TIMEOUT'`, from the same `MagicMock` can't-be-awaited
`TypeError` falling through to the same final generic branch, now inside
`_classify_engine_exception` instead of the removed `except Exception as e:` clause — same log
message `"Engine error: %s"`, same log call site behavior). Full suite (`pytest tests/`): 182 passed,
10 failed — the exact standing baseline, unchanged. `python -c` import check confirms every
extracted/kept public and reused-private symbol (`discover_urls_playwright`, `_process_batch_results`,
`crawl_site_workflow`, `search_web_workflow`, `_engine_with_timing`, `_classify_engine_exception`,
`_cap_pools`, `_query_engines_concurrent`, `_select_engines`) still resolves.

No new substance surfaced by this sweep beyond the extractions themselves — no additional
process-docs content needed past this entry.
