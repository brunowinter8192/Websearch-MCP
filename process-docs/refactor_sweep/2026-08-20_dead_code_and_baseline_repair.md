# Dead code removal + test-baseline repair — full green (2026-08-20)

Two-part milestone: (1) remove code flagged dead by the prior `news_standards_conformance` sweep,
(2) repair the standing `test_query_logger.py`/`test_proxy_pool.py` failures to reach a fully green
suite. Result: **192 passed, 0 failed** (from the long-standing 182/10 baseline), stable across 6+
repeated full-suite runs. Areas: `news_pipeline`, `pooling`.

## Part 1 — dead code removal

**`src/news/engine/scrape.py:_RUN_CFG`** — deleted. Confirmed zero references anywhere in `src/`
before removal (`scrape_entries` builds its own `run_cfg` locally from `scrape_cfg`); the imports
it used (`CrawlerRunConfig`, `CacheMode`, `DefaultMarkdownGenerator`) stayed, since `scrape_entries`'
own `run_cfg` construction still needs them.

**`src/news/engine/proxy_pool/pool_loaders.py`'s 17 per-source `load_X_proxies()` wrappers** —
deleted (`load_curated_proxies` through `load_murongpig_proxies`). Verified per-function via
repo-wide grep (including `dev/`) before removal: every hit outside `pool_loaders.py` itself was in
`dev/news_pipeline/theblock/{curated_sources.py,probe_liveness.py,probe_curated_theblock_cf.py}` —
confirmed those files have zero `src.` imports (independent, same-named, unrelated copies). Kept:
`load_backfill_pool`, `_fetch_proxifly`, `_fetch_bare_txt`, `_fetch_roosterkid`, `_try_source`,
`_merge_dedup`, all `*_SOURCES` constants (still consumed directly by `load_backfill_pool`'s
for-loops). File: 325→190 LOC.

**`src/news/engine/publish.py`** — deleted entirely. `pub_date_str` (+ its `DATE_RE` dependency) was
the only live symbol — imported by `clean_pass.py:_run_clean_pass`. Moved verbatim (including its
`"unknown"` fallback, NOT swapped for `dedup.py`'s near-duplicate `pub_date_str` which has a
different fallback — `""` — and would have been a silent behavior change) into `clean_pass.py`
directly. Everything else in the file (`url_hash`, `copy_articles`, `run_rag_index`,
`parse_index_result`, `_write_index`, `publish_articles`) had zero external callers and went with
it. Updated `engine/DOCS.md` (dropped the module entry + the Role-paragraph mention) and
`src/news/DOCS.md` (`clean_pass.py` entry now documents owning `pub_date_str`; dropped the stale
Gotcha line).

## Part 2 — test-baseline repair

### `test_query_logger.py`: 4 distinct root causes, not the 1-2 previously documented

`src/search/DOCS.md`'s pre-existing Gotcha named ONE root cause (`.search` vs `.search_with_reason`
mock-interface drift) for `test_engine_with_timing_*` + "part of" `test_search_web_workflow_writes_log`.
Investigation found 3 more, all confirmed by direct execution (not guessed):

1. **`.search` vs `.search_with_reason`** (the documented one). Fixed by deleting the file's stale
   shared mock (`_make_mock_engine`, set `.search`) and promoting the already-correct
   `_make_mock_engine_with_reason` (previously a lower, duplicated, locally-scoped helper) to the
   file's one shared Helpers-section mock, extended with an optional `delay` param for the timeout
   test. Also fixed `test_engine_with_timing_timeout`'s stale status assertion: production returns
   `"TIMEOUT_WATCHDOG"` (a `status.py` sub-status), never the bare `"TIMEOUT"` the test asserted —
   confirmed by direct call: `_engine_with_timing(slow_mock, ..., timeout=0.05)` →
   `(..., 'TIMEOUT_WATCHDOG', 'asyncio.TimeoutError after 0.05s watchdog')`.

2. **`ql.LOG_PATH` doesn't exist.** `query_logger.py` has no `LOG_PATH` module attribute at all —
   `log_query()` reads `WEBSEARCH_QUERY_LOG_PATH` fresh from the environment on every call
   (`os.environ.get(...)`, falling back to `DEFAULT_LOG_PATH`). `unittest.mock.patch.object(ql,
   "LOG_PATH", ...)` raises `AttributeError` immediately (confirmed by direct run) since the target
   attribute must already exist. Fixed 4 tests (`test_log_query_writes_jsonl`,
   `test_log_query_appends`, `test_log_query_fail_soft`, `test_search_web_workflow_writes_log`) to
   use `monkeypatch.setenv("WEBSEARCH_QUERY_LOG_PATH", str(log_file))` — the pattern the file's own
   newer tests (`test_log_query_accepts_drilldown_record_shape`,
   `test_search_web_workflow_writes_search_key_matching_cache_key`) already used correctly.

3. **`fetch_previews`/`_merge_and_rank` don't exist in `search_web.py` anymore — new finding, not in
   the prior Gotcha.** `test_search_web_workflow_writes_log` mocked
   `patch.object(search_web, "fetch_previews", ...)` and `"_merge_and_rank"`; grep confirms neither
   function is defined in `search_web.py` at all (`AttributeError` on the first `patch.object` call,
   confirmed by direct run). Current `search_web_workflow` uses `build_engine_pools`/`_cap_pools`/
   `_format_breakdown` instead — the previews-and-merge-and-rank pipeline this test was written
   against has been fully removed from production. The expected log record shape had also drifted:
   no `"preview"` key; current shape is `{record_type, ts, query, language, engines_requested,
   engines_excluded, total_wall_ms, bottleneck_engine, engines, search_key}`. Rewrote the test
   against current `search_web_workflow` behavior, modeled on the already-passing
   `test_search_web_workflow_writes_search_key_matching_cache_key`'s mock pattern
   (`ENGINES`/`_DEFAULT_ENGINES`/`cache_write` patched, `cache_key` left real).

4. **`search_web_workflow` writes TWO log records per call, not one — new finding.** Re-running the
   rewritten test (after fixing 1-3) surfaced a 4th mismatch: `_query_engines_concurrent` (called
   inside `_run_engine_fanout`, the default non-timed path) independently writes its own
   `"engine_run"` record via `log_query(...)`, in addition to `_build_query_log_entry`'s
   `"workflow_summary"` record — confirmed by inspecting the actual 2-line JSONL output from a real
   run. `test_search_web_workflow_writes_search_key_matching_cache_key` already anticipated this
   (filters `[r for r in records if r["record_type"] == "workflow_summary"]`); applied the same
   pattern to `test_search_web_workflow_writes_log`.

**A 5th, independent time-bomb bug, found only after fixing 1-4 revealed it:** with the `LOG_PATH`
layer fixed, `test_log_query_writes_jsonl`, `test_log_query_appends`, and (already in the standing
failure list before this session) `test_log_query_accepts_drilldown_record_shape` started failing
with wrong LINE COUNTS (not attribute errors). Root cause: `query_logger.log_query()` calls
`log_janitor.maybe_prune_jsonl()` on every write, which drops any JSONL line whose `"ts"` field
parses older than the 14-day retention window (or is missing — `KeyError` inside the parse also
counts as "drop, unparseable"). These 3 tests used HARDCODED literal timestamps
(`"2026-01-01T00:00:00.000Z"`, `"2026-08-05T00:00:00.000Z"`, or no `ts` field at all) — harmless when
originally written, but the sandbox's real clock has since caught up to 2026-08-20, putting
`2026-01-01` (232 days back) and `2026-08-05` (15 days back, 1 day past the 14-day cutoff) both
outside the retention window: their own just-written lines were being silently pruned away
immediately after write. Confirmed via `date -u` (sandbox clock: `Thu Aug 20 2026`) +
`log_janitor.py`'s `_prune_jsonl` source (`cutoff = now - 14 days; drop lines with parsed_ts <
cutoff`). This is a genuinely NEW finding not in `src/search/DOCS.md`'s prior Gotcha at all — it
explains why `test_log_query_accepts_drilldown_record_shape` was already failing before this session
despite using the CORRECT `monkeypatch.setenv` pattern (the LOG_PATH fix wasn't its problem; the
stale date was). Fixed all 3 with a shared `_now_ts()` helper (current time, matching production's
own `%Y-%m-%dT%H:%M:%S.%f`-truncated-to-ms `Z`-suffixed format) instead of hardcoded literals —
eliminates this entire class of bug going forward rather than pushing the deadline out again.

### `test_proxy_pool.py`'s 2 `test_run_loop_refresh_*` failures — VERDICT: test bug, production correct

Both tests patch `loop.time` wholesale and drive `time.monotonic()` from a fixed-list `side_effect`,
with inline comments mapping each list value to a specific call site — a fragile mocking style that
requires the list to exactly match the real call count and order.

**Traced the actual call sequence** (both by reading `run_loop`/`_execute_batch` and by running an
instrumented copy with a call-counting `side_effect`): `_last_refresh`(startup) →
`_last_progress`(startup) → `now`(iter1) → **`_last_progress`(per-resolution, inside
`_execute_batch`, once per successful fetch in the batch)** → `now`(iter2) → ... The original
5-value (test 1) / 4-value (test 2) sequences **omitted both the startup `_last_progress` call and
the per-resolution `_last_progress` update call** — undercounting the "early" (pre-refresh) values
needed by exactly 2. Net effect: the refresh fired on the very first loop iteration, before batch 1
ever ran, so the Pool-A proxy never entered `wset` before the pool swap — the tests' own premise
(a proxy surviving in `wset` across a refresh) was never actually exercised. Direct run with the
ORIGINAL sequence confirmed this: `fetch_url` was called with `B1:80` (Pool B) for `url1`, the very
first URL — proving the refresh preceded batch 1.

**Confirmed pre-existing, not introduced by any of this area's prior refactor sessions**: the same
call-site structure (2 startup calls, `now` at top of `while queue:`, `_last_progress` updated once
per resolution inside the executor loop) is present verbatim in the pre-refactor `loop.py`
(commit `fa94f13`, before the `rider.py`/function-size-conformance/comment-conformance sessions ever
touched this file) — the undercounted `mono_seq` bug predates all of them.

**Built and verified corrected 9-value sequences** for both tests (traced independently per test's
own batch/concurrency shape, since test 2 uses concurrency=3 with 3 futures resolving in one batch —
3 separate `_last_progress` calls, not 1): `[0.0, 0.0, 0.0, 0.0, 15.0, 15.0, 15.0, 15.0, 15.0]` +
padding, for both. Re-ran both scenarios against the corrected sequence: **both pass** — Pool-A
proxy `A1:80` correctly re-dispatched post-refresh (test 1); Pool-A proxy alongside both Pool-B
proxies immediately active post-refresh (test 2); all target URLs reach `done` in both. This is
direct behavioral confirmation, not just "the test comment's arithmetic is wrong" — production
`wset` semantics (never touched by `_refresh_pool`, removed only on 2-strike burn) are correct as
implemented. Updated both tests' inline sequence comments to the corrected call-by-call mapping and
removed a stale `loop.py` line-number cross-reference (`"lines 62-68"`) from test 1's docstring.

## Verification

Full suite (`pytest tests/`): **192 passed, 0 failed** — re-run 6 times total across this session
(4 consecutive full-suite runs plus 2 more after the DOCS.md-only edits), zero flakiness observed.
`test_query_logger.py` alone: 10/10, re-run 3 times independently for extra confidence given its
timing/clock sensitivity. `test_proxy_pool.py` alone: 23/23. Syntax-parsed every touched file. Repo-wide
grep confirmed zero remaining references to any deleted symbol (`publish.py` module, `_RUN_CFG`, all
17 `load_X_proxies` wrapper names, the old `.search`-based `_make_mock_engine`) anywhere in `src/`,
`tests/`, or `dev/`.

This is the first fully-green baseline this area has had across the whole `rider.py` →
`pipeline.py` → news-function-size → news-comment-conformance → this milestone's refactor arc; all
prior entries in this arc correctly reported "182 passed / 10 failed, unchanged from standing
baseline" as their success criterion — that baseline no longer applies going forward. Future
sessions in this arc should target 192/0, not 182/10.
