# INFRASTRUCTURE
from pathlib import Path
from urllib.parse import urlparse

# FUNCTIONS

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
