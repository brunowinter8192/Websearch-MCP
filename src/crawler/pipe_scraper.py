# INFRASTRUCTURE
import argparse
import asyncio
import random
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from curl_cffi.requests import AsyncSession

# From src/scraper/scrape_url.py: same config-hash algorithm + crawl4ai diagnosis extraction used
# by the ad-hoc path's log (generic, not path-specific — reused rather than re-implemented)
from src.scraper.scrape_url import hash_config, extract_crawl4ai_diagnosis
# From src/scraper/camoufox_scrape.py: the second acquisition lane's core primitive — reused as-is,
# same engine-switch relationship as the ad-hoc surface (scrape_url_camoufox_workflow), not a
# fallback of the chromium engine
from src.scraper.camoufox_scrape import try_scrape_camoufox
# From src/crawler/pipe_scrape_logger.py: per-URL JSONL log with run/config stamp
from src.crawler.pipe_scrape_logger import log_pipe_scrape

DOWNLOAD_DELAY = 1.0          # Scrapy per-domain base delay (s); jitter = uniform(0.5×, 1.5×)
CONCURRENCY_PER_DOMAIN = 8    # Scrapy per-domain in-flight cap — CHROMIUM engine default
# Camoufox engine's own, much lower default. The chromium engine's 8 was validated (process-docs/
# pipe_scraper_hardening/2026-08-04_stealth_concurrency_probe.md) for a model where 8 concurrent
# in-flight requests share ONE already-launched browser process (cheap per-request marginal cost —
# a new browser context, not a new OS process). try_scrape_camoufox launches a FRESH, real, headed
# Firefox process per call — concurrency_per_domain=8 here would mean up to 8 SIMULTANEOUS headed
# Firefox processes per domain (and unboundedly more across concurrently-processed domains), while
# field evidence already on record for this lane (process-docs/camoufox_lane/) reports Camoufox's
# memory footprint as notably heavier than patchright/undetected-chromium per instance. No
# measurement exists yet for how many concurrent Camoufox instances this machine tolerates —
# per this project's standing rule (a cap is not raised above a proven baseline without evidence),
# defaults to the most conservative value, fully serialized per domain. Raise only with a measured
# reason, the same discipline CONCURRENCY_PER_DOMAIN=8 itself was earned with, not assumed.
CAMOUFOX_CONCURRENCY_PER_DOMAIN = 1
PAGE_TIMEOUT_MS = 15000
DELAY_BEFORE_RETURN_HTML = 0.5
EMPTY_THRESHOLD_BYTES = 100
FALLBACK_FETCH_TIMEOUT_S = 15.0   # symmetric with PAGE_TIMEOUT_MS — comparable worst-case cost per acquisition attempt

# ORCHESTRATOR

# Scrape URL list with Scrapy-style per-domain pacing, write per-URL md files + /tmp report.
# engine: "chromium" (default, current/unchanged behavior) | "camoufox" — a per-RUN choice, not
# per-URL; no auto-selection or fallback between them anywhere in this function or below.
# concurrency_per_domain=None resolves to the ENGINE'S OWN default (CONCURRENCY_PER_DOMAIN for
# chromium, CAMOUFOX_CONCURRENCY_PER_DOMAIN for camoufox) — an explicit value here always wins,
# for either engine, so an operator who knows their machine can still raise it deliberately.
# block_images: only consulted when engine="camoufox" (the chromium engine has no such param, its
# own _build_configs() is fixed) — False by default here, SAME as the ad-hoc lane's own default
# (scrape_url_camoufox_workflow). Settled by design decision, not measurement: Camoufox's own
# LeakWarning documents image-blocking as a known WAF detection signal, and this lane exists
# precisely for hard anti-bot targets — stealth wins over the bandwidth saving. Images never reach
# the output either way (this pipeline produces markdown text), so nothing about the content
# changes; an explicit block_images=True still overrides this default when a caller wants it.
async def scrape_urls_workflow(
    urls: list[str],
    output_dir: Path,
    download_delay: float = DOWNLOAD_DELAY,
    concurrency_per_domain: int | None = None,
    engine: str = "chromium",
    block_images: bool = False,
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = await _scrape_all(urls, output_dir, download_delay, concurrency_per_domain,
                                 engine, block_images)
    wall_s = time.time() - t0
    _print_summary(results, wall_s)
    _write_tmp_report(_domain_from_urls(urls), results)
    return results


# FUNCTIONS

# Derive safe filename from URL
def _url_to_filename(url: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]', '_', url.split('://')[-1])
    slug = re.sub(r'_+', '_', slug).strip('_')[:100]
    return f"{slug}.md"

# Return or create per-domain state entry (lastseen, lock, sem) — asyncio-safe (no await, no race)
def _ensure_domain_state(domain_states: dict, domain: str, concurrency_per_domain: int) -> dict:
    if domain not in domain_states:
        domain_states[domain] = {
            'lastseen': 0.0,
            'lock': asyncio.Lock(),
            'sem': asyncio.Semaphore(concurrency_per_domain),
        }
    return domain_states[domain]

# Scrapy gate: under domain lock, wait until delay elapsed since lastseen, then stamp lastseen=now.
async def _gate_domain(state: dict, download_delay: float) -> None:
    async with state['lock']:
        jitter = random.uniform(0.5 * download_delay, 1.5 * download_delay)
        now = time.time()
        gap = now - state['lastseen']
        if gap < jitter:
            await asyncio.sleep(jitter - gap)
        state['lastseen'] = time.time()

# Read the pacing/browser config actually in effect off the real constructed objects + this
# module's own pacing constants — never re-declare values here, so the stamp can't drift from
# what actually ran (same rule as scrape_url.extract_config_stamp).
def _extract_pipe_config_stamp(
    browser_cfg: BrowserConfig,
    run_cfg: CrawlerRunConfig,
    download_delay: float,
    concurrency_per_domain: int,
) -> dict:
    return {
        "headless": browser_cfg.headless,
        "enable_stealth": browser_cfg.enable_stealth,
        "wait_until": run_cfg.wait_until,
        "page_timeout_ms": run_cfg.page_timeout,
        "delay_before_return_html_s": run_cfg.delay_before_return_html,
        "cache_mode": run_cfg.cache_mode.value,
        "simulate_user": run_cfg.simulate_user,
        "override_navigator": run_cfg.override_navigator,
        "magic": run_cfg.magic,
        "remove_consent_popups": run_cfg.remove_consent_popups,
        # crawl4ai's OWN fallback_fetch_function wiring only (path a) — pipe_scraper's own
        # except-block rescue (path b, _own_fallback_rescue) is unconditional code, not a config
        # object attribute, so it has no stamp field; see pipe_scrape_logger.py's schema comment.
        "fallback_armed": run_cfg.fallback_fetch_function is not None,
        "download_delay_s": download_delay,
        "concurrency_per_domain": concurrency_per_domain,
        "empty_threshold_bytes": EMPTY_THRESHOLD_BYTES,
    }

# Shared low-level curl_cffi GET, underlying BOTH fallback routes — returns the raw curl_cffi
# Response (or None on any exception: timeout, connection error, TLS handshake failure — fail-soft,
# never propagated) so each caller reads only what it needs. Local to this call (no shared/module
# state, no cross-request keying) — safe under _scrape_all's asyncio.gather over hundreds of
# concurrent URLs; nothing here is written or read outside this one function call's own stack.
# response.url is libcurl's EFFECTIVE_URL (curl_cffi 0.16.0 requests/session.py's
# _parse_response: `rsp.url = c.getinfo(CurlInfo.EFFECTIVE_URL)`), always the FINAL url after
# following redirects, never the originally-requested one on a redirecting fetch — confirmed live,
# this venv: GET https://www.rfc-editor.org/rfc/rfc2616 -> status 200, response.url =
# https://www.rfc-editor.org/info/rfc2616/, response.redirect_count = 1. curl_cffi follows
# redirects by default and reports exactly where it landed; the old (None, None) blanket answer on
# both fallback routes was this project's own call site throwing that value away before crawl4ai
# ever got a chance to overwrite it — the fix belongs here, not in crawl4ai.
async def _curl_cffi_get(url: str):
    try:
        async with AsyncSession(impersonate="chrome") as session:
            return await asyncio.wait_for(
                session.get(url, timeout=FALLBACK_FETCH_TIMEOUT_S), timeout=FALLBACK_FETCH_TIMEOUT_S,
            )
    except Exception:
        return None

# Plain-HTTP-with-browser-TLS-fingerprint acquisition attempt for the case where the BROWSER is
# the weaker client: a capture run took 0/23 on crossref.org, every URL empty at the ~15s
# page-load ceiling with no HTTP status, while plain curl on the same URLs returned HTTP 200 /
# 79274 bytes in 7.2s (process-docs/pipe_scraper_hardening/). curl_cffi impersonate="chrome"
# carries a real browser TLS fingerprint, not just a UA string — an httpx/requests fallback would
# be the weaker client again and defeat the purpose (process-docs/news_pipeline/: impersonate=
# "chrome" got 80/425 proxies through Cloudflare with HTTP 200 where another client managed
# 0/17202, the isolating variable being the TLS fingerprint alone). Wired DIRECTLY into
# CrawlerRunConfig.fallback_fetch_function (path a) — crawl4ai's own mechanism, invoked when the
# browser returns a non-exception result that is_blocked() flags; crawl4ai calls this exact
# function and consumes the return value itself (async_webcrawler.py: `_fallback_html =
# await _fallback_fn(url)`, then treats it directly as HTML text), so this signature (str | None)
# is a contract, not just this module's own choice — a tuple return here would break that wiring.
# _own_fallback_rescue (path b) does NOT call this — it calls _curl_cffi_get directly instead, to
# also read the landed URL this function's return shape has no room for (see that function).
# Thin wrapper over _curl_cffi_get. status_code != 200 gate is deliberate: crawl4ai's own fallback
# wiring forces status_code=200 on ANY non-empty return value regardless of what actually happened,
# so if curl_cffi itself got blocked (403/429) but still returned an HTML block page, returning it
# anyway would make crawl4ai mark that a false success.
async def _fallback_fetch(url: str) -> str | None:
    response = await _curl_cffi_get(url)
    if response is None or response.status_code != 200:
        return None
    return response.text

# pipe_scraper's OWN fallback rescue (path b) — called only from _scrape_one's except block, the
# one place crawl4ai's own fallback_fetch_function cannot reach at max_retries=0 (browser call
# raised outright, no crawl_result ever formed). Calls _curl_cffi_get directly (not _fallback_fetch)
# specifically to also read response.url — the landed URL curl_cffi actually ended up on, real and
# available at this call site (unlike path a, see _fallback_fetch's comment). Converts the fetched
# HTML to markdown via crawl4ai's own raw:// pipeline (verified: raw:// URLs run through the same
# DefaultMarkdownGenerator, are exempted from anti-bot/fallback machinery entirely — no recursion
# risk from reusing run_cfg's fallback_fetch_function here) rather than hand-rolling HTML-to-markdown.
# Returns (outcome, http_status, byte_count, pipe_fallback_used, pipe_fallback_resolved, landed_url).
# landed_url is recorded whenever a response was actually obtained (regardless of status_code) —
# redirect behaviour was genuinely observed either way; None only when _curl_cffi_get itself
# returned None (the fetch never completed at all: exception, timeout).
# pipe_fallback_resolved describes the FETCH (curl_cffi returned a genuine 200 with a body) — it is
# NOT about whether that body converted into usable markdown, which is what `outcome` describes.
# The two can legitimately disagree: resolved=True with outcome="empty" means curl_cffi got a real
# 200 but the raw://-pipeline conversion produced too little content to clear
# EMPTY_THRESHOLD_BYTES — read that as "fetch worked, content didn't", not as a contradiction.
# http_status is 200 ONLY when pipe_fallback_resolved is True (a real curl_cffi 200) — never faked,
# unlike crawl4ai's own fallback wiring which forces 200 regardless of the real outcome. Same
# status_code != 200 gate as _fallback_fetch (see that function's comment) — a curl-side block
# must not be treated as a genuine rescue, independent of whether landed_url is known.
async def _own_fallback_rescue(
    crawler: AsyncWebCrawler, url: str, run_cfg: CrawlerRunConfig, output_dir: Path,
) -> tuple[str, int | None, int, bool, bool, str | None]:
    response = await _curl_cffi_get(url)
    landed_url = (response.url or None) if response is not None else None
    if response is None or response.status_code != 200:
        return 'error', None, 0, True, False, landed_url
    html = response.text
    if not html:
        return 'error', None, 0, True, False, landed_url
    try:
        fb_result = await crawler.arun(url=f"raw://{html}", config=run_cfg)
        raw_md = (fb_result.markdown.raw_markdown if fb_result.markdown else '') or ''
    except Exception:
        raw_md = ''
    byte_count = len(raw_md.encode('utf-8'))
    if raw_md:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{raw_md}", encoding='utf-8')
    outcome = 'ok' if byte_count >= EMPTY_THRESHOLD_BYTES else 'empty'
    return outcome, 200, byte_count, True, True, landed_url

# Read landed_url off the successful, non-exception result — but ONLY when crawl4ai's OWN
# fallback_fetch_function was NOT the route that produced this result (diagnosis["crawl4ai_
# fallback_fetch_used"]). Verified in the installed crawl4ai 0.9.2 source
# (async_webcrawler.py, the fallback_fetch_function block, ~line 580): on that route
# redirected_url is hardcoded to the ORIGINAL requested url regardless of what curl_cffi's own
# fetch actually followed — recording it verbatim would report a fabricated fact. None on that
# route, DELIBERATELY not fixed: curl_cffi's own _fallback_fetch (called BY crawl4ai internally
# here, not by our own code) returns only a str per crawl4ai's own contract (see _fallback_fetch's
# comment) — there is no channel back out of that call for the landed URL crawl4ai itself does not
# surface. Reaching in via a module-level dict keyed by url would work in the common case but is
# explicitly rejected: _scrape_all runs asyncio.gather over hundreds of URLs at once, and anything
# keyed that loosely risks cross-contamination if the same URL is ever in flight twice in one run,
# plus unbounded growth/cleanup concerns for no clean ownership story. An honest None beats a
# fragile channel. pipe_scraper's OWN rescue (_own_fallback_rescue, path b) is DIFFERENT: it calls
# _curl_cffi_get directly (its own call, not one crawl4ai mediates), so it reads response.url
# itself and reports a real landed_url — see that function's own comment. No verdict computed
# here or anywhere in this module: an agent reading the log has both "url" and "landed_url" in the
# same record and compares them itself (see process-docs/scrape_pipeline/
# content_judgment_removal_2026-08-05.md for the same reasoning applied to content judgment).
def _landed_url_from_result(result, diagnosis: dict) -> str | None:
    if diagnosis.get("crawl4ai_fallback_fetch_used"):
        return None
    return getattr(result, "redirected_url", None)


# Assemble and write one JSONL record for a single URL's outcome — fail-soft via log_pipe_scrape.
# CHROMIUM engine only — see _log_pipe_camoufox_record for the camoufox engine's own record shape
# (deliberately NOT this same function with extra optional params: the crawl4ai-own-fallback and
# pipe-own-rescue fields below are CHROMIUM-lane machinery that never runs on the camoufox engine
# at all, so forcing them into every camoufox record as False/None would misrepresent a mechanism
# that was never even in play — same "absent, not null" discipline as scrape_logger.py's schema).
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


# Assemble and write one JSONL record for a single URL's camoufox-engine outcome — SIBLING to
# _log_pipe_record, not a shared function with it: this engine has no crawl4ai-own-fallback, no
# pipe-own-rescue (both are chromium-lane machinery that does not run here at all — camoufox IS
# the deliberate alternative engine; a fallback of the alternative would be exactly the
# auto-selection/trigger logic this whole lane exists to avoid), and has its own two facts the
# chromium engine has no concept of (markdown_conversion_error, content_is_raw_html). config/
# config_hash are read straight off THIS URL's own meta (try_scrape_camoufox computes them per
# call, same as the ad-hoc lane's scrape_url_camoufox_workflow) — there is no upfront, whole-run
# config object to stamp once the way the chromium engine's _build_configs() provides.
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
        "config_hash": meta.get("config_hash"), "config": meta.get("config"),
    })

# Scrape one URL: acquire domain semaphore cap, gate on per-domain delay, then run crawler.
async def _scrape_one(
    crawler: AsyncWebCrawler,
    url: str,
    run_cfg: CrawlerRunConfig,
    domain_states: dict,
    download_delay: float,
    concurrency_per_domain: int,
    output_dir: Path,
    run_ctx: dict,
) -> dict:
    domain = urlparse(url).netloc
    state = _ensure_domain_state(domain_states, domain, concurrency_per_domain)
    async with state['sem']:
        await _gate_domain(state, download_delay)
        # Stamped here, not before the semaphore/gate: asyncio.gather starts every _scrape_one
        # coroutine at once, so a ts taken before the gate would record queue time (identical
        # across an entire run) instead of actual request start.
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        t0 = time.time()
        try:
            result = await crawler.arun(url=url, config=run_cfg)
        except Exception:
            # crawl4ai's own fallback_fetch_function cannot reach this failure mode at
            # max_retries=0 (verified: the browser exception re-raises past that block entirely
            # for a single-implicit-proxy/no-retry config — this except clause is the only place
            # that failure mode is ever seen). wall_ms below deliberately includes this rescue
            # attempt's full cost on top of the failed browser attempt — see pipe_scrape_logger.py's
            # wall_ms schema note.
            outcome, status, byte_count, fb_used, fb_resolved, landed_url = await _own_fallback_rescue(
                crawler, url, run_cfg, output_dir)
            wall_ms = int((time.time() - t0) * 1000)
            _log_pipe_record(run_ctx, ts, url, domain, outcome, status, byte_count, wall_ms, {},
                              pipe_fallback_used=fb_used, pipe_fallback_resolved=fb_resolved,
                              landed_url=landed_url)
            return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count,
                    'status_code': status, 'outcome': outcome}
        wall_ms = int((time.time() - t0) * 1000)

    raw_md = (result.markdown.raw_markdown if result.markdown else '') or ''
    status = getattr(result, 'status_code', None)
    byte_count = len(raw_md.encode('utf-8'))

    if status == 429:
        outcome = 'waf_429'
    elif status and status >= 400:
        outcome = 'http_error'
    elif byte_count < EMPTY_THRESHOLD_BYTES:
        outcome = 'empty'
    else:
        outcome = 'ok'

    if raw_md:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{raw_md}", encoding='utf-8')

    diagnosis = extract_crawl4ai_diagnosis(result)
    landed_url = _landed_url_from_result(result, diagnosis)
    _log_pipe_record(run_ctx, ts, url, domain, outcome, status, byte_count, wall_ms, diagnosis,
                      landed_url=landed_url)

    return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count,
            'status_code': status, 'outcome': outcome}

# Scrape one URL via the CAMOUFOX engine: SAME per-domain semaphore/gate as _scrape_one (the
# pacing gate is engine-agnostic — see CAMOUFOX_CONCURRENCY_PER_DOMAIN's own comment for why the
# VALUE differs even though the MECHANISM doesn't), but no shared browser/crawler to pass in —
# try_scrape_camoufox launches and tears down its own per call. No crawl4ai-own-fallback, no
# pipe-own-rescue: both are chromium-lane machinery (see _log_pipe_camoufox_record's comment) —
# there is no except-block rescue path here at all, try_scrape_camoufox is already fail-soft on
# its own (acquisition_error covers everything that would otherwise need a rescue).
async def _scrape_one_camoufox(
    url: str,
    domain_states: dict,
    download_delay: float,
    concurrency_per_domain: int,
    output_dir: Path,
    run_ctx: dict,
    block_images: bool,
) -> dict:
    domain = urlparse(url).netloc
    state = _ensure_domain_state(domain_states, domain, concurrency_per_domain)
    async with state['sem']:
        await _gate_domain(state, download_delay)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        t0 = time.time()
        content, meta = await try_scrape_camoufox(url, block_images=block_images)
        wall_ms = int((time.time() - t0) * 1000)

    status = meta.get('status_code')
    byte_count = len(content.encode('utf-8')) if content else 0

    # acquisition_error checked FIRST and maps to outcome='error' — the same meaning 'error' has
    # on the chromium engine (total acquisition failure, nothing usable at all): budget_exhausted/
    # browser_missing/exception all leave status_code=None and content empty, which would
    # otherwise fall through to 'empty' below and misreport a hard acquisition failure as merely
    # "browser succeeded, page had nothing."
    if meta.get('acquisition_error'):
        outcome = 'error'
    elif status == 429:
        outcome = 'waf_429'
    elif status and status >= 400:
        outcome = 'http_error'
    elif byte_count < EMPTY_THRESHOLD_BYTES:
        outcome = 'empty'
    else:
        outcome = 'ok'

    # Written to the SAME .md filename convention regardless of content_is_raw_html (matching the
    # ad-hoc lane's own sidecar precedent) — format ambiguity is resolved via the LOG record
    # (content_is_raw_html), not by the filename lying about what it contains either way.
    if content:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{content}", encoding='utf-8')

    _log_pipe_camoufox_record(run_ctx, ts, url, domain, outcome, status, byte_count, wall_ms, meta)

    return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count,
            'status_code': status, 'outcome': outcome}

# Construct the browser/run config actually used for a scrape run — factored out (not inlined in
# _scrape_all) so a test can exercise the SAME real objects crawl4ai wires against, not a
# re-declared copy. Anti-bot posture only; no extraction-side settings (no content filter, no
# preserve_tags) — this path optimizes for getting through, not extraction quality (the capture
# skill's Phase 3 LLM step does all cleanup afterwards).
def _build_configs() -> tuple[BrowserConfig, CrawlerRunConfig]:
    browser_cfg = BrowserConfig(
        headless=True,
        verbose=False,
        # Verified working on the installed stack, not assumed: crawl4ai 0.9.2's StealthAdapter
        # (browser_adapter.py) imports playwright_stealth's `Stealth` class; playwright-stealth
        # 2.0.3 provides it. The older `stealth_async` ImportError recorded against crawl4ai 0.8.6
        # + playwright-stealth 2.0.2 (process-docs/scrape_pipeline/crawl4ai_stealth_stack_2026-05-31.md)
        # no longer applies on this stack — confirmed live and by
        # tests/test_pipe_scraper.py's wiring test, which asserts against crawl4ai's own
        # BrowserManager/StealthAdapter objects rather than trusting this flag alone (StealthAdapter
        # silently degrades to a no-op on ImportError with no error raised anywhere — a flag-only
        # check would not have caught the 2026-05-31 break).
        # Reachable here specifically because pipe_scraper passes no crawler_strategy/adapter to
        # AsyncWebCrawler: browser_manager.py only builds the StealthAdapter when
        # `enable_stealth and not use_undetected`, and use_undetected resolves from
        # `isinstance(self.adapter, UndetectedAdapter)` (async_crawler_strategy.py:117) — default
        # adapter here is PlaywrightAdapter, so that condition holds. The moment anyone passes a
        # custom crawler_strategy/adapter to this module, re-check that this still resolves True.
        # Measured to hold at CONCURRENCY_PER_DOMAIN=8 on the 316-URL reference set, 0 crashes
        # (process-docs/pipe_scraper_hardening/2026-08-04_stealth_concurrency_probe.md). Second
        # effect worth naming: crawl4ai only appends --disable-gpu/--disable-gpu-compositing/
        # --disable-software-rasterizer when enable_stealth is FALSE (browser_manager.py) — its
        # own comment says those flags disable WebGL, which anti-bot sensors read as headless.
        # UndetectedAdapter (the OTHER stealth mechanism, used by src/scraper/scrape_url.py) is
        # NOT used here: crawl4ai issue #1500 documents crashes above concurrency 1 ("Target
        # page/context/browser has been closed"), incompatible by construction with this path's
        # CONCURRENCY_PER_DOMAIN=8 on a pacing model validated at that concurrency.
        enable_stealth=True,
    )
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded",
        delay_before_return_html=DELAY_BEFORE_RETURN_HTML,
        page_timeout=PAGE_TIMEOUT_MS,
        markdown_generator=DefaultMarkdownGenerator(),
        # Mouse-move + scroll signals anti-bot systems look for. async_crawler_strategy.py gates
        # this on `config.simulate_user or config.magic` (~line 978) — available without magic's
        # other, unwanted effect (see magic=False below).
        simulate_user=True,
        # navigator_overrider init script. Same file gates it on
        # `config.override_navigator or config.simulate_user or config.magic` (~line 598) — also
        # available without magic.
        override_navigator=True,
        # Explicitly False, not left at the implicit default — likely to look like a missed
        # improvement to a later reader, so the full reasoning, not a summary: magic bundles
        # simulate_user + override_navigator (both already taken individually above, same effect)
        # PLUS a random user-agent via ValidUAGenerator, triggered by
        # `config.magic or config.user_agent_mode == "random"` (async_crawler_strategy.py:553-554).
        # At CONCURRENCY_PER_DOMAIN=8 that means eight different generated UAs from one IP hitting
        # one domain at once — a signal in itself. A generated UA also has no knowledge of which
        # Chromium build is actually running in this browser instance; a UA/browser-version
        # mismatch is a documented anti-bot flagging signal in scraper-practitioner reports. Net:
        # take the two useful magic effects individually (above), leave the user-agent alone (the
        # real installed browser's own UA).
        magic=False,
        # The capture skill DELETES a confirmed block page outright rather than cleaning it
        # (skills/websearch-capture-and-index/SKILL.md Phase 3: "A confirmed block page is
        # garbage -> DELETE it") — so on THIS path an un-dismissed consent wall is a LOST page, a
        # reachability problem, not a cosmetic one. This is the opposite framing from
        # src/scraper/scrape_url.py, where the same switch is a content-quality measure (an
        # un-dismissed consent wall there degrades one answer, doesn't delete a page outright) —
        # that asymmetry is why the setting transfers to this path at all, not just because it
        # worked well there. Bounded cost: 1.3s worst case, counted from remove_consent_popups.js's
        # six wait sites (five 300ms, one 500ms) + the Python-side sleep
        # (process-docs/time_budget/2026-08-04_config_rules_and_the_promised_maximum.md).
        remove_consent_popups=True,
        # crawl4ai's OWN fallback mechanism (path a) — invoked internally when the browser returns
        # a non-exception result that is_blocked() flags (e.g. HTTP 403/503 block page, HTTP 200 +
        # near-empty body). Confirmed working at max_retries=0 (this module's default — never
        # raised, see _own_fallback_rescue's comment for why) via a local synthetic-server test: a
        # near-empty HTTP 200 response correctly triggered is_blocked()'s "HTTP 200 + near-empty
        # content" branch and the fallback fired. Costs nothing when nothing is blocked. Does NOT
        # cover the browser-raised-an-exception case — that is _own_fallback_rescue, called
        # directly from _scrape_one's except block, a separate mechanism (see that function's
        # comment for why max_retries was deliberately NOT raised to reach this case here instead).
        fallback_fetch_function=_fallback_fetch,
        verbose=False,
    )
    return browser_cfg, run_cfg

# Scrape all URLs with per-domain Scrapy-style pacing — dispatches to ONE of two engines per RUN
# (never per-URL, never auto-selected). concurrency_per_domain=None resolves to the ENGINE's own
# default here (not in scrape_urls_workflow) so any direct caller of this function gets the same
# engine-aware default scrape_urls_workflow provides.
#
# CHROMIUM: one shared AsyncWebCrawler across all in-flight requests (cheap per-request marginal
# cost), one upfront config stamp for the whole run (_extract_pipe_config_stamp).
# CAMOUFOX: no shared browser to construct — try_scrape_camoufox launches/tears down its own per
# call — so there is no upfront config object to stamp either; each URL's own record reads
# config/config_hash off THAT call's own meta (see _log_pipe_camoufox_record). block_images is
# only meaningful here (chromium's _build_configs() has no such param at all).
async def _scrape_all(
    urls: list[str],
    output_dir: Path,
    download_delay: float,
    concurrency_per_domain: int | None,
    engine: str = "chromium",
    block_images: bool = False,
) -> list[dict]:
    resolved_concurrency = concurrency_per_domain if concurrency_per_domain is not None else (
        CAMOUFOX_CONCURRENCY_PER_DOMAIN if engine == "camoufox" else CONCURRENCY_PER_DOMAIN
    )
    domain_states: dict = {}

    if engine == "camoufox":
        run_ctx = {"run_id": str(uuid.uuid4())}
        raw = await asyncio.gather(
            *[_scrape_one_camoufox(url, domain_states, download_delay, resolved_concurrency,
                                    output_dir, run_ctx, block_images)
              for url in urls],
            return_exceptions=True,
        )
    else:
        browser_cfg, run_cfg = _build_configs()
        config_stamp = _extract_pipe_config_stamp(browser_cfg, run_cfg, download_delay, resolved_concurrency)
        run_ctx = {
            "run_id": str(uuid.uuid4()),
            "config_hash": hash_config(config_stamp),
            "config": config_stamp,
        }
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            raw = await asyncio.gather(
                *[_scrape_one(crawler, url, run_cfg, domain_states,
                              download_delay, resolved_concurrency, output_dir, run_ctx)
                  for url in urls],
                return_exceptions=True,
            )
    return [
        r if isinstance(r, dict)
        else {'url': urls[i], 'outcome': 'error', 'wall_ms': 0, 'bytes': 0, 'status_code': None}
        for i, r in enumerate(raw)
    ]

# Extract domain string from first URL (used for /tmp report filename)
def _domain_from_urls(urls: list[str]) -> str:
    if not urls:
        return 'unknown'
    return urlparse(urls[0]).netloc.replace('.', '_')

# Write per-URL report to /tmp/<domain>_scrape_report.md
def _write_tmp_report(domain: str, results: list[dict]) -> None:
    path = Path(f"/tmp/{domain}_scrape_report.md")
    lines = [
        f"# Scrape Report — {domain}",
        "",
        f"Total: {len(results)} URLs",
        "",
        "| outcome | status | bytes | wall_ms | url |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['outcome']} | {r.get('status_code') or '-'} | "
            f"{r['bytes']} | {r['wall_ms']} | {r['url']} |"
        )
    path.write_text('\n'.join(lines), encoding='utf-8')

# Print one-line console summary
def _print_summary(results: list[dict], wall_s: float) -> None:
    ok = sum(1 for r in results if r['outcome'] == 'ok')
    total = len(results)
    err = total - ok
    print(f"Scraped {ok}/{total} ok, {err} errors in {wall_s:.0f}s")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pipe scraper — crawl URL list to markdown with Scrapy-style per-domain pacing')
    parser.add_argument('--url-file', required=True, help='Text file with URLs (one per line)')
    parser.add_argument('--output-dir', required=True, help='Directory to write per-URL markdown files')
    parser.add_argument('--download-delay', type=float, default=DOWNLOAD_DELAY,
                        help=f'Scrapy per-domain base delay in seconds (default: {DOWNLOAD_DELAY}); actual jitter = uniform(0.5×, 1.5×)')
    # No literal default here (None) — scrape_urls_workflow/_scrape_all resolve the ENGINE'S OWN
    # default (8 chromium, 1 camoufox) when this flag is absent; an explicit value always wins.
    parser.add_argument('--concurrency-per-domain', type=int, default=None,
                        help=f'Per-domain in-flight request cap (default: {CONCURRENCY_PER_DOMAIN} '
                             f'chromium / {CAMOUFOX_CONCURRENCY_PER_DOMAIN} camoufox — resolved by --engine when omitted)')
    parser.add_argument('--engine', choices=['chromium', 'camoufox'], default='chromium',
                        help='Acquisition engine, chosen per RUN not per URL: "chromium" (crawl4ai, '
                             'default, current behavior) or "camoufox" (Playwright-Firefox, a '
                             'deliberate second lane — not a fallback of chromium)')
    # default=False on THIS action is what actually applies when the flag is omitted — argparse
    # resolves a shared dest's default from the first action added that lacks a namespace value
    # yet, so this default (not --no-block-images's) governs omission.
    parser.add_argument('--block-images', dest='block_images', action='store_true', default=False,
                        help='camoufox engine only: block image requests (default: off — stealth '
                             'wins over bandwidth; Camoufox\'s own LeakWarning documents '
                             'image-blocking as a WAF detection signal)')
    parser.add_argument('--no-block-images', dest='block_images', action='store_false',
                        help='camoufox engine only: allow image requests (default)')
    args = parser.parse_args()

    urls = [ln.strip() for ln in Path(args.url_file).read_text(encoding='utf-8').splitlines()
            if ln.strip()]
    asyncio.run(scrape_urls_workflow(
        urls, Path(args.output_dir), args.download_delay, args.concurrency_per_domain,
        args.engine, args.block_images,
    ))
