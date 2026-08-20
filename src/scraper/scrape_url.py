# INFRASTRUCTURE
import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from htmldate import find_date

from mcp.types import TextContent
# From scrape_logger.py: per-URL JSONL log + sidecar content file
from src.scraper.scrape_logger import log_scrape, write_sidecar

logger = logging.getLogger(__name__)

HTMLDATE_TIMEOUT_S = 5.0
TOTAL_SCRAPE_BUDGET_S = 221.3
_LINK_LINE_RE = re.compile(r'^\[.+\]\(.+\)$')
MIN_CONTENT_THRESHOLD = 200

COOKIE_CONSENT_SELECTOR = ", ".join([
    "[class*='cookie-banner']", "[id*='cookie-banner']",
    "[class*='cookie-consent']", "[id*='cookie-consent']",
    "[class*='cookie-notice']", "[id*='cookie-notice']",
    "[class*='cookie-law']", "[id*='cookie-law']",
    "[class*='cky-consent']", "[class*='cky-banner']", "[class*='cky-modal']",
    "[class*='onetrust']", "[id*='onetrust']",
    "[id*='CookiebotDialog']", "[class*='CookiebotWidget']",
    "[class*='cc-banner']", "[class*='cc-window']",
    "[class*='gdpr']", "[id*='gdpr']",
])

_ACQUISITION_ERROR_MESSAGES = {
    "browser_missing": "browser binary missing — run `./venv/bin/python -m patchright install chromium` to install it",
    "budget_exhausted": f"scrape exceeded the total time budget ({TOTAL_SCRAPE_BUDGET_S}s)",
}

_BROWSER_LAUNCH_SIGNATURES = (
    "executable doesn't exist",
    "playwright install",
    "browsertype.launch",
)


# ORCHESTRATOR

# Scrape one URL end to end: acquire, log, render — returns content as-is plus acquisition facts
async def scrape_url_workflow(url: str) -> list[TextContent]:
    t_total = time.perf_counter()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    domain = (urlparse(url).hostname or "").removeprefix("www.")
    logger.info("Scraping: %s", url)

    content, meta = await try_scrape(url)
    total_wall = round((time.perf_counter() - t_total) * 1000)
    config = meta.get("config") or {"config_incomplete": True}
    config_hash = hash_config(config)
    published_date = meta.get("date")

    outcome = meta.get("acquisition_error") or ("ok" if content else "empty")
    content_path = write_sidecar(url, ts, content, outcome, "filtered")
    log_scrape({
        "ts": ts, "url": url, "domain": domain, "mode": "filtered", "outcome": outcome,
        "engine": "chromium",
        "timings_ms": {"total_wall": total_wall},
        "http_status": meta.get("status_code"), "content_type": meta.get("content_type"),
        "bytes_returned": len(content.encode("utf-8")) if content else 0,
        "bytes_raw_markdown": meta.get("raw_markdown_bytes", 0),
        "fallback_to_raw": meta.get("fallback_to_raw", False),
        "content_path": content_path,
        "published_date": published_date,
        "landed_url": meta.get("landed_url"),
        "crawl4ai_success": meta.get("crawl4ai_success"),
        "crawl4ai_error_message": meta.get("crawl4ai_error_message"),
        "crawl4ai_attempts": meta.get("crawl4ai_attempts"),
        "crawl4ai_resolved_by": meta.get("crawl4ai_resolved_by"),
        "crawl4ai_fallback_fetch_used": meta.get("crawl4ai_fallback_fetch_used"),
        "config_hash": config_hash, "config": config,
    })
    logger.info("Scrape complete: %s (%d chars, outcome=%s)", url, len(content), outcome)
    return [TextContent(type="text", text=_format_scrape_output(url, content, meta, published_date))]


# FUNCTIONS

# Run one browser acquisition + date extraction + content selection, the guarded span inside try_scrape's budget
async def _acquire_scrape(
    url: str, browser_config: BrowserConfig, crawler_strategy: AsyncPlaywrightCrawlerStrategy,
    run_config: CrawlerRunConfig, empty_meta: dict,
) -> tuple[str, dict]:
    async with AsyncWebCrawler(config=browser_config, crawler_strategy=crawler_strategy) as crawler:
        result = await crawler.arun(url=url, config=run_config)
    status_code = result.status_code if hasattr(result, "status_code") else None
    ct = None
    if hasattr(result, "headers") and result.headers:
        ct = result.headers.get("content-type") or result.headers.get("Content-Type")
    landed_url = getattr(result, "redirected_url", None)
    meta: dict = {**empty_meta, "status_code": status_code, "content_type": ct,
                  "landed_url": landed_url}
    meta.update(extract_crawl4ai_diagnosis(result))
    if not result.markdown:
        return "", meta
    raw_md = result.markdown.raw_markdown or ""
    meta["raw_markdown_bytes"] = len(raw_md.encode("utf-8"))
    meta["date"] = await extract_date(result.html or "", url)
    content = result.markdown.fit_markdown or ""
    fallback_to_raw = False
    if len(content) < MIN_CONTENT_THRESHOLD and raw_md:
        content = raw_md
        fallback_to_raw = True
    meta["fallback_to_raw"] = fallback_to_raw
    return content, meta


# Single-call crawl4ai scrape with native anti-bot baseline; returns (content, meta) unconditionally, no content judgment
async def try_scrape(url: str) -> tuple[str, dict]:
    browser_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
    adapter = UndetectedAdapter()
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=adapter
    )
    run_config = CrawlerRunConfig(
        magic=True,
        wait_until="load",
        page_timeout=30000,
        delay_before_return_html=5.0,
        max_retries=0,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, preserve_tags=["pre", "code"])
        ),
        excluded_selector=COOKIE_CONSENT_SELECTOR,
        remove_consent_popups=True,
        verbose=False,
    )
    config_stamp = extract_config_stamp(browser_config, adapter, crawler_strategy, run_config)
    _empty_meta: dict = {
        "acquisition_error": None, "status_code": None, "content_type": None,
        "fallback_to_raw": False, "raw_markdown_bytes": 0, "date": None,
        "crawl4ai_success": None, "crawl4ai_error_message": None,
        "crawl4ai_attempts": None, "crawl4ai_resolved_by": None,
        "crawl4ai_fallback_fetch_used": None, "landed_url": None,
        "config": config_stamp,
    }
    try:
        return await asyncio.wait_for(
            _acquire_scrape(url, browser_config, crawler_strategy, run_config, _empty_meta),
            timeout=TOTAL_SCRAPE_BUDGET_S,
        )
    except asyncio.TimeoutError:
        logger.warning("Scrape budget exhausted (%.1fs): %s", TOTAL_SCRAPE_BUDGET_S, url)
        return "", {**_empty_meta, "acquisition_error": "budget_exhausted"}
    except Exception as e:
        if is_browser_launch_error(e):
            logger.error("Browser binary missing/failed to launch for %s: %s", url, e)
            return "", {**_empty_meta, "acquisition_error": "browser_missing"}
        logger.warning("Failed to scrape %s: %s", url, e)
        return "", {**_empty_meta, "acquisition_error": "exception"}


# Read the scrape-governing config back off the actual constructed objects, never re-declared
def extract_config_stamp(browser_config, adapter, crawler_strategy, run_config) -> dict:
    content_filter = run_config.markdown_generator.content_filter
    return {
        "headless": browser_config.headless,
        "enable_stealth": browser_config.enable_stealth,
        "adapter": type(adapter).__name__,
        "crawler_strategy": type(crawler_strategy).__name__,
        "magic": run_config.magic,
        "wait_until": run_config.wait_until,
        "page_timeout_ms": run_config.page_timeout,
        "delay_before_return_html_s": run_config.delay_before_return_html,
        "max_retries": run_config.max_retries,
        "cache_mode": run_config.cache_mode.value,
        "content_filter": type(content_filter).__name__,
        "content_filter_threshold": content_filter.threshold,
        "content_filter_preserve_tags": sorted(content_filter.preserve_tags),
        "excluded_selector_hash": hashlib.sha256(run_config.excluded_selector.encode()).hexdigest()[:8],
        "remove_consent_popups": run_config.remove_consent_popups,
        "total_budget_s": TOTAL_SCRAPE_BUDGET_S,
        "min_content_threshold": MIN_CONTENT_THRESHOLD,
    }


# Stable short hash over the config record — cheap "same config" grouping key
def hash_config(config: dict) -> str:
    blob = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


# Read crawl4ai's own anti-bot diagnosis off the result object, verbatim — an OBSERVATION, not a verdict
def extract_crawl4ai_diagnosis(result) -> dict:
    stats = getattr(result, "crawl_stats", None) or {}
    return {
        "crawl4ai_success": getattr(result, "success", None),
        "crawl4ai_error_message": getattr(result, "error_message", None) or None,
        "crawl4ai_attempts": stats.get("attempts"),
        "crawl4ai_resolved_by": stats.get("resolved_by"),
        "crawl4ai_fallback_fetch_used": stats.get("fallback_fetch_used"),
    }


# Original publication date (day precision) from raw HTML via htmldate, bounded by a hard timeout
async def extract_date(html: str, url: str) -> str | None:
    if not html:
        return None
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(find_date, html, extensive_search=True, original_date=True, url=url),
            timeout=HTMLDATE_TIMEOUT_S,
        )
    except Exception as e:
        logger.debug("htmldate extraction failed for %s: %s", url, e)
        return None


# Detect browser-launch/executable-missing failure (environment defect) vs. an ordinary per-URL error
def is_browser_launch_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(sig in msg for sig in _BROWSER_LAUNCH_SIGNATURES)


# Detect garbage content (error/cookie/login/nav-dump pages) — used only by crawl_site.py's batch filter
def is_garbage_content(content: str) -> str | None:
    if not content or len(content.strip()) < 50:
        return "minimal_content"
    lower = content.lower()

    crawl4ai_errors = ["crawl4ai error:", "document is empty", "page is not fully supported"]
    if any(p in lower for p in crawl4ai_errors):
        return "crawl4ai_error"

    if len(content) < 1000:
        error_keywords = ["not_found", "404", "403", "forbidden", "access denied", "page not found"]
        if any(k in lower for k in error_keywords):
            return "http_error"

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if len(lines) >= 20:
        link_lines = sum(1 for l in lines if _LINK_LINE_RE.match(l))
        if link_lines / len(lines) > 0.6:
            return "nav_dump"

    sample = lower[:5000]
    cookie_signals = sample.count("cookie") + sample.count("consent") + sample.count("duration")
    cookie_wall_signals = ("consent preferences" in sample or "cookieyes" in sample or "cookie preferences" in sample)
    if cookie_signals > 15 and cookie_wall_signals:
        return "cookie_wall"

    if len(content) < 2000:
        login_patterns = [
            "sign in", "log in", "login", "subscribe to continue", "create account",
            "create an account", "premium content", "paywall", "members only", "subscriber only",
        ]
        if any(p in lower for p in login_patterns):
            return "login_wall"

    if len(content) < 500:
        if "checking your browser" in lower or "enable javascript and cookies" in lower:
            return "cloudflare"

    if "just a moment" in lower and "cloudflare" in lower:
        return "cloudflare"

    return None


# Render acquisition facts + full content into one fixed-shape text block
def _format_scrape_output(url: str, content: str, meta: dict, published_date: str | None) -> str:
    lines = [f"# Content from: {url}", ""]
    if published_date:
        lines.append(f"Published: {published_date}")
    selection_note = " + raw fallback" if meta.get("fallback_to_raw") else ""
    lines += [
        "## Acquisition facts",
        f"- HTTP status: {meta.get('status_code')}",
        f"- Landed URL (the URL the browser actually returned content from): {meta.get('landed_url')}",
        f"- Bytes (raw markdown from crawl4ai): {meta.get('raw_markdown_bytes', 0)}",
        f"- Bytes (content below, after PruningContentFilter{selection_note}): "
        f"{len(content.encode('utf-8')) if content else 0}",
        "- crawl4ai diagnosis (an OBSERVATION off crawl4ai's own anti-bot detector, NOT a "
        "verdict — it has documented false positives and is not acted on by this scraper): "
        f"success={meta.get('crawl4ai_success')}, resolved_by={meta.get('crawl4ai_resolved_by')}, "
        f"attempts={meta.get('crawl4ai_attempts')}, "
        f"error_message={meta.get('crawl4ai_error_message') or 'none'}",
    ]
    if meta.get("acquisition_error"):
        reason = _ACQUISITION_ERROR_MESSAGES.get(meta["acquisition_error"], meta["acquisition_error"])
        lines.append(f"- Acquisition error: {reason}")
    lines += ["", "## Content", "", content if content else "(no content returned)"]
    return "\n".join(lines)
