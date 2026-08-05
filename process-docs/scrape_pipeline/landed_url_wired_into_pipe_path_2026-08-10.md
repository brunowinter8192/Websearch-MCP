# Landed URL wired into the pipe-scraper path (2026-08-10)

Milestone 3 of 3 — the final piece of the requested-vs-landed URL effort; the `is_same_target`
primitive and its wiring into `src/scraper/scrape_url.py` were built in two earlier sessions of
this same area. This session did the same for `src/crawler/pipe_scraper.py`'s
`pipe_scrape_log.jsonl` — log only, no rendered-output half exists on this path (it writes files,
not chat text). `is_same_target` itself untouched, imported as-is (same cross-module pattern
`hash_config`/`extract_crawl4ai_diagnosis` already established for this path — see
`process-docs/pipe_scraper_hardening/` for why that log's schema already deviates field-by-field
from the ad-hoc one; the new fields had to fit that same reasoning).

## The complication: two fallback routes, both making `redirected_url` untrustworthy

Verified directly against the installed crawl4ai 0.9.2 source before relying on either claim
(both confirmed correct, independent of the brief that named them):

- **crawl4ai's own fallback** (`fallback_fetch_function=_fallback_fetch`, path a): when the
  browser result is flagged blocked, crawl4ai calls the fetch function and builds the result with
  `redirected_url=url` — the REQUESTED url, hardcoded (`async_webcrawler.py`, the
  `fallback_fetch_function` block). Any redirect curl_cffi's own fetch followed is invisible; the
  field positively (and wrongly, in general) asserts "no redirect happened."
- **pipe_scraper's own rescue** (`_own_fallback_rescue`, path b): the fetched HTML runs through
  crawl4ai's `raw://` pipeline. On a `raw:` scheme, `redirected_url` comes from `config.base_url`
  (`async_crawler_strategy.py`), which this module's `run_cfg` never sets — always `None` there.

Recording either forced value verbatim would fabricate a fact — exactly the class of error the
2026-08-05 content-judgment removal (this same area, `scrape_url.py`'s own history) already
eliminated once.

## Decision: (null, null) on both fallback routes, tri-state same_target

`_landed_url_facts(url, result, diagnosis)` returns real `(landed_url, is_same_target(...))` only
when `diagnosis["crawl4ai_fallback_fetch_used"]` is not True; otherwise `(None, None)`. Path b never
calls it at all — its call site passes `(None, None)` directly, since `_own_fallback_rescue`'s
`raw://` conversion result never carries a meaningful `redirected_url` by construction.

Consequence: `same_target` on this log is TRI-STATE (`True`/`False`/`None`), not the always-bool
field milestone 2 gave `scrape_log.jsonl`. This is a genuine, justified divergence, not an
inconsistency between two opinions on the same question — checked afterward that `scrape_url.py`
wires no `fallback_fetch_function` at all on the ad-hoc path, so the ad-hoc path structurally never
faces this ambiguity; the pipe path does, by construction of its two-fallback-route design. Field
NAMES stayed identical (`landed_url`, `same_target`) across both logs for cross-log comparability;
only the value space differs, and only because the underlying data source genuinely differs.

## Verification

25 tests in `tests/test_pipe_scraper.py` (was 21): plain-success-route with a real deviating
redirect (`landed_url` recorded, `same_target=False`), plain-success-route with no redirect
(`same_target=True` via `is_same_target`'s missing-input rule — noted afterward that this
particular test's name promises the identical-URL case but its fake result actually leaves
`redirected_url` unset, so what it exercises is the absent-URL path through the same True result;
both shapes are still covered overall, via the real run below and the existing fake-result
defaults — not fixed this session, flagged only), crawl4ai's-own-fallback route (`(None, None)`,
`crawl4ai_fallback_fetch_used=True` confirmed alongside), and pipe_scraper's-own-rescue route
(`(None, None)`, `pipe_fallback_used=True` confirmed alongside).

Real CLI run, 5 URLs (`./venv/bin/python -m src.crawler.pipe_scraper --url-file ... --output-dir
...`), all `outcome=ok`, plain success route throughout (neither fallback exercised by these 5 —
both fallback-route decisions are pinned by the fake-crawler unit tests instead, not this run):

| requested | landed | same_target | http_status |
|---|---|---|---|
| `example.com/` | identical | `true` | 200 |
| `rfc-editor.org/info/rfc2616/` | identical | `true` | 200 |
| `rfc-editor.org/rfc/rfc2616` | `rfc-editor.org/info/rfc2616/` | `false` | 302 |
| `docs.anthropic.com/en/api/getting-started` | `platform.claude.com/docs/en/api/overview` | `false` | 301 |
| `rfc-editor.org/rfc/rfc7231` | `rfc-editor.org/info/rfc7231/` | `false` | 302 |

Full suite: `9 failed, 174 passed`. `FAILED` list diffed against the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py`) — identical, no drift. `config`/`config_hash`
(`_extract_pipe_config_stamp`) confirmed untouched — the two new fields are per-URL results, not
configuration, and were deliberately kept out of that stamp.
