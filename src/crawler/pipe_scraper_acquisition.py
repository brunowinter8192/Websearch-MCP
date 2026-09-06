# INFRASTRUCTURE
import asyncio
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from curl_cffi.requests import AsyncSession

# From src/crawler/pipe_scraper_constants.py: shared pacing/timeout values
from src.crawler.pipe_scraper_constants import FALLBACK_FETCH_TIMEOUT_S
# From src/crawler/pipe_scraper_pacing.py: per-domain Scrapy pacing gate
from src.crawler.pipe_scraper_pacing import _ensure_domain_state, _gate_domain
# From src/crawler/pipe_scraper_records.py: JSONL record assemblers (chromium + camoufox engines)
from src.crawler.pipe_scraper_records import _log_pipe_record, _log_pipe_camoufox_record
# From src/scraper/chromium_scrape.py: crawl4ai diagnosis extraction, reused as-is (generic, not path-specific)
from src.scraper.chromium_scrape import extract_crawl4ai_diagnosis
# From src/scraper/camoufox_scrape.py: the camoufox engine's own acquisition primitive
from src.scraper.camoufox_scrape import try_scrape_camoufox

# FUNCTIONS

# Derive safe filename from URL
def _url_to_filename(url: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]', '_', url.split('://')[-1])
    slug = re.sub(r'_+', '_', slug).strip('_')[:100]
    return f"{slug}.md"

# Shared low-level curl_cffi GET underlying both fallback routes — fail-soft, returns Response or None
async def _curl_cffi_get(url: str):
    try:
        async with AsyncSession(impersonate="chrome") as session:
            return await asyncio.wait_for(
                session.get(url, timeout=FALLBACK_FETCH_TIMEOUT_S), timeout=FALLBACK_FETCH_TIMEOUT_S,
            )
    except Exception:
        return None

# Path (a): crawl4ai's own fallback_fetch_function — plain-HTTP-with-browser-TLS-fingerprint acquisition
async def _fallback_fetch(url: str) -> str | None:
    response = await _curl_cffi_get(url)
    if response is None or response.status_code != 200:
        return None
    return response.text

# Path (b): pipe_scraper's own fallback rescue, called from _scrape_one's except block on a hard browser exception
async def _own_fallback_rescue(
    crawler: AsyncWebCrawler, url: str, run_cfg: CrawlerRunConfig, output_dir: Path,
) -> tuple[int | None, int, bool, bool, str | None]:
    response = await _curl_cffi_get(url)
    landed_url = (response.url or None) if response is not None else None
    if response is None or response.status_code != 200:
        return None, 0, True, False, landed_url
    html = response.text
    if not html:
        return None, 0, True, False, landed_url
    try:
        fb_result = await crawler.arun(url=f"raw:{html}", config=run_cfg)
        raw_md = (fb_result.markdown.raw_markdown if fb_result.markdown else '') or ''
    except Exception:
        raw_md = ''
    byte_count = len(raw_md.encode('utf-8'))
    if raw_md:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{raw_md}", encoding='utf-8')
    return 200, byte_count, True, True, landed_url

# Read landed_url off a successful result — null on crawl4ai's own fallback route (path a)
def _landed_url_from_result(result, diagnosis: dict) -> str | None:
    if diagnosis.get("crawl4ai_fallback_fetch_used"):
        return None
    return getattr(result, "redirected_url", None)

# Scrape one URL via the CHROMIUM engine, with per-domain pacing + fallback rescue on a hard exception
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
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        t0 = time.time()
        try:
            result = await crawler.arun(url=url, config=run_cfg)
        except Exception:
            status, byte_count, fb_used, fb_resolved, landed_url = await _own_fallback_rescue(
                crawler, url, run_cfg, output_dir)
            wall_ms = int((time.time() - t0) * 1000)
            _log_pipe_record(run_ctx, ts, url, domain, status, byte_count, wall_ms, {},
                              pipe_fallback_used=fb_used, pipe_fallback_resolved=fb_resolved,
                              landed_url=landed_url)
            return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count, 'status_code': status}
        wall_ms = int((time.time() - t0) * 1000)

    raw_md = (result.markdown.raw_markdown if result.markdown else '') or ''
    status = getattr(result, 'status_code', None)
    byte_count = len(raw_md.encode('utf-8'))

    if raw_md:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{raw_md}", encoding='utf-8')

    diagnosis = extract_crawl4ai_diagnosis(result)
    landed_url = _landed_url_from_result(result, diagnosis)
    _log_pipe_record(run_ctx, ts, url, domain, status, byte_count, wall_ms, diagnosis,
                      landed_url=landed_url)

    return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count, 'status_code': status}

# Scrape one URL via the CAMOUFOX engine, with the same per-domain pacing gate as _scrape_one
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

    if content:
        fname = _url_to_filename(url)
        (output_dir / fname).write_text(f"<!-- source: {url} -->\n\n{content}", encoding='utf-8')

    _log_pipe_camoufox_record(run_ctx, ts, url, domain, status, byte_count, wall_ms, meta)

    return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count, 'status_code': status}
