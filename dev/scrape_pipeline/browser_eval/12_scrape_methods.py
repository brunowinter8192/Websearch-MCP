#!/usr/bin/env python3

# INFRASTRUCTURE
import asyncio
import hashlib
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from src.scraper.scrape_url import is_garbage_content, COOKIE_CONSENT_SELECTOR

REPORTS_DIR = Path(__file__).parent / "12_reports"
ENGINE_REPORTS_DIR = Path(__file__).parent / "../../search_pipeline/weights_eval/11_reports"
DELAY_BETWEEN_URLS = 2
MIN_CONTENT_THRESHOLD = 200

TABLE_ROW_RE = re.compile(r'^\|\s*\d+\s*\|\s*(https?://[^\s|]+)')

METHODS = [
    {"id": "1_networkidle",       "dir": "method_1_networkidle",       "wait_until": "networkidle",       "stealth": False},
    {"id": "2_domcontentloaded",  "dir": "method_2_domcontentloaded",  "wait_until": "domcontentloaded",  "stealth": False},
    {"id": "3_stealth",           "dir": "method_3_stealth",           "wait_until": "networkidle",       "stealth": True},
]


# ORCHESTRATOR
def run_scrape_methods():
    url_pool = collect_urls()
    if not url_pool:
        print("ERROR: No URLs found in 11_reports/engine_*.md — run 11_engine_isolation.py first.", file=sys.stderr)
        sys.exit(1)
    save_url_pool(url_pool)
    print(f"URL pool: {len(url_pool)} unique URLs", file=sys.stderr)
    results = asyncio.run(scrape_all_urls(url_pool))
    save_summary(results)


# FUNCTIONS

# Parse engine_*.md files to build deduplicated URL → engines mapping
def collect_urls() -> dict[str, list[str]]:
    if not ENGINE_REPORTS_DIR.exists():
        return {}
    url_engines: dict[str, list[str]] = {}
    for engine_file in sorted(ENGINE_REPORTS_DIR.glob("engine_*.md")):
        engine_name = engine_file.stem.removeprefix("engine_").replace("_", " ")
        for line in engine_file.read_text(encoding="utf-8").splitlines():
            m = TABLE_ROW_RE.match(line)
            if m:
                url = m.group(1).strip().rstrip("/")
                if url not in url_engines:
                    url_engines[url] = []
                if engine_name not in url_engines[url]:
                    url_engines[url].append(engine_name)
    return url_engines


# Write url_pool.txt: one URL per line with engine annotation comment
def save_url_pool(url_pool: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"{url}  # {', '.join(sorted(engines))}" for url, engines in sorted(url_pool.items())]
    (REPORTS_DIR / "url_pool.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {REPORTS_DIR / 'url_pool.txt'}")


# Scrape all URLs across all 3 methods and collect result records
async def scrape_all_urls(url_pool: dict) -> list[dict]:
    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48)
    )
    records = []
    urls = list(url_pool.keys())
    for i, url in enumerate(urls):
        print(f"[{i + 1}/{len(urls)}] {url}", file=sys.stderr)
        engines = url_pool[url]
        for method in METHODS:
            print(f"  [{method['id']}]", file=sys.stderr)
            scrape_data = await scrape_one_method(url, method, md_generator)
            save_scrape_result(url, method, scrape_data)
            records.append({
                "url": url,
                "engines": engines,
                "method": method["id"],
                "content_len": len(scrape_data["content"]),
                "time_seconds": scrape_data["time_seconds"],
                "garbage_type": scrape_data["garbage_type"],
                "status_code": scrape_data["status_code"],
                "error": scrape_data["error"],
            })
        if i < len(urls) - 1:
            await asyncio.sleep(DELAY_BETWEEN_URLS)
    return records


# Scrape one URL with one method config, return raw scrape data dict
async def scrape_one_method(url: str, method: dict, md_generator) -> dict:
    if method["stealth"]:
        browser_config = BrowserConfig(headless=True, verbose=False, enable_stealth=True)
        adapter = UndetectedAdapter()
        strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_config,
            browser_adapter=adapter,
        )
        crawler_kwargs = {"config": browser_config, "crawler_strategy": strategy}
    else:
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawler_kwargs = {"config": browser_config}

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=method["wait_until"],
        excluded_selector=COOKIE_CONSENT_SELECTOR,
        markdown_generator=md_generator,
    )
    start = time.time()
    try:
        async with AsyncWebCrawler(**crawler_kwargs) as crawler:
            result = await crawler.arun(url=url, config=run_config)
        elapsed = time.time() - start
        status_code = result.status_code if hasattr(result, "status_code") else None
        content = ""
        if result.markdown:
            content = result.markdown.fit_markdown or ""
            if len(content) < MIN_CONTENT_THRESHOLD and result.markdown.raw_markdown:
                content = result.markdown.raw_markdown
        garbage_type = is_garbage_content(content) if content else None
        return {
            "content": content,
            "status_code": status_code,
            "time_seconds": elapsed,
            "garbage_type": garbage_type,
            "error": None,
        }
    except Exception as e:
        return {
            "content": "",
            "status_code": None,
            "time_seconds": time.time() - start,
            "garbage_type": None,
            "error": str(e)[:200],
        }


# Write scraped content with metadata header to the method subdirectory
def save_scrape_result(url: str, method: dict, scrape_data: dict) -> None:
    method_dir = REPORTS_DIR / method["dir"]
    method_dir.mkdir(parents=True, exist_ok=True)
    if scrape_data["error"]:
        garbage_str = "exception"
    elif scrape_data["garbage_type"]:
        garbage_str = scrape_data["garbage_type"]
    else:
        garbage_str = "null"
    header = build_metadata_header({
        "url": url,
        "method": method["id"],
        "status_code": scrape_data["status_code"] if scrape_data["status_code"] is not None else "null",
        "chars": len(scrape_data["content"]),
        "time_seconds": round(scrape_data["time_seconds"], 2),
        "garbage_type": garbage_str,
    })
    full_content = header + "\n\n" + scrape_data["content"]
    filename = sanitize_filename(url) + ".md"
    (method_dir / filename).write_text(full_content, encoding="utf-8")


# Build HTML comment metadata block for scrape output files
def build_metadata_header(metadata: dict) -> str:
    return "\n".join([
        f"<!-- url: {metadata['url']} -->",
        f"<!-- method: {metadata['method']} -->",
        f"<!-- status_code: {metadata['status_code']} -->",
        f"<!-- chars: {metadata['chars']} -->",
        f"<!-- time_seconds: {metadata['time_seconds']} -->",
        f"<!-- garbage_type: {metadata['garbage_type']} -->",
    ])


# Build a safe filename: sanitized hostname + short MD5 hash of full URL
def sanitize_filename(url: str) -> str:
    from urllib.parse import urlparse
    try:
        hostname = urlparse(url).hostname or "unknown"
    except Exception:
        hostname = "unknown"
    safe_domain = re.sub(r"[^a-zA-Z0-9._-]", "_", hostname)[:40]
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{safe_domain}_{url_hash}"


# Write summary.md with per-method stats and cross-method disagreements
def save_summary(results: list[dict]) -> None:
    report = build_summary_report(results)
    (REPORTS_DIR / "summary.md").write_text(report, encoding="utf-8")
    print(f"Saved: {REPORTS_DIR / 'summary.md'}")


# Build summary report markdown from result records
def build_summary_report(results: list[dict]) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_urls = len({r["url"] for r in results})

    lines = [
        "# Scrape Methods Comparison",
        f"Date: {timestamp}",
        f"Total unique URLs: {total_urls}",
        f"Methods tested: {len(METHODS)}",
        "",
        "## Per-Method Stats",
        "",
        "| Method | Total | Success | Success Rate | Avg Time (s) | Avg Content (chars) |",
        "|--------|-------|---------|--------------|--------------|---------------------|",
    ]

    for method in METHODS:
        method_records = [r for r in results if r["method"] == method["id"]]
        total = len(method_records)
        success_records = [
            r for r in method_records
            if r["content_len"] > 0 and r["garbage_type"] is None and r["error"] is None
        ]
        success_count = len(success_records)
        success_rate = f"{success_count / total * 100:.0f}%" if total > 0 else "—"
        avg_time = f"{sum(r['time_seconds'] for r in method_records) / total:.1f}" if total > 0 else "—"
        avg_chars = f"{sum(r['content_len'] for r in success_records) / success_count:.0f}" if success_count > 0 else "—"
        lines.append(f"| {method['id']} | {total} | {success_count} | {success_rate} | {avg_time} | {avg_chars} |")

    lines += ["", "## Garbage Type Distribution", ""]
    for method in METHODS:
        method_records = [r for r in results if r["method"] == method["id"]]
        counts: dict[str, int] = {}
        for r in method_records:
            if r["error"]:
                key = "exception"
            elif r["garbage_type"]:
                key = r["garbage_type"]
            elif r["content_len"] == 0:
                key = "empty"
            else:
                key = "ok"
            counts[key] = counts.get(key, 0) + 1
        distribution = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        lines.append(f"**{method['id']}:** {distribution}")

    urls_by_url: dict[str, dict[str, str]] = {}
    for r in results:
        url = r["url"]
        if url not in urls_by_url:
            urls_by_url[url] = {}
        if r["error"]:
            outcome = "exception"
        elif r["garbage_type"]:
            outcome = r["garbage_type"]
        elif r["content_len"] == 0:
            outcome = "empty"
        else:
            outcome = "ok"
        urls_by_url[url][r["method"]] = outcome

    disagreements = [
        (url, outcomes)
        for url, outcomes in urls_by_url.items()
        if len(set(outcomes.values())) > 1
    ]

    method_ids = [m["id"] for m in METHODS]
    lines += [
        "",
        f"## Cross-Method Disagreements ({len(disagreements)} URLs)",
        "",
        "URLs where methods produced different outcomes (ok / garbage type / empty / exception).",
        "",
        "| URL | " + " | ".join(method_ids) + " |",
        "|-----|" + "------|" * len(METHODS),
    ]

    for url, outcomes in sorted(disagreements):
        row = [url[:80]] + [outcomes.get(mid, "—") for mid in method_ids]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


if __name__ == "__main__":
    run_scrape_methods()
