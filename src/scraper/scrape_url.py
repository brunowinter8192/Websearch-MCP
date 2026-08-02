# INFRASTRUCTURE
import asyncio
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

# Bound on htmldate's synchronous parse — dateparser (one of htmldate's own dependencies) is
# flagged as slow in htmldate's own source; without a hard cap a single pathological page could
# stall the extraction. Runs off the event loop via asyncio.to_thread regardless.
HTMLDATE_TIMEOUT_S = 5.0

_LINK_LINE_RE = re.compile(r'^\[.+\]\(.+\)$')

DEFAULT_MAX_CONTENT_LENGTH = 15000
MIN_CONTENT_THRESHOLD = 200

CONSENT_WORDS = ["cookie", "consent", "einwilligung", "tracking", "akzeptieren", "datenschutz", "zweck"]
CONSENT_DENSITY_THRESHOLD = 5
CONSENT_SKIP_OFFSET = 300

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

_GARBAGE_MESSAGES = {
    "minimal_content": "Page returned only whitespace or near-empty content",
    "cookie_wall": "Cookie/consent wall detected — page returns only GDPR consent text, not actual content",
    "login_wall": "Login/paywall detected — page requires authentication",
    "cloudflare": "Cloudflare protection — page requires browser verification",
    "http_error": "HTTP error page (404/403)",
    "nav_dump": "Navigation dump — page returned only links, no content",
    "crawl4ai_error": "Crawl4AI extraction error",
    "browser_missing": "Browser binary missing — run `./venv/bin/python -m patchright install chromium` to install it",
}

# Substrings that mark an exception as a browser-launch/executable failure, not a per-URL scrape miss
_BROWSER_LAUNCH_SIGNATURES = (
    "executable doesn't exist",
    "playwright install",
    "browsertype.launch",
)


# ORCHESTRATOR
async def scrape_url_workflow(url: str, max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH) -> list[TextContent]:
    t_total = time.perf_counter()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    domain = (urlparse(url).hostname or "").removeprefix("www.")
    logger.info("Scraping: %s", url)

    content, meta = await try_scrape(url)
    total_wall = round((time.perf_counter() - t_total) * 1000)

    if not content:
        outcome = meta.get("garbage_type") or "empty"
        content_path = write_sidecar(url, ts, meta.get("garbage_content"), outcome, "filtered")
        log_scrape({
            "ts": ts, "url": url, "domain": domain, "mode": "filtered", "outcome": outcome,
            "timings_ms": {"total_wall": total_wall},
            "http_status": meta.get("status_code"), "content_type": meta.get("content_type"),
            "bytes_returned": None, "bytes_raw_markdown": None,
            "fallback_to_raw": False, "truncated": False,
            "consent_stripped": False, "garbage_type": meta.get("garbage_type"),
            "content_path": content_path,
        })
        hint = get_plugin_hint(url)
        reason = _GARBAGE_MESSAGES.get(outcome, "No content extracted")
        msg = f"Error scraping {url}: {reason}"
        if hint:
            msg += f"\n\nHint: {hint}"
        return [TextContent(type="text", text=msg)]

    logger.info("Scrape complete: %s (%d chars)", url, len(content))
    final = truncate_content(content, max_content_length)
    content_path = write_sidecar(url, ts, final, "ok", "filtered")
    published_date = meta.get("date")
    log_scrape({
        "ts": ts, "url": url, "domain": domain, "mode": "filtered", "outcome": "ok",
        "timings_ms": {"total_wall": total_wall},
        "http_status": meta.get("status_code"), "content_type": meta.get("content_type"),
        "bytes_returned": len(final.encode("utf-8")),
        "bytes_raw_markdown": meta.get("raw_markdown_bytes", len(content.encode("utf-8"))),
        "fallback_to_raw": meta.get("fallback_to_raw", False),
        "truncated": len(content) > max_content_length,
        "consent_stripped": meta.get("consent_stripped", False),
        "garbage_type": None,
        "content_path": content_path,
        "published_date": published_date,
    })
    header = f"# Content from: {url}"
    if published_date:
        header += f"\nPublished: {published_date}"
    return [TextContent(type="text", text=f"{header}\n\n{final}")]


# FUNCTIONS

# Single-call crawl4ai scrape with native anti-bot baseline; return (content, meta)
# meta keys: garbage_type, status_code, content_type, fallback_to_raw, consent_stripped,
#            garbage_content (content that triggered garbage detection, for sidecar logging),
#            raw_markdown_bytes (raw_markdown length before filter/fallback),
#            date (original publication date, ISO day precision, or None)
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
        page_timeout=60000,
        max_retries=0,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.48)),
        excluded_selector=COOKIE_CONSENT_SELECTOR,
        verbose=False,
    )
    _empty_meta: dict = {
        "garbage_type": None, "status_code": None, "content_type": None,
        "fallback_to_raw": False, "consent_stripped": False,
        "garbage_content": None, "raw_markdown_bytes": 0, "date": None,
    }
    try:
        async with AsyncWebCrawler(config=browser_config, crawler_strategy=crawler_strategy) as crawler:
            result = await crawler.arun(url=url, config=run_config)
        status_code = result.status_code if hasattr(result, "status_code") else None
        ct = None
        if hasattr(result, "headers") and result.headers:
            ct = result.headers.get("content-type") or result.headers.get("Content-Type")
        meta: dict = {**_empty_meta, "status_code": status_code, "content_type": ct}
        if status_code and status_code >= 400:
            logger.warning("HTTP %d detected: %s", status_code, url)
            return "", {**meta, "garbage_type": "http_error"}
        if not result.markdown:
            return "", meta
        raw_md = result.markdown.raw_markdown or ""
        meta["raw_markdown_bytes"] = len(raw_md.encode("utf-8"))
        # Extracted from raw HTML BEFORE cookie-wall/garbage handling — a consent-walled markdown
        # extract can still sit on top of HTML carrying real JSON-LD/meta-tag date information.
        meta["date"] = await extract_date(result.html or "", url)
        content = result.markdown.fit_markdown or ""
        fallback_to_raw = False
        if len(content) < MIN_CONTENT_THRESHOLD and raw_md:
            content = raw_md
            fallback_to_raw = True
        meta["fallback_to_raw"] = fallback_to_raw
        garbage_type = is_garbage_content(content)
        if garbage_type == "cookie_wall":
            stripped = strip_consent_prefix(content)
            if stripped != content and is_garbage_content(stripped) is None:
                logger.debug("Consent prefix stripped: %s (%d chars removed)", url, len(content) - len(stripped))
                return stripped, {**meta, "consent_stripped": True}
        if garbage_type:
            logger.warning("Garbage detected [%s]: %s", garbage_type, url)
            return "", {**meta, "garbage_type": garbage_type, "garbage_content": content}
        return content, meta
    except Exception as e:
        if is_browser_launch_error(e):
            logger.error("Browser binary missing/failed to launch for %s: %s", url, e)
            return "", {**_empty_meta, "garbage_type": "browser_missing"}
        logger.warning("Failed to scrape %s: %s", url, e)
        return "", dict(_empty_meta)


# Original publication date (day precision) from raw HTML via htmldate — extensive_search (higher
# recall, parse cost is negligible next to this scraper's browser fetch) + original_date=True
# (REQUIRED: default htmldate behavior returns last-modified, not publication, date). Runs off the
# event loop with a hard timeout so a slow/pathological page can never stall the scrape; any
# exception, timeout, or absence degrades to None — never a guessed value.
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


# Detect garbage content: error pages, cookie walls, login walls, navigation dumps
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


# Strip leading consent block: detect by keyword density, cut before first heading after offset
def strip_consent_prefix(content: str) -> str:
    if not content:
        return content
    sample = content[:3000].lower()
    density = sum(sample.count(w) for w in CONSENT_WORDS)
    if density <= CONSENT_DENSITY_THRESHOLD:
        return content
    match = re.search(r'\n(#{1,2} )', content[CONSENT_SKIP_OFFSET:])
    if match:
        pos = CONSENT_SKIP_OFFSET + match.start() + 1
        return content[pos:]
    return content


# Truncate content at paragraph boundary if too long
def truncate_content(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n\n')
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[Content truncated...]"


# No plugin-routing hint — all domains are scrapable
def get_plugin_hint(url: str) -> str:
    return ""
