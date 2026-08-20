# INFRASTRUCTURE
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# From src/crawler/pipe_scraper_constants.py: shared pacing/timeout/threshold values
from src.crawler.pipe_scraper_constants import PAGE_TIMEOUT_MS, DELAY_BEFORE_RETURN_HTML, EMPTY_THRESHOLD_BYTES
# From src/crawler/pipe_scraper_acquisition.py: crawl4ai's own fallback_fetch_function wiring target
from src.crawler.pipe_scraper_acquisition import _fallback_fetch

# FUNCTIONS

# Construct the browser/run config actually used for a scrape run — factored out (not inlined in
# _scrape_all) so a test can exercise the SAME real objects crawl4ai wires against. Fixed anti-bot
# posture only, optimized for reachability not extraction quality — full sourced rationale for
# every value in src/crawler/DOCS.md.
def _build_configs() -> tuple[BrowserConfig, CrawlerRunConfig]:
    browser_cfg = BrowserConfig(
        headless=True,
        verbose=False,
        enable_stealth=True,
    )
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded",
        delay_before_return_html=DELAY_BEFORE_RETURN_HTML,
        page_timeout=PAGE_TIMEOUT_MS,
        markdown_generator=DefaultMarkdownGenerator(),
        simulate_user=True,
        override_navigator=True,
        magic=False,
        remove_consent_popups=True,
        fallback_fetch_function=_fallback_fetch,
        verbose=False,
    )
    return browser_cfg, run_cfg

# Read the pacing/browser config actually in effect off the real constructed objects + pacing
# values passed in — never re-declare values here, so the stamp can't drift from what actually ran.
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
        # except-block rescue (path b) is unconditional code, not a config object attribute, so it
        # has no stamp field; see pipe_scrape_logger.py's schema comment.
        "fallback_armed": run_cfg.fallback_fetch_function is not None,
        "download_delay_s": download_delay,
        "concurrency_per_domain": concurrency_per_domain,
        "empty_threshold_bytes": EMPTY_THRESHOLD_BYTES,
    }
