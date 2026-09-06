# INFRASTRUCTURE
from pathlib import Path
from urllib.parse import urlparse

# From src/crawler/pipe_scraper_acquisition.py: the same URL-identity collapse
# _extract_onward_links already applied to every discovered link, reused here so an input URL
# collapses to the identical comparison key
from src.crawler.pipe_scraper_acquisition import _onward_link_identity

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

# Merge every scraped page's own onward links (already host-restricted, identity-normalized, and
# per-page-deduped by pipe_scraper_acquisition._extract_onward_links) into one run-wide, order-
# preserving deduped list, excluding anything that normalizes to a URL already in the run's own
# input list — a link back to a page the caller already scraped this round carries no new
# information for the "is a further round worth it" decision this file exists to support. Returns
# None, not an empty list, when the engine never collects links at all (camoufox — try_scrape_
# camoufox returns content + metadata, no link set) so a caller can tell "found nothing new" apart
# from "this engine cannot look" — see pipe_scraper_acquisition.py's own Gotchas.
def _collect_onward_links(urls: list[str], results: list[dict], engine: str) -> list[str] | None:
    if engine == "camoufox":
        return None
    already_known = {_onward_link_identity(u) for u in urls}
    already_known.discard(None)
    seen = set(already_known)
    onward = []
    for r in results:
        for link in r.get('links', []):
            if link in seen:
                continue
            seen.add(link)
            onward.append(link)
    return onward

# Write the run's onward links (see _collect_onward_links) to /tmp/<domain>_scrape_links.txt,
# following the same /tmp/<domain>_scrape_report.md naming the per-URL report already uses. Writes
# nothing at all when onward_links is None (camoufox) — no file to point at is the honest signal,
# never an empty one indistinguishable from "chromium looked and found zero".
def _write_onward_links_file(domain: str, onward_links: list[str] | None) -> None:
    if onward_links is None:
        return
    path = Path(f"/tmp/{domain}_scrape_links.txt")
    path.write_text(("\n".join(onward_links) + "\n") if onward_links else "", encoding='utf-8')

# Print one-line console summary: a raw HTTP-status histogram (including a "no_status" bucket for
# a URL our own code never got a status for at all), a zero-byte count, and the onward-link count
# (or an explicit "not collected" note on the camoufox engine, never a bare 0 that would look
# identical to "chromium looked and found none") — all counted straight off already-recorded
# facts, nothing inferred about what a status/byte-count combination means.
def _print_summary(results: list[dict], wall_s: float, onward_links: list[str] | None) -> None:
    total = len(results)
    status_counts: dict = {}
    for r in results:
        key = r['status_code'] if r['status_code'] is not None else 'no_status'
        status_counts[key] = status_counts.get(key, 0) + 1
    status_str = ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items(), key=lambda kv: str(kv[0])))
    zero_bytes = sum(1 for r in results if r['bytes'] == 0)
    links_str = ("onward links not collected (camoufox engine)" if onward_links is None
                 else f"{len(onward_links)} onward links collected")
    print(f"Scraped {total} URLs in {wall_s:.0f}s — status: {status_str} — "
          f"{zero_bytes} returned 0 bytes — {links_str}")
