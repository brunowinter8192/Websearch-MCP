# INFRASTRUCTURE
# From src/crawler/pipe_scrape_logger.py: per-URL JSONL log with run/config stamp
from src.crawler.pipe_scrape_logger import log_pipe_scrape

# FUNCTIONS

# Assemble and write one JSONL record for a single URL's CHROMIUM-engine outcome, fail-soft via log_pipe_scrape
def _log_pipe_record(
    run_ctx: dict, ts: str, url: str, domain: str, outcome: str,
    status: int | None, byte_count: int, wall_ms: int, diagnosis: dict,
    pipe_fallback_used: bool = False, pipe_fallback_resolved: bool = False,
    landed_url: str | None = None,
) -> None:
    log_pipe_scrape({
        "ts": ts, "run_id": run_ctx["run_id"], "url": url, "domain": domain,
        "outcome": outcome, "http_status": status, "bytes": byte_count, "wall_ms": wall_ms,
        "engine": "chromium",
        "crawl4ai_success": diagnosis.get("crawl4ai_success"),
        "crawl4ai_error_message": diagnosis.get("crawl4ai_error_message"),
        "crawl4ai_attempts": diagnosis.get("crawl4ai_attempts"),
        "crawl4ai_resolved_by": diagnosis.get("crawl4ai_resolved_by"),
        "crawl4ai_fallback_fetch_used": diagnosis.get("crawl4ai_fallback_fetch_used"),
        "pipe_fallback_used": pipe_fallback_used, "pipe_fallback_resolved": pipe_fallback_resolved,
        "landed_url": landed_url,
        "config_hash": run_ctx["config_hash"], "config": run_ctx["config"],
    })

# Assemble and write one JSONL record for a single URL's CAMOUFOX-engine outcome — sibling to _log_pipe_record, not shared
def _log_pipe_camoufox_record(
    run_ctx: dict, ts: str, url: str, domain: str, outcome: str,
    status: int | None, byte_count: int, wall_ms: int, meta: dict,
) -> None:
    log_pipe_scrape({
        "ts": ts, "run_id": run_ctx["run_id"], "url": url, "domain": domain,
        "outcome": outcome, "http_status": status, "bytes": byte_count, "wall_ms": wall_ms,
        "engine": "camoufox",
        "landed_url": meta.get("landed_url"),
        "markdown_conversion_error": meta.get("markdown_conversion_error"),
        "content_is_raw_html": meta.get("content_is_raw_html", False),
        "document_status_chain": meta.get("document_status_chain"),
        "config_hash": meta.get("config_hash"), "config": meta.get("config"),
    })
