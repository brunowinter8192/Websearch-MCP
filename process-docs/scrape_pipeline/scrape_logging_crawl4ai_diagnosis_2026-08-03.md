# Scrape Pipeline — Surfacing crawl4ai's Own Anti-Bot Diagnosis in the Scrape Log

*Dated entry — historical record of the investigation; the live current state is the source code, not this file.*

## Problem Observed

As of 2026-08, crawl4ai (this project pins 0.9.2) performs its own anti-bot detection internally and
reports it on the `CrawlResult` object — `success`, `error_message`, `crawl_stats` — but
`src/scraper/scrape_url.py`'s `try_scrape` discarded all of it, classifying content purely via its own
pattern-matching `is_garbage_content()`. On an empty/blocked scrape the scrape log recorded only our own
verdict (`outcome`, `garbage_type`), with no way to distinguish "crawl4ai's detector says the site
blocked us, and names which system" from "we got content but our own classifier rejected it".

## Investigation

Verified field names against the INSTALLED crawl4ai 0.9.2 (not trusted from any external doc) by reading
`venv/lib/python3.14/site-packages/crawl4ai/async_webcrawler.py:399-646` and
`CrawlResult.model_fields` in `models.py`. Confirmed on the real source:

- `result.success: bool`, `result.error_message: str` — real `CrawlResult` fields.
- `result.crawl_stats: dict | None`, built at `async_webcrawler.py:411-417` and populated at the end of
  the anti-bot retry loop (`:634`/`:646`): `attempts` (int, total browser attempts across
  proxies/retries), `retries` (int), `proxies_used` (list[dict] — proxy/status_code/blocked/reason per
  attempt), `fallback_fetch_used` (bool), `resolved_by` (`"direct"` | `"proxy"` | `"fallback_fetch"` |
  `None`).
- With this project's `CrawlerRunConfig` (`CacheMode.BYPASS`, `check_robots_txt` defaults `False`,
  neither overridden), execution always enters the fetch branch (`:380`) that populates `crawl_stats` —
  so for every non-exception `arun()` return, `crawl_stats` is a real dict, never `None`. Only
  `try_scrape`'s own `except Exception` branch (no `result` object ever obtained — network/launch
  failure before crawl4ai could build one) leaves the new fields `null`.
- The block-message format matches crawl4ai's own construction exactly:
  `f"Blocked by anti-bot protection: {_block_reason}"` (`async_webcrawler.py:633`).

## Decision — Record Only, Never Act On It

Deliberately NOT wired into `outcome`/`garbage_type` or any branching. crawl4ai's own block detector has
documented false positives on its own issue tracker (issue #2058: a legitimate 378-byte `file://` page
failing its `minimal_text` structural tier; issue #1974: a `<frameset>` page, 612 bytes, real content
inside the frame, misclassified as `"Blocked by anti-bot protection: Structural: minimal_text on small
page"`) — crawl4ai's own code special-cases its detector internally for exactly this reason. Treating
`error_message` as a verdict rather than an information source would have imported those false positives
directly into this project's classification. The new fields exist purely as forensic signal for a later
reader of the JSONL log.

## Fields Added

`src/scraper/scrape_url.py`: new `extract_crawl4ai_diagnosis(result) -> dict`, called in `try_scrape`
right after `status_code`/`content_type` are read off the result, before the `http_error` short-circuit
and before any garbage-classification branching — so the fields are captured on every path that ever
obtained a `result` object. Prefixed `crawl4ai_` (not bare `success`/`error_message`) to keep them
visually unambiguous against this module's own `outcome`/`garbage_type` verdict fields in the flat JSONL
record — the prefix is the signal that these came from the library, not from `is_garbage_content()`.

Added to both `log_scrape({...})` call sites in `scrape_url_workflow` (empty/garbage branch, `ok`
branch): `crawl4ai_success`, `crawl4ai_error_message`, `crawl4ai_attempts`, `crawl4ai_resolved_by`,
`crawl4ai_fallback_fetch_used`. `crawl_stats["proxies_used"]` and `crawl_stats["retries"]` deliberately
NOT surfaced — out of scope for this milestone (the prompt's "at least" list), and `proxies_used`'s
list-of-dicts shape doesn't fit the flat-field style of the existing record.

## Verification

Real before/after on the same static URL (`https://www.rfc-editor.org/rfc/rfc2616`), two separate CLI
runs (`./venv/bin/python cli.py scrape_url <url>`) either side of the code change:

- Pre-change record: `outcome: "ok"`, `garbage_type: null`, `bytes_returned: 12168`,
  `bytes_raw_markdown: 540353`, `http_status: 302`, `published_date: "1999-06-01"`.
- Post-change record: identical on every one of those fields, byte-for-byte. Only
  `timings_ms.total_wall` differed (2298ms vs 2266ms — ordinary run-to-run wall-clock jitter, not a
  behaviour change) and `ts`/`content_path` (expected, timestamp-derived).
- New fields, real populated values on this successful, unblocked scrape:
  `crawl4ai_success: true`, `crawl4ai_error_message: null`, `crawl4ai_attempts: 1`,
  `crawl4ai_resolved_by: "direct"`, `crawl4ai_fallback_fetch_used: false`.

NOT verified: the block-path field mapping (a genuinely anti-bot-blocked page, e.g. DataDome/Cloudflare)
— confirmed by source-read of `async_webcrawler.py` only, no live blocked run performed this session.
`tests/test_scrape_url.py` (10 cases, pure-function regression guard on `is_garbage_content` /
browser-launch classification) unaffected — no new test cases added since the change is additive-only
with no new branching to guard.

## Sources

None — internal instrumentation change; crawl4ai issue numbers (#2058, #1974) referenced as they were
supplied in the originating task brief, not independently re-fetched this session.
