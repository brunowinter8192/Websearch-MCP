# Catching-power triage of tests/ (milestone 1 of 2, 2026-08-24)

Pre-relocation triage of the full pytest suite (13 modules, `tests/`) — judged every test
group per module for REAL catching power (ability to fail on a genuine defect), independent of
mock usage. Milestone 2 (relocation of the surviving tests) is separate, not part of this session.

## Baseline vs. the last recorded number

Prior baseline (`process-docs/refactor_sweep/`, the 2026-08-20 baseline-repair entry): 192
passed / 0 failed. Actual run at session start: **209 passed / 0 failed** — the suite grew by 17
tests since that entry (camoufox acquisition lane, pipe_scraper camoufox-engine switch, and other
work added in sessions not covered by that doc). The 192 figure is stale as a live count; this
entry's own baseline (209) is itself only a point-in-time record too, not a claim about the
suite's current size going forward.

## Method

Read every test module in full (all 13, ~4070 LOC across `tests/`) and grouped tests by each
file's own `# ---` comment-delimited sections (no `class Test...` groups exist anywhere in this
suite — every module uses flat `def test_...` functions plus helper/fake classes). Judged each
group against two poles:

- KEEP: drives a real production function/class through real branch logic, even with I/O-boundary
  mocks (network client, browser automation, subprocess) — includes library-upgrade guards that
  call real installed library code, regression repros of real production failures, and real-file
  tmp_path I/O tests.
- DROP: verifies only its own wiring — asserts a function's return *shape* (type/keys) without
  exercising any value a real defect would change, or passes a fake value through and asserts it
  came back unchanged.

## Finding: 208 of 209 tests earned KEEP

Every group across all 13 modules drives real production code through real branches. Notable
KEEP examples confirmed during review (not exhaustive): `test_pipe_scraper.py`'s
`test_build_configs_produces_live_stealth_adapter` (constructs the real crawl4ai
`AsyncPlaywrightCrawlerStrategy`, catches the exact silent-degrade failure mode
`process-docs/scrape_pipeline` documents for `crawl4ai 0.8.6 + playwright-stealth 2.0.2`);
`test_scrape_url.py`'s `test_build_browser_flags_symbol_resolves_and_is_callable` (live call
into `crawl4ai.browser_manager.ManagedBrowser.build_browser_flags`, no pinning); `test_bing_engine.py`'s
`_clean_url` tests (real captured `bing.com/ck/a` redirect sample); `test_camoufox_scrape.py`'s
`test_html_to_markdown_survives_bracket_before_first_slash` (real "Invalid IPv6 URL" regression
repro, same class of bug documented in `process-docs/refactor_sweep`'s baseline-repair entry);
`test_proxy_pool.py`'s `test_run_loop_refresh_*` pair (explicitly confirmed production-correct,
not a test bug, in the 2026-08-20 baseline-repair entry — carried forward as KEEP here too).

**One DROP**: `tests/test_proxy_pool.py::test_load_backfill_pool_returns_tuple`. Called the real
`load_backfill_pool()` (httpx mocked) but asserted only `isinstance(pool, list)`,
`isinstance(sources, list)`, and per-source key membership (`{"url","ok","count"} <= s.keys()`) —
no assertion on any value a parsing/dedup/count defect would actually change. Redundant with the
two adjacent tests in the same group (`test_load_backfill_pool_continues_when_monosans_fails`,
`test_load_backfill_pool_source_count_on_success`), which assert real counts and per-source
outcomes and fully cover the same code path with actual catching power.

## Outcome

- Deleted the one test (no dedicated helper/fake existed only for it — self-contained, single
  function removal, `tests/test_proxy_pool.py` 592→573 LOC).
- Full suite re-run: 208 passed / 0 failed.
- Repo-wide grep (`src/`, `tests/`, `dev/`) for the deleted test's name: zero hits.
- Commit `88d29fe`.

Milestone 2 (relocation of `tests/` — out of this session's scope) will act on the 208 tests kept
here.
