# INFRASTRUCTURE
import asyncio
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from curl_cffi.requests import AsyncSession

# From src/crawler/pipe_scraper_constants.py: shared pacing/timeout/threshold values
from src.crawler.pipe_scraper_constants import FALLBACK_FETCH_TIMEOUT_S, EMPTY_THRESHOLD_BYTES
# From src/crawler/pipe_scraper_pacing.py: per-domain Scrapy pacing gate
from src.crawler.pipe_scraper_pacing import _ensure_domain_state, _gate_domain
# From src/crawler/pipe_scraper_records.py: JSONL record assemblers (chromium + camoufox engines)
from src.crawler.pipe_scraper_records import _log_pipe_record, _log_pipe_camoufox_record
# From src/scraper/scrape_url.py: crawl4ai diagnosis extraction, reused as-is (generic, not path-specific)
from src.scraper.scrape_url import extract_crawl4ai_diagnosis
# From src/scraper/camoufox_scrape.py: the camoufox engine's own acquisition primitive
from src.scraper.camoufox_scrape import try_scrape_camoufox

# FUNCTIONS

# Derive safe filename from URL
def _url_to_filename(url: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]', '_', url.split('://')[-1])
    slug = re.sub(r'_+', '_', slug).strip('_')[:100]
    return f"{slug}.md"

# Shared low-level curl_cffi GET underlying both fallback routes — fail-soft, returns the raw
# curl_cffi Response or None on any exception; response.url is libcurl's EFFECTIVE_URL (final URL
# after redirects). Full sourced rationale in src/crawler/DOCS.md.
async def _curl_cffi_get(url: str):
    try:
        async with AsyncSession(impersonate="chrome") as session:
            return await asyncio.wait_for(
                session.get(url, timeout=FALLBACK_FETCH_TIMEOUT_S), timeout=FALLBACK_FETCH_TIMEOUT_S,
            )
    except Exception:
        return None

# Path (a): crawl4ai's own fallback_fetch_function — plain-HTTP-with-browser-TLS-fingerprint
# acquisition for when the browser is the weaker client. Signature (str | None) is a contract with
# crawl4ai, consumed directly as HTML text — see src/crawler/DOCS.md.
async def _fallback_fetch(url: str) -> str | None:
    response = await _curl_cffi_get(url)
    if response is None or response.status_code != 200:
        return None
    return response.text

# Path (b): pipe_scraper's own fallback rescue, called only from _scrape_one's except block — the
# one place crawl4ai's own fallback_fetch_function cannot reach at max_retries=0. Calls
# _curl_cffi_get directly (not _fallback_fetch) to also read the landed URL. Returns (outcome,
# http_status, byte_count, pipe_fallback_used, pipe_fallback_resolved, landed_url) — full sourced
# rationale (raw: prefix, resolved-vs-outcome semantics) in src/crawler/DOCS.md.
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
        fb_result = await crawler.arun(url=f"raw:{html}", config=run_cfg)
        raw_md = (fb_result.markdown.raw_markdown if fb_result.markdown else '') or ''
    except Exception:
        raw_md = ''
    byte_count = len(raw_md.encode('utf-8'))
    if raw_md:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{raw_md}", encoding='utf-8')
    outcome = 'ok' if byte_count >= EMPTY_THRESHOLD_BYTES else 'empty'
    return outcome, 200, byte_count, True, True, landed_url

# Read landed_url off a successful, non-exception result — null on crawl4ai's own fallback route
# (path a), where redirected_url is hardcoded to the requested url regardless of what curl_cffi's
# own fetch actually followed. See src/crawler/DOCS.md Gotchas for the full sourced rationale.
def _landed_url_from_result(result, diagnosis: dict) -> str | None:
    if diagnosis.get("crawl4ai_fallback_fetch_used"):
        return None
    return getattr(result, "redirected_url", None)

# Scrape one URL via the CHROMIUM engine: acquire domain semaphore cap, gate on per-domain delay,
# run crawler, rescue via _own_fallback_rescue on a hard browser exception.
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
        # Stamped after the gate, not before — see src/crawler/DOCS.md Gotchas
        # (test_scrape_one_ts_reflects_request_start_not_queue_time).
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        t0 = time.time()
        try:
            result = await crawler.arun(url=url, config=run_cfg)
        except Exception:
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

# Scrape one URL via the CAMOUFOX engine: same per-domain pacing gate as _scrape_one, no shared
# browser (try_scrape_camoufox launches/tears down its own per call), no crawl4ai-own-fallback/
# pipe-own-rescue at all (chromium-lane machinery only — see src/crawler/DOCS.md).
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

    # acquisition_error maps to outcome='error' FIRST — budget_exhausted/browser_missing/exception
    # leave status_code=None and content empty, which would otherwise misreport as 'empty'.
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

    if content:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{content}", encoding='utf-8')

    _log_pipe_camoufox_record(run_ctx, ts, url, domain, outcome, status, byte_count, wall_ms, meta)

    return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count,
            'status_code': status, 'outcome': outcome}
