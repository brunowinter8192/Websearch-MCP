# INFRASTRUCTURE
import json
import logging
import os
from pathlib import Path

# From src/log_janitor.py: lazy 14-day prune on write
from src.log_janitor import maybe_prune_jsonl

logger = logging.getLogger(__name__)

# Record schema — three record_type values: two written per production query (plus one per probe
# query for engine_run), one written per search_engine_drilldown call:
#
# record_type = "engine_run"  (written by _query_engines_concurrent — always):
# {
#   "record_type": "engine_run",
#   "ts": str (ISO-8601 UTC),
#   "query": str,
#   "language": str,
#   "engines_requested": [str],
#   "engines": {
#     "<engine_name>": {
#       "rate_wait_ms": int, "search_ms": int, "result_count": int,
#       "status": str,       # OK | RATE_SKIP
#                            # EMPTY | EMPTY_NO_RESULTS | EMPTY_NO_CONTAINER | EMPTY_CONSENT | EMPTY_BLOCK | EMPTY_CONCURRENT_RACE
#                            # TIMEOUT | TIMEOUT_WATCHDOG | TIMEOUT_NONCOOP | TIMEOUT_HTTPX
#                            # ERROR | ERROR_BROWSER | ERROR_HTTP | ERROR_PARSE | ERROR_OTHER
#       "drop_reason": str | null
#     }
#   }
# }
#
# record_type = "workflow_summary"  (written by search_web_workflow — production only):
# {
#   "record_type": "workflow_summary",
#   "ts": str (ISO-8601 UTC),
#   "query": str,
#   "language": str,
#   "engines_requested": [str],
#   "engines_excluded": { "<engine_name>": "<reason>" },
#   "total_wall_ms": int,
#   "bottleneck_engine": str | null,
#   "engines": { ... same as engine_run ... },
#   "search_key": str        # see "search_key" note below
# }
#
# record_type = "drilldown"  (written by cli.py's search_engine_drilldown branch — always):
# {
#   "record_type": "drilldown",
#   "ts": str (ISO-8601 UTC),
#   "query": str,
#   "language": str,
#   "mode": "books" | "pdf" | "docs" | null,
#   "engine": str,            # the --engine value requested
#   "search_key": str,        # see "search_key" note below
#   "cache_status": str,      # "hit" | "miss_then_searched" (cache miss triggered a fresh search
#                             # that then produced a cache entry) | "miss_then_search_failed" (miss,
#                             # re-searched, still no cache entry — engine/urls fields below are empty/False)
#   "engine_in_pools": bool,  # whether --engine was present in this search's cached pools at all —
#                             # False distinguishes "engine excluded upstream / never ran" from
#                             # "engine ran, returned zero results" (result_count=0 either way)
#   "result_count": int,      # len(pools[engine]); 0 when engine_in_pools is False
#   "urls": [str]             # the URLs that engine's pool actually contained, in position order —
#                             # deliberately just the URL string, not the full cached result object
#                             # (title/snippet/date/position): answers "did engine X ever offer URL
#                             # Y in this session", which is all a plain URL list is needed for; the
#                             # full objects still live in the cache file (~/.cache/websearch/<key>.json,
#                             # 1h TTL) if ever needed
# }
#
# search_key: the SAME value cache.cache_key(query, language, engines, time_range, modifier_id=mode)
# computes — not a random per-run id. Two separate searches of the same query under the same mode
# correctly share one search_key; that is deterministic hashing working as intended, not a
# collision. It is the join key: any "workflow_summary" and any "drilldown" record sharing the same
# search_key are provably about the same search. LIMIT: this file is lazily pruned by
# log_janitor on a 14-day window — a "drilldown" record can outlive the "workflow_summary" it
# points at (the drilldown written well after the search, or the search's own record already
# pruned). A search_key with no matching "workflow_summary" left in the file is NOT a sign of an
# orphaned record or log corruption — it is ordinary retention; the join is opportunistic, not
# guaranteed present.
#
# NOT correlatable: nothing in this file carries an identifier shared with src/logs/scrape_log.jsonl
# (a separate file) — a URL later scraped cannot be mechanically tied back to a drilldown record.
#
# Old records (no record_type field) are workflow_summary-equivalent — backward compatible.
# Log path: WEBSEARCH_QUERY_LOG_PATH env var → DEFAULT_LOG_PATH fallback.
DEFAULT_LOG_PATH = Path(__file__).parent.parent.parent / "src" / "logs" / "query_log.jsonl"


# FUNCTIONS

# Append one JSONL record; path read from WEBSEARCH_QUERY_LOG_PATH env var at call time; fail-soft
def log_query(record: dict) -> None:
    env = os.environ.get("WEBSEARCH_QUERY_LOG_PATH")
    log_path = Path(env) if env else DEFAULT_LOG_PATH
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        maybe_prune_jsonl(log_path)
    except Exception as e:
        logger.warning("query_log write failed: %s", e)
