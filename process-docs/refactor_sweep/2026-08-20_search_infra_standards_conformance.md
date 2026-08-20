# Full comment-rule conformance sweep — search + crawler + scraper logging infra (2026-08-20)

Phase-2 milestone continuing the `refactor_sweep` area: full comment-rule conformance (three
comment types only; no docstrings) across `src/search/` (all modules + all 14 engines +
`base.py`), `src/crawler/crawl_site.py`, the two log-schema modules
(`src/crawler/pipe_scrape_logger.py`, `src/scraper/scrape_logger.py`), and `src/log_janitor.py`.
Zero code changes — comments/docstrings only, verified by an unchanged 182-passed/10-failed
baseline. `src/news/` is a separate, already-completed area — untouched here.

## Method

Checked every non-conforming block against the owning `DOCS.md` first (the primary source for this
codebase — already dense from prior sessions), then against `process-docs/search_pipeline/` (the
main covering area for this sweep) where DOCS.md didn't fully carry a claim. Constants get ZERO
comment lines (not even a one-line label), per the rule already established in the `pipe_scraper.py`
split — module-specific rationale lives in the owning DOCS.md, not per-constant in code. Every
multi-line function/class header condensed to one line; every in-body comment deleted after
confirming coverage; both `rate_limiter.py` docstrings (class + method) converted to one-line
comments above their target (`__doc__` usage grepped first — zero hits on `RateLimiter` or
`acquire`, only unrelated dev-script module-docstrings feeding their own `argparse` description).

## Result: overwhelmingly category 3 (covered) — one genuinely uncovered pocket found

Nearly every block across ~26 files was already recorded in the owning DOCS.md (the `pipe_scraper`/
`scrape_url`/`camoufox_scrape` sessions had already set the precedent of moving derivation content
there). Three exceptions needed real work:

**1. `status.py`'s per-status trailing comments (the status-taxonomy semantics)** — genuinely
uncovered: `src/search/DOCS.md`'s `status.py` entry only gave a bucket count ("17 total: 5 legacy +
5 EMPTY + 3 TIMEOUT + 4 ERROR"), not the per-constant meaning. Moved the full breakdown (all 17
names + their one-line meanings) into that DOCS.md entry before deleting the code comments.

**2. `query_logger.py`'s ~78-line module-level schema comment** — DOCS.md's Purpose paragraph
covered the CONCEPTS (three record types, `search_key` join semantics, the 14-day-pruning limit,
non-correlation with `scrape_log.jsonl`) but not the literal per-record-type field lists (`engine_run`'s
`engines.<name>` shape, `workflow_summary`'s `engines_excluded`/`bottleneck_engine`, `drilldown`'s
`cache_status` 3-value enum + `engine_in_pools`/`urls` semantics). Expanded the DOCS.md Purpose
paragraph into a per-record-type field breakdown before deleting the code comment.

**3. `search_web.py`'s `ENGINE_WATCHDOG_OVERRIDE`/`ENGINE_MAX_RESULTS` per-engine trailing
comments** — genuinely uncovered anywhere: DOCS.md lists the override VALUES
(`open_library 6.0, semantic_scholar 5.0, crossref 6.0, startpage 6.0, brave 6.0`) but not the
per-engine REASONING; the `search_pipeline` area's own master reference entry (itself stale — still
references a `filter_modes.py` module that no longer exists) covers only 3 of the 5 override entries
and none of the 14 `ENGINE_MAX_RESULTS` entries. This is the one substance that had no home —
recorded below.

### `ENGINE_WATCHDOG_OVERRIDE` (search_web.py) — per-engine reasoning as of the code comments this session removed

| Engine | Override | Reasoning |
|---|---|---|
| `open_library` | 6.0s | Server-dominated 1.4-5.8s latency; the 3.6s default caused ~35% timeouts |
| `semantic_scholar` | 5.0s | CSR hydration 0.5-2.5s + `go_to` budget, post-DOM-drift fix |
| `crossref` | 6.0s | API response 1-5s range; 3.6s httpx cap raced the watchdog deadline |
| `startpage` | 6.0s | 2-step homepage+submit flow measured 2.7-4.1s (`dev/search_pipeline/25_startpage_probe.py`); 3.6s too tight |
| `brave` | 6.0s | Probe latency max ~3.9s (`dev/search_pipeline/26_brave_probe.py`); 3.6s too tight, same reasoning as startpage |

`bing`/`yandex`/`marginalia` deliberately carry NO override entry (already documented in DOCS.md):
all three probed well under the 3.6s default.

### `ENGINE_MAX_RESULTS` (search_web.py) — per-engine ceiling source, from `max_results_probe_20260507_024429.md`

| Engine | Max | Source |
|---|---|---|
| `google` | 100 | server cap via `num=` URL param; DOM renders ~9-11 regardless |
| `duckduckgo` | 10 | no count param; post-fetch DOM slice only |
| `mojeek` | 10 | no count param; post-fetch DOM slice only |
| `lobsters` | 20 | no count param; pool is query-dependent |
| `openalex` | 200 | `per_page=` API param; documented max 200 |
| `crossref` | 200 | `rows=` API param; documented max 1000, practical 200 |
| `stack_exchange` | 100 | `pagesize=` API param; hard cap 100 |
| `semantic_scholar` | 10 | 10/page hardcoded by SS UI; no override param |
| `open_library` | 100 | `limit=` API param; supports 1000+ but latency server-dominated (1.4-5.8s at 100) |
| `startpage` | 10 | no count param; 10/page fixed by DOM (`dev/search_pipeline/25_startpage_probe.py`) |
| `brave` | 10 | no count param; 10/page fixed by DOM (`dev/search_pipeline/26_brave_probe.py`) |
| `bing` | 10 | no count param; 10/page fixed by DOM (`dev/search_pipeline/28_bing_probe.py`) |
| `yandex` | 10 | no count param; 10/page fixed by DOM (`dev/search_pipeline/29_yandex_probe.py`) |
| `marginalia` | 10 | `count=` API param (`dev/search_pipeline/30_marginalia_probe.py`) |

Not folded into DOCS.md itself — this table is dense probe-report data, not module-map-level prose;
`src/search/DOCS.md`'s own `search_web.py` entry keeps citing the values inline as it already did,
this entry is where the per-value evidence now lives.

## Guard-type Gotchas added (not new investigation, existing landmines surfaced by the sweep)

- `src/search/DOCS.md`: `browser.py`'s `_FALSY_ENV_VALUES` landmine (a bare `bool(os.environ.get(...))`
  would invert `WEBSEARCH_HEADLESS=0`/`=false`) — was previously only in the code comment and
  `process-docs/browser_posture/`, now also a standing Gotcha.
- `src/search/engines/DOCS.md`: `crossref.py`/`open_library.py`'s `httpx` timeout is hand-aligned
  with `search_web.py`'s `ENGINE_WATCHDOG_OVERRIDE` for that engine, not derived from it — a
  silent-decoupling risk if one is tuned without the other.

## Two dangling-reference fixes (DOCS.md pointed at code comments this sweep deleted)

- `src/scraper/DOCS.md`'s `scrape_logger.py` entry said historical outcome values were "named
  explicitly in the schema comment" — reworded to "named explicitly here" (the same sentence already
  names them, the phrase just needed to stop pointing at the deleted code comment).
- `src/search/search_web.py`'s `_build_query_log_entry` header said "see query_logger.py's schema
  comment" — deleted along with the rest of that function's now-redundant multi-line header (the
  `search_key` join semantics this pointed at are fully covered by this session's own
  `query_logger.py` DOCS.md expansion above).

## Verification

Full suite (`pytest tests/`): 182 passed, 10 failed — the exact standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py` + 1 additional `test_query_logger.py` test),
confirmed identical before and after this sweep. `test_engine_with_timing_*`'s failure mode
(mock exposes `.search` not `.search_with_reason`) reproduces identically post-sweep — this sweep
touched zero logic, only comments, so no behavior change was possible by construction; the test run
is a confirmation, not a discovery. `__doc__` grepped repo-wide before removing `rate_limiter.py`'s
two docstrings — no reference to either found outside unrelated dev-script module-docstrings.
