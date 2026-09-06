# INFRASTRUCTURE
from pathlib import Path
from urllib.parse import urlparse

# FUNCTIONS

# Extract domain string from first URL (used for /tmp report filename)
def _domain_from_urls(urls: list[str]) -> str:
    if not urls:
        return 'unknown'
    return urlparse(urls[0]).netloc.replace('.', '_')

# Write per-URL report to /tmp/<domain>_scrape_report.md — status/bytes/wall_ms/url are the raw
# observed facts; no ok/error verdict is computed or printed anywhere in this module.
def _write_tmp_report(domain: str, results: list[dict]) -> None:
    path = Path(f"/tmp/{domain}_scrape_report.md")
    lines = [
        f"# Scrape Report — {domain}",
        "",
        f"Total: {len(results)} URLs",
        "",
        "| status | bytes | wall_ms | url |",
        "|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r.get('status_code') or '-'} | {r['bytes']} | {r['wall_ms']} | {r['url']} |"
        )
    path.write_text('\n'.join(lines), encoding='utf-8')

# Print one-line console summary: a raw HTTP-status histogram (including a "no_status" bucket for
# a URL our own code never got a status for at all) plus a zero-byte count — both counted straight
# off already-recorded facts, nothing inferred about what a status/byte-count combination means.
def _print_summary(results: list[dict], wall_s: float) -> None:
    total = len(results)
    status_counts: dict = {}
    for r in results:
        key = r['status_code'] if r['status_code'] is not None else 'no_status'
        status_counts[key] = status_counts.get(key, 0) + 1
    status_str = ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items(), key=lambda kv: str(kv[0])))
    zero_bytes = sum(1 for r in results if r['bytes'] == 0)
    print(f"Scraped {total} URLs in {wall_s:.0f}s — status: {status_str} — {zero_bytes} returned 0 bytes")
