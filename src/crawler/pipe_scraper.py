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
        "simulate_user": run_cfg.simulate_user,
        "override_navigator": run_cfg.override_navigator,
        "magic": run_cfg.magic,
        "remove_consent_popups": run_cfg.remove_consent_popups,
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
        verbose=False,
    )
    return browser_cfg, run_cfg

# Scrape all URLs under a single crawler with per-domain Scrapy-style pacing.
async def _scrape_all(
    urls: list[str],
    output_dir: Path,
    download_delay: float,
    concurrency_per_domain: int,
) -> list[dict]:
    browser_cfg, run_cfg = _build_configs()
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
