# Persistent per-URL JSONL log with config stamp (2026-08-04)

Part of the `pipe_scraper_hardening` effort on `src/crawler/pipe_scraper.py`
(the mass-capture scrape path). Precedes any config change (stealth, fallback fetch, pacing tuning) by
design: this project's calibration method derives config values from external sources only (vendor
docs/source/issue trackers), never from its own domain sweeps — a sweep's result holds for the sampled
domains, not the next unknown one. What locates the real weak spots is the OPERATIONAL LOG accumulating
over time (which domains fail, how, under which config). That log has to exist before a config changes,
or there is nothing to compare later runs against.

## Design — reuse over reinvention

Studied the ad-hoc single-URL path's existing pattern first (`src/scraper/scrape_logger.py`,
`scrape_url.py`'s `extract_config_stamp`/`hash_config`/`extract_crawl4ai_diagnosis`, `src/log_janitor.py`)
rather than inventing a new one. Reused directly: `maybe_prune_jsonl` (fully generic, no changes needed),
`hash_config` and `extract_crawl4ai_diagnosis` (imported from `scrape_url.py` — generic, not
path-specific; precedent for this kind of cross-package import already exists, `crawl_site.py` already
imports `scrape_url.is_garbage_content`).

Built new, separate from the ad-hoc path per explicit decision: `src/crawler/pipe_scrape_logger.py`
(writer, `log_pipe_scrape`, own file `src/logs/pipe_scrape_log.jsonl`, own env var
`WEBSEARCH_PIPE_SCRAPE_LOG_PATH`) and `_extract_pipe_config_stamp`/`_log_pipe_record` inside
`pipe_scraper.py` itself (co-located with where `BrowserConfig`/`CrawlerRunConfig` are actually
constructed, same split as the ad-hoc path keeps its own `extract_config_stamp` next to its config
construction site, not inside the writer module).

Fields deliberately NOT carried over from `scrape_logger.py`'s schema, and why: no sidecar/`content_path`
(pipe_scraper already writes every page's raw markdown to `--output-dir` — that IS the content record);
no `mode` (pipe path has no content-filtering mode, always raw — the field would carry no signal); no
`fallback_to_raw`/`truncated`/`consent_stripped`/`garbage_content`/`garbage_type`/`published_date` (all
describe ad-hoc-path processing — filtering, truncation, consent-stripping, htmldate extraction — that
pipe_scraper does not do; its own contract is "save every page raw, no garbage-drop").

One field kept deliberately despite reading as a constant today: `crawl4ai_fallback_fetch_used` is
`None`/`False` on every current record (no fallback fetch path exists — that is a later milestone in this
effort). Kept in the schema now anyway, because the log's whole point is comparability ACROSS a future
config change — if the field only appeared once the fallback path landed, every pre-change record would
be structurally different from every post-change one.

`config_hash`'s scope was made explicit in the schema comment after review: it groups records that ran
under the same config, but it is NOT a stable identity across schema versions — it changes whenever ANY
stamped value changes, including a field being added to or removed from the stamp itself. A hash change
alone does not prove the running config changed; the full `config` dict is what a later reader must check.

`run_id` (uuid4, one per `scrape_urls_workflow` invocation, shared by every record it writes) is the one
addition beyond the ad-hoc path's shape — needed here in a way it is not there, since a single capture run
writes hundreds of records at once and later analysis needs to separate one run's records from another's.

## Defect found in review — ts stamped at queue time, not request time

First implementation stamped `ts` before `async with state['sem']` / before `_gate_domain` in
`_scrape_one`. Since `asyncio.gather` starts every `_scrape_one` coroutine at once, every record in a run
carried an almost-identical `ts` (the two sample records in the initial report: 2ms apart, in a run the
pacing gate stretches over seconds) — `wall_ms` was correct (measured after the gate) but `ts` recorded
queue time, not fetch time, silently destroying the log's ability to answer "did failures start N minutes
into the run" — the exact class of question this log exists to answer.

Root cause: `ts` was computed outside the gated critical section. Fix: moved the `ts` computation to
immediately after `await _gate_domain(...)`, next to `_scrape_one`'s own `t0`, in both the success path
and the `except Exception` path. Schema comment in `pipe_scrape_logger.py` now states explicitly what
`ts` means (request start, post-gate — not queue time, not completion time) so the stamp point isn't
moved back without noticing why it matters.

Added a regression guard (`tests/test_pipe_scraper.py::test_scrape_one_ts_reflects_request_start_not_queue_time`):
6 same-domain URLs, `concurrency_per_domain=1`, `download_delay=0.05`, fake crawler (no network) —
asserts the recorded timestamps actually spread (`len(distinct) > 1`, spread > 0.1s) rather than
collapsing to one value. Verified this test actually catches the defect: stashed the fix, re-ran the
test alone → failed with `assert 1 > 1` (all 6 records sharing one identical timestamp,
`21:35:03.311000`); re-applied the fix → passed. Also reproduced the fix on a real (non-fake) 6-URL CLI
run against `docs.github.com`: recorded timestamps `21:35:26.593` through `21:35:30.297`, a ~3.7s spread
matching the gate's pacing, not collapsed.

## Verification

12-URL smoke run (`docs.github.com/de/rest`, real CLI invocation) before the fix: 12/12 ok, one shared
`run_id`, correct config stamp, but all `ts` values within ~2ms of each other (the defect, not yet caught
at that point). Same smoke pattern re-run after the fix (6 URLs): real, spread timestamps as above.

Full test suite before this milestone's changes: `9 failed, 105 passed, 0 errors` (established at
milestone 1). After adding the logger + 7 initial tests: `9 failed, 112 passed, 0 errors`. After the ts
fix + 1 additional regression test: `9 failed, 113 passed, 0 errors`. Diffed the `FAILED` line list
against the milestone-1 baseline at every stage — identical, no drift. The 9 pre-existing failures
(`tests/test_query_logger.py`, `tests/test_proxy_pool.py`) are unrelated to this work and were confirmed
unchanged throughout.

Confirmed `src/logs/` (the log's default location) is gitignored (`.gitignore:25`) before any commit —
`git check-ignore -v` matched, and `git status --short` after the smoke runs (which used an explicit
`/tmp` path override) showed no `src/logs/` entry at all, tracked or untracked.
