# scrape_url.py + camoufox_scrape.py comment sweep + helper extraction (2026-08-20)

Comment-rule conformance pass on `src/scraper/scrape_url.py` (465 LOC) and
`src/scraper/camoufox_scrape.py` (532 LOC) — same discipline as the `pipe_scraper.py` split
(`refactor_sweep` area). Both files were dominated by large derivation comment blocks (some
30-50 lines) violating the worker comment rules (section markers / one-line function headers /
cross-module import comments only). Pure refactor — zero behavior/config/log-schema/rendered-output
change.

## Triage result: 100% category 3 (already covered) — zero new substance found

Every large comment block was checked against `src/scraper/DOCS.md` first (already dense and
near-verbatim for this package from prior sessions), then against the `scrape_pipeline`,
`camoufox_lane`, `cloudflare_render_wait`, and `time_budget` areas where DOCS.md didn't fully carry
a claim. Every block — `TOTAL_SCRAPE_BUDGET_S`'s 221.3s composition and its two honesty caveats,
`page_timeout`/`delay_before_return_html` derivation (R7/R4/R5 of the time-budget rules),
`remove_consent_popups` evidence (azubiyo.de, rfc-editor.org measurements), `HTMLDATE_TIMEOUT_S`'s
dateparser-slowness rationale, `_ensure_no_focus_steal`'s LSUIElement mechanism + empirical
focus-poll verification, `_build_camoufox_kwargs`'s full per-parameter calibration
(headless/os/humanize/geoip/enable_cache/locale/block_webgl), `_html_to_markdown`'s `raw:` vs
`raw://` fix, `_extract_camoufox_config_stamp`'s fingerprint-exclusion logic,
`_format_camoufox_output`'s sibling-not-shared rationale, both acquisition-error-message dicts'
framing — was already recorded elsewhere, most near-verbatim. **Zero blocks contained substance
recorded nowhere else; this entry itself is the only new process-docs content the sweep produced.**

Constants get ZERO comment lines (not even a one-line label), per the same rule established in the
`pipe_scraper.py` split: `HTMLDATE_TIMEOUT_S`, `TOTAL_SCRAPE_BUDGET_S`, `_LINK_LINE_RE`,
`_ACQUISITION_ERROR_MESSAGES`, `_BROWSER_LAUNCH_SIGNATURES` (scrape_url.py);
`_PLAYWRIGHT_DEFAULT_TIMEOUT_MS`, `_GOTO_WAIT_UNTIL`, `CAMOUFOX_RENDER_WAIT_S`,
`TOTAL_CAMOUFOX_BUDGET_S`, `_CAMOUFOX_ACQUISITION_ERROR_MESSAGES`, and every in-dict comment inside
`_build_camoufox_kwargs` (camoufox_scrape.py) — all deleted outright, rationale lives in DOCS.md /
the four areas above. Every function header condensed to one line (WHAT not HOW); every in-body
comment deleted after confirming coverage.

## Two DOCS.md dangling references fixed

Two existing `src/scraper/DOCS.md` lines pointed at code comments this sweep deleted:
- `camoufox_scrape.py`'s Purpose paragraph said "see `CAMOUFOX_RENDER_WAIT_S`'s own comment for the
  full trade-off" (the `page.wait_for_timeout` → `asyncio.sleep` swap) — repointed to the dated entry
  in the `camoufox_lane` area that carries the full trade-off (the render-wait budget rebooking
  session).
- `scrape_url.py`'s Purpose paragraph said "see the CrawlerRunConfig construction comments for the
  full history" (the `delay_before_return_html` 2.0→5.0 history, both sources) — repointed to the
  dated entry in the `cloudflare_render_wait` area.
- A third phrase, "every value justified in its own comment" (`_build_camoufox_kwargs`), was reworded
  to "every value justified below" — the justification was already inline in that same DOCS.md
  paragraph, the phrase just needed to stop pointing at the code comment.

## Mandatory helper extraction

Both `try_scrape` (64 code lines) and `try_scrape_camoufox` (55 code lines) exceeded the 50-code-line
threshold, each with a coherent helper already half-formed as a nested `_acquire()` closure. Extracted
to module-level `_acquire_scrape(url, browser_config, crawler_strategy, run_config, empty_meta)` and
`_acquire_camoufox(url, kwargs, empty_meta)` respectively — closure variables became explicit
parameters, return contract unchanged. Brought both parent functions under 50 (44 and 23 code lines)
and both new helpers under 50 too (26 and 34). No other function in either file reached 50 code lines
(measured by AST walk before deciding: `is_garbage_content` 34, `_ensure_no_focus_steal` 17,
`_format_scrape_output`/`_format_camoufox_output` 23/22 — all comfortably under). Neither test file
references `_acquire` by name (grepped before extracting); both test files patch module-level globals
(`AsyncWebCrawler`, `AsyncCamoufox`, `launch_options`, budget constants, `try_scrape`) that remain
resolvable identically since neither file was split into separate modules.

## Split verdict: no split for either file

Post-triage `wc -l`: `scrape_url.py` 299 (was 465), `camoufox_scrape.py` 227 (was 532) — both well
under the 400-LOC ceiling. No concern-based split needed.

## Verification

`tests/test_scrape_url.py`: 27/27 passing, unchanged. `tests/test_camoufox_scrape.py`: 26/26 passing,
unchanged. Neither test file needed import re-pointing (no split happened). Full suite (`pytest
tests/`): 182 passed, 10 failed — identical failure set to the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py` + 1 additional `test_query_logger.py` test not
present when the original "9 failed" baseline was recorded), confirmed unchanged before and after
this sweep. `try_scrape`'s and `try_scrape_camoufox`'s `meta` key contracts untouched (same keys,
same semantics) — verified by the unchanged test assertions, which read specific `meta`/logged-record
keys directly.
