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

# Bound on htmldate's synchronous parse — dateparser (one of htmldate's own dependencies) is
# flagged as slow in htmldate's own source; without a hard cap a single pathological page could
# stall the extraction. Runs off the event loop via asyncio.to_thread regardless.
HTMLDATE_TIMEOUT_S = 5.0

# Hard wall-clock budget for the entire ad-hoc scrape acquisition — the only outer guard on this
# path (page_timeout=30000 only bounds Playwright's page.goto; everything after a successful
# goto — crawl4ai's own two internal, non-configurable 30s render waits, consent handling, date
# extraction — is otherwise unbounded from our side). Per R9 (process-docs/time_budget/
# 2026-08-04_config_rules_and_the_promised_maximum.md): the sum of countable maxima. Composed of:
#   + browser cold start 180.0s (this path's own browser — enable_stealth=True below selects
#     UndetectedAdapter, crawl4ai/async_crawler_strategy.py's use_undetected switch, so this launch
#     runs via patchright.async_api's chromium.launch(), not plain playwright; crawl4ai's own
#     _build_browser_args() never sets a "timeout" kwarg regardless of undetected/not, so
#     Playwright/patchright's own enforced launch-timeout fallback governs:
#     DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS=180000, installed
#     patchright/_impl/_helper.py:253-263, identical mechanism/value to plain playwright's own
#     _impl/_helper.py:290. Source-read and probe-confirmed this session
#     (dev/camoufox_lane/01_launch_timeout_probe.py, process-docs/camoufox_lane/
#     2026-08-11_launch_timeout_enforcement_and_coldstart_ceiling.md) — replaces the earlier 1.1s
#     figure, which was a measured TYPICAL duration transferred from a different lane
#     (src/search/browser.py), not a ceiling; R9 only admits counted maxima)
#   + navigation cap 30s (page_timeout)
#   + render wait 5.0s (delay_before_return_html — raised from 2.0 for self-resolving Cloudflare
#     challenge pages; see delay_before_return_html's own comment for the Cloudflare-documented
#     source)
#   + consent handling 1.3s (remove_consent_popups, worst case: one unconditional 500ms sleep in
#     remove_consent_popups.js + 500ms Python-side + at most one 300ms post-click sleep, the rest
#     mutually exclusive behind break/return)
#   + date extraction 5.0s (HTMLDATE_TIMEOUT_S)
# = 221.3. Unbounded synchronous work such as markdown generation gets no reserved share of its
# own — it is simply covered by this same outer guard.
# Two honesty caveats on what this guard does NOT do:
#  - asyncio.wait_for only cancels at await points. Markdown generation + PruningContentFilter
#    run as synchronous CPU work inside crawl4ai's arun() — a pathological synchronous parse can
#    overrun this budget; the guard only fires once control returns to an await. Not fixed here
#    (no thread offload, no executor) — this constant bounds network/browser hangs, not
#    synchronous CPU inside crawl4ai.
#  - This budget wraps ACQUISITION only (try_scrape's browser call + date extraction +
#    content selection) — post-acquisition local work (write_sidecar, log_scrape, output
#    formatting) sits outside the guarded span, so a budget-exhausted record is still writable.
#    The logged total_wall in scrape_log.jsonl can therefore exceed this value by that
#    post-processing cost.
TOTAL_SCRAPE_BUDGET_S = 221.3

# Used by is_garbage_content, kept for src/crawler/crawl_site.py's unattended batch-crawl filter
# (a different consumer than this module's own workflow — no agent looking at that output, so an
# automatic verdict is correct there). See is_garbage_content's own comment.
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

# Short descriptions for the ONLY failure states left that mean "acquisition produced zero
# content" — not content judgment (that layer is removed; see meta["acquisition_error"] and
# try_scrape's comment). "exception" (the residual catch-all) has no entry — its detail already
# goes to cli.log via logger.warning; not worth guessing a message for an unclassified error.
_ACQUISITION_ERROR_MESSAGES = {
    "browser_missing": "browser binary missing — run `./venv/bin/python -m patchright install chromium` to install it",
    "budget_exhausted": f"scrape exceeded the total time budget ({TOTAL_SCRAPE_BUDGET_S}s)",
}

# Substrings that mark an exception as a browser-launch/executable failure, not a per-URL scrape miss
_BROWSER_LAUNCH_SIGNATURES = (
    "executable doesn't exist",
    "playwright install",
    "browsertype.launch",
)


# ORCHESTRATOR
# Returns content AS-IS (never replaced by a message about it) plus the acquisition facts
# alongside — the agent judges, this scraper no longer does. See _format_scrape_output.
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

    # outcome: "ok" (content came back) | "empty" (browser succeeded, page had nothing) |
    # "budget_exhausted" | "browser_missing" | "exception" (acquisition itself failed — no
    # content-judgment categories anymore, see meta["acquisition_error"] / try_scrape's comment)
    outcome = meta.get("acquisition_error") or ("ok" if content else "empty")
    content_path = write_sidecar(url, ts, content, outcome, "filtered")
    log_scrape({
        "ts": ts, "url": url, "domain": domain, "mode": "filtered", "outcome": outcome,
        # First-class discriminator between this (chromium/crawl4ai) lane and the camoufox lane
        # (camoufox_scrape.py's scrape_url_camoufox_workflow) sharing this same log file — the
        # config stamp already differs structurally between the two, but a reader filtering the
        # log should not have to do config-shape archaeology to tell them apart. Absent on every
        # record written before this field existed, same convention as every prior field addition
        # this session (see scrape_logger.py's schema comment).
        "engine": "chromium",
        "timings_ms": {"total_wall": total_wall},
        "http_status": meta.get("status_code"), "content_type": meta.get("content_type"),
        "bytes_returned": len(content.encode("utf-8")) if content else 0,
        "bytes_raw_markdown": meta.get("raw_markdown_bytes", 0),
        "fallback_to_raw": meta.get("fallback_to_raw", False),
        "content_path": content_path,
        "published_date": published_date,
        # landed_url: RAW, exactly as crawl4ai reported (see try_scrape's comment) — no verdict
        # stored alongside it. An agent reading this log has both this field and "url" in the same
        # record and can compare them itself; a stored same/different verdict would be a
        # re-derivable conclusion kept as data, and this scraper reports facts, not conclusions
        # (see process-docs/scrape_pipeline/content_judgment_removal_2026-08-05.md).
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

# Single-call crawl4ai scrape with native anti-bot baseline; return (content, meta). Returns
# whatever content crawl4ai produced, UNCONDITIONALLY — no status-code gate, no content-based
# verdict. This scraper reports facts; the caller (an agent, with a user to report to) judges.
# Real evidence this judgment was wrong in both directions: de.trustpilot.com/review/entega.de
# returns HTTP 403 with 42707 bytes of the real review page (the old status>=400 gate discarded
# all of it); idealo.de's OffersOfProduct page returns HTTP 200 with 401 bytes reading "Sorry!
# Something has gone wrong" (the old content classifier let it through as a clean "ok").
# meta keys: acquisition_error (None | "budget_exhausted" | "browser_missing" | "exception" —
#            ONLY set when acquisition itself produced no result at all; never a content verdict),
#            status_code, content_type, fallback_to_raw (fit_markdown was too thin, raw_markdown
#            used instead — PruningContentFilter's own fallback, untouched, not a garbage check),
#            raw_markdown_bytes (raw_markdown length before filter/fallback),
#            date (original publication date, ISO day precision, or None),
#            crawl4ai_success, crawl4ai_error_message, crawl4ai_attempts,
#            crawl4ai_resolved_by, crawl4ai_fallback_fetch_used
#            (crawl4ai's own anti-bot diagnosis, recorded verbatim — an OBSERVATION, not acted on
#            here and must not be presented as a verdict by the caller either; see Gotchas —
#            guenstiger.de reports "Blocked by anti-bot protection: Cloudflare JS challenge" from
#            crawl4ai's own detector on a render that returns the full 38691-byte product page)
#            config (scrape-side config stamp — browser/run/content-filter settings actually used,
#            read directly off the real constructed objects, see extract_config_stamp)
#            landed_url (crawl4ai's result.redirected_url, RAW/unnormalized — the URL the browser
#            actually ended up on, set from page.url both right after goto and again immediately
#            before the response is built to also catch JS-driven navigation; None on any return
#            path that never obtained a result object — see _empty_meta. status_code is the FIRST
#            hop of a redirect chain while landed_url/content are the LAST — a record can
#            legitimately show status 301 next to real content; that combination is not a bug)
# The whole acquisition (browser call + date extraction) runs inside
# asyncio.wait_for(TOTAL_SCRAPE_BUDGET_S) — see that constant's comment for the exact guarded
# span and its two honesty caveats (sync CPU inside crawl4ai; post-acquisition work uncounted).
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
        # 60000 was not a derived figure — crawl4ai's own CHANGELOG lists replacing a previously
        # hardcoded 30s timeout, justified only as "better handling for slow-loading pages", no
        # measurement behind the raise. Rule applied: a phase cap is not raised above the default
        # of the layer that actually executes it without evidence for the raise. patchright
        # 1.61.2 (DEFAULT_PLAYWRIGHT_TIMEOUT_IN_MILLISECONDS, _impl/_helper.py) — the library that
        # actually runs this timeout — defaults to 30000; crawl4ai's own docs/examples scatter
        # across 10000/30000/60000/80000/120000/200000, no consistent evidence either way. No
        # evidence for the raise -> falls back to the executing layer's own default.
        page_timeout=30000,
        # 5.0, raised from an earlier 2.0 (crawl4ai issue #1665's JS-heavy-page saturation knee at
        # 3s, discounted for remove_consent_popups' own ~1s forced render wait below) — the
        # earlier value captured self-resolving Cloudflare challenge pages too early: measured on
        # guenstiger.de (2026-08-05, varying only this wait), 2.0s captured the interstitial, 6.0s
        # the real product page, 12.0s/20.0s added ~50 bytes over 6.0s. That single-domain
        # measurement is corroborating evidence, not the basis for the value: the basis is
        # Cloudflare's own docs (developers.cloudflare.com/cloudflare-challenges/challenge-types/
        # challenge-pages/, section "Non-Interactive Challenges", page last updated 2026-07-06),
        # which state the visitor must wait until the browser finishes processing the challenge
        # JavaScript, "typically ... less than five seconds" — taken AS-IS, no invented safety
        # margin added on top.
        delay_before_return_html=5.0,
        max_retries=0,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, preserve_tags=["pre", "code"])
        ),
        excluded_selector=COOKIE_CONSENT_SELECTOR,
        # Click-based CMP dismissal (OneTrust/Cookiebot/CookieYes/~100 others), runs on the live
        # page BEFORE page.content() capture — a second layer alongside excluded_selector (which
        # runs later, on the captured HTML string), not a replacement. Real recovered content on
        # azubiyo.de (excluded_selector alone lets ~3400 consent-banner chars through).
        # Fixed, UNCONDITIONAL cost on every page regardless of whether a popup exists — two
        # separate 500ms sleeps: one inside crawl4ai's own remove_consent_popups.js (line 332,
        # "wait for CMP animations/transitions", fires whether or not anything was clicked/removed)
        # and one on the Python side after the JS eval returns (async_crawler_strategy.py:1581,
        # page.wait_for_timeout(500)). Measured end-to-end on a page with no consent layer
        # (rfc-editor.org): +0.96s wall time (1.93s -> 2.89s). Relevant to future determinism work:
        # this switch spends ~1s on every scrape to help only the subset with a consent layer.
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
    # Guarded span: browser launch through content selection. Excludes config construction above
    # (instant, needed for _empty_meta/config stamp even on timeout) and post-acquisition local
    # work in scrape_url_workflow (sidecar/log — must stay writable on timeout too).
    async def _acquire() -> tuple[str, dict]:
        async with AsyncWebCrawler(config=browser_config, crawler_strategy=crawler_strategy) as crawler:
            result = await crawler.arun(url=url, config=run_config)
        status_code = result.status_code if hasattr(result, "status_code") else None
        ct = None
        if hasattr(result, "headers") and result.headers:
            ct = result.headers.get("content-type") or result.headers.get("Content-Type")
        # RAW, never normalized — any comparison rule is a rule applied when READING this data,
        # not a storage format; keeping the raw value means it stays analysable under any rule
        # (current or future) applied later, by whoever reads the record.
        landed_url = getattr(result, "redirected_url", None)
        meta: dict = {**_empty_meta, "status_code": status_code, "content_type": ct,
                      "landed_url": landed_url}
        meta.update(extract_crawl4ai_diagnosis(result))
        # No status-code gate here — a status is a fact returned alongside content, not evidence
        # to discard it on: trustpilot returns HTTP 403 WITH the real 42707-byte review page.
        if not result.markdown:
            return "", meta
        raw_md = result.markdown.raw_markdown or ""
        meta["raw_markdown_bytes"] = len(raw_md.encode("utf-8"))
        # Extracted from raw HTML BEFORE content selection — PruningContentFilter can still
        # produce a page whose markdown lacks a heading/byline; the raw HTML underneath it still
        # carries real JSON-LD/meta-tag date information.
        meta["date"] = await extract_date(result.html or "", url)
        content = result.markdown.fit_markdown or ""
        fallback_to_raw = False
        if len(content) < MIN_CONTENT_THRESHOLD and raw_md:
            content = raw_md
            fallback_to_raw = True
        meta["fallback_to_raw"] = fallback_to_raw
        # Selection between two crawl4ai-provided candidates (fit vs raw) ends here — no verdict
        # on whether the selected content itself is "good"; that judgment is the caller's now.
        return content, meta

    try:
        return await asyncio.wait_for(_acquire(), timeout=TOTAL_SCRAPE_BUDGET_S)
    except asyncio.TimeoutError:
        logger.warning("Scrape budget exhausted (%.1fs): %s", TOTAL_SCRAPE_BUDGET_S, url)
        return "", {**_empty_meta, "acquisition_error": "budget_exhausted"}
    except Exception as e:
        if is_browser_launch_error(e):
            logger.error("Browser binary missing/failed to launch for %s: %s", url, e)
            return "", {**_empty_meta, "acquisition_error": "browser_missing"}
        logger.warning("Failed to scrape %s: %s", url, e)
        return "", {**_empty_meta, "acquisition_error": "exception"}


# Read the scrape-governing config back off the actual constructed objects — never re-declare
# their values here, so the stamp cannot drift from what the call above it actually used. Limited
# to the kwargs this module explicitly tunes (the ones that shape scrape behavior), not the full
# ~130-key BrowserConfig/CrawlerRunConfig surface (mostly untouched library defaults, no signal).
# excluded_selector is recorded as a hash, not verbatim (426 chars, rarely changes, source-visible).
# total_budget_s is not a crawl4ai kwarg at all — it's this module's own outer wall-clock guard
# (TOTAL_SCRAPE_BUDGET_S); included here on the same "read the real value, don't re-declare it"
# rule, so the stamp still changes if the guard value ever changes.
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
        # Module constant (not a crawl4ai kwarg), same "read the real value" rule as total_budget_s
        # above — governs the fit->raw content-selection fallback, not a garbage-verdict threshold.
        "min_content_threshold": MIN_CONTENT_THRESHOLD,
    }


# Stable short hash over the config record — cheap "same config" grouping key for a later reader;
# the full config dict alongside it is what makes the value inspectable
def hash_config(config: dict) -> str:
    blob = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


# Read crawl4ai's own anti-bot diagnosis off the result object, verbatim — an OBSERVATION
# surfaced to the log AND to the caller (_format_scrape_output), never used to alter this
# module's own return value. It has documented false positives (e.g. guenstiger.de: "Cloudflare
# JS challenge" reported on a render that returns the full product page) — the caller must
# present it as an observation too, not restate it as a verdict.
def extract_crawl4ai_diagnosis(result) -> dict:
    stats = getattr(result, "crawl_stats", None) or {}
    return {
        "crawl4ai_success": getattr(result, "success", None),
        "crawl4ai_error_message": getattr(result, "error_message", None) or None,
        "crawl4ai_attempts": stats.get("attempts"),
        "crawl4ai_resolved_by": stats.get("resolved_by"),
        "crawl4ai_fallback_fetch_used": stats.get("fallback_fetch_used"),
    }


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


# Detect garbage content: error pages, cookie walls, login walls, navigation dumps. NOT called by
# this module's own scrape_url_workflow/try_scrape (that gate was removed — the agent judges
# content now, not this function). Kept and exported for src/crawler/crawl_site.py's unattended
# BFS batch-crawl filter — a different consumer with no agent reviewing its output, where an
# automatic verdict is still the correct design. Do not reintroduce a call to this from try_scrape.
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


# Render acquisition facts + full content into one text block — facts ALWAYS precede content,
# separated by a fixed "## Content" delimiter, so the shape is identical regardless of outcome
# (thin page, blocked-looking page, or a normal one) and an agent can parse it reliably. Content
# is never replaced by a message about it — even zero content renders as an explicit
# "(no content returned)" line under the same delimiter, not a substituted string standing in for
# the page. crawl4ai's diagnosis is labeled an OBSERVATION, not a verdict, on the line itself —
# not just in a code comment the caller never sees — because it has documented false positives
# (guenstiger.de: reports "Cloudflare JS challenge" on a render that returns the full page).
def _format_scrape_output(url: str, content: str, meta: dict, published_date: str | None) -> str:
    lines = [f"# Content from: {url}", ""]
    if published_date:
        lines.append(f"Published: {published_date}")
    selection_note = " + raw fallback" if meta.get("fallback_to_raw") else ""
    lines += [
        "## Acquisition facts",
        f"- HTTP status: {meta.get('status_code')}",
        # Unconditional, like every other line in this block — this module reports facts, it does
        # not decide which facts the agent gets to see (see this function's own docstring). The
        # requested URL is already in the header above; this is the URL the browser actually
        # returned content from, whatever it is — same as the requested one, different, or absent
        # (None, rendered literally like every other absent value in this block, e.g. HTTP status
        # on a budget_exhausted record) — the agent compares the two itself, nothing here decides
        # "redirected" or "same" on its behalf.
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
