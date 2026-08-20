# pipe_scraper.py split + comment sweep (2026-08-20)

`src/crawler/pipe_scraper.py` (630 LOC, over the 400-LOC ceiling) split into 7 concern-based
modules under `src/crawler/`. Pure refactor — zero behavior/config/log-schema change, verified by
full test-suite parity (see Verification).

## Module cut

| Module | Owns |
|---|---|
| `pipe_scraper.py` (entry, unchanged CLI) | `scrape_urls_workflow` (orchestrator), `_scrape_all` (per-run engine dispatch), argparse |
| `pipe_scraper_constants.py` | pacing/timeout/threshold constants |
| `pipe_scraper_pacing.py` | per-domain Scrapy gate (`_ensure_domain_state`, `_gate_domain`) |
| `pipe_scraper_config.py` | chromium `BrowserConfig`/`CrawlerRunConfig` construction + config stamp |
| `pipe_scraper_acquisition.py` | curl_cffi fallback routes + per-URL engine executors (chromium + camoufox) |
| `pipe_scraper_records.py` | JSONL record assemblers (both engines) |
| `pipe_scraper_report.py` | `/tmp` outcome report + console summary |

Two decisions deviate from the prompt's literal candidate-concern list:

- **`pipe_scraper_constants.py` added** (not a named candidate) — `DOWNLOAD_DELAY`/
  `CONCURRENCY_PER_DOMAIN`/`CAMOUFOX_CONCURRENCY_PER_DOMAIN`/`PAGE_TIMEOUT_MS`/
  `DELAY_BEFORE_RETURN_HTML`/`EMPTY_THRESHOLD_BYTES`/`FALLBACK_FETCH_TIMEOUT_S` are each read by
  3+ of the split modules (e.g. `EMPTY_THRESHOLD_BYTES` by both the config stamp and the
  acquisition module's outcome mapping) — code-standards rule for constants shared by 2+ modules.
  Splitting them per-owning-module instead would have created import cycles (see next point).
- **"curl_cffi fallback routes" and "per-URL engine executors" merged into one
  `pipe_scraper_acquisition.py`**, not two modules as the prompt's candidate list suggested. Tried
  the two-module split first; it produces a genuine bidirectional import: `_own_fallback_rescue`
  (fallback) is called directly from `_scrape_one`'s (executor) except block AND needs
  `_url_to_filename` (naturally an executor-side helper, since `_scrape_one`/`_scrape_one_camoufox`
  are its other two callers) to write the rescued content — an unavoidable cycle, not a naming
  convenience. Merging the two concerns into one module (their real coupling in the original code)
  resolved it cleanly.

Resulting LOC (`wc -l`): `pipe_scraper.py` 124, `pipe_scraper_acquisition.py` 189,
`pipe_scraper_config.py` 63, `pipe_scraper_records.py` 46, `pipe_scraper_report.py` 36,
`pipe_scraper_pacing.py` 26, `pipe_scraper_constants.py` 12 — all well under the 400 ceiling. No
function reached the 50-code-line helper-extraction threshold after comment stripping (`_scrape_one`
~48, `_scrape_one_camoufox` ~35, measured by hand before the split).

## Comment triage

The original file carried large derivation-style comment blocks (verified stealth-adapter
reachability, curl_cffi TLS-fingerprint evidence, `raw:` vs `raw://` fix, landed_url path-a/path-b
semantics, engine-switch rationale, argparse dest-resolution mechanics) that violate the worker
comment rules (only section markers / one-line function headers / cross-module import comments are
allowed). Every block was checked against `src/crawler/DOCS.md`, `pipe_scrape_logger.py`'s schema
comment, and the `pipe_scraper_hardening`/`camoufox_lane`/`scrape_pipeline` process-docs areas
before deleting.

**Result: every substantive block was already recorded elsewhere, near-verbatim in most cases.**
Zero blocks contained substance recorded nowhere else — none needed net-new process-docs content
beyond this sweep record itself.

| Original block (function) | Verdict | Covering surface |
|---|---|---|
| `CAMOUFOX_CONCURRENCY_PER_DOMAIN` rationale | deleted | `src/crawler/DOCS.md` Gotchas; `camoufox_lane` area |
| `scrape_urls_workflow` param docstring (engine/concurrency/block_images) | deleted, condensed to 1-line header | `src/crawler/DOCS.md` Purpose; `camoufox_lane` area |
| `_extract_pipe_config_stamp` header | condensed to 1-line header | self-explanatory, no external doc needed |
| `_curl_cffi_get` (EFFECTIVE_URL finding) | deleted | `src/crawler/DOCS.md`; `scrape_pipeline` area |
| `_fallback_fetch` header (crossref evidence, TLS-fingerprint citation) | deleted | `src/crawler/DOCS.md`; `pipe_scraper_hardening` area |
| `_own_fallback_rescue` header (`raw:` fix, resolved-vs-outcome semantics) | deleted | `src/crawler/DOCS.md`; `camoufox_lane` area; `pipe_scrape_logger.py` schema comment |
| `_landed_url_from_result` header | deleted | `src/crawler/DOCS.md` Gotchas (already near-verbatim) |
| `_log_pipe_record` / `_log_pipe_camoufox_record` headers | deleted | `pipe_scrape_logger.py` schema comment |
| `_scrape_one_camoufox` header (engine switch) | deleted | `src/crawler/DOCS.md` Purpose; `camoufox_lane` area |
| `_build_configs` header + inline per-field rationale (stealth/magic/consent/fallback wiring) | deleted, minus 1 guard (see below) | `src/crawler/DOCS.md`; `pipe_scraper_hardening` area |
| `_scrape_all` header | deleted | `src/crawler/DOCS.md`; `camoufox_lane` area |
| argparse `--concurrency-per-domain`/`--block-images` dest-resolution comments | deleted | `src/crawler/DOCS.md`; `camoufox_lane` area |

Tally: **12 blocks deleted as covered** (0 condensed to a DOCS.md Gotchas line as new content — the
guards below were additions to existing bullets, not new ones; 0 required new process-docs
substance).

## Guards folded into `src/crawler/DOCS.md` Gotchas

- `_build_configs()`'s `enable_stealth=True` reachability precondition ("no custom
  `crawler_strategy`/adapter passed to `AsyncWebCrawler`") was stated as plain prose in the deleted
  comment, not previously phrased as an actionable guard in Gotchas — added one line.
- The existing `magic=False` Gotcha line pointed at "the module's own comment before turning it
  on" — that comment is now deleted, so the reference was repointed to the `pipe_scraper_hardening`
  area instead of a dangling in-file pointer.

## Residual pass (same session, post-review)

First pass left non-conforming comments that weren't full derivation blocks: multi-line function
headers (2-5 lines, should be one) on `_curl_cffi_get`, `_fallback_fetch`, `_own_fallback_rescue`,
`_landed_url_from_result`, `_log_pipe_record`/`_log_pipe_camoufox_record`, `_scrape_one`,
`_scrape_one_camoufox`, `_build_configs`, `_extract_pipe_config_stamp`,
`scrape_urls_workflow`/`_scrape_all`; and full comment lines inside function bodies (the
`fallback_armed` comment inside `_extract_pipe_config_stamp`'s dict, the ts-stamp comment in
`_scrape_one`, the `acquisition_error` comment in `_scrape_one_camoufox`, two argparse comments in
`pipe_scraper.py`'s `__main__` block, and `pipe_scraper_constants.py`'s 3-line preamble). All
headers condensed to one line. Body comments triaged against `src/crawler/DOCS.md` and
`pipe_scrape_logger.py`'s schema comment specifically (narrower surface than the first pass, since
this is cleanup of the first pass's own leftovers, not a fresh sweep):

- `fallback_armed` comment → deleted, verbatim-covered by `pipe_scrape_logger.py`'s schema comment.
- ts-stamp comment in `_scrape_one` → deleted, verbatim-covered by the existing `src/crawler/DOCS.md`
  Gotchas bullet on `ts`/`_gate_domain` ordering.
- argparse `--concurrency-per-domain` comment → deleted; substance (engine-conditional default) was
  already in `src/crawler/DOCS.md`'s `pipe_scraper.py` Purpose paragraph, and the remainder
  (explicit value always wins) is ordinary argparse `default=` behavior, not a project-specific fact.
- `acquisition_error`-checked-first reasoning in `_scrape_one_camoufox` → genuinely NOT covered by
  `src/crawler/DOCS.md` or the schema comment — added to `src/crawler/DOCS.md`'s
  `pipe_scraper_acquisition.py` Engine-switch paragraph before deleting the comment.
- argparse `--block-images`/`--no-block-images` shared-`dest` resolution comment → genuinely NOT
  covered — added as a new `src/crawler/DOCS.md` Gotchas bullet (argparse resolves a shared dest's
  default from the FIRST `add_argument` call added, a real re-ordering trap) before deleting.
- `pipe_scraper_constants.py`'s 3-line preamble → deleted outright; `src/crawler/DOCS.md`'s own
  constants-module entry already carries the "rationale lives in DOCS.md, not per-constant" pointer.

## Verification

`tests/test_pipe_scraper.py` re-pointed to the new module locations for every moved symbol
(`pipe_scraper_config.BrowserConfig/CrawlerRunConfig/CacheMode/_build_configs/
_extract_pipe_config_stamp`, `pipe_scraper_constants.*`, `pipe_scraper_acquisition.
_fallback_fetch/_curl_cffi_get/_url_to_filename/AsyncSession/FALLBACK_FETCH_TIMEOUT_S/
try_scrape_camoufox`) — `AsyncWebCrawler` patches and all `_scrape_all(...)` calls needed no change
since both stayed in `pipe_scraper.py`. 35/35 `test_pipe_scraper.py` tests pass. Full suite (`pytest
tests/`): 182 passed, 10 failed — confirmed via `git stash` to be the identical pre-existing
failure set on this branch before this refactor touched anything (7 `test_query_logger.py` +
1 additional `test_query_logger.py` test not present when the "9 failed" baseline was last recorded
+ 2 `test_proxy_pool.py`; unrelated to `pipe_scraper`, no drift introduced by this change).
Repo-wide grep for every moved symbol name confirmed zero remaining live (import/attribute-access)
references outside the new modules and the re-pointed test file; the only surviving mentions are
prose comments in `pipe_scrape_logger.py` and a dev-local mirrored copy
(`dev/pipe_scraper_hardening/01_stealth_concurrency_probe.py`) that name a function by
`pipe_scraper.<name>` for origin-tracing purposes, not as executable references — left untouched
(out of scope, still correct at the function-name level).
`python -m src.crawler.pipe_scraper --help` exits 0 with an unchanged CLI surface.
