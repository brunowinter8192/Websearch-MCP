# INFRASTRUCTURE
import argparse
import asyncio
import time
import uuid
from pathlib import Path

from crawl4ai import AsyncWebCrawler

# From src/scraper/scrape_url.py: same config-hash algorithm used by the ad-hoc path's log
# (generic, not path-specific — reused rather than re-implemented)
from src.scraper.scrape_url import hash_config
# From src/crawler/pipe_scraper_constants.py: shared pacing constants
from src.crawler.pipe_scraper_constants import DOWNLOAD_DELAY, CONCURRENCY_PER_DOMAIN, CAMOUFOX_CONCURRENCY_PER_DOMAIN
# From src/crawler/pipe_scraper_config.py: chromium browser/run config construction + config stamp
from src.crawler.pipe_scraper_config import _build_configs, _extract_pipe_config_stamp
# From src/crawler/pipe_scraper_acquisition.py: per-URL engine executors (chromium + camoufox)
from src.crawler.pipe_scraper_acquisition import _scrape_one, _scrape_one_camoufox
# From src/crawler/pipe_scraper_report.py: /tmp outcome report + console summary
from src.crawler.pipe_scraper_report import _domain_from_urls, _write_tmp_report, _print_summary

# ORCHESTRATOR

# Scrape URL list with Scrapy-style per-domain pacing; engine/concurrency-per-domain defaults
# resolved per-run (see _scrape_all) — write per-URL md files + /tmp report + JSONL log.
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

# Scrape all URLs with per-domain pacing — dispatches to ONE of two engines per RUN (chromium
# default/unchanged, or camoufox), never per-URL, never auto-selected.
# concurrency_per_domain=None resolves to the engine's own default here (not in
# scrape_urls_workflow) so any direct caller of this function gets the same engine-aware default.
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
