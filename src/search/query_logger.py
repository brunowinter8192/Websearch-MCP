# INFRASTRUCTURE
import json
import logging
import os
from pathlib import Path

# From src/log_janitor.py: lazy 14-day prune on write
from src.log_janitor import maybe_prune_jsonl

logger = logging.getLogger(__name__)

# Record schema — two record_type values written per production query, one per probe query:
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
#   "preview": { "urls_attempted": int, "urls_succeeded": int, "url_timeouts": int, "total_ms": int }
# }
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
