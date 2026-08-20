# news-area function-size conformance sweep (2026-08-20)

Function-size conformance pass across `src/news/` — no module splits, only intra-module helper
extraction on 6 hard targets (≥100 code-relevant LOC, mandatory) + 7 soft targets (50-99, extract
only where a coherent helper exists). Zero behavior change: report/markdown output byte-identical
where verifiable, argparse surface unchanged, `cursor_loop` pagination/termination semantics
unchanged. Same discipline as the `rider.py` / `pipeline.py` splits (area: `news_pipeline`).

## Monkeypatch-namespace / exact-call-semantics findings

Every touched module was checked for `dev/`/`tests/` patch targets before extracting anything
(worker-rule-mandated, same class of check as the `rider.py` milestone's finding).

**`janitor.py` and `theblock/discover.py` had REAL pytest coverage** (`tests/test_proxy_pool.py`,
`tests/test_theblock_discover.py`) — imported functions directly and, for `janitor.py`, asserted on
rendered `job.md` text content. This coverage doubled as regression proof for the extraction: both
suites pass unchanged post-refactor (`test_theblock_discover.py` 13/13; the `test_job_md_*`/
`test_group_pool_sources_*` subset of `test_proxy_pool.py` all pass).

**`proxy_pool/loop.py` carried a new, more subtle constraint than a simple attribute-patch.**
`tests/test_proxy_pool.py`'s two `test_run_loop_refresh_*` tests (part of the standing 2-test
`test_proxy_pool.py` failure baseline — pre-existing wset-survival logic mismatch, unrelated to this
sweep) do `patch("src.news.engine.proxy_pool.loop.time")` — replacing the ENTIRE `time` module
reference inside `loop.py`'s namespace with a `MagicMock`, then drive `mock_time.monotonic.side_effect`
with a hand-counted sequence, each entry commented with the exact original call site it corresponds
to (e.g. "call 3 → line 60 iter 2 now = 15.0"). This meant the extraction could not just move
`_last_progress = time.monotonic()` calls around — the ORIGINAL called `time.monotonic()` once per
url that resolved to done/dead inside the batch-processing loop (0 to N times depending on batch
size and outcome), not once per batch. Collapsing it to a single post-batch call (the initially
obvious design — track a `progressed: bool` flag, call `time.monotonic()` once after `_execute_batch`
returns) would have changed the total call count whenever a batch had >1 simultaneous done/dead
resolution, desyncing the pre-counted `mono_seq` in `test_run_loop_refresh_fresh_candidates_from_new_pool`
(concurrency=3, 3 simultaneous "ok" resolutions in its second batch). Fix: `_execute_batch` reproduces
the exact original per-resolution `time.monotonic()` call pattern internally, returning only the
FINAL value as `last_progress` (`None` if no resolution happened) — functionally identical to the
original's repeated reassignment (only the last call's value survives past the loop either way), but
call-count-identical too. Verified: both tests fail with the IDENTICAL assertion text before and
after (`"wset survival failed: expected Pool-A proxy 'A1:80'... got 'B1:80'"` and `"Pool A proxy
A1:80 missing from dispatched set — wset cleared unexpectedly"` respectively) — no `StopIteration`,
no new failure mode, confirming the call-count preservation held.

**`proxy_riding/reporter.py`, `browser_reporter.py`, `coindesk/discover.py`, `coindesk/cleanup.py`,
`engine/scrape.py`, `engine/scrape_job.py`, `__main__.py` had NO test coverage** — free to refactor
internals; verified by other means (see Verification).

## Per-target extraction summary

| Target | LOC before→after (code lines) | Helper(s) |
|---|---|---|
| `proxy_riding/reporter.py:_compute_stats` (hard) | 118→53 | `_compute_retry_outcome`, `_compute_pool_windows`, `_compute_load_percentiles`, `_compute_connect_fail_stats` |
| `proxy_riding/reporter.py:_write_md` (hard) | 149→13 | `_md_header_counts`, `_md_proxy_riding`, `_md_pool_windows`, `_md_regwall`, `_md_connect_fail`, `_md_load_time`, `_md_plots` |
| `coindesk/discover.py:cursor_loop` (hard) | 138→63 | `_CursorLoopStats` (scratch dataclass), `_process_batch`, `_fetch_next_page`, `_handle_cursor_exhaustion` |
| `proxy_pool/loop.py:run_loop` (hard) | 122→52 | `_refresh_pool`, `_execute_batch` |
| `__main__.py:main` (hard) | 116→30 | `_build_parser`, `_add_core_args`, `_add_scrape_only_args` |
| `browser_reporter.py:_write_md` (hard) | 101→21 | `_md_header`, `_md_char_distribution`, `_md_failure_list`, `_md_url_list_section` (shared, dedups the verbatim-identical Regwall-URLs/Empty-URLs blocks) |
| `proxy_pool/loop.py:_build_batch` (soft) | 51→23 | `_assign_batch_slots` (dedups Phase 1's two near-identical proxy-assignment loops) |
| `pool_loaders.py:load_backfill_pool` (soft) | 56 (unchanged) | **not extracted** — see below |
| `scrape_job.py:scrape_chunks_raw` (soft) | 55→19 | `_scrape_one_chunk` |
| `engine/scrape.py:_fetch_one` (soft) | 52→32 | `_classify_fetch` |
| `janitor.py:_write_md` (soft) | 65→27 | `_md_window_table`, `_md_source_breakdown` |
| `janitor.py:_compute_window_stats` (soft) | 52→12 | `_compute_one_window` |
| `theblock/discover.py:discover` (soft) | 53→21 | `_resolve_target_subs` |
| `coindesk/cleanup.py:clean_body` (soft) | 52→8 | `_strip_and_substitute_lines`, `_normalize_paragraphs` |

**`pool_loaders.py:load_backfill_pool` deliberately NOT extracted.** It's a flat ordered sequence of
18 `_try_source(url, fetch_fn, entries, sources)` calls; the package's own `DOCS.md` already states
(pre-existing, from an earlier sweep) "no extractable concern exists... Do not split" for this exact
flat-list-of-loaders shape at the MODULE level. The same reasoning holds one level down at the
FUNCTION level: `_merge_dedup` is "first occurrence wins" (confirmed by reading its implementation),
so the CALL ORDER of `_try_source(...)` determines which source's entry survives a cross-repo
duplicate, and `sources`' reported order (rendered in `job.md`'s "Pool source breakdown" section)
is also order-sensitive. A data-driven loop over `(SOURCES_LIST, fetch_fn)` pairs would need to
preserve that exact order anyway, adding indirection for zero behavioral gain — left as one flat
function, matching the pre-existing module-level Gotcha's spirit.

## `cursor_loop`'s tri-state exhaustion signal — verified by construction, not just reading

The original has two SEQUENTIAL checks after the cursor-fallback loop: `if next_body is None and
next_url: <try re-warm, break on fatal>` then `if next_body is None: <print "Cursor exhausted",
break>`. On the fatal re-warm path, the ORIGINAL breaks immediately inside the first check — the
second check's message is never reached. A naive extraction returning just `(headers, body)` from
the re-warm helper and letting the caller re-check `if body is None: print(...)` would print BOTH
messages on a fatal re-warm (a real behavior change: doubled log noise, and the fatal path's own
message would be followed by a false-implying "no body" message reached via unrelated fallthrough).
Fix: `_handle_cursor_exhaustion` returns `(headers, body, fatal: bool)`; the caller `break`s
immediately when `fatal`, before reaching the second check. Verified with a throwaway script
(`/tmp/verify_cursor_loop.py`, not committed) mocking `httpx.get` to always 403 and `try_rewarm` to
return `method="fatal"`: exactly 1 "FATAL: re-warm failed" message, 0 "Cursor exhausted with no
body" messages, across the full `cursor_loop` call (not just the extracted helper in isolation) —
confirms the caller-side dispatch, not just the helper's own logic, is correct.

## Comment triage

Scope: comments inside the 13 target functions actually touched (the 6 hard + the 6 soft targets
extracted from; `load_backfill_pool` untouched, no triage needed there beyond the Gotcha note
above), plus any newly-authored helper headers. Pre-existing multi-line docstrings/headers on
functions NOT listed as targets (e.g. `coindesk/discover.py`'s `discover()`, `Janitor`'s class
docstring, `engine/scrape.py`'s `scrape_entries`) were left untouched — out of this sweep's scope
(not restructured, not part of the 13 targets).

| Comment | Verdict |
|---|---|
| `reporter.py:_compute_stats`'s `# connect_fail breaks before job_records.append()...` | deleted — verbatim covered by `state.py`'s `DOCS.md` paragraph (from the `rider.py` split) |
| `reporter.py:_compute_stats`'s `# Retry outcome: among URLs...` | reused verbatim as `_compute_retry_outcome`'s new 1-line header |
| `reporter.py:_compute_stats`'s `# Eligible pool over time — bucket...` | reused verbatim as `_compute_pool_windows`'s new 1-line header |
| `coindesk/discover.py:cursor_loop`'s 2-line header | condensed to 1 line |
| `coindesk/discover.py:cursor_loop`'s `# Termination: oldest article...` (inline) | deleted — redundant with the adjacent print message |
| `coindesk/discover.py`'s `# Process and incrementally write this batch` | reused verbatim as `_process_batch`'s header |
| `coindesk/discover.py`'s `# Build next cursor; fall back to N-1, N-2 articles on 403` | reused (lightly extended) as `_fetch_next_page`'s header |
| `coindesk/discover.py`'s `# All cursor fallbacks exhausted → try re-warm` | reused (lightly extended) as `_handle_cursor_exhaustion`'s header |
| `coindesk/discover.py`'s `# Proactive re-warm every REWARM_EVERY seconds...` (inline) | moved — folded into `platforms/coindesk/DOCS.md`'s discover.py paragraph (the `httpx_rewarm_confirmed`-gating detail was NOT previously documented anywhere) |
| `coindesk/discover.py`'s `# Checkpoint log every CHECKPOINT_EVERY successful calls` (inline) | deleted — self-evident from the adjacent `if ok_calls % CHECKPOINT_EVERY == 0` + "checkpoint" print |
| `loop.py:run_loop`'s 13-line docstring | deleted, condensed to 1 line — the `(done, dead, gap)` semantics already in `DOCS.md` Flow; the exhaustion-sleep mechanics already in `_compute_sleep`'s own 1-line header |
| `loop.py:run_loop`'s `# stall detection: last time a URL resolved to done or dead` (inline) | deleted — verbatim already in `DOCS.md`'s Stall-terminate Gotcha |
| `loop.py:run_loop`'s `# buf + wset exhausted — sleep until next eligible proxy...` (inline) | deleted — redundant with `_compute_sleep`'s own header |
| `loop.py:_build_batch`'s 7-line docstring | condensed to 1 line; Phase 1/Phase 2 split already implicit in the new `_assign_batch_slots` extraction |
| `loop.py:_build_batch`'s `# Phase 2 — Tail: ...` (inline) | deleted — redundant with `_build_batch`'s own condensed header, which now states both phases |
| `loop.py:_execute_batch`'s 4-line header (newly authored, not salvaged) | condensed to 1 line; the `last_progress`-replicates-exact-call-semantics rationale → `DOCS.md` Gotchas (new) + this entry's finding above (it's a refactor-mechanics fact, not a runtime landmine alone, so both) |
| `scrape_job.py:_scrape_one_chunk`'s 2-line header (newly authored) | condensed to 1 line |
| `janitor.py:_compute_window_stats`'s 3-line header | condensed to 1 line; the refresh-bucketing boundary edge case (`t0+3600s` lands in window 1, not 0) moved to `DOCS.md`'s janitor.py paragraph (not previously documented) |
| `janitor.py:_compute_window_stats`'s `# Pre-compute (window_index, size)...` (inline) | deleted — redundant with the header's own "same `int((ts-t0)/3600)` formula" phrasing |
| `theblock/discover.py:discover`'s 4-line header | condensed to 1 line — the four-mode timeframe breakdown already verbatim in `platforms/theblock/DOCS.md`'s "Four timeframe modes" bullet list |
| `theblock/discover.py`'s `pool_cache: list = []  # lazy-loaded on first proxy fallback...` (inline) | deleted — verbatim already in `platforms/theblock/DOCS.md` |

Tally: **7 deleted-as-covered**, **4 reused verbatim/near-verbatim as new helper headers** (the ideal
outcome — the comment already described exactly what got extracted), **3 moved to `DOCS.md`** as
genuinely new documentation (proactive re-warm gating, window-bucketing boundary edge case,
`_execute_batch`'s call-semantics contract), **5 condensed multi-line headers with no salvageable
extra content** (already fully covered elsewhere). Two stale cross-references from the PRIOR
`pipeline.py` split were also caught and fixed while updating adjacent `DOCS.md` text this session:
`engine/DOCS.md`'s `scrape.py`/`scrape_job.py`/`browser_reporter.py`/`dedup.py` entries still said
`pipeline.py:run_pipeline`/`run_scrape_only` where the actual caller is now `_run_pipeline_proxy_pool`/
`_run_pipeline_browser`/`_run_scrape_only_browser`; `platforms/theblock/DOCS.md` still said
`pipeline.py:_persist_master_list` where the function moved to `pipeline_support.py`.

## Verification

Full suite (`pytest tests/`): 182 passed, 10 failed (8 `test_query_logger.py` + 2
`test_proxy_pool.py`) — identical to the standing baseline throughout every incremental change in
this sweep, re-checked after each file.
`tests/test_proxy_pool.py`: 21 passed / 2 failed (unchanged failure set, IDENTICAL failure-assertion
text confirmed before/after for both `test_run_loop_refresh_*` tests — see the exact-call-semantics
finding above). `tests/test_theblock_discover.py`: 13/13 passed (unchanged).
`proxy_riding/reporter.py` + `browser_reporter.py` (no test coverage, `matplotlib` not installed
in-venv): `_compute_stats`/`_write_md` called directly against a synthetic `RiderState`/
`job_records` via a throwaway script (`/tmp/verify_riding_reporter.py`, `/tmp/verify_browser_reporter.py`,
not committed); rendered `job.md` diffed byte-for-byte before/after with the two inherently
non-deterministic lines (`Wall-clock`, `URLs/min`, `Backfill projection` — all derived from
`datetime.now()` inside `_compute_stats`) excluded from the diff — zero other differences.
`cursor_loop`'s tri-state exhaustion signal: verified by construction with the throwaway
`/tmp/verify_cursor_loop.py` script (see above) — exact message-count assertions, not just code
inspection.
`__main__.py`: `python -m src.news --help` text captured before and after via `diff` — byte-identical
(argparse surface, flag order, help text unchanged).
`coindesk/cleanup.py:clean_body`: no test coverage; sanity-checked with a synthetic markdown body
covering every strip rule (byline, date-byline, tag-footer, image, inline-link substitution,
trailing whitespace, paragraph-boundary blank insertion) via a throwaway one-off `python -c` call —
all rules fired as expected; not a byte-diff since no "before" run was captured for this
specific function (mechanical 1:1 body-move, lower risk than the reporters).
Repo-wide grep confirmed no dev/tests reference to any of the newly-introduced helper names
(`_compute_retry_outcome`, `_md_header_counts`, `_process_batch`, `_refresh_pool`, `_execute_batch`,
`_assign_batch_slots`, `_build_parser`, `_scrape_one_chunk`, `_classify_fetch`, `_md_window_table`,
`_compute_one_window`, `_resolve_target_subs`, `_strip_and_substitute_lines`,
`_normalize_paragraphs`) — all are purely internal, no re-pointing needed anywhere.
