#!/usr/bin/env python3
"""Download-classify probe — sniff-classifies academic URLs from the search pool without saving any content."""

# INFRASTRUCTURE
import asyncio
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import httpx

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"
DATA_DIR = SCRIPT_DIR / "txt"

RANDOM_SEED = 42
DOI_SAMPLE_SIZE = 300
GLOBAL_MAX_CONNECTIONS = 8
GLOBAL_MAX_KEEPALIVE = 4
DOMAIN_CONCURRENCY_CAP = 2
DOMAIN_COURTESY_SLEEP = 0.5
TIER1_TIMEOUT = 15.0
DEFAULT_TIMEOUT = 8.0
HTML_READ_BYTES = 32 * 1024
PDF_SNIFF_BYTES = 1024

TIER1_DOMAINS = frozenset({"arxiv.org", "aclanthology.org", "openreview.net", "pmc.ncbi.nlm.nih.gov"})
TIER2_DOMAINS = frozenset({"openalex.org", "semanticscholar.org"})
TIER3_DOMAINS = frozenset({"doi.org"})
TIER4_DOMAINS = frozenset({
    "dl.acm.org", "link.springer.com", "ieeexplore.ieee.org", "jstor.org",
    "books.google.com", "sciencedirect.com", "muse.jhu.edu", "mdpi.com",
    "onlinelibrary.wiley.com", "nature.com", "springer.com", "tandfonline.com",
    "researchgate.net", "direct.mit.edu", "biorxiv.org", "medrxiv.org",
    "ssrn.com", "cambridge.org", "oup.com", "acm.org", "worldscientific.com",
    "frontiersin.org", "plos.org", "hindawi.com", "thieme-connect.com",
    "search.proquest.com", "scribd.com", "spiedigitallibrary.org",
    "elib.uni-stuttgart.de", "cyberleninka.ru", "inspirehep.net",
    "search.ebscohost.com",
})

PAYWALL_MARKERS = [
    "institutional login",
    "institutional access",
    "purchase article",
    "buy this article",
    "purchase access",
    "sign in to read",
    "log in to access",
    "access options",
    "get full access",
    "full text is not available",
    "subscribe to read",
    "register to read",
    "article access required",
]

SMOKE_REPORTS_GLOB = "pipeline_smoke_*.md"
FREE_WORD_REPORTS_GLOB = "free_word_injection_probe_*.md"


# ORCHESTRATOR

async def run_probe() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Pool extraction
    smoke_path = _latest_report(SMOKE_REPORTS_GLOB)
    free_path = _latest_report(FREE_WORD_REPORTS_GLOB)
    print(f"[pool] smoke={smoke_path.name}", file=sys.stderr)
    print(f"[pool] free_word={free_path.name}", file=sys.stderr)

    all_urls = _extract_pool(smoke_path, free_path)
    tier_pool = _filter_and_tier(all_urls)
    sampled_pool, doi_sample = _apply_doi_sampling(tier_pool)
    _write_pool_files(sampled_pool, doi_sample, ts)

    total = len(sampled_pool)
    print(f"[pool] {total} URLs to classify (doi sample={len(doi_sample)}/all={sum(1 for u,t in tier_pool if t=='T3')})", file=sys.stderr)

    # Classification
    t_wall_start = time.monotonic()
    results = await _classify_all(sampled_pool)
    wall_secs = time.monotonic() - t_wall_start

    report_path = _write_report(results, sampled_pool, doi_sample, wall_secs, smoke_path, free_path, ts)
    print(f"\nReport: {report_path}", file=sys.stderr)


# FUNCTIONS

# Return path of most-recently-modified report matching glob
def _latest_report(glob_pattern: str) -> Path:
    candidates = sorted(REPORT_DIR.glob(glob_pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No report matching {glob_pattern} in {REPORT_DIR}")
    return candidates[0]


# Extract deduplicated URLs with real paths from both source reports
def _extract_pool(smoke_path: Path, free_path: Path) -> set[str]:
    smoke_text = smoke_path.read_text(encoding="utf-8")
    free_text = free_path.read_text(encoding="utf-8")

    urls: set[str] = set()

    for line in smoke_text.splitlines():
        m = re.match(r"\s*URL:\s+(https?://\S+)", line)
        if m:
            urls.add(m.group(1).rstrip(".,)"))

    for m in re.finditer(r"\| \d+ \| \S+ \| \d+ \| (https?://\S+?) \|", free_text):
        urls.add(m.group(1))

    # Drop root-domain-only URLs (path empty or '/')
    return {u for u in urls if _has_real_path(u)}


# Return True if URL has a non-trivial path component
def _has_real_path(url: str) -> bool:
    try:
        path = urlparse(url).path
        return bool(path) and path != "/"
    except Exception:
        return False


# Map URL to tier string or None
def _url_tier(url: str) -> str | None:
    d = _base_domain(url)
    if d in TIER1_DOMAINS or any(d.endswith("." + t) for t in TIER1_DOMAINS):
        return "T1"
    if d in TIER2_DOMAINS or any(d.endswith("." + t) for t in TIER2_DOMAINS):
        return "T2"
    if d in TIER3_DOMAINS or any(d.endswith("." + t) for t in TIER3_DOMAINS):
        return "T3"
    if d in TIER4_DOMAINS or any(d.endswith("." + t) for t in TIER4_DOMAINS):
        return "T4"
    return None


# Extract registrable base domain (strip www.)
def _base_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""


# Filter pool to academic URLs; return list of (url, tier) sorted by domain then url
def _filter_and_tier(all_urls: set[str]) -> list[tuple[str, str]]:
    tiered = [(u, t) for u in all_urls if (t := _url_tier(u)) is not None]
    tiered.sort(key=lambda x: (_base_domain(x[0]), x[0]))
    return tiered


# Apply doi.org sampling (seed=42, 300 URLs); return (full_sampled_pool, doi_sample_list)
def _apply_doi_sampling(tier_pool: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], list[str]]:
    doi_urls = [u for u, t in tier_pool if t == "T3"]
    non_doi = [(u, t) for u, t in tier_pool if t != "T3"]

    rng = random.Random(RANDOM_SEED)
    doi_sample = sorted(rng.sample(doi_urls, min(DOI_SAMPLE_SIZE, len(doi_urls))))
    sampled = non_doi + [(u, "T3") for u in doi_sample]
    sampled.sort(key=lambda x: (_base_domain(x[0]), x[0]))
    return sampled, doi_sample


# Write pool.txt and doi_sample.txt; log paths to stderr
def _write_pool_files(sampled_pool: list[tuple[str, str]], doi_sample: list[str], ts: str) -> None:
    pool_path = DATA_DIR / f"pool_{ts}.txt"
    pool_path.write_text("\n".join(u for u, _ in sampled_pool) + "\n", encoding="utf-8")
    print(f"[pool] written: {pool_path.name}", file=sys.stderr)

    doi_path = DATA_DIR / f"pool_doi_sample_{ts}.txt"
    doi_path.write_text("\n".join(doi_sample) + "\n", encoding="utf-8")
    print(f"[pool] written: {doi_path.name}", file=sys.stderr)


# Classify all URLs with httpx; return list of result dicts ordered as sampled_pool
async def _classify_all(sampled_pool: list[tuple[str, str]]) -> list[dict]:
    limits = httpx.Limits(max_connections=GLOBAL_MAX_CONNECTIONS, max_keepalive_connections=GLOBAL_MAX_KEEPALIVE)
    domain_sems: dict[str, asyncio.Semaphore] = {}
    results: list[dict | None] = [None] * len(sampled_pool)

    async with httpx.AsyncClient(
        limits=limits,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; research-probe/1.0)"},
    ) as client:
        tasks = [
            _classify_with_cap(client, url, tier, idx, domain_sems, results)
            for idx, (url, tier) in enumerate(sampled_pool)
        ]
        done = 0
        total = len(tasks)
        for coro in asyncio.as_completed(tasks):
            await coro
            done += 1
            if done % 50 == 0 or done == total:
                print(f"[classify] {done}/{total}", file=sys.stderr)

    return [r for r in results if r is not None]


# Semaphore-wrapped classify; writes result into results list at idx
async def _classify_with_cap(
    client: httpx.AsyncClient,
    url: str,
    tier: str,
    idx: int,
    domain_sems: dict[str, asyncio.Semaphore],
    results: list,
) -> None:
    netloc = urlparse(url).netloc
    if netloc not in domain_sems:
        domain_sems[netloc] = asyncio.Semaphore(DOMAIN_CONCURRENCY_CAP)
    async with domain_sems[netloc]:
        result = await _classify_url(client, url, tier)
        await asyncio.sleep(DOMAIN_COURTESY_SLEEP)
    results[idx] = result


# Core classification: apply transform, GET, sniff content-type + body
async def _classify_url(client: httpx.AsyncClient, original_url: str, tier: str) -> dict:
    transformed_url = _apply_transform(original_url)
    fetch_url = transformed_url or original_url
    timeout = TIER1_TIMEOUT if tier == "T1" else DEFAULT_TIMEOUT

    rec: dict = {
        "original_url": original_url,
        "transformed_url": transformed_url,
        "tier": tier,
        "final_url": None,
        "outcome": None,
        "status_code": None,
        "content_type": None,
        "page_title": None,
        "has_citation_pdf_url": False,
        "paywall_marker": None,
        "citation_pdf_url": None,
    }

    try:
        async with client.stream("GET", fetch_url, timeout=timeout) as resp:
            rec["status_code"] = resp.status_code
            rec["final_url"] = str(resp.url)
            ct = resp.headers.get("content-type", "").lower()
            rec["content_type"] = ct

            if resp.status_code >= 400:
                rec["outcome"] = f"HTTP_{resp.status_code}"
                return rec

            # Single-pass read: accumulate up to HTML_READ_BYTES; check PDF magic on first bytes
            body_chunks: list[bytes] = []
            bytes_read = 0
            async for chunk in resp.aiter_bytes(chunk_size=4096):
                body_chunks.append(chunk)
                bytes_read += len(chunk)
                if bytes_read >= HTML_READ_BYTES:
                    break
            body = b"".join(body_chunks)

            if "application/pdf" in ct or body[:4] == b"%PDF":
                rec["outcome"] = "PDF_OK"
                return rec

            if "text/html" in ct:
                try:
                    body_str = body.decode("utf-8", errors="replace")
                except Exception:
                    body_str = ""

                rec["page_title"] = _extract_title(body_str)

                # citation_pdf_url check
                m = re.search(
                    r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
                    body_str, re.IGNORECASE,
                )
                if not m:
                    m = re.search(
                        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
                        body_str, re.IGNORECASE,
                    )
                if m:
                    rec["has_citation_pdf_url"] = True
                    rec["citation_pdf_url"] = m.group(1)[:200]

                # Paywall marker check
                body_lower = body_str.lower()
                for marker in PAYWALL_MARKERS:
                    if marker in body_lower:
                        rec["paywall_marker"] = marker
                        break

                if rec["has_citation_pdf_url"]:
                    rec["outcome"] = "HTML_HAS_PDF_LINK"
                elif rec["paywall_marker"]:
                    rec["outcome"] = "HTML_PAYWALL"
                else:
                    rec["outcome"] = "HTML_OK"
                return rec

            # Non-PDF, non-HTML 200
            rec["outcome"] = "HTML_OK"
            return rec

    except httpx.TimeoutException:
        rec["outcome"] = "TIMEOUT"
    except httpx.ConnectError as e:
        rec["outcome"] = "CONNECTION_ERROR"
        rec["page_title"] = str(e)[:80]
    except httpx.RequestError as e:
        rec["outcome"] = "CONNECTION_ERROR"
        rec["page_title"] = str(e)[:80]
    except Exception as e:
        rec["outcome"] = "CONNECTION_ERROR"
        rec["page_title"] = f"{type(e).__name__}: {str(e)[:60]}"

    return rec


# Apply Tier-1 URL transform; return transformed URL or None if no transform applies
def _apply_transform(url: str) -> str | None:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    # arxiv.org: /abs/<id> or /html/<id> → /pdf/<id>
    if domain == "arxiv.org":
        path = parsed.path
        if re.match(r"^/(abs|html)/", path):
            new_path = re.sub(r"^/(abs|html)/", "/pdf/", path)
            return urlunparse(parsed._replace(path=new_path))
        return None  # /pdf/ path — no transform needed, GET as-is

    # aclanthology.org: strip trailing slash → append .pdf (skip if already .pdf)
    if domain == "aclanthology.org":
        path = parsed.path
        if path.lower().endswith(".pdf"):
            return None
        new_path = path.rstrip("/") + ".pdf"
        return urlunparse(parsed._replace(path=new_path))

    # openreview.net: /forum?id=X → /pdf?id=X
    if domain == "openreview.net":
        if parsed.path == "/forum":
            return urlunparse(parsed._replace(path="/pdf"))
        return None

    return None


# Extract first <title>...</title> from HTML body; return None if not found
def _extract_title(body: str) -> str | None:
    m = re.search(r"<title[^>]*>([^<]{1,300})</title>", body, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()[:200]
    return None


# Write the markdown report; return path
def _write_report(
    results: list[dict],
    sampled_pool: list[tuple[str, str]],
    doi_sample: list[str],
    wall_secs: float,
    smoke_path: Path,
    free_path: Path,
    ts: str,
) -> Path:
    path = REPORT_DIR / f"download_classify_{ts}.md"
    lines = _build_report(results, sampled_pool, doi_sample, wall_secs, smoke_path, free_path, ts)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# Assemble all report sections; return list of lines
def _build_report(
    results: list[dict],
    sampled_pool: list[tuple[str, str]],
    doi_sample: list[str],
    wall_secs: float,
    smoke_path: Path,
    free_path: Path,
    ts: str,
) -> list[str]:
    lines: list[str] = [f"# Download-Classify Probe — {ts}", ""]

    lines += _section_metadata(results, sampled_pool, doi_sample, wall_secs, smoke_path, free_path, ts)
    lines += _section_domain_aggregate(results)
    lines += _section_tier1_transforms(results)
    lines += _section_html_pdf_link_sample(results)
    lines += _section_paywall_sample(results)
    lines += _section_per_url_detail(results)

    return lines


# Section 1 — Run Metadata
def _section_metadata(
    results: list[dict],
    sampled_pool: list[tuple[str, str]],
    doi_sample: list[str],
    wall_secs: float,
    smoke_path: Path,
    free_path: Path,
    ts: str,
) -> list[str]:
    total_doi_in_pool = sum(1 for _, t in sampled_pool if t == "T3")
    tier_counts = {t: sum(1 for _, tier in sampled_pool if tier == t) for t in ("T1", "T2", "T3", "T4")}

    outcome_counts: dict[str, int] = defaultdict(int)
    for r in results:
        outcome_counts[r["outcome"]] += 1

    minutes, seconds = divmod(int(wall_secs), 60)

    return [
        "## Section 1 — Run Metadata",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Timestamp | {ts} |",
        f"| Source smoke | {smoke_path.name} |",
        f"| Source free-word | {free_path.name} |",
        f"| Total unique URLs in combined pool (with path) | {len(sampled_pool)} |",
        f"| Tier breakdown | T1={tier_counts.get('T1',0)} T2={tier_counts.get('T2',0)} T3={tier_counts.get('T3',0)} (sampled) T4={tier_counts.get('T4',0)} |",
        f"| doi.org: total in pool | (not probed: full pool has ~2013) |",
        f"| doi.org: sampled | {len(doi_sample)} (seed={RANDOM_SEED}) |",
        f"| doi_sample file | pool_doi_sample_{ts}.txt |",
        f"| Concurrency | global_max={GLOBAL_MAX_CONNECTIONS}, keepalive={GLOBAL_MAX_KEEPALIVE}, per_domain_cap={DOMAIN_CONCURRENCY_CAP} |",
        f"| Timeout | Tier-1={TIER1_TIMEOUT}s, all others={DEFAULT_TIMEOUT}s |",
        f"| Courtesy sleep | {DOMAIN_COURTESY_SLEEP}s per domain slot after request |",
        f"| Wall clock | {minutes}m {seconds}s |",
        f"| Outcomes | PDF_OK={outcome_counts.get('PDF_OK',0)} HTML_HAS_PDF_LINK={outcome_counts.get('HTML_HAS_PDF_LINK',0)} HTML_PAYWALL={outcome_counts.get('HTML_PAYWALL',0)} HTML_OK={outcome_counts.get('HTML_OK',0)} TIMEOUT={outcome_counts.get('TIMEOUT',0)} CONN_ERROR={outcome_counts.get('CONNECTION_ERROR',0)} HTTP_4xx/5xx={sum(v for k,v in outcome_counts.items() if k.startswith('HTTP_'))} |",
        "",
    ]


# Section 2 — Per-Domain Aggregate Table
def _section_domain_aggregate(results: list[dict]) -> list[str]:
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        d = _base_domain(r["original_url"])
        by_domain[d].append(r)

    def _counts(recs: list[dict]) -> dict:
        c: dict[str, int] = defaultdict(int)
        for r in recs:
            c[r["outcome"]] += 1
        return c

    rows = []
    for d in sorted(by_domain, key=lambda x: -len(by_domain[x])):
        recs = by_domain[d]
        c = _counts(recs)
        http4xx = sum(v for k, v in c.items() if k.startswith("HTTP_4"))
        http5xx = sum(v for k, v in c.items() if k.startswith("HTTP_5"))
        rows.append((
            d, len(recs),
            c.get("PDF_OK", 0), c.get("HTML_OK", 0),
            c.get("HTML_HAS_PDF_LINK", 0), c.get("HTML_PAYWALL", 0),
            http4xx, http5xx,
            c.get("TIMEOUT", 0), c.get("CONNECTION_ERROR", 0),
        ))

    lines = [
        "## Section 2 — Per-Domain Aggregate Table",
        "",
        "| Domain | Total | PDF_OK | HTML_OK | HTML_HAS_PDF_LINK | HTML_PAYWALL | HTTP_4xx | HTTP_5xx | TIMEOUT | CONN_ERROR |",
        "|--------|------:|-------:|--------:|------------------:|-------------:|---------:|---------:|--------:|-----------:|",
    ]
    for row in rows:
        lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} | {row[8]} | {row[9]} |")
    lines.append("")
    return lines


# Section 3 — Tier-1 Transform Effectiveness
def _section_tier1_transforms(results: list[dict]) -> list[str]:
    t1_results = [r for r in results if r["tier"] == "T1"]
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for r in t1_results:
        d = _base_domain(r["original_url"])
        by_domain[d].append(r)

    lines = [
        "## Section 3 — Tier-1 Transform Effectiveness",
        "",
        "| Domain | Applied Transform | PDF_OK | HTML_HAS_PDF_LINK | HTML_OK | HTML_PAYWALL | HTTP_4xx | TIMEOUT | CONN_ERROR |",
        "|--------|:-----------------:|-------:|------------------:|--------:|-------------:|---------:|--------:|-----------:|",
    ]

    for d in sorted(by_domain):
        recs = by_domain[d]
        applied = sum(1 for r in recs if r["transformed_url"] is not None)
        c: dict[str, int] = defaultdict(int)
        for r in recs:
            c[r["outcome"]] += 1
        http4xx = sum(v for k, v in c.items() if k.startswith("HTTP_4"))
        lines.append(
            f"| {d} | {applied}/{len(recs)} | {c.get('PDF_OK',0)} | "
            f"{c.get('HTML_HAS_PDF_LINK',0)} | {c.get('HTML_OK',0)} | "
            f"{c.get('HTML_PAYWALL',0)} | {http4xx} | "
            f"{c.get('TIMEOUT',0)} | {c.get('CONNECTION_ERROR',0)} |"
        )

    lines.append("")
    lines += ["### Tier-1 URL Detail", ""]
    lines += [
        "| Domain | Original URL | Transformed URL | Outcome |",
        "|--------|-------------|-----------------|---------|",
    ]
    for r in sorted(t1_results, key=lambda x: (_base_domain(x["original_url"]), x["original_url"])):
        d = _base_domain(r["original_url"])
        orig = r["original_url"][:80]
        trans = (r["transformed_url"] or "—")[:80]
        lines.append(f"| {d} | {orig} | {trans} | {r['outcome']} |")
    lines.append("")
    return lines


# Section 4 — HTML_HAS_PDF_LINK Sample (first 30)
def _section_html_pdf_link_sample(results: list[dict]) -> list[str]:
    pdf_link_results = [r for r in results if r["outcome"] == "HTML_HAS_PDF_LINK"]
    lines = [
        "## Section 4 — HTML_HAS_PDF_LINK Sample",
        "",
        f"Total with citation_pdf_url: **{len(pdf_link_results)}**",
        "",
        "| Original URL | citation_pdf_url |",
        "|-------------|-----------------|",
    ]
    for r in pdf_link_results[:30]:
        orig = r["original_url"][:80].replace("|", "%7C")
        pdf_url = (r["citation_pdf_url"] or "")[:80].replace("|", "%7C")
        lines.append(f"| {orig} | {pdf_url} |")
    lines.append("")
    return lines


# Section 5 — HTML_PAYWALL Sample (first 30)
def _section_paywall_sample(results: list[dict]) -> list[str]:
    paywall_results = [r for r in results if r["outcome"] == "HTML_PAYWALL"]
    lines = [
        "## Section 5 — HTML_PAYWALL Sample",
        "",
        f"Total with paywall markers: **{len(paywall_results)}**",
        "",
        "| Original URL | Matched Marker |",
        "|-------------|----------------|",
    ]
    for r in paywall_results[:30]:
        orig = r["original_url"][:80].replace("|", "%7C")
        marker = (r["paywall_marker"] or "")
        lines.append(f"| {orig} | `{marker}` |")
    lines.append("")
    return lines


# Section 6 — Per-URL Detail Table
def _section_per_url_detail(results: list[dict]) -> list[str]:
    sorted_results = sorted(results, key=lambda r: (_base_domain(r["original_url"]), r["original_url"]))

    lines = [
        "## Section 6 — Per-URL Detail",
        "",
        "| Domain | Tier | Original URL | Transform? | Final Outcome | Notes |",
        "|--------|------|-------------|:----------:|---------------|-------|",
    ]
    for r in sorted_results:
        d = _base_domain(r["original_url"])
        tier = r["tier"]
        orig = r["original_url"][:70].replace("|", "%7C")
        has_transform = "✓" if r["transformed_url"] else "—"
        outcome = r["outcome"] or "?"

        notes_parts = []
        if r["citation_pdf_url"]:
            notes_parts.append(f"pdf_url={r['citation_pdf_url'][:40]}")
        if r["paywall_marker"]:
            notes_parts.append(f"marker={r['paywall_marker']}")
        if r["page_title"] and outcome in ("CONNECTION_ERROR", "TIMEOUT"):
            notes_parts.append(f"err={r['page_title'][:40]}")
        notes = "; ".join(notes_parts)

        lines.append(f"| {d} | {tier} | {orig} | {has_transform} | {outcome} | {notes} |")
    lines.append("")
    return lines


if __name__ == "__main__":
    asyncio.run(run_probe())
