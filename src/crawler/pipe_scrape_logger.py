# INFRASTRUCTURE
import json
import logging
import os
from pathlib import Path

# From src/log_janitor.py: lazy 14-day prune on write, same mechanism as scrape_log.jsonl
from src.log_janitor import maybe_prune_jsonl

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path(__file__).parent.parent.parent / "src" / "logs" / "pipe_scrape_log.jsonl"

# Record schema (one record per URL per pipe_scraper run):
# {
#   "ts": str (ISO-8601 UTC, millisecond precision) — REQUEST START: stamped after the per-domain
#         semaphore/pacing gate, right next to _scrape_one's own t0, not when the URL's coroutine
#         was queued (asyncio.gather starts every _scrape_one at once, so a pre-gate ts would be
#         near-identical across an entire run's hundreds of records — that bug existed and was
#         fixed; do not move this stamp back above the gate). Not completion time either — that is
#         ts + wall_ms.
#   "run_id": str (uuid4, shared by every record of one scrape_urls_workflow invocation) — a
#             capture run writes hundreds of records at once; this is the field that separates
#             one run's records from another's without re-parsing timestamps/config.
#   "url": str,
#   "domain": str,                        # urlparse(url).netloc — groups records without re-parsing url
#   "outcome": "ok" | "waf_429" | "http_error" | "empty" | "error",
#   "http_status": int | null,
#   "bytes": int,
#   "wall_ms": int,                        # NOTE: on a record where pipe_fallback_used is True, this
#             includes the FULL failed browser attempt PLUS the curl_cffi fallback fetch time — not
#             just the fallback's own cost. Failure records got systematically longer once the
#             fallback path landed (browser-cap + HTTP-cap, not just browser-cap); nothing else in
#             the schema marks this — a time-distribution analysis across a log spanning the
#             before/after boundary must cross-check pipe_fallback_used, not read the wall_ms jump
#             alone as a slowdown.
#   "crawl4ai_success": bool | null,       # crawl4ai's OWN result.success; null on pre-result exception.
#   "crawl4ai_error_message": str | null,  # verbatim, informational only — the library's own
#                                           # anti-bot detector has documented false positives, never
#                                           # acted on, same posture as scrape_log.jsonl
#   "crawl4ai_attempts": int | null,
#   "crawl4ai_resolved_by": str | null,
#   "crawl4ai_fallback_fetch_used": bool | null,  # These 5 crawl4ai_* fields describe CRAWL4AI'S OWN
#             fallback_fetch_function mechanism ONLY (invoked internally by crawl4ai when the browser
#             returns a non-exception result that is_blocked() flags — e.g. HTTP 403/503 block page,
#             HTTP 200 + near-empty body). They do NOT cover pipe_scraper's own except-block rescue
#             (see pipe_fallback_used/pipe_fallback_resolved below) — that is a SEPARATE mechanism for
#             a case crawl4ai's own fallback cannot reach at max_retries=0 (the browser call raising
#             outright, e.g. a navigation timeout — no crawl_result ever forms, so crawl4ai's own
#             diagnosis fields stay null on that path, correctly: there is no real crawl4ai diagnosis
#             to report). Never conflate the two mechanisms when reading this log.
#   "pipe_fallback_used": bool,            # pipe_scraper's OWN curl_cffi (impersonate="chrome") rescue
#             was attempted, from _scrape_one's except block — always False unless the browser call
#             raised. Default False on every record (including all pre-this-milestone ones logically)
#             for the same cross-config-change comparability reason as crawl4ai_fallback_fetch_used.
#   "pipe_fallback_resolved": bool,        # curl_cffi returned a genuine HTTP 200 with a body — this
#             describes the FETCH succeeding, NOT whether that body converted into usable markdown.
#             The two CAN legitimately disagree: resolved=True + outcome="empty" means curl_cffi got a
#             real 200 but the raw://-pipeline markdown conversion produced too little content to pass
#             EMPTY_THRESHOLD_BYTES — that is not a contradiction, read it as "fetch worked, content
#             didn't". False means curl_cffi itself failed/timed out/returned non-200 — this record's
#             http_status is then null, never a faked 200 (see pipe_scraper._own_fallback_rescue).
#             Three readable states via (used, resolved): browser succeeded (False, False); pipe's own
#             fallback rescued it (True, True); everything failed (True, False).
#   "landed_url": str | null,              # crawl4ai's result.redirected_url, RAW/unnormalized —
#             recorded ONLY from the plain successful browser route (neither fallback engaged).
#             null on BOTH fallback routes — see same_target below for why.
#   "same_target": bool | null,            # src/scraper/scrape_url.py's is_same_target(url,
#             landed_url), evaluated at write time. TRI-STATE here, unlike scrape_log.jsonl's
#             ad-hoc-path same_target (always a bool there) — null means "not measurable on this
#             record's route", never "confirmed same". Two routes force (null, null):
#             (a) crawl4ai's OWN fallback_fetch_function (crawl4ai_fallback_fetch_used=True):
#                 verified in the installed crawl4ai 0.9.2 source (async_webcrawler.py) that on
#                 this route redirected_url is hardcoded to the ORIGINAL requested url regardless
#                 of what curl_cffi's own fetch actually followed — recording it at face value
#                 would report a fabricated "no redirect", exactly the class of error
#                 content_judgment_removal_2026-08-05.md (src/scraper/scrape_url.py's own history)
#                 already eliminated once.
#             (b) pipe_scraper's own rescue (pipe_fallback_used=True): the raw:// pipeline this
#                 route runs through only ever reports redirected_url=config.base_url (verified in
#                 crawl4ai's async_crawler_strategy.py), which this module never sets — always
#                 None, carrying no real signal either way.
#             Only the plain successful browser path (both pipe_fallback_used=False and
#             crawl4ai_fallback_fetch_used is not True) gets a real True/False verdict.
#             Absent by definition on every record written before these two fields were added —
#             read that absence as "predates the field," not as "no redirect happened" (same
#             convention as scrape_log.jsonl's own landed_url/same_target addition).
#   "config_hash": str,                    # first 10 hex chars of sha256(sort_keys JSON of "config") —
#             groups records that ran under the SAME config. It is NOT a stable identity across
#             schema versions: it changes whenever ANY stamped value changes, including when a
#             field is ADDED to or removed from the stamp itself (the added/removed field changes
#             the JSON that gets hashed even if every other value is untouched). A hash change
#             therefore does not by itself prove the running config changed — check "config" for
#             what actually changed before concluding that.
#   "config": {                            # read off the real BrowserConfig/CrawlerRunConfig
#                                           # objects + this module's own pacing constants — see
#                                           # pipe_scraper._extract_pipe_config_stamp
#     "headless": bool, "enable_stealth": bool,
#     "wait_until": str, "page_timeout_ms": int, "delay_before_return_html_s": float,
#     "cache_mode": str,
#     "simulate_user": bool, "override_navigator": bool, "magic": bool,
#     "remove_consent_popups": bool,
#     "fallback_armed": bool,              # whether CrawlerRunConfig.fallback_fetch_function was
#                                           # wired for this run (crawl4ai's OWN mechanism, path a
#                                           # above) — NOT whether pipe_scraper's own except-block
#                                           # rescue (path b) is present, which is unconditional code,
#                                           # not a config-object attribute, so it has no stamp field.
#     "download_delay_s": float, "concurrency_per_domain": int, "empty_threshold_bytes": int,
#   }
# }
#
# Separate file from src/scraper/scrape_log.jsonl (the ad-hoc single-URL path's log) — different
# schema (has run_id/domain, no sidecar/content_path/mode) and wildly different volume (hundreds
# of records per invocation here vs one there). No sidecar content files: pipe_scraper already
# writes every page's raw markdown to --output-dir; that IS the content record.
#
# Log path: WEBSEARCH_PIPE_SCRAPE_LOG_PATH env var -> DEFAULT_LOG_PATH fallback.
# Retention: same 14-day lazy prune as scrape_log.jsonl (src/log_janitor.py, WEBSEARCH_LOG_RETENTION_DAYS).


# FUNCTIONS

# Append one JSONL record; path from WEBSEARCH_PIPE_SCRAPE_LOG_PATH env var; fail-soft — a
# logging failure must never break a scrape run, same posture as scrape_logger.log_scrape
def log_pipe_scrape(record: dict) -> None:
    env = os.environ.get("WEBSEARCH_PIPE_SCRAPE_LOG_PATH")
    log_path = Path(env) if env else DEFAULT_LOG_PATH
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        maybe_prune_jsonl(log_path)
    except Exception as e:
        logger.warning("pipe_scrape_log write failed: %s", e)
