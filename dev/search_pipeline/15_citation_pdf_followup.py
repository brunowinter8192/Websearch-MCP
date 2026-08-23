#!/usr/bin/env python3
"""Two-hop validation probe: re-GETs HTML_HAS_PDF_LINK URLs and follows their citation_pdf_url to classify actual PDF delivery."""

# INFRASTRUCTURE
import asyncio
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"
DATA_DIR = SCRIPT_DIR / "txt"

SOURCE_REPORT = "download_classify_20260507_172709.md"
SOURCE_POOL = "pool_20260507_172709.txt"

GLOBAL_MAX_CONNECTIONS = 8
GLOBAL_MAX_KEEPALIVE = 4
DOMAIN_CONCURRENCY_CAP = 2
DOMAIN_COURTESY_SLEEP = 0.5
HOP_TIMEOUT = 8.0
HTML_READ_BYTES = 32 * 1024

CITATION_PDF_META_RE = re.compile(
    r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']'
    r'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
    re.IGNORECASE,
)


# ORCHESTRATOR

async def run_probe() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    pool = _load_pool()
    _write_pool_file(pool, ts)
    print(f"[pool] {len(pool)} HTML_HAS_PDF_LINK URLs loaded", file=sys.stderr)

    t_start = time.monotonic()
    results = await _probe_all(pool)
    wall_secs = time.monotonic() - t_start

    report_path = _write_report(results, wall_secs, ts)
    print(f"\nReport: {report_path}", file=sys.stderr)


# FUNCTIONS

# Load HTML_HAS_PDF_LINK URLs from probe-14 report; resolve truncated entries via pool file
def _load_pool() -> list[str]:
    report_path = REPORT_DIR / SOURCE_REPORT
    pool_path = DATA_DIR / SOURCE_POOL

    report_text = report_path.read_text(encoding="utf-8")
    pool_urls = set(pool_path.read_text(encoding="utf-8").splitlines())
    pool_urls.discard("")

    urls: list[str] = []
    in_s6 = False
    for line in report_text.splitlines():
        if "## Section 6" in line:
            in_s6 = True
            continue
        if in_s6 and line.startswith("## Section"):
            break
        if not in_s6 or not line.startswith("| "):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7 or parts[5] != "HTML_HAS_PDF_LINK":
            continue
        url_part = parts[3]
        if url_part in pool_urls:
            urls.append(url_part)
        else:
            matches = [u for u in pool_urls if u.startswith(url_part)]
            if len(matches) == 1:
                urls.append(matches[0])
            else:
                print(f"[pool] WARNING: could not resolve {url_part!r} → skipped", file=sys.stderr)

    return urls


# Write pool file; log path to stderr
def _write_pool_file(pool: list[str], ts: str) -> None:
    path = DATA_DIR / f"pool_has_pdf_link_{ts}.txt"
    path.write_text("\n".join(pool) + "\n", encoding="utf-8")
    print(f"[pool] written: {path.name}", file=sys.stderr)


# Run two-hop classification for all URLs; return result list
async def _probe_all(pool: list[str]) -> list[dict]:
    limits = httpx.Limits(max_connections=GLOBAL_MAX_CONNECTIONS, max_keepalive_connections=GLOBAL_MAX_KEEPALIVE)
    domain_sems: dict[str, asyncio.Semaphore] = {}
    results: list[dict | None] = [None] * len(pool)

    async with httpx.AsyncClient(
        limits=limits,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; research-probe/1.0)"},
    ) as client:
        tasks = [
            _probe_with_cap(client, url, idx, domain_sems, results)
            for idx, url in enumerate(pool)
        ]
        done = 0
        total = len(tasks)
        for coro in asyncio.as_completed(tasks):
            await coro
            done += 1
            if done % 20 == 0 or done == total:
                print(f"[probe] {done}/{total}", file=sys.stderr)

    return [r for r in results if r is not None]


# Semaphore-gated probe; semaphore keyed on citation_pdf_url domain (resolved during Hop 1)
async def _probe_with_cap(
    client: httpx.AsyncClient,
    url: str,
    idx: int,
    domain_sems: dict[str, asyncio.Semaphore],
    results: list,
) -> None:
    # Hop 1: GET original URL, extract citation_pdf_url (no semaphore — original URLs are diverse)
    hop1 = await _hop1_extract(client, url)

    if hop1["citation_pdf_url"] is None:
        results[idx] = {
            "original_url": url,
            "original_domain": _base_domain(url),
            "citation_pdf_url": None,
            "pdf_host_domain": None,
            "hop2_outcome": "EXTRACTION_FAILED",
            "hop2_status": None,
            "hop2_content_type": None,
            "hop2_title": None,
            "hop2_body_preview": None,
            "hop1_outcome": hop1["outcome"],
        }
        return

    pdf_url = hop1["citation_pdf_url"]
    pdf_domain = urlparse(pdf_url).netloc

    # Hop 2: GET citation_pdf_url, semaphore keyed on PDF host domain
    if pdf_domain not in domain_sems:
        domain_sems[pdf_domain] = asyncio.Semaphore(DOMAIN_CONCURRENCY_CAP)
    async with domain_sems[pdf_domain]:
        hop2 = await _hop2_classify(client, pdf_url)
        await asyncio.sleep(DOMAIN_COURTESY_SLEEP)

    results[idx] = {
        "original_url": url,
        "original_domain": _base_domain(url),
        "citation_pdf_url": pdf_url,
        "pdf_host_domain": _base_domain(pdf_url),
        "hop2_outcome": hop2["outcome"],
        "hop2_status": hop2["status"],
        "hop2_content_type": hop2["content_type"],
        "hop2_title": hop2["title"],
        "hop2_body_preview": hop2["body_preview"],
        "hop1_outcome": hop1["outcome"],
    }


# Hop 1: GET original URL, extract citation_pdf_url; return dict with outcome + citation_pdf_url
async def _hop1_extract(client: httpx.AsyncClient, url: str) -> dict:
    rec = {"outcome": None, "citation_pdf_url": None}
    try:
        async with client.stream("GET", url, timeout=HOP_TIMEOUT) as resp:
            if resp.status_code >= 400:
                rec["outcome"] = f"HTTP_{resp.status_code}"
                return rec
            ct = resp.headers.get("content-type", "").lower()
            if "text/html" not in ct:
                rec["outcome"] = f"UNEXPECTED_CT:{ct[:40]}"
                return rec
            body = b""
            async for chunk in resp.aiter_bytes(chunk_size=4096):
                body += chunk
                if len(body) >= HTML_READ_BYTES:
                    break
            body_str = body.decode("utf-8", errors="replace")
            m = CITATION_PDF_META_RE.search(body_str)
            if m:
                rec["citation_pdf_url"] = m.group(1) or m.group(2)
                rec["outcome"] = "OK"
            else:
                rec["outcome"] = "NO_META_TAG"
    except httpx.TimeoutException:
        rec["outcome"] = "TIMEOUT"
    except httpx.RequestError as e:
        rec["outcome"] = f"CONN_ERROR:{type(e).__name__}"
    except Exception as e:
        rec["outcome"] = f"ERROR:{type(e).__name__}"
    return rec


# Hop 2: GET citation_pdf_url, classify response; return dict with outcome + details
async def _hop2_classify(client: httpx.AsyncClient, pdf_url: str) -> dict:
    rec = {"outcome": None, "status": None, "content_type": None, "title": None, "body_preview": None}
    try:
        async with client.stream("GET", pdf_url, timeout=HOP_TIMEOUT) as resp:
            rec["status"] = resp.status_code
            ct = resp.headers.get("content-type", "").lower()
            rec["content_type"] = ct

            if resp.status_code >= 400:
                rec["outcome"] = f"HTTP_{resp.status_code}"
                return rec

            body = b""
            async for chunk in resp.aiter_bytes(chunk_size=4096):
                body += chunk
                if len(body) >= HTML_READ_BYTES:
                    break

            if "application/pdf" in ct or body[:4] == b"%PDF":
                rec["outcome"] = "PDF_OK"
                return rec

            if "text/html" in ct:
                body_str = body.decode("utf-8", errors="replace")
                title_m = re.search(r"<title[^>]*>([^<]{1,300})</title>", body_str, re.IGNORECASE | re.DOTALL)
                if title_m:
                    rec["title"] = title_m.group(1).strip()[:200]
                # First 200 chars of visible text (strip tags)
                visible = re.sub(r"<[^>]+>", " ", body_str[:2000])
                visible = re.sub(r"\s+", " ", visible).strip()
                rec["body_preview"] = visible[:200]
                rec["outcome"] = "HTML_FALLBACK"
                return rec

            rec["outcome"] = "HTML_FALLBACK"
    except httpx.TimeoutException:
        rec["outcome"] = "TIMEOUT"
    except httpx.RequestError as e:
        rec["outcome"] = f"CONN_ERROR:{type(e).__name__}"
    except Exception as e:
        rec["outcome"] = f"ERROR:{type(e).__name__}"
    return rec


# Extract bare domain (strip www.) from URL
def _base_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""


# Write markdown report; return path
def _write_report(results: list[dict], wall_secs: float, ts: str) -> Path:
    path = REPORT_DIR / f"citation_pdf_followup_{ts}.md"
    path.write_text("\n".join(_build_report(results, wall_secs, ts)), encoding="utf-8")
    return path


# Assemble all report sections
def _build_report(results: list[dict], wall_secs: float, ts: str) -> list[str]:
    lines: list[str] = [f"# Citation PDF Followup Probe — {ts}", ""]
    lines += _section_metadata(results, wall_secs, ts)
    lines += _section_source_domain_table(results)
    lines += _section_pdf_host_table(results)
    lines += _section_pdf_ok_sample(results)
    lines += _section_html_fallback_sample(results)
    lines += _section_per_url_detail(results)
    return lines


# Section 1 — Run Metadata
def _section_metadata(results: list[dict], wall_secs: float, ts: str) -> list[str]:
    minutes, seconds = divmod(int(wall_secs), 60)
    outcome_counts: dict[str, int] = defaultdict(int)
    for r in results:
        outcome_counts[r["hop2_outcome"]] += 1
    http4xx = sum(v for k, v in outcome_counts.items() if k.startswith("HTTP_4"))
    http5xx = sum(v for k, v in outcome_counts.items() if k.startswith("HTTP_5"))
    downloadable = outcome_counts.get("PDF_OK", 0)
    pct = f"{100 * downloadable / len(results):.1f}%" if results else "0%"

    return [
        "## Section 1 — Run Metadata",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Timestamp | {ts} |",
        f"| Source report | {SOURCE_REPORT} |",
        f"| Input URLs (HTML_HAS_PDF_LINK) | {len(results)} |",
        f"| Concurrency | global_max={GLOBAL_MAX_CONNECTIONS}, per_pdf_host_cap={DOMAIN_CONCURRENCY_CAP} |",
        f"| Timeout | {HOP_TIMEOUT}s per hop |",
        f"| Courtesy sleep | {DOMAIN_COURTESY_SLEEP}s per pdf-host domain slot |",
        f"| Wall clock | {minutes}m {seconds}s |",
        f"| PDF_OK | {outcome_counts.get('PDF_OK', 0)} ({pct} of input) |",
        f"| HTML_FALLBACK | {outcome_counts.get('HTML_FALLBACK', 0)} |",
        f"| HTTP_4xx | {http4xx} |",
        f"| HTTP_5xx | {http5xx} |",
        f"| TIMEOUT | {outcome_counts.get('TIMEOUT', 0)} |",
        f"| EXTRACTION_FAILED | {outcome_counts.get('EXTRACTION_FAILED', 0)} |",
        "",
    ]


# Section 2 — Per-Source-Domain Table (where the ORIGINAL URL lives)
def _section_source_domain_table(results: list[dict]) -> list[str]:
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_domain[r["original_domain"]].append(r)

    lines = [
        "## Section 2 — Per-Source-Domain Table (original URL domain)",
        "",
        "| Source Domain | Total | PDF_OK | HTML_FALLBACK | HTTP_4xx | HTTP_5xx | TIMEOUT | EXTRACTION_FAILED | Downloadable % |",
        "|---------------|------:|-------:|-------------:|---------:|---------:|--------:|------------------:|---------------:|",
    ]
    for d in sorted(by_domain, key=lambda x: -len(by_domain[x])):
        recs = by_domain[d]
        c: dict[str, int] = defaultdict(int)
        for r in recs:
            c[r["hop2_outcome"]] += 1
        total = len(recs)
        pdf_ok = c.get("PDF_OK", 0)
        html_fb = c.get("HTML_FALLBACK", 0)
        http4xx = sum(v for k, v in c.items() if k.startswith("HTTP_4"))
        http5xx = sum(v for k, v in c.items() if k.startswith("HTTP_5"))
        timeout = c.get("TIMEOUT", 0)
        extr_fail = c.get("EXTRACTION_FAILED", 0)
        pct = f"{100 * pdf_ok / total:.0f}%"
        lines.append(
            f"| {d} | {total} | {pdf_ok} | {html_fb} | {http4xx} | {http5xx} | {timeout} | {extr_fail} | {pct} |"
        )
    lines.append("")
    return lines


# Section 3 — Per-PDF-Host-Domain Table (where citation_pdf_url points)
def _section_pdf_host_table(results: list[dict]) -> list[str]:
    by_host: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        host = r["pdf_host_domain"] or "(no citation_pdf_url)"
        by_host[host].append(r)

    lines = [
        "## Section 3 — Per-PDF-Host-Domain Table (citation_pdf_url domain)",
        "",
        "| PDF Host | Total | PDF_OK | HTML_FALLBACK | HTTP_4xx | HTTP_5xx | TIMEOUT | Downloadable % |",
        "|----------|------:|-------:|-------------:|---------:|---------:|--------:|---------------:|",
    ]
    for h in sorted(by_host, key=lambda x: -len(by_host[x])):
        recs = by_host[h]
        c: dict[str, int] = defaultdict(int)
        for r in recs:
            c[r["hop2_outcome"]] += 1
        total = len(recs)
        pdf_ok = c.get("PDF_OK", 0)
        html_fb = c.get("HTML_FALLBACK", 0)
        http4xx = sum(v for k, v in c.items() if k.startswith("HTTP_4"))
        http5xx = sum(v for k, v in c.items() if k.startswith("HTTP_5"))
        timeout = c.get("TIMEOUT", 0)
        pct = f"{100 * pdf_ok / total:.0f}%" if total else "—"
        lines.append(
            f"| {h} | {total} | {pdf_ok} | {html_fb} | {http4xx} | {http5xx} | {timeout} | {pct} |"
        )
    lines.append("")
    return lines


# Section 4 — PDF_OK Sample (first 20)
def _section_pdf_ok_sample(results: list[dict]) -> list[str]:
    ok = [r for r in results if r["hop2_outcome"] == "PDF_OK"]
    lines = [
        "## Section 4 — PDF_OK Sample",
        "",
        f"Total PDF_OK: **{len(ok)}**",
        "",
        "| Original URL | citation_pdf_url | Outcome |",
        "|-------------|-----------------|---------|",
    ]
    for r in ok[:20]:
        orig = r["original_url"][:80].replace("|", "%7C")
        pdf = (r["citation_pdf_url"] or "")[:80].replace("|", "%7C")
        lines.append(f"| {orig} | {pdf} | PDF_OK |")
    lines.append("")
    return lines


# Section 5 — HTML_FALLBACK Sample (first 20) with title + body preview
def _section_html_fallback_sample(results: list[dict]) -> list[str]:
    fb = [r for r in results if r["hop2_outcome"] == "HTML_FALLBACK"]
    lines = [
        "## Section 5 — HTML_FALLBACK Sample",
        "",
        f"Total HTML_FALLBACK: **{len(fb)}**",
        "",
        "| Original URL | citation_pdf_url | Title / Body Preview |",
        "|-------------|-----------------|---------------------|",
    ]
    for r in fb[:20]:
        orig = r["original_url"][:70].replace("|", "%7C")
        pdf = (r["citation_pdf_url"] or "")[:60].replace("|", "%7C")
        preview = (r["hop2_title"] or r["hop2_body_preview"] or "")[:80].replace("|", " ")
        lines.append(f"| {orig} | {pdf} | {preview} |")
    lines.append("")
    return lines


# Section 6 — Per-URL Detail Table (all 124)
def _section_per_url_detail(results: list[dict]) -> list[str]:
    sorted_results = sorted(results, key=lambda r: (r["original_domain"], r["original_url"]))

    lines = [
        "## Section 6 — Per-URL Detail",
        "",
        "| Source Domain | Original URL | PDF Host | citation_pdf_url | Hop2 Outcome | Hop2 Status | Notes |",
        "|--------------|-------------|----------|-----------------|:------------:|:-----------:|-------|",
    ]
    for r in sorted_results:
        src = r["original_domain"]
        orig = r["original_url"][:70].replace("|", "%7C")
        host = r["pdf_host_domain"] or "—"
        pdf = (r["citation_pdf_url"] or "—")[:60].replace("|", "%7C")
        outcome = r["hop2_outcome"] or "?"
        status = str(r["hop2_status"]) if r["hop2_status"] else "—"
        notes = ""
        if r["hop2_title"]:
            notes = r["hop2_title"][:60].replace("|", " ")
        elif r["hop1_outcome"] and r["hop1_outcome"] != "OK":
            notes = f"hop1={r['hop1_outcome']}"
        lines.append(f"| {src} | {orig} | {host} | {pdf} | {outcome} | {status} | {notes} |")
    lines.append("")
    return lines


if __name__ == "__main__":
    asyncio.run(run_probe())
