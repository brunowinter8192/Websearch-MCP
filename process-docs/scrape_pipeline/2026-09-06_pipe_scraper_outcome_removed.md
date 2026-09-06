# pipe_scraper's guessed outcome classification removed (2026-09-06)

Applies the same fact-vs-verdict line `process-docs/search_pipeline/2026-09-05_guessed_verdict_
removal.md` drew to the search engines, and `content_judgment_removal_2026-08-05.md`/
`status_gate_removal_evidence_2026-08-05.md` drew to the ad-hoc scrape path, to the batch pipe path:
`src/crawler/pipe_scraper*.py`'s per-URL `outcome` field (`ok`/`empty`/`http_error`/`waf_429`/
`error`).

## Problem

Four of the five `outcome` values were verdicts computed on top of facts the same record already
carried: `waf_429` on `status_code == 429`, `http_error` on `status_code >= 400`, `empty` on a byte
count below an invented 100-byte threshold, `ok` asserting the page was good on no evidence at all.
A real case on record: 13 pages came back at 9738 bytes of pure navigation chrome plus 51 lines
reading `Loading...`, were classified `ok` on that byte count alone, and went into the RAG index
that way — the exact failure mode `content_judgment_removal_2026-08-05.md` had already found and
fixed on the ad-hoc path, present unfixed on this one.

## Method: branch-by-branch fact check before deleting anything

Every classification branch in `pipe_scraper_acquisition.py` (`_scrape_one`, `_scrape_one_camoufox`,
`_own_fallback_rescue`) was checked against the record's own already-logged fields before its code
was touched:

- `waf_429`/`http_error` (both engines, `status==429` / `status>=400`) → `http_status` already
  carried the exact code. Pure re-derivation, deleted outright, no new field.
- `empty`/`ok` (both engines plus `_own_fallback_rescue`, `byte_count` vs. `EMPTY_THRESHOLD_BYTES`)
  → `bytes` already carried the exact count. Pure re-derivation, deleted outright, no new field.
- `_own_fallback_rescue`'s two `'error'` returns (curl_cffi fallback itself failed) → already fully
  described by `pipe_fallback_used=True`/`pipe_fallback_resolved=False` plus `http_status=None`/
  `bytes=0`, all already logged. Deleted outright, no new field — the tuple simply dropped its
  leading `outcome` element.
- `_scrape_one_camoufox`'s `outcome='error'` on `meta.get('acquisition_error')` — the ONE branch
  that did NOT already have its distinguishing fact in the record. `try_scrape_camoufox` (out of
  scope, untouched) already computes `acquisition_error` (`"budget_exhausted"`/`"browser_missing"`/
  `"exception"`) on its own `meta` dict, but `_log_pipe_camoufox_record` never logged it — the
  branch collapsed all three real, distinct reasons into the single string `"error"`. Fixed in the
  required order: the fact was added to `_log_pipe_camoufox_record`'s JSONL output FIRST
  (`"acquisition_error": meta.get("acquisition_error")`), then the branch was deleted. No new
  computation — the fact already existed, it just wasn't wired through to the log.

Six branches removed total, one new logged field added, zero new computation anywhere.

## What else went with it

`EMPTY_THRESHOLD_BYTES` (`pipe_scraper_constants.py`) and its `"empty_threshold_bytes"` config-stamp
key (`pipe_scraper_config.py`) had no reason to exist once nothing computed against them — removed.
`outcome` was dropped from every return dict (`_scrape_one`, `_scrape_one_camoufox`, `_scrape_all`'s
raw-exception placeholder), the JSONL schema (`pipe_scraper_records.py`), the `/tmp` report table
column, and the console summary's "N ok, M errors" line (all `pipe_scraper_report.py`).

## The console summary, redesigned to state facts only

`_print_summary` can only draw on the same four fields every return dict carries: `url`, `wall_ms`,
`bytes`, `status_code`. The replacement prints a raw HTTP-status histogram (each URL's own observed
code, plus a `no_status` bucket for a URL our own code never got a status for at all) and a
zero-byte count — both plain tallies of already-recorded facts, nothing inferred about what a
status/byte-count combination means. Real output against a 3-URL mixed run (a normal 200, an
`httpbin.org` 404, and an unresolvable domain):

```
Scraped 3 URLs in 3s — status: 200=1, 404=1, no_status=1 — 1 returned 0 bytes
```

The `/tmp` report lost its `outcome` column; `status`/`bytes`/`wall_ms`/`url` are unchanged.

## A deliberate asymmetry left in place: the return dict stays thin

`acquisition_error` was added to the JSONL log (the rich, engine-specific fact store this project
already uses — chromium's own `crawl4ai_*`/`pipe_fallback_*` fields live only there too, never in
the return dict). It was NOT also added to `_scrape_one_camoufox`'s returned per-URL dict, which
stays `{url, wall_ms, bytes, status_code}` for both engines. Reasoning: the chromium engine's
richest failure fact (a caught hard exception) is likewise invisible in ITS OWN return dict, visible
only via the JSONL log's `pipe_fallback_used`/`crawl4ai_success=None` combination — matching that
existing asymmetry was judged more consistent than special-casing camoufox's return dict to carry
one extra field the chromium engine has no equivalent slot for.

## Scope held

`src/scraper/chromium_scrape.py`/`camoufox_scrape.py` (the ad-hoc single-URL path) carry their own,
separate `outcome` field and were not touched — a deliberately deferred, separate task. Every dev/
script found importing from `src.crawler.pipe_scraper*` or reading `pipe_scrape_log.jsonl` was
checked: `dev/news_pipeline/prod_scrape_smoke.py` imports `scrape_urls_workflow` but never reads
`outcome` from its return value (derives its own regwall verdict from output file bytes instead) —
unaffected. `dev/lane_choice/01_backfill_pairs.py`/`04_lane_metrics.py` read `outcome` from
`src/logs/scrape_log.jsonl`, the SEPARATE ad-hoc-path log — unaffected, out of scope. Five more dev
scripts (`dev/pipe_scraper_hardening/01_stealth_concurrency_probe.py`,
`dev/scrape_pipeline/07_pipe_scrape_eval.py`/`p1_pipe_scraper.py`,
`dev/news_pipeline/02b_coindesk_scrape_fresh_context.py`, `dev/camoufox_lane/01_launch_timeout_
probe.py`) all carry their own independent, copied-not-imported `outcome`/`EMPTY_THRESHOLD_BYTES`
logic — none import the touched modules, none affected.

## Verification

Full suite: 346 passed (was 347 — one test deleted outright,
`test_extract_pipe_config_stamp_carries_empty_threshold_off_the_constant`, since its entire subject,
the constant and the stamp key, no longer exist; roughly a dozen more had only their `outcome`
assertions replaced with the underlying `http_status`/`bytes` fact, same test, same subject,
rewritten in place). Real run against `https://example.com/`, `https://httpbin.org/status/404`, and
an unresolvable test domain (`WEBSEARCH_PIPE_SCRAPE_LOG_PATH` pointed at a scratch file): console
line shown above; `/tmp/example_com_scrape_report.md` rows carried plain `status`/`bytes`/`wall_ms`/
`url`, no verdict column; the three JSONL records carried `http_status`/`bytes`/`crawl4ai_success`/
`crawl4ai_error_message`/`crawl4ai_resolved_by`/`crawl4ai_fallback_fetch_used`/`pipe_fallback_used`/
`pipe_fallback_resolved`/`landed_url`/`config_hash`/`config` and no `outcome` key at all — including
the unresolvable-domain record, whose real crawl4ai `ERR_NAME_NOT_RESOLVED` error message is present
verbatim as `crawl4ai_error_message`, the actual fact a caller needs, where the old schema would
have said only `"outcome": "error"`.
