# Scrape Pipeline — Stamping Every Scrape Record With Its Producing Config

*Dated entry — historical record of the investigation; the live current state is the source code, not this file.*

## Problem Observed

As of 2026-08, `src/logs/scrape_log.jsonl` recorded a rich RESULT side per scrape (own `outcome`/
`garbage_type`, crawl4ai's own diagnosis) but no INPUT side — which configuration produced that
result. The intent behind the log is to accumulate evidence, over weeks of ordinary real traffic,
about which configuration yields which outcomes, instead of running artificial sweeps over a
hand-picked domain set. That only works if every record carries the config that produced it — a
record without the stamp is permanently unusable for that purpose once written.

## Design — Hash for Grouping, Full Dict for Reading

Two requirements from the same field: (1) group records by "same config" cheaply, (2) see what that
config was without the source. A bare hash gives (1) not (2); a full dump gives (2) and makes (1)
awkward (comparing N keys by hand). Resolved by writing both, as sibling top-level fields:
`config_hash` (10 hex chars, sha256 over the sorted-key JSON of the config dict — cheap equality
grouping) and `config` (the full flat dict — one nesting level, same pattern as the pre-existing
`timings_ms` field, not a deep blob).

## Which Parameters Are Load-Bearing

Read `try_scrape`'s `BrowserConfig(...)`/`CrawlerRunConfig(...)`/`PruningContentFilter(...)`
constructor calls in `src/scraper/scrape_url.py`. Decision rule: every kwarg this codebase
*explicitly* passes is load-bearing by construction — it's a value the project chose to tune, hence
behavior-relevant. `crawl4ai`'s full `CrawlerRunConfig.to_dict()` was checked and rejected as the
stamp source — it dumps ~92 keys (confirmed via `venv/lib/python3.14/site-packages/crawl4ai` on the
installed 0.9.2), almost all untouched library defaults with no signal, and objects like
`scraping_strategy`/`table_extraction` that aren't even scalar-serializable. A diff-against-a-fresh-
default-CrawlerRunConfig() approach was also tried and rejected: several of our explicit kwargs
(`page_timeout=60000`, `cache_mode=CacheMode.BYPASS`, `max_retries=0`) happen to already coincide
with the library's own current defaults, so a diff would silently omit them from the stamp — and
worse, an unrelated crawl4ai version bump that changes an untouched default elsewhere would then
shift which fields appear in the stamp, with no code change on our side. Explicit-kwargs-read-back
avoids both problems.

Excluded `verbose` (both configs) — pure logging, no scrape-behavior effect. `excluded_selector`
(426 chars, `COOKIE_CONSENT_SELECTOR`, static, source-visible, rarely changes) is recorded as an
8-hex-char sha256 hash rather than verbatim — still flags a future change via a differing hash,
without repeating a near-constant 426-byte string on every line.

## Fields Captured

`extract_config_stamp(browser_config, adapter, crawler_strategy, run_config)` in `scrape_url.py`:
`headless`, `enable_stealth`, `adapter` (class name), `crawler_strategy` (class name), `magic`,
`wait_until`, `page_timeout_ms`, `max_retries`, `cache_mode` (`.value`), `content_filter` (class
name), `content_filter_threshold`, `excluded_selector_hash`. Called right after `run_config` is
built, BEFORE the `try` block — so `meta["config"]` is set in `_empty_meta` and present on every
`try_scrape` return path, including total network/browser failure, since the config objects exist
before the call is even attempted (unlike the crawl4ai diagnosis fields from the prior milestone,
which need a real result object).

`build_config_record(scrape_config, max_content_length)` in `scrape_url_workflow` merges that stamp
with the two post-processing params only the orchestrator knows: `max_content_length` (per-call arg)
and `MIN_CONTENT_THRESHOLD` (module constant). `hash_config(config)` derives the grouping key.
Both fields read values off real objects/params — never a hand-typed literal duplicate — so a future
config change is picked up automatically by whichever line already reads that attribute.

## Defect Found in Review, and the Fix

Initial `build_config_record` used `meta.get("config", {})` — if `try_scrape`'s "config is always
set" invariant were ever to break (a future refactor moves the stamp computation, a new early-return
path is added upstream of it, etc.), the caller would silently receive `{}`, `build_config_record`
would merge in just the two post-processing fields, and `hash_config` would produce a perfectly
normal-looking 10-char hash over that near-empty dict. A later reader grouping by `config_hash`
would get a bucket whose `config` says nothing about the browser, filter, or wait strategy — with no
signal that anything was missing, indistinguishable from a real (if sparse) config.

Fixed to check falsiness explicitly (`meta.get("config")`, defaulting to `None`, not `{}`) and
return `{"config_incomplete": True, "max_content_length": ..., "min_content_threshold": ...}` on the
missing/falsy case — visible in the record itself, and it also lands in a distinct `config_hash`
bucket automatically (the marker changes the hash), so both the full-dict reader and the
grouping-by-hash reader get the signal that something broke, without recomputing anything.

## Verification

Real before/after on the same static URL (`https://www.rfc-editor.org/rfc/rfc2616`), isolated via
`git stash`/`stash pop` around the change:

- Pre-change line: 656 bytes. Post-change line: 1103 bytes — **stamp costs 447 bytes/record**
  (`config` + `config_hash` together). Framed against log volume: ~160 records over ~2 weeks of real
  use (a slow-growing log, not a high-volume stream) — 447 bytes/record is ~70KB accumulated over
  that same span, negligible against the log's own stated purpose (comparing config-vs-outcome
  across weeks).
- Every pre-existing field (`outcome: "ok"`, `garbage_type: null`, `bytes_returned: 12168`,
  `bytes_raw_markdown: 540353`, `http_status: 302`, `published_date: "1999-06-01"`, all 5
  `crawl4ai_*` fields from the prior milestone) identical byte-for-byte before/after — confirmed via
  field-by-field diff, not eyeballing.
- Real populated stamp on a successful scrape: `config_hash: "7ac9eefa4b"`,
  `config: {"headless": true, "enable_stealth": true, "adapter": "UndetectedAdapter",
  "crawler_strategy": "AsyncPlaywrightCrawlerStrategy", "magic": true, "wait_until": "load",
  "page_timeout_ms": 60000, "max_retries": 0, "cache_mode": "bypass",
  "content_filter": "PruningContentFilter", "content_filter_threshold": 0.48,
  "excluded_selector_hash": "360593b1", "max_content_length": 15000,
  "min_content_threshold": 200}`.
- Re-ran the same scrape after the `config_incomplete` fix — identical `config_hash`/`config`
  (the fix only changes behavior on the falsy-input path, never exercised by a normal successful
  scrape) — confirms the safeguard didn't perturb the real path.

NOT verified: the `config_incomplete` branch actually firing against a live `try_scrape` invariant
break — it was only exercised directly against `build_config_record(None, ...)` /
`build_config_record({}, ...)` as isolated calls, not through a genuine `try_scrape` failure mode
that reaches it (by design, no such path currently exists — that's the point of the invariant).
`tests/test_scrape_url.py` (10 cases) unaffected, no new regression case added for
`config_incomplete` since there's no code path today that can trigger it through `try_scrape`.

## Sources

None — internal instrumentation change and internal code review, no external sources.
