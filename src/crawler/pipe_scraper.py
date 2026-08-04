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

# From src/scraper/scrape_url.py: same config-hash algorithm + crawl4ai diagnosis extraction used
# by the ad-hoc path's log (generic, not path-specific — reused rather than re-implemented)
from src.scraper.scrape_url import hash_config, extract_crawl4ai_diagnosis
# From src/crawler/pipe_scrape_logger.py: per-URL JSONL log with run/config stamp
from src.crawler.pipe_scrape_logger import log_pipe_scrape

DOWNLOAD_DELAY = 1.0          # Scrapy per-domain base delay (s); jitter = uniform(0.5×, 1.5×)
CONCURRENCY_PER_DOMAIN = 8    # Scrapy per-domain in-flight cap
PAGE_TIMEOUT_MS = 15000
DELAY_BEFORE_RETURN_HTML = 0.5
EMPTY_THRESHOLD_BYTES = 100

# ORCHESTRATOR

# Scrape URL list with Scrapy-style per-domain pacing, write per-URL md files + /tmp report.
async def scrape_urls_workflow(
    urls: list[str],
    output_dir: Path,
    download_delay: float = DOWNLOAD_DELAY,
    concurrency_per_domain: int = CONCURRENCY_PER_DOMAIN,
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = await _scrape_all(urls, output_dir, download_delay, concurrency_per_domain)
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
        "download_delay_s": download_delay,
        "concurrency_per_domain": concurrency_per_domain,
        "empty_threshold_bytes": EMPTY_THRESHOLD_BYTES,
    }

# Assemble and write one JSONL record for a single URL's outcome — fail-soft via log_pipe_scrape
def _log_pipe_record(
    run_ctx: dict, ts: str, url: str, domain: str, outcome: str,
    status: int | None, byte_count: int, wall_ms: int, diagnosis: dict,
) -> None:
    log_pipe_scrape({
        "ts": ts, "run_id": run_ctx["run_id"], "url": url, "domain": domain,
        "outcome": outcome, "http_status": status, "bytes": byte_count, "wall_ms": wall_ms,
        "crawl4ai_success": diagnosis.get("crawl4ai_success"),
        "crawl4ai_error_message": diagnosis.get("crawl4ai_error_message"),
        "crawl4ai_attempts": diagnosis.get("crawl4ai_attempts"),
        "crawl4ai_resolved_by": diagnosis.get("crawl4ai_resolved_by"),
        "crawl4ai_fallback_fetch_used": diagnosis.get("crawl4ai_fallback_fetch_used"),
        "config_hash": run_ctx["config_hash"], "config": run_ctx["config"],
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
            wall_ms = int((time.time() - t0) * 1000)
            _log_pipe_record(run_ctx, ts, url, domain, 'error', None, 0, wall_ms, {})
            return {'url': url, 'wall_ms': wall_ms,
                    'bytes': 0, 'status_code': None, 'outcome': 'error'}
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
    _log_pipe_record(run_ctx, ts, url, domain, outcome, status, byte_count, wall_ms, diagnosis)

    return {'url': url, 'wall_ms': wall_ms, 'bytes': byte_count,
            'status_code': status, 'outcome': outcome}

# Scrape all URLs under a single crawler with per-domain Scrapy-style pacing.
async def _scrape_all(
    urls: list[str],
    output_dir: Path,
    download_delay: float,
    concurrency_per_domain: int,
) -> list[dict]:
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded",
        delay_before_return_html=DELAY_BEFORE_RETURN_HTML,
        page_timeout=PAGE_TIMEOUT_MS,
        markdown_generator=DefaultMarkdownGenerator(),
        verbose=False,
    )
    config_stamp = _extract_pipe_config_stamp(browser_cfg, run_cfg, download_delay, concurrency_per_domain)
    run_ctx = {
        "run_id": str(uuid.uuid4()),
        "config_hash": hash_config(config_stamp),
        "config": config_stamp,
    }
    domain_states: dict = {}
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        raw = await asyncio.gather(
            *[_scrape_one(crawler, url, run_cfg, domain_states,
                          download_delay, concurrency_per_domain, output_dir, run_ctx)
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
    parser.add_argument('--concurrency-per-domain', type=int, default=CONCURRENCY_PER_DOMAIN,
                        help=f'Per-domain in-flight request cap (default: {CONCURRENCY_PER_DOMAIN})')
    args = parser.parse_args()

    urls = [ln.strip() for ln in Path(args.url_file).read_text(encoding='utf-8').splitlines()
            if ln.strip()]
    asyncio.run(scrape_urls_workflow(
        urls, Path(args.output_dir), args.download_delay, args.concurrency_per_domain,
    ))
