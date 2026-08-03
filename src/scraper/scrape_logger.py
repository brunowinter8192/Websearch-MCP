# INFRASTRUCTURE
import json
import logging
import os
import re
from pathlib import Path

# From src/log_janitor.py: lazy 14-day prune on write
from src.log_janitor import maybe_prune_jsonl, maybe_prune_sidecars

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path(__file__).parent.parent.parent / "src" / "logs" / "scrape_log.jsonl"

# Record schema (one record per scrape_url call):
# {
#   "ts": str (ISO-8601 UTC, millisecond precision),
#   "url": str,
#   "domain": str,
#   "mode": "filtered",
#   "outcome": "ok" | "garbage" | "empty" | "timeout" | "error",
#   "timings_ms": {"total_wall": int},
#   "http_status": int | null,
#   "content_type": str | null,
#   "bytes_returned": int | null,
#   "bytes_raw_markdown": int | null,
#   "fallback_to_raw": bool,
#   "truncated": bool,
#   "consent_stripped": bool,
#   "garbage_type": str | null,
#   "content_path": str | null,           # relative path under log dir, e.g. "scrape_content/<file>.md"
#   "published_date": str | null,         # ISO day precision (YYYY-MM-DD), htmldate-extracted, only on "ok" outcome
#   "crawl4ai_success": bool | null,      # crawl4ai's own result.success; null only when the call raised before a result existed
#   "crawl4ai_error_message": str | null, # crawl4ai's own result.error_message verbatim (e.g. "Blocked by anti-bot protection: <reason>"); NOT a verdict — the library's own detector has documented false positives, informational only
#   "crawl4ai_attempts": int | null,      # result.crawl_stats["attempts"] — total browser attempts across proxies/retries
#   "crawl4ai_resolved_by": str | null,   # result.crawl_stats["resolved_by"]: "direct" | "proxy" | "fallback_fetch" | null
#   "crawl4ai_fallback_fetch_used": bool | null,  # result.crawl_stats["fallback_fetch_used"]
#   "config_hash": str,                    # first 10 hex chars of sha256(sort_keys JSON of "config") — cheap "same config" grouping key
#   "config": {                            # scrape config actually in effect for this call, read off the real config objects (never hand-duplicated)
#     "headless": bool, "enable_stealth": bool, "adapter": str, "crawler_strategy": str,
#     "magic": bool, "wait_until": str, "page_timeout_ms": int, "max_retries": int,
#     "cache_mode": str, "content_filter": str, "content_filter_threshold": float,
#     "content_filter_preserve_tags": list[str],  # HTML tags exempted from pruning recursion — e.g. ["code", "pre"] guards syntax-highlighted code from whitespace-span decomposition (crawl4ai issue #2110)
#     "excluded_selector_hash": str,       # first 8 hex chars of sha256(excluded_selector) — the 426-char selector itself is source-visible, not worth repeating per record
#     "remove_consent_popups": bool,       # crawl4ai's own CMP click-dismissal, alongside (not instead of) excluded_selector; unconditional ~1s cost per scrape, see scrape_url.py comment at its CrawlerRunConfig construction
#     "max_content_length": int, "min_content_threshold": int
#     # OR, only if try_scrape's config invariant ever breaks: {"config_incomplete": true, "max_content_length": int, "min_content_threshold": int}
#   }
# }
#
# Log path: WEBSEARCH_SCRAPE_LOG_PATH env var → DEFAULT_LOG_PATH fallback.
# Sidecar path: <log_dir>/scrape_content/<ts_safe>_<url_slug>.md


# FUNCTIONS

# Sanitize ISO timestamp for filesystem: replace `:` with `-`
def _sanitize_ts(ts: str) -> str:
    return ts.replace(":", "-")


# Derive URL slug: strip protocol, replace non-alphanumeric with `-`, collapse runs, cap 80 chars
def _url_slug(url: str) -> str:
    slug = re.sub(r'^https?://', '', url)
    slug = re.sub(r'[^a-zA-Z0-9]', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')[:80]


# Write sidecar .md to <log_dir>/scrape_content/; return relative path or None on empty/error
def write_sidecar(url: str, ts: str, content: str, outcome: str, mode: str) -> str | None:
    if not content:
        return None
    env = os.environ.get("WEBSEARCH_SCRAPE_LOG_PATH")
    log_path = Path(env) if env else DEFAULT_LOG_PATH
    sidecar_dir = log_path.parent / "scrape_content"
    filename = f"{_sanitize_ts(ts)}_{_url_slug(url)}.md"
    header = (
        f"<!-- url: {url} -->\n"
        f"<!-- ts: {ts} -->\n"
        f"<!-- outcome: {outcome} -->\n"
        f"<!-- bytes: {len(content.encode('utf-8'))} -->\n"
        f"<!-- mode: {mode} -->\n"
    )
    try:
        sidecar_dir.mkdir(parents=True, exist_ok=True)
        (sidecar_dir / filename).write_text(header + "\n" + content, encoding="utf-8")
        maybe_prune_sidecars(sidecar_dir)
        return f"scrape_content/{filename}"
    except Exception as e:
        logger.warning("scrape_logger sidecar write failed: %s", e)
        return None


# Append one JSONL record; path from WEBSEARCH_SCRAPE_LOG_PATH env var; fail-soft
def log_scrape(record: dict) -> None:
    env = os.environ.get("WEBSEARCH_SCRAPE_LOG_PATH")
    log_path = Path(env) if env else DEFAULT_LOG_PATH
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        maybe_prune_jsonl(log_path)
    except Exception as e:
        logger.warning("scrape_log write failed: %s", e)
