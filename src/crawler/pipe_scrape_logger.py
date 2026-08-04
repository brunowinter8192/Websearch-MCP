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
#   "wall_ms": int,
#   "crawl4ai_success": bool | null,       # crawl4ai's own result.success; null on pre-result exception
#   "crawl4ai_error_message": str | null,  # verbatim, informational only — the library's own
#                                           # anti-bot detector has documented false positives, never
#                                           # acted on, same posture as scrape_log.jsonl
#   "crawl4ai_attempts": int | null,
#   "crawl4ai_resolved_by": str | null,
#   "crawl4ai_fallback_fetch_used": bool | null,  # ALWAYS None/False today — pipe_scraper has no
#             fallback fetch path yet (that is a later milestone). Kept in the schema NOW anyway,
#             deliberately: the whole point of this log is comparability ACROSS a future config
#             change. If this field only appeared once the fallback path landed, every pre-change
#             record would be structurally different from every post-change one. Do not remove it
#             for reading as None on every current record — that is expected, not a bug.
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
