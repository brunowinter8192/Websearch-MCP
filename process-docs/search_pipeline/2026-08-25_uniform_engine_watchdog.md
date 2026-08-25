# Engine watchdog unified to 6.0s, per-engine override dropped (2026-08-25)

Config-level change, decided with the user from log evidence rather than a fresh measurement pass.
`ENGINE_WATCHDOG_TIMEOUT` (the default `asyncio.wait_for` bound on `engine.search_with_reason` in
`search_web.py::_engine_with_timing`) moved from `3.6s` to `6.0s`; `ENGINE_WATCHDOG_OVERRIDE`
(`open_library`/`crossref`/`startpage`/`brave` at `6.0`, `semantic_scholar` at `5.0`) deleted
entirely — every engine now races the same bound.

## Reasoning

Engines run concurrently (`asyncio.gather` over per-engine `asyncio.wait_for`-guarded tasks), so
the SWEEP's wall time is bounded by whichever engine is slowest that run, not by the sum of
individual timeouts — a shorter timeout on a fast-usually engine buys the sweep nothing UNLESS that
engine is also consistently the bottleneck. Read off 138 `workflow_summary` records in
`query_log.jsonl`: the sweep already paid the 6s class on nearly every run regardless of the 3.6s
default (bottleneck engine: `semantic_scholar` 84x, `startpage` 26x, `open_library` 19x —
`google`, one of the 3.6s-default engines, only 3x). Median `total_wall_ms` 5069, p90 6074 — both
already inside the 6.0s band before this change, meaning raising the default couldn't realistically
lengthen typical sweeps further; the sweep's actual ceiling was already set by the override
engines. Meanwhile the shorter 3.6s default was actively censoring engines that were slow but
alive, not dead: `google` recorded 19 `TIMEOUT_WATCHDOG` events, `duckduckgo` 46, in that same
138-record window — real results discarded purely because they landed in the 3.6-6.0s band a
same-cost sweep would have tolerated from an override engine.

## Mechanical scope, one non-surprise

`crossref.py`/`open_library.py`'s `httpx.AsyncClient(timeout=6.0)` — flagged by
`src/search/engines/DOCS.md` as hand-aligned with the (now-deleted) override entry for those two
engines — were ALREADY at `6.0`, coincidentally already equal to the new uniform value. No code
change needed there; only the DOCS.md gotcha describing the coupling needed rewording (it named the
deleted dict). `semantic_scholar.py`'s own internal `tab.go_to(..., timeout=3.0)` (page-navigation
timeout, a different mechanism than the outer watchdog) was left untouched — comfortably under both
the old `5.0` override and the new `6.0` uniform value either way, never the limiting factor.
`LOCK_HARD_BUDGET_S` in `src/search/browser.py` (from the browser-lifecycle milestone,
`process-docs/browser_lifecycle/`) stayed numerically `60 + 6 + 15 = 81` unchanged — its derivation
comment was reworded only, since it used to name "the slowest per-engine watchdog override" and
there is no longer an override dict to point at.

## Live verification

Full suite green (226 tests, no test file needed changes — `test_query_logger.py`'s
`_engine_with_timing` calls pass `timeout=3.6`/`timeout=0.05` as arbitrary literal function
arguments for their own test purposes, not reads of the module constant, so they were unaffected).
A real `cli.py search_web "postgresql query planning"` run: 11/14 engines `OK`, `open_library`
timed out at exactly `search_ms=6001` (the new uniform bound, as expected), `google`/`duckduckgo` —
previously capped at 3.6s — completed `OK` at 2737ms/3539ms respectively, both durations that would
have been killed under the old default. Zero leftover Chrome processes before and after.
